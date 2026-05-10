# docs 索引

> 最后更新时间：2026-04-30
> 适用范围：整个 `docs/` 目录的阅读入口与分工说明
> 本文主职责：告诉新线程先看什么、每份文档写什么、哪些内容只能去别处找
> 推荐下一跳：`handoff/latest.md`

## 先读顺序

1. `handoff/latest.md`
2. `product/current-state.md`
3. `architecture/ia-and-navigation.md`
4. `architecture/domain-boundaries.md`
5. `architecture/system-map.md`
6. `workflow/collaboration.md`
7. `workflow/prompt-template.md`
8. `workflow/team-loop.md`，仅在进入 Team Loop 模式时再看
9. `planner/planner-system.md`、`planner/planner-input-template.md`、`planner/planner-output-schema.md`，仅在需要 plan-only / prompt framing / review framing 时再看
10. `workflow/docs-maintenance.md`
11. `product/active-directions.md`
12. `plans/tech-debt.md`
13. `plans/active/` 和 `plans/completed/`，仅在当前轮次已经进入计划管理时再看
14. `handoff/archive/`，仅在需要追溯历史快照时再看

## 任务先看什么

- 只想快速建立上下文：先看 `handoff/latest.md`，再看 `product/current-state.md`
- 要确认顶层 IA 或底栏：先看 `architecture/ia-and-navigation.md`
- 要确认跨域边界和合同：先看 `architecture/domain-boundaries.md`
- 要确认目录、服务、后端映射：先看 `architecture/system-map.md`
- 要发起执行轮：先看 `workflow/collaboration.md` 和 `workflow/prompt-template.md`
- 要发起 `@team-loop` / Leader 调度多个 subagent 的类 team-mode 闭环：先看 `workflow/team-loop.md`，再看 `workflow/prompt-template.md`
- 要做 plan-only / 执行 prompt framing / review framing：先看 `workflow/collaboration.md`、`workflow/prompt-template.md`，再按需看 `planner/planner-system.md`、`planner/planner-input-template.md`、`planner/planner-output-schema.md`；输出必须声明 schema、subagent 决策、阶段控制面板和仓库状态分层
- 根因未锁、需要“只读审计 -> evidence -> 回流执行 prompt”：先看根目录 `workflow/audit-first.md`
- 要整理 docs 维护：先看 `workflow/docs-maintenance.md`
- 要看当前候选方向或后置项：先看 `product/active-directions.md`
- 要看跨轮次技术债：先看 `plans/tech-debt.md`
- 要管理当前计划或结束后的计划工件：先看 `plans/active/` 和 `plans/completed/`
- 要追溯历史 handoff：先看 `handoff/archive/`

## 文件职责

- `architecture/system-map.md`
  - 只写系统地图、目录结构、页面 service 后端映射、hosted 依赖、核心对象关系
  - 不写当前优先级，不写候选方向，不写长篇复盘
- `architecture/ia-and-navigation.md`
  - 只写顶层 IA、底栏、角色专用后台、chrome 和真实生效层
  - 不写系统地图，不写路线图
- `architecture/domain-boundaries.md`
  - 只写最容易误判的跨域边界和合同
  - 不写系统目录，不写任务清单
- `product/current-state.md`
  - 只写当前阶段、已验收主链路、仍成立的合同、不要再误判的事实
  - 不写长篇过程复盘，不写候选方向
- `product/active-directions.md`
  - 只写当前候选方向、明确后置方向、backlog
  - 不写已解决历史，不重复 current-state
- `workflow/collaboration.md`
  - 只写长期协作规范、审计顺序、证据优先、根因锁定规则
  - 不写当前产品状态
- `workflow/docs-maintenance.md`
  - 只写 docs-only、更新节奏、刷新时机、目录职责
  - 不写产品事实正文
- `workflow/prompt-template.md`
  - 只写固定 prompt 结构、输出结构、验收清单要求
  - 不写产品合同
- `workflow/team-loop.md`
  - 只写 Team Loop 可选增强流程、Leader 调度规则、plan-gated / auto-execute、scout request、Evidence Pack 和 Evaluation Bundle
  - 不写产品事实，不替代普通执行轮
- `planner/`
  - 放普通工作流 planning / prompt-framing / review-framing 的参考规范、输入模板和输出 schema
  - 固定承载 subagent 决策、schema 接入、GUI 约束、阶段控制面板和仓库状态分层要求
  - 不放业务事实，不替代 `workflow/collaboration.md`
- `../workflow/audit-first.md`
  - 放仓库级“只读审计 -> evidence -> 回流执行 prompt”机制
  - 根因未锁时要求 evidence 沉淀到 `docs/evidence/<feature>-audit.md` 后再回流执行 prompt
  - 不替代 `docs/workflow/` 的长期协作规范
- `plans/active/`
  - 放当前还在跑的计划工件
- `plans/completed/`
  - 放已经收口的计划工件
- `plans/tech-debt.md`
  - 放跨轮次、跨主题的技术债或结构债跟踪
- `handoff/latest.md`
  - 放新线程的短导读，不复制整份状态正文
- `handoff/archive/`
  - 放历史 handoff 快照，只保留归档，不回写当前正文

## 事实判断优先级

1. `current code`
2. 对应专题 docs
3. `handoff/latest.md`
4. `handoff/archive/`

说明：

- handoff 和摘要是加速入口，不是最高事实源
- 归档只用于追溯，不凌驾于当前代码
- 如果 docs 和代码冲突，后续必须以 current code 再核实

## 本轮推进目标来源

- 由当前用户目标决定
- 只决定本轮应该优先修哪一组 docs，不参与事实真伪判断

## 去重原则

- 一条事实只保留一个主落点
- 其他文档如果要提，只写短摘要并链接到主落点
- 不把同一件事在多个文件里写成长段正文
- 不把已修复问题重新写成 blocker

## 目录树

- `architecture/`
- `product/`
- `workflow/`
- `planner/`
- `plans/`
- `handoff/`
