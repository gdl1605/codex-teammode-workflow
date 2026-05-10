# Audit First Workflow

> 最后更新时间：2026-05-02
> 适用范围：普通工作流 / Team Loop 中根因未锁、实现层不确定、需要审计回流的轮次
> 本文主职责：定义“只读审计 -> evidence -> 回流执行 prompt / generator 指令”的高风险前置闸门
> 推荐下一跳：`../docs/workflow/collaboration.md`

## 什么时候必须先审计

以下情况在普通工作流或 Team Loop 中必须先走只读审计，不应直接写执行 prompt 或派 generator 试修：

- 根因未锁。
- 建议实现层不确定。
- 当前看到的是现象，不是原因。
- 对 current code 的真实状态不确定。
- docs、handoff、用户描述之间存在冲突。
- 多个页面 / 模块可能共享同一个根因。
- 执行轮可能触及业务状态机 / 权限 / 行级授权 / 复杂资源链路 / 高风险产品域（具体列表由目标仓库维护）。

## 审计轮产物

审计轮默认只读，产物包括：

- 只读审计 prompt。
- 审计结论摘要。
- evidence 文档。
- 必要时的 `HUMAN_CHECK_REQUIRED` 人工检查项。

只读审计 prompt 的目标是锁定事实和根因，而不是让 generator 先试修。它至少要回答：

- current code 真实状态是什么。
- docs / handoff / 用户描述之间是否存在冲突。
- 根因是否已经足以支持执行 prompt。
- 仍缺哪些证据，哪些需要人工验收。
- 下一轮允许进入执行，还是必须继续审计。

审计轮不应：

- 改代码。
- 改业务 docs 的事实口径，除非本轮本身是 docs-only 审计收口。
- 截图或 GUI hunting，除非用户明确要求且本轮允许。
- 把推断写成已证实事实。

## Evidence 沉淀位置

只读审计结果沉淀到：

```text
docs/evidence/<feature>-audit.md
```

命名建议：

- `<feature>` 使用本轮主题的短横线命名。
- 如果已有 evidence 包，也可以在对应 evidence 目录下新增 audit README 或追加审计结论。
- evidence 文档应写清读取文件、可证实事实、推断、缺失证据、下一步建议。

最低内容建议：

- `Startup / Read Scope`：本轮读过的 docs、code、evidence。
- `Repository State Layers`：历史脏项 / 在途开发面、本轮真实候选范围、不可混入项。
- `Verified Facts`：由 current code 或 docs 直接证实的事实。
- `Inferences`：基于事实的推断，不能写成已证实。
- `Unknowns / HUMAN_CHECK_REQUIRED`：只读无法确认的内容。
- `Execution Preconditions`：进入执行 prompt 前必须满足的条件。

## 审计后的回流动作

审计完成后：

1. 普通工作流的 planning phase 或 Team Loop 的 Leader 读取 `docs/evidence/<feature>-audit.md`。
2. planning phase / Leader 把 evidence 中的事实、推断、缺口分开。
3. 普通工作流中，planning phase 明确当前采用 `planner-output-schema.md` 中的 `plan / execute / review` 哪一种 schema。
4. 普通工作流中，planning phase 再产出执行 prompt，或判断还不能进入执行。
5. Team Loop 中，Leader 必须把 evidence 裁剪为 Evidence Pack 后再派 generator，不把原始 scout / audit 输出直接转交 generator。
6. Team Loop 中，Leader 派 planner / scout 做只读审计时，必须把下方“最小审计 prompt 骨架”的 `必读` 转换为 `Context Bootstrap`。
7. Team Loop 中，Leader 派 generator 时，必须把 evidence 裁剪为 Evidence Pack，并同时附带 required read scope。
8. 执行 prompt 或 Leader 给 generator 的正式指令必须引用 evidence，并要求 generator 启动前重新审计 current code、输出 `Read Scope Ack`。

不允许：

- 跳过 evidence，凭记忆或想象设计实现。
- 把审计 prompt 直接当执行 prompt。
- 在根因未锁时让 generator “先试着修一下”。
- 只写背景总结，不说明 evidence 如何回流到下一轮执行。

## GUI / computer-use 约束

- audit-first 默认不使用 computer-use / GUI。
- 审计轮禁止截图和 GUI 试跑，除非用户明确允许且该动作是极简单只读确认。
- 复杂运行态验证、视觉强弱判断、状态命中验证，应写入 `HUMAN_CHECK_REQUIRED` 或交给后续执行轮，不作为 planning phase / Leader 自证任务。

## 与普通工作流文档的关系

- `../docs/workflow/collaboration.md`：普通工作流主入口，说明 plan-only / read-only audit / execute / review 的关系。
- `../docs/workflow/team-loop.md`：Team Loop 的 Leader / planner subagent / generator / scout / evaluator 调度规则。
- `../docs/planner/planner-input-template.md`：普通工作流 plan-only / read-only audit / review 输入模板。
- `../docs/planner/planner-output-schema.md`：普通工作流 plan / execute / review 输出结构。
- `../AGENTS.md` 或 `../CLAUDE.md`：声明普通工作流、Team Loop 与 legacy `@planner` alias。

对应关系：

- 只读审计 prompt 本身通常按 `plan` schema 输出。
- 审计 evidence 足够后，普通工作流的 planning phase 再按 `execute` schema 产出执行 prompt。
- Team Loop 中，Leader 基于 evidence 形成 Evidence Pack，再派 generator。
- 若用户要求独立复核 evidence 或 generator 输出，则按 `review` schema 输出。
- 每次输出都必须显式声明采用哪一种 schema，不允许只说原则不给结构。

## 最小审计 prompt 骨架

```md
# 只读审计 Prompt

## 目标
- 本轮只读审计目标：
- 本轮采用 schema：plan / review

## 必读
- AGENTS.md 或 CLAUDE.md
- docs/README.md
- docs/handoff/latest.md
- 相关 docs：
- 相关代码：

## 禁止
- 不改代码
- 不改 docs
- 不截图 / 不 GUI，除非本轮明确允许

## 必须回答
- current code 真实状态是什么
- 根因是否已锁
- 哪些是事实，哪些是推断
- 当前阶段控制面板是什么
- 历史脏项 / 本轮候选范围如何分层
- 需要沉淀到哪个 evidence 文件
- 下一轮是否可以进入执行 prompt

## 输出
- Read Scope Ack
- files_read
- verified_facts with citations
- 审计结论摘要
- evidence 写入建议
- 执行 prompt 前置条件
- subagent 决策
- GUI / computer-use 是否使用，默认 0
```
