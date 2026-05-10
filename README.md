# Codex-teammode Workflow

> 中文优先 / English below.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.1.0-blue.svg)](./CHANGELOG.md)

Codex-teammode Workflow 是一个面向 **Codex** 同时兼容 **Claude Code** 的 prompt-first 工作流包。它不是运行时框架，而是一组可复制到任意项目中的 Markdown 规则、bootstrap prompt 和 docs scaffold，让个人开发者和小团队在 AI 编码会话中稳定执行：

- plan / audit / execute / review 轮次
- audit-first 根因锁定
- docs impact check
- 可选的 Team Mode：Leader + planner / generator / scout / evaluator
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
```

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
  workflow/                        # 协作、prompt、Team Mode、docs maintenance
  planner/                         # plan / execute / review schema
  product/                         # 项目事实占位，需按目标仓库填写
  architecture/                    # 架构占位，需按目标仓库填写
  handoff/                         # 跨会话 handoff
  plans/                           # active / completed plans
  evidence/                        # audit evidence
```

## 重要边界

这个项目只安装 **工作流机制**，不安装任何业务事实。

Bootstrap prompt 会要求目标 agent 不要复制本仓库的产品状态、计划、证据、架构结论或领域示例。目标仓库的 current code 永远是最高事实源。

## 核心概念

- **Normal workflow**：单 agent 轮次，包括 `plan-only`、`read-only audit`、`docs-only`、`execute`、`review`。
- **Team Mode**：由 Leader 在同一个会话里调度 planner / generator / scout / evaluator。
- **audit-first**：根因未锁定时先审计、写 evidence，再进入执行。
- **Fact priority**：current code > topic docs > `docs/handoff/latest.md` > archive。
- **human_acceptance_required**：最终停点，只有人类可以验收。

更多术语见 [`CONCEPTS.md`](./CONCEPTS.md)。

## Team Loop 工作流

Team Loop 是普通工作流的可选增强形态，适合需要一个 Leader 主线程调度多个独立 subagent 的任务。它不会替代普通的 `plan / audit / execute / review` 轮次；只有当用户明确使用 `@team-loop`、要求类 team-mode 闭环，或要求 Leader 调度多个 subagent 时才进入。

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

- **plan-gated**：用于数据库 schema / migration、服务端函数、权限、状态机、数据合同、高风险产品域、复杂资源链路、根因未锁，或用户明确要求先批准 plan 的任务。Leader 先派 planner 做只读收口，把 plan 交给用户确认后，才进入 generator 实现。
- **auto-execute**：用于文案、轻 UI、局部样式、docs 小修，以及 allowed scope 清楚、forbidden scope 简单的低风险任务。Leader 仍会先派 planner 快速只读收口，但不需要把 plan 先交给用户批准。

### 角色规范

- **Leader** 是唯一调度者。Leader 负责确认目标、判断 `plan-gated / auto-execute`、派生 subagent、附带 `Context Bootstrap`、核验每个 subagent 的 `Read Scope Ack`、整理 Evidence Pack、运行验证、组装 Evaluation Bundle，并决定返工、阻塞或停在 `human_acceptance_required`。Leader 不能让 subagent 彼此直接通信，也不能替 evaluator 自评通过。
- **Planner subagent** 是 Team Loop 内部只读角色，不等于旧的独立 planner mode。它负责读取入口文档、目标相关 docs / code / handoff / evidence，收口目标和非目标，判断风险模式，定义 allowed scope / forbidden scope、minimum progress unit、generator 启动前核对清单、可能的 scout 问题和 evaluator focus。planner 不改代码，也不能把建议实现层写成已验证事实。
- **Generator** 是默认唯一写代码角色。它必须消费 Leader 提供的 planner handoff 和 Evidence Pack，但仍要重新审计 current code，并在输出里给出 `Read Scope Ack`、touched files、修改摘要、验证建议、evaluator notes 和 docs impact。若审计范围过大，generator 只能向 Leader 提交 Scout Request，不能直接联系 scout 或自行派生 subagent。
- **Scout** 是只读线索收集角色。它只回答 Leader 指定的问题，只读必要的 current code、docs、handoff 或 evidence，并输出 verified facts、inferences、unresolved 和 citations。Scout Evidence 只能回 Leader，不能直接传给 generator，也不能设计完整实现方案或评价结果是否通过。
- **Evaluator** 是独立核验角色。它只消费 Leader 提供的 Evaluation Bundle 作为叙事入口，并读取必要 diff、code 和 docs 做复核。evaluator 要核验 generator 的 read scope、actual diff、allowed scope、docs impact 和验证输出，优先找 P0 / P1 阻塞问题；P2 / P3 默认进入 residual risk、backlog 或人工验收。

### 硬规则

- subagent 之间禁止直接通信；所有 planner / generator / scout / evaluator 输出都只回 Leader。
- Leader 每次派生 subagent 必须附带 `Context Bootstrap`，每个 subagent 输出开头必须有 `Read Scope Ack`。
- Evidence Pack 不能替代 generator 自己读取 current code；事实优先级始终是 current code > topic docs > handoff。
- P0 / P1、验证失败、越过 forbidden scope、缺少关键 read scope 时进入返工或 blocked。
- Team Loop 的终态只能是 `human_acceptance_required` 或 `blocked`；`accepted` 只能由人类明确表达。

完整规范见 [`workflow-kernel/docs/workflow/team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)，启动模板见 [`workflow-kernel/docs/workflow/prompt-template.md`](./workflow-kernel/docs/workflow/prompt-template.md)。

## 当前状态

`v0.1.0` 是 public preview。核心内核目前中文优先，README 提供中英双语入口。第一版明确支持 Codex 和 Claude Code；其他工具可参考 AGENTS.md/CLAUDE.md 约定自行适配。

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

It installs a normal plan / audit / execute / review workflow, an audit-first evidence flow, a docs impact check, and an optional Team Mode where a Leader coordinates planner, generator, scout, and evaluator roles.

This is an unofficial community project. It is not affiliated with, endorsed by, or sponsored by OpenAI.

Install:

```bash
git clone https://github.com/gdl1605/codex-teammode-workflow.git
cd codex-teammode-workflow
./install.sh /path/to/your-target-project
```

Then open Codex or Claude Code in the target project and paste the bootstrap prompt printed by the installer.

### Team Loop At A Glance

Team Loop is an optional workflow for tasks that benefit from one Leader coordinating multiple isolated subagents. It is only triggered when the user explicitly asks for `@team-loop`, a team-mode loop, or Leader-driven subagent coordination.

- **Leader** is the only scheduler. It chooses `plan-gated` or `auto-execute`, sends each subagent a Context Bootstrap, checks Read Scope Ack, prepares Evidence Packs and Evaluation Bundles, runs validation, and stops at `human_acceptance_required`.
- **Planner subagent** is read-only. It narrows the problem, risk mode, allowed scope, forbidden scope, minimum progress unit, generator startup checks, possible scout questions, and evaluator focus.
- **Generator** is the default writing role. It must re-audit current code before implementation, respect forbidden scope, report touched files and docs impact, and request scout support only through Leader.
- **Scout** is read-only evidence support. It answers Leader-scoped questions with verified facts, inferences, unresolved items, citations, and confidence.
- **Evaluator** is independent verification. It reviews the Evaluation Bundle, diff, code, docs, validation output, generator read scope, and docs impact claim before returning pass, request changes, or blocked.

Subagents never talk directly to each other. The final state is `human_acceptance_required` or `blocked`; only a human can mark the work accepted.
