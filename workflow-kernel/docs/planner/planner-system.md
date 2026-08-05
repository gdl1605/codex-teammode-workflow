# Planning / Prompt Framing Reference

> 最后更新时间：2026-08-04
> 适用范围：普通工作流中的 plan-only / read-only audit / prompt-framing / review-framing
> 本文主职责：保留当前有效的 planning 规则；旧迁移长规范已压缩为链接化规则
> 推荐下一跳：`planner-input-template.md`

## 用途

本文不定义独立 planner mode。它只服务普通工作流中的 planning / prompt-framing / review-framing。

`@planner` 或“帮我做一轮方案”只是历史兼容入口，等价于普通工作流中的 `plan-only` 或 `read-only audit`，不触发 subagent。

Team Loop 只有在用户明确声明 `@team-loop` / `Team Loop` / `teamloop`，或明确要求 Leader 调度 subagent 时才启用。Team Loop subagent 不默认读取 `docs/planner/*`；相关规则见 `../workflow/team-loop.md`、`../workflow/team-loop-core.md` 和 `../workflow/team-loop-roles/`。

## 关系

- `../../AGENTS.md`：仓库默认入口，声明普通工作流、Team Loop 与 legacy `@planner` alias。
- `../README.md`：docs 入口地图，决定本轮按需补读哪些专题 docs。
- `../workflow/collaboration.md`：普通工作流的协作闭环、证据优先和根因锁定规则。
- `../workflow/prompt-template.md`：普通执行 prompt、输出结构和人工验收清单主落点。
- `planner-input-template.md`：plan-only / read-only audit / review framing 的输入模板。
- `planner-output-schema.md`：普通工作流 `plan / execute / review` 输出 schema。
- `../../workflow/audit-first.md`：根因未锁或实现层不确定时的只读审计和 evidence 回流机制。
- `../workflow/session-startup.md`：执行轮 startup / git / validation / 环境健康检查规则。

## 读取原则

- 默认先读 current code，再按任务需要读对应 docs，最后参考 handoff。
- 当前实现事实的证据优先级固定为 `current code > topic docs > docs/handoff/latest.md > docs/handoff/archive/`；业务意图与外部生命周期事实按各自权限/evidence 路由。
- docs 按需读取；不要为了普通轮次启动而重复读取全量 docs。
- `docs/README.md` 是入口地图，不是全量阅读要求。
- 口头摘要、handoff 和旧 planner 结论都不能替代 current code。
- 如果 docs 与 current code 冲突，先记录当前实现，再判断代码偏离业务合同还是 docs 陈述了错误的实现事实；不能自动让任一方覆盖另一方。

## 启动说明

planning / prompt-framing / review-framing 轮次启动时，应显式说明：

- 已读取文件：入口、current code、专题 docs、handoff 或 evidence。
- 工作流决策：普通工作流，或用户明确声明的 Team Loop。
- 当前职责：plan / execute prompt framing / review framing / docs-process。
- 只读与否：是否允许改代码、是否允许改 docs。
- schema 接入：当前采用 `planner-output-schema.md` 中的 `plan / execute / review` 哪一种。
- audit-first 接入：根因是否已锁；未锁时 evidence 应沉淀到哪里。
- 当前阶段控制面板：当前主线、暂停项、前置条件、下一步允许推进什么、下一步不允许推进什么。
- 仓库状态分层：历史脏项 / 在途开发面、本轮候选范围、不可混入本轮 bundle 的残留。
- docs impact check：本轮是否影响流程规则、计划状态、产品事实或 docs 主落点。

## 阶段职责

### plan-only / read-only audit

- 默认只读，不改代码。
- 先审计 current code，再读必要 docs / evidence。
- 收口目标、非目标、allowed scope、forbidden scope 和风险。
- 根因未锁时先走 `../../workflow/audit-first.md`，不要给猜测性 patch prompt。
- 输出应说明哪些是 verified facts，哪些是 inferences，哪些仍需要人工确认。

### prompt-framing

- 把用户目标、current code 事实、专题 docs 和 evidence 转成可执行 prompt。
- 固定先解释：问题、修改思路、为什么这样改，再给 Markdown prompt。
- 执行 prompt 的结构、输出要求和人工验收清单以 `../workflow/prompt-template.md` 为准。
- 建议实现层必须标注为建议路径，最终应以 current code 审计结果为准做最小调整。

### review-framing

- 只有用户明确要求 review / evaluator，或当前轮次本身是 review 轮，才准备 evaluator prompt。
- 普通执行轮不默认启动独立 evaluator；执行者仍需做最小自检和 docs impact check。
- review 输入至少包含本轮合同层目标、actual diff / 改动摘要、验证结果、风险说明和未完成验证项。
- Team Loop 的 evaluator 操作方式以 `../workflow/team-loop.md` 和 `../workflow/team-loop-roles/evaluator.md` 为准。

## Prompt 规则

- 给目标 coding agent / generator / evaluator 的 prompt 必须使用 Markdown 代码块，方便复制。
- 不要把 prompt 混在普通散文里，不要输出不可复制的碎片式 prompt。
- 合同层和建议实现层必须分开。
- 合同层只放已成立的目标、边界、数据 / 状态机 / 权限约束、输出要求、验收标准和 docs impact check。
- 建议实现层只放推荐切入点、推荐文件范围、推荐修法顺序和切片顺序。
- 不得把建议实现层写成唯一事实。

## 关键约束

- 单轮只允许一个主 feature / 主问题；跨主链请求应先拆轮次。
- 一个主 feature 可以拆多个 slice，但每个 slice 应能到达 clean state。
- 执行轮默认先审计，再最小实现，再验证 / 人工验收，再 docs impact check。
- 涉及 database schema、migration、authorization policy、helper function、RPC / stored procedure、serverless / edge function 时，输出必须说明改的对象、语义差异、是否需要 deploy / apply、当前是否已生效。
- 不要回改旧 migration；优先新增 patch migration。
- 不要通过放宽 policy 掩盖真实问题。
- 除非用户明确要求完整文件，否则输出关键片段、改动文件列表、风险、验证结果和人工复测步骤即可。

## GUI / Computer-use 约束

- plan-only / read-only audit 默认不用 computer-use / GUI。
- plan 轮和只读审计轮禁止截图、禁止 GUI 试跑、禁止通过视觉 hunting 自证结论。
- 若任务明确允许 GUI，只能做极简单只读确认。
- 复杂运行态、视觉强弱、反复状态命中统一交给人工验收或后续执行轮。

## Team Loop 边界

- 普通工作流不默认建议或调度 subagent。
- 如果用户明确启用 Team Loop，Leader 应按 `../workflow/team-loop.md`、`../workflow/team-loop-core.md` 和 `../workflow/team-loop-roles/` 裁剪 subagent read scope。
- 普通 plan-only / read-only audit 只需要说明普通工作流下的读取范围和下一步建议，不主动标注 subagent 块。

## 禁止事项

planning phase 不应：

- 在根因未锁时生成猜测性 patch prompt。
- 把建议路径写成唯一事实。
- 把多个主 feature 混成一个执行轮。
- 让执行者在未做必要 startup 的情况下直接开改。
- 在用户明确要求 review / evaluator 或 Team Loop 时省略对应 review 输入。
- 省略 docs impact check。
- 把 docs 清债扩成无边界整理。
- 自动解析、转写或改写外部 `.rtf` 规范。
- 凭空补写尚未进入仓库 docs 的完整条款。

## 适用范围

适用于：

- 生成 plan prompt。
- 生成执行 prompt。
- 生成 evaluator prompt。
- 对 coding agent 输出做二次规划或二次审查 framing。

不适用于：

- Team Loop subagent 启动合同。
- 纯闲聊、纯翻译、纯文案润色。
- 无代码 / 无 docs 变化的轻量交流。
