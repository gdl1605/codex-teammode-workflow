## Summary

What changes, in 1-2 lines.

## Type

- [ ] kernel change (affects what gets installed into target repos)
- [ ] template change (`docs-structure-template/`)
- [ ] bootstrap prompt change
- [ ] top-level docs (README / CONCEPTS / FAQ / CONTRIBUTING / ROADMAP / SUPPORT)
- [ ] tooling / CI

## Self-install sanity check

- [ ] I imagined giving `BOOTSTRAP_PROMPT.md` to an agent in an empty repo and the install still works.
- [ ] If the kernel changed, `MANIFEST.md` and `BOOTSTRAP_PROMPT.md` are updated.
- [ ] No project-specific business facts leaked into kernel files.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` if user-visible.
