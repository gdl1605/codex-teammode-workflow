# docs Index Template

<!-- codex-teammode:managed:start scope=docs-index version=0.1.0 -->

> Last updated: TBD
> Scope: target repo docs entry map
> Responsibility: tell future agents what to read first and where each kind of project truth belongs
> Recommended next hop: `handoff/latest.md`

## Read Order

1. `handoff/latest.md`
2. `product/current-state.md`
3. `architecture/system-map.md`
4. `architecture/domain-boundaries.md`
5. `architecture/ia-and-navigation.md`
6. `workflow/collaboration.md`
7. `workflow/prompt-template.md`
8. `workflow/team-loop.md` only when Team Loop is explicitly requested; dispatch subagents with `workflow/team-loop-core.md` and only the matching `workflow/team-loop-roles/<role>.md`
9. `planner/*` only for normal-workflow plan-only / read-only audit / prompt framing / review framing; Team Loop subagents do not read it by default
10. `workflow/update-policy.md` only when upgrading an older workflow install
11. `workflow/docs-maintenance.md`
12. `product/active-directions.md`
13. `plans/tech-debt.md`
14. `plans/active/` and `plans/completed/` when a managed plan is in scope
15. `handoff/archive/` only for history lookup

## Fact Priority

1. current code
2. topic docs
3. `handoff/latest.md`
4. `handoff/archive/`

## Directory Responsibilities

- `architecture/`: system map, information architecture, domain boundaries
- `product/`: current state and active directions
- `workflow/`: collaboration rules, prompt templates, Team Loop, role capsules, update policy, docs maintenance
- `planner/`: normal-workflow plan / audit / review schema and templates
- `plans/`: active plans, completed plans, long-term debt
- `handoff/`: latest handoff and archived handoff snapshots
- `evidence/`: audit evidence and read-only findings

## Target Project Notes

TBD after target code audit.

<!-- codex-teammode:managed:end -->
