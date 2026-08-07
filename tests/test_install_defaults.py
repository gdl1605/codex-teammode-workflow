from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "install.sh"


class InstallDefaultsTests(unittest.TestCase):
    def test_default_package_keeps_docs_review_out_of_agent_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            target = root / "target"
            target.mkdir()
            env = os.environ.copy()
            env["CODEX_HOME"] = str(root / "isolated-codex-home")

            result = subprocess.run(
                [str(INSTALLER), "--no-clipboard", str(target)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            installed_package = target / "codex-teammode-workflow"
            self.assertTrue(
                (installed_package / "skills" / "docs-review" / "SKILL.md").is_file()
            )
            for entry_name in ("AGENTS.md", "CLAUDE.md"):
                entry = (installed_package / "workflow-kernel" / entry_name).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn("docs-review", entry.lower())


if __name__ == "__main__":
    unittest.main()
