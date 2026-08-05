# Concepts

Quick glossary of the terms used throughout this kit. Read this once before installing into a target project so the bootstrap prompt makes sense.

## Two top-level workflows

The kit defines exactly two AI collaboration workflows. Everything else is a sub-mode of one of these.

### 1. Normal workflow

Linear, single-agent. Each turn is one of these "round types":

| Round type | What the agent is allowed to do |
|---|---|
| **plan-only** | Read code/docs, output a plan. No code edits. |
| **read-only audit** | Read code/docs, output findings/evidence. No edits. |
| **docs-only** | Edit `docs/**` only. No business code. |
| **execute** | Audit first, then make minimal code changes. |
| **review** | Read the diff, output a review. No edits. |

Default rule: do not exceed the round type the user asked for. Normal workflow does not default to subagents or independent planner/generator/evaluator roles.

### 2. Team Loop workflow

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

A fallback flow used when the **root cause of a bug is not yet locked**. Instead of jumping to a fix:

1. Run a read-only audit.
2. Sink the findings into `docs/evidence/<feature>-audit.md`.
3. Feed that evidence file back into a fresh execute prompt.

Goal: stop "imagined fixes" — every change must trace back to evidence, not vibes.

## Fact-priority order

For ordinary implementation work, this is the default descriptive-fact routing order:

1. **Current code** (highest)
2. The relevant topic doc under `docs/`
3. `docs/handoff/latest.md`
4. `docs/handoff/archive/`

Handoffs and summaries are *fast entry points*, not the source of truth.

The explicitly invoked `$docs-review` macro does not use “current code always wins” across
every kind of claim. It routes authority by fact type:

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

## Schemas

The kit defines three structured output schemas (see `workflow-kernel/docs/planner/planner-output-schema.md`):

- **plan schema** — for plan-only / audit rounds
- **execute schema** — for execute rounds
- **review schema** — for explicit review / evaluator rounds

Every round must declare which schema it is using.

## docs impact check

End-of-round ritual: ask "did this round change a project fact, contract, plan state, or known debt?" If yes, update the **single owning doc**. If no, say so explicitly. Never write the same fact into two docs.

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

Version 2 uses a structured Finding Disposition Ledger. Every scanner-schema-4 occurrence
binds its source fingerprint to a resolution group with one scoped claim, intended semantics,
authority/evidence, and approved docs. Literal coverage is limited to real route, field, RPC,
migration, and doc-path identifiers; natural-language business meaning is independently
audited instead of being forced into validator-only anchor phrases. Audit IDs never belong in
project docs.

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
| Subagent | A read-only or write-bounded helper spawned by Leader. |
| Context Bootstrap | The minimum context Leader hands a new subagent. |
| Read Scope Ack | A subagent's confirmation of which files it actually opened. |
| Scout Request | generator → Leader: "I need more evidence to proceed." |
| Evidence Pack | Leader-curated evidence handed to generator. |
| Evaluation Bundle | Leader-curated diff + criteria handed to evaluator. |
| Residual risk | A P2/P3 issue noted but not blocking acceptance. |
| `human_acceptance_required` | Terminal state — only a human can move to `accepted`. |
| `blocked` | Terminal state — loop cannot proceed without external input. |
| `$docs-review` | Explicit fact-reconciliation macro loop; never triggered by routine docs impact. |
| Claim Ledger | Temporary per-review list of scoped factual assertions and their evidence. |
| Resolution Ledger | Temporary per-review list of evidence-backed or human-confirmed dispositions. |
| Resolution Group | Schema-v2 binding from one scoped claim and authority to intended semantics and approved docs. |
| Shard auditor | Fresh read-only auditor responsible for one deterministic full-read/search batch. |
| Synthesis auditor | Fresh final auditor that rechecks cross-shard semantic closure without treating shard reports as fact authority. |
| `role_session_reuse` | Planner and scout may be reused across dispatches; generator and evaluator are always fresh. |
| `freshly_read` | Files the subagent opened in this dispatch. Replaces the old `files_read`. |
| `satisfied_from_verified_cache` | Files a reused subagent trusts from a previous dispatch's verified cache. |
| `Planner Delta Output` | Short-form output from a reused planner, covering only new reads and changes. |
| `Scout Delta Evidence` | Short-form output from a reused scout, covering only new findings. |
