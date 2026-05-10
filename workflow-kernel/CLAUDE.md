# CLAUDE.md

## 默认工作方式

- 这是 AI 编码 agent（Codex / Claude Code 等支持 `AGENTS.md` 或 `CLAUDE.md` 约定的工具）的仓库默认工作入口。
- 需要项目上下文时，先读 [`docs/README.md`](docs/README.md)，再按任务进入对应专题 docs。
- 事实判断优先级固定为：
  1. `current code`
  2. 对应专题 docs
  3. `handoff/latest.md`
  4. `handoff/archive/`
- 当前用户目标只决定本轮范围，不决定事实真伪。

## 轮次规则

- docs-only 轮：只改 `docs/**`，不动业务代码；process 配置轮可按本轮目标改 `workflow/**`、`AGENTS.md` 或 `CLAUDE.md`。
- plan 轮：只出方案，不改代码。
- 执行轮：先审计，再最小实现。
- 默认不要改不在本轮目标里的内容。
- 默认优先最小必要修改，不顺手扩模块或重构。

## 普通工作流中的 plan / audit / review 轮次

- 当前仓库只保留两个顶层 AI 工作流：普通工作流与 Team Loop。
- `@planner` 或“帮我做一轮方案”是历史兼容入口，不再表示独立 planner 模式；等价于普通工作流中的 `plan-only` 或 `read-only audit` 轮。
- plan-only / read-only audit 轮默认只读：
  - 先读 current code
  - 先做只读审计
  - 不直接改代码
  - 不把建议实现层写成已验证事实
- plan / execute / review 输出结构暂时沿用 [`docs/planner/planner-output-schema.md`](docs/planner/planner-output-schema.md)，并显式声明当前采用 `plan / execute / review` 哪一种 schema。
- plan-only / read-only audit 输入模板暂时见 [`docs/planner/planner-input-template.md`](docs/planner/planner-input-template.md)。
- planning / prompt-framing / review-framing 详细规范暂时见 [`docs/planner/planner-system.md`](docs/planner/planner-system.md)。
- 普通工作流中的 planning 阶段事实优先级仍是：
  1. `current code`
  2. 对应专题 docs
  3. `handoff/latest.md`
  4. `handoff/archive/`
- 当根因未锁、建议实现层不确定、当前看到的是现象不是原因时，优先走 [`workflow/audit-first.md`](workflow/audit-first.md)。
- plan / audit / review 轮每轮必须显式说明 subagent 决策：若拆，写清 `Subagent A / B / C` 的审计目标、读取文件、期望输出；若不拆，说明为什么串行更合适。
- plan-only / read-only audit 轮默认不使用 computer-use / GUI，不截图、不做运行态 hunting；若确需调用，只允许极简单只读确认，复杂验证交给人工或后续执行轮。
- planning 输出应包含“当前阶段控制面板”：当前主线、暂停项、前置条件、下一步允许推进什么、下一步不允许推进什么。
- planning 阶段必须分层表达仓库状态：历史脏项 / 在途开发面、本轮真实候选范围、不可混入本轮 bundle 的残留。
- planning 阶段目标是产出 plan、只读审计 prompt，或基于 evidence 产出执行 prompt；不得跳过审计做想象式方案。

## Team Loop 模式

- 当用户 prompt 以 `@team-loop` 开头，或明确要求“类 team-mode 闭环 / Leader 调度多个 subagent / 自动返工直到人工验收”时，当前 agent 进入 Team Loop 模式。
- Team Loop 规范落点见 [`docs/workflow/team-loop.md`](docs/workflow/team-loop.md)。
- Team Loop 是可选增强流程，不替代普通执行轮；用户未明确触发时，不默认升级为 Team Loop。
- Leader 主线程是唯一调度者：
  - Leader 派 planner / generator / scout / evaluator。
  - Leader 派生任何 subagent 时必须附带 `Context Bootstrap`，并要求 subagent 输出 `Read Scope Ack`。
  - Team Loop 中的 planner 是 Leader 调度的只读 subagent，不是旧的独立 planner 模式。
  - 所有 subagent 只能回报 Leader。
  - subagent 之间禁止直接通信。
  - generator / evaluator / scout 不得自行派生 subagent。
- Team Loop 支持两种模式：
  - `plan-gated`：适合涉及数据合同 / 权限 / 状态机 / 高风险产品域 / 复杂资源链路 / 根因未锁的任务，或用户明确要求先批准 plan 的任务（目标仓库应自行列出具体高风险域）；planner plan 必须先交给用户确认，批准后才派 generator。
  - `auto-execute`：适合文案、轻 UI、局部样式、docs 小修和 allowed scope 清楚的低风险任务；Leader 在 planner 快速收口后可直接派 generator。
- generator 如审计范围过大，只能向 Leader 提交 `Scout Request`；scout 只能只读收集线索并回报 Leader；Leader 必须整理 `Evidence Pack` 后再交给 generator。
- audit-first 场景必须复用 `workflow/audit-first.md` 的必读骨架和 evidence 回流要求。
- evaluator 只消费 Leader 提供的 `Evaluation Bundle`，不继承 generator 完整对话叙事；P0 / P1 阻塞返工，P2 / P3 默认进入 residual risk、backlog 或人工验收。
- Team Loop 运行中可进入 `changes_requested` 并返工；最终只能停在 `human_acceptance_required` 或 `blocked`；不得自动进入 `accepted`。

## 输出规则

- 默认不要贴完整文件全文，除非用户明确要求。
- 需要验证时，优先写清人工验收清单。
- 如果一轮改动涉及数据库 schema / migration / 服务端函数（RPC / 存储过程 / serverless 或 edge function 等），输出必须说明改的是哪个对象、语义差异、是否需要 deploy / apply、以及当前是否已生效。

## docs impact check

- 每轮结束前，必须判断本轮是否改变了：项目事实、产品合同 / 边界、当前阶段已成立能力、候选方向 / 后置方向、计划状态、长期技术债 / 结构债 / 体验债 / 流程债。
- 若有变化，必须更新对应 docs 主落点；不要把同一事实分散回写到多个文档。
- 若无变化，输出里也必须明确写“本轮无需更新 docs”及原因。
- docs impact check 只要求更新被本轮语义真正影响的主落点，不要求每轮全量刷新 docs。

## 其他约束

- 涉及项目知识时，以 `docs/README.md` 为入口地图，不要把本文件写成项目百科。
- 若当前轮次没有明确目标，先补上下文或做只读审查，不要直接写实现。
