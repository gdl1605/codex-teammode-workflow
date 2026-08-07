from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]


class DocsReviewV3ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.interaction = (SKILL_ROOT / "references" / "interaction-and-output.md").read_text(encoding="utf-8")
        cls.reconciliation = (SKILL_ROOT / "references" / "reconciliation-rules.md").read_text(encoding="utf-8")
        cls.shard_role_path = SKILL_ROOT / "references" / "independent-closure-auditor.md"
        cls.synthesis_role_path = SKILL_ROOT / "references" / "independent-closure-synthesizer.md"
        cls.shard_role = cls.shard_role_path.read_text(encoding="utf-8")
        cls.synthesis_role = cls.synthesis_role_path.read_text(encoding="utf-8")
        cls.all_text = "\n".join(
            [cls.skill, cls.interaction, cls.reconciliation, cls.shard_role, cls.synthesis_role]
        )

    def test_roles_and_scripts_are_packaged(self) -> None:
        self.assertTrue(self.shard_role_path.is_file())
        self.assertTrue(self.synthesis_role_path.is_file())
        for name in (
            "scan_docs.py",
            "validate_docs_review.py",
            "prepare_closure_audit.py",
            "validate_closure_audit.py",
            "merge_closure_audits.py",
        ):
            self.assertTrue((SKILL_ROOT / "scripts" / name).is_file(), name)
        self.assertIn("independent-closure-synthesizer.md", self.skill)

    def test_dispatch_is_always_exactly_two_fields(self) -> None:
        for text in (self.skill, self.interaction, self.shard_role, self.synthesis_role):
            self.assertIn("exactly two top-level fields", " ".join(text.split()))
            self.assertIn("role_file:", text)
            self.assertIn("verification_clauses:", text)
        self.assertIn("must not add role instructions", self.skill)

    def test_roles_require_honest_main_agent_error_reporting(self) -> None:
        self.assertIn("report those errors and omissions honestly", self.shard_role)
        self.assertIn("Report the main Agent's errors and omissions honestly", self.synthesis_role)
        self.assertIn("why_main_agent_is_wrong_or_incomplete", self.shard_role)
        self.assertIn("Never repair a finding", self.shard_role)
        self.assertIn("read-only", self.synthesis_role)

    def test_plan_gate_is_schema_v3_and_scanner_v5(self) -> None:
        self.assertIn("plan_schema_version: 3", self.skill)
        self.assertIn('"plan_schema_version": 3', self.interaction)
        self.assertIn('"schema_version": 5', self.interaction)
        self.assertIn("--phase plan", self.skill)
        self.assertIn("source_fingerprint", self.interaction)
        self.assertIn("resolution_groups", self.interaction)
        self.assertIn("audit_scope_manifest", self.interaction)
        self.assertIn("edit_contracts", self.interaction)
        self.assertIn("--plan-file <temporary-plan-v3.json>", self.skill)

    def test_edit_promises_have_structured_postconditions(self) -> None:
        for marker in (
            "claim_transfer",
            "semantic_claim",
            "path_rewrite",
            "literal_absent",
            "lifecycle_move",
            "path_present",
            "path_absent",
        ):
            self.assertIn(marker, self.all_text)
        self.assertIn("active_plan_missing_from_index", (SKILL_ROOT / "scripts" / "scan_docs.py").read_text(encoding="utf-8"))

    def test_machine_protocol_is_not_written_to_business_docs(self) -> None:
        self.assertIn("required_identifiers", self.interaction)
        self.assertIn("semantic_claims", self.interaction)
        self.assertIn("Never add `claim_id: DR-*`", self.interaction)
        self.assertIn("docs_review_protocol_leak", (SKILL_ROOT / "scripts" / "scan_docs.py").read_text(encoding="utf-8"))

    def test_authority_scope_keeps_lifecycle_axes_independent(self) -> None:
        for field in (
            "authority.kind",
            "authority.resolution_id",
            "scope.platforms",
            "scope.environments",
            "scope.subjects",
            "scope.lifecycle_axes",
            "scope.effective_date",
        ):
            self.assertIn(field, self.all_text)
        self.assertIn("Never infer", self.shard_role)
        self.assertIn("migration_applied", self.shard_role)
        self.assertIn("released", self.shard_role)

    def test_sharding_budgets_concurrency_and_oversize_stop_are_explicit(self) -> None:
        self.assertIn("--max-batch-bytes 120000", self.skill)
        self.assertIn("--max-batch-lines 2000", self.skill)
        self.assertIn("waves of at most three", self.skill)
        self.assertIn("concurrency ceiling", self.skill)
        self.assertIn("never a ceiling on total batches", self.skill)
        self.assertIn("Never use the\nthree-agent ceiling to reduce approved coverage", self.reconciliation)
        self.assertIn("oversized_full_read_file", self.skill)
        self.assertIn("belongs to exactly one shard", self.skill)

    def test_raw_report_validation_and_human_gate_are_lossless(self) -> None:
        self.assertIn("exact raw JSON", self.skill)
        self.assertIn("without reconstruction", self.skill)
        self.assertIn("artifact_layer", self.shard_role)
        self.assertIn("effect_class", self.shard_role)
        self.assertIn("P0", self.shard_role)
        self.assertIn("Do not repair in the same audit-failure turn", self.skill)
        self.assertIn("Leave current files unchanged", self.interaction)

    def test_synthesis_is_fresh_and_shards_are_not_fact_authority(self) -> None:
        self.assertIn("Shard reports prove coverage, not business facts", self.interaction)
        self.assertIn("Always run a new synthesis auditor", " ".join(self.skill.split()))
        self.assertIn("Never reuse synthesis", self.reconciliation)
        self.assertIn("reuse_key", self.skill)
        self.assertIn("fresh", self.synthesis_role)

    def test_nonpass_wave_stops_later_dispatches(self) -> None:
        compact = " ".join(self.skill.split())
        self.assertIn("do not schedule another wave", compact)
        self.assertIn("list undispatched batches as not run", compact)


if __name__ == "__main__":
    unittest.main()
