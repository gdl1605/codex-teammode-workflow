# Codex-teammode Workflow

> 中文优先 / English below.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.2.0-blue.svg)](./CHANGELOG.md)

Codex-teammode Workflow 是一个面向 **Codex** 同时兼容 **Claude Code** 的 prompt-first 工作流包。它不是运行时框架，而是一组可复制到任意项目中的 Markdown 规则、bootstrap prompt 和 docs scaffold，让个人开发者和小团队在 AI 编码会话中稳定执行：

- plan / audit / execute / review 轮次
- audit-first 根因锁定
- docs impact check
- 可选 `$docs-review`：人工触发的跨文档事实对账与清理
- 可选的 Team Loop：Leader + planner / generator / scout / evaluator
- 永远停在 `human_acceptance_required`，不让 agent 自己宣布验收

## 非官方说明

Codex-teammode Workflow 是社区项目，不是 OpenAI 官方项目，也未获得 OpenAI 认可、赞助或背书。`Codex` 相关名称仅用于说明本工作流面向的使用场景。

## 适用对象

- 使用 Codex 或 Claude Code 的个人开发者
- 希望统一 AI 协作规则的小团队
- 经常被上下文丢失、想象式修复、未审计执行困扰的 AI coding agent 重度用户

## 安装

### 脚本安装

```bash
git clone https://github.com/gdl1605/codex-teammode-workflow.git
cd codex-teammode-workflow
./install.sh /path/to/your-target-project
```

脚本会把本项目复制到目标仓库的 `codex-teammode-workflow/` 目录，并尽量把 bootstrap prompt 复制到剪贴板。然后在目标仓库中打开 Codex 或 Claude Code，粘贴 prompt。

常用参数：

```bash
./install.sh --dry-run /path/to/project
./install.sh --force /path/to/project
./install.sh --no-clipboard /path/to/project
./install.sh --install-docs-review /path/to/project
./install.sh --install-docs-review --skill-root /path/to/skills /path/to/project
```

`docs-review` 是可选个人 skill。没有 `--install-docs-review` 时，安装器绝不修改个人
skill 目录。默认目标是 `$CODEX_HOME/skills`，未设置时使用 `~/.codex/skills`。
目标不存在时安装，内容完全一致时 no-op；内容不同时默认拒绝覆盖，只有
显式加 `--force-skill` 才会先创建时间戳备份，再替换精确的 `docs-review` 目录。
`--dry-run` 会同时显示 workflow package 目标和可选 skill 目标，不写文件。
默认 bootstrap / update 也不会把这个可选 skill 的介绍写入目标项目的 `AGENTS.md` 或
`CLAUDE.md`；需要时由用户显式安装并调用 skill。

### 手动安装

1. 把 `codex-teammode-workflow/` 文件夹复制到目标仓库根目录。
2. 在目标仓库中打开 Codex 或 Claude Code。
3. 粘贴 [`BOOTSTRAP_PROMPT.md`](./BOOTSTRAP_PROMPT.md) 的内容。

目标 agent 会读取工作流内核，审计目标仓库，并创建或合并：

```text
AGENTS.md                          # Codex / AGENTS.md-aware tools 入口
CLAUDE.md                          # Claude Code 入口，与 AGENTS.md 同步
workflow/audit-first.md            # 根因审计优先流程
docs/
  README.md                        # docs 入口地图
  workflow/                        # 协作、prompt、Team Loop、docs maintenance
  planner/                         # plan / execute / review schema
  product/                         # 项目事实占位，需按目标仓库填写
  architecture/                    # 架构占位，需按目标仓库填写
  handoff/                         # 跨会话 handoff
  plans/                           # active / completed plans
  evidence/                        # audit evidence
```

## 升级旧项目

当目标项目已经安装过旧版工作流时，不要重新粘贴 bootstrap prompt 做全量覆盖。把新版 `codex-teammode-workflow/` 文件夹放进目标项目后，粘贴 [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md)。

升级流程按 [`UPDATE_MANIFEST.md`](./UPDATE_MANIFEST.md) 的 ownership 策略执行：

- **workflow kernel**：`docs/workflow/*`、`docs/planner/*`、`workflow/audit-first.md` 等原地替换旧版工作流文件，不生成 `.new`，并清理旧升级遗留的 workflow `.new` 文件。
- **mixed files**：`AGENTS.md`、`CLAUDE.md`、`docs/README.md` 只替换 `codex-teammode:managed` block，保留 block 外的目标项目规则。
- **target facts**：`docs/product/*`、`docs/architecture/*`、`docs/handoff/*`、`docs/plans/*`、`docs/evidence/*` 永不自动覆盖。

升级完成后，目标项目应写入 `docs/workflow/.codex-teammode-version`，用于记录版本和已安装文件 hash。后续升级会用这个 marker 做基线和报告，但 workflow kernel 仍按新版原地替换。

## 重要边界

这个项目只安装 **工作流机制**，不安装任何业务事实。

Bootstrap prompt 会要求目标 agent 不要复制本仓库的产品状态、计划、证据、架构结论或领域示例。普通实现事实仍以目标仓库的 current code 为首要证据；显式运行 `$docs-review` 时则按 claim 类型路由权限，业务意图、部署、人工验收和法务状态不能被“代码已实现”替代。

复杂长规划可选使用独立 skill 包 [`gdl1605-Skills`](https://github.com/gdl1605/gdl1605-Skills)，其中 `longterm-planning` 用于长线程规划 / 长规划 / 系统级规划的方向选择、HTML Selection 和小规划产出。

## 核心概念

- **Normal workflow**：单 agent 轮次，包括 `plan-only`、`read-only audit`、`docs-only`、`execute`、`review`。
- **Team Loop**：由 Leader 在同一个会话里调度 planner / generator / scout / evaluator。
- **audit-first**：根因未锁定时先审计、写 evidence，再进入执行。
- **Fact priority**：普通实现事实按 current code > topic docs > `docs/handoff/latest.md` > archive；`$docs-review` 对业务意图、部署、验收和法务 claim 使用各自权限。
- **docs impact / docs-review**：前者是每轮增量微循环；后者是人工触发、Plan/Apply 两阶段的事实校正宏循环。
- **docs-review v3 plan gate**：scanner schema 5 的每条 finding 都绑定 source fingerprint、结构化 resolution group、精确人工权限和批准文件；完整 audit scope 与每项 edit contract 同时冻结，机器 Claim ID / 稳定锚点不得写进业务 docs。
- **docs-review sharded closure**：大型全文审查按预算分片，原始 auditor JSON 无损校验；所有 shard pass 后再由全新 synthesis auditor 做跨分片终审，任一不足先停在人类确认门。
- **human_acceptance_required**：最终停点，只有人类可以验收。

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

## Team Loop 工作流

Team Loop 是普通工作流的可选增强形态，适合需要一个 Leader 主线程调度多个独立 subagent 的任务。它不会替代普通的 `plan / audit / execute / review` 轮次；只有当用户明确使用 `@team-loop`、`Team Loop`、`teamloop`，或明确要求 Leader 调度 subagent 时才进入。普通工作流不因任务复杂度自动升级为 Team Loop。

Team Loop 的核心通信结构是：

```text
User
  <-> Leader
      -> planner subagent
      -> generator subagent
      -> scout subagent A / B
      -> evaluator subagent
      -> human_acceptance_required
```

### 两种运行模式

本节只在用户已经明确进入 Team Loop 后使用，用于选择 Team Loop 内部节奏，不作为自动触发 Team Loop 的条件。

- **plan-gated**：先把 planner 收口结果交给用户确认，再派 generator。
- **auto-execute**：Leader 在 planner 快速收口后直接派 generator，最后仍停在人工验收。

### 角色规范

- **Leader** 是唯一调度者。Leader 负责确认目标、判断 `plan-gated / auto-execute`、派生 subagent、附带 `Context Bootstrap`、核验每个 subagent 的 `Read Scope Ack`、整理 Evidence Pack、运行验证、组装 Evaluation Bundle，并决定返工、阻塞或停在 `human_acceptance_required`。Leader 不能直接实现或改文件，不能让 subagent 彼此直接通信，也不能替 evaluator 自评通过。
- **Planner subagent** 是 Team Loop 内部只读角色，不等于旧的独立 planner mode。它负责读取入口文档、目标相关 docs / code / handoff / evidence，收口目标和非目标，判断风险模式，定义 allowed scope / forbidden scope、minimum progress unit、generator 启动前核对清单、可能的 scout 问题和 evaluator focus。planner 不改代码，也不能把建议实现层写成已验证事实。
- **Generator** 是默认唯一写代码角色。它必须消费 Leader 提供的 planner handoff 和 Evidence Pack，但仍要重新审计 current code，并在输出里给出 `Read Scope Ack`、touched files、修改摘要、验证建议、evaluator notes 和 docs impact。若审计范围过大，generator 只能向 Leader 提交 Scout Request，不能直接联系 scout 或自行派生 subagent。
- **Scout** 是只读线索收集角色。它只回答 Leader 指定的问题，只读必要的 current code、docs、handoff 或 evidence，并输出 verified facts、inferences、unresolved 和 citations。Scout Evidence 只能回 Leader，不能直接传给 generator，也不能设计完整实现方案或评价结果是否通过。
- **Evaluator** 是独立核验角色。它只消费 Leader 提供的 Evaluation Bundle 作为叙事入口，并读取必要 diff、code 和 docs 做复核。evaluator 要核验 generator 的 read scope、actual diff、allowed scope、docs impact 和验证输出，优先找 P0 / P1 阻塞问题；P2 / P3 默认进入 residual risk、backlog 或人工验收。

### 硬规则

- subagent 之间禁止直接通信；所有 planner / generator / scout / evaluator 输出都只回 Leader。
- Leader 每次派生 fresh subagent 必须附带 `Context Bootstrap`；复用 planner / scout 时必须附带 cache manifest 和 freshness check。每个 subagent 输出开头必须有 `Read Scope Ack`。
- planner / scout 可按 freshness check 有限复用；generator / evaluator 每轮 fresh。
- Evidence Pack 不能替代 generator 自己读取 current code；对当前实现事实，证据优先级是 current code > topic docs > handoff，业务意图和外部生命周期事实按各自权限/evidence 路由。
- P0 / P1、验证失败、越过 forbidden scope、缺少关键 read scope 时进入返工或 blocked。
- Team Loop 的终态只能是 `human_acceptance_required` 或 `blocked`；`accepted` 只能由人类明确表达。

完整规范和启动模板见 [`workflow-kernel/docs/workflow/team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)，subagent 默认核心合同见 [`workflow-kernel/docs/workflow/team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md)，轻量角色胶囊见 [`workflow-kernel/docs/workflow/team-loop-roles/`](./workflow-kernel/docs/workflow/team-loop-roles/)。

## 当前状态

`v0.2.0` 是当前 public preview。核心内核目前中文优先，README 提供中英双语入口。当前版本明确支持 Codex 和 Claude Code；其他工具可参考 AGENTS.md/CLAUDE.md 约定自行适配。

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

Codex-teammode Workflow is a prompt-first workflow package for **Codex** and **Claude Code**. It is not a runtime framework. It is a portable set of Markdown rules, a bootstrap prompt, and a docs scaffold that helps solo developers and small teams run a consistent AI coding process.

It installs a normal plan / audit / execute / review workflow, an audit-first evidence flow, a docs impact check, an optional explicit-only `$docs-review` fact-reconciliation skill, and an optional Team Loop where a Leader coordinates planner, generator, scout, and evaluator roles.

This is an unofficial community project. It is not affiliated with, endorsed by, or sponsored by OpenAI.

For complex long-horizon planning, use the optional standalone [`gdl1605-Skills`](https://github.com/gdl1605/gdl1605-Skills) skill package; its `longterm-planning` skill handles direction selection, local HTML Selection, and scoped mini-plan output.

Install:

```bash
git clone https://github.com/gdl1605/codex-teammode-workflow.git
cd codex-teammode-workflow
./install.sh /path/to/your-target-project
```

Optionally install the bundled personal skill with:

```bash
./install.sh --install-docs-review /path/to/your-target-project
./install.sh --install-docs-review --skill-root /path/to/skills /path/to/your-target-project
```

Without `--install-docs-review`, the installer never changes a personal skill directory.
The default parent is `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is unset.
Use `--force-skill` only when you want the exact existing `docs-review` target backed up and
replaced. Workflow package updates do not silently refresh the personal skill.
Default bootstrap and update flows also keep the optional skill guide out of target
`AGENTS.md` and `CLAUDE.md`; users install and invoke the skill explicitly when needed.

Docs Review v3 uses scanner schema 5 and a schema-3 plan gate: each deterministic finding
binds its source fingerprint to scoped authority, intended semantics, evidence, and approved
docs. The plan also freezes the complete audit scope and executable edit contracts. Audit-only
IDs and validator phrases stay out of project documentation. After apply, large full-read
scopes are split into bounded independent shards; raw reports are validated losslessly and a
fresh synthesis auditor must pass before the final verdict. Any deficiency stops at a human
approval gate. Unchanged passing shards may be safely reused by hash in a correction round,
but synthesis is always fresh.

Then open Codex or Claude Code in the target project and paste the bootstrap prompt printed by the installer.

Upgrade an existing target project by copying in the newer package and pasting [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md). Updates are ownership-based: workflow kernel files replace old workflow files in place, mixed files use managed blocks, and target project facts are never overwritten.

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

### Team Loop At A Glance

Team Loop is an optional workflow for tasks that benefit from one Leader coordinating multiple isolated subagents. It is only triggered when the user explicitly asks for `@team-loop`, `Team Loop`, `teamloop`, or Leader-driven subagent coordination. The normal workflow never auto-upgrades to Team Loop based on task complexity.

- **Leader** is the only scheduler. It chooses `plan-gated` or `auto-execute`, sends each subagent a Context Bootstrap, checks Read Scope Ack, prepares Evidence Packs and Evaluation Bundles, runs validation, and stops at `human_acceptance_required`. Leader does not implement changes directly.
- **Planner subagent** is read-only. It narrows the problem, risk mode, allowed scope, forbidden scope, minimum progress unit, generator startup checks, possible scout questions, and evaluator focus.
- **Generator** is the default writing role. It must re-audit current code before implementation, respect forbidden scope, report touched files and docs impact, and request scout support only through Leader.
- **Scout** is read-only evidence support. It answers Leader-scoped questions with verified facts, inferences, unresolved items, citations, and confidence.
- **Evaluator** is independent verification. It reviews the Evaluation Bundle, diff, code, docs, validation output, generator read scope, and docs impact claim before returning pass, request changes, or blocked.

Planner and scout may be reused across dispatches with freshness checks; generator and evaluator are always fresh per round.

Each fresh subagent should receive a slim Context Bootstrap with the current tool's primary entry file, `docs/README.md`, `team-loop-core.md`, and only its matching role capsule.

Subagents never talk directly to each other. The final state is `human_acceptance_required` or `blocked`; only a human can mark the work accepted.
