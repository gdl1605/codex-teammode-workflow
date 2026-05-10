# Team Loop Workflow

> 最后更新时间：2026-05-02
> 适用范围：需要由 Leader 主线程调度多个独立 subagent 的类 team-mode 闭环
> 本文主职责：定义 plan-gated / auto-execute 两种模式、角色边界、通信规则、Context Bootstrap、Read Scope Ack、scout 支援机制和人工验收停点
> 推荐下一跳：`collaboration.md`、`prompt-template.md`

## 1. 定位

Team Loop 是当前人工工作流的可选增强形态。

它用于让一个 Leader 主线程调度多个独立 subagent，形成：

```text
User
  <-> Leader 主线程
      -> planner subagent
      -> generator subagent
      -> scout subagent A / B
      -> evaluator subagent
      -> human acceptance
```

Team Loop 运行在 Codex 或 Claude Code 等单个编码 agent 会话内，由 Leader 主线程负责派生、等待、汇总和再派发 subagent。

Team Loop 中的 `planner subagent` 是 Leader 调度的内部只读角色，不等于旧独立 planner mode，也不等于普通工作流里的 planning phase。

## 2. 非目标

Team Loop 不做：

- 不让 subagent 彼此直接通信。
- 不让 generator / evaluator / scout 自己派生 subagent。
- 不自动进入 `accepted`。
- 不替代 `current code > docs > handoff` 的事实优先级。
- 不把 scout 结论直接当作 generator 的正式输入。

## 3. 两种模式

### 3.1 plan-gated

适用：

- 数据库 schema / migration / 服务端函数（RPC / 存储过程 / serverless 或 edge function 等）。
- 权限、状态机、数据合同。
- 高风险产品域（例如多步状态机、跨角色协作链路、并发受限资源；具体列表由目标仓库维护）。
- 复杂资源链路（如上传、处理、派生、缓存、发布等多步骤资源合同）。
- 根因未锁或 current code / docs / handoff 存在冲突。
- 用户明确要求先看 plan 再批准执行。

流程：

```text
Leader 接收任务
-> 派 planner subagent
-> Leader 汇总 plan 并交给用户
-> 用户批准执行
-> Leader 派 generator subagent
-> generator 如需支援，只能向 Leader 提交 Scout Request
-> Leader 决定是否派 scout subagent
-> scout 只回 Leader
-> Leader 整理 Evidence Pack 给 generator
-> generator 实现
-> Leader 验证
-> Leader 派 evaluator subagent
-> P0 / P1 不通过则返工
-> 通过则停在 human_acceptance_required
```

### 3.2 auto-execute

适用：

- 文案。
- 轻 UI。
- 局部样式。
- docs 小修。
- allowed scope 清楚、forbidden scope 简单、无需人工先批准 plan 的低风险任务。

流程：

```text
Leader 接收任务
-> 派 planner subagent 快速只读收口
-> Leader 判断 allowed scope / forbidden scope 是否足够清楚
-> 满足条件则直接派 generator subagent
-> generator 必要时可向 Leader 申请 1 个 scout
-> scout 只回 Leader
-> Leader 整理 Evidence Pack 给 generator
-> generator 实现
-> Leader 验证
-> Leader 派 evaluator subagent
-> P0 / P1 不通过则返工
-> 通过则停在 human_acceptance_required
```

auto-execute 不是跳过 Team Loop 的 planner subagent，而是不需要把 planner subagent 的 plan 先交给用户批准。

## 4. 通信硬规则

允许：

```text
User <-> Leader
Leader -> planner subagent / generator / scout / evaluator
planner subagent / generator / scout / evaluator -> Leader
Leader -> generator with Evidence Pack
Leader -> evaluator with Evaluation Bundle
```

禁止：

```text
planner subagent -> generator
generator -> scout
scout -> generator
evaluator -> generator
planner subagent / generator / scout / evaluator 彼此直接通信
generator 自己派生 subagent
evaluator 自己派生 subagent
scout 自己派生 subagent
```

Leader 不是简单转发器。Leader 必须对 subagent 产物做裁剪、去噪、可信度标注和正式输入封装。

## 5. 角色边界

### Leader

Leader 是唯一调度者。

职责：

- 与用户确认目标、模式、风险和停点。
- 判断 `plan-gated / auto-execute`。
- 派 planner subagent / generator / scout / evaluator，并为每次派生附带 `Context Bootstrap`。
- 核验每个 subagent 输出中的 `Read Scope Ack`，确认其已读材料覆盖本轮合同。
- 审批或拒绝 generator 的 Scout Request。
- 汇总 scout 输出，形成 Leader Evidence Pack。
- 跑验证命令并整理 validation output。
- 形成 Evaluation Bundle 给 evaluator。
- 根据 evaluator 输出决定返工、阻塞或停到 `human_acceptance_required`。

禁止：

- 不绕过 generator 做大范围实现。
- 不替 evaluator 自评通过。
- 不自动 accepted。
- 不让 subagent 之间直接通信。
- 不把 scout 原文未经裁剪直接交给 generator。

### Planner Subagent

planner subagent 默认只读。

职责：

- 输出 `Read Scope Ack`，说明实际读取的入口、docs、code、handoff 或 evidence。
- 收口本轮问题、目标和非目标。
- 判断风险模式。
- 输出 allowed scope / forbidden scope。
- 定义 minimum progress unit。
- 给出 generator 启动前的 current code 核对清单。
- 给出 generator 的建议 `Context Bootstrap` / required read scope。
- 说明是否允许 scout，以及可能的 scout 问题。
- 给出 evaluator focus。

禁止：

- 不改代码。
- 不省略 `Read Scope Ack`。
- 不把建议实现层写成已验证事实。
- 不绕过 current code 证据做想象式方案。

### Generator

generator subagent 是默认唯一写代码角色。

职责：

- 启动前读取 Leader 给出的 `Context Bootstrap`。
- 输出 `Read Scope Ack`，说明已重新审计的 current code、docs、handoff 或 evidence。
- 消费 Leader 给出的 planner subagent handoff 和 Evidence Pack，但不把它们当作 current code 的替代品。
- 按 current code 做最小实现。
- 若 `Context Bootstrap`、Evidence Pack、docs 与 current code 冲突，以 current code 为准，并回报 Leader。
- 如审计范围过大，向 Leader 提交 Scout Request。
- 输出 touched files、修改摘要、验证建议和给 Leader 的 evaluator notes。
- 明确 docs impact。

禁止：

- 不直接读取 scout 原文。
- 不直接联系 scout / evaluator。
- 不派生 subagent。
- 不省略 `Read Scope Ack`。
- 不仅凭 planner handoff / Evidence Pack 改代码而不重新审计 current code。
- 不自称 passed。
- 不越过 forbidden scope。

### Scout

scout subagent 是只读线索收集角色。

职责：

- 只回答 Leader 指定的问题。
- 只读必要 current code、docs、handoff 或 evidence。
- 输出 `Scout Evidence`；其中 `files_read` 等价于本角色的 `Read Scope Ack`。
- 输出 verified facts、inferences、unresolved 和 citations。
- 帮助缩短 generator 的审计路径。

禁止：

- 不改代码。
- 不改 docs。
- 不设计完整实现方案。
- 不评价 generator 是否通过。
- 不直接把结论传给 generator。

### Evaluator

evaluator subagent 是独立核验角色。

职责：

- 只消费 Leader 提供的 Evaluation Bundle。
- 输出 `Read Scope Ack`，说明核验所读的 Evaluation Bundle、diff、docs 和 code。
- 核验 generator 的 `Read Scope Ack` 是否覆盖关键文件和合同 docs。
- 不继承 generator 完整对话叙事。
- 优先找 P0 / P1 阻塞问题。
- 若缺少关键 docs / code / diff 导致无法判断，应输出 `request changes` 或 `blocked`，而不是 pass。
- P2 / P3 默认进入 residual risk、backlog 或后续优化。
- 输出 pass / request changes / blocked。

禁止：

- 不改代码。
- 不省略 `Read Scope Ack`。
- 不直接联系 generator。
- 不自动 accepted。
- 不把个人偏好写成阻塞，除非违反合同、业务逻辑、可访问性或可用性。

## 6. Context Bootstrap

Leader 每次派生 planner subagent / generator / scout / evaluator 时，必须附带 `Context Bootstrap`。它不是可选背景摘要，而是 subagent 启动合同；subagent 必须按该合同读取材料并回报实际 read scope。

最低字段：

```md
## Context Bootstrap

- repo_entry:
  - AGENTS.md
  - CLAUDE.md
  - docs/README.md
- workflow_docs:
  - docs/workflow/team-loop.md
  - docs/workflow/prompt-template.md
  - docs/workflow/collaboration.md
  - workflow/audit-first.md（根因未锁 / 高风险 / 审计回流时必读）
- task_docs:
- handoff_or_evidence:
- fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:
```

规则：

- `repo_entry` 默认必须包含 `AGENTS.md`、`CLAUDE.md` 和 `docs/README.md`。
- `task_docs` 由 Leader 按 `docs/README.md` 的入口地图裁剪，不能要求 subagent 盲读全量 `docs/`。
- 允许 Leader 缩小专题 docs 范围，但必须说明裁剪理由，并要求 subagent 在 `Read Scope Ack` 中列出未读但可能相关的材料。
- `handoff_or_evidence` 按阶段选择；根因未锁、高风险或审计回流时优先引用 `docs/evidence/<feature>-audit.md` 或 root `workflow/audit-first.md` 的审计产物。
- Evidence Pack 不能替代 generator 自己读取 current code。
- Evaluation Bundle 是 evaluator 的叙事入口；actual diff、referenced files、required docs 是 evaluator 可读取的核验材料。

## 7. Read Scope Ack

每个 subagent 输出开头必须包含 `Read Scope Ack`。Leader 需要先核验该回执，再采纳 subagent 结论、Evidence Pack 或 evaluation verdict。

统一模板：

```md
## Read Scope Ack

- files_read:
- docs_read:
- code_read:
- evidence_or_handoff_read:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:
```

角色要求：

- planner subagent 必须证明读过 `AGENTS.md` 或 `CLAUDE.md`、`docs/README.md`、Team Loop 主文档、prompt-template、本轮相关 docs / code。
- generator 必须证明启动前重新审计了 current code；不能只消费 planner handoff / Evidence Pack。
- scout 保留 `Scout Evidence` 模板；其中 `files_read` 等价于本角色的 `Read Scope Ack`。
- evaluator 必须证明只消费 Leader 的 Evaluation Bundle 作为叙事入口，并读取必要 diff / code / docs 做独立核验。
- 如果 subagent 发现 `Context Bootstrap` 与 current code、专题 docs 或 allowed scope 冲突，必须写入 `scope_conflicts`，由 Leader 决定返工、补 evidence 或 blocked。

## 8. Scout Request

generator 只能向 Leader 提交 Scout Request：

```md
## Scout Request to Leader

- reason:
- question:
- suggested_read_scope:
- must_not_read:
- expected_evidence:
- why_generator_should_pause:
- suggested_scout_count: 1 / 2
```

允许申请 scout 的情况：

- planner subagent 的 current code 核对范围过大。
- 涉及多个互不重叠的页面 / service / helper。
- generator 发现 current code 与 planner 建议路径冲突。
- docs / handoff / current code 口径不一致。
- generator 能提出明确问题和读取范围，而不是泛泛要求“帮我看看”。

Leader 可以：

- 批准。
- 缩小 scope 后批准。
- 拒绝。
- 升级为 plan-gated。
- 停到 blocked。

## 9. Scout Evidence

scout 只能回 Leader：

```md
## Scout Evidence to Leader

- question_answered:
- files_read:
- verified_facts:
- inferences:
- unresolved:
- citations:
- confidence:
```

`files_read` 等价于 scout 的 `Read Scope Ack`。如果 scout 发现 Leader 给出的 read scope 不足，应在 `unresolved` 中说明缺失材料，而不是扩范围自行设计完整方案。

Scout Evidence 不是 generator 正式输入。只有经 Leader 整理后的 Evidence Pack 才能交给 generator。

## 10. Leader Evidence Pack

Leader 给 generator 的正式证据包：

```md
## Leader Evidence Pack for Generator

- context_bootstrap:
- required_read_scope:
- source_evidence:
- accepted_facts:
- rejected_or_low_confidence_notes:
- relevant_files:
- implementation_constraints:
- unresolved:
- generator_startup_ack_required: yes
- next_generator_instruction:
```

Leader 应把 scout 的低可信推断、无关发现、重复信息和越界建议过滤掉。Leader Evidence Pack 不能替代 generator 的 current code 审计；generator 必须输出 `Read Scope Ack` 后才能进入实现结论。

## 11. Evaluation Bundle

Leader 给 evaluator：

```md
## Evaluation Bundle

- original_problem:
- mode:
- context_bootstrap_used:
- planner_handoff:
- generator_result:
- generator_read_scope_ack:
- leader_evidence_pack:
- required_evaluator_read_scope:
- actual_diff:
- validation_output:
- docs_impact_claim:
- known_residual_risks:
- human_acceptance_target:
```

Evaluation Bundle 应避免包含 generator 完整对话历史，除非 evaluator 明确需要核对某个 claim。Evaluator 要核验 `Context Bootstrap` 是否被执行、generator 的 read scope 是否覆盖关键文件、actual diff 是否符合 allowed scope、docs impact check 是否匹配本轮事实变化。

## 12. 状态与返工

Team Loop 使用轻量状态，不引入 repo 状态机：

```text
planning
waiting_for_human_plan_approval
generating
scout_requested
scouting
evaluating
changes_requested
human_acceptance_required
blocked
```

默认：

```text
max_rounds = 3
```

返工条件：

- evaluator 发现 P0 / P1。
- validation failed 且无明确 human waiver。
- generator 越过 forbidden scope。
- generator 省略 `Read Scope Ack` 或 read scope 明显缺少关键 current code / docs。
- actual diff 与 planner subagent allowed scope 不符。

不默认返工：

- P2 / P3。
- 文案偏好。
- 可由人工验收覆盖的小视觉差异。
- 已明确标注 residual risk 的非阻塞项。

终态：

- `human_acceptance_required`
- `blocked`

`accepted` 永远只能由用户人工表达，不由 Team Loop 自动写入。

## 13. 与现有工作流的关系

Team Loop 是可选增强流程，不替代普通执行轮。

默认执行轮仍按 `collaboration.md` 的 `planning phase -> generator -> evaluator -> human acceptance` 理解。只有当用户明确使用 `@team-loop`、要求类 team-mode 闭环，或明确要求 Leader 调度多个 subagent 时，才进入 Team Loop。

docs-only、plan-only、read-only audit 轮不应被强制升级为 Team Loop。

## 14. 触发 prompt 模板

```md
@team-loop

task_id: <short-task-id>
mode: plan-gated / auto-execute
max_rounds: 3

problem:
<本轮要解决的问题、目标和验收停点。>

constraints:
- allowed scope: <允许读取 / 修改的文件、模块或文档>
- forbidden scope: <明确禁止触碰的文件、模块、业务语义或外部系统>
- validation: <Leader 需要运行或人工检查的验证项>

context_bootstrap:
- repo_entry:
  - AGENTS.md
  - CLAUDE.md
  - docs/README.md
- workflow_docs:
  - docs/workflow/team-loop.md
  - docs/workflow/prompt-template.md
  - docs/workflow/collaboration.md
  - workflow/audit-first.md（根因未锁 / 高风险 / 审计回流时必读）
- task_docs:
- handoff_or_evidence:
- fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:
- read_scope_ack_required: 每个 subagent 输出必须带 files_read / docs_read / code_read / evidence_or_handoff_read

team_loop:
- Leader 是唯一调度者
- Leader 每次派生 subagent 必须附带 Context Bootstrap
- planner subagent / generator / scout / evaluator 只能回报 Leader
- planner / generator / evaluator / scout 都必须回报 Read Scope Ack
- planner 是 Team Loop 内部只读 subagent，不代表旧独立 planner mode 或普通工作流 planning phase
- subagent 之间禁止直接通信
- generator 如审计范围过大，只能向 Leader 提交 Scout Request
- scout 只读收集线索，只回 Leader
- Leader 整理 Evidence Pack 后再交给 generator
- audit-first 场景必须复用 workflow/audit-first.md 的必读与 evidence 回流骨架
- Leader 跑验证
- Leader 派 evaluator 独立核验
- P0 / P1 不通过则最多返工 3 轮
- 最后停在 human_acceptance_required
```
