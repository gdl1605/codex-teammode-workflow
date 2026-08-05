from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
INSTALLER = REPO_ROOT / "install.sh"
SKILL_SOURCE = REPO_ROOT / "skills" / "docs-review"


@unittest.skipUnless(INSTALLER.is_file(), "installer test runs only in the workflow source repo")
class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.target = self.root / "target"
        self.target.mkdir()
        self.skill_root = self.root / "skills"
        self.env = os.environ.copy()
        self.env["CODEX_HOME"] = str(self.root / "isolated-codex-home")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_install(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(INSTALLER), *args],
            cwd=REPO_ROOT,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
        )

    def tree_snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(INSTALLER)], check=False, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_prints_only_the_documented_interface(self) -> None:
        result = self.run_install("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--install-docs-review", result.stdout)
        self.assertIn("--force-skill", result.stdout)
        self.assertNotIn("set -euo pipefail", result.stdout)

    def test_default_install_does_not_touch_personal_skill_root(self) -> None:
        result = self.run_install("--no-clipboard", str(self.target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "isolated-codex-home").exists())
        self.assertTrue(
            (self.target / "codex-teammode-workflow" / "skills" / "docs-review" / "SKILL.md").is_file()
        )

    def test_dry_run_does_not_create_skill_root(self) -> None:
        result = self.run_install(
            "--dry-run",
            "--install-docs-review",
            "--skill-root",
            str(self.skill_root),
            str(self.target),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Skill action: install", result.stdout)
        self.assertFalse(self.skill_root.exists())

    def test_install_noop_refuse_and_force_backup(self) -> None:
        first = self.run_install(
            "--no-clipboard",
            "--install-docs-review",
            "--skill-root",
            str(self.skill_root),
            str(self.target),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = self.skill_root / "docs-review"
        self.assertEqual(self.tree_snapshot(installed), self.tree_snapshot(SKILL_SOURCE))
        self.assertTrue((installed / "scripts" / "prepare_closure_audit.py").is_file())
        self.assertTrue((installed / "scripts" / "merge_closure_audits.py").is_file())
        self.assertTrue(
            (installed / "references" / "independent-closure-synthesizer.md").is_file()
        )

        second = self.run_install(
            "--force",
            "--no-clipboard",
            "--install-docs-review",
            "--skill-root",
            str(self.skill_root),
            str(self.target),
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("already identical; no-op", second.stdout)

        (installed / "local-change.txt").write_text("preserve me", encoding="utf-8")
        other_skill = self.skill_root / "other-skill"
        other_skill.mkdir()
        (other_skill / "keep.txt").write_text("untouched", encoding="utf-8")
        refused = self.run_install(
            "--force",
            "--no-clipboard",
            "--install-docs-review",
            "--skill-root",
            str(self.skill_root),
            str(self.target),
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertTrue((installed / "local-change.txt").is_file())

        forced = self.run_install(
            "--force",
            "--no-clipboard",
            "--install-docs-review",
            "--force-skill",
            "--skill-root",
            str(self.skill_root),
            str(self.target),
        )
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(self.tree_snapshot(installed), self.tree_snapshot(SKILL_SOURCE))
        backups = list(self.skill_root.glob("docs-review.backup.*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "local-change.txt").is_file())
        self.assertEqual((other_skill / "keep.txt").read_text(encoding="utf-8"), "untouched")

    def test_skill_options_require_explicit_install_flag(self) -> None:
        result = self.run_install(
            "--dry-run", "--skill-root", str(self.skill_root), str(self.target)
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --install-docs-review", result.stderr)


if __name__ == "__main__":
    unittest.main()
