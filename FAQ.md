# FAQ

### 这是框架还是运行时？

都不是。Codex-teammode Workflow 是一组 Markdown 规则、prompt 和 docs scaffold。真正“执行”的是你打开的 Codex 或 Claude Code 会话。

### 支持哪些 AI 工具？

第一版明确支持：

- Codex：通过 `AGENTS.md` 入口读取工作流规则。
- Claude Code：通过 `CLAUDE.md` 入口读取同一套工作流规则。

其他工具如果支持类似的项目规则文件，也可以手动适配，但 v0.1.0 不把它们列为一线支持对象。

### 为什么同时生成 `AGENTS.md` 和 `CLAUDE.md`？

因为 Codex 和 Claude Code 的项目入口约定不同。这个项目会让两份文件保持同一套协作流程，避免同一个仓库里不同 agent 读到不同规则。

### Team Mode 是什么？

Team Mode 是一个在单个人类驱动会话里运行的多角色流程。Leader 是主线程，负责调度 planner、generator、scout、evaluator。它不是后台服务，也不是自动化多 agent 平台。

### 为什么不自动 accepted？

因为“agent 说完成了”和“改动真的正确”不是同一件事。工作流最终只能停在 `human_acceptance_required`，由人类确认是否验收。

### 会覆盖我已有的文件吗？

Bootstrap prompt 明确要求先审查再合并。如果目标仓库已有 `AGENTS.md`、`CLAUDE.md`、`docs/` 或 `workflow/`，目标 agent 应保留已有规则并做合并。

### 现在为什么中文优先？

这套工作流最初来自中文项目实践，核心 kernel 仍以中文表达最准确。README 已提供双语入口；英文 kernel 翻译欢迎 PR。

### 这是 OpenAI 官方项目吗？

不是。Codex-teammode Workflow 是非官方社区项目，未获得 OpenAI 认可、赞助或背书。

### 可以用于非软件项目吗？

可以部分借鉴，但默认事实优先级是 `current code > docs > handoff`，偏软件项目。非软件项目需要把 `current code` 替换成自己的 primary artifact。
