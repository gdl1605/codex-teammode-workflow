# v0.3.0

本版聚焦 prompt 显式触发的 Team Loop，并简化安装方式。

## 主要变化

- 只保留 Team Loop 编码工作流，移除普通 plan / audit / execute / review 规则、`@planner` 兼容入口及 6 份配套文档。
- 同步 AGENTS.md、CLAUDE.md、角色合同和文档索引。未明确触发 Team Loop 时，不规定轮次、输出 schema、启动检查或 subagent 调度。
- 安装方式简化为：clone 仓库 → 复制 BOOTSTRAP_PROMPT.md 全文 → 发送到任意目标项目的 agent 对话。Bootstrap 可使用项目外的本地 checkout，或临时 clone。
- 升级清单新增 `remove-workflow`，精确移除旧普通流程文件，保留目标项目事实及 managed block 外的规则。
- 内核版本、managed block 和 README 版本统一为 0.3.0。

## 升级

已安装旧版本的项目使用 UPDATE_PROMPT.md 升级；首次安装使用 BOOTSTRAP_PROMPT.md。
Team Loop 内部的 planner、执行模式、返工和人工验收规则保留；可选 docs-review skill 仍单独显式安装。

**完整变更**：[v0.2.0...v0.3.0](https://github.com/gdl1605/codex-teammode-workflow/compare/v0.2.0...v0.3.0)
