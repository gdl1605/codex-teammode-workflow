# docs Index Template

<!-- codex-teammode:managed:start scope=docs-index version=0.5.0 -->

> Last updated: TBD
> Scope: target repo docs entry map
> Responsibility: tell future agents what to read first and where each kind of project truth belongs
> Recommended next hop: `handoff/latest.md`

Only an explicit current user request to change a mechanism or plan that change activates
the development workflow. Normal execution, recovery, troubleshooting, existing configuration
selection, business operation plans / RequestSpecs, and reports follow the project's existing
runtime contract without development Grill-me or evaluator dispatch. A fault, generated file,
or agent-authored repair plan cannot create change authorization; explicit execution-only or
no-review instructions take precedence. Existing business planner / reviewer / Oracle stages remain intact.

For an authorized mechanism change, default development traces consequential choices before formal
plan delivery, including plan-only tasks, and clarifies unconfirmed choices through native
question cards and actual user answers. A fresh evaluator lightly reviews the original request,
corrections, and plan before delivery. The main agent rechecks those sources before authorized
implementation, then uses another fresh evaluator to review actual behavior and completion claims.
Team Loop requires an explicit user prompt and uses the same two review stages, reporting only to Leader.
Plan-only work ends on reviewed plan delivery without requiring Generator results or implementation evidence.
This index is a project reference map; read only what the task needs.

## Read Order

1. `handoff/latest.md`
2. `product/current-state.md`
3. `architecture/system-map.md`
4. `architecture/domain-boundaries.md`
5. `architecture/ia-and-navigation.md`
6. `workflow/default-workflow.md` for ordinary development; dispatch its evaluator with `workflow/independent-evaluator.md` and the scoped Review Request
7. `workflow/team-loop.md` only when Team Loop is explicitly requested; dispatch subagents with `workflow/team-loop-core.md` and the matching `workflow/team-loop-roles/<role>.md`; Evaluator also reads the shared criteria in `workflow/independent-evaluator.md`
8. `workflow/update-policy.md` only when upgrading an older workflow install
9. `workflow/docs-maintenance.md`
10. `product/active-directions.md`
11. `plans/tech-debt.md`
12. `plans/active/` and `plans/completed/` when a managed plan is in scope
13. `handoff/archive/` only for history lookup

## Fact Priority

For current implementation facts:

1. current code
2. topic docs
3. `handoff/latest.md`
4. `handoff/archive/`

This order does not let code silently override explicit business intent, nor prove deployment,
acceptance, legal, or release state. Route those claims to their direct authority/evidence.

## Directory Responsibilities

- `architecture/`: system map, information architecture, domain boundaries
- `product/`: current state and active directions
- `workflow/`: default development, independent evaluator, explicit Team Loop, role capsules, update policy, docs maintenance
- `plans/`: active plans, completed plans, long-term debt
- `handoff/`: latest handoff and archived handoff snapshots
- `evidence/`: audit evidence and read-only findings

## Target Project Notes

TBD after target code audit.

<!-- codex-teammode:managed:end -->
