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
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_closure_audit.py"


def clause_hash(clauses: list[dict]) -> str:
    clauses = copy.deepcopy(clauses)
    for clause in clauses:
        clause.pop("audit_binding", None)
    value = json.dumps(clauses, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ValidateClosureAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.role_file = self.root / "role.md"
        self.role_file.write_text("# Test role\n", encoding="utf-8")
        sha = "a" * 64
        base_clauses = [
            {"clause_id": "DR-CLOSURE-001", "kind": "claim", "coverage_targets": [{"path": "docs/current.md", "sha256": sha, "line_count": 10, "obligation": "full_read", "reason": "changed claim"}]},
            {"clause_id": "DR-CLOSURE-GLOBAL", "kind": "global", "coverage_targets": [{"path": "docs/current.md", "sha256": sha, "line_count": 10, "obligation": "full_read", "reason": "changed file"}, {"path": "docs/neighbor.md", "sha256": "b" * 64, "line_count": 20, "obligation": "targeted_search", "reason": "global scope"}]},
        ]
        manifest_hash = clause_hash(base_clauses)
        self.shard_clauses = copy.deepcopy(base_clauses)
        self.synthesis_clauses = copy.deepcopy(base_clauses)
        for clause in self.shard_clauses:
            clause["audit_binding"] = {
                "audit_id": "audit-001",
                "stage": "shard",
                "batch_id": "batch-a",
                "clause_manifest_sha256": manifest_hash,
            }
        for clause in self.synthesis_clauses:
            clause["audit_binding"] = {
                "audit_id": "audit-001",
                "stage": "synthesis",
                "batch_id": "synthesis",
                "clause_manifest_sha256": manifest_hash,
            }
        self.manifest = {
            "audit_schema_version": 2,
            "audit_id": "audit-001",
            "batches": [{"batch_id": "batch-a", "dispatch": {"role_file": str(self.role_file), "verification_clauses": self.shard_clauses}}],
            "synthesis_dispatch": {"role_file": str(self.role_file), "verification_clauses": self.synthesis_clauses},
        }
        self.report = self.make_report("shard", "batch-a")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def make_report(self, stage: str, batch_id: str) -> dict:
        clauses = self.shard_clauses if stage == "shard" else self.synthesis_clauses
        return {
            "audit_schema_version": 2, "audit_id": "audit-001", "stage": stage, "batch_id": batch_id, "clause_manifest_sha256": clause_hash(clauses),
            "closure_audit": {
                "verdict": "pass", "role_acknowledgement": {"role_file_read": True, "two_field_input_valid": True, "read_only": True},
                "clause_results": [
                    {"clause_id": "DR-CLOSURE-001", "outcome": "verified", "evidence": "docs/current.md:3", "full_read_files": ["docs/current.md"], "targeted_search_files": [], "searches_performed": ["claim vocabulary"], "deficiency_ids": [], "blocked_check_ids": []},
                    {"clause_id": "DR-CLOSURE-GLOBAL", "outcome": "verified", "evidence": "docs/current.md:3; docs/neighbor.md:4", "full_read_files": ["docs/current.md"], "targeted_search_files": ["docs/neighbor.md"], "searches_performed": ["global vocabulary"], "deficiency_ids": [], "blocked_check_ids": []},
                ],
                "main_agent_deficiencies": [], "blocked_checks": [],
                "coverage_accounting": {"expected_clause_ids": ["DR-CLOSURE-001", "DR-CLOSURE-GLOBAL"], "completed_clause_ids": ["DR-CLOSURE-001", "DR-CLOSURE-GLOBAL"], "required_full_read_files": ["docs/current.md"], "full_read_files_completed": ["docs/current.md"], "required_targeted_search_files": ["docs/neighbor.md"], "targeted_search_files_completed": ["docs/neighbor.md"], "omitted_or_unverifiable": []},
                "global_review": {"paths_examined": ["docs/current.md", "docs/neighbor.md"], "search_scopes": ["docs"], "searches_performed": ["lifecycle search"], "residual_risk": "none found"},
            },
        }

    def rebind_shard_contract(self) -> None:
        manifest_hash = clause_hash(self.shard_clauses)
        for clause in self.shard_clauses:
            clause["audit_binding"] = {
                "audit_id": "audit-001",
                "stage": "shard",
                "batch_id": "batch-a",
                "clause_manifest_sha256": manifest_hash,
            }
        self.manifest["batches"][0]["dispatch"]["verification_clauses"] = self.shard_clauses
        self.report["clause_manifest_sha256"] = manifest_hash

    def add_support_path_contract(self) -> None:
        clause = self.shard_clauses[0]
        clause["authority_and_evidence"] = [
            {"path": "/audit/current-evidence.json", "sha256": "c" * 64, "proves": "bounded evidence"}
        ]
        clause["artifacts"] = {
            "repository_root": "/repo",
            "before": [
                {
                    "source_path": "docs/current.md",
                    "snapshot_path": "/audit/before/docs/current.md",
                    "sha256": "d" * 64,
                }
            ],
            "after": [
                {
                    "source_path": "docs/current.md",
                    "current_path": "/repo/docs/current.md",
                    "sha256": "a" * 64,
                }
            ],
        }
        clause["audit_read_scope"] = ["docs", "src/current.ts"]
        self.report["closure_audit"]["global_review"]["paths_examined"].extend(
            [
                "/audit/current-evidence.json",
                "/audit/before/docs/current.md",
                "src/current.ts",
                "docs/supporting-context.md",
            ]
        )
        self.rebind_shard_contract()

    def run_validate(self, report: dict | str | None = None, *, stage: str = "shard", batch_id: str | None = "batch-a") -> tuple[int, dict]:
        manifest_path, report_path = self.root / "manifest.json", self.root / "report.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        report_path.write_text(report if isinstance(report, str) else json.dumps(self.report if report is None else report), encoding="utf-8")
        command = [sys.executable, str(VALIDATE_SCRIPT), "--stage", stage, "--audit-manifest", str(manifest_path), "--report-file", str(report_path)]
        if batch_id is not None:
            command.extend(["--batch-id", batch_id])
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def error_types(self, payload: dict) -> set[str]:
        return {item["type"] for item in payload["errors"]}

    def finding_types(self, payload: dict) -> set[str]:
        return {item["type"] for item in payload["findings"]}

    def add_deficiency(self, report: dict, **overrides: object) -> None:
        audit = report["closure_audit"]
        audit["verdict"] = "deficiencies_found"
        audit["clause_results"][0].update({"outcome": "deficiency", "deficiency_ids": ["CA-001"]})
        deficiency = {"finding_id": "CA-001", "severity": "P1", "clause_id": "DR-CLOSURE-001", "type": "direct_contradiction", "artifact_layer": "docs", "effect_class": "reader_contract", "location": "docs/current.md:3", "comparison_evidence": "docs/current.md:3", "why_main_agent_is_wrong_or_incomplete": "The current contract contradicts the bounded evidence.", "affected_scope": "current readers", "correction_constraint": "Preserve canonical ownership."}
        deficiency.update(overrides)
        audit["main_agent_deficiencies"] = [deficiency]

    def test_complete_shard_pass_exit_zero(self) -> None:
        code, payload = self.run_validate()
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_authorized_support_paths_are_separate_from_exact_coverage(self) -> None:
        self.add_support_path_contract()
        code, payload = self.run_validate()
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_dispatched_role_file_may_be_reported_as_examined(self) -> None:
        self.report["closure_audit"]["global_review"]["paths_examined"].append(
            str(self.role_file)
        )
        code, payload = self.run_validate()
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_authorized_support_paths_preserve_coherent_deficiency_exit_one(self) -> None:
        self.add_support_path_contract()
        self.add_deficiency(self.report)
        code, payload = self.run_validate()
        self.assertEqual(code, 1)
        self.assertEqual(payload["summary"]["errors"], 0)
        self.assertIn("auditor_reported_non_pass", self.finding_types(payload))

    def test_unauthorized_examined_path_exits_two(self) -> None:
        self.add_support_path_contract()
        self.report["closure_audit"]["global_review"]["paths_examined"].append(
            "/unapproved/private.txt"
        )
        code, payload = self.run_validate()
        self.assertEqual(code, 2)
        self.assertIn("global_path_outside_dispatch_scope", self.error_types(payload))

    def test_missing_required_authority_path_exits_two(self) -> None:
        self.add_support_path_contract()
        self.report["closure_audit"]["global_review"]["paths_examined"].remove(
            "/audit/current-evidence.json"
        )
        code, payload = self.run_validate()
        self.assertEqual(code, 2)
        self.assertIn("global_required_support_path_not_examined", self.error_types(payload))

    def test_missing_required_before_snapshot_exits_two(self) -> None:
        self.add_support_path_contract()
        self.report["closure_audit"]["global_review"]["paths_examined"].remove(
            "/audit/before/docs/current.md"
        )
        code, payload = self.run_validate()
        self.assertEqual(code, 2)
        self.assertIn("global_required_support_path_not_examined", self.error_types(payload))

    def test_after_artifact_accepts_repo_relative_source_alias(self) -> None:
        self.add_support_path_contract()
        paths = self.report["closure_audit"]["global_review"]["paths_examined"]
        self.assertIn("docs/current.md", paths)
        self.assertNotIn("/repo/docs/current.md", paths)
        code, payload = self.run_validate()
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["errors"], 0)

    def test_complete_synthesis_pass_exit_zero(self) -> None:
        report = self.make_report("synthesis", "synthesis")
        code, payload = self.run_validate(report, stage="synthesis", batch_id=None)
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["findings"], 0)

    def test_coherent_deficiency_exits_one(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(report)
        code, payload = self.run_validate(report)
        self.assertEqual(code, 1)
        self.assertIn("auditor_reported_non_pass", self.finding_types(payload))

    def test_coherent_blocked_exits_one(self) -> None:
        report = copy.deepcopy(self.report)
        audit = report["closure_audit"]
        audit["verdict"] = "blocked"
        audit["clause_results"][0].update({"outcome": "blocked", "blocked_check_ids": ["CB-001"]})
        audit["blocked_checks"] = [{"blocked_check_id": "CB-001", "clause_id": "DR-CLOSURE-001", "reason": "Evidence is unavailable.", "required_to_unblock": "Provide evidence/current.json."}]
        code, payload = self.run_validate(report)
        self.assertEqual(code, 1)
        self.assertIn("auditor_reported_non_pass", self.finding_types(payload))

    def test_missing_deficiency_field_exits_two(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(report)
        del report["closure_audit"]["main_agent_deficiencies"][0]["correction_constraint"]
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("required_field_missing", self.error_types(payload))

    def test_truncated_json_exits_two(self) -> None:
        code, payload = self.run_validate("{\"audit_schema_version\": 2")
        self.assertEqual(code, 2)
        self.assertEqual(payload["summary"]["errors"], 1)

    def test_binding_mismatch_exits_two(self) -> None:
        report = copy.deepcopy(self.report)
        report["batch_id"] = "wrong-batch"
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("report_binding_mismatch", self.error_types(payload))

    def test_coverage_omission_and_pass_claim_exit_two(self) -> None:
        report = copy.deepcopy(self.report)
        report["closure_audit"]["coverage_accounting"]["targeted_search_files_completed"] = []
        report["closure_audit"]["clause_results"][1]["targeted_search_files"] = []
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("completed_coverage_mismatch", self.error_types(payload))

    def test_invalid_p0_attribution_exits_two(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(report, severity="P0", artifact_layer="docs", effect_class="reader_contract", type="direct_contradiction")
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("invalid_p0_attribution", self.error_types(payload))

    def test_documentation_scope_violation_cannot_be_p0(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(
            report,
            severity="P0",
            artifact_layer="docs",
            effect_class="current_behavior",
            type="scope_violation",
        )
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("invalid_p0_attribution", self.error_types(payload))

    def test_implementation_finding_needs_code_or_evidence_path(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(report, artifact_layer="implementation", comparison_evidence="docs/current.md:3")
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertIn("invalid_implementation_attribution", self.error_types(payload))

    def test_deficiency_needs_exact_location_and_comparison_citation(self) -> None:
        report = copy.deepcopy(self.report)
        self.add_deficiency(
            report,
            location="the current document",
            comparison_evidence="The two sources disagree.",
        )
        code, payload = self.run_validate(report)
        self.assertEqual(code, 2)
        self.assertTrue(
            {"deficiency_location_not_exact", "comparison_evidence_not_exact"}.issubset(
                self.error_types(payload)
            )
        )

    def test_shard_and_synthesis_binding_are_distinct(self) -> None:
        report = self.make_report("synthesis", "synthesis")
        code, payload = self.run_validate(report, stage="shard", batch_id="batch-a")
        self.assertEqual(code, 2)
        self.assertIn("report_binding_mismatch", self.error_types(payload))

    def test_dispatch_with_third_top_level_field_is_rejected(self) -> None:
        self.manifest["batches"][0]["dispatch"]["narrative"] = "main-agent summary"
        code, payload = self.run_validate()
        self.assertEqual(code, 2)
        self.assertEqual(payload["errors"][0]["type"], "input_error")


if __name__ == "__main__":
    unittest.main()
