from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCAN_SCRIPT = SCRIPTS_DIR / "scan_docs.py"


class ScanDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        (self.repo / "docs").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_scan(self, *extra: str) -> tuple[int, dict]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCAN_SCRIPT),
                "--repo-root",
                str(self.repo),
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def finding_types(self, payload: dict) -> set[str]:
        return {finding["type"] for finding in payload["findings"]}

    def test_clean_docs_exit_zero(self) -> None:
        self.write("docs/README.md", "# Docs\n\nCurrent project documentation.\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertEqual(payload["summary"]["findings"], 0)
        self.assertEqual(payload["scanner_manifest"]["schema_version"], 5)
        self.assertRegex(payload["scanner_manifest"]["scanner_sha256"], r"^[0-9a-f]{64}$")

    def test_broken_internal_link_exit_one(self) -> None:
        self.write("docs/README.md", "# Docs\n\n[Missing](missing.md)\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("broken_internal_link", self.finding_types(payload))

    def test_header_date_earlier_than_body_event(self) -> None:
        self.write(
            "docs/handoff/latest.md",
            "# Handoff\n\n> 最后更新时间：2026-01-03\n\n2026-02-04 完成阶段切换。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("stale_header_date", self.finding_types(payload))

    def test_current_state_candidate_candidate(self) -> None:
        self.write(
            "docs/product/current-state.md",
            "# Current\n\n候选方案：未来可能自动定位。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("current_state_candidate", self.finding_types(payload))

    def test_domain_doc_runtime_status_candidate(self) -> None:
        self.write(
            "docs/architecture/domain-boundaries.md",
            "# Contract\n\nThe migration is deployed in production.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("domain_runtime_status", self.finding_types(payload))

    def test_active_plan_completion_candidate(self) -> None:
        self.write(
            "docs/plans/active/location.md",
            "# Location\n\nStatus: human_accepted.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("active_plan_completion", self.finding_types(payload))

    def test_completed_plan_unscoped_active_status_is_reported(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n> 当前阶段：completed\n\n当前仍在 active 中，等待人工验收。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("completed_plan_stale_lifecycle", self.finding_types(payload))

    def test_completed_plan_explicit_historical_status_is_not_reported(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n> 当前阶段：completed\n\n历史快照：当前仍在 active 中，等待人工验收。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("completed_plan_stale_lifecycle", self.finding_types(payload))

    def test_completed_plan_header_disclaimer_does_not_hide_stale_body(self) -> None:
        self.write(
            "docs/plans/completed/community.md",
            "# Community\n\n"
            "> 以下正文均为归档历史，不代表当前状态。\n\n"
            "## Implementation\n\n"
            "当前状态：数据库迁移仍是候选，需要 apply 061/062。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        types = self.finding_types(payload)
        self.assertIn("completed_plan_stale_lifecycle", types)
        self.assertIn("completed_plan_header_only_archive_overlay", types)

    def test_completed_plan_historical_heading_scopes_retained_snapshot(self) -> None:
        self.write(
            "docs/plans/completed/community.md",
            "# Community\n\n"
            "## 历史快照（截至 2026-03-17）\n\n"
            "当前状态：数据库迁移仍是候选，需要 apply 061/062。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("completed_plan_stale_lifecycle", self.finding_types(payload))

    def test_completed_plan_phase_heading_scopes_execution_history(self) -> None:
        self.write(
            "docs/plans/completed/community.md",
            "# Community\n\n"
            "## Round 2 candidate implementation（2026-03-17）\n\n"
            "Candidate implementation was pending apply during this round.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("completed_plan_stale_lifecycle", self.finding_types(payload))

    def test_historical_document_title_does_not_scope_all_later_sections(self) -> None:
        self.write(
            "docs/plans/completed/community.md",
            "# Historical community plan\n\n"
            "## Current status\n\n"
            "Candidate migration is pending apply.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("completed_plan_stale_lifecycle", self.finding_types(payload))

    def test_navigation_like_inline_path_is_checked(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n> 推荐下一跳：`plans/active/location.md`\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        types = self.finding_types(payload)
        self.assertIn("broken_navigation_path", types)
        self.assertIn("completed_plan_active_navigation", types)

    def test_existing_navigation_like_inline_path_is_accepted(self) -> None:
        self.write("docs/product/current-state.md", "# Current\n\nStable fact.\n")
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n> 推荐下一跳：`../../product/current-state.md`\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("broken_navigation_path", self.finding_types(payload))

    def test_bare_markdown_filename_in_navigation_is_checked(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n> 推荐下一跳：`missing-current-contract.md`\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("broken_navigation_path", self.finding_types(payload))

    def test_missing_non_markdown_navigation_directory_is_checked(self) -> None:
        self.write(
            "docs/handoff/latest.md",
            "# Handoff\n\n设计源入口：`design/v2/secondary/`\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("broken_navigation_path", self.finding_types(payload))

    def test_bare_markdown_filename_without_navigation_hint_is_checked(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\nCanonical owner: `missing-current-contract.md`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("broken_inline_markdown_reference", self.finding_types(payload))

    def test_markdown_path_template_or_glob_is_not_treated_as_a_live_reference(self) -> None:
        self.write(
            "docs/template.md",
            "# Template\n\nUse `docs/evidence/<feature>-audit.md` or `contracts/*.md`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("broken_inline_markdown_reference", self.finding_types(payload))

    def test_machine_specific_absolute_inline_path_is_reported(self) -> None:
        self.write(
            "docs/plans/completed/design.md",
            "# Design\n\nHistorical source: `/Users/example/Desktop/project/prototype.html`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("machine_specific_absolute_path", self.finding_types(payload))
        self.assertEqual(payload["summary"]["machine_specific_paths"], 1)

    def test_missing_explicit_repository_glob_prefix_is_reported(self) -> None:
        self.write(
            "docs/architecture/system-map.md",
            "# Map\n\nPublished contracts came from `docs/legal/*` drafts.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("missing_repository_path_reference", self.finding_types(payload))

    def test_existing_explicit_repository_glob_prefix_is_accepted(self) -> None:
        self.write("src/privacy/contracts/privacy.md", "# Privacy\n")
        self.write(
            "docs/architecture/system-map.md",
            "# Map\n\nPublished contracts are in `src/privacy/contracts/*.md`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("missing_repository_path_reference", self.finding_types(payload))

    def test_docs_index_missing_directory_is_reported(self) -> None:
        self.write("docs/architecture/current.md", "# Current\n")
        self.write(
            "docs/README.md",
            "# Docs\n\n- `architecture/`\n- `legal/`\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        findings = [
            item for item in payload["findings"]
            if item["type"] == "missing_docs_index_directory"
        ]
        self.assertEqual([item["evidence"]["raw"] for item in findings], ["legal/"])

    def test_docs_index_repo_prefixed_directory_is_resolved_from_repo_root(self) -> None:
        self.write("docs/workflow/current.md", "# Current\n")
        self.write(
            "docs/README.md",
            "# Docs\n\nScope: `docs/`; maintenance: `docs/workflow/`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("missing_docs_index_directory", self.finding_types(payload))

    def test_explicit_historical_inline_path_is_not_treated_as_navigation(self) -> None:
        self.write(
            "docs/plans/completed/location.md",
            "# Location\n\n历史下一步（非存活路径）：`plans/active/location.md`。\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("broken_navigation_path", self.finding_types(payload))

    def test_frozen_release_scope_requires_active_plan_classification(self) -> None:
        self.write(
            "docs/product/current-state.md",
            "# Current\n\n首版功能范围已冻结。\n",
        )
        self.write("docs/plans/active/feature.md", "# Feature\n\nStill in progress.\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        types = self.finding_types(payload)
        self.assertIn("active_plan_release_scope_missing", types)
        self.assertIn("active_plan_release_blocking_missing", types)

    def test_frozen_release_scope_accepts_explicit_active_plan_classification(self) -> None:
        self.write(
            "docs/product/current-state.md",
            "# Current\n\n首版功能范围已冻结。\n",
        )
        self.write(
            "docs/plans/active/feature.md",
            "# Feature\n\n> release_scope: post_release\n> release_blocking: false\n",
        )
        self.write(
            "docs/plans/active/README.md",
            "# Active\n\n- [Feature](feature.md)\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("active_plan_release_scope_missing", self.finding_types(payload))

    def test_active_plan_missing_from_index_is_reported(self) -> None:
        self.write("docs/plans/active/README.md", "# Active\n\n- [Launch](launch.md)\n")
        self.write("docs/plans/active/launch.md", "# Launch\n\nIn progress.\n")
        self.write("docs/plans/active/delivery.md", "# Delivery\n\nIn progress.\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        findings = [
            item for item in payload["findings"]
            if item["type"] == "active_plan_missing_from_index"
        ]
        self.assertEqual(
            [item["evidence"]["active_plan"] for item in findings],
            ["docs/plans/active/delivery.md"],
        )

    def test_active_plan_singleton_claim_is_checked_against_directory(self) -> None:
        self.write(
            "docs/plans/active/README.md",
            "# Active\n\n- [Launch](launch.md)：唯一 active 计划。\n",
        )
        self.write("docs/plans/active/launch.md", "# Launch\n\nIn progress.\n")
        self.write("docs/plans/active/delivery.md", "# Delivery\n\nIn progress.\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("active_plan_count_contradiction", self.finding_types(payload))

    def test_active_plans_require_an_index(self) -> None:
        self.write("docs/plans/active/feature.md", "# Feature\n\nIn progress.\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("active_plan_index_missing", self.finding_types(payload))

    def test_lifecycle_status_indirection_is_reported(self) -> None:
        self.write(
            "docs/plans/active/launch.md",
            "# Launch\n\n| feature | migration_applied |\n|---|---|\n| map | 按 evidence 独立读取 |\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("lifecycle_status_indirection", self.finding_types(payload))

    def test_semantic_metrics_count_inline_path_anchors(self) -> None:
        self.write(
            "docs/architecture/system-map.md",
            "# Map\n\n- `src/pages/a.vue` uses `src/services/a.ts`.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertEqual(
            payload["inventory"][0]["semantic_metrics"]["path_reference_count"], 2
        )

    def test_duplicate_normalized_paragraph(self) -> None:
        paragraph = (
            "This deliberately long project fact is repeated in two documents so the "
            "deterministic review scanner can identify a normalized duplicate candidate."
        )
        self.write("docs/a.md", f"# A\n\n{paragraph}\n")
        self.write("docs/b.md", f"# B\n\n{paragraph}\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("duplicate_normalized_block", self.finding_types(payload))
        self.assertEqual(len(payload["signals"]["duplicate_blocks"]), 1)

    def test_duplicate_markdown_table_is_reported(self) -> None:
        table = (
            "| route | owner | status |\n"
            "|---|---|---|\n"
            "| booking/create | booking | current |\n"
            "| booking/detail | booking | current |\n"
            "| community/list | community | current |\n"
            "| community/detail | community | current |\n"
        )
        self.write("docs/a.md", f"# A\n\n{table}")
        self.write("docs/b.md", f"# B\n\n{table}")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        duplicates = payload["signals"]["duplicate_blocks"]
        self.assertTrue(
            any(item.get("match_kind") == "exact_normalized" for item in duplicates)
        )

    def test_near_duplicate_markdown_table_is_reported(self) -> None:
        rows = [
            "| route | owner | status |",
            "|---|---|---|",
            "| booking/create | booking | current |",
            "| booking/detail | booking | current |",
            "| community/list | community | current |",
            "| community/detail | community | current |",
            "| profile/index | account | current |",
        ]
        self.write("docs/a.md", "# A\n\n" + "\n".join(rows) + "\n")
        changed = rows[:-1] + ["| profile/index | identity | current |"]
        self.write("docs/b.md", "# B\n\n" + "\n".join(changed) + "\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        self.assertIn("duplicate_near_table_block", self.finding_types(payload))

    def test_findings_have_stable_machine_keys(self) -> None:
        self.write("docs/README.md", "# Docs\n\n[Missing](missing.md)\n")
        _, first = self.run_scan()
        self.write("docs/README.md", "\n# Docs\n\n[Missing](missing.md)\n")
        _, second = self.run_scan()
        self.assertEqual(
            first["findings"][0]["finding_key"], second["findings"][0]["finding_key"]
        )

    def test_finding_has_source_fingerprint_and_local_section(self) -> None:
        self.write(
            "docs/README.md",
            "# Docs\n\n## Navigation\n\n[Missing](missing.md)\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        finding = payload["findings"][0]
        self.assertRegex(finding["source_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertEqual(finding["section"]["heading"], "Navigation")
        self.assertEqual(finding["section"]["heading_line"], 3)

    def test_docs_review_protocol_leak_is_reported(self) -> None:
        self.write(
            "docs/current.md",
            "# Current\n\n稳定锚点：地图状态\n\nstable anchor: booking state\n\nclaim_id: DR-LOCATION-001\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 1)
        leaks = [
            item
            for item in payload["findings"]
            if item["type"] == "docs_review_protocol_leak"
        ]
        self.assertEqual(len(leaks), 3)

    def test_docs_review_protocol_examples_in_fence_are_ignored(self) -> None:
        self.write(
            "docs/example.md",
            "# Example\n\n```json\n{\"claim_id\": \"DR-EXAMPLE\"}\n```\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertNotIn("docs_review_protocol_leak", self.finding_types(payload))

    def test_long_bullet_candidate_is_reported_as_signal(self) -> None:
        bullet = (
            "This intentionally long bullet carries a complete project claim with enough "
            "detail to be considered for cross-document duplicate reconciliation."
        )
        self.write("docs/long.md", f"# Long\n\n- {bullet}\n")
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        self.assertEqual(payload["signals"]["long_bullets"][0]["kind"], "long_bullet")

    def test_platform_markers_are_signals_not_truth(self) -> None:
        self.write(
            "docs/platforms.md",
            "# Platforms\n\nH5 uses one entry; mp-weixin uses another; shared behavior is undecided.\n",
        )
        code, payload = self.run_scan()
        self.assertEqual(code, 0)
        terms = {item["term"] for item in payload["signals"]["platform_terms"]}
        self.assertTrue({"H5", "mp-weixin", "shared"}.issubset(terms))

    def test_unicode_path(self) -> None:
        self.write("docs/业务/定位说明.md", "# 定位\n\n这是当前说明。\n")
        code, payload = self.run_scan("--scope", "docs/业务")
        self.assertEqual(code, 0)
        self.assertEqual(payload["inventory"][0]["path"], "docs/业务/定位说明.md")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support is required")
    def test_symlink_escape_is_rejected_with_exit_two(self) -> None:
        outside = self.repo / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        os.symlink(outside, self.repo / "docs" / "escape.md")
        code, payload = self.run_scan()
        self.assertEqual(code, 2)
        self.assertEqual(payload["summary"]["errors"], 1)
        self.assertIn("symlink escapes docs root", payload["errors"][0]["message"])

    def test_scope_does_not_read_sibling(self) -> None:
        self.write("docs/booking/current.md", "# Booking\n\nCurrent booking facts.\n")
        self.write("docs/payments/broken.md", "# Payments\n\n[Missing](missing.md)\n")
        code, payload = self.run_scan("--scope", "booking")
        self.assertEqual(code, 0)
        self.assertEqual(
            [item["path"] for item in payload["inventory"]], ["docs/booking/current.md"]
        )

    def test_invalid_scope_exit_two(self) -> None:
        self.write("docs/README.md", "# Docs\n")
        code, payload = self.run_scan("--scope", "../outside")
        self.assertEqual(code, 2)
        self.assertTrue(payload["errors"])


if __name__ == "__main__":
    unittest.main()
