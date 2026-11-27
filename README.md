# Codex-teammode Workflow

> 中文优先 / English below.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.5.1-blue.svg)](./CHANGELOG.md)

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

**先计划，再实现。** 普通工作流完整正文直接写入 `AGENTS.md` / `CLAUDE.md`，工程方案送审和定稿前强制执行 **Grill-me**。关键取舍沿用有出处的既有决定，新增选择通过原生卡片确认；异步发卡后保持当前回合并实际 wait 到用户回答。主 agent 负责实现和验证，独立 evaluator 分别审查计划和实现，审查限于原要求及改动的直接影响。仅执行、仅规划或专项核验按用户指定的范围交付。

![普通开发：草案 → Grill-me → wait 回答 → 审查 → 实施](./assets/default-development.svg)

1. **形成草案。** 对照原要求、有效合同和当前实现，区分事实、已确认的决定和建议，按任务规模拟定方案。
2. **强制完成 Grill-me。** 事实由主 agent 查证，明确决定和委托直接沿用并注明出处。新增关键取舍用原生卡片给出选项、影响和推荐；工具受限时说明原因并用文本选项。独立的问题同轮提交，发卡后在当前回合持续实际 wait；收到实际回答后写回同一份计划，再提交依赖前置决定的问题。
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
5. **Leader 处理返工或交回用户。** 确定缺口交对应角色修正，不能仅因 P2 / P3 标签或列为 residual risk 就忽略明确违反要求的项。授权实施后核验收口停在 `human_acceptance_required`，真实阻塞报 `blocked`；仅规划注明未实施，不能因没有 Generator 结果判阻塞。最终验收由用户决定。

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

- **workflow kernel**：按清单原地替换普通开发与 Team Loop 内核，移除精确列出的退役文件及其旧 `.new` 副本。
- **mixed files**：`AGENTS.md`、`CLAUDE.md`、`docs/README.md` 只替换 `codex-teammode:managed` block，保留 block 外的目标项目规则。
- **target facts**：`docs/product/*`、`docs/architecture/*`、`docs/handoff/*`、`docs/plans/*`、`docs/evidence/*` 永不自动覆盖。

升级完成后，目标项目应写入 `docs/workflow/.codex-teammode-version`，用于记录版本和已安装文件 hash。后续升级会用这个 marker 做基线和报告，但 workflow kernel 仍按新版原地替换。

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

当前发布版本为 [v0.5.1](https://github.com/gdl1605/codex-teammode-workflow/releases/tag/v0.5.1)，变更见 [CHANGELOG.md](./CHANGELOG.md)。核心内核中文优先，README 提供中英双语入口，支持 Codex 和 Claude Code；其他工具可参考 AGENTS.md/CLAUDE.md 约定自行适配。

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

Codex-teammode Workflow provides installable collaboration rules, a bootstrap prompt, and a docs scaffold for **Codex** and **Claude Code**. The two execution modes share a project wiki.

**Default execution** follows the project's existing process for routine work. Explicit requests to change a mechanism or plan that change enter [default development](#default-development-at-a-glance). [Team Loop](#team-loop-at-a-glance) is an explicit choice to have a Leader coordinate the agent team.

The agent creates or merges the `docs/` **project wiki** during installation, with `docs/README.md` as its index. It [updates the affected docs](./workflow-kernel/docs/workflow/docs-maintenance.md) after development work. [`$docs-review`](#docs-review-at-a-glance) periodically clears accumulated duplicates and stale material.

### Default Development At A Glance

**Planning comes before implementation.** Open choices about implementation details or how much to deliver require **Grill-me** before plan delivery when they affect behavior, scope, cost, or acceptance. The main agent plans, implements, and verifies the change. Separate independent evaluators review the plan and the implementation against the original requirements and direct effects. Execution-only, plan-only, and standalone review requests follow the user's requested scope.

1. **Draft the plan.** Read the original request, governing contracts, and current implementation. Separate facts, confirmed decisions, and proposals. Match the plan's detail to the task.
2. **Clarify with Grill-me.** Investigate facts and use existing decisions or explicit delegation. Present open choices that need a user decision in native question cards, with options, consequences, and a recommendation. Explain any tool restriction before falling back to text choices. Ask independent questions together, wait for actual answers before asking dependent questions, and record answers and sources in the same plan.
3. **Review the plan.** Before delivery, a fresh read-only evaluator checks the plan against the user's original requirements and corrections for omissions, changed constraints, and the basis for key decisions. The main agent corrects confirmed gaps, investigates facts, and asks the user to settle genuine ambiguities. Plan-only work ends on delivery.
4. **Implement within authorization.** Recheck the original request, corrections, and revised plan, then complete the implementation and its wiring and run directly relevant checks.
5. **Review the implementation independently.** A different fresh read-only evaluator checks the original requirements, revised plan, actual diff, affected paths, validation evidence, and completion claims for omissions, work outside scope, and extra acceptance conditions. The main agent checks findings against the original requirements and direct effects, fixes confirmed gaps within authorization, investigates missing facts, and brings genuine choices back to the user.

For example, waiting for the current request to finish before exiting and adding active cancellation are different delivery scopes. If the choice is open, use Grill-me to explain the differences in behavior and cost.

Both development workflows distinguish `review_phase: plan / implementation` from `review_kind: initial / recheck`. Key rules, test expectations, and review findings need original evidence. Rechecks cover only the original findings, fixes, and their direct effects. A new blocking finding must explain its causal link to a fix. Review independent additions within their own scope and end when the original requirements are met.

See [`default-workflow.md`](./workflow-kernel/docs/workflow/default-workflow.md) and [`independent-evaluator.md`](./workflow-kernel/docs/workflow/independent-evaluator.md).

### Team Loop At A Glance

**The Leader splits the task across an agent team and automatically coordinates planning, implementation, and internal acceptance checks.** When a check finds a gap, the Leader sends it back for rework and a focused recheck. Once every acceptance criterion assigned to the team in the plan passes, the Leader hands the result and evidence to the user for final acceptance. The team handles basic errors before handoff.

Start Team Loop when the current user explicitly requests a mechanism change or its engineering plan and selects `@team-loop`, `Team Loop`, `teamloop`, or Leader-driven delegation. The Leader coordinates handoffs and validation within the chat. The Generator implements, and each subagent reports to the Leader.

1. **Dispatch Planner first.** The read-only Planner returns the goal, allowed and forbidden scope, a proposed approach, and review focus.
2. **Review the plan before dispatch.** Leader gives a fresh Evaluator the relevant user quotes, corrections, decision sources, and plan. Definite omissions return to Planner; agents investigate factual gaps; Leader asks the user about genuine choices. Plan-only work ends on delivery. For authorized implementation, `plan-gated` waits for plan approval and `auto-execute` adds no approval step. Generator still reads the original request, revised plan, and current code.
3. **Add Scout on demand.** Generator sends a Scout Request to Leader. If approved, a read-only Scout returns evidence to Leader, who curates an Evidence Pack and hands it back to Generator.
4. **Validate and review implementation.** Leader sends original quotes and corrections, the revised plan, actual diff, read scope, results, and completion claims to another fresh Evaluator. It checks requirements against real behavior and reports only to Leader, using the shared review criteria.
5. **Route rework or hand off.** Definite gaps return to the responsible role for a cause-level repair. Leader sends a scoped `recheck` with the original findings, repair delta, and direct effects; severity alone cannot reopen unchanged work, and low severity cannot waive an in-scope requirement. End review when the original requirements are met. Authorized implementation stops at `human_acceptance_required` or a real `blocked` state. Plan-only delivery states that no implementation occurred and does not require Generator results. The user makes the acceptance decision.

Leader sends a scoped Context Bootstrap and checks each role's Read Scope Ack. Planner and Scout can be reused after checking freshness. Generator and Evaluator use fresh sessions each round.

See [`team-loop.md`](./workflow-kernel/docs/workflow/team-loop.md) for the dispatch protocol, trigger template, and rework criteria, and [`team-loop-core.md`](./workflow-kernel/docs/workflow/team-loop-core.md) for the minimal context.

### Updating An Existing Project

Copy in the newer package and paste [`UPDATE_PROMPT.md`](./UPDATE_PROMPT.md). Updates replace the workflow kernel in place, remove the exact retired files listed in the [update manifest](./UPDATE_MANIFEST.md), and preserve the target project's facts.

### Docs Review At A Glance

[`$docs-review`](./skills/docs-review/SKILL.md) is an optional skill for periodic project wiki cleanup, installed with the `--install-docs-review` option. Routine `docs impact` records changes from each task. A person starts `$docs-review` to address duplicates, stale claims, and historical material mixed into current docs.

**The agent organizes the wiki.** It scans the docs, checks code, contracts, and evidence, then proposes merging duplicates, updating stale claims, and archiving accepted plans. Each lasting fact has one owning doc, with brief links elsewhere and useful history kept with its date or version.

**A person confirms the scope and key facts.** They confirm which docs can change and settle questions of business intent or historical acceptance. The agent ties each conclusion to its evidence or the scope of the human decision, and marks open facts for verification.

A monthly review or the end of a milestone is a good time to start:

1. **Plan Mode**: `$docs-review` reviews the whole wiki read-only, and `$docs-review scope=docs/product` covers one directory and its direct dependencies. The agent presents a cleanup plan, evidence, and questions.
2. **Default Mode**: After approval, `$docs-review apply` runs in the same task, checks the baseline, and edits only approved Markdown files. An independent reviewer verifies the result.

The [skill protocol](./skills/docs-review/SKILL.md) and [fact model](./skills/docs-review/references/fact-model.md) give the full rules.
