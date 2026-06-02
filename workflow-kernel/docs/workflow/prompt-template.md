# Prompt 模板

> 最后更新时间：2026-06-02
> 适用范围：执行轮、方案轮、交接轮的固定输入和输出结构
> 本文主职责：把 prompt 和输出的骨架固定下来
> 推荐下一跳：`workflow/collaboration.md`

## 普通工作流输出顺序

普通工作流是默认路径，不拆成独立 planner / generator / evaluator。需要先给用户输出执行 prompt 时，固定按下面顺序组织：

1. 问题
2. 修改思路
3. 为什么这样改
4. prompt

约束：

- 不要一上来先给 prompt，再把问题和理由补在后面。
- `问题` 只写当前要解决的真实对象和现象，不提前写死根因。
- `修改思路` 先写收口方向，再落到最小修改边界。
- `为什么这样改` 要解释为什么这是当前代码下更稳的路线，而不是抽象上的理想方案。

## 固定执行 prompt 结构

后续给 Codex / Claude Code 等目标 coding agent 的执行 prompt 固定为 7 段：

1. 当前已知事实
2. 本轮目标
3. 修改边界
4. 合同层
5. 建议实现层
6. 输出要求
7. 验收标准

其中：

- `合同层`
  - 只写当前已成立的产品合同、数据约束、状态机约束、权限边界、owner 语义和不可回归项。
  - 这里应尽量只放已验证事实，不放猜测性实现路径。
- `建议实现层`
  - 只写推荐切入点、推荐 slice、推荐文件范围、推荐修法顺序。
  - 这一层不是已验证事实，也不是唯一实现答案。
  - 执行者必须以 current code 审计结果为准，对建议实现层做最小调整。
  - 如果 current code 与建议实现层冲突，以 current code 为准，并在输出中明确说明。

## 固定输出结构

默认输出结构保持为：

1. 改动文件列表
2. 每个文件改了什么
3. 实现说明
4. 风险 / 阻塞说明
5. build 结果
6. 手工复测步骤
7. docs impact check

`docs impact check` 默认写清：

- 本轮是否需要更新 docs
- 更新了哪些 docs
- 为什么更新这些
- 或为什么本轮无需更新 docs

普通工作流中，docs 按需读取；不要为了启动一轮执行而重复读取全量 docs。只有当本轮涉及产品合同、状态机、权限、数据库 schema / 服务端函数、多版本资源链路、shared 设计合同、计划状态或 docs 与代码冲突时，才按 `docs/README.md` 补读专题 docs。

## Team Loop 启动模板

当用户明确声明使用 `@team-loop`、`Team Loop`、`teamloop`，或明确要求 Leader 调度 subagent 形成类 team-mode 闭环时，使用 `workflow/team-loop.md` 的触发模板。

Team Loop 不是普通执行轮的默认要求；未明确声明时，始终按 `workflow/collaboration.md` 的普通工作流推进，不因任务复杂度自动升级。

Team Loop 中的 `planner` 是 Leader 调度的只读 subagent，不代表旧独立 planner 模式。

不要在本文重复维护 Team Loop 的完整启动模板、Scout Request、Evidence Pack 或 Evaluation Bundle。对应主落点是：

- `workflow/team-loop-core.md`：subagent 默认 slim Context Bootstrap 的核心合同。
- `workflow/team-loop.md`：完整模式选择、通信规则、Context Bootstrap、触发模板、Evidence Pack、Evaluation Bundle 和返工规则。
- `workflow/team-loop-roles/leader.md`：Leader 的轻量角色合同和最终收口输出。
- `workflow/team-loop-roles/planner.md`：planner 的只读合同、fresh handoff 和 delta output。
- `workflow/team-loop-roles/generator.md`：generator 的写代码合同、Scout Request 和 Generator Result。
- `workflow/team-loop-roles/scout.md`：scout 的只读 evidence 输出。
- `workflow/team-loop-roles/evaluator.md`：evaluator 的独立核验输出。

Context Bootstrap 默认使用 `slim`：当前工具入口 `AGENTS.md` 或 `CLAUDE.md` 二选一、`docs/README.md`、`team-loop-core.md`、当前角色的 role capsule、本轮 task docs / code / evidence。`team-loop.md` 完整规范只在需要核对完整规则时加入；`workflow/audit-first.md` 只在根因未锁、高风险或审计回流时加入；Team Loop subagent 不默认读取 `docs/planner/*`。

## docs-only 轮的输出

- docs-only 轮不写 build 结果
- 仍然要说明改了哪些文件、为什么改、还缺什么
- 仍然要带 `docs impact check`
- 不要打印完整文件全文，除非用户明确要求

## 与 collaboration 对齐

- prompt 结构应与 [`workflow/collaboration.md`](collaboration.md) 的协作闭环保持一致。
- 普通执行轮不默认包含独立 evaluator；只有用户明确要求 review / evaluator 或进入 Team Loop 时，prompt 里的输出要求才需要预留 Evaluation Bundle / evaluator 结果。
- 执行轮开头的上下文、git 和环境检查，继续按 [`workflow/session-startup.md`](session-startup.md) 执行。

## 人工验收清单

只要是执行轮，输出里默认要带人工验收清单，且至少写到下面粒度：

- 进入哪个页面
- 使用哪个账号或哪类测试数据
- 点击什么、输入什么
- 预期看到什么

如果某个场景当前无法直接验收，必须写明原因和替代方式。
