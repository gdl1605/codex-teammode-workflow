# Codex-teammode Workflow

> 中文优先 / English below.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.1.0-blue.svg)](./CHANGELOG.md)

Codex-teammode Workflow 是一个面向 **Codex** 和 **Claude Code** 的 prompt-first 工作流包。它不是运行时框架，而是一组可复制到任意项目中的 Markdown 规则、bootstrap prompt 和 docs scaffold，让个人开发者和小团队在 AI 编码会话中稳定执行：

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
