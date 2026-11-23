# Codex-teammode Workflow

## 安装

1. Clone 本仓库到本地：

   ```bash
   git clone https://github.com/gdl1605/codex-teammode-workflow.git
   ```

2. 打开 clone 得到的目录，复制 [`BOOTSTRAP_PROMPT.md`](./BOOTSTRAP_PROMPT.md) 的全部内容。
3. 在任意一个你想安装工作流的项目中打开 agent 对话（如 Codex 或 Claude Code），粘贴并发送即可。Agent 会读取工作流，并将它安装到当前项目。

## 这是什么

Codex-teammode Workflow 为 **Codex** 和 **Claude Code** 提供可安装到项目里的协作规则、启动提示和文档结构。两种执行模式共用一个项目 Wiki。

**普通执行**是默认入口。日常运行、恢复、排障和业务报告沿项目原流程；用户明确要求改机制或规划该变更时，进入[普通开发](#普通开发工作流)。[Team Loop](#team-loop-工作流) 在用户显式启用后由 Leader 调度团队。

安装时，agent 自动生成或合并 `docs/` **项目 Wiki**，索引为 `docs/README.md`。开发收口时，agent 按[文档维护规则](./workflow-kernel/docs/workflow/docs-maintenance.md)更新受影响的主文档；长期积累的冗余和过期内容用 [`$docs-review`](#docs-review-skill) 定期清理。

![项目 Wiki：安装生成 → 增量更新 → 定期用 $docs-review 清理](./assets/project-wiki.svg)

## 普通开发工作流

**先计划，再实现。** 影响行为、范围、成本或验收的实施细节或交付粒度仍待决定时，必须在定稿前用 **Grill-me** 确认。主 agent 负责实现和验证，独立 evaluator 分别审查计划和实现，审查限于原要求及改动的直接影响。仅执行、仅规划或专项核验按用户指定的范围交付。

![普通开发：计划 → Grill-me（取舍待定时） → 实现 → 独立审查](./assets/default-development.svg)

1. **形成草案。** 对照原要求、有效合同和当前实现，区分事实、已确认的决定和建议，按任务规模拟定方案。
2. **用 Grill-me 澄清取舍。** 事实由主 agent 查证，明确决定和委托直接沿用。仍需用户决定的取舍用原生卡片给出选项、影响和推荐；工具受限时说明原因并用文本选项。独立的问题同轮提交，依赖前置决定的问题等实际回答后再提交，回答及其来源写回同一份计划。
3. **轻量核验计划。** 正式交付前，由新的只读 evaluator 对照原话、后续纠正和计划，核对遗漏、约束变化和关键决定的依据。主 agent 修正明确缺口、补查事实，真实歧义交用户确认。仅规划任务在计划交付后结束。
4. **按授权实现。** 主 agent 回查原要求、后续纠正与修订计划，完成实现和实际接线，再运行直接相关的验证。
5. **独立核验实现。** 由另一位新的只读 evaluator 对照原要求、修订计划、实际 diff、调用路径、验证证据和完成声明，检查漏做、越界实现及额外验收条件。主 agent 按原要求和直接影响核对审查发现，在授权内修复明确缺口，事实缺口补证，真实取舍交用户。

例如，等待当前请求结束后退出和增加主动取消，对应不同交付范围。范围仍待决定时，主 agent 用 Grill-me 说明两种做法的行为和成本差异。

普通开发与 Team Loop 都区分 `review_phase: plan / implementation`（规划 / 实现）和 `review_kind: initial / recheck`（首次 / 复审）。关键规则、测试预期和审查发现都需要原始依据。复审只覆盖原问题、修复及直接影响，新阻塞项须说明与修复的因果关系；独立新增实现只审新增部分。达到原要求即收口。

完整流程和 Review Request 见 [`default-workflow.md`](./workflow-kernel/docs/workflow/default-workflow.md)，核验角色见 [`independent-evaluator.md`](./workflow-kernel/docs/workflow/independent-evaluator.md)。

## Team Loop 工作流

**Leader 拆分任务，调度 agent 团队自动推进规划、实现、验收和返工。** 基本错误由团队在交付前处理；计划里由团队负责的验收条款全部通过后，Leader 把结果和证据交给人做最终验收。

![Team Loop：规划 → 实现 → 内部验收（缺口返工） → 人工验收](./assets/team-loop.svg)

用户本轮明确要求机制变更或其工程方案，并指定 `@team-loop`、`Team Loop` / `teamloop` 或 Leader 调度时启用。同一会话中，Leader 统一调度、交接和验证；Generator 负责实现，各 subagent 只向 Leader 回报。

### 一轮怎样调度

```text
Leader 派 Planner → 澄清关键取舍 → fresh Evaluator 轻量审计划 → Leader 安排修正
→ 仅规划则交付；已授权实施则按模式放行 → Generator 回查原要求并实现
→ Leader 验证并派 fresh Evaluator → 回报 Leader → 返工或人工验收
```

1. **先派 Planner。** 只读核对需求和当前代码，给 Leader 返回目标、允许与禁止的修改范围、实现建议和核验重点。
2. **先核验计划，再按模式放行。** Leader 把相关原话、纠正、决定来源和计划交 fresh Evaluator 轻量核对；明确遗漏回 Planner 修订，事实补证，真实歧义由 Leader 发原生卡片。仅规划交付后结束；已授权实施时，`plan-gated` 等用户批准计划，`auto-execute` 不新增批准。Generator 仍回查原话、修订计划和当前代码。
3. **需要时插入 Scout。** Generator 缺证据时向 Leader 提出 `Scout Request`。Leader 决定是否派只读 Scout；Scout 把证据交回 Leader，由 Leader 整理成 `Evidence Pack` 再交 Generator。Scout 不是每轮固定步骤。
4. **验证后再派 Evaluator。** Leader 运行必要验证，提供原话、纠正、修订计划、实际 diff、读取范围、验证结果及完成声明。Evaluator 按共用核验原则追真实行为，检查要求弱化、遗漏、计划与实际偏离、假设混写及声称已做却无证据，只向 Leader 回报。
5. **Leader 处理返工或交回用户。** 确定缺口交对应角色按根因修复，Leader 用原问题、修复变化及直接影响派定向复审；严重性标签不能重开未变部分，也不能用低严重性忽略范围内违反要求的项。达到原要求就结束核验。授权实施后停在 `human_acceptance_required`，真实阻塞报 `blocked`；仅规划注明未实施，不能因没有 Generator 结果判阻塞。最终验收由用户决定。

Leader 派发时提供裁剪过的 `Context Bootstrap`，用 `Read Scope Ack` 确认角色实际读了哪些材料。Planner 和 Scout 核对材料仍有效后可以复用；Generator 和 Evaluator 每轮使用新会话。

完整调度、触发示例与返工条件见 [`team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md)；最小上下文和角色约定见 [`team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md) 与[角色文件](./workflow-kernel/docs/workflow/team-loop-roles/)。

## 安装后会生成什么

```text
AGENTS.md                          # Codex / AGENTS.md-aware tools 入口
CLAUDE.md                          # Claude Code 入口，与 AGENTS.md 同步
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

- **workflow kernel**：按清单原地替换普通开发与 Team Loop 内核，移除精确列出的退役文件及其旧 `.new` 副本。
- mixed files：`AGENTS.md`、`CLAUDE.md`、`docs/README.md` 只替换 `codex-teammode:managed` block。
- target facts：`docs/product/*`、`docs/architecture/*`、`docs/handoff/*`、`docs/plans/*`、`docs/evidence/*` 永不自动覆盖。

升级后目标项目应写入 `docs/workflow/.codex-teammode-version`，用于记录版本和已安装文件 hash，作为后续升级基线和报告依据；workflow kernel 仍按新版原地替换。

## 重要边界

安装包提供**工作流规则和文档骨架**，项目事实以目标项目为来源。当前代码是实现事实的首要证据；业务意图、部署、人工验收和法务状态各有相应依据。

## Docs Review Skill

[`$docs-review`](./skills/docs-review/SKILL.md) 是项目 Wiki 的定期清理 skill，可通过安装器的 `--install-docs-review` 选项安装。日常 `docs impact` 写回本轮变化；`$docs-review` 由人显式启动，集中处理多轮积累的重复、过期说法和混入当前说明的历史记录。

**Agent 整理文档。** 自动扫描并对照代码、合同和已有证据，提出合并重复说明、替换过期结论、归档已验收计划的方案。每项长期事实归到一份主文档，其他位置留简短链接；有用的历史和证据按时间或版本保留。

**人确认边界和关键事实。** 人确定清理范围和可改的文档，裁决需要人工确认的业务意图和历史验收。Agent 把结论锚定到相应证据或人工确认的具体范围，证据待补的事项保留为待核实。

建议在每月复盘或里程碑收口时运行：

1. **Plan Mode**：`$docs-review` 只读检查整个 Wiki；`$docs-review scope=docs/product` 只检查指定目录及其直接依赖。Agent 给出清理方案、证据和待确认事项。
2. **Default Mode**：人批准方案后，在同一任务运行 `$docs-review apply`。Agent 核对文档基线，只修改批准的 Markdown 文档，再由独立核验者复核清理结果。

完整协议见 [`SKILL.md`](./skills/docs-review/SKILL.md)，各类事实的依据见[事实模型](./skills/docs-review/references/fact-model.md)。

## 当前状态

当前发布版本为 [v0.5.0](https://github.com/gdl1605/codex-teammode-workflow/releases/tag/v0.5.0)，变更见 [CHANGELOG.md](./CHANGELOG.md)。核心内核中文优先，支持 Codex 和 Claude Code。

## 贡献

欢迎贡献工作流表达、Codex / Claude Code 使用反馈、英文翻译、安装脚本改进，以及泛化、脱敏、可复用的示例模板。见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

路线图见 [`ROADMAP.md`](./ROADMAP.md)，支持渠道见 [`SUPPORT.md`](./SUPPORT.md)。

## License

[MIT](./LICENSE).
