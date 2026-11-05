# v0.4.0

本次新增普通开发工作流，并保留显式触发的 Team Loop。

- **普通开发**：主 agent 负责规划、实现和验证，实现后派全新上下文的只读 evaluator 核验。
- **规划时的 Grill-me**：正式计划交付前（包括仅规划），先核对关键取舍的依据。仍未确认的选择通过原生提问卡片逐轮澄清，收到实际回答再写回同一份计划。
- **独立核验**：对照原要求、实际改动和验证证据，检查假设是否被写成事实或执行条件。确定缺口回实现 agent 修复，业务争议交用户裁决。
- **Team Loop**：继续由用户显式启动，Leader 按需调度 Planner、Generator、Scout 和 Evaluator。中英文 README 现分别说明两条流程的启动条件、职责和返工路径。

已安装项目可按 [UPDATE_PROMPT.md](https://github.com/gdl1605/codex-teammode-workflow/blob/v0.4.0/UPDATE_PROMPT.md) 同步规则，保留项目自己的约束和业务文件。

**完整变更**：[v0.3.1...v0.4.0](https://github.com/gdl1605/codex-teammode-workflow/compare/v0.3.1...v0.4.0)
