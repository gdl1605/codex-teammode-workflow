from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = SCRIPTS_DIR / "prepare_closure_audit.py"


class PrepareClosureAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.write("roles/shard.md", "# shard\n")
        self.write("roles/synthesis.md", "# synthesis\n")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def target(self, path: str, obligation: str) -> dict:
        data = (self.root / path).read_bytes()
        return {
            "path": path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "line_count": len(data.splitlines()),
            "obligation": obligation,
            "reason": "test coverage",
        }

    def run_prepare(self, clauses: object, *extra: str) -> tuple[int, dict]:
        if isinstance(clauses, dict):
            clause_list = copy.deepcopy(clauses.get("verification_clauses", []))
            wrapped = True
        else:
            clause_list = copy.deepcopy(clauses)
            wrapped = False
        if isinstance(clause_list, list) and not any(
            isinstance(clause, dict) and clause.get("kind") == "global"
            for clause in clause_list
        ):
            targets_by_path: dict[str, dict] = {}
            for clause in clause_list:
                if not isinstance(clause, dict):
                    continue
                for target in clause.get("coverage_targets", []):
                    if not isinstance(target, dict) or not isinstance(target.get("path"), str):
                        continue
                    previous = targets_by_path.get(target["path"])
                    if previous is None or target.get("obligation") == "full_read":
                        targets_by_path[target["path"]] = copy.deepcopy(target)
            if targets_by_path:
                clause_list.append(
                    {
                        "clause_id": "__test_global__",
                        "kind": "global",
                        "coverage_targets": list(targets_by_path.values()),
                    }
                )
        clauses = {"verification_clauses": clause_list} if wrapped else clause_list
        clauses_path = self.root / "clauses.json"
        clauses_path.write_text(json.dumps(clauses), encoding="utf-8")
        target_entries = [
            target
            for clause in clause_list
            if isinstance(clause, dict)
            for target in clause.get("coverage_targets", [])
            if isinstance(target, dict) and isinstance(target.get("path"), str)
        ] if isinstance(clause_list, list) else []
        target_paths = {target["path"] for target in target_entries}
        approved_paths = sorted(
            {
                target["path"]
                for target in target_entries
                if target.get("obligation") == "full_read"
            }
        )
        plan_path = self.root / "plan.json"
        plan_path.write_text(
            json.dumps(
                {
                    "plan_schema_version": 3,
                    "approved_files": approved_paths,
                    "audit_scope_manifest": {
                        path: {"baseline_state": "present", "post_state": "present"}
                        for path in sorted(target_paths)
                    },
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PREPARE_SCRIPT),
                "--repo-root",
                str(self.root),
                "--clauses-file",
                str(clauses_path),
                "--plan-file",
                str(plan_path),
                "--shard-role-file",
                str(self.root / "roles/shard.md"),
                "--synthesis-role-file",
                str(self.root / "roles/synthesis.md"),
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_multiple_batches_and_exact_dispatch_shape(self) -> None:
        self.write("docs/a.md", "a" * 10)
        self.write("docs/b.md", "b" * 9)
        self.write("docs/c.md", "needle\n")
        clauses = [
            {"clause_id": "A", "coverage_targets": [self.target("docs/a.md", "full_read")]},
            {"clause_id": "B", "coverage_targets": [self.target("docs/b.md", "full_read")]},
            {"clause_id": "C", "coverage_targets": [self.target("docs/c.md", "targeted_search")]},
        ]
        code, payload = self.run_prepare(clauses, "--max-batch-bytes", "10", "--max-batch-lines", "10")
        self.assertEqual(code, 0)
        self.assertEqual([item["batch_id"] for item in payload["batches"]], ["DRB-001", "DRB-002"])
        self.assertEqual(sum(len(item["targeted_search_files"]) for item in payload["batches"]), 1)
        for batch in payload["batches"]:
            self.assertEqual(set(batch["dispatch"]), {"role_file", "verification_clauses"})
            self.assertRegex(batch["input_sha256"], r"^[0-9a-f]{64}$")
            for clause in batch["dispatch"]["verification_clauses"]:
                self.assertEqual(clause["audit_binding"]["stage"], "shard")
                self.assertEqual(clause["audit_binding"]["batch_id"], batch["batch_id"])

    def test_full_read_dominates_targeted_search_and_paths_are_unique(self) -> None:
        self.write("docs/shared.md", "shared\n")
        self.write("docs/other.md", "other\n")
        clauses = {"verification_clauses": [
            {"clause_id": "one", "coverage_targets": [self.target("docs/shared.md", "targeted_search")]},
            {"clause_id": "two", "coverage_targets": [self.target("docs/shared.md", "full_read"), self.target("docs/other.md", "targeted_search")]},
        ]}
        code, payload = self.run_prepare(clauses)
        self.assertEqual(code, 0)
        self.assertEqual([item["path"] for item in payload["coverage"]["full_read_files"]], ["docs/shared.md"])
        self.assertEqual([item["path"] for item in payload["coverage"]["targeted_search_files"]], ["docs/other.md"])
        assigned = [path for batch in payload["batches"] for path in batch["full_read_files"] + batch["targeted_search_files"]]
        self.assertEqual(sorted(assigned), ["docs/other.md", "docs/shared.md"])
        shared_targets = [
            target
            for clause in payload["batches"][0]["dispatch"]["verification_clauses"]
            for target in clause["coverage_targets"]
            if target["path"] == "docs/shared.md"
        ]
        self.assertTrue(shared_targets)
        self.assertTrue(all(target["obligation"] == "full_read" for target in shared_targets))

    def test_batch_prunes_unassigned_doc_scope_and_keeps_exact_evidence(self) -> None:
        for name, content in (("a", "a" * 10), ("b", "b" * 10), ("c", "search\n")):
            self.write(f"docs/{name}.md", content)
        self.write("src/model.py", "STATE = 'current'\n")
        self.write("evidence/proof.json", "{}\n")
        doc_paths = ["docs/a.md", "docs/b.md", "docs/c.md"]
        clause = {
            "clause_id": "global",
            "kind": "global",
            "statement_to_verify": "Every selected document preserves the current contract.",
            "fact_scope": {
                "subjects": [*doc_paths, "booking lifecycle", "src/model.py"],
                "temporal_class": "current",
            },
            "authority_and_evidence": [
                {"path": "evidence/proof.json", "proves": "bounded test evidence"},
                {"path": "docs/a.md", "proves": "document A evidence"},
                {"path": "docs/b.md", "proves": "document B evidence"},
            ],
            "changed_files": doc_paths,
            "approved_edit_scope": ["docs"],
            "audit_read_scope": ["docs", "src/model.py", "evidence/proof.json"],
            "required_consumers": doc_paths,
            "semantic_neighbors": list(reversed(doc_paths)),
            "forbidden_inferences": ["deployment status"],
            "required_anchors": ["booking-lifecycle"],
            "artifacts": {
                "repository_root": str(self.root),
                "docs_root": str(self.root / "docs"),
                "before": [
                    {
                        "source_path": path,
                        "snapshot_path": str(self.root / "snapshots" / f"{index}.md"),
                        "sha256": str(index) * 64,
                    }
                    for index, path in enumerate(doc_paths, start=1)
                ],
                "after": [
                    {
                        "source_path": path,
                        "current_path": str(self.root / path),
                    }
                    for path in doc_paths
                ],
            },
            "coverage_targets": [
                self.target("docs/a.md", "full_read"),
                self.target("docs/b.md", "full_read"),
                self.target("docs/c.md", "targeted_search"),
            ],
        }
        code, payload = self.run_prepare(
            [clause], "--max-batch-bytes", "10", "--max-batch-lines", "10"
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["batches"]), 2)
        for batch in payload["batches"]:
            selected = set(batch["full_read_files"] + batch["targeted_search_files"])
            dispatched = batch["dispatch"]["verification_clauses"][0]
            for field in (
                "changed_files",
                "approved_edit_scope",
                "required_consumers",
                "semantic_neighbors",
            ):
                self.assertEqual(set(dispatched[field]), selected)
            self.assertEqual(
                set(dispatched["fact_scope"]["subjects"]),
                selected | {"booking lifecycle", "src/model.py"},
            )
            self.assertEqual(
                set(dispatched["audit_read_scope"]),
                selected | {"src/model.py", "evidence/proof.json"},
            )
            for stage in ("before", "after"):
                self.assertEqual(
                    {entry["source_path"] for entry in dispatched["artifacts"][stage]},
                    selected,
                )
            authority_paths = {
                entry["path"] for entry in dispatched["authority_and_evidence"]
            }
            self.assertEqual(
                authority_paths,
                {"evidence/proof.json"} | (selected & {"docs/a.md", "docs/b.md"}),
            )
            self.assertEqual(dispatched["forbidden_inferences"], ["deployment status"])
            self.assertEqual(dispatched["required_anchors"], ["booking-lifecycle"])

    def test_pruned_dispatches_preserve_globally_exact_coverage(self) -> None:
        for name in ("a", "b", "c", "d"):
            self.write(f"docs/{name}.md", name * 8)
        clause = {
            "clause_id": "global",
            "kind": "global",
            "changed_files": [f"docs/{name}.md" for name in ("a", "b", "c", "d")],
            "audit_read_scope": ["docs"],
            "coverage_targets": [
                self.target("docs/a.md", "full_read"),
                self.target("docs/b.md", "full_read"),
                self.target("docs/c.md", "targeted_search"),
                self.target("docs/d.md", "targeted_search"),
            ],
        }
        code, payload = self.run_prepare([clause], "--max-batch-bytes", "8")
        self.assertEqual(code, 0)
        expected = {f"docs/{name}.md" for name in ("a", "b", "c", "d")}
        assigned = [
            path
            for batch in payload["batches"]
            for path in batch["full_read_files"] + batch["targeted_search_files"]
        ]
        dispatched_targets = [
            target["path"]
            for batch in payload["batches"]
            for dispatched in batch["dispatch"]["verification_clauses"]
            for target in dispatched["coverage_targets"]
        ]
        self.assertEqual(set(assigned), expected)
        self.assertEqual(len(assigned), len(expected))
        self.assertEqual(set(dispatched_targets), expected)
        self.assertEqual(len(dispatched_targets), len(expected))

    def test_hash_and_line_mismatches_are_findings(self) -> None:
        self.write("docs/a.md", "one\ntwo\n")
        target = self.target("docs/a.md", "full_read")
        target["sha256"] = "0" * 64
        target["line_count"] = 1
        code, payload = self.run_prepare([{"clause_id": "a", "coverage_targets": [target]}])
        self.assertEqual(code, 1)
        self.assertEqual(payload["batches"], [])
        self.assertIn("coverage_sha256_mismatch", {f["type"] for f in payload["findings"]})

    def test_line_mismatch_is_a_finding_when_hash_matches(self) -> None:
        self.write("docs/a.md", "one\ntwo\n")
        target = self.target("docs/a.md", "full_read")
        target["line_count"] = 1
        code, payload = self.run_prepare([{"clause_id": "a", "coverage_targets": [target]}])
        self.assertEqual(code, 1)
        self.assertIn("coverage_line_count_mismatch", {f["type"] for f in payload["findings"]})

    def test_oversized_full_read_stops_dispatch(self) -> None:
        self.write("docs/a.md", "x" * 12)
        code, payload = self.run_prepare(
            [{"clause_id": "a", "coverage_targets": [self.target("docs/a.md", "full_read")]}],
            "--max-batch-bytes",
            "10",
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["batches"], [])
        self.assertIn("oversized_full_read_file", {f["type"] for f in payload["findings"]})

    def test_full_read_over_line_budget_stops_dispatch(self) -> None:
        self.write("docs/long.md", "\n".join(f"line {index}" for index in range(11)) + "\n")
        code, payload = self.run_prepare(
            [{"clause_id": "long", "coverage_targets": [self.target("docs/long.md", "full_read")]}],
            "--max-batch-lines",
            "10",
        )
        self.assertEqual(code, 1)
        self.assertEqual(payload["batches"], [])
        self.assertIn("oversized_full_read_file", {f["type"] for f in payload["findings"]})

    def test_bad_path_and_bad_json_exit_two(self) -> None:
        self.write("docs/a.md", "ok\n")
        bad = self.target("docs/a.md", "full_read")
        bad["path"] = "../outside.md"
        code, payload = self.run_prepare([{"clause_id": "a", "coverage_targets": [bad]}])
        self.assertEqual(code, 2)
        self.assertEqual(len(payload["errors"]), 1)
        clauses_path = self.root / "invalid.json"
        clauses_path.write_text("{broken", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(PREPARE_SCRIPT), "--repo-root", str(self.root), "--clauses-file", str(clauses_path), "--shard-role-file", str(self.root / "roles/shard.md"), "--synthesis-role-file", str(self.root / "roles/synthesis.md")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["type"], "input_error")

    def test_output_is_deterministic(self) -> None:
        self.write("docs/a.md", "aaa\n")
        self.write("docs/b.md", "bbb\n")
        clauses = [
            {"clause_id": "b", "coverage_targets": [self.target("docs/b.md", "full_read")]},
            {"clause_id": "a", "coverage_targets": [self.target("docs/a.md", "full_read")]},
        ]
        first_code, first = self.run_prepare(copy.deepcopy(clauses), "--max-batch-bytes", "4")
        second_code, second = self.run_prepare(copy.deepcopy(clauses), "--max-batch-bytes", "4")
        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
