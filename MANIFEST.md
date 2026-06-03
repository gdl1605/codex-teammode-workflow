# Codex-teammode Workflow Manifest

## Package Intent

Codex-teammode Workflow is a prompt-first workflow package for Codex and Claude Code. It ships workflow rules, bootstrap instructions, and a docs scaffold. It does not ship product facts.

## Included Workflow Kernel

```text
workflow-kernel/
  VERSION
  AGENTS.md
  CLAUDE.md
  docs/README.md
  docs/workflow/collaboration.md
  docs/workflow/docs-maintenance.md
  docs/workflow/session-startup.md
  docs/workflow/prompt-template.md
  docs/workflow/team-loop-core.md
  docs/workflow/team-loop.md
  docs/workflow/team-loop-roles/leader.md
  docs/workflow/team-loop-roles/planner.md
  docs/workflow/team-loop-roles/generator.md
  docs/workflow/team-loop-roles/scout.md
  docs/workflow/team-loop-roles/evaluator.md
  docs/workflow/update-policy.md
  docs/planner/planner-system.md
  docs/planner/planner-input-template.md
  docs/planner/planner-output-schema.md
  workflow/audit-first.md
```

`AGENTS.md` and `CLAUDE.md` are intentionally synchronized so Codex and Claude Code start from the same process rules. Team Loop dispatch should use the current tool's primary entry file instead of reading both by default.

`VERSION`, `UPDATE_MANIFEST.md`, `UPDATE_PROMPT.md`, and `docs/workflow/update-policy.md` define the upgrade protocol for replacing old workflow installs without overwriting target project facts.

## Included Docs Structure Template

```text
docs-structure-template/
  docs/README.md
  docs/product/current-state.md
  docs/product/active-directions.md
  docs/architecture/system-map.md
  docs/architecture/ia-and-navigation.md
  docs/architecture/domain-boundaries.md
  docs/handoff/latest.md
  docs/handoff/archive/README.md
  docs/plans/tech-debt.md
  docs/plans/active/README.md
  docs/plans/completed/README.md
  docs/evidence/README.md
```

## Target Docs Taxonomy

The target repo docs taxonomy is:

```text
docs/
  README.md
  architecture/
  product/
  workflow/
    .codex-teammode-version
  planner/
  plans/
    active/
    completed/
  handoff/
    archive/
  evidence/
```

## Must-Template Items

The target agent must adapt these before treating the workflow as installed:

- Target project fact-priority paths, especially `docs/handoff/latest.md`.
- Validation commands in `docs/workflow/session-startup.md`.
- Stack-specific terms such as database schema, authorization policy, migrations, helper functions, RPC/stored procedures, serverless/edge functions, build commands, hosted deploys, or package managers.
- High-risk domain examples such as state machines, permissions, cross-role writes, external integrations, concurrent resources, or multi-step resource pipelines.
- Planning / prompt-framing defaults in `docs/planner/planner-system.md`, especially schema use, audit-first thresholds, and review-framing expectations.
- `docs/README.md` task routing and file responsibilities.

## Update Ownership

Workflow updates use `UPDATE_MANIFEST.md` and `UPDATE_PROMPT.md`.

- `overwrite-if-clean`: workflow kernel files such as `docs/workflow/*`, `docs/planner/*`, and `workflow/audit-first.md`.
- `managed-block`: mixed files such as `AGENTS.md`, `CLAUDE.md`, and `docs/README.md`.
- `create-if-missing`: scaffold placeholders from `docs-structure-template/`.
- `never-overwrite`: target-owned facts under `docs/product/**`, `docs/architecture/**`, `docs/handoff/**`, `docs/plans/**`, and `docs/evidence/**`.

Target projects should record installed workflow hashes in `docs/workflow/.codex-teammode-version` after bootstrap or update.

## Do Not Copy As Facts

Do not copy this repo's current:

- Product state.
- Architecture facts.
- Handoff narrative.
- Active plans.
- Completed plans.
- Evidence screenshots.
- Business domain contracts.
- Validation outputs.

Those must be inferred from the target repo only.
