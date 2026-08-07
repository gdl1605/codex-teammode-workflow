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
MERGE_SCRIPT = SCRIPTS_DIR / "merge_closure_audits.py"
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_closure_audit.py"
SCAN_SCRIPT = SCRIPTS_DIR / "scan_docs.py"


class MergeClosureAuditsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.write("roles/shard.md", "# Shard role\n")
        self.write("roles/synthesis.md", "# Synthesis role\n")
        self.write("docs/a.md", "a" * 10)
        self.write("docs/b.md", "b" * 9)
        a = self.target("docs/a.md")
        b = self.target("docs/b.md")
        self.clauses = [
            {"clause_id": "CLAIM-A", "kind": "claim", "coverage_targets": [a]},
            {"clause_id": "CLAIM-B", "kind": "claim", "coverage_targets": [b]},
            {
                "clause_id": "GLOBAL",
                "kind": "global",
                "changed_files": ["docs/a.md", "docs/b.md"],
                "approved_edit_scope": ["docs/a.md", "docs/b.md"],
                "audit_read_scope": ["docs"],
                "required_consumers": ["docs/a.md", "docs/b.md"],
                "semantic_neighbors": ["docs/b.md", "docs/a.md"],
                "authority_and_evidence": [
                    {"path": "docs/a.md", "proves": "bounded A"},
                    {"path": "docs/b.md", "proves": "bounded B"},
                ],
                "fact_scope": {
                    "subjects": ["docs/a.md", "docs/b.md"],
                    "platforms": ["shared"],
                    "environments": ["fixture"],
                    "lifecycle_axes": ["validated"],
                    "effective_date": "2026-08-04",
                },
                "artifacts": {
                    "repository_root": str(self.root),
                    "docs_root": str(self.root / "docs"),
                    "before": [],
                    "after": [
                        {"source_path": "docs/a.md", "current_path": str(self.root / "docs/a.md")},
                        {"source_path": "docs/b.md", "current_path": str(self.root / "docs/b.md")},
                    ],
                },
                "coverage_targets": [copy.deepcopy(a), copy.deepcopy(b)],
            },
        ]
        self.manifest = self.prepare(self.clauses)
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.report_paths: list[Path] = []
        for batch in self.manifest["batches"]:
            path = self.root / f"{batch['batch_id']}.json"
            path.write_text(json.dumps(self.make_report(self.manifest, batch["batch_id"])), encoding="utf-8")
            self.report_paths.append(path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def target(self, relative: str) -> dict:
        data = (self.root / relative).read_bytes()
        return {
            "path": relative,
            "sha256": hashlib.sha256(data).hexdigest(),
            "line_count": len(data.splitlines()),
            "obligation": "full_read",
            "synthesis_obligation": "targeted_search",
            "reason": "cross-shard fixture contract",
        }

    def prepare(self, clauses: list[dict]) -> dict:
        clause_path = self.root / "clauses.json"
        clause_path.write_text(json.dumps(clauses), encoding="utf-8")
        target_paths = sorted(
            {
                target["path"]
                for clause in clauses
                for target in clause.get("coverage_targets", [])
            }
        )
        approved_paths = sorted(
            {
                target["path"]
                for clause in clauses
                for target in clause.get("coverage_targets", [])
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
                        for path in target_paths
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
                str(clause_path),
                "--plan-file",
                str(plan_path),
                "--shard-role-file",
                str(self.root / "roles/shard.md"),
                "--synthesis-role-file",
                str(self.root / "roles/synthesis.md"),
                "--max-batch-bytes",
                "10",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return json.loads(result.stdout)

    def make_report(self, manifest: dict, batch_id: str) -> dict:
        batch = next(item for item in manifest["batches"] if item["batch_id"] == batch_id)
        clauses = batch["dispatch"]["verification_clauses"]
        clause_results = []
        all_full: set[str] = set()
        all_search: set[str] = set()
        for clause in clauses:
            full = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "full_read")
            search = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "targeted_search")
            all_full.update(full)
            all_search.update(search)
            clause_results.append(
                {
                    "clause_id": clause["clause_id"],
                    "outcome": "verified",
                    "evidence": ", ".join(full + search),
                    "full_read_files": full,
                    "targeted_search_files": search,
                    "searches_performed": ["bounded fixture vocabulary"],
                    "deficiency_ids": [],
                    "blocked_check_ids": [],
                }
            )
        clause_ids = sorted(result["clause_id"] for result in clause_results)
        return {
            "audit_schema_version": 2,
            "audit_id": manifest["audit_id"],
            "stage": "shard",
            "batch_id": batch_id,
            "clause_manifest_sha256": batch["clause_manifest_sha256"],
            "closure_audit": {
                "verdict": "pass",
                "role_acknowledgement": {
                    "role_file_read": True,
                    "two_field_input_valid": True,
                    "read_only": True,
                },
                "clause_results": clause_results,
                "main_agent_deficiencies": [],
                "blocked_checks": [],
                "coverage_accounting": {
                    "expected_clause_ids": clause_ids,
                    "completed_clause_ids": clause_ids,
                    "required_full_read_files": sorted(all_full),
                    "full_read_files_completed": sorted(all_full),
                    "required_targeted_search_files": sorted(all_search),
                    "targeted_search_files_completed": sorted(all_search),
                    "omitted_or_unverifiable": [],
                },
                "global_review": {
                    "paths_examined": sorted(all_full | all_search),
                    "search_scopes": ["assigned batch"],
                    "searches_performed": ["lifecycle and platform vocabulary"],
                    "residual_risk": "Cross-shard conclusions remain for synthesis.",
                },
            },
        }

    def make_synthesis_report(self, merged: dict) -> dict:
        clauses = merged["synthesis_dispatch"]["verification_clauses"]
        results = []
        full: set[str] = set()
        search: set[str] = set()
        for clause in clauses:
            clause_full = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "full_read")
            clause_search = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "targeted_search")
            full.update(clause_full)
            search.update(clause_search)
            results.append(
                {
                    "clause_id": clause["clause_id"],
                    "outcome": "verified",
                    "evidence": ", ".join(clause_full + clause_search),
                    "full_read_files": clause_full,
                    "targeted_search_files": clause_search,
                    "searches_performed": ["cross-shard contract vocabulary"],
                    "deficiency_ids": [],
                    "blocked_check_ids": [],
                }
            )
        ids = sorted(item["clause_id"] for item in results)
        validated_report_paths = {
            item["path"] for item in merged["validated_shard_reports"]
        }
        return {
            "audit_schema_version": 2,
            "audit_id": merged["audit_id"],
            "stage": "synthesis",
            "batch_id": "synthesis",
            "clause_manifest_sha256": merged["synthesis_clause_manifest_sha256"],
            "closure_audit": {
                "verdict": "pass",
                "role_acknowledgement": {"role_file_read": True, "two_field_input_valid": True, "read_only": True},
                "clause_results": results,
                "main_agent_deficiencies": [],
                "blocked_checks": [],
                "coverage_accounting": {
                    "expected_clause_ids": ids,
                    "completed_clause_ids": ids,
                    "required_full_read_files": sorted(full),
                    "full_read_files_completed": sorted(full),
                    "required_targeted_search_files": sorted(search),
                    "targeted_search_files_completed": sorted(search),
                    "omitted_or_unverifiable": [],
                },
                "global_review": {
                    "paths_examined": sorted(full | search | validated_report_paths),
                    "search_scopes": ["cross-shard fixture"],
                    "searches_performed": ["current/candidate and lifecycle comparison"],
                    "residual_risk": "No residual risk found in the bounded fixture.",
                },
            },
        }

    def run_merge(
        self,
        reports: list[Path],
        *,
        manifest_path: Path | None = None,
        previous_manifest: Path | None = None,
        previous_reports: list[Path] | None = None,
    ) -> tuple[int, dict]:
        command = [
            sys.executable,
            str(MERGE_SCRIPT),
            "--audit-manifest",
            str(manifest_path or self.manifest_path),
        ]
        for report in reports:
            command.extend(["--report-file", str(report)])
        if previous_manifest is not None:
            command.extend(["--previous-audit-manifest", str(previous_manifest)])
        for report in previous_reports or []:
            command.extend(["--previous-report-file", str(report)])
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_all_shards_pass_generate_two_field_synthesis_dispatch(self) -> None:
        code, payload = self.run_merge(self.report_paths)
        self.assertEqual(code, 0, payload["errors"])
        self.assertEqual(payload["verdict"], "ready_for_fresh_synthesis")
        self.assertEqual(set(payload["synthesis_dispatch"]), {"role_file", "verification_clauses"})
        self.assertFalse(payload["report_reuse"]["synthesis_reuse_allowed"])
        globals_ = [
            clause
            for clause in payload["synthesis_dispatch"]["verification_clauses"]
            if clause["kind"] == "global"
        ]
        self.assertEqual(len(globals_), 1)
        self.assertEqual(len(globals_[0]["validated_shard_reports"]), 2)
        self.assertNotIn("synthesis_requirements", globals_[0])
        global_clause = globals_[0]
        expected_docs = {"docs/a.md", "docs/b.md"}
        for field in (
            "changed_files",
            "approved_edit_scope",
            "audit_read_scope",
            "required_consumers",
            "semantic_neighbors",
        ):
            self.assertEqual(set(global_clause[field]), expected_docs)
        self.assertEqual(
            {entry["path"] for entry in global_clause["authority_and_evidence"]},
            expected_docs,
        )
        self.assertEqual(set(global_clause["fact_scope"]["subjects"]), expected_docs)
        self.assertEqual(
            {entry["source_path"] for entry in global_clause["artifacts"]["after"]},
            expected_docs,
        )

    def test_merge_output_accepts_a_fresh_complete_synthesis_report(self) -> None:
        code, merged = self.run_merge(self.report_paths)
        self.assertEqual(code, 0)
        merge_path = self.root / "merged.json"
        merge_path.write_text(json.dumps(merged), encoding="utf-8")
        clauses = merged["synthesis_dispatch"]["verification_clauses"]
        results = []
        full: set[str] = set()
        search: set[str] = set()
        for clause in clauses:
            clause_full = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "full_read")
            clause_search = sorted(target["path"] for target in clause["coverage_targets"] if target["obligation"] == "targeted_search")
            full.update(clause_full)
            search.update(clause_search)
            results.append(
                {
                    "clause_id": clause["clause_id"],
                    "outcome": "verified",
                    "evidence": ", ".join(clause_full + clause_search),
                    "full_read_files": clause_full,
                    "targeted_search_files": clause_search,
                    "searches_performed": ["cross-shard contract vocabulary"],
                    "deficiency_ids": [],
                    "blocked_check_ids": [],
                }
            )
        ids = sorted(item["clause_id"] for item in results)
        validated_report_paths = {
            item["path"] for item in merged["validated_shard_reports"]
        }
        report = {
            "audit_schema_version": 2,
            "audit_id": merged["audit_id"],
            "stage": "synthesis",
            "batch_id": "synthesis",
            "clause_manifest_sha256": merged["synthesis_clause_manifest_sha256"],
            "closure_audit": {
                "verdict": "pass",
                "role_acknowledgement": {"role_file_read": True, "two_field_input_valid": True, "read_only": True},
                "clause_results": results,
                "main_agent_deficiencies": [],
                "blocked_checks": [],
                "coverage_accounting": {
                    "expected_clause_ids": ids,
                    "completed_clause_ids": ids,
                    "required_full_read_files": sorted(full),
                    "full_read_files_completed": sorted(full),
                    "required_targeted_search_files": sorted(search),
                    "targeted_search_files_completed": sorted(search),
                    "omitted_or_unverifiable": [],
                },
                "global_review": {
                    "paths_examined": sorted(full | search | validated_report_paths),
                    "search_scopes": ["cross-shard fixture"],
                    "searches_performed": ["current/candidate and lifecycle comparison"],
                    "residual_risk": "No residual risk found in the bounded fixture.",
                },
            },
        }
        report_path = self.root / "synthesis-report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_SCRIPT),
                "--stage",
                "synthesis",
                "--audit-manifest",
                str(merge_path),
                "--report-file",
                str(report_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_duplicate_batch_report_is_exit_two(self) -> None:
        code, payload = self.run_merge(self.report_paths + [self.report_paths[0]])
        self.assertEqual(code, 2)
        self.assertIn("duplicate_batch_report", {item["type"] for item in payload["errors"]})

    def test_missing_batch_report_is_exit_two(self) -> None:
        code, payload = self.run_merge(self.report_paths[:1])
        self.assertEqual(code, 2)
        self.assertIn("missing_batch_report", {item["type"] for item in payload["errors"]})

    def test_coverage_overlap_is_exit_two(self) -> None:
        broken = copy.deepcopy(self.manifest)
        duplicate_path = broken["batches"][0]["full_read_files"][0]
        broken["batches"][1]["targeted_search_files"].append(duplicate_path)
        path = self.root / "broken-manifest.json"
        path.write_text(json.dumps(broken), encoding="utf-8")
        code, payload = self.run_merge(self.report_paths, manifest_path=path)
        self.assertEqual(code, 2)
        self.assertIn("batch_coverage_overlap", {item["type"] for item in payload["errors"]})

    def test_tampered_reuse_key_is_exit_two(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["batches"][0]["reuse_key"] = "0" * 64
        path = self.root / "tampered-reuse.json"
        path.write_text(json.dumps(broken), encoding="utf-8")
        code, payload = self.run_merge(self.report_paths, manifest_path=path)
        self.assertEqual(code, 2)
        self.assertIn("batch_reuse_key_mismatch", {item["type"] for item in payload["errors"]})

    def test_nonpass_shard_creates_lossless_human_gate_and_no_synthesis(self) -> None:
        report = json.loads(self.report_paths[0].read_text(encoding="utf-8"))
        claim_result = next(item for item in report["closure_audit"]["clause_results"] if item["clause_id"] != "GLOBAL")
        claim_result.update({"outcome": "deficiency", "deficiency_ids": ["CA-001"]})
        deficiency = {
            "finding_id": "CA-001",
            "severity": "P1",
            "clause_id": claim_result["clause_id"],
            "type": "direct_contradiction",
            "artifact_layer": "docs",
            "effect_class": "reader_contract",
            "location": claim_result["full_read_files"][0] + ":1",
            "comparison_evidence": claim_result["full_read_files"][0] + ":1 differs from its bounded repository evidence.",
            "why_main_agent_is_wrong_or_incomplete": "The edit preserved a stale current-state statement.",
            "affected_scope": "Readers of the current contract.",
            "correction_constraint": "Replace only the stale current-state sentence.",
        }
        report["closure_audit"]["main_agent_deficiencies"] = [deficiency]
        report["closure_audit"]["verdict"] = "deficiencies_found"
        self.report_paths[0].write_text(json.dumps(report), encoding="utf-8")
        code, payload = self.run_merge(self.report_paths)
        self.assertEqual(code, 1, payload.get("errors"))
        self.assertIsNone(payload["synthesis_dispatch"])
        self.assertEqual(payload["human_gate"]["deficiencies"], [deficiency])
        self.assertEqual(payload["human_gate"]["proposed_correction_scope"], [claim_result["full_read_files"][0]])
        self.assertIn(claim_result["full_read_files"][0], payload["human_gate"]["post_apply_baseline"])
        self.assertEqual(payload["human_gate"]["finding_boundaries"][0]["finding_id"], "CA-001")

    def test_reconstructed_or_incomplete_report_is_exit_two(self) -> None:
        report = json.loads(self.report_paths[0].read_text(encoding="utf-8"))
        report["closure_audit"].pop("coverage_accounting")
        self.report_paths[0].write_text(json.dumps(report), encoding="utf-8")
        code, payload = self.run_merge(self.report_paths)
        self.assertEqual(code, 2)
        self.assertIn("invalid_shard_report", {item["type"] for item in payload["errors"]})

    def test_hash_based_reuse_only_fills_unchanged_batch(self) -> None:
        self.write("docs/a.md", "changed-a")
        updated_clauses = copy.deepcopy(self.clauses)
        updated_target = self.target("docs/a.md")
        for clause in updated_clauses:
            clause["coverage_targets"] = [
                copy.deepcopy(updated_target) if target["path"] == "docs/a.md" else target
                for target in clause["coverage_targets"]
            ]
        current = self.prepare(updated_clauses)
        old_keys = {batch["reuse_key"] for batch in self.manifest["batches"]}
        changed_batch = next(batch for batch in current["batches"] if batch["reuse_key"] not in old_keys)
        current_path = self.root / "current-manifest.json"
        current_path.write_text(json.dumps(current), encoding="utf-8")
        fresh_report = self.root / "fresh-changed.json"
        fresh_report.write_text(json.dumps(self.make_report(current, changed_batch["batch_id"])), encoding="utf-8")
        code, payload = self.run_merge(
            [fresh_report],
            manifest_path=current_path,
            previous_manifest=self.manifest_path,
            previous_reports=self.report_paths,
        )
        self.assertEqual(code, 0, payload.get("errors"))
        self.assertEqual(payload["report_reuse"]["fresh_batches"], [changed_batch["batch_id"]])
        self.assertEqual(len(payload["report_reuse"]["reused_batches"]), 1)
        self.assertFalse(payload["report_reuse"]["synthesis_reuse_allowed"])

    def test_scanner_zero_does_not_override_synthesis_semantic_deficiency(self) -> None:
        scan = subprocess.run(
            [sys.executable, str(SCAN_SCRIPT), "--repo-root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(scan.returncode, 0, scan.stdout)
        code, merged = self.run_merge(self.report_paths)
        self.assertEqual(code, 0)
        report = self.make_synthesis_report(merged)
        global_result = next(item for item in report["closure_audit"]["clause_results"] if item["clause_id"] == "GLOBAL")
        global_result.update({"outcome": "deficiency", "deficiency_ids": ["SA-001"]})
        report["closure_audit"]["verdict"] = "deficiencies_found"
        report["closure_audit"]["main_agent_deficiencies"] = [
            {
                "finding_id": "SA-001",
                "severity": "P1",
                "clause_id": "GLOBAL",
                "type": "cross_shard_semantic_contradiction",
                "artifact_layer": "docs",
                "effect_class": "reader_contract",
                "location": "docs/b.md:1",
                "comparison_evidence": "docs/a.md:1 and docs/b.md:1 express incompatible cross-shard contracts.",
                "why_main_agent_is_wrong_or_incomplete": "Deterministic syntax checks passed but the two semantic owners remain incompatible.",
                "affected_scope": "Readers consuming both canonical slices.",
                "correction_constraint": "Resolve canonical ownership without inferring implementation behavior.",
            }
        ]
        merge_path = self.root / "semantic-merge.json"
        report_path = self.root / "semantic-synthesis.json"
        merge_path.write_text(json.dumps(merged), encoding="utf-8")
        report_path.write_text(json.dumps(report), encoding="utf-8")
        validation = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_SCRIPT),
                "--stage",
                "synthesis",
                "--audit-manifest",
                str(merge_path),
                "--report-file",
                str(report_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(validation.returncode, 1, validation.stdout)
        payload = json.loads(validation.stdout)
        self.assertEqual(payload["summary"]["errors"], 0)


if __name__ == "__main__":
    unittest.main()
