# docs 维护规则

> 最后更新时间：2026-08-04
> 适用范围：docs-only 轮、docs impact check、更新时间、刷新节奏、目录职责
> 本文主职责：只写 docs 如何维护
> 推荐下一跳：`workflow/collaboration.md`

## docs-only 轮默认规则

- 不改业务源码目录（如 `src/**`）
- 不改后端 / 数据层资产目录（如 `supabase/**`、`db/**`、`migrations/**` 等，按本仓库实际目录裁剪）
- 不改 `README.md`
- 不执行 build，除非用户明确要求
- 重点只做旧结论替换、已验收状态写回、协作规范沉淀

## 刷新节奏

- 日常小轮次默认不全量更新主 docs
- 阶段切换、主线切换、收官阶段再做集中刷新
- docs 应服务后续协作与记忆留存，不做流水账

## docs impact check

- 每轮结束前，先判断本轮是否改变了项目事实、合同 / 边界、已成立能力、候选方向、计划状态或长期债务。
- 有变化就更新对应 docs 主落点；没有变化也要在输出里明确写“本轮无需更新 docs”及原因。
- docs impact check 只判断“要不要更新”和“该更新哪份”，不要求每轮全量刷新 docs。
- docs impact check 是每轮增量维护的**微循环**；它不负责跨文档整体对账，也不得自动触发 `$docs-review`。
- 每轮 docs impact 输出应附带：

  ```yaml
  reconciliation_recommended: yes | no
  reason: <是否出现重复、矛盾、状态混写、证据断链或长期未整体校正的简短原因>
  ```

- `reconciliation_recommended: yes` 只向人类建议另开宏循环，不授权当前 agent 扩大读取范围或调用 skill。

## `$docs-review` 事实校正宏循环

- `$docs-review` 是可选、人工显式触发的跨文档事实对账；普通 docs 修改、docs-only 轮和 docs impact 不自动进入它。
- Codex 中优先在 Plan Mode 运行 `$docs-review`：只读 current code / schema / tests / 已有 evidence 与 docs，抽取冲突并请人类裁决业务意图、历史验收和无法证明的外部状态。
- 用户批准 decision-complete 计划后，另在 Default Mode 调用 `$docs-review apply`；apply 只改批准列表中的 docs，并先检查 baseline hash 是否漂移。
- 没有外部证据时，部署、运行态、人工验收、法务验收和发布状态只能写成未核验，不能从“代码已实现”推导。
- `$docs-review` 的清理原则是替换旧事实、确立单一主落点、去重和迁移失效状态，不是在旧结论后追加一段纠正文。
- v2 的 Plan Mode 必须先通过结构化事实处置 gate：每条 scanner finding 绑定 source fingerprint、resolution group、精确人工权限、证据、目标语义和批准文件；自然语言语义由独立审计判断，Claim ID / audit ID / validator 专用锚点不能污染业务 docs。
- apply 后先按 120,000 bytes / 2,000 lines 预算拆分 full-read 文件，最多并发三个 fresh shard auditor；完整 raw JSON 不能由主 Agent 摘要或补字段。任一 shard deficiency 立即进入人类确认门，不得同轮自行修复。
- 全部 shard pass 后仍须由全新的 synthesis auditor 读取经过验证的 shard 报告、canonical docs、跨分片 consumer 和原始 evidence；shard 报告只证明覆盖，不是业务事实权限。修正轮可按 hash 复用完全未变化的 pass shard，但 synthesis 永不复用。
- skill 可随 workflow package 版本化，但个人 skill 目录只能通过安装器的 `--install-docs-review` 显式安装或更新。

## 按变化类型更新哪份 docs

- 改了系统结构、IA、领域边界、权限、生效层、服务映射：更新 `architecture/*` 对应主落点。
- 改了当前阶段事实、当前已成立能力、已修复且不应再误判的事项：更新 `product/current-state.md`。
- 产生新的候选方向、明确后置方向或 backlog：更新 `product/active-directions.md`。
- 真正进入多轮执行任务：建或更新 `plans/active/`。
- 已完成并验收的计划：迁到 `plans/completed/`。
- 暂不单开计划、但需要长期跟踪的技术债 / 结构债 / 体验债 / 流程债：更新 `plans/tech-debt.md`。
- 阶段切换、里程碑收口、大交接：更新 `handoff/latest.md`，并按需归档旧快照到 `handoff/archive/`。
- 纯内部重构或局部修补，如果没有改变上述内容：可以不更新 docs，但必须显式说明原因。

## 更新频率与粒度

- 不是每个小改动都要全量刷新 docs。
- 只更新被本轮语义真正影响的主落点。
- 默认不跨多个 docs 重复写同一事实；其他位置只保留短摘要或不写。
- 阶段切换时，再集中刷新 `product/current-state.md`、`handoff/latest.md` 和相关归档。

## 顶部元信息

所有新主文档尽量保留下面四项：

- 最后更新时间
- 适用范围
- 本文主职责
- 推荐下一跳阅读文档

## 目录职责

- `architecture/`
  - 系统图、IA、边界
- `product/`
  - 当前状态、当前方向
- `workflow/`
  - 协作规则、docs 维护、prompt 模板
- `plans/`
  - 当前计划、已完成计划、技术债
- `handoff/`
  - 新线程短导读、历史归档

## 去重规则

- 一条事实只保留一个主落点
- 其他文档只写短摘要并链接到主落点
- 不把同一事实在多个文件里写成长段正文
- 已修复问题不要重新写成 blocker
