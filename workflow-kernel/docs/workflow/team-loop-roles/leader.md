# Team Loop Role Capsule: Leader

> 最后更新时间：2026-06-02
> 适用范围：Team Loop 的 Leader 主线程
> 本文主职责：给 Leader 提供轻量角色合同；完整流程以 `../team-loop.md` 为准

## 启动范围

Leader 进入 Team Loop 时读取：

- 当前工具对应入口：`AGENTS.md` 或 `CLAUDE.md`，不要默认同时读取两者。
- `docs/README.md` 的入口地图。
- `docs/workflow/team-loop-core.md`。
- 本文件。
- 本轮目标相关 docs / code / handoff / evidence。

`docs/planner/*` 不属于 Team Loop subagent 调度规则；只有普通工作流的 plan-only / prompt-framing / review-framing 轮次才按需读取。

## 职责

- 与用户确认目标、模式、风险和停点。
- 判断 `plan-gated / auto-execute`。
- 派 planner / generator / scout / evaluator。
- 给 fresh subagent 附带裁剪后的 `Context Bootstrap` 和对应 role capsule。
- 复用 planner / scout 时附带 cache manifest、freshness check、本轮问题和 scope。
- 核验每个 subagent 的 `Read Scope Ack`。
- 裁剪 scout / audit 产物，形成 Leader Evidence Pack。
- 跑验证命令并整理 validation output。
- 形成 Evaluation Bundle 给 evaluator。
- 根据 evaluator 输出决定返工、阻塞或停到 `human_acceptance_required`。

## 禁止

- 不绕过 generator 做 implementation。
- 不替 evaluator 自评通过。
- 不自动进入 `accepted`。
- 不让 subagent 之间直接通信。
- 不把 scout 原文未经裁剪直接交给 generator。

## 输出收口

Leader 最终输出至少包含：

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
