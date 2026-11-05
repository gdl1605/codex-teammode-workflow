# Codex-teammode Workflow

> 中文优先 / English below.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.3.1-blue.svg)](./CHANGELOG.md)

## 安装

1. Clone 本仓库到本地：

   ```bash
   git clone https://github.com/gdl1605/codex-teammode-workflow.git
   ```

2. 打开 clone 得到的目录，复制 [`BOOTSTRAP_PROMPT.md`](./BOOTSTRAP_PROMPT.md) 的全部内容。
3. 在任意一个你想安装工作流的项目中打开 agent 对话（如 Codex 或 Claude Code），粘贴并发送即可。Agent 会读取工作流，并将它安装到当前项目。

## 这是什么

Codex-teammode Workflow 为 **Codex** 和 **Claude Code** 提供可安装到项目里的协作规则、启动提示和文档结构。安装后有两条开发路径：

| 工作流 | 什么时候用 | 谁实现 | 核验结果交给谁 |
| --- | --- | --- | --- |
| 普通开发 | 默认，包括只要求独立核验的任务 | 主 agent | 独立 evaluator 直接回报主 agent |
| Team Loop | 用户明确要求 `@team-loop` 或 Leader 调度时 | Leader 派出的 Generator | Evaluator 回报 Leader，由 Leader 安排返工或人工验收 |

## 普通开发工作流

**主 agent 负责规划、实现和验证，独立 evaluator 负责核验。** 一次任务按下面的顺序走：

1. **形成草案。** 主 agent 核对原要求、已有合同和实际代码，区分当前事实、已确认的决定和自己的建议。
2. **用 Grill-me 澄清取舍。** 正式计划交付前（包括仅规划），沿用已有决定，按明确委托自行选择，并说明依据。仍会影响行为、范围、成本或验收的未确认取舍，用原生卡片问。Codex 暴露 `request_user_input_async` 时调用它，每题给出选项、影响和推荐；工具不可用或受限时说明限制，再用文本选项。互不依赖的问题同轮问，依赖问题等到实际回答后再问，答案及其来源写回同一份计划。推荐或预选不算确认。
3. **交付计划，按授权实现。** 仅规划到正式计划为止。已授权实现时，由主 agent 改动并运行直接相关的验证。普通实现细节由 agent 自行决定。
4. **独立核验并收口。** 主 agent 把原要求、已确认决定、实际 diff、相关调用路径和验证证据交给全新上下文的只读 evaluator。它检查实现是否偏离要求、假设有没有被写成事实或门禁。确定缺口直接回主 agent 修复，并复核受影响部分；事实不明由 agent 补证，业务争议交用户裁决。

例如，代码没有取消入口是**现状**；本次是“等当前请求结束再退出（推荐）”，还是“增加取消、停止确认和部分结果保存”，则是**交付取舍**。用户还没决定时，就把这两个选项发成卡片。

完整流程和 Review Request 见 [`default-workflow.md`](./workflow-kernel/docs/workflow/default-workflow.md)，核验角色见 [`independent-evaluator.md`](./workflow-kernel/docs/workflow/independent-evaluator.md)。

## Team Loop 工作流

用户明确要求 `@team-loop`、`Team Loop` / `teamloop` 或 Leader 调度时启用。**Leader 是同一聊天里的唯一调度者，负责交接和验证，不直接改文件；Generator 负责实现。** 各 subagent 只向 Leader 回报。

### 一轮怎样调度

```text
Leader 派 Planner → Leader 收到计划并按模式放行 → Generator 实现
→ Leader 验证并派 Evaluator → Evaluator 回报 Leader → 返工或人工验收
```

1. **先派 Planner。** 只读核对需求和当前代码，给 Leader 返回目标、允许与禁止的修改范围、实现建议和核验重点。根因未锁时，先按 [audit-first](./workflow-kernel/workflow/audit-first.md) 只读查明，再安排实现。
2. **按模式派 Generator。** `plan-gated` 先把计划交用户批准，再派 Generator；`auto-execute` 在计划与边界收口后直接派。两种模式都由新会话的 Generator 重读相关代码后实现。
3. **需要时插入 Scout。** Generator 缺证据时向 Leader 提出 `Scout Request`。Leader 决定是否派只读 Scout；Scout 把证据交回 Leader，由 Leader 整理成 `Evidence Pack` 再交 Generator。Scout 不是每轮固定步骤。
4. **验证后派 Evaluator。** Leader 运行必要验证，把原要求、计划、实际 diff、读取范围和验证结果整理成 `Evaluation Bundle`，交给新会话的只读 Evaluator。Evaluator 独立核对后，只向 Leader 返回结论。
5. **Leader 处理返工或交回用户。** 遇到 P0 / P1、验证失败或范围违规时，Leader 按现有规则安排返工或报告阻塞；返工时把具体问题交下一轮 Generator。核验通过后停在 `human_acceptance_required`；无法推进时报告 `blocked`。最终验收由用户决定。

Leader 派发时提供裁剪过的 `Context Bootstrap`，用 `Read Scope Ack` 确认角色实际读了哪些材料。Planner 和 Scout 核对材料仍有效后可以复用；Generator 和 Evaluator 每轮使用新会话。

完整调度、触发示例与返工条件见 [`team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)；最小上下文和角色约定见 [`team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md) 与[角色文件](./workflow-kernel/docs/workflow/team-loop-roles/)。

## 适用对象

- 使用 Codex 或 Claude Code 的个人开发者
- 希望统一 AI 协作规则的小团队
- 经常被上下文丢失、想象式修复、未审计执行困扰的 AI coding agent 重度用户

## 安装后会生成什么

目标 agent 会读取工作流内核，审计目标仓库，并创建或合并：

```text
AGENTS.md                          # Codex / AGENTS.md-aware tools 入口
CLAUDE.md                          # Claude Code 入口，与 AGENTS.md 同步
workflow/audit-first.md            # 根因审计优先流程
docs/
  README.md                        # docs 入口地图
  workflow/                        # 普通开发、独立 evaluator、Team Loop、docs maintenance
  product/                         # 项目事实占位，需按目标仓库填写
  architecture/                    # 架构占位，需按目标仓库填写
  handoff/                         # 跨会话 handoff
  plans/                           # active / completed plans
  evidence/                        # audit evidence
```

## 升级旧项目

当目标项目已经安装过旧版工作流时，不要重新粘贴 bootstrap prompt 做全量覆盖。把新版 `codex-teammode-workflow/` 文件夹放进目标项目后，粘贴 [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md)。

升级流程按 [`UPDATE_MANIFEST.md`](./UPDATE_MANIFEST.md) 的 ownership 策略执行：

- **workflow kernel**：清单内的普通开发 / Team Loop 内核及 `workflow/audit-first.md` 原地替换旧版文件；按 `remove-workflow` 清单删除退役 planner schema 等精确文件，不生成 `.new`，并清理旧升级遗留的 workflow `.new` 文件。
- **mixed files**：`AGENTS.md`、`CLAUDE.md`、`docs/README.md` 只替换 `codex-teammode:managed` block，保留 block 外的目标项目规则。
- **target facts**：`docs/product/*`、`docs/architecture/*`、`docs/handoff/*`、`docs/plans/*`、`docs/evidence/*` 永不自动覆盖。

升级完成后，目标项目应写入 `docs/workflow/.codex-teammode-version`，用于记录版本和已安装文件 hash。后续升级会用这个 marker 做基线和报告，但 workflow kernel 仍按新版原地替换。

## 重要边界

这个项目只安装 **工作流机制**，不安装任何业务事实。

Bootstrap prompt 会要求目标 agent 不要复制本仓库的产品状态、计划、证据、架构结论或领域示例。普通实现事实仍以目标仓库的 current code 为首要证据；显式运行 `$docs-review` 时则按 claim 类型路由权限，业务意图、部署、人工验收和法务状态不能被“代码已实现”替代。

## 核心概念

- **普通工作流**：主 agent 在正式计划交付前核对关键取舍来源、追问未确认选择（含仅规划），授权实现后派 fresh 只读 evaluator；确定缺口直接回主 agent，业务争议交用户裁决。
- **Team Loop**：由 Leader 在同一个会话里调度 planner / generator / scout / evaluator。
- **audit-first**：根因未锁定时先审计、写 evidence，再进入执行。
- **Fact priority**：普通实现事实按 current code > topic docs > `docs/handoff/latest.md` > archive；`$docs-review` 对业务意图、部署、验收和法务 claim 使用各自权限。
- **docs impact / docs-review**：前者是每轮增量微循环；后者是人工触发、Plan/Apply 两阶段的事实校正宏循环。
- **docs-review v3 plan gate**：scanner schema 5 的每条 finding 都绑定 source fingerprint、结构化 resolution group、精确人工权限和批准文件；完整 audit scope 与每项 edit contract 同时冻结，机器 Claim ID / 稳定锚点不得写进业务 docs。
- **docs-review sharded closure**：大型全文审查按预算分片，原始 auditor JSON 无损校验；所有 shard pass 后再由全新 synthesis auditor 做跨分片终审，任一不足先停在人类确认门。
- **human_acceptance_required**：Team Loop 的人工验收停点，只有人类可以验收。

更多术语见 [`CONCEPTS.md`](./CONCEPTS.md)。

## Docs Review Skill

[`skills/docs-review/`](./skills/docs-review/) 是随工作流包版本化、但只允许人工显式触发的
项目事实校正 skill。它解决的是长期增量维护后常见的宏观偏差：同一业务事实散落在多份
docs 中、current 与 candidate 混写、active/completed 生命周期错位、历史状态伪装成当前
状态，以及实现、部署、验收、法务和发布被压缩成一个模糊的“已完成”。

它和普通 `docs impact` 的分工是：

- `docs impact` 是每轮结束时维护受影响主落点的微循环。
- `$docs-review` 是人工触发、跨文档对账和清理的宏循环，不会被普通 docs 修改自动调用。

Codex 中推荐分两阶段使用：

```text
Plan Mode:  $docs-review [scope=<domain-or-docs-path>]
Default Mode: $docs-review apply
```

Plan Mode 只读 docs、current code、schema、tests 和已有 evidence，逐类判断事实权限并向人类
询问无法由仓库证据唯一决定的业务含义。`apply` 只消费同一任务中已经批准、通过 schema-3
计划门且 baseline 未漂移的方案，只修改批准列表中的 Markdown docs；它不会顺手修改业务
代码、migration、测试、部署环境或外部系统。

v3 为每条 scanner-schema-5 finding 记录 source fingerprint、结构化 disposition、目标语义、
证据和精确人工权限，并冻结完整 `audit_scope_manifest` 与结构化 `edit_contracts`，验证
canonical transfer、path rewrite 和 lifecycle move 的后置条件；自然语言业务含义交给独立
审计，不把 Claim ID、audit ID 或 validator 专用锚点写进项目 docs。Apply 后，大型全文范围
会按预算拆成多个 fresh shard auditor，原始 JSON 报告必须无损保存并通过严格校验。全部 shard
pass 后，还要由一个全新的 synthesis auditor 重新核验 canonical owner、跨分片 consumer 和
原始 evidence。任一 deficiency 或协议错误都会立即停在人类确认门，不能在同一失败轮自行修复。

最终 verdict 只有 `consistent`、`partially_consistent` 或 `blocked`；这些结果都不会自动推导
`human_accepted`、`legal_accepted`、`deployed` 或 `released`。完整协议见
[`SKILL.md`](./skills/docs-review/SKILL.md)，事实模型与独立审计角色见
[`skills/docs-review/references/`](./skills/docs-review/references/)。

## 当前状态

发布记录为 `v0.3.1`；当前源码内核为尚未发布的 `0.4.0-dev`，普通工作流变更见 `CHANGELOG.md` 的 Unreleased。核心内核中文优先，README 提供中英双语入口，支持 Codex 和 Claude Code；其他工具可参考 AGENTS.md/CLAUDE.md 约定自行适配。

## 贡献

欢迎贡献：

- 更清晰的 workflow kernel 表达
- Codex / Claude Code 使用反馈
- 英文翻译
- 更好的安装脚本和一致性检查
- 泛化、脱敏、可复用的示例模板

见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

路线图见 [`ROADMAP.md`](./ROADMAP.md)，支持渠道见 [`SUPPORT.md`](./SUPPORT.md)。

## License

[MIT](./LICENSE).

---

## English

### Installation

1. Clone this repository locally:

   ```bash
   git clone https://github.com/gdl1605/codex-teammode-workflow.git
   ```

2. Open the cloned directory and copy the entire contents of [`BOOTSTRAP_PROMPT.md`](./BOOTSTRAP_PROMPT.md).
3. Open an agent conversation in any project where you want the workflow installed, paste the contents, and send. The agent will read the workflow and install it into that project.

### About

Codex-teammode Workflow is a prompt-first workflow package for **Codex** and **Claude Code**. It is not a runtime framework. It is a portable set of Markdown rules, a bootstrap prompt, and a docs scaffold that helps solo developers and small teams run a consistent AI coding process.

Default development keeps planning and implementation in the main agent, traces consequential choices to their authority and clarifies unconfirmed choices before formal plan delivery (including plan-only tasks), and dispatches a fresh read-only evaluator after authorized implementation. Explicit Team Loop instead uses a Leader coordinating planner, generator, scout, and evaluator roles. Both use evidence appropriate to the claim and scoped docs impact checks. The optional explicit-only `$docs-review` skill remains separately installable.

The bundled `docs-review` skill is optional and installed separately through
`install.sh --install-docs-review`; bootstrap does not modify personal skill directories.

Docs Review v3 uses scanner schema 5 and a schema-3 plan gate: each deterministic finding
binds its source fingerprint to scoped authority, intended semantics, evidence, and approved
docs. The plan also freezes the complete audit scope and executable edit contracts. Audit-only
IDs and validator phrases stay out of project documentation. After apply, large full-read
scopes are split into bounded independent shards; raw reports are validated losslessly and a
fresh synthesis auditor must pass before the final verdict. Any deficiency stops at a human
approval gate. Unchanged passing shards may be safely reused by hash in a correction round,
but synthesis is always fresh.

Upgrade an existing target project by copying in the newer package and pasting [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md). Updates are ownership-based: workflow kernel files replace old workflow files in place, mixed files use managed blocks, and target project facts are never overwritten.

### Default Development At A Glance

**The main agent plans, implements, and runs focused checks. A fresh read-only evaluator independently reviews the result.** Asking for independent review alone uses this workflow.

1. **Draft the plan.** Read the original request, governing contracts, and current code. Separate facts, confirmed decisions, and proposed choices.
2. **Clarify with Grill-me.** Before delivering the plan, including plan-only work, cite existing decisions or explicit delegation and ask about consequential choices that remain open. Use native question cards (`request_user_input_async` when Codex exposes it), with options, consequences, and a recommendation. Ask independent questions together and wait for actual answers before asking dependent questions. Explain an actual tool restriction before using text choices. Recommendations and preselection are not answers. Record answers and their sources in the same plan.
3. **Deliver the plan and implement when authorized.** Plan-only work ends with the formal plan. For authorized changes, the main agent implements and runs the directly relevant checks.
4. **Review and resolve.** Give the independent evaluator the original requirements, confirmed decisions, actual diff, relevant consumers, and validation evidence. It checks for deviations and assumptions promoted to facts or execution conditions. Confirmed gaps return directly to the main agent for repair and focused recheck; missing facts need evidence, and genuine business disputes go to the user.

For example, an interface that lacks cancellation is a fact about the current code. Waiting for the current request or adding cancellation is a scope choice to ask about before finalizing the plan.

See [`default-workflow.md`](./workflow-kernel/docs/workflow/default-workflow.md) and [`independent-evaluator.md`](./workflow-kernel/docs/workflow/independent-evaluator.md).

### Team Loop At A Glance

Start Team Loop only when the user explicitly requests `@team-loop`, `Team Loop`, `teamloop`, or Leader-driven delegation. **Leader coordinates and validates within the chat without editing files; Generator implements.** Subagents report to Leader.

1. **Dispatch Planner first.** The read-only Planner returns the goal, allowed and forbidden scope, a proposed approach, and review focus. Use [audit-first](./workflow-kernel/workflow/audit-first.md) when the cause is still unknown.
2. **Dispatch Generator when the plan permits it.** In `plan-gated`, Leader waits for the user's plan approval; in `auto-execute`, Leader dispatches once the scope is clear. Both use a fresh Generator that checks current code before editing.
3. **Add Scout on demand.** Generator sends a Scout Request to Leader. If approved, a read-only Scout returns evidence to Leader, who curates an Evidence Pack and hands it back to Generator.
4. **Validate and dispatch Evaluator.** Leader runs relevant validation and sends the original request, plan, actual diff, read scope, and results as an Evaluation Bundle to a fresh read-only Evaluator. Its findings return to Leader.
5. **Route rework or hand off.** For P0/P1 findings, failed validation, or scope violations, Leader schedules rework under the existing rules or reports a block. After review passes, the workflow stops at `human_acceptance_required`; if it cannot proceed, it reports `blocked`. The user makes the acceptance decision.

Leader sends a scoped Context Bootstrap and checks each role's Read Scope Ack. Planner and Scout can be reused after checking freshness. Generator and Evaluator use fresh sessions each round.

See [`team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md) for the dispatch protocol, trigger template, and rework criteria, and [`team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md) for the minimal context.

### Docs Review At A Glance

[`skills/docs-review/`](./skills/docs-review/) is an explicit-only macro workflow for
reconciling project facts after incremental documentation has accumulated duplication, stale
state, lifecycle leakage, or conflicting business meaning. It complements the per-turn
`docs impact` micro loop and is never invoked automatically by routine documentation edits.

Run `$docs-review [scope=<domain-or-docs-path>]` in Plan Mode for a read-only audit and human
arbitration, then run `$docs-review apply` in Default Mode only after the same task has an
approved schema-3 plan and an unchanged baseline. Apply is docs-only: it does not change
business code, migrations, tests, deployments, or external systems.

Version 3 binds every scanner-schema-5 finding to an exact source fingerprint, structured
disposition, evidence, intended semantics, and scoped authority. It also closes the complete
audit scope and validates executable edit contracts for transfers, path rewrites, and moves.
Post-apply closure uses bounded fresh shard auditors, losslessly validated raw JSON reports,
and a new synthesis auditor for cross-shard consumers and original evidence. Any deficiency
or protocol failure stops at a human approval gate. See the complete contract in
[`skills/docs-review/SKILL.md`](./skills/docs-review/SKILL.md).
