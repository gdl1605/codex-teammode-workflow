# Codex-teammode Workflow Manifest

## Package Intent

Codex-teammode Workflow is a prompt-first workflow package for Codex and Claude Code. It ships workflow rules, bootstrap instructions, and a docs scaffold. It does not ship product facts.

## Included Workflow Kernel

```text
workflow-kernel/
  AGENTS.md
  CLAUDE.md
  docs/README.md
  docs/workflow/collaboration.md
  docs/workflow/docs-maintenance.md
  docs/workflow/session-startup.md
  docs/workflow/prompt-template.md
  docs/workflow/team-loop.md
  docs/planner/planner-system.md
  docs/planner/planner-input-template.md
  docs/planner/planner-output-schema.md
  workflow/audit-first.md
```

`AGENTS.md` and `CLAUDE.md` are intentionally synchronized so Codex and Claude Code start from the same process rules.

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
- Stack-specific terms such as database, auth, migrations, server functions, build commands, hosted deploys, or package managers.
- High-risk domain examples such as state machines, permissions, cross-role writes, external integrations, concurrent resources, or multi-step resource pipelines.
- Product phase language in `docs/planner/planner-system.md`.
- `docs/README.md` task routing and file responsibilities.

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
