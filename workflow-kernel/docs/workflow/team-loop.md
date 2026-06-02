# Team Loop Workflow

> 最后更新时间：2026-06-02
> 适用范围：需要由 Leader 主线程调度多个独立 subagent 的类 team-mode 闭环
> 本文主职责：定义 plan-gated / auto-execute 两种模式、角色边界、通信规则、Context Bootstrap、Read Scope Ack、scout 支援机制和人工验收停点
> 推荐下一跳：`team-loop-core.md`、`team-loop-roles/`

## 1. 定位

Team Loop 是当前人工工作流的可选增强形态，只在用户明确声明使用 `@team-loop`、`Team Loop`、`teamloop`，或明确要求 Leader 调度 subagent 时启用。

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

普通工作流是默认路径。即使任务复杂、根因未锁或风险较高，也不自动升级为 Team Loop；Leader 只能提示用户可另开 Team Loop，不能替用户默认启用。

## 2. 非目标

Team Loop 不做：

- 不让 subagent 彼此直接通信。
- 不让 generator / evaluator / scout 自己派生 subagent。
- 不自动进入 `accepted`。
- 不替代 `current code > docs > handoff` 的事实优先级。
- 不把 scout 结论直接当作 generator 的正式输入。
- 不作为普通工作流的默认执行方式。
- 不复用 generator / evaluator role session。

## 3. 两种模式

### 3.1 plan-gated

进入 Team Loop 后，`plan-gated` 适用于用户希望先批准 plan 再执行的轮次。模式选择只影响 Team Loop 内部节奏，不作为自动触发 Team Loop 的条件。

特点：

- planner 收口后先交给用户确认。
- 用户批准后再派 generator。
- 最后仍停在 `human_acceptance_required`。

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

进入 Team Loop 后，`auto-execute` 适用于用户允许 Leader 在 planner 快速收口后直接派 generator 的轮次。

特点：

- 不需要把 planner subagent 的 plan 先交给用户批准。
- `auto-execute` 只跳过人工 plan approval，不跳过 generator。
- Leader 仍要核验 planner 输出、generator read scope 和 evaluator verdict。
- 最后仍停在 `human_acceptance_required`。

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

auto-execute 不是跳过 Team Loop 的 planner subagent，也不是让 Leader 自己实现；它只是不需要把 planner subagent 的 plan 先交给用户批准，后续实现仍必须由 fresh generator subagent 完成。

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

本节是完整主规范中的角色摘要。Leader 派生 subagent 时，不应把完整主规范或所有角色段落都作为默认上下文发给每个角色；默认应使用 `docs/workflow/team-loop-core.md` 和对应 `docs/workflow/team-loop-roles/<role>.md`。

### Leader

Leader 是唯一调度者。

职责：

- 与用户确认目标、模式、风险和停点。
- 判断 `plan-gated / auto-execute`。
- 派 planner subagent / generator / scout / evaluator；复用 planner / scout 时附带 cache manifest 和 freshness check，新建或 fresh 角色时附带 `Context Bootstrap`。
- 维护 planner / scout role session 复用状态、dispatch count 和失效条件。
- 核验每个 subagent 输出中的 `Read Scope Ack`，确认其已读材料覆盖本轮合同。
- 审批或拒绝 generator 的 Scout Request。
- 汇总 scout 输出，形成 Leader Evidence Pack。
- 跑验证命令并整理 validation output。
- 形成 Evaluation Bundle 给 evaluator。
- 根据 evaluator 输出决定返工、阻塞或停到 `human_acceptance_required`。

禁止：

- 不绕过 generator 做任何实现，包括单文件 patch、小范围 UI / docs patch 或低风险修复。
- 不替 evaluator 自评通过。
- 不自动 accepted。
- 不让 subagent 之间直接通信。
- 不把 scout 原文未经裁剪直接交给 generator。

### Planner Subagent

planner subagent 默认只读。

职责：

- 输出 `Read Scope Ack`，说明实际读取的入口、docs、code、handoff 或 evidence。
- 复用时只输出本轮 delta：需要额外读取的 docs / code / evidence、无需读取的 docs 及理由、建议执行路径和 scout 需求。
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
- 复用时不复述已验证缓存的基线 docs。
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
- 输出 `Scout Evidence`；其中 `freshly_read` 与 `satisfied_from_verified_cache` 等价于本角色的 `Read Scope Ack`。
- 复用时只输出本轮 delta evidence，不复述已验证缓存的背景。
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
- 使用 fresh role session；默认模型为 `gpt-5.4`，reasoning effort 为 `medium`。

禁止：

- 不改代码。
- 不省略 `Read Scope Ack`。
- 不直接联系 generator。
- 不自动 accepted。
- 不把个人偏好写成阻塞，除非违反合同、业务逻辑、可访问性或可用性。
- 不复用上一轮 evaluator 上下文。

## 6. Role Session Reuse / Model Policy

Team Loop 支持有限 role session 复用，用于降低重复读取 workflow docs 和项目索引的 token 消耗。复用只允许加速 read scope 路由，不允许替代 current code、task docs、Evidence Pack 或 Evaluation Bundle。

默认策略：

```yaml
role_session_reuse:
  reusable_roles:
    planner:
      ttl_dispatches: 10
      model: gpt-5.5
      reasoning_effort: high
    scout:
      ttl_dispatches: 10
      model: gpt-5.5
      reasoning_effort: high
  fresh_roles:
    generator:
      model: gpt-5.5
      reasoning_effort: high
    evaluator:
      model: gpt-5.4
      reasoning_effort: medium
```

规则：

- planner / scout 可以复用，最多 `10` 次 dispatch；达到上限后关闭并重建。
- generator / evaluator 每轮 fresh，不复用。
- planner 初始化时读取 workflow 基线 docs；后续复用时只接收本轮问题、cache manifest、freshness check 和必要 task hints。
- 复用 planner 每轮只输出 `Planner Delta Output`，重点是本轮需要额外读什么，不复述初始 docs。
- scout 建议按领域复用，例如 workflow / product-area / integration-area / high-risk-domain；复用 scout 每轮只回答 Leader 指定问题。
- Leader 维护 cache manifest：文件路径、hash 或 `mtime + size`、读取时间、scope tag、dispatch count 和上次 ack。

失效条件：

- 复用次数达到 `ttl_dispatches`。
- `AGENTS.md`、`docs/README.md`、workflow docs 或本轮缓存命中的 task docs 发生变化。
- 本轮跨到未缓存领域，或 task scope 与缓存 scope tag 不匹配。
- current code 与缓存摘要冲突。
- subagent 省略 `Read Scope Ack` / delta ack。
- Leader 判断输出引用了旧事实或越过 allowed scope。

## 7. Context Bootstrap

Leader 每次派生 fresh planner / generator / scout / evaluator 时，必须附带 `Context Bootstrap`。它不是可选背景摘要，而是 subagent 启动合同；subagent 必须按该合同读取材料并回报实际 read scope。

复用 planner / scout 时，Leader 可以用 `Reuse Bootstrap` 替代完整基线 docs 重发，但必须附带 cache manifest、freshness check、本轮问题和本轮 allowed / forbidden scope。

最低字段：

```md
## Context Bootstrap

- context_bootstrap_level: slim / full
- repo_entry:
  - primary_entry: AGENTS.md / CLAUDE.md（按当前工具选择一个；不要默认同时读取）
  - docs_index: docs/README.md
- workflow_contract:
  - docs/workflow/team-loop-core.md
  - docs/workflow/team-loop-roles/<leader|planner|generator|scout|evaluator>.md
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - docs/workflow/collaboration.md（仅需对齐普通工作流边界时）
  - docs/workflow/prompt-template.md（仅需生成可复制 prompt 时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- handoff_or_evidence:
- fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:
- role_session_reuse:
  - role:
  - reuse_status: fresh / reused
  - dispatch_count:
  - cache_manifest:
  - freshness_check:
```

规则：

- `context_bootstrap_level` 默认用 `slim`；只有 fresh 首次建立跨领域背景、workflow 规则刚变化或本轮跨到未缓存领域时才用 `full`。
- `repo_entry.primary_entry` 在 Codex / AGENTS.md-aware 工具中使用 `AGENTS.md`，在 Claude Code 中使用 `CLAUDE.md`；不要默认同时读取两者。只有目标仓库存在工具特有差异时，才把另一个入口列入条件核对。
- `workflow_contract` 是本轮 subagent 的必须合同；Leader 应只给 Team Loop core 和当前角色对应的 role capsule。
- `conditional_workflow_docs` 是上限列表，不是每个 subagent 的必读列表。
- `task_docs` 由 Leader 按 `docs/README.md` 的入口地图裁剪，不能要求 subagent 盲读全量 `docs/`。
- Team Loop subagent 不默认读取 `docs/planner/*`；Team Loop 的 planner subagent 规则来自 `team-loop-core.md`、`team-loop.md` 的完整规范和 `team-loop-roles/planner.md`，不是普通工作流的 planner docs。
- 允许 Leader 缩小专题 docs 范围，但必须说明裁剪理由，并要求 subagent 在 `Read Scope Ack` 中列出未读但可能相关的材料。
- `handoff_or_evidence` 按阶段选择；根因未锁、高风险或审计回流时优先引用 `docs/evidence/<feature>-audit.md` 或 root `workflow/audit-first.md` 的审计产物。
- `workflow/audit-first.md` 只有在根因未锁、高风险或审计回流时才进入 Context Bootstrap；普通 Team Loop 不默认读取。
- Evidence Pack 不能替代 generator 自己读取 current code。
- Evaluation Bundle 是 evaluator 的叙事入口；actual diff、referenced files、required docs 是 evaluator 可读取的核验材料。

## 8. Read Scope Ack

每个 subagent 输出开头必须包含 `Read Scope Ack`。Leader 需要先核验该回执，再采纳 subagent 结论、Evidence Pack 或 evaluation verdict。

统一模板：

```md
## Read Scope Ack

- freshly_read:
- satisfied_from_verified_cache:
- stale_or_rechecked:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:
```

角色要求：

- fresh planner subagent 必须证明读过 `AGENTS.md` 或 `CLAUDE.md` 中的当前工具入口、`docs/README.md`、Team Loop core、planner role capsule、本轮相关 docs / code。
- reused planner subagent 必须证明 workflow 基线来自已验证缓存，并列出本轮额外需要读的 docs / code / evidence。
- generator 必须证明启动前重新审计了 current code；不能只消费 planner handoff / Evidence Pack。
- scout 保留 `Scout Evidence` / `Scout Delta Evidence` 模板；其中 `freshly_read` 和 `satisfied_from_verified_cache` 等价于本角色的 `Read Scope Ack`。
- evaluator 必须证明只消费 Leader 的 Evaluation Bundle 作为叙事入口，并读取必要 diff / code / docs 做独立核验。
- 如果 subagent 发现 `Context Bootstrap` 与 current code、专题 docs 或 allowed scope 冲突，必须写入 `scope_conflicts`，由 Leader 决定返工、补 evidence 或 blocked。

## 9. Scout Request

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

## 10. Scout Evidence

scout 只能回 Leader：

```md
## Scout Evidence to Leader

- question_answered:
- freshly_read:
- satisfied_from_verified_cache:
- verified_facts:
- inferences:
- unresolved:
- next_read_if_needed:
- citations:
- confidence:
```

`freshly_read` 与 `satisfied_from_verified_cache` 等价于 scout 的 `Read Scope Ack`。如果 scout 发现 Leader 给出的 read scope 不足，应在 `unresolved` 中说明缺失材料，而不是扩范围自行设计完整方案。

Scout Evidence 不是 generator 正式输入。只有经 Leader 整理后的 Evidence Pack 才能交给 generator。

## 11. Leader Evidence Pack

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

## 12. Evaluation Bundle

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

## 13. 状态与返工

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

## 14. 与现有工作流的关系

Team Loop 是可选增强流程，不替代普通执行轮。

默认执行轮按 `collaboration.md` 的普通工作流推进：先审计 current code，按需读 docs，最小实现，做 docs impact check，再收口验证或人工验收清单。只有当用户明确使用 `@team-loop` / `Team Loop` / `teamloop`，或明确要求 Leader 调度 subagent 时，才进入 Team Loop。

docs-only、plan-only、read-only audit 轮不应被强制升级为 Team Loop。

## 15. 触发 prompt 模板

```md
@team-loop

task_id: <short-task-id>
mode: plan-gated / auto-execute
max_rounds: 3

role_session_reuse:
  reusable_roles:
    planner:
      ttl_dispatches: 10
      model: gpt-5.5
      reasoning_effort: high
    scout:
      ttl_dispatches: 10
      model: gpt-5.5
      reasoning_effort: high
  fresh_roles:
    generator:
      model: gpt-5.5
      reasoning_effort: high
    evaluator:
      model: gpt-5.4
      reasoning_effort: medium

problem:
<本轮要解决的问题、目标和验收停点。>

constraints:
- allowed scope: <允许读取 / 修改的文件、模块或文档>
- forbidden scope: <明确禁止触碰的文件、模块、业务语义或外部系统>
- validation: <Leader 需要运行或人工检查的验证项>

context_bootstrap:
- context_bootstrap_level: slim
- repo_entry:
  - primary_entry: AGENTS.md / CLAUDE.md（按当前工具选择一个；不要默认同时读取）
  - docs_index: docs/README.md
- workflow_contract:
  - docs/workflow/team-loop-core.md
  - docs/workflow/team-loop-roles/<role>.md（Leader 派生每个 subagent 时替换为具体角色）
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - docs/workflow/collaboration.md（仅需对齐普通工作流边界时）
  - docs/workflow/prompt-template.md（仅需生成可复制 prompt 时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- handoff_or_evidence:
- fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:
- read_scope_ack_required: 每个 subagent 输出必须带 freshly_read / satisfied_from_verified_cache / stale_or_rechecked / files_not_read_but_relevant / scope_conflicts / confidence
- delta_output_required: 复用 planner / scout 只输出本轮额外 read scope 与 delta evidence，不复述初始 docs
- planner_docs_exclusion: Team Loop subagent 不默认读取 docs/planner/*；只有普通工作流 plan-only / prompt-framing / review-framing 才按需读取

team_loop:
- Leader 是唯一调度者
- Leader 每次派生 fresh subagent 必须附带 Context Bootstrap；复用 planner / scout 时必须附带 cache manifest 和 freshness check
- Leader 只负责调度、裁剪证据、验证和汇总，不直接做 implementation
- planner subagent / generator / scout / evaluator 只能回报 Leader
- planner / generator / evaluator / scout 都必须回报 Read Scope Ack
- planner / scout 可复用，generator / evaluator 不复用
- evaluator 使用 gpt-5.4 medium；其他角色默认 gpt-5.5 high
- planner 是 Team Loop 内部只读 subagent，不代表旧独立 planner mode 或普通工作流 planning phase
- subagent 之间禁止直接通信
- generator 如审计范围过大，只能向 Leader 提交 Scout Request
- scout 只读收集线索，只回 Leader
- Leader 整理 Evidence Pack 后再交给 generator
- audit-first 场景必须复用 workflow/audit-first.md 的必读与 evidence 回流骨架
- Leader 跑验证
- Leader 派 evaluator 独立核验
- 缺少 generator_result 或 generator_read_scope_ack 时，本轮必须标记为 blocked / protocol_violation
- P0 / P1 不通过则最多返工 3 轮
- 最后停在 human_acceptance_required
```
