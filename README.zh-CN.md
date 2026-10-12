# Codex-teammode Workflow

Codex-teammode Workflow 是一个面向 **Codex** 和 **Claude Code** 的 prompt-first 工作流包。它不是运行时框架，而是一组可复制到任意项目中的 Markdown 规则、bootstrap prompt 和 docs scaffold。

它的目标是帮助个人开发者和小团队在 AI 编码会话中稳定执行：

- plan / audit / execute / review 轮次
- audit-first 根因锁定
- docs impact check
- 可选 `$docs-review`：人工触发的跨文档事实对账与清理
- 可选 Team Loop：Leader + planner / generator / scout / evaluator
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
./install.sh --install-docs-review /path/to/project
./install.sh --install-docs-review --skill-root /path/to/skills /path/to/project
```

`docs-review` 是可选个人 skill。未提供 `--install-docs-review` 时，安装器不会修改
个人 skill 目录。默认目标是 `$CODEX_HOME/skills`，未设置时使用
`~/.codex/skills`。目标不存在时安装、内容相同则 no-op；内容不同时必须显式加
`--force-skill`，安装器会先备份再只替换精确的 `docs-review` 目录。`--dry-run`
会显示 workflow 与可选 skill 两个目标，但不写入。
默认 bootstrap / update 也不会把这个可选 skill 的介绍写入目标项目的 `AGENTS.md` 或
`CLAUDE.md`；需要时由用户显式安装并调用 skill。

## 安装后会生成什么

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

目标项目已经安装过旧版工作流时，不要重新用 bootstrap 做全量覆盖。把新版 `codex-teammode-workflow/` 文件夹放进目标项目后，粘贴 [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md)。

升级按 [`UPDATE_MANIFEST.md`](./UPDATE_MANIFEST.md) 的 ownership 策略执行：

- workflow kernel：`docs/workflow/*`、`docs/planner/*`、`workflow/audit-first.md` 等原地替换旧版工作流文件，不生成 `.new`，并清理旧升级遗留的 workflow `.new` 文件。
- mixed files：`AGENTS.md`、`CLAUDE.md`、`docs/README.md` 只替换 `codex-teammode:managed` block。
- target facts：`docs/product/*`、`docs/architecture/*`、`docs/handoff/*`、`docs/plans/*`、`docs/evidence/*` 永不自动覆盖。

升级后目标项目应写入 `docs/workflow/.codex-teammode-version`，用于记录版本和已安装文件 hash，作为后续升级基线和报告依据；workflow kernel 仍按新版原地替换。

## Docs Review Skill

[`skills/docs-review/`](./skills/docs-review/) 是随工作流包版本化、但只允许人工显式触发的
项目事实校正 skill。它用于处理长期增量维护后出现的重复事实、过期状态、current/candidate
混写、active/completed 生命周期错位，以及实现、部署、验收、法务和发布状态被错误合并为
“已完成”等问题。

它与 `docs impact` 的分工是：`docs impact` 负责每轮增量维护，`$docs-review` 负责人工触发的
跨文档宏观对账。Codex 中先在 Plan Mode 运行 `$docs-review [scope=<domain-or-docs-path>]`
完成只读审计和人工裁决，再在同一任务存在已批准 schema-3 计划且 baseline 未漂移时，在
Default Mode 运行 `$docs-review apply`。Apply 只修改批准的 Markdown docs，不修改业务代码、
migration、测试、部署环境或外部系统。

v3 会把每条 scanner-schema-5 finding 精确绑定到 source fingerprint、结构化 disposition、
目标语义、证据和人工权限，同时冻结完整 `audit_scope_manifest` 与结构化 `edit_contracts`，
验证 canonical transfer、path rewrite 和 lifecycle move 的后置条件。Apply 后按预算运行多个
fresh shard auditor，原始 JSON 必须无损保存和严格验证；全部 shard pass 后，还要由全新的
synthesis auditor 核验跨分片 consumer、canonical owner 和原始 evidence。任一 deficiency
或协议错误都会停在人类确认门，不能同轮自行修复。完整协议见
[`SKILL.md`](./skills/docs-review/SKILL.md)。

## Team Loop 工作流

Team Loop 是普通工作流的可选增强，只有用户明确声明 `@team-loop` / `Team Loop` / `teamloop` 时才启用。Leader 调度 planner / generator / scout / evaluator，planner / scout 可复用，generator / evaluator 每轮 fresh。终态只能是 `human_acceptance_required` 或 `blocked`。

完整规范和启动模板见 [`workflow-kernel/docs/workflow/team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)，subagent 默认核心合同见 [`workflow-kernel/docs/workflow/team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md)，轻量角色胶囊见 [`workflow-kernel/docs/workflow/team-loop-roles/`](./workflow-kernel/docs/workflow/team-loop-roles/)。

## 重要边界

这个项目只安装 **工作流机制**，不安装任何业务事实。普通实现事实以目标仓库的 current code 为首要证据；显式运行 `$docs-review` 时按 claim 类型路由权限，业务意图、部署、人工验收和法务状态不能从“代码已实现”直接推导。

docs impact 是每轮增量维护的微循环；`$docs-review` 是独立的人工触发宏循环。Codex
中先在 Plan Mode 只读核验并裁决，再在同一任务形成已批准计划后用
`$docs-review apply` 做 docs-only 校正。工作流 package 升级不会静默覆盖个人安装的
skill；需要采用新版时重新显式运行 skill 安装命令。
新版校正会保护 canonical 业务语义覆盖，禁止只在归档页头覆盖矛盾正文，并在首版范围
冻结时要求每份 active plan 明确是否属于首版、是否阻塞发布。

`docs-review` v3 使用 scanner schema 5 和 plan schema 3：每条 deterministic finding
必须绑定 source fingerprint、结构化 resolution group、精确人工权限、证据与批准文件，并由
完整 `audit_scope_manifest` 和结构化 `edit_contracts` 封闭读写范围及后置条件；Claim ID、
审计 ID 和仅供 validator 使用的“稳定锚点”不得写进业务 docs。Apply 后会把大型全文范围按
预算分成多个独立 shard，无损保存并严格校验原始 auditor JSON；全部 shard 通过后仍须由
全新的 synthesis auditor 做跨分片终审。任一 deficiency 都先停下来向人类报告并等待批准；
修正轮只可按 hash 复用完全未变化且已 pass 的 shard，synthesis 永不复用。

复杂长规划可选使用独立 skill 包 [`gdl1605-Skills`](https://github.com/gdl1605/gdl1605-Skills)，其中 `longterm-planning` 用于长线程规划 / 长规划 / 系统级规划的方向选择、HTML Selection 和小规划产出。

## 当前状态

`v0.2.0` 是当前 public preview。核心内核目前中文优先，当前版本明确支持 Codex 和 Claude Code。

## 贡献

欢迎贡献工作流表达、Codex / Claude Code 使用反馈、英文翻译、安装脚本改进，以及泛化、脱敏、可复用的示例模板。见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

路线图见 [`ROADMAP.md`](./ROADMAP.md)，支持渠道见 [`SUPPORT.md`](./SUPPORT.md)。

## License

[MIT](./LICENSE).
