# Current Docs Structure Reference

This file records the docs shape used when distilling this workflow package.

It is a structural reference only. Do not copy package-local notes as target project facts.

## Directory Shape

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

## Workflow / Planner Files Copied Into Kernel

```text
docs/workflow/collaboration.md
docs/workflow/docs-maintenance.md
docs/workflow/session-startup.md
docs/workflow/prompt-template.md
docs/workflow/team-loop.md
docs/planner/planner-output-schema.md
docs/planner/planner-input-template.md
docs/planner/planner-system.md
```

## Product / Architecture Template Slots

These are represented as generic placeholders in `docs-structure-template/`.

```text
docs/product/current-state.md
docs/product/active-directions.md
docs/architecture/domain-boundaries.md
docs/architecture/ia-and-navigation.md
docs/architecture/system-map.md
```

## Plans Template Slots

These are represented as generic placeholders in `docs-structure-template/`.

```text
docs/plans/tech-debt.md
docs/plans/active/README.md
docs/plans/completed/README.md
```

Concrete active/completed plan files are intentionally excluded because they would be project facts.

## Handoff Template Slots

```text
docs/handoff/latest.md
docs/handoff/archive/README.md
```

Concrete handoff content is intentionally excluded because it would be project-specific.

## Evidence Template Slot

```text
docs/evidence/README.md
```

Concrete evidence folders, screenshots, and audit files are intentionally excluded.
