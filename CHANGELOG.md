# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning for public releases.

## [Unreleased]

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
