# Contributing

Thanks for improving Codex-teammode Workflow.

## What This Project Is

This project is a portable collection of AI collaboration process documents and prompts. It is not a runtime framework and should stay lightweight.

Most contributions touch:

- `workflow-kernel/`: workflow rules installed into target repos
- `docs-structure-template/`: generic docs scaffold
- `BOOTSTRAP_PROMPT.md`: installation instructions for the target agent
- `install.sh`: installer behavior
- top-level docs such as `README.md`, `README.zh-CN.md`, `CONCEPTS.md`, `FAQ.md`, `ROADMAP.md`, and `SUPPORT.md`

## How To Propose A Change

1. Open an issue first for kernel or behavior changes.
2. Fork and open a PR against `main`.
3. Keep PRs focused on one logical change.
4. If the install behavior changes, update `BOOTSTRAP_PROMPT.md`, `MANIFEST.md`, and `CHANGELOG.md`.
5. Run a self-install sanity check against an empty target repo.

## What We Want

- Clearer prompts and stricter guardrails
- Better Codex and Claude Code compatibility
- English translation of the Chinese-first kernel
- Installer safety improvements
- Generic, sanitized examples that do not encode a specific product domain
- Bug reports for ambiguous wording in kernel docs

## What We Do Not Want

- Project-specific business facts
- Private product names, customer names, screenshots, domains, or credentials
- Heavy runtime code or an orchestration service
- Tool adapters that are untested or documented only by assumption

## Style

- Markdown for everything.
- One topic per file.
- Keep terms consistent with [`CONCEPTS.md`](./CONCEPTS.md).
- Add new glossary terms only when they remove ambiguity.
- Keep `AGENTS.md` and `CLAUDE.md` synchronized unless a difference is explicitly tool-specific.

## License

By contributing, you agree your contributions are licensed under the project's [MIT License](./LICENSE).
