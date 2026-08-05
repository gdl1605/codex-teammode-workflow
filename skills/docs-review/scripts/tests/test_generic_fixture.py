from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCAN_SCRIPT = SCRIPTS_DIR / "scan_docs.py"


class GenericInconsistentFixtureTests(unittest.TestCase):
    def test_fixture_surfaces_generic_project_patterns_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            files = {
                "docs/README.md": "# Docs\n\n[Evidence](evidence/runtime.md)\n",
                "docs/product/current-state.md": (
                    "# Current\n\n首版功能范围已冻结。候选入口与 live IA 共用此处；"
                    "H5 自动定位，mp-weixin 默认只读。\n"
                ),
                "docs/architecture/domain-boundaries.md": (
                    "# Domain\n\nThe location migration is deployed in production.\n"
                ),
                "docs/plans/active/location.md": (
                    "# Location plan\n\nStatus: human_accepted and completed.\n"
                ),
                "docs/plans/completed/visual.md": (
                    "# Visual plan\n\n> 当前阶段：completed\n"
                    "> 以下正文均为归档历史，不代表当前状态。\n"
                    "> 推荐下一跳：`plans/active/visual.md`\n\n"
                    "当前仍在 active 中，等待人工验收。\n"
                ),
                "docs/handoff/latest.md": (
                    "# Handoff\n\n> 最后更新时间：2026-01-01\n\n2026-02-01 状态更新。\n"
                ),
                "docs/contracts/pending.md": (
                    "# Migration\n\nThe migration remains pending and is not proven applied.\n"
                ),
                "docs/contracts/applied.md": (
                    "# Migration\n\nThe same migration is described as migration_applied.\n"
                ),
                "docs/contracts/matrix-a.md": (
                    "# Matrix A\n\n| route | owner | status |\n|---|---|---|\n"
                    "| booking/create | booking | current |\n"
                    "| booking/detail | booking | current |\n"
                    "| community/list | community | current |\n"
                    "| community/detail | community | current |\n"
                ),
                "docs/contracts/matrix-b.md": (
                    "# Matrix B\n\n| route | owner | status |\n|---|---|---|\n"
                    "| booking/create | booking | current |\n"
                    "| booking/detail | booking | current |\n"
                    "| community/list | community | current |\n"
                    "| community/detail | community | current |\n"
                ),
                "src/location.py": "def locate():\n    return 'readonly'\n",
                "tests/test_location.py": "def test_location():\n    assert True\n",
            }
            tracked_hashes: dict[str, str] = {}
            for relative, content in files.items():
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                tracked_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

            result = subprocess.run(
                [sys.executable, str(SCAN_SCRIPT), "--repo-root", str(repo)],
                check=False,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            types = {finding["type"] for finding in payload["findings"]}
            self.assertTrue(
                {
                    "broken_internal_link",
                    "current_state_candidate",
                    "domain_runtime_status",
                    "active_plan_completion",
                    "stale_header_date",
                    "completed_plan_stale_lifecycle",
                    "completed_plan_header_only_archive_overlay",
                    "broken_navigation_path",
                    "completed_plan_active_navigation",
                    "duplicate_normalized_block",
                    "active_plan_release_scope_missing",
                    "active_plan_release_blocking_missing",
                }.issubset(types)
            )
            platform_terms = {item["term"] for item in payload["signals"]["platform_terms"]}
            self.assertTrue({"H5", "mp-weixin"}.issubset(platform_terms))
            status_terms = {item["term"] for item in payload["signals"]["status_terms"]}
            self.assertTrue({"pending", "migration_applied"}.issubset(status_terms))
            inventory = {item["path"] for item in payload["inventory"]}
            self.assertFalse(any(path.startswith("src/") for path in inventory))
            self.assertFalse(any(path.startswith("tests/") for path in inventory))
            for relative, expected_hash in tracked_hashes.items():
                actual_hash = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
                self.assertEqual(actual_hash, expected_hash)


if __name__ == "__main__":
    unittest.main()
