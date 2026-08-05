---
name: docs-review
description: >-
  Use only when the user explicitly invokes $docs-review, says "运行 docs-review",
  or explicitly requests global project-fact reconciliation across docs. Reconcile
  duplicated, stale, contradictory, or weakly evidenced project claims against current
  repository evidence and human-confirmed business facts. Do not use for ordinary docs
  edits or the per-turn docs impact check.
---

# Docs Review

Run the manually triggered fact-reconciliation macro loop that complements incremental
`docs impact`. Keep business facts, audit protocol, and implementation evidence separate.

## Invocation and mode gate

Accept `$docs-review`, `$docs-review scope=<domain-or-docs-path>`, and `$docs-review apply`.
Never infer this skill from routine documentation maintenance. Omitted scope means all docs;
resolve a domain through the docs index and keep a path scope inside the repository docs root.

Run audit and arbitration in Plan Mode without writes. Outside Plan Mode, a normal review may
scan read-only, then must ask the user to switch to Plan Mode. Run `apply` only in Default
Mode, in the same task as a human-approved, decision-complete schema-v2 plan. In Plan Mode,
`apply` may refine the plan only. Missing approval, old schemas, or drift restart the audit.

## Required references

Read these files completely when their stage is reached:

1. [fact-model.md](references/fact-model.md) before extracting claims.
2. [reconciliation-rules.md](references/reconciliation-rules.md) before resolving conflicts
   or defining edit scope.
3. [interaction-and-output.md](references/interaction-and-output.md) before questions,
   plan output, or apply output.
4. [independent-closure-auditor.md](references/independent-closure-auditor.md) before creating
   shard clauses or dispatching shard auditors.
5. [independent-closure-synthesizer.md](references/independent-closure-synthesizer.md) before
   merging shards or dispatching the fresh synthesis auditor.

The role files are executable contracts. The main Agent must never paraphrase, supplement,
or orally override them in a subagent package.

## Plan Mode audit

1. Read the repository agent entry, docs index and maintenance rules, current-state, latest
   handoff, scoped canonical docs, active/completed plans, tests, schema, and existing
   evidence. Follow only direct dependencies of the approved scope.
2. Run:

   ```bash
   python3 scripts/scan_docs.py --repo-root <repo> --docs-root docs [--scope <path>]
   ```

   Scanner schema 4 emits an exact `finding_key`, `source_fingerprint`, file, line, local
   section, and evidence for each deterministic candidate. Exit `1` is expected when it
   finds candidates. Exit `2` stops the review. Pin its complete `scanner_manifest`.
3. Build temporary Claim, Resolution, Canonical Coverage, Active Plan, and Finding
   Disposition Ledgers in task context only. Never write these ledgers or their `DR-*`,
   audit, or batch IDs into project docs.
4. Reconcile descriptive facts against current code, types, schema, migration contents,
   focused tests, and existing evidence. A migration file proves content, never apply,
   deploy, runtime, or release state. Do not probe an external environment without separate
   authorization.
5. Ask about business intent, historical acceptance, legal meaning, and externally
   unverifiable state. Use native `request_user_input` in batches of one to three. Before
   offering choices, test maintenance omission, manual removal/override, supersession or
   revert, partial completion, lost evidence, and genuine non-occurrence. Always permit a
   bounded unresolved result.
6. Bind every human decision exactly through `claim_type`, `authority.kind`,
   `authority.resolution_id`, and scope fields for platforms, environments, subjects,
   lifecycle axes, and effective date. Never expand one slice, environment, platform, or
   lifecycle confirmation to another.
7. Give every scanner finding one structured disposition. A `resolution_group` may serve
   several findings only when they share the same bounded claim, intended post-edit
   semantics, authority/evidence, and approved target docs. Do not use a free-text
   “handle this occurrence/type” rationale.
8. Split canonical coverage into:
   - `required_identifiers`: literal route, field, RPC, migration, or doc-path identifiers;
   - `semantic_claims`: natural-language meaning that independent auditors must judge.

   Never create validator-only prose anchors. Project docs may contain business-readable
   unresolved language such as `legal_accepted=externally_unverified`, but never Claim IDs,
   stable-anchor labels, audit IDs, or batch IDs.
9. Materialize the temporary plan outside the target repository and run before calling it
   decision-complete:

   ```bash
   python3 scripts/validate_docs_review.py \
     --repo-root <repo> --docs-root docs --phase plan \
     --plan-file <temporary-plan-v2.json>
   ```

   Exit `0` is the plan gate. Exit `1` means the plan remains incomplete. Exit `2` means the
   gate itself failed. A schema-v1 scanner manifest, plan, or closure report is never
   compatible; rerun from Plan Mode.
10. Output the self-contained `<proposed_plan>` contract from
    `interaction-and-output.md`, including plan schema 2, exact edit list, all disposition
    bindings, resolution groups, authority scope, coverage, baseline SHA-256 values,
    neutral closure clauses, code follow-ups, unresolved gaps, and verdict.

Keep `planned`, `implemented`, `validated`, `evaluator_passed`, `migration_applied`,
`deployed`, `runtime_smoked`, `human_accepted`, `legal_accepted`, and `released` independent.
Agent agreement is not evidence.

## Apply and deterministic validation

1. Confirm Default Mode, same-task approval, `plan_schema_version: 2`,
   `decision_complete: true`, and an exact approved docs list.
2. Run the pre-apply gate before the first write:

   ```bash
   python3 scripts/validate_docs_review.py \
     --repo-root <repo> --docs-root docs --phase pre-apply \
     --plan-file <temporary-plan-v2.json>
   ```

   Stop on any baseline, scanner, authority, fingerprint, evidence, coverage, or plan
   finding. Re-review only affected claims and obtain renewed approval. Snapshot approved
   docs and named semantic neighbors outside the repository before editing.
3. Modify only approved Markdown docs. Never modify business code, schema, migrations,
   tests, deployment state, or external systems. Replace stale facts instead of appending
   corrections; keep one canonical owner and short references elsewhere. Scope history at
   its nearest dated heading or sentence, not with a file-wide disclaimer.
4. When confirmed business intent differs from code, correct only the contract and report
   `code_followup_required`. Keep high-risk unresolved facts explicit in business language
   and use `partially_consistent` or `blocked`.
5. Run post-apply validation with every actual changed path:

   ```bash
   python3 scripts/validate_docs_review.py \
     --repo-root <repo> --docs-root docs --phase post-apply \
     --plan-file <temporary-plan-v2.json> \
     --changed-file <doc> [--changed-file <doc> ...]
   ```

   Do not continue on exit `1` or `2`.

## Sharded independent closure audit

1. Build neutral verification clauses from the approved plan. Each clause must carry every
   changed file, baseline snapshot, evidence source, consumer, and semantic neighbor it
   depends on. Add one `kind: global` clause whose coverage enumerates the entire approved
   Markdown read scope. Mark changed docs and moved completed plans `full_read`; mark all
   remaining files at least `targeted_search`. Dependencies omitted from coverage make a
   shard non-reusable.
2. Prepare deterministic shards:

   ```bash
   python3 scripts/prepare_closure_audit.py \
     --repo-root <repo> --clauses-file <clauses.json> \
     --shard-role-file <absolute independent-closure-auditor.md> \
     --synthesis-role-file <absolute independent-closure-synthesizer.md> \
     --max-batch-bytes 120000 --max-batch-lines 2000
   ```

   Stop on `oversized_full_read_file`; do not split one file automatically. A full-read file
   belongs to exactly one shard. Keep the emitted manifest and dispatches unchanged.
3. Spawn fresh, context-isolated shard auditors in waves of at most three. Three is only the
   concurrency ceiling, never a ceiling on total batches: run as many waves as the complete
   coverage manifest requires while each completed wave passes. Never multiply the per-batch
   budget by three, shrink coverage, restore approved edits, or turn repairable debt into
   unresolved merely to fit one wave.
   Send each batch's `dispatch` verbatim. It must contain exactly two top-level fields:

   ```yaml
   role_file: <absolute packaged shard role>
   verification_clauses: [<complete batch clauses>]
   ```

   The main Agent must not add role instructions. Save each subagent's exact raw JSON
   response without reconstruction, summarization, field insertion, or conversion. If the
   raw response cannot be obtained losslessly, stop as report-validation exit `2`.
4. Validate each raw report:

   ```bash
   python3 scripts/validate_closure_audit.py \
     --stage shard --audit-manifest <audit-manifest.json> \
     --batch-id <batch-id> --report-file <raw-report.json>
   ```

   Exit `0` is a structurally valid shard pass. Exit `1` is a complete deficiency/blocked
   report. Exit `2` is truncation, missing fields, binding mismatch, false coverage, omitted
   required support evidence, an examined path outside the dispatched scope, or an otherwise
   unverifiable report. Coverage arrays stay exact to Markdown obligations; the report's
   `paths_examined` must also enumerate all dispatch-authorized evidence, snapshots, code, and
   raw reports actually read; it may also list the dispatched role file itself.
   Validate every response already returned by the current wave. If any report exits `1` or
   `2`, do not schedule another wave: preserve the reports, present the exact deficiency,
   blocked, or protocol-error objects, list undispatched batches as not run, and wait for user
   approval. Do not fabricate missing batch reports merely to invoke the merger.
5. Only after every batch has one structurally valid raw report, merge them:

   ```bash
   python3 scripts/merge_closure_audits.py \
     --audit-manifest <audit-manifest.json> \
     --report-file <raw-shard-1.json> [--report-file <raw-shard-N.json> ...]
   ```

   Any shard non-pass already present in a complete report set yields exit `1`, a lossless
   unified human gate, and no synthesis dispatch. Report every deficiency and blocked check
   to the user, preserve current files, and stop.
   Do not repair in the same audit-failure turn. Structural failure exits `2` and also stops.
6. When all shards pass, send the merge output's `synthesis_dispatch` verbatim to one new,
   context-isolated synthesis auditor. It also contains only `role_file` and
   `verification_clauses`. Shard reports prove coverage only; they never become fact
   authority. Save the synthesis auditor's exact raw JSON and run:

   ```bash
   python3 scripts/validate_closure_audit.py \
     --stage synthesis --audit-manifest <merge-output.json> \
     --report-file <raw-synthesis-report.json>
   ```

   Only exit `0` permits the final apply verdict. On exit `1`, present the synthesis
   deficiencies through the same human gate and stop. On exit `2`, report that independent
   closure is unavailable and stop.

## Correction rounds and reuse

After user approval, define the exact correction scope and post-apply baseline, edit only
that scope, regenerate clauses, and rerun the preparation step. A previously passed shard
may be reused only when its emitted `reuse_key` proves its role, files, evidence, consumers,
and unbound clause semantics are unchanged. Pass the previous manifest and raw reports to
the merger:

```bash
python3 scripts/merge_closure_audits.py \
  --audit-manifest <new-manifest.json> --report-file <fresh-changed-shard.json> \
  --previous-audit-manifest <old-manifest.json> \
  --previous-report-file <old-pass-report.json>
```

Never reuse a failed, blocked, structurally invalid, or ambiguous shard. Always run a new
synthesis auditor, even when every shard report was safely reused.

## Final and failure behavior

- Baseline/scope drift: stop before writes and re-review affected claims.
- Missing external evidence: retain `externally_unverified`; never infer deploy, legal,
  acceptance, or release state.
- Required path outside scope: request explicit scope expansion before reading or editing.
- Independent auditor unavailable or non-isolated: do not claim semantic closure.
- Auditor deficiency: report the main Agent's error honestly and wait for user approval.
- Final output may say `consistent`, `partially_consistent`, or `blocked`, but must separately
  list unresolved axes, code follow-ups, deterministic gates, shard/synthesis results, and
  confirm that no business code or external state changed.
