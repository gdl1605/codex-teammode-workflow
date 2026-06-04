# Codex-teammode Update Manifest

> Schema version: 1
> Package version source: `workflow-kernel/VERSION`
> Target marker: `docs/workflow/.codex-teammode-version`

This file defines how a newer `codex-teammode-workflow/` package updates an older target project installation.

The update rule is ownership-based:

- Workflow-owned files replace old workflow files in place.
- Mixed files are updated only inside managed blocks.
- Target project facts are never overwritten.

## Managed Block Markers

Use managed blocks in mixed files:

```md
<!-- codex-teammode:managed:start scope=<scope> version=<version> -->
... workflow-owned content ...
<!-- codex-teammode:managed:end -->
```

Everything outside the block belongs to the target project and must be preserved.

## Strategies

| Strategy | Meaning |
|---|---|
| `replace-workflow` | Replace the target file in place from the package. Use for workflow-owned files only. Do not create `.new` siblings for this strategy; old workflow files are meant to be replaced by the new workflow. If `<target>.new` exists from a previous update attempt, remove it after replacing the target file. |
| `managed-block` | Replace only the content between `codex-teammode:managed` markers. If markers are missing, do not overwrite; report the required managed block insertion for human review. |
| `create-if-missing` | Create from template only when the target path is missing. Existing target files are preserved. |
| `never-overwrite` | Never update automatically. These paths hold target project facts, plans, handoff, or evidence. |
| `marker-file` | Write update metadata for future clean/dirty checks. This file is generated from update results, not copied verbatim. |
| `package-only` | Keep inside the copied `codex-teammode-workflow/` package. Do not copy into target root workflow docs. |

## Target File Strategy

| Source path in package | Target path | Strategy |
|---|---|---|
| `workflow-kernel/VERSION` | `docs/workflow/.codex-teammode-version` | `marker-file` |
| `workflow-kernel/AGENTS.md` | `AGENTS.md` | `managed-block` |
| `workflow-kernel/CLAUDE.md` | `CLAUDE.md` | `managed-block` |
| `workflow-kernel/docs/README.md` | `docs/README.md` | `managed-block` |
| `workflow-kernel/docs/workflow/collaboration.md` | `docs/workflow/collaboration.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/docs-maintenance.md` | `docs/workflow/docs-maintenance.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/session-startup.md` | `docs/workflow/session-startup.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/prompt-template.md` | `docs/workflow/prompt-template.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-core.md` | `docs/workflow/team-loop-core.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop.md` | `docs/workflow/team-loop.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-roles/leader.md` | `docs/workflow/team-loop-roles/leader.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-roles/planner.md` | `docs/workflow/team-loop-roles/planner.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-roles/generator.md` | `docs/workflow/team-loop-roles/generator.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-roles/scout.md` | `docs/workflow/team-loop-roles/scout.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/team-loop-roles/evaluator.md` | `docs/workflow/team-loop-roles/evaluator.md` | `replace-workflow` |
| `workflow-kernel/docs/workflow/update-policy.md` | `docs/workflow/update-policy.md` | `replace-workflow` |
| `workflow-kernel/docs/planner/planner-system.md` | `docs/planner/planner-system.md` | `replace-workflow` |
| `workflow-kernel/docs/planner/planner-input-template.md` | `docs/planner/planner-input-template.md` | `replace-workflow` |
| `workflow-kernel/docs/planner/planner-output-schema.md` | `docs/planner/planner-output-schema.md` | `replace-workflow` |
| `workflow-kernel/workflow/audit-first.md` | `workflow/audit-first.md` | `replace-workflow` |
| `docs-structure-template/docs/product/current-state.md` | `docs/product/current-state.md` | `create-if-missing` |
| `docs-structure-template/docs/product/active-directions.md` | `docs/product/active-directions.md` | `create-if-missing` |
| `docs-structure-template/docs/architecture/system-map.md` | `docs/architecture/system-map.md` | `create-if-missing` |
| `docs-structure-template/docs/architecture/ia-and-navigation.md` | `docs/architecture/ia-and-navigation.md` | `create-if-missing` |
| `docs-structure-template/docs/architecture/domain-boundaries.md` | `docs/architecture/domain-boundaries.md` | `create-if-missing` |
| `docs-structure-template/docs/handoff/latest.md` | `docs/handoff/latest.md` | `create-if-missing` |
| `docs-structure-template/docs/handoff/archive/README.md` | `docs/handoff/archive/README.md` | `create-if-missing` |
| `docs-structure-template/docs/plans/tech-debt.md` | `docs/plans/tech-debt.md` | `create-if-missing` |
| `docs-structure-template/docs/plans/active/README.md` | `docs/plans/active/README.md` | `create-if-missing` |
| `docs-structure-template/docs/plans/completed/README.md` | `docs/plans/completed/README.md` | `create-if-missing` |
| `docs-structure-template/docs/evidence/README.md` | `docs/evidence/README.md` | `create-if-missing` |

## Never-overwrite Target Areas

These target paths are project-owned after installation:

```text
docs/product/**
docs/architecture/**
docs/handoff/**
docs/plans/**
docs/evidence/**
```

Do not update them automatically. If a workflow release needs a new placeholder or convention in one of these areas, report it as a manual migration note.

## Marker File Format

After a successful update, write or refresh `docs/workflow/.codex-teammode-version` in the target project:

```yaml
version: <workflow-kernel/VERSION>
updated_at: <ISO-8601 timestamp>
update_schema: 1
package_source: codex-teammode-workflow
managed_files:
  <target path>:
    strategy: replace-workflow / managed-block / create-if-missing
    installed_sha256: <sha256 after update>
```

Future updates may compare the current target file hash with `installed_sha256` for reporting:

- If equal, the file was unchanged since the last workflow update.
- If different and the strategy is `replace-workflow`, replace it in place anyway and report that local workflow edits were replaced.
- If different and the strategy is `managed-block`, preserve all content outside the managed block.

## Legacy Adoption

For old installations without `docs/workflow/.codex-teammode-version`:

1. Treat workflow-owned files listed as `replace-workflow` as old workflow files and replace them in place from the package.
2. Do not create `.new` siblings for workflow-owned files.
3. Remove stale `<target>.new` siblings for workflow-owned files after the target file has been replaced.
4. `managed-block` files may only update content inside existing markers; if markers are missing, report the required managed block insertion instead of rewriting project-owned text.
5. `create-if-missing` files are created only when missing.
6. `never-overwrite` paths are skipped.
7. Always write a new marker file after the update.
