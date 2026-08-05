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
VERSION
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
docs/planner/planner-output-schema.md
docs/planner/planner-input-template.md
docs/planner/planner-system.md
```

## Update Protocol Files

```text
UPDATE_PROMPT.md
UPDATE_MANIFEST.md
workflow-kernel/VERSION
workflow-kernel/docs/workflow/update-policy.md
```

## Optional Docs Review Skill

```text
skills/docs-review/
  SKILL.md
  agents/openai.yaml
  scripts/{scan_docs,validate_docs_review,prepare_closure_audit,validate_closure_audit,merge_closure_audits}.py
  scripts/tests/
  references/{fact-model,reconciliation-rules,interaction-and-output}.md
  references/{independent-closure-auditor,independent-closure-synthesizer}.md
```

This is a package-level fact-reconciliation skill, not a target docs fact. It remains inside
the copied workflow package unless the user explicitly installs it into a personal skill root.

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
