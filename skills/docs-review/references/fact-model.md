# Fact model

Use this model to keep evidence, interpretation, and human authority separate. A claim is
not true merely because it appears in a canonical-looking document.

## Contents

- [Claim Ledger](#claim-ledger)
- [Evidence routing by claim type](#evidence-routing-by-claim-type)
- [Independent lifecycle axes](#independent-lifecycle-axes)
- [Fact classes](#fact-classes)
- [Confidence](#confidence)
- [Active plan classification](#active-plan-classification)
- [Scope of human decisions](#scope-of-human-decisions)

## Claim Ledger

Keep the ledger in task context. Do not add it to the target repository.

| Field | Meaning |
|---|---|
| `claim_id` | Stable ID for this review, such as `DR-ARCH-001`. |
| `claim_type` | `implementation_fact`, `data_contract`, `business_intent`, `deployment_fact`, `acceptance_fact`, `legal_fact`, `release_fact`, or `documentation_fact`. |
| `subject` | Entity, page, workflow, table, role, or obligation being described. |
| `predicate` | Property or relation asserted about the subject. |
| `value` | Asserted value, state, behavior, or boundary. |
| `authority.kind` | Evidence route or `human_resolution`; use `unresolved` when no authority decides the claim. |
| `authority.resolution_id` | Exact evidence or user-decision identifier. Never reuse a broad answer implicitly. |
| `scope.platforms` | Exact platforms. Use an explicit shared value rather than assuming shared. |
| `scope.environments` | Exact environments; external lifecycle facts may not use a generic unknown/all value. |
| `scope.subjects` | Exact feature slices, migration files, routes, entities, or obligations. |
| `scope.lifecycle_axes` | Only axes the evidence/decision actually covers. Empty is allowed for non-lifecycle meaning. |
| `scope.effective_date` | `YYYY-MM-DD` date at which the scoped resolution applies. |
| `temporal_class` | `current`, `historical`, or `prospective`. Do not infer this from directory placement alone. |
| `source` | Repo-relative file and exact line or tight line span. |
| `evidence` | Supporting or contradicting sources with what each source actually proves. |
| `confidence` | `high`, `medium`, or `low`, with a reason. |
| `supersedes` | Earlier claim or snapshot displaced by this claim, if known. |

Normalize paraphrases into the same subject/predicate only when their scope, platform,
environment, and lifecycle axis truly match. Similar wording is not automatically the same
claim.

## Evidence routing by claim type

| Claim type | Stronger evidence | Important limit |
|---|---|---|
| Implementation fact | Current code, public types, focused tests | Code can implement the wrong business rule. |
| Data contract | Current schema, migration contents, generated/static types, focused tests | A migration file does not prove `migration_applied`. |
| Business intent | Explicit user confirmation, canonical domain contract | Current code may be a bug; do not let it silently rewrite intent. |
| Deployment fact | Existing deployment record, runtime evidence tied to an environment | Local files do not prove deployed or released state. |
| Acceptance fact | Explicit human acceptance tied to a scope/version | Evaluator/build pass does not prove `human_accepted`. |
| Legal fact | Explicit legal or accountable-owner confirmation | Technical implementation and drafts are not legal acceptance. |

Within a row, prefer evidence that is current, direct, scoped to the same subject, platform and
environment, and reproducible. Record contradictory evidence rather than averaging it.

## Independent lifecycle axes

Represent each relevant axis separately:

```text
planned
implemented
validated
evaluator_passed
migration_applied
deployed
runtime_smoked
human_accepted
legal_accepted
released
```

One axis never entails the next. In particular:

- `implemented` does not imply `validated`, `deployed`, or `released`.
- `evaluator_passed` does not imply `human_accepted`.
- migration content in source does not imply `migration_applied`.
- `deployed` in one environment does not imply production release.
- product acceptance does not imply `legal_accepted`.

Use `true`, `false`, `unknown`, or `not_applicable` per axis when useful. If an external
axis has no repository evidence, use `externally_unverified`, not a guessed boolean.

## Fact classes

- **Descriptive**: what code, schema, tests, or recorded runtime currently do. Repository
  evidence can often determine these without a question.
- **Normative**: what the business, product, or law says should happen. Ask the accountable
  human when authoritative contracts conflict or are absent.
- **Historical**: what was true at a named time/version. Keep it in history/evidence and do
  not let an undated historical statement present itself as current.
- **Prospective**: candidate, planned, proposed, or exploratory. Keep it out of current
  contracts and current-state summaries.

## Confidence

- `high`: direct evidence proves the exact claim and scope.
- `medium`: evidence is indirect or one scope dimension is inferred.
- `low`: wording is ambiguous, evidence is stale, or external state is unverified.

Confidence is not authority. A high-confidence implementation fact cannot decide a
conflicting business intent by itself.

## Active plan classification

When a release scope is frozen, classify every active plan independently:

```text
release_scope: included | excluded | post_release | parallel_non_blocking | unresolved
release_blocking: true | false | unknown
current_relationship: matches_current | intended_change | superseded | reverted |
  parallel_experiment | unresolved
```

An active plan may contain completed rounds without being complete. State the remaining
slice. If a prospective behavior differs from current code, code proves only
`current_relationship`; it does not decide whether the candidate is still intended.

## Scope of human decisions

A broad answer such as “these plans are complete” proves only the explicitly named plan
scope and acceptance axis. It does not automatically prove every deploy, release, legal,
runtime, or documentation subclaim inside those plans. Expand a bulk answer claim by claim,
and ask again when old body text implies a narrower or different completion boundary.

Store human scope explicitly as `authority.kind`, `authority.resolution_id`, and the five
`scope` dimensions. For `migration_applied`, identify each migration file/number and target
environment in the question itself. Never derive `deployed`, `runtime_smoked`, `released`,
or `legal_accepted` from that answer. Likewise, `human_accepted` is not release authority.

Claim IDs are temporary audit identifiers. They may appear in the in-memory plan and raw
auditor packages, but never in project-facing docs. An unresolved fact stays visible through
business language naming the missing evidence or lifecycle axis, not through `DR-*` tokens.
