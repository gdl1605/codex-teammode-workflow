# Bootstrap Prompt For Target Agent

Use this prompt in a target project root after placing the `codex-teammode-workflow/` folder there.

```md
# Install Codex-teammode Workflow

You are working in a target project root. A folder named `codex-teammode-workflow/` has been placed in this repo.

## Goal

Install and adapt Codex-teammode Workflow so this target project can use the same AI collaboration process:

- normal workflow: plan-only / read-only audit / docs-only / execute / review
- Team Mode workflow: Leader + planner / generator / scout / evaluator
- audit-first evidence flow
- planner input and output schemas
- docs impact check
- synchronized `AGENTS.md` and `CLAUDE.md` entry files

## Hard Rules

- Do not blindly overwrite existing target repo files.
- Do not copy product facts, architecture claims, plans, evidence, or domain assumptions from this workflow repo into the target repo.
- Current target repo code is the highest source of truth.
- If target docs conflict with target code, target code wins.
- If the target repo has existing `AGENTS.md`, `CLAUDE.md`, `docs/`, or `workflow/`, inspect and merge.
- Keep edits limited to workflow/process files and docs scaffolding unless the user explicitly allows business code changes.

## Required Read Scope

First read:

- `codex-teammode-workflow/README.md`
- `codex-teammode-workflow/MANIFEST.md`
- `codex-teammode-workflow/workflow-kernel/AGENTS.md`
- `codex-teammode-workflow/workflow-kernel/CLAUDE.md`
- `codex-teammode-workflow/workflow-kernel/docs/README.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/team-loop.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/collaboration.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/prompt-template.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/session-startup.md`
- `codex-teammode-workflow/workflow-kernel/docs/workflow/docs-maintenance.md`
- `codex-teammode-workflow/workflow-kernel/docs/planner/planner-output-schema.md`
- `codex-teammode-workflow/workflow-kernel/docs/planner/planner-input-template.md`
- `codex-teammode-workflow/workflow-kernel/docs/planner/planner-system.md`
- `codex-teammode-workflow/workflow-kernel/workflow/audit-first.md`

Then inspect the target repo:

- current `AGENTS.md`, if present
- current `CLAUDE.md`, if present
- current `docs/README.md`, if present
- current `docs/`, if present
- package/build config, only to identify validation commands
- source tree, only enough to infer docs taxonomy placeholders and tech stack

## Install Tasks

1. Create or merge `AGENTS.md`.
   - Preserve target-specific rules if they exist.
   - Add the workflow rules from `workflow-kernel/AGENTS.md`.
   - Normalize handoff paths consistently. Prefer `docs/handoff/latest.md` unless the target repo already has another clear convention.

2. Create or merge `CLAUDE.md`.
   - Keep it synchronized with `AGENTS.md` unless the target repo already has Claude Code-specific rules.
   - If Claude-specific rules exist, preserve them and add the shared workflow rules from `workflow-kernel/CLAUDE.md`.

3. Create or merge workflow docs:
   - `docs/workflow/collaboration.md`
   - `docs/workflow/prompt-template.md`
   - `docs/workflow/team-loop.md`
   - `docs/workflow/session-startup.md`
   - `docs/workflow/docs-maintenance.md`

4. Create or merge planner docs:
   - `docs/planner/planner-system.md`
   - `docs/planner/planner-input-template.md`
   - `docs/planner/planner-output-schema.md`

5. Create or merge:
   - `workflow/audit-first.md`

6. Create missing docs scaffold from `docs-structure-template/`, but keep placeholders generic:
   - `docs/product/current-state.md`
   - `docs/product/active-directions.md`
   - `docs/architecture/system-map.md`
   - `docs/architecture/ia-and-navigation.md`
   - `docs/architecture/domain-boundaries.md`
   - `docs/handoff/latest.md`
   - `docs/handoff/archive/README.md`
   - `docs/plans/tech-debt.md`
   - `docs/plans/active/README.md`
   - `docs/plans/completed/README.md`
   - `docs/evidence/README.md`

7. Rewrite `docs/README.md` for the target repo.
   - Keep the same role as an entry map.
   - Replace generic routes, modules, domains, and validation examples with target repo facts.
   - If target facts are unknown, write `TBD after target code audit` rather than guessing.

8. Adapt validation commands.
   - Replace generic command placeholders with target project commands.
   - If unknown, write placeholders and mark `HUMAN_CHECK_REQUIRED`.

9. Run a docs impact check for this install.

## Required Output

Use `plan` schema for the initial audit, then switch to `execute` schema only if the install is safe.

Final response must include:

- files read
- files created or changed
- existing files merged versus newly created
- path conventions chosen
- validation commands discovered or left as placeholders
- `AGENTS.md` and `CLAUDE.md` sync status
- workflow docs installed
- docs scaffold installed
- remaining project-specific TODOs
- docs impact check

Do not mark the workflow as accepted. End at `human_acceptance_required`.
```
