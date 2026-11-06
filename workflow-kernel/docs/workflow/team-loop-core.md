# Team Loop Core

> 最后更新时间：2026-11-06
> 适用范围：Team Loop subagent 的默认 slim Context Bootstrap
> 本文主职责：提供 Team Loop 核心合同；完整规范见 `team-loop.md`

## 触发边界

Team Loop 只在用户本轮明确要求机制变更或其工程方案，并明确声明 `@team-loop`、`Team Loop`、`teamloop`，或要求 Leader 调度 subagent 时启用。

未明确触发时，仅当前用户明确要求的机制变更及其工程方案使用 `default-workflow.md`；正常执行、恢复、排障和业务操作计划产出不进入开发流程。agent 自拟修复计划、任务复杂、根因未锁或风险较高都不构成触发；“仅执行 / 不要 review”等明确限制优先。仅讨论、引用、安装、修改规则或历史上用过 Team Loop，也不等于本轮启用它。

## 模式

- 两种模式都在关键取舍澄清后、正式计划交付前派 fresh evaluator 轻量核对原要求与计划；采用 `independent-evaluator.md` 的共用核验原则。明确遗漏由 Leader 交 planner 修订，事实先补证，真实业务歧义沿原生卡片交用户。
- `plan-gated`：规划核验收口后交用户确认，批准后再派 generator。
- `auto-execute`：规划核验收口且已有实施授权后派 generator，不新增整份计划人工批准，也不跳过 generator。

仅规划时交付计划并结束，注明未实施，不派 generator、不做实现核验；generator 结果与实现验证不适用。授权实施后，两种模式最终都只能停在 `human_acceptance_required` 或 `blocked`。

## 通信规则

允许：

```text
User <-> Leader
Leader -> planner / generator / scout / evaluator
planner / generator / scout / evaluator -> Leader
Leader -> generator with Evidence Pack
Leader -> evaluator with Evaluation Bundle
```

禁止：

```text
planner -> generator
generator -> scout
scout -> generator
evaluator -> generator
subagent 彼此直接通信
generator / scout / evaluator 自行派生 subagent
```

Leader 不是简单转发器。Leader 必须裁剪、去噪、标注可信度，并把正式输入封装为 Evidence Pack 或 Evaluation Bundle。

## 角色规则入口

Leader 派生 subagent 时，必须附带当前角色的 role capsule：

- `team-loop-roles/planner.md`
- `team-loop-roles/generator.md`
- `team-loop-roles/scout.md`
- `team-loop-roles/evaluator.md`

Leader 自身参考 `team-loop-roles/leader.md`。每个 subagent 只需要自己的 role capsule，不需要读取所有角色文件。

## Context Bootstrap

默认使用 `slim`：

```md
## Context Bootstrap

- context_bootstrap_level: slim
- repo_entry:
  - primary_entry: AGENTS.md / CLAUDE.md（按当前工具选择一个；不要默认同时读取）
  - docs_index: docs/README.md
- workflow_contract:
  - docs/workflow/team-loop-core.md
  - docs/workflow/team-loop-roles/<role>.md
  - docs/workflow/independent-evaluator.md（仅 evaluator，规划 / 实现共用核验原则）
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- code_scope:
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

`conditional_workflow_docs` 是上限列表，不是每个 subagent 的必读列表。

## Read Scope Ack

每个 subagent 输出开头必须包含：

```md
## Read Scope Ack

- freshly_read:
- satisfied_from_verified_cache:
- stale_or_rechecked:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:
```

Leader 先核验该回执，再采纳 subagent 结论、Evidence Pack 或 evaluation verdict。

## Role Session Reuse

- planner / scout 可以复用，默认最多 `10` 次 dispatch。
- generator / evaluator 每轮 fresh，不复用。
- 复用 planner / scout 时，只接收本轮问题、cache manifest、freshness check 和必要 task hints。
- 复用只能作为范围索引，不能替代 current code、task docs、Evidence Pack 或 Evaluation Bundle。

## Evidence 和 Evaluation

- generator 只能向 Leader 提交 Scout Request。
- scout 只回 Leader。
- Leader 整理 Evidence Pack 后再交给 generator。
- Evidence Pack 不能替代 generator 重新审计 current code。
- generator 实现前仍回查用户原话、纠正与修订计划；计划经过核验不能替代原要求。
- evaluator 只消费 Leader 提供的 Evaluation Bundle 作为叙事入口，沿原话、纠正和合同独立核验，不能只认 Leader 的摘要。Bundle 区分规划 / 实现阶段；规划不要求尚不存在的 diff、generator 结果或运行证据，实现核验追真实消费路径与完成声明。

## 返工和终态

返工或 blocked 条件：

- 发现本次原要求、有效合同或已确认决定被遗漏、弱化或违反；规划缺口回 planner，实现缺口回 generator，均由 Leader 调度。
- evaluator 发现 P0 / P1。
- validation failed 且无明确 human waiver。
- generator 越过 forbidden scope。
- generator 省略 `Read Scope Ack` 或缺少关键 current code / docs。
- actual diff 与 allowed scope 不符。

不默认返工：

- P2 / P3。
- 文案偏好。
- 可由人工验收覆盖的小视觉差异。
- 已标注 residual risk 的非阻塞项。

上述非阻塞项不包括明确违反本次要求的缺口，不能用严重性标签或 residual risk 改低要求。规划修正只 fresh 复核发现及直接影响；没有本阶段应有的证据时报告缺失，不为规划补造实现结果或增加验证门槛。

`accepted` 永远只能由用户人工表达，不由 Team Loop 自动写入。
