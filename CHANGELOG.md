# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning for public releases.

## [Unreleased]

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
