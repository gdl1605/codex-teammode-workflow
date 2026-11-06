# Team Loop Workflow

> 最后更新时间：2026-11-06
> 适用范围：需要由 Leader 主线程调度多个独立 subagent 的类 team-mode 闭环
> 本文主职责：定义 plan-gated / auto-execute 两种模式、角色边界、通信规则、Context Bootstrap、Read Scope Ack、scout 支援机制和人工验收停点
> 推荐下一跳：`team-loop-core.md`、`team-loop-roles/`

## 1. 定位

Team Loop 是本包显式选择的多角色编码协作工作流，只在用户本轮明确要求机制变更或其工程方案，并明确声明使用 `@team-loop`、`Team Loop`、`teamloop`，或要求 Leader 调度 subagent 时启用。

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

Team Loop 中的 `planner subagent` 是 Leader 调度的内部只读角色，职责见 `team-loop-roles/planner.md`。

未明确触发时，仅当前用户明确要求的机制变更及其工程方案使用 `default-workflow.md`；正常执行、恢复、排障和业务操作计划产出不进入开发流程。agent 自拟修复计划、任务复杂、根因未锁或风险较高都不构成触发；“仅执行 / 不要 review”等明确限制优先。仅讨论、引用、安装、修改规则或历史上用过 Team Loop，也不等于本轮启用它。

## 2. 非目标

Team Loop 不做：

- 不让 subagent 彼此直接通信。
- 不让 generator / evaluator / scout 自己派生 subagent。
- 不自动进入 `accepted`。
- 不替代“current code 优先证明当前实现事实、其他 claim 按权限/evidence 分流”的事实规则。
- 不把 scout 结论直接当作 generator 的正式输入。
- 不复用 generator / evaluator role session。

## 3. 两种模式

### 3.1 plan-gated

进入 Team Loop 后，`plan-gated` 适用于用户希望先批准 plan 再执行的轮次。模式选择只影响 Team Loop 内部节奏，不作为自动触发 Team Loop 的条件。

特点：

- planner 收口并完成轻量独立规划核验后，交给用户确认。
- 用户批准后再派 generator。
- 最后仍停在 `human_acceptance_required`。

流程：

```text
Leader 接收任务
-> 派 planner subagent
-> Leader 澄清未决关键取舍，派 fresh evaluator 轻量核对原要求与计划
-> 明确遗漏交 planner 修正；事实补证，真实歧义交用户；只复核受影响部分
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
-> 修复范围内有依据的缺口，fresh 只复审原问题及直接影响
-> 通过则停在 human_acceptance_required
```

### 3.2 auto-execute

进入 Team Loop 后，`auto-execute` 适用于用户允许 Leader 在 planner 快速收口后直接派 generator 的轮次。

特点：

- 不需要把 planner subagent 的 plan 先交给用户批准。
- `auto-execute` 只跳过人工 plan approval，不跳过 generator。
- Leader 仍要派轻量规划 evaluator，并核验 planner 输出、generator read scope 和实现 evaluator verdict。
- 最后仍停在 `human_acceptance_required`。

流程：

```text
Leader 接收任务
-> 派 planner subagent 快速只读收口
-> Leader 判断 allowed scope / forbidden scope 是否足够清楚
-> 澄清未决关键取舍，派 fresh evaluator 轻量核对原要求与计划并安排必要修正
-> 满足条件则直接派 generator subagent
-> generator 必要时可向 Leader 申请 1 个 scout
-> scout 只回 Leader
-> Leader 整理 Evidence Pack 给 generator
-> generator 实现
-> Leader 验证
-> Leader 派 evaluator subagent
-> 修复范围内有依据的缺口，fresh 只复审原问题及直接影响
-> 通过则停在 human_acceptance_required
```

auto-execute 不是跳过 Team Loop 的 planner subagent，也不是让 Leader 自己实现；它只是不需要把 planner subagent 的 plan 先交给用户批准，后续实现仍必须由 fresh generator subagent 完成。

### 3.3 正式计划交付前的核验与仅规划

两种模式均在关键取舍已有依据或收到实际回答后、正式计划交付前，派 fresh 只读 evaluator，以 `review_phase: plan` 轻量核对原要求、后续纠正、有效合同与计划。共用判断原则见 `independent-evaluator.md`；只按需查计划依赖的关键事实，不展开实现审计或运行回归。

Leader 提供相关原话及纠正，不能只交 planner 或自己的总结。明确遗漏、弱化约束或错误转译交 planner 修订同一份 handoff；事实先补证；不同解释会改变行为、范围或验收时，Leader 复用 `default-workflow.md` 的 Grill-me / 原生卡片方式提问，实际回答回写计划。这只复用澄清规则，不启动普通工作流或转移实现职责。修正后由 fresh evaluator 只复核发现及直接影响，不因每次草案编辑全量重审。

仅规划时，在上述核验后交付计划并结束，注明未实施及实际核验范围；不派 generator，不要求实现 diff、generator 结果或实现验证，也不把规划通过称为实现通过。Leader、planner 和 evaluator 仍不改工程文件；尚无获授权写入角色时，按 `docs-maintenance.md` 在聊天中交付同一份计划，不为落盘提前启动实现。授权实施时，generator 仍回查原话、纠正和修订计划，实现后再派 fresh evaluator；规划核验不能替代这两步。

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
- 给 planner、generator 和 evaluator 提供相关原话、后续纠正、合同与决定来源；正式计划交付前派 fresh evaluator 轻量核验，按 3.3 节处理修正、补证和歧义。
- 审批或拒绝 generator 的 Scout Request。
- 汇总 scout 输出，形成 Leader Evidence Pack。
- 跑验证命令并整理 validation output。
- 形成 Evaluation Bundle 给 evaluator。
- 区分 `initial / recheck`：首次审查前确认本次承诺已实现、接线及必要验证已完成；复审提供原问题、逐项修复、相对上次送审的变化和直接影响，不重新布置开放式全量审查。按根因交对应角色修复相关分支，达到原要求就收口。
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
- 保留原要求、纠正及其限定，区分事实、决定、建议和未决选择；按 Leader 回流的规划核验缺口修订同一份 handoff，不能自行降低目标。
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
- 实现前回查相关用户原话、纠正和修订计划，发现遗漏或弱化时回 Leader；不能因为规划已核验就省略原要求。
- 按 current code 做最小实现，同时遵守已确认的合同层。
- 若 `Context Bootstrap`、Evidence Pack、docs 与 current code 冲突，先向 Leader 回报“当前实现行为”和冲突的 claim 类型；实现事实以代码为准，业务意图不得被代码静默覆盖。
- 如审计范围过大，向 Leader 提交 Scout Request。
- 输出 touched files、修改摘要、验证建议和给 Leader 的 evaluator notes。
- 首次送审前完成本次承诺中的真实入口与生产消费接线；返工按原问题的根因修复相关分支，说明逐项修复及直接影响，不只修审查给出的单个反例，也不顺手加入独立改进。
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

- 以 Leader 的 Evaluation Bundle 为叙事入口，按 `review_phase: plan / implementation`、`review_kind: initial / recheck` 和 `independent-evaluator.md` 核验，摘要不能替代相关用户原话及后续纠正。
- 首次审查围绕本次交付集中回报确定问题；复审仅核对原问题及修复直接影响，新缺口须证明因果关系。无关旧问题、额外能力与设计偏好不阻塞，不因 fresh 或 P0 / P1 标签重开未变且已通过的部分。
- 输出 `Read Scope Ack`，说明本阶段实际核验的来源、计划或实现证据和未覆盖范围；每阶段都不继承规划者或实现者完整对话。
- 规划时轻量检查原要求与计划解释，找遗漏、约束弱化、无来源取舍、事实与假设混淆及真实歧义，不要求尚不存在的实现结果。
- 实现时重新对照原要求、修订计划、真实消费路径、generator 读取范围、验证记录和完成声明，检查说了没做、计划与实现不一致及同源错误互证。
- 将确定缺口、待补事实、待用户裁决分开，只回 Leader；具体职责和输出见 `team-loop-roles/evaluator.md`。
- 优先找 P0 / P1 阻塞问题。
- 若缺少本阶段关键来源导致无法判断，指出缺失及影响，应输出 `request changes` 或按真实阻塞输出 `blocked`，不能写成 pass。
- P2 / P3 的非阻塞项默认进入 residual risk、backlog 或后续优化；明确违反本次要求的项不能仅因标签或 residual risk 而跳过修复。
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
  - docs/workflow/independent-evaluator.md（仅 evaluator，规划 / 实现共用核验原则）
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- handoff_or_evidence:
- implementation_fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- non_implementation_authority: explicit business contract or direct lifecycle evidence
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
- `workflow_contract` 是本轮 subagent 的必须合同；Leader 应给 Team Loop core 和当前角色对应的 role capsule，evaluator 另附 `independent-evaluator.md`，其他角色不默认加读。
- `conditional_workflow_docs` 是上限列表，不是每个 subagent 的必读列表。
- `task_docs` 由 Leader 按 `docs/README.md` 的入口地图裁剪，不能要求 subagent 盲读全量 `docs/`。
- Team Loop 的 planner subagent 规则来自 `team-loop-core.md`、本完整规范和 `team-loop-roles/planner.md`。
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

- review_phase: plan / implementation
- review_kind: initial / recheck
- review_baseline: 本次原要求 / 确认计划、待审版本及改动边界；已通过且未受影响的部分
- recheck_request: 仅 recheck；原问题及依据 → 对应修复、相对上次送审的修复 diff / 计划变化、直接影响路径和已有验证
- original_problem:
- original_requirements_and_corrections: 相关用户原话、后续纠正及有效合同的准确位置
- confirmed_decisions_and_assumptions: 决定、实际回答 / 委托及来源；假设和未决项分开
- expected_behavior_and_boundaries: 本次要求对应的可观察结果及不能改变的限定；关键规则和测试预期的有效原来源、推导与适用范围，假设或来源缺口单列
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
- delivery_claims: 本阶段准备向用户声称什么、证据达到哪一层
- known_residual_risks:
- human_acceptance_target:
```

Evaluation Bundle 应避免包含规划者或实现者完整对话历史，保留相关原话和纠正及其准确来源。Leader 的摘要仅用于导航，不能替代原始依据或静默省略不利于当前计划的要求。涉及规格或接口时，引用适用 Spec、正式合同、实际生产消费路径与已有唯一校验入口，区分拟用检查和实际结果。

`review_phase` 和 `review_kind` 分别指定。首次实现审查前先完成本次承诺及必要验证；复审保留原问题的标识或原文，不能只重发整份首次请求。按 `independent-evaluator.md` 的「首次审查与复审」确定直接影响；送审后确需补做原授权内的独立实现，Leader 说明对应原条款、原因及新增改动，仅新增部分按 `initial` 核验，已通过且未受影响的部分不重开。

Evaluator 还按 `independent-evaluator.md` 核对关键规则和测试预期本身的依据，不能只检查实现符合既有断言。Leader 核对发现所引的原始依据、推导与具体影响后，再交对应角色处理；来源缺失先补证，不据此擅自删规则、降低标准或宣布业务失败。确认规则和测试共同维护错误假设时，在原授权及测试权限内修正规则、实现和相关测试；真实业务取舍或有效合同冲突才交用户。

规划阶段以当前 planner handoff / 计划为待审产物，generator_result、generator_read_scope_ack、actual_diff、实现 validation_output 和实现 human_acceptance_target 尚不适用时注明，不因缺少这些项判阻塞。实现阶段必须提供实际变更、结果和准备对外作出的完成声明。Evaluator 按共用核验原则追原要求，再核验本阶段的读取范围、实际行为与 docs impact；规划 pass 不替代实现核验。必要来源缺失时补查或明确未覆盖，不能宣称该部分已通过。

## 13. 状态与返工

Team Loop 使用轻量状态，不引入 repo 状态机：

下列实现状态及 generator 结果要求只在授权实施后适用。仅规划按 3.3 节交付并注明未实施，不因没有 generator 或实现结果进入 blocked，也不进入实现验收。

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

是否继续由本次原要求的未解决缺口及修复直接影响决定，不以固定轮数判通过 / 失败。以下返工条件仅适用于本次审查范围；复审限原问题及直接影响，严重性标签不授权扩审：

- 原要求、有效合同或已确认决定被遗漏、弱化或违反；规划缺口由 Leader 交 planner 修订，实现缺口交 generator 修复。
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

以上不默认返工的项不包括范围内明确违反本次要求的缺口，不能用低严重性标签或 residual risk 改低要求。规划和实现修正都只派 fresh 定向复审，逐项说明原问题是否关闭及有无修复直接引入的偏差；范围外建议不阻塞。原问题及直接影响已处理、证据支持原要求和交付声明后结束核验，不要求建议清零或继续寻找其他问题。

终态：

- `human_acceptance_required`
- `blocked`

`accepted` 永远只能由用户人工表达，不由 Team Loop 自动写入。

## 14. 触发 prompt 模板

```md
@team-loop

task_id: <short-task-id>
mode: plan-gated / auto-execute

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
  - docs/workflow/independent-evaluator.md（仅 evaluator）
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- handoff_or_evidence:
- implementation_fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- non_implementation_authority: explicit business contract or direct lifecycle evidence
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:
- read_scope_ack_required: 每个 subagent 输出必须带 freshly_read / satisfied_from_verified_cache / stale_or_rechecked / files_not_read_but_relevant / scope_conflicts / confidence
- delta_output_required: 复用 planner / scout 只输出本轮额外 read scope 与 delta evidence，不复述初始 docs

team_loop:
- Leader 是唯一调度者
- Leader 每次派生 fresh subagent 必须附带 Context Bootstrap；复用 planner / scout 时必须附带 cache manifest 和 freshness check
- Leader 只负责调度、裁剪证据、验证和汇总，不直接做 implementation
- planner subagent / generator / scout / evaluator 只能回报 Leader
- planner / generator / evaluator / scout 都必须回报 Read Scope Ack
- planner / scout 可复用，generator / evaluator 不复用
- evaluator 使用 gpt-5.4 medium；其他角色默认 gpt-5.5 high
- planner 是 Team Loop 内部只读 subagent，按 planner role capsule 输出 handoff 或 delta
- subagent 之间禁止直接通信
- generator 如审计范围过大，只能向 Leader 提交 Scout Request
- scout 只读收集线索，只回 Leader
- Leader 整理 Evidence Pack 后再交给 generator
- audit-first 场景必须复用 workflow/audit-first.md 的必读与 evidence 回流骨架
- Leader 跑验证
- Leader 在正式计划交付前派 fresh evaluator 轻量核对原要求、纠正与计划；明确遗漏回 planner，真实歧义沿原生卡片交用户
- Leader 在实现后再派 fresh evaluator 独立核验实际行为与完成声明
- 仅在实现核验阶段，缺少 generator_result 或 generator_read_scope_ack 时标记 blocked / protocol_violation；仅规划不要求这些实现字段
- Evaluation Bundle 区分 review_phase: plan / implementation 与 review_kind: initial / recheck；首次审本次承诺，复审只核对原问题、逐项修复及直接影响
- 返工项须有本次原依据及具体影响；范围外建议和严重性标签不重开已通过部分，达到原要求即收口，不设固定轮数
- 仅规划交付经核验的计划并注明未实施；授权实施后最后停在 human_acceptance_required
```
