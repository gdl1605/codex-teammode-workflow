# Prompt 模板

> 最后更新时间：2026-05-02
> 适用范围：执行轮、方案轮、交接轮的固定输入和输出结构
> 本文主职责：把 prompt 和输出的骨架固定下来
> 推荐下一跳：`workflow/collaboration.md`

## planning phase 输出顺序

普通工作流中的 planning phase 在给用户输出执行 prompt 前，固定按下面顺序组织：

1. 问题
2. 修改思路
3. 为什么这样改
4. prompt

约束：

- 不要一上来先给 prompt，再把问题和理由补在后面。
- `问题` 只写当前要解决的真实对象和现象，不提前写死根因。
- `修改思路` 先写收口方向，再落到最小修改边界。
- `为什么这样改` 要解释为什么这是当前代码下更稳的路线，而不是抽象上的理想方案。

## 固定执行 prompt 结构

后续给 Codex / Claude Code 的执行 prompt 固定为 7 段：

1. 当前已知事实
2. 本轮目标
3. 修改边界
4. 合同层
5. 建议实现层
6. 输出要求
7. 验收标准

其中：

- `合同层`
  - 只写当前已成立的产品合同、数据约束、状态机约束、权限边界、owner 语义和不可回归项。
  - 这里应尽量只放已验证事实，不放猜测性实现路径。
- `建议实现层`
  - 只写推荐切入点、推荐 slice、推荐文件范围、推荐修法顺序。
  - 这一层不是已验证事实，也不是唯一实现答案。
  - generator 必须以 current code 审计结果为准，对建议实现层做最小调整。
  - 如果 current code 与建议实现层冲突，以 current code 为准，并在输出中明确说明。

## 固定输出结构

默认输出结构保持为：

1. 改动文件列表
2. 每个文件改了什么
3. 实现说明
4. 风险 / 阻塞说明
5. build 结果
6. 手工复测步骤
7. docs impact check

`docs impact check` 默认写清：

- 本轮是否需要更新 docs
- 更新了哪些 docs
- 为什么更新这些
- 或为什么本轮无需更新 docs

## Team Loop 启动模板

当用户明确使用 `@team-loop`，或要求 Leader 调度多个 subagent 形成类 team-mode 闭环时，使用下面模板。

Team Loop 不是普通执行轮的默认要求；未明确触发时，仍按 `workflow/collaboration.md` 的普通执行轮推进。

Team Loop 中的 `planner` 是 Leader 调度的只读 subagent，不代表旧独立 planner 模式。

```md
@team-loop

task_id:
mode: plan-gated / auto-execute
max_rounds: 3

problem:

constraints:
- allowed scope:
- forbidden scope:
- 不改：

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
- read_scope_ack_required: planner / generator / scout / evaluator 均必须输出 Read Scope Ack

team_loop:
- Leader 是唯一调度者。
- Leader 每次派生 subagent 必须附带 Context Bootstrap。
- planner / generator / scout / evaluator 只能回报 Leader。
- planner / generator / scout / evaluator 都必须回报 Read Scope Ack。
- planner 是 Team Loop 内部只读 subagent，不代表旧独立 planner 模式。
- subagent 之间禁止直接通信。
- generator 如审计范围过大，只能向 Leader 提交 Scout Request。
- scout 只读收集线索，只回 Leader。
- Leader 整理 Evidence Pack 后再交给 generator。
- audit-first 场景必须复用 workflow/audit-first.md 的必读与 evidence 回流骨架。
- Leader 跑验证。
- Leader 派 evaluator 独立核验。
- P0 / P1 不通过则最多返工 3 轮。
- 最后停在 human_acceptance_required。

output:
- 最终状态
- rounds / attempts
- 修改文件
- subagent_read_scope_acks
- context_bootstrap_deviations
- 验证结果
- evaluator 结论
- 人工验收清单
- docs impact check
```

### Team Loop 模式选择

- `plan-gated`：用于数据库 schema / 服务端函数 / 权限 / 状态机 / 高风险产品域 / 复杂资源链路 / 根因未锁或用户要求先批准 plan 的任务（高风险域由目标仓库自行列出）。
- `auto-execute`：用于文案、轻 UI、局部样式、docs 小修和 allowed scope 清楚的低风险任务。

### Team Loop subagent 启动片段

Leader 派生 planner / generator / scout / evaluator 时，至少附带下面片段；具体 docs 和 code scope 由 Leader 按 `docs/README.md` 的入口地图裁剪。

```md
You are <planner/generator/scout/evaluator> subagent in Team Loop.
You only report to Leader.

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
- code_scope:
- handoff_or_evidence:
- fact_priority: current code > topic docs > handoff/latest.md > handoff/archive
- allowed_read_scope:
- forbidden_read_scope:
- allowed_write_scope:
- forbidden_write_scope:
- expected_output_schema:

## Required Read Scope Ack

- files_read:
- docs_read:
- code_read:
- evidence_or_handoff_read:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:
```

### Scout Request 模板

generator 不能直接联系 scout，只能向 Leader 提交：

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

### Evidence Pack 模板

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

### Evaluation Bundle 模板

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

## docs-only 轮的输出

- docs-only 轮不写 build 结果
- 仍然要说明改了哪些文件、为什么改、还缺什么
- 仍然要带 `docs impact check`
- 不要打印完整文件全文，除非用户明确要求

## 与 collaboration 对齐

- prompt 结构应与 [`workflow/collaboration.md`](collaboration.md) 的协作闭环保持一致。
- 执行轮若默认包含独立 evaluator，prompt 里的输出要求也应预留审计 / review 结果，而不是只写生成结果。
- 执行轮开头的上下文、git 和环境检查，继续按 [`workflow/session-startup.md`](session-startup.md) 执行。

## 人工验收清单

只要是执行轮，输出里默认要带人工验收清单，且至少写到下面粒度：

- 进入哪个页面
- 使用哪个账号或哪类测试数据
- 点击什么、输入什么
- 预期看到什么

如果某个场景当前无法直接验收，必须写明原因和替代方式。
