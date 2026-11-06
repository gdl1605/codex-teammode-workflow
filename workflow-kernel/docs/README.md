# docs 索引

<!-- codex-teammode:managed:start scope=docs-index version=0.5.0 -->

> 最后更新时间：2026-11-06
> 适用范围：整个 `docs/` 目录的阅读入口与分工说明
> 本文主职责：告诉新线程先看什么、每份文档写什么、哪些内容只能去别处找
> 推荐下一跳：`handoff/latest.md`

## 先读顺序

本索引是项目资料地图，按任务读取，不要求全量读取。正常运行、恢复、排障及业务操作计划 / 报告产出沿项目原流程，不触发本包开发工作流。只有用户本轮明确要求机制变更或其工程方案，才适用普通开发的澄清和独立核验；Team Loop 还须用户本轮明确指定。

1. `handoff/latest.md`
2. `product/current-state.md`
3. `architecture/ia-and-navigation.md`
4. `architecture/domain-boundaries.md`
5. `architecture/system-map.md`
6. `workflow/default-workflow.md`，普通开发时按需看；派独立 evaluator 时附带 `workflow/independent-evaluator.md` 和本次 Review Request
7. `workflow/team-loop.md`，仅在进入 Team Loop 模式时再看；派 subagent 时默认附带 `workflow/team-loop-core.md` 和对应 `workflow/team-loop-roles/<role>.md`，evaluator 另附共用核验原则 `workflow/independent-evaluator.md`
8. `workflow/update-policy.md`，仅在升级已安装旧工作流时再看
9. `workflow/docs-maintenance.md`
10. `product/active-directions.md`
11. `plans/tech-debt.md`
12. `plans/active/` 和 `plans/completed/`，仅在当前轮次已经进入计划管理时再看
13. `handoff/archive/`，仅在需要追溯历史快照时再看

## 任务先看什么

- 要正常执行业务、恢复、排障或产出业务计划 / 报告：沿项目业务入口和既有运行合同，不派开发 planner / evaluator；故障或 agent 自拟修复计划不能把任务升级成机制变更
- 只想快速建立上下文：先看 `handoff/latest.md`，再看 `product/current-state.md`
- 要确认顶层 IA 或底栏：先看 `architecture/ia-and-navigation.md`
- 要确认跨域边界和合同：先看 `architecture/domain-boundaries.md`
- 要改接口、状态或职责：沿项目现有规范索引（或领域边界文档）找到正式合同，再核对可执行定义、实际生产者 / 消费者和该范围的正式校验入口；规格及写回规则见 [文档维护](workflow/docs-maintenance.md#已确认规格接口合同与校验入口)
- 要确认目录、服务、后端映射：先看 `architecture/system-map.md`
- 用户明确要求机制变更或规划该变更：看 `workflow/default-workflow.md`；工程计划的未决关键取舍才 Grill-me，工程规划和实现分别核验；派发依据须回到用户原话，不用 agent 自拟计划触发
- 用户本轮明确要求机制变更或其工程方案，并指定 `@team-loop` / Leader 调度时才看 `workflow/team-loop.md`；派生 subagent 时附带 core、对应 role 和本轮必要原话 / docs / code / evidence，evaluator 另附共用核验原则。规划与实现分别核验，只回 Leader；仅规划交付后结束，不要求实现结果
- Team Loop 涉及规格或接口变更时，Leader 按 [文档维护](workflow/docs-maintenance.md#已确认规格接口合同与校验入口) 在现有 `Evaluation Bundle` 中引用适用的已确认规格、正式合同和实际验证证据
- 两种工作流的规划 / 实现核验均区分首次 / 复审：首次检查本次承诺，复审只核对原问题、修复及直接影响，未变且已通过的部分不重开，达到原要求就收口；具体边界见 `workflow/independent-evaluator.md`
- Team Loop 中根因未锁、需要“只读审计 -> evidence -> Evidence Pack”：先看根目录 `workflow/audit-first.md`
- 要升级已安装的旧工作流：先看包内 `UPDATE_MANIFEST.md`、`UPDATE_PROMPT.md` 和 `workflow/update-policy.md`，按 ownership 策略更新，不覆盖目标项目事实
- 要整理 docs 维护：先看 `workflow/docs-maintenance.md`
- 要做跨文档整体事实校正：只有用户显式触发 `$docs-review` 时，先看 `workflow/docs-maintenance.md`，再由已安装的可选 skill 在 Plan Mode 只读核验；v3 使用 scanner schema 5 / plan schema 3、封闭 audit scope、结构化 edit contracts、分片独立审计和全新 synthesis 终审，docs impact 不自动进入该流程
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
- `workflow/docs-maintenance.md`
  - 只写普通开发与 Team Loop 的文档归属、规格 / 接口合同 / 校验的衔接、更新节奏，以及 docs impact 微循环 / `$docs-review` 宏循环的分工
  - 不写产品事实正文
- `workflow/default-workflow.md`
  - 普通开发的需求追问、轻量规划核验、主 agent 实现、实现核验、Review Request 与缺口 / 争议回流；不要求 Team Loop 或新建 schema
- `workflow/independent-evaluator.md`
  - 普通工作流与 Team Loop 共用的 fresh 只读核验原则、首次 / 复审边界和收口条件，分别对照原要求与计划 / 实际行为及声明，不以计划与实现互相自证；调度和回报对象沿各自工作流
- `workflow/team-loop.md`
  - 只写 prompt 显式触发的 Team Loop 流程、Leader 调度规则、planner / scout 复用、generator / evaluator fresh-only、model policy、plan-gated / auto-execute、scout request、Evidence Pack 和 Evaluation Bundle
- `workflow/team-loop-core.md`
  - 只写 Team Loop subagent 默认 slim Context Bootstrap 需要的核心合同
  - 不写完整角色细节，不替代 `workflow/team-loop.md` 的完整规范
- `workflow/team-loop-roles/`
  - 放 Team Loop 的轻量角色胶囊：leader / planner / generator / scout / evaluator
  - 派生 subagent 时只附带当前角色对应文件，不要求每个 subagent 读取所有角色规则
- `workflow/update-policy.md`
  - 放旧工作流升级到新版工作流时的覆盖 / 合并 / 永不覆盖策略
  - 不放产品事实，不替代 `UPDATE_MANIFEST.md`
- `../workflow/audit-first.md`
  - 放 Team Loop 条件使用的“只读审计 -> evidence -> Evidence Pack”机制
  - 根因未锁时要求 evidence 沉淀到 `docs/evidence/<feature>-audit.md` 后再回流执行 prompt
- `plans/active/`
  - 放当前还在跑的计划工件；跨会话交接且无既有规格惯例时，在同一计划记录「已确认规格」，引用正式合同和适用校验
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
- 上述顺序用于当前实现事实；显式 `$docs-review` 必须按 claim 类型分流，业务意图、部署、人工验收和法务事实不能从代码存在直接推导

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
  - `default-workflow.md`
  - `independent-evaluator.md`
  - `team-loop.md`
  - `team-loop-core.md`
  - `team-loop-roles/`
  - `update-policy.md`
- `plans/`
- `handoff/`

<!-- codex-teammode:managed:end -->
