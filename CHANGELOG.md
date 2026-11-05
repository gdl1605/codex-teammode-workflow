# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning for public releases.

## [Unreleased]

## [0.5.0] - 2026-11-05

### Added

- Confirmed Spec handoff in the existing active plan when cross-session continuity is needed, while durable terminology and interface contracts stay in the project's canonical documents and executable definitions.
- Grill-with-docs: trace affected terms and contracts through actual producers, consumers, and existing validation before asking about unresolved choices; write decisions back to the same plan and update formal contracts during authorized implementation.
- Lightweight independent review before formal plan delivery, including plan-only work, in both default development and Team Loop. Check original requirements and corrections against the plan without requiring future implementation evidence.

### Changed

- Share evaluator criteria across planning and implementation: find omitted or weakened requirements, unauthorized consequential choices, assumptions promoted to facts, plan/implementation differences, unsupported completion claims, and assumptions shared by code and tests.
- Preserve relevant user quotes, corrections, decision sources, and stage-specific delivery claims in Review Requests and Evaluation Bundles. Implementers still recheck original requirements and the revised plan before editing.
- Route Team Loop planning gaps through Leader to Planner and implementation gaps to Generator. Agents investigate factual gaps; genuine intent or contract disputes use native question cards. Low-severity or residual-risk labels cannot waive explicit requirements.
- End plan-only work after reviewed plan delivery without dispatching Generator or demanding its results. Plan review neither grants implementation authorization nor replaces implementation review or existing user approval requirements.
- Reuse one formal validation entry per contract or verification scope, with shared executable definitions and actual consumers; distinguish planned checks, executed evidence, and uncovered behavior.
- Align the Chinese README, docs index template, kernel versions, and managed-block markers with the current workflow.

## [0.4.0] - 2026-11-05

### Added

- Lightweight default development in `default-workflow.md`: the main agent plans and implements, clarifies consequential unresolved choices through a built-in Grill-me step, and dispatches a fresh read-only evaluator afterward.
- `independent-evaluator.md` with a scoped Review Request, original-requirement and consumer tracing, facts-versus-assumptions review, direct repair feedback, factual follow-up, and user arbitration for genuine disputes.

### Changed

- Drive planning-time Grill-me with native structured question cards (`request_user_input_async` when exposed), actual user answers, same-plan writeback, and dependent question rounds. Recommendations, preselection, tool returns, request cleanup, and elapsed time do not count as confirmation; explain actual tool restrictions before using text choices.
- Clarify consequential choices before formal plan delivery, including plan-only tasks: identify the original user decision, contract, or explicit delegation; ask about remaining proposals before treating them as settled. Agent-selected defaults and "first version" scope choices cannot silently bypass Grill-me. Preserve draft-first requests and existing implementation freedom without adding blanket plan approval.
- Keep facts, user decisions/contracts, agent assumptions, and unknowns distinct, especially when writing plans, execution conditions, documentation, and completion claims.
- Install/update the new default alongside explicitly triggered Team Loop; requesting an independent evaluator alone does not start Team Loop. Keep retired planner schemas retired and preserve explicit target restrictions.
- Synchronize agent entries, docs indexes, and bootstrap/update manifests. Describe ordinary development and Team Loop dispatch in both README entries.

## [0.3.1] - 2026-10-19

### Changed

- Put installation instructions before the project introduction in both README languages.
- Remove the unofficial-project disclaimer section and its English equivalent from the README.
- Update the README status, kernel version, and managed-block versions to 0.3.1.

## [0.3.0] - 2026-10-19

### Changed

- Keep only prompt-triggered Team Loop for coding collaboration. Untriggered tasks receive no round types, output schemas, startup checks, or subagent scheduling.
- Remove normal-workflow planner schemas, collaboration/startup/prompt templates, and the legacy `@planner` alias; synchronize agent entries, role contracts, manifests, and indexes.
- Simplify installation to clone → copy the entire bootstrap prompt → send it in any target project agent conversation. Bootstrap can use an external checkout or a temporary clone.
- Add `remove-workflow` upgrade instructions for exact retired files while preserving target project facts and content outside managed blocks.
- Set the kernel version, managed-block versions, and README status to 0.3.0.

## [0.2.0] - 2026-08-07

### Changed

- Renamed "Team Mode" to "Team Loop" across all files.
- Normal workflow is now the explicit default; no longer defaults to subagent scheduling or independent planner/generator/evaluator roles.
- `@planner` is now a legacy-compat alias for `plan-only` or `read-only audit`, not an independent planner mode.
- `plan-gated` / `auto-execute` descriptions no longer bind to risk levels; they are Team Loop internal pacing choices.
- Leader is explicitly forbidden from implementing changes directly.
- `files_read` replaced by `freshly_read` / `satisfied_from_verified_cache` in Read Scope Ack.
- Execution prompt structure changed from 7 sections to 8 (removed "建议的并行只读审计", added "建议实现路径").
- Session startup protocol changed from mandatory to on-demand for low-risk tasks.
- Removed project-specific examples (Supabase, `author_user_id`, posting contracts) and replaced with generic language.
- Docs maintenance now distinguishes the per-turn docs impact micro loop from the manually triggered `$docs-review` macro loop and emits `reconciliation_recommended` without automatic invocation.
- `$docs-review` now protects canonical semantic coverage during cleanup, reconciles completed-plan bodies instead of adding header-only status overrides, validates navigation-like inline paths, and requires explicit release scope/blocking for active plans when a release scope is frozen.
- `$docs-review` now assigns every deterministic finding an exact disposition, pins finding keys to a scanner manifest, detects locally unscoped archive language, repeated Markdown tables, bare `.md` references, and missing navigation directories, and machine-validates independent-auditor clause/file coverage before accepting a pass.
- Human arbitration in `$docs-review` now expands maintenance-omission, manual-removal, superseded/reverted, partial-completion, and lost-evidence hypotheses before presenting choices.
- `$docs-review` v3 upgrades to scanner schema 5 and plan schema 3, adds a closed audit-scope manifest plus executable edit contracts, validates active-plan indexes, repository path/glob prefixes, machine-specific absolute paths, canonical transfers, path rewrites, and lifecycle moves; older scanner or plan schemas must restart in Plan Mode.
- Independent closure now uses size-bounded, scope-pruned shard auditors followed by a fresh synthesis auditor, preserves raw report JSON, separately validates Markdown coverage and authorized support-file reads, distinguishes docs/implementation/evidence/process defects, and supports hash-safe reuse of unchanged passing shards only.
- Default `AGENTS.md` and `CLAUDE.md` templates no longer embed the optional `docs-review` skill guide; the bundled skill remains package-only and explicitly installable.

### Added

- Workflow update protocol: `UPDATE_PROMPT.md`, `UPDATE_MANIFEST.md`, `workflow-kernel/VERSION`, and `docs/workflow/update-policy.md`.
- Ownership-based upgrade strategies: `replace-workflow`, `managed-block`, `create-if-missing`, and `never-overwrite`.
- Optional, explicit-only `$docs-review` skill for Plan Mode fact reconciliation and approved docs-only apply.
- Standard-library `scan_docs.py`, `validate_docs_review.py`, `prepare_closure_audit.py`, `validate_closure_audit.py`, and `merge_closure_audits.py` tools with structured JSON, scope/symlink safety, hard plan gates, deterministic sharding, strict raw-report validation, and fresh synthesis dispatch.
- Installer flags `--install-docs-review`, `--skill-root`, and `--force-skill`, including exact-target backup and identical-copy no-op behavior.
- `role_session_reuse`: planner / scout may be reused with freshness checks; generator / evaluator are fresh each round.
- `Planner Delta Output` and `Scout Delta Evidence` short-form templates for reused roles.
- `delta_output_required` flag in Team Loop context bootstrap.
- `implementation_owner: generator` in Team Loop output.
- `generator_result` / `generator_read_scope_ack` as required output fields; missing them triggers `blocked / protocol_violation`.
- Evaluator model strategy: `gpt-5.4 medium` by default; other roles `gpt-5.5 high`.

## [0.1.0] - 2026-05-10

### Added

- Initial public preview of Codex-teammode Workflow.
- `workflow-kernel/` with `AGENTS.md`, `CLAUDE.md`, `docs/workflow/*`, `docs/planner/*`, and `workflow/audit-first.md`.
- `docs-structure-template/` with a generic target-repo docs scaffold.
- `BOOTSTRAP_PROMPT.md` for one-shot installation into a target repo.
- `MANIFEST.md` and `CURRENT_DOCS_STRUCTURE.md` reference docs.
- Bilingual README entry: `README.md` plus Chinese-focused `README.zh-CN.md`.
- Top-level OSS metadata: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, GitHub issue templates, PR template, and MIT license.
- `install.sh` with `--dry-run`, `--force`, and `--no-clipboard`.

### Changed

- Set the public project name to Codex-teammode Workflow.
- Renamed the install payload folder to `codex-teammode-workflow/`.
- Explicitly supports Codex and Claude Code as first-class targets.
- Installer now copies release metadata such as `LICENSE` and `CHANGELOG.md` into the payload to avoid broken local links.
- Kernel language is kept Chinese-first while top-level docs provide bilingual onboarding.

### Sanitized

- Removed concrete sample project files from `examples/`.
- Removed source-domain examples and replaced them with generic high-risk workflow language.
- Removed local editor/agent settings and pre-launch issue parking notes from the public package.
- Added an unofficial-project disclaimer for OpenAI affiliation.
