from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = SCRIPTS_DIR / "prepare_closure_audit.py"


class LargeShardedFixtureTests(unittest.TestCase):
    def test_six_hundred_kilobyte_fixture_is_split_without_file_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            shard_role = root / "roles" / "shard.md"
            synthesis_role = root / "roles" / "synthesis.md"
            shard_role.parent.mkdir(parents=True)
            shard_role.write_text("# Shard\n", encoding="utf-8")
            synthesis_role.write_text("# Synthesis\n", encoding="utf-8")
            full_targets = []
            full_sizes: dict[str, tuple[int, int]] = {}
            for index in range(32):
                path = root / "docs" / "completed" / f"plan-{index:02d}.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                lines = [f"# Completed plan {index:02d}", ""]
                lines.extend(
                    f"Historical fixture {index:02d}-{line:03d}: " + (chr(65 + index % 26) * 150)
                    for line in range(120)
                )
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                data = path.read_bytes()
                relative = path.relative_to(root).as_posix()
                full_sizes[relative] = (len(data), len(data.splitlines()))
                full_targets.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "line_count": len(data.splitlines()),
                        "obligation": "full_read",
                        "synthesis_obligation": "targeted_search",
                        "reason": "large completed-plan fixture",
                    }
                )
            targeted_paths: list[str] = []
            for index in range(4):
                path = root / "docs" / "consumers" / f"consumer-{index}.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"# Consumer {index}\n\nCurrent route owner {index}.\n", encoding="utf-8")
                data = path.read_bytes()
                relative = path.relative_to(root).as_posix()
                targeted_paths.append(relative)
                full_targets.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "line_count": len(data.splitlines()),
                        "obligation": "targeted_search",
                        "synthesis_obligation": "full_read",
                        "reason": "cross-shard canonical consumer",
                    }
                )
            self.assertGreater(sum(size for size, _ in full_sizes.values()), 600_000)
            clauses_path = root / "clauses.json"
            clauses_path.write_text(
                json.dumps(
                    [
                        {
                            "clause_id": "DR-LARGE-GLOBAL",
                            "kind": "global",
                            "statement_to_verify": "The large completed-plan set remains semantically closed.",
                            "coverage_targets": full_targets,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            plan_path = root / "plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "plan_schema_version": 3,
                        "approved_files": sorted(full_sizes),
                        "audit_scope_manifest": {
                            target["path"]: {
                                "baseline_state": "present",
                                "post_state": "present",
                            }
                            for target in full_targets
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
                    str(root),
                    "--clauses-file",
                    str(clauses_path),
                    "--plan-file",
                    str(plan_path),
                    "--shard-role-file",
                    str(shard_role),
                    "--synthesis-role-file",
                    str(synthesis_role),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertGreaterEqual(len(payload["batches"]), 6)
            assigned_full = [path for batch in payload["batches"] for path in batch["full_read_files"]]
            assigned_targeted = [path for batch in payload["batches"] for path in batch["targeted_search_files"]]
            self.assertEqual(sorted(assigned_full), sorted(full_sizes))
            self.assertEqual(len(assigned_full), len(set(assigned_full)))
            self.assertEqual(sorted(assigned_targeted), sorted(targeted_paths))
            self.assertEqual(len(assigned_targeted), len(set(assigned_targeted)))
            self.assertTrue(all(len(batch["full_read_files"]) < len(full_sizes) for batch in payload["batches"]))
            for batch in payload["batches"]:
                self.assertLessEqual(sum(full_sizes[path][0] for path in batch["full_read_files"]), 120_000)
                self.assertLessEqual(sum(full_sizes[path][1] for path in batch["full_read_files"]), 2_000)
                self.assertEqual(set(batch["dispatch"]), {"role_file", "verification_clauses"})


if __name__ == "__main__":
    unittest.main()
