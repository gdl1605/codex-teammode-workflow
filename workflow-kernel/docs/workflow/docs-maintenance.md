# docs 维护规则

> 最后更新时间：2026-11-05
> 适用范围：普通开发与 Team Loop 的 docs impact check 与文档修改，以及显式触发的可选 `$docs-review`
> 本文主职责：只写 docs 如何维护
> 推荐下一跳：`default-workflow.md` 或已显式启用的 `team-loop.md`

## 文档修改任务的范围

- 不改业务源码目录（如 `src/**`）
- 不改后端 / 数据层资产目录（如 `supabase/**`、`db/**`、`migrations/**` 等，按本仓库实际目录裁剪）
- 不执行 build，除非用户明确要求
- 重点只做旧结论替换、已验收状态写回、协作规范沉淀

上述范围用于文档修改任务，不把包含业务代码的开发任务改成 docs-only。本文件不定义另一套工作流：普通开发由主 agent 修改，Team Loop 中由 generator 按 allowed scope 修改文档。

## 刷新节奏

- 日常小轮次默认不全量更新主 docs
- 阶段切换、主线切换、收官阶段再做集中刷新
- docs 应服务后续协作与记忆留存，不做流水账

## docs impact check

- 普通开发收口前及 Team Loop 每轮结束前，先判断本轮是否改变了项目事实、合同 / 边界、已成立能力、候选方向、计划状态或长期债务。
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
- v3 的 Plan Mode 使用 scanner schema 5 / plan schema 3：除逐条绑定 source fingerprint、resolution group、精确人工权限、证据、目标语义和批准文件外，还必须冻结完整 `audit_scope_manifest`，并用结构化 `edit_contracts` 声明 canonical transfer、path rewrite 和 lifecycle move 的可执行后置条件；自然语言语义由独立审计判断，Claim ID / audit ID / validator 专用锚点不能污染业务 docs。
- apply 后先按 120,000 bytes / 2,000 lines 预算拆分 full-read 文件，最多并发三个 fresh shard auditor；完整 raw JSON 不能由主 Agent 摘要或补字段。任一 shard deficiency 立即进入人类确认门，不得同轮自行修复。
- 全部 shard pass 后仍须由全新的 synthesis auditor 读取经过验证的 shard 报告、canonical docs、跨分片 consumer 和原始 evidence；shard 报告只证明覆盖，不是业务事实权限。修正轮可按 hash 复用完全未变化的 pass shard，但 synthesis 永不复用。
- skill 可随 workflow package 版本化，但个人 skill 目录只能通过安装器的 `--install-docs-review` 显式安装或更新。

## 已确认规格、接口合同与校验入口

需要跨会话交接、且项目没有既有任务规格惯例时，默认在 `docs/plans/active/` 的同一份活动计划里加「已确认规格」一节。记录本次已确认的目标、可观察行为、范围、不变边界和决定依据；未决选项继续单列。有既有规格惯例时沿用项目原落点。原合同内的小修引用已有规范即可，不额外创建 Spec。

只读规划或尚无计划写入授权时，先在当前聊天草案或已有交接材料中保留该节，注明计划落点。已有写入授权时由当前工作流的写入角色回填同一份计划；Team Loop 的 Planner 仍只读，Leader 仍按原模式派 Generator，不因 Spec 落盘提前进入实施。

- **接口变更。** 在本次规格或计划里指出受影响的正式合同、可执行定义和实际生产者 / 消费者。说明本次改变的输入、输出、字段或状态语义及职责边界；拟新增的定义或消费者标为拟实施。长期术语和合同仍归项目的原有主文档，可执行规则由项目的共享代码持有。计划记差异，索引和其他文档链接主落点。
- **唯一校验。** 按合同或验证范围确定正式入口：同一协议或产物在同一检查范围内沿用一个项目认可的入口，不同范围可以沿用各自的现有入口。按本次变化选择对应的检查方式，复用原可执行定义、生产读者及必要已有测试；不复制 Schema 或另写平行的检查规则。
- **验证证据。** 计划记录拟用的入口、检查方式和能证明的范围；实施记录区分实际执行、结果及未覆盖项。没有同源检查时标明缺口，是否补齐沿已有授权与验收要求处理。结构校验只证明其声明的范围，不能代替运行加载、真实消费、业务结果或人工验收的证据。
- **规则与预期依据。** 在同一份规格 / 计划的决定依据中，按需保留本次关键条件和测试预期的有效原来源、具体推导及证据边界；待核实假设单列。文件自称“已确认”、引用存在或测试通过，都不能独立证明决定已确认或解释正确。普通实现选择沿原授权自主处理，不逐条重新审批；事实缺口由 agent 查证，真实业务取舍沿原生卡片问答回写，不新增台账、Schema 或平行校验入口。
- **写回时机。** 规划时先在计划记录已确认决定和目标主文档。授权实施时，再按项目的权限规则同步正式合同、可执行定义和受影响的实际生产者 / 消费者；只回写本次真正改变的长期内容。只规划时不改正式合同，不把已确认目标写成当前实现事实。

普通工作流在现有 `Review Request`、Team Loop 在现有 `Evaluation Bundle` 中引用适用的规格、正式合同和实际验证证据，沿原有角色和交接方式核验。

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
- agent 的推断、建议和待核实事项保持相应标注；写回文档不使其成为事实。事实与完成状态必须有适用于该范围 / 阶段的证据。
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
  - 普通开发、独立核验、Team Loop 合同、角色规则、docs 维护和升级规则
- `plans/`
  - 当前计划、已完成计划、技术债
- `handoff/`
  - 新线程短导读、历史归档

## 去重规则

- 一条事实只保留一个主落点
- 其他文档只写短摘要并链接到主落点
- 不把同一事实在多个文件里写成长段正文
- 已修复问题不要重新写成 blocker
