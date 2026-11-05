# FAQ

### 这是框架还是运行时？

都不是。Codex-teammode Workflow 是一组 Markdown 规则、prompt 和 docs scaffold。真正“执行”的是你打开的 Codex 或 Claude Code 会话。

### 支持哪些 AI 工具？

第一版明确支持：

- Codex：通过 `AGENTS.md` 入口读取工作流规则。
- Claude Code：通过 `CLAUDE.md` 入口读取同一套工作流规则。

其他工具如果支持类似的项目规则文件，也可以手动适配，但当前版本不把它们列为一线支持对象。

### 为什么同时生成 `AGENTS.md` 和 `CLAUDE.md`？

因为 Codex 和 Claude Code 的项目入口约定不同。这个项目会让两份文件保持同一套协作流程，避免同一个仓库里不同 agent 读到不同规则。

### Team Loop 是什么？

Team Loop 是一个显式触发、在单个人类驱动会话里运行的多角色流程。Leader 是主线程，负责调度 planner、generator、scout、evaluator，但不直接实现或改文件。planner / scout 可跨 dispatch 复用，generator / evaluator 每轮 fresh。它不是后台服务，也不是自动化多 agent 平台。

### 为什么不自动 accepted？

因为“agent 说完成了”和“改动真的正确”不是同一件事。普通工作流报告实际核验范围和剩余事项，Team Loop 停在 `human_acceptance_required` 或 `blocked`；人工验收都由用户表达，独立核验不代替它。

### 会覆盖我已有的文件吗？

Bootstrap prompt 明确要求先审查再合并。如果目标仓库已有 `AGENTS.md`、`CLAUDE.md`、`docs/` 或 `workflow/`，目标 agent 应保留已有规则并做合并。

### 现在为什么中文优先？

这套工作流最初来自中文项目实践，核心 kernel 仍以中文表达最准确。README 已提供双语入口；英文 kernel 翻译欢迎 PR。

### 这是 OpenAI 官方项目吗？

不是。Codex-teammode Workflow 是非官方社区项目，未获得 OpenAI 认可、赞助或背书。

### 可以用于非软件项目吗？

可以部分借鉴，但默认事实优先级是 `current code > docs > handoff`，偏软件项目。非软件项目需要把 `current code` 替换成自己的 primary artifact。

### 没有触发 Team Loop 时会怎样？

开发规划与维护默认使用[普通工作流](./workflow-kernel/docs/workflow/default-workflow.md)：主 agent 在正式计划交付前核对关键取舍来源、追问未确认选择，授权实现后派 fresh 只读 evaluator。确定缺口直接回实现 agent 修复，事实未知先补证，业务争议给用户裁决。仅要求独立 evaluator 或讨论、引用、修改 Team Loop 规则不会启动 Team Loop。

### evaluator 怎么知道该审查什么？

Review Request 提供用户原话和纠正、有效合同、确认后的计划、明确标注的假设、实际 diff、消费者和验证证据。evaluator 从原要求确定目标，从实际改动和真实调用关系确定影响范围；主 agent 的总结只用于导航。重点查假设是否被写成事实或升级为执行条件，不只比较两份总结是否一致。角色合同见[独立 evaluator](./workflow-kernel/docs/workflow/independent-evaluator.md)。

### 是否必须安装外部 grill-me skill？

不需要。普通流程内置需求追问：事实由 agent 查，正式计划交付前核对关键取舍的原决定或委托依据，尚未确认的关键选择先问用户，答案回写同一份计划。不设必须问满的轮数，也不新增每次实现都要整份计划批准的要求。

### 只让我产出计划，也要做 Grill-me 吗？

要在正式计划交付前完成关键取舍来源核对。已有决定、有效合同或明确委托足够时，简短指出依据，无需重复问；仍是 agent 建议、会改变行为或交付范围的选择，先问再定稿。不能因为已选好默认方案就认为没有未决项。“仅规划”只意味着交付后不自动实现或运行实现后 evaluator，不豁免前面的澄清。用户只要待确认草案时可先展示草案，保留未决项，不冒充已确认计划。

### Grill-me 用什么形式提问？

默认实际调用原生结构化提问工具，发成可选择的卡片。Codex 暴露 `request_user_input_async` 时使用它，按当前 schema 和模式限制调用。每题说明取舍、选项影响和推荐，当前可回答的独立问题一起问，等实际回答后更新同一份计划，再推进依赖问题。不能只在正文列题却声称已发卡片，也不能把推荐、预选、工具返回或超时当作答案。工具确实不可用或受限时，说明限制后用编号文本选项；无需新增 WebSocket 服务。
