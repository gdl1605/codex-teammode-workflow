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

Default rule: do not exceed the round type the user asked for.

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
- generator / scout / evaluator may not spawn their own subagents.
- The loop ends at `human_acceptance_required` or `blocked`. **Never auto-`accepted`.**

Two execution modes inside Team Loop:

- **plan-gated** — planner output must be approved by the human before generator runs. Used for high-risk changes (data contracts, permissions, state machines, anything where a wrong move is costly).
- **auto-execute** — Leader hands off to generator immediately after a fast plan. Used for low-risk changes (copy edits, small UI tweaks, doc fixes).

## audit-first

A fallback flow used when the **root cause of a bug is not yet locked**. Instead of jumping to a fix:

1. Run a read-only audit.
2. Sink the findings into `docs/evidence/<feature>-audit.md`.
3. Feed that evidence file back into a fresh execute prompt.

Goal: stop "imagined fixes" — every change must trace back to evidence, not vibes.

## Fact-priority order

When code, docs, and handoffs disagree, this order decides truth:

1. **Current code** (highest)
2. The relevant topic doc under `docs/`
3. `docs/handoff/latest.md`
4. `docs/handoff/archive/`

Handoffs and summaries are *fast entry points*, not the source of truth.

## Schemas

The kit defines two structured output schemas (see `workflow-kernel/docs/planner/planner-output-schema.md`):

- **plan schema** — for plan-only / audit rounds
- **execute schema** — for execute rounds

Every round must declare which schema it is using.

## docs impact check

End-of-round ritual: ask "did this round change a project fact, contract, plan state, or known debt?" If yes, update the **single owning doc**. If no, say so explicitly. Never write the same fact into two docs.

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
