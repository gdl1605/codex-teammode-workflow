from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_docs_review.py"
SCAN_SCRIPT = SCRIPTS_DIR / "scan_docs.py"
SCANNER_SHA256 = hashlib.sha256(SCAN_SCRIPT.read_bytes()).hexdigest()


class ValidateDocsReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        (self.repo / "docs").mkdir()
        self.doc = self.repo / "docs" / "current.md"
        self.doc.write_text("# Current\n\nStable fact.\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_scan(self) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCAN_SCRIPT), "--repo-root", str(self.repo)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def claim(
        self,
        claim_id: str = "DR-001",
        *,
        resolution: str = "resolved",
        axes: list[str] | None = None,
        environments: list[str] | None = None,
        subjects: list[str] | None = None,
        authority_kind: str = "repository_evidence",
        resolution_id: str = "REPO-001",
    ) -> dict:
        return {
            "claim_id": claim_id,
            "claim_type": "documentation_fact",
            "resolution": resolution,
            "risk": "medium",
            "authority": {
                "kind": authority_kind,
                "resolution_id": resolution_id,
            },
            "scope": {
                "platforms": ["shared"],
                "environments": environments if environments is not None else ["repository"],
                "subjects": subjects if subjects is not None else ["docs/current.md"],
                "lifecycle_axes": axes if axes is not None else [],
                "effective_date": "2026-08-04",
            },
        }

    def evidence_group(
        self,
        claim_id: str = "DR-001",
        *,
        intended_semantics: str = "The broken reference is intentionally retained as a bounded fixture.",
        group_id: str = "DRG-001",
        target: str = "docs/current.md",
    ) -> dict:
        return {
            "group_id": group_id,
            "claim_id": claim_id,
            "subject": "current documentation reference",
            "intended_semantics": intended_semantics,
            "basis": {
                "kind": "repository_evidence",
                "references": [
                    {
                        "path": "docs/current.md",
                        "sha256": self.digest(self.doc),
                        "proves": "The exact current fixture text and link target declaration.",
                    }
                ],
            },
            "target_docs": [target],
        }

    def disposition(
        self,
        source: dict,
        *,
        value: str = "false_positive",
        group_id: str = "DRG-001",
        **extra: object,
    ) -> dict:
        entry = {
            "finding_key": source["finding_key"],
            "source_fingerprint": source["source_fingerprint"],
            "disposition": value,
            "group_id": group_id,
            "expected_post_state": "absent" if value == "resolve_by_edit" else "present",
        }
        if value == "false_positive":
            entry["reason_code"] = "bounded_scope_exception"
        entry.update(extra)
        return entry

    def write_plan(
        self,
        *,
        baseline_manifest: dict[str, str] | None = None,
        approved: list[str] | None = None,
        claims: list[dict] | None = None,
        groups: list[dict] | None = None,
        coverage: dict[str, dict] | None = None,
        dispositions: list[dict] | None = None,
        scanner_manifest: dict | None = None,
        audit_scope_manifest: dict[str, dict] | None = None,
        edit_contracts: list[dict] | None = None,
        verdict: str = "consistent",
        schema: int = 3,
        decision_complete: bool = True,
    ) -> Path:
        approved_files = approved if approved is not None else ["docs/current.md"]
        disposition_entries = dispositions if dispositions is not None else []
        group_ids = sorted(
            {
                entry.get("group_id")
                for entry in disposition_entries
                if entry.get("disposition") == "resolve_by_edit"
                and isinstance(entry.get("group_id"), str)
            }
        )
        if audit_scope_manifest is None:
            inventory_paths = {
                item["path"] for item in self.run_scan().get("inventory", [])
            }
            audit_scope_manifest = {
                path: {
                    "baseline_state": "present" if path in inventory_paths else "absent",
                    "post_state": "present",
                }
                for path in sorted(inventory_paths | set(approved_files))
            }
        if edit_contracts is None:
            edit_contracts = [
                {
                    "edit_id": "DRE-TEST-001",
                    "kind": "content_rewrite",
                    "source_files": approved_files,
                    "target_files": approved_files,
                    "group_ids": group_ids,
                    "postconditions": [
                        {
                            "kind": "path_present",
                            "path": path,
                            "reason": "The approved test document remains present.",
                        }
                        for path in approved_files
                    ],
                }
            ]
        plan = {
            "plan_schema_version": schema,
            "decision_complete": decision_complete,
            "scanner_manifest": scanner_manifest
            if scanner_manifest is not None
            else {"schema_version": 5, "scanner_sha256": SCANNER_SHA256},
            "baseline_manifest": baseline_manifest
            if baseline_manifest is not None
            else {"docs/current.md": self.digest(self.doc)},
            "approved_files": approved_files,
            "claims": claims if claims is not None else [],
            "resolution_groups": groups if groups is not None else [],
            "finding_dispositions": disposition_entries,
            "coverage_manifest": coverage if coverage is not None else {},
            "audit_scope_manifest": audit_scope_manifest,
            "edit_contracts": edit_contracts,
            "verdict": verdict,
        }
        path = self.repo / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def run_validate(self, *extra: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "--repo-root", str(self.repo), *extra],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    @staticmethod
    def types(payload: dict) -> set[str]:
        return {item["type"] for item in payload["findings"]}

    def test_plan_phase_matching_baseline_exit_zero(self) -> None:
        plan = self.write_plan()
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 0)
        self.assertEqual(payload["plan_schema_version"], 3)

    def test_v1_plan_is_rejected(self) -> None:
        plan = self.write_plan(schema=1)
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("unsupported_plan_schema", self.types(payload))

    def test_plan_must_be_decision_complete(self) -> None:
        plan = self.write_plan(decision_complete=False)
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("plan_not_decision_complete", self.types(payload))

    def test_scanner_drift_exit_one(self) -> None:
        plan = self.write_plan(scanner_manifest={"schema_version": 5, "scanner_sha256": "0" * 64})
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("scanner_drift", self.types(payload))

    def test_pre_apply_baseline_drift_exit_one(self) -> None:
        plan = self.write_plan(baseline_manifest={"docs/current.md": "0" * 64})
        code, payload = self.run_validate("--phase", "pre-apply", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("baseline_drift", self.types(payload))

    def test_post_apply_rejects_changed_file_outside_approved_list(self) -> None:
        extra = self.repo / "docs" / "extra.md"
        extra.write_text("# Extra\n", encoding="utf-8")
        plan = self.write_plan()
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan), "--changed-file", "docs/extra.md"
        )
        self.assertEqual(code, 1)
        self.assertIn("changed_file_outside_approved_list", self.types(payload))

    def test_post_apply_clean_approved_change_exit_zero(self) -> None:
        plan = self.write_plan()
        self.doc.write_text("# Current\n\nCorrected stable fact.\n", encoding="utf-8")
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan), "--changed-file", "docs/current.md"
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["changed_files"], ["docs/current.md"])

    def test_audit_scope_manifest_must_cover_every_scanned_markdown_file(self) -> None:
        (self.repo / "docs" / "neighbor.md").write_text("# Neighbor\n", encoding="utf-8")
        plan = self.write_plan(
            audit_scope_manifest={
                "docs/current.md": {"baseline_state": "present", "post_state": "present"}
            }
        )
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("audit_scope_inventory_omission", self.types(payload))

    def test_literal_absent_postcondition_blocks_unfinished_path_rewrite(self) -> None:
        self.doc.write_text(
            "# Current\n\nSource: `/Users/example/Desktop/project/prototype.html`.\n",
            encoding="utf-8",
        )
        source = self.run_scan()["findings"][0]
        claim = self.claim()
        group = self.evidence_group(
            intended_semantics="The machine-specific prototype path is retained only in this negative fixture."
        )
        plan = self.write_plan(
            claims=[claim],
            groups=[group],
            dispositions=[self.disposition(source)],
            edit_contracts=[
                {
                    "edit_id": "DRE-PATH-001",
                    "kind": "path_rewrite",
                    "source_files": ["docs/current.md"],
                    "target_files": ["docs/current.md"],
                    "group_ids": [],
                    "postconditions": [
                        {
                            "kind": "literal_absent",
                            "path": "docs/current.md",
                            "value": "/Users/example/Desktop/project/",
                            "reason": "Portable docs must not retain a developer-machine prefix.",
                        }
                    ],
                }
            ],
        )
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan),
            "--changed-file", "docs/current.md",
        )
        self.assertEqual(code, 1)
        self.assertIn("edit_postcondition_failed", self.types(payload))

    def test_claim_transfer_postcondition_requires_subject_markers_at_owner(self) -> None:
        source = self.repo / "docs" / "source.md"
        target = self.repo / "docs" / "product" / "current-state.md"
        source.write_text("# Source\n\nUGC hosted status moves to current-state.\n", encoding="utf-8")
        target.parent.mkdir(parents=True)
        target.write_text("# Current\n\nNo hosted details yet.\n", encoding="utf-8")
        scan = self.run_scan()
        source_item = next(item for item in scan["inventory"] if item["path"] == "docs/source.md")
        target_item = next(item for item in scan["inventory"] if item["path"] == "docs/product/current-state.md")
        claim = self.claim(claim_id="DR-UGC-001", subjects=["ugc-content-submit"])
        group = self.evidence_group(
            claim_id="DR-UGC-001",
            group_id="DRG-UGC-001",
            target="docs/product/current-state.md",
            intended_semantics="Current-state owns the exact UGC hosted lifecycle boundary.",
        )
        group["basis"]["references"] = [
            {
                "path": "docs/source.md",
                "sha256": self.digest(source),
                "proves": "The source delegates the UGC hosted lifecycle boundary.",
            }
        ]
        coverage = {
            "docs/source.md": {
                "baseline": source_item["semantic_metrics"],
                "required_identifiers": [],
                "semantic_claims": [],
                "removed_claims": [
                    {
                        "claim_id": "DR-UGC-001",
                        "disposition": "moved",
                        "destination": "docs/product/current-state.md",
                    }
                ],
                "allow_major_reduction": False,
            },
            "docs/product/current-state.md": {
                "baseline": target_item["semantic_metrics"],
                "required_identifiers": [],
                "semantic_claims": [
                    {
                        "claim_id": "DR-UGC-001",
                        "meaning": "Current-state owns the exact UGC hosted lifecycle boundary.",
                        "owner": "docs/product/current-state.md",
                    }
                ],
                "removed_claims": [],
                "allow_major_reduction": False,
            }
        }
        plan = self.write_plan(
            baseline_manifest={
                "docs/source.md": self.digest(source),
                "docs/product/current-state.md": self.digest(target),
            },
            approved=["docs/source.md", "docs/product/current-state.md"],
            claims=[claim],
            groups=[group],
            coverage=coverage,
            edit_contracts=[
                {
                    "edit_id": "DRE-TRANSFER-001",
                    "kind": "claim_transfer",
                    "source_files": ["docs/source.md"],
                    "target_files": ["docs/product/current-state.md"],
                    "group_ids": ["DRG-UGC-001"],
                    "postconditions": [
                        {
                            "kind": "semantic_claim",
                            "path": "docs/product/current-state.md",
                            "claim_id": "DR-UGC-001",
                            "markers": ["ugc-content-submit"],
                            "reason": "The destination must visibly receive the transferred subject.",
                        }
                    ],
                }
            ],
        )
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan),
            "--changed-file", "docs/product/current-state.md",
        )
        self.assertEqual(code, 1)
        self.assertIn("semantic_postcondition_failed", self.types(payload))

    def test_moved_claim_cannot_be_disguised_as_content_rewrite(self) -> None:
        source = self.repo / "docs" / "source.md"
        target = self.repo / "docs" / "product" / "current-state.md"
        source.write_text("# Source\n\nUGC ownership moves out.\n", encoding="utf-8")
        target.parent.mkdir(parents=True)
        target.write_text("# Current\n\nUGC owner.\n", encoding="utf-8")
        inventory = {item["path"]: item for item in self.run_scan()["inventory"]}
        coverage = {
            "docs/source.md": {
                "baseline": inventory["docs/source.md"]["semantic_metrics"],
                "required_identifiers": [],
                "semantic_claims": [],
                "removed_claims": [
                    {
                        "claim_id": "DR-UGC-001",
                        "disposition": "moved",
                        "destination": "docs/product/current-state.md",
                    }
                ],
                "allow_major_reduction": False,
            },
            "docs/product/current-state.md": {
                "baseline": inventory["docs/product/current-state.md"]["semantic_metrics"],
                "required_identifiers": [],
                "semantic_claims": [
                    {
                        "claim_id": "DR-UGC-001",
                        "meaning": "Current-state owns UGC runtime status.",
                        "owner": "docs/product/current-state.md",
                    }
                ],
                "removed_claims": [],
                "allow_major_reduction": False,
            },
        }
        plan = self.write_plan(
            baseline_manifest={
                "docs/source.md": self.digest(source),
                "docs/product/current-state.md": self.digest(target),
            },
            approved=["docs/source.md", "docs/product/current-state.md"],
            claims=[self.claim(claim_id="DR-UGC-001", subjects=["ugc-content-submit"])],
            coverage=coverage,
            edit_contracts=[
                {
                    "edit_id": "DRE-WRONG-KIND",
                    "kind": "content_rewrite",
                    "source_files": ["docs/source.md"],
                    "target_files": ["docs/product/current-state.md"],
                    "group_ids": [],
                    "postconditions": [
                        {
                            "kind": "path_present",
                            "path": "docs/product/current-state.md",
                            "reason": "Insufficient existence-only assertion.",
                        }
                    ],
                }
            ],
        )
        code, payload = self.run_validate(
            "--phase", "plan", "--plan-file", str(plan)
        )
        self.assertEqual(code, 1)
        self.assertIn("moved_claim_without_transfer_contract", self.types(payload))

    def test_plan_requires_one_disposition_per_scanner_finding(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        plan = self.write_plan()
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("scan_finding_without_disposition", self.types(payload))

    def test_structured_false_positive_passes_plan_gate(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        claim = self.claim()
        group = self.evidence_group()
        plan = self.write_plan(claims=[claim], groups=[group], dispositions=[self.disposition(source)])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 0, payload["findings"])

    def test_disposition_source_fingerprint_must_match(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        disposition = self.disposition(source)
        disposition["source_fingerprint"] = "0" * 64
        plan = self.write_plan(claims=[self.claim()], groups=[self.evidence_group()], dispositions=[disposition])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("finding_source_fingerprint_mismatch", self.types(payload))

    def test_template_semantics_cannot_close_resolution_group(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        group = self.evidence_group(intended_semantics="处理该类型")
        plan = self.write_plan(claims=[self.claim()], groups=[group], dispositions=[self.disposition(source)])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("resolution_group_semantics_missing", self.types(payload))

    def test_long_occurrence_template_cannot_close_resolution_group(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        group = self.evidence_group(
            intended_semantics="Handle this broken-link finding occurrence in the approved document according to the cleanup plan."
        )
        plan = self.write_plan(claims=[self.claim()], groups=[group], dispositions=[self.disposition(source)])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("resolution_group_semantics_missing", self.types(payload))

    def test_resolution_group_without_evidence_fails(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        group = self.evidence_group()
        group["basis"]["references"] = []
        plan = self.write_plan(claims=[self.claim()], groups=[group], dispositions=[self.disposition(source)])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("resolution_group_evidence_missing", self.types(payload))

    def test_migration_confirmation_requires_exact_environment_and_subject(self) -> None:
        claim = self.claim(
            axes=["migration_applied"],
            environments=[],
            subjects=["community migrations"],
        )
        plan = self.write_plan(claims=[claim])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertTrue(
            {"environment_bound_fact_is_ambiguous", "migration_subject_is_ambiguous"}.issubset(self.types(payload))
        )

    def test_human_resolution_must_match_claim_authority(self) -> None:
        claim = self.claim(authority_kind="human_resolution", resolution_id="USER-001")
        group = self.evidence_group()
        group["basis"] = {"kind": "human_resolution", "resolution_id": "USER-OTHER", "references": []}
        plan = self.write_plan(claims=[claim], groups=[group])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("human_resolution_authority_mismatch", self.types(payload))

    def test_verified_historical_binds_nearest_dated_heading(self) -> None:
        self.doc.write_text(
            "# Current\n\n## 历史快照（截至 2026-03-17）\n\n[Missing](missing.md)\n",
            encoding="utf-8",
        )
        source = self.run_scan()["findings"][0]
        disposition = self.disposition(
            source,
            value="verified_historical",
            historical_scope={
                "kind": "dated_heading",
                "path": "docs/current.md",
                "line": 3,
                "date": "2026-03-17",
                "marker": "历史快照",
            },
        )
        plan = self.write_plan(claims=[self.claim()], groups=[self.evidence_group()], dispositions=[disposition])
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 0, payload["findings"])

    def test_resolve_by_edit_must_disappear_post_apply(self) -> None:
        self.doc.write_text("# Current\n\n[Missing](missing.md)\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        group = self.evidence_group(intended_semantics="The invalid internal link is removed from the current document.")
        plan = self.write_plan(
            claims=[self.claim()], groups=[group], dispositions=[self.disposition(source, value="resolve_by_edit")]
        )
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan), "--changed-file", "docs/current.md"
        )
        self.assertEqual(code, 1)
        self.assertIn("scan_finding_not_resolved", self.types(payload))

    def test_retain_unresolved_uses_business_language_not_claim_id(self) -> None:
        marker = "The target of this navigation remains unknown and requires product confirmation."
        self.doc.write_text(f"# Current\n\n[Missing](missing.md)\n\n{marker}\n", encoding="utf-8")
        source = self.run_scan()["findings"][0]
        claim = self.claim(
            resolution="unresolved",
            authority_kind="unresolved",
            resolution_id="UNRESOLVED-001",
        )
        group = self.evidence_group(intended_semantics="The unresolved navigation target remains explicit for product confirmation.")
        group["basis"] = {"kind": "unresolved_claim", "references": []}
        disposition = self.disposition(
            source,
            value="retain_unresolved",
            unresolved_claim_id="DR-001",
            business_gap={"path": "docs/current.md", "marker": marker},
        )
        plan = self.write_plan(
            claims=[claim], groups=[group], dispositions=[disposition], verdict="partially_consistent"
        )
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan), "--changed-file", "docs/current.md"
        )
        self.assertEqual(code, 0, payload["findings"])

    def canonical_fixture(self) -> tuple[Path, str, dict]:
        canonical = self.repo / "docs" / "architecture" / "system-map.md"
        canonical.parent.mkdir(parents=True)
        canonical.write_text("# Map\n\nField `booking.quoteCents` is current.\n", encoding="utf-8")
        scan = self.run_scan()
        item = next(entry for entry in scan["inventory"] if entry["path"] == "docs/architecture/system-map.md")
        path = "docs/architecture/system-map.md"
        coverage = {
            path: {
                "baseline": item["semantic_metrics"],
                "required_identifiers": [
                    {"kind": "field", "value": "booking.quoteCents", "reason": "Current booking amount contract."}
                ],
                "semantic_claims": [
                    {"claim_id": "DR-CANONICAL-001", "meaning": "Booking records expose one exact quote amount.", "owner": path}
                ],
                "removed_claims": [],
                "allow_major_reduction": False,
            }
        }
        return canonical, path, coverage

    def test_canonical_coverage_accepts_technical_identifier_and_semantic_claim(self) -> None:
        canonical, path, coverage = self.canonical_fixture()
        plan = self.write_plan(
            baseline_manifest={path: self.digest(canonical)}, approved=[path], coverage=coverage
        )
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 0, payload["findings"])

    def test_doc_path_identifier_accepts_plain_spaces(self) -> None:
        canonical, path, coverage = self.canonical_fixture()
        coverage[path]["required_identifiers"] = [
            {
                "kind": "doc_path",
                "value": "historical design files/specs/01-home.md",
                "reason": "Preserve an exact historical source identity.",
            }
        ]
        plan = self.write_plan(
            baseline_manifest={path: self.digest(canonical)}, approved=[path], coverage=coverage
        )
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 0, payload["findings"])

    def test_doc_path_identifier_rejects_non_space_whitespace(self) -> None:
        canonical, path, coverage = self.canonical_fixture()
        coverage[path]["required_identifiers"] = [
            {
                "kind": "doc_path",
                "value": "historical\tdesign/spec.md",
                "reason": "Invalid control whitespace must not enter a literal path.",
            }
        ]
        plan = self.write_plan(
            baseline_manifest={path: self.digest(canonical)}, approved=[path], coverage=coverage
        )
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("invalid_required_identifier", self.types(payload))

    def test_natural_language_is_not_a_required_identifier(self) -> None:
        canonical, path, coverage = self.canonical_fixture()
        coverage[path]["required_identifiers"][0] = {
            "kind": "field",
            "value": "Booking records expose one exact quote amount",
            "reason": "semantic prose",
        }
        plan = self.write_plan(
            baseline_manifest={path: self.digest(canonical)}, approved=[path], coverage=coverage
        )
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 1)
        self.assertIn("invalid_required_identifier", self.types(payload))

    def test_post_apply_missing_required_identifier_fails(self) -> None:
        canonical, path, coverage = self.canonical_fixture()
        plan = self.write_plan(
            baseline_manifest={path: self.digest(canonical)}, approved=[path], coverage=coverage
        )
        canonical.write_text("# Map\n\nThe contract remains documented without a literal field name.\n", encoding="utf-8")
        code, payload = self.run_validate(
            "--phase", "post-apply", "--plan-file", str(plan), "--changed-file", path
        )
        self.assertEqual(code, 1)
        self.assertIn("required_identifier_missing", self.types(payload))

    def test_protocol_text_in_business_docs_is_a_finding(self) -> None:
        self.doc.write_text("# Current\n\n稳定锚点：booking lifecycle\n", encoding="utf-8")
        code, payload = self.run_validate()
        self.assertEqual(code, 1)
        self.assertIn("docs_review_protocol_leak", self.types(payload))

    def test_bad_plan_json_exit_two(self) -> None:
        plan = self.repo / "bad.json"
        plan.write_text("{not-json", encoding="utf-8")
        code, payload = self.run_validate("--phase", "plan", "--plan-file", str(plan))
        self.assertEqual(code, 2)
        self.assertTrue(payload["errors"])


if __name__ == "__main__":
    unittest.main()
