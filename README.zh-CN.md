# Codex-teammode Workflow

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
3. **轻量核验计划。** 正式交付前派 fresh 只读 evaluator，对照原话、后续纠正和计划，找遗漏、约束弱化、无来源取舍及假设混写。明确遗漏直接修正，事实由 agent 补查，真实歧义沿原生卡片交用户；修正只复核发现及直接影响。仅规划在交付后结束，不要求实现结果。
4. **按授权实现。** 主 agent 仍回查原话、纠正和修订计划，再改动并运行直接相关的验证。规划核验不新增整份计划批准，也不能替代实施授权。
5. **独立核验并收口。** 把原要求、修订计划、实际 diff、相关调用路径、验证证据及完成声明交给另一个 fresh 只读 evaluator。它检查实际行为是否满足原要求、是否说了没做、假设是否被写成事实或门禁；不能用实现与测试共享同一假设来证明要求已满足。确定缺口回主 agent 修复，事实补证，真实争议交用户。

例如，代码没有取消入口是**现状**；本次是“等当前请求结束再退出（推荐）”，还是“增加取消、停止确认和部分结果保存”，则是**交付取舍**。用户还没决定时，就把这两个选项发成卡片。

规划与实现核验都会检查关键规则和测试预期本身的依据。代码、测试或文档写了什么，不会自动证明这条规则正确；reviewer 的判断也要给出原依据和具体影响。明确错误在授权内修，事实不明由 agent 补证，真实业务取舍沿原生卡片交用户。

完整流程和 Review Request 见 [`default-workflow.md`](./workflow-kernel/docs/workflow/default-workflow.md)，核验角色见 [`independent-evaluator.md`](./workflow-kernel/docs/workflow/independent-evaluator.md)。

## Team Loop 工作流

用户明确要求 `@team-loop`、`Team Loop` / `teamloop` 或 Leader 调度时启用。**Leader 是同一聊天里的唯一调度者，负责交接和验证，不直接改文件；Generator 负责实现。** 各 subagent 只向 Leader 回报。

### 一轮怎样调度

```text
Leader 派 Planner → 澄清关键取舍 → fresh Evaluator 轻量审计划 → Leader 安排修正
→ 仅规划则交付；已授权实施则按模式放行 → Generator 回查原要求并实现
→ Leader 验证并派 fresh Evaluator → 回报 Leader → 返工或人工验收
```

1. **先派 Planner。** 只读核对需求和当前代码，给 Leader 返回目标、允许与禁止的修改范围、实现建议和核验重点。根因未锁时，先按 [audit-first](./workflow-kernel/workflow/audit-first.md) 只读查明，再安排实现。
2. **先核验计划，再按模式放行。** Leader 把相关原话、纠正、决定来源和计划交 fresh Evaluator 轻量核对；明确遗漏回 Planner 修订，事实补证，真实歧义由 Leader 发原生卡片。仅规划交付后结束；已授权实施时，`plan-gated` 等用户批准计划，`auto-execute` 不新增批准。Generator 仍回查原话、修订计划和当前代码。
3. **需要时插入 Scout。** Generator 缺证据时向 Leader 提出 `Scout Request`。Leader 决定是否派只读 Scout；Scout 把证据交回 Leader，由 Leader 整理成 `Evidence Pack` 再交 Generator。Scout 不是每轮固定步骤。
4. **验证后再派 Evaluator。** Leader 运行必要验证，提供原话、纠正、修订计划、实际 diff、读取范围、验证结果及完成声明。Evaluator 按共用核验原则追真实行为，检查要求弱化、遗漏、计划与实际偏离、假设混写及声称已做却无证据，只向 Leader 回报。
5. **Leader 处理返工或交回用户。** 确定缺口交对应角色修正，不能仅因 P2 / P3 标签或列为 residual risk 就忽略明确违反要求的项。授权实施后核验收口停在 `human_acceptance_required`，真实阻塞报 `blocked`；仅规划注明未实施，不能因没有 Generator 结果判阻塞。最终验收由用户决定。

Leader 派发时提供裁剪过的 `Context Bootstrap`，用 `Read Scope Ack` 确认角色实际读了哪些材料。Planner 和 Scout 核对材料仍有效后可以复用；Generator 和 Evaluator 每轮使用新会话。

完整调度、触发示例与返工条件见 [`team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)；最小上下文和角色约定见 [`team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md) 与[角色文件](./workflow-kernel/docs/workflow/team-loop-roles/)。

## 安装后会生成什么

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

目标项目已经安装过旧版工作流时，不要重新用 bootstrap 做全量覆盖。把新版 `codex-teammode-workflow/` 文件夹放进目标项目后，粘贴 [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md)。

升级按 [`UPDATE_MANIFEST.md`](./UPDATE_MANIFEST.md) 的 ownership 策略执行：

- workflow kernel：清单内的普通开发 / Team Loop 内核及 `workflow/audit-first.md` 原地替换旧版文件；按 `remove-workflow` 清单删除退役 planner schema 等精确文件，不生成 `.new`，并清理旧升级遗留的 workflow `.new` 文件。
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

## 当前状态

当前发布版本为 [v0.5.0](https://github.com/gdl1605/codex-teammode-workflow/releases/tag/v0.5.0)，变更见 [CHANGELOG.md](./CHANGELOG.md)。核心内核中文优先，支持 Codex 和 Claude Code。

## 贡献

欢迎贡献工作流表达、Codex / Claude Code 使用反馈、英文翻译、安装脚本改进，以及泛化、脱敏、可复用的示例模板。见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

路线图见 [`ROADMAP.md`](./ROADMAP.md)，支持渠道见 [`SUPPORT.md`](./SUPPORT.md)。

## License

[MIT](./LICENSE).
