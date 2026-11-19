# CLAUDE.md

<!-- codex-teammode:managed:start scope=agent-entry version=0.5.0 -->

## 工作流入口

- 只有用户本轮明确要求改变机制（如代码行为、接口或合同）或规划该变更时，才进入开发工作流。默认按[普通开发工作流](docs/workflow/default-workflow.md)执行。
- 在上述范围内，用户本轮以 `@team-loop` 开头或明确要求使用 Team Loop / `teamloop` / 由 Leader 调度多个 subagent 时，改读并按 [Team Loop](docs/workflow/team-loop.md) 执行。讨论、引用、安装或修改 Team Loop 规则，以及历史上用过该模式，都不触发。
- 正常运行、恢复、排障、切换已有配置和产出业务计划或报告沿项目原流程。故障、文件写入和 agent 自拟方案不构成机制变更授权；超出本轮授权的机制改动由用户决定。
- 仅要求核验结果时，只做指定核验。遵守用户和项目对执行权限、职责、review 及 subagent 的明确限制。

## 知识库维护

- 需要项目上下文时，先读 [docs 索引](docs/README.md)，再按任务找到专题主文档与事实来源。
- 按[文档维护规则](docs/workflow/docs-maintenance.md)在收口时核对本轮实际变化，只更新受影响的主文档；无需更新时说明原因。

<!-- codex-teammode:managed:end -->
