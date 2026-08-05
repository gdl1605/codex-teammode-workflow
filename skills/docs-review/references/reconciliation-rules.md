# Reconciliation rules

## Contents

- [Conflict taxonomy](#conflict-taxonomy)
- [Canonical ownership](#canonical-ownership)
- [Canonical preservation gate](#canonical-preservation-gate)
- [Plan lifecycle closure](#plan-lifecycle-closure)
- [Scope rules](#scope-rules)
- [Automatic versus human resolution](#automatic-versus-human-resolution)
- [Resolution Ledger](#resolution-ledger)
- [Baseline and apply safety](#baseline-and-apply-safety)
- [Cleanup transformations](#cleanup-transformations)
- [Independent semantic closure](#independent-semantic-closure)

## Conflict taxonomy

Classify each issue before proposing an edit:

| Type | Detection question | Default treatment |
|---|---|---|
| Duplicate fact | Is the same scoped claim defined fully in more than one place, including repeated or near-repeated table rows? | Keep one canonical definition; replace others with short links. |
| Direct contradiction | Do two current claims assign incompatible values to the same subject/predicate/scope? | Resolve by evidence authority or ask the user. |
| Stale status | Does a status claim lag direct evidence or its own dated event? | Replace the stale current claim; retain history only where useful. |
| Candidate/current mixing | Is a proposal written inside a current contract or state summary? | Move it to active directions/plans and link briefly. |
| Implementation/contract mismatch | Does code behavior disagree with confirmed intent? | Preserve the confirmed contract; emit `code_followup_required`. |
| Platform leakage | Is an H5, mini-program, native, or shared rule generalized beyond evidence? | Split claims by platform; do not infer shared behavior. |
| Lifecycle error | Is accepted/completed work still active, or is one status axis standing in for another? | Archive or declare the remaining active slice; restore independent axes. |
| Historical-current leakage | Is a dated or superseded fact presented as current? | Move to history/evidence or remove if it has no continuing value. |
| Missing evidence | Does a current/deployed/accepted claim rely on an absent or broken source? | Repair the link, remove the claim, or mark evidence unavailable. |
| Canonical coverage loss | Would cleanup remove stable unique semantics or system mappings from their expected entry point? | Preserve them or name a new canonical owner before deleting. |
| Archive overlay conflict | Does a completed header sit above body text that still says active, candidate, or awaiting acceptance? | Reconcile the body; a header-only override is insufficient. |
| Prospective/current divergence | Does an active candidate differ from current code or current-state without saying whether it remains intended? | Classify it as intended, superseded, reverted, parallel, or unresolved. |
| Navigation path ghost | Does a Markdown link or inline “next hop” path point to moved/deleted material? | Repair it or mark it as a non-navigable historical identifier. |
| Release-scope gap | Is work active while release scope is frozen, but inclusion/blocking is unspecified? | Record `release_scope` and `release_blocking` or ask the user. |
| Lifecycle indirection | Does a lifecycle owner say “read another plan/evidence” instead of recording a concrete scoped value? | Store a value such as `externally_unverified` and link its evidence. |

Deterministic scan findings are candidates. They do not settle business truth.

## Canonical ownership

Choose one owning document for each enduring fact:

- domain invariant or permission boundary: the relevant architecture/domain contract;
- present product capability: current-state;
- future direction: active-directions or an active plan;
- task execution detail: active plan while active, completed plan after acceptance;
- current cross-session entry: latest handoff;
- proof: evidence.

The owning document contains the full statement. Summaries contain only enough context to
route the reader and a valid link. Do not append “correction” paragraphs underneath the old
fact; replace or relocate the old assertion.

## Canonical preservation gate

Before shortening a canonical document, inventory its stable claims, headings, and mapping
anchors. Give every removed claim exactly one disposition:

- `retained` at the same owner;
- `replaced` by a corrected statement;
- `moved` to a named canonical destination;
- `historical` in a dated history/evidence location; or
- `removed_duplicate` with the surviving owner named.

Do not use “current code contains it” as the destination for business meaning. Code is valid
evidence for implementation, not a substitute for a domain contract. A large reduction in
line count, headings, or repository-path anchors is a review gate, not proof of good cleanup.
Require explicit human approval and a coverage reason before applying such a reduction.
Use only real route, field, RPC, migration, or doc-path values as deterministic
`required_identifiers`. Put business meaning in `semantic_claims` for independent semantic
review. Never add validator-only prose, Claim IDs, “stable anchor” labels, audit IDs, or batch
IDs to project docs.

## Plan lifecycle closure

Moving a file to `plans/completed/` requires a full-document pass:

- replace unscoped present-tense active/candidate/waiting language;
- label retained state snapshots as historical and name the date that bounded them;
- rewrite `Next step` sections as historical outcomes or remove them;
- repair recommended next hops and inline paths that still point to `plans/active/` or
  deleted design sources;
- preserve explicit unknown external axes rather than promoting them to complete; and
- reconcile linked evidence whose “current status” now contradicts the accepted plan.

Scope retained history locally. Use a dated historical heading for a whole section or an
explicit historical prefix on the individual sentence/table row. Never use one top-of-file
notice to reinterpret unbounded later uses of “current”, `candidate`, `pending`, “需要
apply”, “等待验收”, or “下一步”. Search readers and deep links may bypass that notice.

Do not mechanically project a bulk human answer into every sentence of every plan. If the
body exposes a different scope, ask whether it was omitted from maintenance, manually
removed after acceptance, superseded/reverted, partially completed, or still intended.

## Scope rules

An explicit path scope may read only that path plus direct dependencies identified by its
index, links, claims, code references, current-state, handoff, plan, and evidence. A domain
scope must first be resolved through the docs index to concrete paths.

When a necessary source falls outside approved scope:

1. Name the claim that cannot be decided.
2. Name the exact additional path and why it is needed.
3. Ask for scope expansion.
4. Until approved, keep the claim unresolved and do not read or edit the path.

Never use a broad repository crawl to bypass a narrow scope.

## Automatic versus human resolution

Automatic correction is allowed only when direct repository evidence uniquely decides a
descriptive fact. Examples include a broken relative link, a duplicated identical paragraph,
or an implementation description contradicted by current types and focused tests.

Human arbitration is required when:

- business intent has two plausible contracts;
- current code may be a bug rather than the desired behavior;
- acceptance, deployment, release, or legal state lacks direct evidence;
- history does not identify which decision superseded another;
- removing a statement would erase a high-risk unresolved conflict.

Agent consensus is never a substitute for evidence or accountable human authority.

## Resolution Ledger

Keep this ledger in task context:

| Field | Meaning |
|---|---|
| `claim_id` | Claim/conflict being resolved. |
| `decision` | Chosen meaning, automatic evidence-backed correction, or `unresolved`. |
| `claim_type` | Evidence route for the claim. |
| `authority.kind` / `authority.resolution_id` | Exact evidence or human decision that authorizes the resolution. |
| `scope.platforms` / `scope.environments` / `scope.subjects` | Exact bounded objects and runtime scope. |
| `scope.lifecycle_axes` / `scope.effective_date` | Exact independent axes and date covered. |
| `affected_docs` | Exact docs allowed to change. |
| `code_followup_required` | Whether implementation now conflicts with confirmed intent. |
| `risk` | `high`, `medium`, or `low`. |

Maintain a schema-v2 Finding Disposition Ledger for deterministic candidates. Record every
scanner `finding_key` and `source_fingerprint` exactly once with one of:

- `resolve_by_edit`: the finding must disappear after apply;
- `verified_historical`: the exact occurrence is already locally and unambiguously scoped
  as history;
- `false_positive`: direct evidence proves this exact occurrence is harmless; or
- `retain_unresolved`: the finding remains visible, binds an unresolved Claim Ledger entry,
  and names the business-readable gap that project docs preserve.

Every entry binds a structured `resolution_group` containing one claim, exact subject,
intended semantics, evidence/human authority, and approved target docs. A group may cover
many occurrences only when all of those fields truly match. `verified_historical` also binds
the nearest dated heading or sentence; `false_positive` uses a supported reason code plus
hashed evidence. Free-text occurrence/type templates are invalid. A scanner count is triage,
not a disposition.

## Baseline and apply safety

The proposed plan must include SHA-256 for every file whose content supports a planned
resolution or will be edited. It must also pin the scanner schema and implementation SHA-256
that generated its finding keys. Before apply, recompute file hashes and verify the scanner
manifest. If either differs:

- make no edits;
- identify only the claims depending on changed files;
- re-audit those claims;
- refresh the manifest and obtain renewed approval.

The approved file list is closed. A newly discovered edit target requires a revised plan and
approval. Apply may modify docs only, even if code/schema/test drift caused the review.
The Plan Mode validator must first match every schema-4 finding key and source fingerprint to
the approved ledger. The pre-apply validator repeats this against unchanged baselines. After
apply, `resolve_by_edit` findings must be absent and every retained/new finding must have an
exact approved relationship; otherwise stop. Old scanner/plan schemas never continue apply.

## Cleanup transformations

- Replace stale facts; do not append a second competing truth.
- Keep full facts at canonical owners and short links elsewhere.
- Move candidates out of current-state/current contracts.
- Move apply/deploy/runtime status out of stable domain invariants.
- Move human-accepted plans from active to completed, or state the exact residual active
  slice when only part was accepted.
- For every active plan under a frozen release scope, record `release_scope` and
  `release_blocking`; do not leave readers to infer whether it blocks launch.
- Put concrete lifecycle values at the lifecycle owner. Use `externally_unverified` rather
  than “read evidence independently”; include `released` when release status is in scope.
- Keep latest handoff as a current entry map, not an accumulated activity log.
- Repair missing evidence links, remove unsupported low-value claims, or mark evidence as
  unavailable with the affected lifecycle axis.

If a confirmed contract and current implementation disagree, edit the contract only and
report the code mismatch. It belongs to a separate execution task.

## Independent semantic closure

Deterministic validation is necessary but cannot establish that prose still carries the
intended meaning. After apply, an independent read-only auditor must test neutral verification
clauses against raw baseline snapshots, current docs, repository evidence, and named semantic
neighbors.

The clause set must exercise at least these dimensions when relevant:

- direct cross-document contradiction after the edit;
- stale or superseded wording in adjacent paragraphs, tables, headings, summaries, and file
  tails—not only the sentence that was edited;
- incomplete propagation to current-state, canonical contracts, handoff, active/completed
  plans, indexes, and evidence consumers;
- loss of stable business meaning, mappings, identifiers, or evidence provenance while
  deduplicating or shortening docs;
- current/candidate/historical and active/completed lifecycle leakage across the whole file;
- platform, environment, release-scope, and lifecycle-axis overgeneralization;
- doc-to-code route, type, schema, and focused-test correspondence for descriptive facts;
  and
- unsupported facts introduced while resolving a different conflict.

Attach a coverage target manifest to the clauses. Mark every changed file and every moved
completed plan `full_read`; mark every other Markdown file in the approved read scope at
least `targeted_search`. Include exact file path, SHA-256, line count, obligation, and reason.
Directory names are search scopes, not proof that a file was examined.

Partition large audits deterministically by full-read file size. One full-read file belongs
to one shard; targeted-search files follow related clauses. Stop before dispatch when one
full-read file exceeds 120,000 bytes or 2,000 lines. Run no more than three fresh shard
auditors concurrently. This is a concurrency limit only: the audit may contain any number of
batches, which run in successive waves until the manifest is exhausted. Never use the
three-agent ceiling to reduce approved coverage or downgrade a repairable finding.
Validate each completed wave before scheduling the next. A deficiency, blocked check, or
invalid raw report stops later waves immediately; batches not yet dispatched are reported as
not run, never synthesized into fake coverage.

When dispatches are built, prune document-valued clause fields and before/after artifacts to
the files assigned to that batch. Materialize a broad docs directory scope as those exact
batch paths. Markdown authority records follow the same assigned coverage boundary; retain
explicitly named non-Markdown code/evidence inputs because they are support dependencies,
not Markdown coverage. Auditors report support files in `paths_examined` without adding them
to coverage arrays.

Each shard auditor must search both required new meaning and residual old language and must
be free to state that the main Agent was wrong, incomplete, overconfident, or destructive.
It may not edit files, make business decisions, or turn agreement into evidence. Preserve
its complete raw JSON; a main-Agent reconstruction is an invalid audit report.

Require exactly one terminal result for every dispatched clause and explicit fulfillment or
omission for every coverage target. Treat an incomplete report as a blocked audit even when
its stated verdict is `pass`.

Any shard deficiency or blocked check activates a human gate before synthesis. The main
Agent reports it and stops; the same turn may not contain a repair. Only explicit user
confirmation creates a new edit authorization, after which deterministic checks and a
different fresh independent auditor run again. When every shard passes, use a separate fresh
synthesis auditor to inspect raw reports, canonical docs, cross-shard consumers, and original
evidence. Shard reports prove coverage, not business facts. Only synthesis pass permits the
final verdict.

In correction rounds, reuse a passed shard only when its role, file/evidence/consumer hashes,
and unbound clause semantics are unchanged. Rerun every changed or failed shard with fresh
context. Never reuse synthesis.
