# Update Codex-teammode Workflow In Target Project

Use this prompt in a target project root after placing a newer `codex-teammode-workflow/` folder there.

```md
# Update Codex-teammode Workflow

You are working in a target project root. A newer folder named `codex-teammode-workflow/` has been placed in this repo.

## Goal

Upgrade the target repo's installed Codex-teammode Workflow without overwriting target project facts or local customizations.

Use ownership-based updates:

- Workflow-owned kernel files: replace old workflow files in place.
- Mixed files: update only inside `codex-teammode:managed` blocks.
- Target project facts / handoff / plans / evidence: never overwrite.

## Hard Rules

- Do not blindly overwrite existing target repo files.
- Do not edit business code.
- Do not copy product facts, architecture claims, handoff, plans, evidence, or domain assumptions from this workflow repo into the target repo.
- Current target repo code is the highest source of truth.
- If target docs conflict with target code, target code wins.
- Preserve all target-project content outside managed blocks.
- Do not create `.new` files for workflow-owned files. The goal is to replace old workflow files, not keep old and new copies side by side.
- If a mixed file cannot be updated safely because managed markers are missing, report the required managed block insertion instead of creating `.new`.

## Required Read Scope

First read from the package:

- `codex-teammode-workflow/workflow-kernel/VERSION`
- `codex-teammode-workflow/UPDATE_MANIFEST.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/update-policy.md`
- `codex-teammode-workflow/MANIFEST.md`

Then inspect the target repo:

- `docs/workflow/.codex-teammode-version`, if present
- `AGENTS.md`, if present
- `CLAUDE.md`, if present
- `docs/README.md`, if present
- `docs/workflow/`, if present
- `docs/planner/`, if present
- `workflow/audit-first.md`, if present
- `docs/product/`, `docs/architecture/`, `docs/handoff/`, `docs/plans/`, `docs/evidence/` only to confirm they exist; do not rewrite their facts

## Update Procedure

1. Detect installed version.
   - If `docs/workflow/.codex-teammode-version` exists, read its version and `managed_files` hashes.
   - If missing, treat the repo as a legacy install and use the Legacy Adoption rules in `UPDATE_MANIFEST.md`.

2. Classify files by `UPDATE_MANIFEST.md`.
   - `replace-workflow`
   - `managed-block`
   - `create-if-missing`
   - `never-overwrite`
   - `marker-file`
   - `package-only`

3. For `replace-workflow` files:
   - If target file is missing, create it from the package.
   - If target file exists, replace it in place from the package even when no marker exists or hashes differ.
   - If a previous marker exists and the old hash differs, note that local workflow edits were replaced.
   - Do not create `<path>.new` for this strategy.
   - Do not preserve old workflow files beside new ones.
   - If `<path>.new` exists from an earlier update attempt for the same workflow-owned file, remove that stale `.new` file after the real target file has been replaced.

4. For `managed-block` files:
   - Replace only content between:
     `<!-- codex-teammode:managed:start ... -->`
     and
     `<!-- codex-teammode:managed:end -->`
   - Preserve all text outside the block.
   - If markers are missing, do not rewrite the file and do not create `.new`. Report the exact managed block that should be inserted or ask for human review.

5. For `create-if-missing` files:
   - Create only missing placeholders.
   - Preserve existing files unchanged.

6. For `never-overwrite` paths:
   - Do not change existing target facts, architecture docs, handoff, plans, or evidence.
   - If a new workflow version expects a convention change there, report it as a manual migration note.

7. Refresh marker file.
   - Write `docs/workflow/.codex-teammode-version`.
   - Include the package version, timestamp, update schema, and `managed_files` entries with fresh sha256 hashes for updated / managed files.

8. Run docs impact check.

## Required Output

Final response must include:

- detected previous version
- new package version
- files updated
- files created
- managed blocks updated
- workflow-owned files replaced in place
- stale workflow `.new` files removed
- mixed-file conflicts requiring human review
- never-overwrite paths skipped
- marker file status
- remaining manual migration notes
- docs impact check

Do not mark the workflow update as accepted. End at `human_acceptance_required`.
```
