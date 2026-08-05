# Interaction and output protocol

## Human arbitration

Use Plan Mode's native `request_user_input` in batches of one to three independent
questions. Do not ask what direct repository evidence already decides.

Each question states:

- conflict ID and exact subject;
- competing meanings with platform, environment, object, date, and lifecycle axes;
- evidence for and against each meaning and what that evidence cannot prove;
- affected docs and likely implementation follow-up;
- a recommended option with rationale; and
- a bounded unresolved option.

Before constructing choices, test whether the apparent gap is caused by omitted docs
maintenance, manual removal or override, superseded/reverted work, partial completion, lost
evidence, or genuine non-occurrence. Include repository-supported causes. Do not offer only
“downgrade”, “unknown”, and “mark complete” variants. If more than two substantive meanings
remain, ask a coarser cause question first. A free-form response is an escape hatch, not a
substitute for plausible choices.

A human answer is authority only for objects and axes named in the question. “Migration was
applied” is unusable until the question and answer identify each migration and environment.
Never project a confirmation to another feature slice, platform, environment, date, or axis.

## Proposed plan contract

End Plan Mode with one self-contained `<proposed_plan>` that includes:

```xml
<proposed_plan>
mode: docs-review
plan_schema_version: 2
decision_complete: true
scope: <repo-relative docs scope>
verdict_if_applied: consistent | partially_consistent | blocked

scanner_manifest: <schema 4 and scanner SHA-256>
baseline_manifest: <every edit/evidence/dependency path and SHA-256>
approved_docs: <closed Markdown edit list>

claims: <typed claims with exact authority and scope>
resolution_groups: <bounded shared semantics/evidence/edit targets>
finding_dispositions: <one exact disposition for every scanner finding>
canonical_coverage: <technical identifiers plus semantic claims>
edits: <file-level replacement/move/deduplication instructions>
code_followups: <contract/implementation mismatches; no code edits>
unresolved: <business-readable gaps and affected lifecycle axes>
closure_requirements: <neutral claim and global clauses>
validation: <plan, pre-apply, post-apply, shard, merge, synthesis gates>
</proposed_plan>
```

Do not call a plan decision-complete if required human authority, edit scope, evidence paths,
or scanner disposition bindings are missing. `approved_docs` is exact, never a glob.

## Temporary plan JSON schema 2

Materialize the machine-checkable plan outside the target repository. The following is the
normative shape; values are illustrative:

```json
{
  "plan_schema_version": 2,
  "decision_complete": true,
  "scanner_manifest": {
    "schema_version": 4,
    "scanner_sha256": "<sha256 of scan_docs.py>"
  },
  "baseline_manifest": {
    "docs/architecture/system-map.md": "<sha256>",
    "supabase/migrations/061_community_sections_and_topics.sql": "<sha256>"
  },
  "approved_files": [
    "docs/architecture/system-map.md"
  ],
  "claims": [
    {
      "claim_id": "DR-COMMUNITY-001",
      "claim_type": "deployment_fact",
      "resolution": "resolved",
      "risk": "high",
      "authority": {
        "kind": "human_resolution",
        "resolution_id": "USER-2026-08-04-01"
      },
      "scope": {
        "platforms": ["shared"],
        "environments": ["production-cn"],
        "subjects": [
          "supabase/migrations/061_community_sections_and_topics.sql",
          "supabase/migrations/062_community_seed.sql"
        ],
        "lifecycle_axes": ["migration_applied"],
        "effective_date": "2026-08-04"
      }
    }
  ],
  "resolution_groups": [
    {
      "group_id": "DRG-001",
      "claim_id": "DR-COMMUNITY-001",
      "subject": "community migrations 061 and 062 in production-cn",
      "intended_semantics": "Both named migrations are recorded as applied in production-cn; no deploy, runtime, legal, or release state is implied.",
      "basis": {
        "kind": "human_resolution",
        "resolution_id": "USER-2026-08-04-01",
        "references": [
          {
            "path": "supabase/migrations/061_community_sections_and_topics.sql",
            "sha256": "<sha256>",
            "proves": "The exact schema changes contained in migration 061, but not apply state."
          }
        ]
      },
      "target_docs": ["docs/architecture/system-map.md"]
    }
  ],
  "finding_dispositions": [
    {
      "finding_key": "DRSK-0123456789abcdefabcd-01",
      "source_fingerprint": "<scanner source_fingerprint>",
      "disposition": "resolve_by_edit",
      "group_id": "DRG-001",
      "expected_post_state": "absent"
    }
  ],
  "coverage_manifest": {
    "docs/architecture/system-map.md": {
      "baseline": {
        "line_count": 80,
        "heading_count": 6,
        "path_reference_count": 12
      },
      "required_identifiers": [
        {
          "kind": "migration",
          "value": "061_community_sections_and_topics.sql",
          "reason": "Keeps the exact migration contract discoverable."
        }
      ],
      "semantic_claims": [
        {
          "claim_id": "DR-COMMUNITY-001",
          "meaning": "Apply state is scoped to the two named migrations and production-cn only.",
          "owner": "docs/architecture/system-map.md"
        }
      ],
      "removed_claims": [],
      "allow_major_reduction": false,
      "reduction_reason": null
    }
  },
  "verdict": "partially_consistent"
}
```

Every `resolution_group` needs a known claim, bounded subject, intended post-edit semantics,
structured basis, and approved target docs. Repository and dated-history bases need hashed
references. `human_resolution` needs the exact same resolution ID as claim authority.

Use dispositions as follows:

- `resolve_by_edit`: bind the finding's approved source doc and use
  `expected_post_state: absent`.
- `verified_historical`: use `expected_post_state: present` and add
  `historical_scope` with `kind: dated_heading | dated_sentence`, exact path, line, date, and
  marker from the nearest local scope.
- `false_positive`: use `expected_post_state: present`, a supported `reason_code`, and hashed
  evidence. Supported codes are `scanner_pattern_not_semantic`,
  `generated_or_example_content`, `intentionally_external_reference`,
  `historical_scope_already_explicit`, and `bounded_scope_exception`.
- `retain_unresolved`: use `expected_post_state: present`, `unresolved_claim_id`, and
  `business_gap: {path, marker}`. The marker is readable project language, never a Claim ID
  or audit token.

Do not require all four dispositions to appear. A uniform real resolution is valid only
through an evidence-complete resolution group. Type-wide or occurrence-template rationale is
invalid.

`required_identifiers` permits only literal `route`, `field`, `rpc`, `migration`, and
`doc_path` values. Put natural-language meaning in `semantic_claims`; independent auditors
judge it. Never add `claim_id: DR-*`, `稳定锚点`, audit IDs, batch IDs, or validator-only
phrases to target docs.

Run `validate_docs_review.py --phase plan` before presenting the plan as complete,
`--phase pre-apply` immediately before writes, and `--phase post-apply` after writes. A v1
plan must be discarded and regenerated.

## Closure verification clauses

After deterministic post-apply validation, create one neutral clause for every resolved or
deliberately unresolved claim and one mandatory `kind: global` clause. Do not encode the
main Agent's suspected mistakes or desired verdict.

```yaml
- clause_id: DR-CLOSURE-001
  kind: claim | canonical_move | lifecycle | unresolved | global
  statement_to_verify: <neutral postcondition>
  fact_scope:
    platforms: [<exact values>]
    environments: [<exact values>]
    subjects: [<exact objects>]
    temporal_class: current | historical | prospective
    lifecycle_axes: [<independent axes>]
    effective_date: YYYY-MM-DD
  authority_and_evidence:
    - path: <exact repository or snapshot path>
      sha256: <hash>
      proves: <bounded proposition>
  artifacts:
    repository_root: <absolute repo path>
    docs_root: <absolute docs root>
    before:
      - source_path: <repo-relative path>
        snapshot_path: <absolute temporary path>
        sha256: <hash>
    after:
      - source_path: <repo-relative path>
        current_path: <absolute path>
        sha256: <hash>
  changed_files: [<exact repo-relative docs>]
  approved_edit_scope: [<exact repo-relative docs>]
  audit_read_scope: [<exact files/directories approved for audit>]
  required_consumers: [<exact files>]
  semantic_neighbors: [<exact files>]
  superseded_vocabulary: [<neutral old terms>]
  forbidden_inferences: [<unsupported implications>]
  allowed_unresolved: [<bounded gaps>]
  required_identifiers: [<real route/field/RPC/migration/doc-path identifiers>]
  semantic_claims: [<business meanings to judge>]
  coverage_targets:
    - path: <exact repo-relative Markdown file>
      sha256: <current hash>
      line_count: <n>
      obligation: full_read | targeted_search
      synthesis_obligation: full_read | targeted_search | none
      reason: <changed/consumer/evidence/neighbor/global reason>
```

The global clause enumerates every in-scope Markdown file. Changed files and moved completed
plans are `full_read`; all others are at least `targeted_search`. A directory is never a
coverage target. Use `synthesis_obligation: full_read` for canonical owners and critical
cross-shard consumers; use targeted search for other global files. Use `none` only when the
file has no cross-shard role, while still preserving its shard obligation.

Every file, evidence source, consumer, and semantic neighbor whose hash can affect a shard
must appear in its clause/coverage. Otherwise that shard cannot be safely reused after a
correction round.

## Minimal dispatches and raw reports

`prepare_closure_audit.py` creates shard dispatches. Send each dispatch verbatim to a fresh
context-isolated subagent. Both shard and synthesis packages contain exactly two top-level
fields—a two-key serialization and nothing else:

Run batches in waves of at most three concurrent shard auditors. The number three limits
simultaneous execution, not total batches; continue with later waves while completed waves
pass. If one returned report is non-pass or structurally invalid, validate all responses
already returned by that wave, stop scheduling later waves, and wait at the human gate. Do
not reduce coverage or reclassify findings to fit one wave.

```yaml
role_file: <absolute packaged role path>
verification_clauses: [<complete clauses>]
```

Do not add a greeting, role summary, change narrative, conclusion, suspected defect, or
follow-up instruction. The role file defines behavior and the raw report schema.

Save the exact subagent JSON. Never reconstruct a missing field, translate YAML to JSON,
extract only deficiencies, or rewrite its severity/evidence. If the response has prose,
truncation, missing fields, manifest mismatch, or false coverage, the strict validator exits
`2`; stop instead of repairing the report.

Coverage accounting and read-scope accounting are deliberately distinct. Coverage arrays
must exactly match the batch's repo-relative Markdown obligations. `global_review.paths_examined`
must additionally include every named authority/evidence file, before snapshot, exact code
file, and (for synthesis) validated raw shard report that was read. It may include the
dispatched role file itself. The validator accepts only
support paths explicitly authorized by a clause or its directory scope; it rejects omissions
and arbitrary extras. `prepare_closure_audit.py` materializes broad docs scopes into the
current batch's exact document paths, so one shard never inherits another shard's docs or
before/after artifacts.

For a valid report:

- exit `0` means complete and pass;
- exit `1` means complete but has a deficiency or blocked check;
- exit `2` means the report itself cannot prove a trustworthy audit occurred.

## Shard merge, synthesis, and human gate

Merge only after every batch has exactly one valid raw report. The merger revalidates each
report, checks that coverage unions exactly match the audit manifest, and rejects duplicate,
missing, overlapping, or fabricated coverage.

If any shard is non-pass, the merger emits a unified human gate containing complete raw
deficiency and blocked objects. The main Agent must:

1. Leave current files unchanged.
2. Report exact ID, severity, artifact layer, effect class, location, comparison evidence,
   explanation, affected scope, and correction constraint.
3. Distinguish docs, implementation, evidence, and process defects.
4. Ask the user to approve an exact correction scope.
5. Stop without a final consistency verdict or same-round repair.

When all shards pass, the merger emits a new two-field synthesis dispatch. The synthesis
auditor reads verified raw reports, canonical docs, cross-shard consumers, and original
evidence. Shard reports prove coverage, not business facts. Synthesis always uses a fresh auditor and is
never reused.

In a correction round, the merger may reuse an old passed shard only when its `reuse_key`
matches the new batch. This key binds the packaged role, file/evidence/consumer hashes, and
unbound clause semantics. Failed, blocked, malformed, ambiguous, or changed shards rerun with
fresh context.

## Apply result

Issue the final result only after deterministic post-apply validation, all shard gates, and
fresh synthesis validation pass. Report:

- `consistent | partially_consistent | blocked`;
- exact changed docs and canonical moves;
- unresolved business-language gaps and independent lifecycle axes;
- `code_followup_required` items without code changes;
- plan/pre/post validation and shard/synthesis results;
- external axes left `externally_unverified`; and
- confirmation that business code, schema, migrations, tests, deployment, and external
  systems were not changed.

An independent pass establishes only that this bounded audit found no remaining in-scope
semantic deficiency. It does not imply deployed, human accepted, legally accepted, or
released.
