# Codex-teammode Workflow

Codex-teammode Workflow 是一个面向 **Codex** 和 **Claude Code** 的 prompt-first 工作流包。它不是运行时框架，而是一组可复制到任意项目中的 Markdown 规则、bootstrap prompt 和 docs scaffold。

它的目标是帮助个人开发者和小团队在 AI 编码会话中稳定执行：

- plan / audit / execute / review 轮次
- audit-first 根因锁定
- docs impact check
- 可选 Team Mode：Leader + planner / generator / scout / evaluator
- 最终停在 `human_acceptance_required`，由人类验收

## 非官方说明

Codex-teammode Workflow 是社区项目，不是 OpenAI 官方项目，也未获得 OpenAI 认可、赞助或背书。`Codex` 相关名称仅用于说明本工作流面向的使用场景。

## 安装

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

## 安装后会生成什么

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

这个项目只安装 **工作流机制**，不安装任何业务事实。目标仓库的 current code 永远是最高事实源。

## 当前状态

`v0.1.0` 是 public preview。核心内核目前中文优先，第一版明确支持 Codex 和 Claude Code。

## 贡献

欢迎贡献工作流表达、Codex / Claude Code 使用反馈、英文翻译、安装脚本改进，以及泛化、脱敏、可复用的示例模板。见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

路线图见 [`ROADMAP.md`](./ROADMAP.md)，支持渠道见 [`SUPPORT.md`](./SUPPORT.md)。

## License

[MIT](./LICENSE).
