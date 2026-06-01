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
- Clarified that optional `longterm-planning` skill decision interviews take precedence over the normal Markdown `plan schema`, and that `plan schema` is not Codex Plan Mode or `request_user_input`.

### Added

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
