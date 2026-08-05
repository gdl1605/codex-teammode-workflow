# AGENTS.md

<!-- codex-teammode:managed:start scope=agent-entry version=0.1.0 -->

## 默认工作方式

- 这是 AI 编码 agent（Codex / Claude Code 等支持 `AGENTS.md` 或 `CLAUDE.md` 约定的工具）的仓库默认工作入口。
- 需要项目上下文时，先读 [`docs/README.md`](docs/README.md)，再按任务进入对应专题 docs。
- 当前实现事实的证据优先级固定为：
  1. `current code`
  2. 对应专题 docs
  3. `handoff/latest.md`
  4. `handoff/archive/`
- 当前用户目标只决定本轮范围，不决定事实真伪。
- 上述顺序只用于判断当前实现行为；明确人工确认 / canonical contract 决定业务意图，部署、验收、法务和发布事实必须有各自直接 evidence。
- docs 与代码冲突时先区分 claim 类型：记录代码当前做了什么，但不得用实现现状静默覆盖已确认的业务合同。

## 轮次规则

- docs-only 轮：只改 `docs/**`，不动业务代码；process 配置轮可按本轮目标改 `workflow/**`、`AGENTS.md` 或 `CLAUDE.md`。
- plan 轮：只出方案，不改代码。
- 执行轮：先审计，再最小实现。
- 默认采用普通工作流：先看 current code，按需补读 docs，最小实现，做 docs impact check，再收口验证或人工验收清单。
- 默认不要改不在本轮目标里的内容。
- 默认优先最小必要修改，不顺手扩模块或重构。

## 普通工作流中的 plan / audit / review 轮次

- 当前仓库只保留两个顶层 AI 工作流：普通工作流与 Team Loop。
- 普通工作流是默认路径；不默认调度 subagent，也不默认拆成独立 planner / generator / evaluator。
- `@planner` 或“帮我做一轮方案”是历史兼容入口，不再表示独立 planner 模式；等价于普通工作流中的 `plan-only` 或 `read-only audit` 轮。
- plan-only / read-only audit 轮默认只读：
  - 先读 current code
  - 先做只读审计
  - 不直接改代码
  - 不把建议实现层写成已验证事实
- plan / execute / review 输出结构暂时沿用 [`docs/planner/planner-output-schema.md`](docs/planner/planner-output-schema.md)，并显式声明当前采用 `plan / execute / review` 哪一种 schema。
- plan-only / read-only audit 输入模板暂时见 [`docs/planner/planner-input-template.md`](docs/planner/planner-input-template.md)。
- planning / prompt-framing / review-framing 详细规范暂时见 [`docs/planner/planner-system.md`](docs/planner/planner-system.md)。
- 普通工作流中的 planning 阶段，对当前实现事实的证据优先级仍是：
  1. `current code`
  2. 对应专题 docs
  3. `handoff/latest.md`
  4. `handoff/archive/`
- 当根因未锁、建议实现层不确定、当前看到的是现象不是原因时，优先走 [`workflow/audit-first.md`](workflow/audit-first.md)。
- plan / audit / review 轮每轮必须显式说明工作流决策：默认采用普通工作流；只有用户明确声明 Team Loop 时，才进入 Leader / subagent 调度。
- plan-only / read-only audit 轮默认不使用 computer-use / GUI，不截图、不做运行态 hunting；若确需调用，只允许极简单只读确认，复杂验证交给人工或后续执行轮。
- planning 输出应包含“当前阶段控制面板”：当前主线、暂停项、前置条件、下一步允许推进什么、下一步不允许推进什么。
- planning 阶段必须分层表达仓库状态：历史脏项 / 在途开发面、本轮真实候选范围、不可混入本轮 bundle 的残留。
- planning 阶段目标是产出 plan、只读审计 prompt，或基于 evidence 产出执行 prompt；不得跳过审计做想象式方案。

## Team Loop 模式

- Team Loop 是单独的显式模式，不是普通工作流的自动升级。
- 只有当用户 prompt 以 `@team-loop` 开头，或明确说“使用 Team Loop / teamloop / Leader 调度多个 subagent / 类 team-mode 闭环 / 自动返工直到人工验收”时，当前 agent 才进入 Team Loop 模式。
- Team Loop 规范落点见 [`docs/workflow/team-loop.md`](docs/workflow/team-loop.md)。
- 派生 subagent 时，`Context Bootstrap` 默认使用 `slim`：当前工具入口 `AGENTS.md` 或 `CLAUDE.md` 二选一、`docs/README.md`、`docs/workflow/team-loop-core.md`、对应 `docs/workflow/team-loop-roles/<role>.md`、本轮必要 docs / code / evidence；完整 `docs/workflow/team-loop.md` 仅在需要核对完整规范时加入，`workflow/audit-first.md` 仅在根因未锁 / 高风险 / 审计回流时加入，Team Loop subagent 不默认读取 `docs/planner/*`。
- Team Loop 是可选增强流程，不替代普通执行轮；用户未明确触发时，不默认升级为 Team Loop。
- Leader 主线程是唯一调度者：
  - Leader 派 planner / generator / scout / evaluator。
  - Leader 派生任何 subagent 时必须附带裁剪后的 `Context Bootstrap`，并要求 subagent 输出 `Read Scope Ack`。
  - Leader 只负责调度、裁剪证据、验证和汇总；进入 Team Loop 后不得直接改代码或 docs。
  - Team Loop 中的 planner 是 Leader 调度的只读 subagent，不是旧的独立 planner 模式。
  - 所有 subagent 只能回报 Leader。
  - subagent 之间禁止直接通信。
  - generator / evaluator / scout 不得自行派生 subagent。
- Team Loop 支持两种模式：
  - `plan-gated`：适合涉及数据合同 / 权限 / 状态机 / 高风险产品域 / 复杂资源链路 / 根因未锁的任务，或用户明确要求先批准 plan 的任务（目标仓库应自行列出具体高风险域）；planner plan 必须先交给用户确认，批准后才派 generator。
  - `auto-execute`：适合文案、轻 UI、局部样式、docs 小修和 allowed scope 清楚的低风险任务；Leader 在 planner 快速收口后可直接派 generator，但不能跳过 generator 自己实现。
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
- docs impact 是增量维护微循环；输出还必须给出 `reconciliation_recommended: yes/no + reason`，但不得自动调用 `$docs-review`。

## `$docs-review` 可选事实校正

- `$docs-review` 是人工触发的跨文档事实校正宏循环，只在用户明确输入 `$docs-review`、要求“运行 docs-review”或明确要求全局项目事实校正时使用；普通 docs 修改不触发。
- Codex 中优先在 Plan Mode 只读审计并使用原生提问完成业务事实裁决；只有同一任务中已有人工批准、decision-complete 计划时，才在 Default Mode 接受 `$docs-review apply`。
- 它按 claim 类型选择事实权限：current code / types / tests 决定实现事实，schema / migration 内容决定数据合同但不证明已 apply，人工确认 / canonical contract 决定业务意图，部署 / 验收 / 法务 / 发布必须有各自直接 evidence。
- apply 只修改批准列表中的 docs；baseline 漂移必须停下重审，不能顺手修改业务代码、schema、migration、测试或外部环境。
- v2 计划必须通过 schema-2 plan gate：scanner schema 4 的每条 finding 都以 source fingerprint 精确绑定结构化 resolution group、人工权限范围、证据、目标语义和批准文件；Claim ID、审计 ID 与 validator 专用锚点不得写进业务 docs。
- apply 后按文件体积做分片独立审计，最多并发三个 fresh shard auditor；主 Agent 必须无损保存并校验原始 JSON。全部 shard pass 后还要调用全新的 synthesis auditor 做跨分片终审；任一 deficiency 先停下向人类报告并等待明确修正授权。
- 修正轮只允许按角色、文件/evidence/consumer hash 与条款语义复用完全未变化且已 pass 的 shard；失败或变化的 shard 必须 fresh 重跑，synthesis 永不复用。
- 可选 skill 源码位于 workflow package 的 `skills/docs-review/`；个人全局 skill 只通过 `install.sh --install-docs-review` 显式安装，工作流升级不得静默覆盖。
- 完整宏循环规则见 [`docs/workflow/docs-maintenance.md`](docs/workflow/docs-maintenance.md)。

## 其他约束

- 涉及项目知识时，以 `docs/README.md` 为入口地图，不要把本文件写成项目百科。
- 若当前轮次没有明确目标，先补上下文或做只读审查，不要直接写实现。

<!-- codex-teammode:managed:end -->
