# CLAUDE.md

<!-- codex-teammode:managed:start scope=agent-entry version=0.4.0 -->

## 适用范围与触发

- 未显式启用 Team Loop 的开发规划与维护，使用普通工作流：主 agent 澄清关键取舍后，正式计划交付前派 fresh evaluator 轻量核对原要求与计划；授权实施后再派 fresh evaluator 核验实际行为与完成声明。
- 用户 prompt 以 `@team-loop` 开头，或明确要求使用 `Team Loop` / `teamloop` / Leader 调度多个 subagent 时，才启用 Team Loop 规则。
- 仅要求独立 evaluator / review subagent 不启用 Team Loop；主 agent 仍是实现者。用户和目标项目对权限、职责及 subagent 的明确限制优先。
- 仅讨论、引用或修改 Team Loop 规则不等于启动 Team Loop。

## 事实与范围

- 需要项目上下文时，先读 [`docs/README.md`](docs/README.md)，再按任务进入对应专题 docs。
- 当前实现事实的证据优先级：`current code` > 对应专题 docs > `docs/handoff/latest.md` > `docs/handoff/archive/`。
- 当前用户目标决定本轮范围；明确人工确认 / canonical contract 决定业务意图，部署、验收、法务和发布事实必须有各自直接 evidence。
- docs 与代码冲突时，记录代码当前做了什么，不得用实现现状静默覆盖已确认的业务合同。
- 默认只做本轮目标内的最小必要修改，不顺手扩模块或重构。
- 对影响决策的断言，区分已核实事实、用户决定 / 既有合同、agent 假设 / 推断与待核实事项；假设不能因写入计划、代码、测试或总结就变成事实。
- 源码存在、离线通过、运行加载、真实消费和业务成功不能相互替代。已有事实由 agent 查证；真实业务取舍交用户决定。

## 普通工作流

- 完整流程见 [`docs/workflow/default-workflow.md`](docs/workflow/default-workflow.md)，只读核验角色见 [`docs/workflow/independent-evaluator.md`](docs/workflow/independent-evaluator.md)。
- 主 agent 核对实际代码和原要求后形成相称草案；每次交付正式计划前，包括仅规划时，先核对影响行为、算法含义、职责、成本、上限和完成条件的关键取舍。已有决定或明确委托须指出出处；仍是 agent 建议的关键选择先 Grill-me 追问，回答和依据回写同一份计划。不能凭自己选了默认值或写了“建议 / 首版暂不支持”就认为没有未决项；无需追问时也简短交代已有依据。
- Grill-me 默认实际调用原生结构化提问工具发选项卡片；Codex 暴露 `request_user_input_async` 时使用它，遵守当前 schema 和可用模式。问题包含影响和推荐，当前可回答的独立问题同轮发；收到实际用户回答后更新同一份计划，再问依赖问题。推荐 / 预选 / 工具返回不算确认，不按等待时长自动代答；只有原生工具不可用或受限时才说明限制并改用文本选项。
- 正式计划交付前派 fresh 只读 evaluator 轻量检查原话、纠正与计划，找遗漏、约束弱化、无来源取舍和真实歧义。明确遗漏直接修正，事实由 agent 补查，真实业务取舍沿原生卡片交用户；修正只复核发现及直接影响。
- 原有授权足够时在规划核验后直接实现，不新增整份计划批准；用户明确要求先批准计划时遵守该要求。仅规划完成澄清与轻量核验后交付，不自动实现或做实现后核验；单纯只读和安装 / 升级任务不自动进入实现循环。
- 实现前仍回查相关用户原话、纠正和修订计划；规划已核验不能替代原要求。实现及必要验证后再派 fresh 只读 evaluator，只发送本阶段 Review Request，不继承完整规划或实现对话。未具备独立 subagent 能力时说明限制，不冒称已独立核验。
- Review Request 区分规划 / 实现，必须包含相关用户原话 / 纠正、合同和决定来源、标注的假设、待审计划、预期行为及本阶段交付声明；实现阶段另附实际改动与已有脏项界线、消费者和实际验证。总结只用于导航；规划不要求尚不存在的实现结果。
- evaluator 重点核验原要求是否被弱化或遗漏、计划与实际是否偏离、声明是否超过证据、假设是否被写成事实或无依据变成执行条件。明确缺口直接回主 agent，在授权内修复；事实缺口先补证；合同冲突和未决业务选择保留给用户裁决，不阻塞无依赖的工作。
- 修复后仅复核原发现及直接影响；达到既有验收要求就收口。不自行增加 timeout / retry / checksum 门禁、固定审查轮数、额外测试工程或第二套决策入口。
- 按本次真实语义变化更新文档主落点，沿用 `docs/workflow/docs-maintenance.md`；不自动启动其他宏循环，不代替用户验收。

## Team Loop 模式

本节及后续 Team Loop 规则只在明确启用 Team Loop 后生效，不约束普通工作流的实现角色。

- Team Loop 规范落点见 [`docs/workflow/team-loop.md`](docs/workflow/team-loop.md)。
- 派生 subagent 时，`Context Bootstrap` 默认使用 `slim`：当前工具入口 `AGENTS.md` 或 `CLAUDE.md` 二选一、`docs/README.md`、`docs/workflow/team-loop-core.md`、对应 `docs/workflow/team-loop-roles/<role>.md`、本轮必要原话 / docs / code / evidence，evaluator 另附共用核验原则 `docs/workflow/independent-evaluator.md`；完整 `docs/workflow/team-loop.md` 仅在需要核对完整规范时加入，`workflow/audit-first.md` 仅在根因未锁 / 高风险 / 审计回流时加入。
- Leader 主线程是唯一调度者：
  - Leader 派 planner / generator / scout / evaluator。
  - Leader 派生任何 subagent 时必须附带裁剪后的 `Context Bootstrap`，并要求 subagent 输出 `Read Scope Ack`。
  - Leader 只负责调度、裁剪证据、验证和汇总；进入 Team Loop 后不得直接改代码或 docs。
  - Team Loop 中的 planner 是 Leader 调度的只读 subagent。
  - 所有 subagent 只能回报 Leader。
  - subagent 之间禁止直接通信。
  - generator / evaluator / scout 不得自行派生 subagent。
- Team Loop 支持两种模式：
  - `plan-gated`：适合涉及数据合同 / 权限 / 状态机 / 高风险产品域 / 复杂资源链路 / 根因未锁的任务，或用户明确要求先批准 plan 的任务（目标仓库应自行列出具体高风险域）；planner plan 经轻量独立核验后交用户确认，批准后才派 generator。
  - `auto-execute`：适合文案、轻 UI、局部样式、docs 小修和 allowed scope 清楚的低风险任务；Leader 在 planner 快速收口、关键取舍澄清和轻量规划核验后可派 generator，不新增整份计划人工批准，也不能跳过 generator 自己实现。
- generator 如审计范围过大，只能向 Leader 提交 `Scout Request`；scout 只能只读收集线索并回报 Leader；Leader 必须整理 `Evidence Pack` 后再交给 generator。
- audit-first 场景必须复用 `workflow/audit-first.md` 的必读骨架和 evidence 回流要求。
- evaluator 按规划 / 实现阶段消费 Leader 的 `Evaluation Bundle`，并读共用核验原则和相关原话、纠正、合同；不继承规划者或实现者完整叙事。明确缺口经 Leader 回对应角色修正，事实补证，真实歧义交用户；P2 / P3 非阻塞项可留待处理，但不能因此跳过明确违反本次要求的项。
- 仅规划时交付经轻量核验的计划并注明未实施，不派 generator、不要求实现结果。授权实施后可进入 `changes_requested` 并返工，最终停在 `human_acceptance_required` 或 `blocked`；不得自动进入 `accepted`。

## Team Loop 输出规则

- 默认不要贴完整文件全文，除非用户明确要求。
- 需要验证时，优先写清人工验收清单。
- 如果一轮改动涉及数据库 schema / migration / 服务端函数（RPC / 存储过程 / serverless 或 edge function 等），输出必须说明改的是哪个对象、语义差异、是否需要 deploy / apply、以及当前是否已生效。

## Team Loop docs impact check

- 每轮结束前，必须判断本轮是否改变了：项目事实、产品合同 / 边界、当前阶段已成立能力、候选方向 / 后置方向、计划状态、长期技术债 / 结构债 / 体验债 / 流程债。
- 若有变化，必须更新对应 docs 主落点；不要把同一事实分散回写到多个文档。
- 若无变化，输出里也必须明确写“本轮无需更新 docs”及原因。
- docs impact check 只要求更新被本轮语义真正影响的主落点，不要求每轮全量刷新 docs。
- docs impact 是增量维护微循环，不承担跨文档全量事实对账。

<!-- codex-teammode:managed:end -->
