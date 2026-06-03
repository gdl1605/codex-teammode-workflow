# docs 索引

<!-- codex-teammode:managed:start scope=docs-index version=0.1.0 -->

> 最后更新时间：2026-06-03
> 适用范围：整个 `docs/` 目录的阅读入口与分工说明
> 本文主职责：告诉新线程先看什么、每份文档写什么、哪些内容只能去别处找
> 推荐下一跳：`handoff/latest.md`

## 先读顺序

下列顺序只适用于确需建立项目级背景的轮次；普通工作流默认先看 current code，再按任务需要补读对应 docs，不要求每轮全量读取。

1. `handoff/latest.md`
2. `product/current-state.md`
3. `architecture/ia-and-navigation.md`
4. `architecture/domain-boundaries.md`
5. `architecture/system-map.md`
6. `workflow/collaboration.md`
7. `workflow/prompt-template.md`
8. `workflow/team-loop.md`，仅在进入 Team Loop 模式时再看；派 subagent 时默认只附带 `workflow/team-loop-core.md` 和对应 `workflow/team-loop-roles/<role>.md`
9. `planner/planner-system.md`、`planner/planner-input-template.md`、`planner/planner-output-schema.md`，仅在需要普通工作流 plan-only / prompt framing / review framing 时再看；Team Loop subagent 不默认读取
10. `workflow/update-policy.md`，仅在升级已安装旧工作流时再看
11. `workflow/docs-maintenance.md`
12. `product/active-directions.md`
13. `plans/tech-debt.md`
14. `plans/active/` 和 `plans/completed/`，仅在当前轮次已经进入计划管理时再看
15. `handoff/archive/`，仅在需要追溯历史快照时再看

## 任务先看什么

- 只想快速建立上下文：先看 `handoff/latest.md`，再看 `product/current-state.md`
- 要确认顶层 IA 或底栏：先看 `architecture/ia-and-navigation.md`
- 要确认跨域边界和合同：先看 `architecture/domain-boundaries.md`
- 要确认目录、服务、后端映射：先看 `architecture/system-map.md`
- 要发起执行轮：先看 `workflow/collaboration.md` 和 `workflow/prompt-template.md`
- 默认执行普通工作流：先看 current code，按需补读 docs，最小实现，做 docs impact check，再收口验证或人工验收清单
- 要发起 `@team-loop` / Leader 调度多个 subagent 的类 team-mode 闭环：只有用户明确声明 Team Loop 时才看 `workflow/team-loop.md`；派生 subagent 时默认只附带 `workflow/team-loop-core.md`、对应 `workflow/team-loop-roles/<role>.md` 和本轮必要 docs / code / evidence
- 要做 plan-only / 执行 prompt framing / review framing：先看 `workflow/collaboration.md`、`workflow/prompt-template.md`，再按需看 `planner/planner-system.md`、`planner/planner-input-template.md`、`planner/planner-output-schema.md`；输出必须声明 schema、阶段控制面板和仓库状态分层
- 根因未锁、需要“只读审计 -> evidence -> 回流执行 prompt”：先看根目录 `workflow/audit-first.md`
- 要升级已安装的旧工作流：先看包内 `UPDATE_MANIFEST.md`、`UPDATE_PROMPT.md` 和 `workflow/update-policy.md`，按 ownership 策略更新，不覆盖目标项目事实
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
  - 只写长期协作规范、普通工作流轻闭环、审计顺序、证据优先、根因锁定规则
  - 不写当前产品状态
- `workflow/docs-maintenance.md`
  - 只写 docs-only、更新节奏、刷新时机、目录职责
  - 不写产品事实正文
- `workflow/prompt-template.md`
  - 只写固定 prompt 结构、输出结构、验收清单要求
  - 不写产品合同
- `workflow/team-loop.md`
  - 只写显式触发的 Team Loop 可选增强流程、Leader 调度规则、planner / scout 复用、generator / evaluator fresh-only、model policy、plan-gated / auto-execute、scout request、Evidence Pack 和 Evaluation Bundle
  - 不写产品事实，不替代普通执行轮
- `workflow/team-loop-core.md`
  - 只写 Team Loop subagent 默认 slim Context Bootstrap 需要的核心合同
  - 不写完整角色细节，不替代 `workflow/team-loop.md` 的完整规范
- `workflow/team-loop-roles/`
  - 放 Team Loop 的轻量角色胶囊：leader / planner / generator / scout / evaluator
  - 派生 subagent 时只附带当前角色对应文件，不要求每个 subagent 读取所有角色规则
  - 不放普通工作流 planning schema，不替代 `planner/`
- `workflow/update-policy.md`
  - 放旧工作流升级到新版工作流时的覆盖 / 合并 / 永不覆盖策略
  - 不放产品事实，不替代 `UPDATE_MANIFEST.md`
- `planner/`
  - 放普通工作流 planning / prompt-framing / review-framing 的参考规范、输入模板和输出 schema
  - 固定承载 schema 接入、GUI 约束、阶段控制面板和仓库状态分层要求
  - 不负责正式 subagent 调度；Team Loop subagent 不默认读取 `planner/*`
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
  - `team-loop-core.md`
  - `team-loop-roles/`
  - `update-policy.md`
- `planner/`
- `plans/`
- `handoff/`

<!-- codex-teammode:managed:end -->
