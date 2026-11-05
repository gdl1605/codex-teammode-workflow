# Concepts

Quick glossary of the terms used throughout this kit. Read this once before installing into a target project so the bootstrap prompt makes sense.

## Default development

The main agent plans and implements. Before formal plan delivery, including plan-only tasks,
it checks current code and original requirements and traces consequential choices to user
decisions, effective contracts, or explicit delegation. Agent-selected defaults are still
proposals unless covered by that authority. It asks about unconfirmed choices through the
built-in Grill-me step, records answers and sources in the same plan, and briefly identifies
the existing basis when no questions are needed. A fresh read-only evaluator follows
authorized implementation and focused checks.

Grill-me uses native structured question cards: `request_user_input_async` when exposed,
following the tool's current schema and mode restrictions. Independent questions share a
round; actual user answers update the same plan before dependent questions are asked.
Recommendations, preselected options, tool returns, closed requests, and elapsed time are
not answers. Explain a real tool limitation before using numbered text choices instead.
Facts, user decisions/contracts, agent assumptions, and unknowns stay distinct. The evaluator
checks that assumptions have not become facts or unsupported execution conditions, and traces
requirements through actual changes and consumers. Confirmed gaps go directly to the main
agent for repair; factual unknowns need evidence; genuine business disputes go to the user.

This does not require an external skill, a new Spec for every change, fixed interview rounds,
or additional approval where existing authorization is sufficient. Read-only, plan-only,
installation, and update tasks do not automatically enter the development loop. Explicit
target restrictions on permissions, roles, and subagents remain effective.

## Prompt-triggered Team Loop

Team Loop is an explicit alternative to default development. It starts only on an explicit
user request to use Team Loop or Leader-driven multi-subagent coordination. Requesting only
an independent evaluator, discussing, or editing the rules is not a trigger.

A multi-subagent loop run **inside one Leader thread** (Codex / Claude Code session). Triggered when the user prefixes a message with `@team-loop` or asks for a "leader-driven multi-subagent" closure.

```
User
  ↔ Leader (main thread, the only orchestrator)
      → planner subagent     (read-only, produces a plan)
      → generator subagent   (writes the code)
      → scout subagent       (read-only, gathers evidence on demand)
      → evaluator subagent   (reviews against an Evaluation Bundle)
      → human acceptance
```

Hard rules:

- Subagents never talk to each other. They only report to Leader.
- Leader schedules, curates evidence, validates, and summarizes; it does not implement changes inside Team Loop.
- planner and scout may be reused with freshness checks; generator and evaluator are fresh each round.
- generator / scout / evaluator may not spawn their own subagents.
- The loop ends at `human_acceptance_required` or `blocked`. **Never auto-`accepted`.**

Two execution modes inside Team Loop:

- **plan-gated** — planner output must be approved by the human before generator runs.
- **auto-execute** — Leader hands off to generator immediately after a fast plan. Both modes still end at human acceptance.

## audit-first

An evidence flow inside an already triggered Team Loop, used when the **root cause of a bug is not yet locked**. Instead of jumping to a fix:

1. Run a read-only audit.
2. Sink the findings into `docs/evidence/<feature>-audit.md`.
3. Leader curates an Evidence Pack and required read scope for generator.

Goal: stop "imagined fixes" — every change must trace back to evidence, not vibes.

## Fact-priority order

For current implementation behavior in either workflow, this is the descriptive-fact routing order:

1. **Current code** (highest)
2. The relevant topic doc under `docs/`
3. `docs/handoff/latest.md`
4. `docs/handoff/archive/`

Handoffs and summaries are *fast entry points*, not the source of truth.

Neither workflow nor the explicitly invoked `$docs-review` macro treats “current code always
wins” as a rule for every kind of claim. Authority follows the claim type:

| Claim type | Primary authority |
|---|---|
| Implementation | Current code, types, focused tests |
| Data contract | Schema, migration contents, types, tests; file presence does not prove apply |
| Business intent | Explicit human confirmation and the canonical domain contract |
| Deployment | Environment-specific deployment/runtime evidence |
| Acceptance | Explicit human acceptance for the named scope/version |
| Legal | Explicit legal or accountable-owner confirmation |

This distinction prevents an implementation bug from silently rewriting intended business
behavior, while also preventing aspirational docs from being reported as implemented.

## docs impact check

Before concluding default development, or at the end of a Team Loop round: ask "did this work change a project fact, contract, plan state, or known debt?" If yes, update the **single owning doc**. If no, say so explicitly. Never write the same fact into two docs. Preserve labels on assumptions and unknowns instead of turning them into facts during writeback.

It is the incremental **micro loop**. Its output also states
`reconciliation_recommended: yes/no + reason`, but it cannot launch a macro review by itself.

## `$docs-review`

An optional, manually triggered **macro loop** for cross-document fact reconciliation. In
Codex it runs as a read-only Plan Mode audit first, builds temporary Claim/Resolution Ledgers,
uses native questions for ambiguous business facts, and emits a SHA-256-baselined correction
plan. A later `$docs-review apply` in Default Mode may edit only the approved docs after a
drift check.

Cleanup is claim-preserving rather than line-minimizing. Canonical files carry a coverage
manifest, active-to-completed moves require a full body/status/navigation closure pass, and
frozen release scopes require every active plan to declare inclusion and blocking status.
Navigation-like inline paths are validated alongside Markdown links.

Version 3 uses scanner schema 5 and plan schema 3. Every deterministic occurrence binds its
source fingerprint to a resolution group with one scoped claim, intended semantics,
authority/evidence, and approved docs. The plan freezes every scanned Markdown path in an
`audit_scope_manifest` and expresses each approved change as an executable `edit_contract`,
including canonical transfers, path rewrites, and lifecycle moves. Literal coverage is
limited to real route, field, RPC, migration, and doc-path identifiers; natural-language
business meaning is independently audited instead of being forced into validator-only anchor
phrases. Audit IDs never belong in project docs.

Post-apply semantic closure is a two-level independent gate. Full-read files are packed into
bounded shards, no more than three shard auditors run concurrently, and every raw schema-2
report is validated without main-Agent reconstruction. All shards must pass before one new
synthesis auditor checks canonical owners, cross-shard consumers, and original evidence.
Shard reports prove coverage, not business truth. A deficiency stops at a human approval gate;
unchanged passing shards may be hash-reused in a correction round, but synthesis never is.
Each shard receives only its assigned docs and before/after artifacts; shared code/evidence
remains an explicit support dependency. Coverage accounting stays exact to Markdown targets,
while the raw report separately enumerates every authorized support file actually opened.

It separates `planned`, `implemented`, `validated`, `evaluator_passed`,
`migration_applied`, `deployed`, `runtime_smoked`, `human_accepted`, `legal_accepted`, and
`released` instead of collapsing them into “done.” Its verdict is `consistent`,
`partially_consistent`, or `blocked`; none of those verdicts automatically means human
acceptance or release.

## Glossary at a glance

| Term | Meaning |
|---|---|
| Leader | The main thread in Team Loop. The only entity that spawns subagents. |
| Subagent | A helper spawned by the main agent in default development or by Leader in Team Loop; the ordinary evaluator is fresh and read-only. |
| Context Bootstrap | The minimum context Leader hands a new subagent. |
| Read Scope Ack | A subagent's confirmation of which files it actually opened. |
| Scout Request | generator → Leader: "I need more evidence to proceed." |
| Evidence Pack | Leader-curated evidence handed to generator. |
| Evaluation Bundle | Leader-curated diff + criteria handed to evaluator. |
| Residual risk | A P2/P3 issue noted but not blocking acceptance. |
| `human_acceptance_required` | Team Loop terminal state — only a human can move to `accepted`. |
| `blocked` | Terminal state — loop cannot proceed without external input. |
| `$docs-review` | Explicit fact-reconciliation macro loop; never triggered by routine docs impact. |
| Claim Ledger | Temporary per-review list of scoped factual assertions and their evidence. |
| Resolution Ledger | Temporary per-review list of evidence-backed or human-confirmed dispositions. |
| Resolution Group | Schema-v3 binding from one scoped claim and authority to intended semantics and approved docs. |
| Shard auditor | Fresh read-only auditor responsible for one deterministic full-read/search batch. |
| Synthesis auditor | Fresh final auditor that rechecks cross-shard semantic closure without treating shard reports as fact authority. |
| `role_session_reuse` | Planner and scout may be reused across dispatches; generator and evaluator are always fresh. |
| `freshly_read` | Files the subagent opened in this dispatch. Replaces the old `files_read`. |
| `satisfied_from_verified_cache` | Files a reused subagent trusts from a previous dispatch's verified cache. |
| `Planner Delta Output` | Short-form output from a reused planner, covering only new reads and changes. |
| `Scout Delta Evidence` | Short-form output from a reused scout, covering only new findings. |
