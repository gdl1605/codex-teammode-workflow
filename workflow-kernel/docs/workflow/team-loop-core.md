# Team Loop Core

> 最后更新时间：2026-06-02
> 适用范围：Team Loop subagent 的默认 slim Context Bootstrap
> 本文主职责：提供 Team Loop 核心合同；完整规范见 `team-loop.md`

## 触发边界

Team Loop 只在用户明确声明 `@team-loop`、`Team Loop`、`teamloop`，或明确要求 Leader 调度 subagent 时启用。

普通工作流是默认路径。任务复杂、根因未锁或风险较高，都不自动升级为 Team Loop。

## 模式

- `plan-gated`：planner 收口后先交给用户确认，批准后再派 generator。
- `auto-execute`：Leader 在 planner 快速收口后直接派 generator，但不跳过 generator。

两种模式最终都只能停在 `human_acceptance_required` 或 `blocked`。

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
- conditional_workflow_docs:
  - docs/workflow/team-loop.md（需要完整规范核对时）
  - docs/workflow/collaboration.md（仅需对齐普通工作流边界时）
  - docs/workflow/prompt-template.md（仅需生成可复制 prompt 时）
  - workflow/audit-first.md（仅根因未锁 / 高风险 / 审计回流时）
- task_docs:
- code_scope:
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

`conditional_workflow_docs` 是上限列表，不是每个 subagent 的必读列表。Team Loop subagent 不默认读取 `docs/planner/*`。

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
- evaluator 只消费 Leader 提供的 Evaluation Bundle 作为叙事入口，并读取必要 diff / code / docs 做独立核验。

## 返工和终态

返工或 blocked 条件：

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

`accepted` 永远只能由用户人工表达，不由 Team Loop 自动写入。
