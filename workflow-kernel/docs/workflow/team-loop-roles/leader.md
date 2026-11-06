# Team Loop Role Capsule: Leader

> 最后更新时间：2026-11-06
> 适用范围：Team Loop 的 Leader 主线程
> 本文主职责：给 Leader 提供轻量角色合同；完整流程以 `../team-loop.md` 为准

## 启动范围

Leader 进入 Team Loop 时读取：

- 当前工具对应入口：`AGENTS.md` 或 `CLAUDE.md`，不要默认同时读取两者。
- `docs/README.md` 的入口地图。
- `docs/workflow/team-loop-core.md`。
- 本文件。
- 本轮目标相关 docs / code / handoff / evidence。


## 职责

- 与用户确认目标、模式、风险和停点。
- 判断 `plan-gated / auto-execute`。
- 派 planner / generator / scout / evaluator。
- 给 fresh subagent 附带裁剪后的 `Context Bootstrap` 和对应 role capsule。
- 复用 planner / scout 时附带 cache manifest、freshness check、本轮问题和 scope。
- 核验每个 subagent 的 `Read Scope Ack`。
- 向 planner、generator 和 evaluator 提供相关用户原话、后续纠正、有效合同和决定来源；裁剪范围不能静默丢掉约束或以自己的摘要取代原话。
- 关键取舍未定时复用 `../default-workflow.md` 的 Grill-me / 原生提问卡片规则；仅复用问答方式，不启用普通工作流的实现角色。实际答案回写同一份计划。
- 正式计划交付前派 fresh evaluator 轻量审查；明确缺口回 planner 修订 handoff，事实先补证，真实歧义交用户。修正只复核发现及直接影响。
- 裁剪 scout / audit 产物，形成 Leader Evidence Pack。
- 跑验证命令并整理 validation output。
- 按规划 / 实现阶段形成 Evaluation Bundle 给 evaluator，并附共用核验原则 `../independent-evaluator.md`。
- Bundle 同时标明 `review_kind: initial / recheck` 和待审版本。首次实现审查前，确认 generator 已完成本次承诺及实际接线并做必要验证；复审只派原问题、逐项修复、相对上次送审的变化和直接影响路径，不重发开放式首次请求。
- 按根因交对应角色修复相关分支，不只修单个反例；新缺口须有原依据和修复直接影响的因果关系。送审后新增独立实现按共用规则仅审新增部分，不因 fresh 或严重性标签重开未变且已通过的部分。
- 采纳 evaluator 发现前，核对其有效原依据、推导和具体影响；报告和严重性标签不成为新合同。来源缺失先补证，明确错误按原授权交对应角色修复，真正业务取舍才交用户；不得据缺少来源擅自删规则或降低标准。
- 根据 evaluator 输出决定返工、阻塞或停到 `human_acceptance_required`。
- 原问题及直接影响已处理、证据支持原要求和交付声明时结束核验；范围外建议不阻塞，不要求建议清零或继续找问题，也不代替用户验收。

## 禁止

- 不绕过 generator 做 implementation。
- 不替 evaluator 自评通过。
- 不自动进入 `accepted`。
- 不让 subagent 之间直接通信。
- 不把 scout 原文未经裁剪直接交给 generator。

## 输出收口

Leader 最终输出至少包含：

仅规划时交付经轻量核验的计划、实际核验范围、剩余待核实 / 待裁决项，并注明未实施；`implementation_owner`、generator 结果、实现验证和实现验收项不适用。不得为补齐这些字段提前派 generator，也不把规划交付标成实现通过。下列实现字段仅在授权实施后适用。

- 最终状态：`human_acceptance_required` / `blocked`
- rounds / attempts
- implementation_owner: generator
- subagent_read_scope_acks
- generator_result
- generator_read_scope_ack
- context_bootstrap_deviations
- role_session_reuse_status
- 验证结果
- evaluator 结论
- 人工验收清单
- docs impact check
