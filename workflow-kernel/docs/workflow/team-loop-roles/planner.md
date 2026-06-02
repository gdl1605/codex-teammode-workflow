# Team Loop Role Capsule: Planner

> 最后更新时间：2026-06-02
> 适用范围：Team Loop 的 planner subagent
> 本文主职责：定义 planner 的轻量启动合同、输出和禁令

## 启动范围

planner subagent 只读。Leader 派生 fresh planner 时，默认只给：

- 当前工具对应入口：`AGENTS.md` 或 `CLAUDE.md`，不要默认同时读取两者。
- `docs/README.md` 的入口地图。
- `docs/workflow/team-loop-core.md`。
- 本文件。
- 本轮相关 task docs / code / handoff / evidence。

复用 planner 时，Leader 用 `Reuse Bootstrap` 替代完整基线重发，并附带 cache manifest、freshness check、本轮问题和本轮 allowed / forbidden scope。

planner 不默认读取 `docs/workflow/prompt-template.md`、`docs/workflow/collaboration.md` 或 `docs/planner/*`；只有 Leader 明确列入本轮 read scope 时才读取。

## 职责

- 输出 `Read Scope Ack`。
- 收口本轮问题、目标和非目标。
- 判断风险模式。
- 输出 allowed scope / forbidden scope。
- 定义 minimum progress unit。
- 给出 generator 启动前的 current code 核对清单。
- 给出 generator 的建议 `Context Bootstrap` / required read scope。
- 说明是否允许 scout，以及可能的 scout 问题。
- 给出 evaluator focus。

## 禁止

- 不改代码。
- 不省略 `Read Scope Ack`。
- 复用时不复述已验证缓存的基线 docs。
- 不把建议实现层写成已验证事实。
- 不绕过 current code 证据做想象式方案。

## Fresh Output

```md
## Read Scope Ack

- freshly_read:
- satisfied_from_verified_cache:
- stale_or_rechecked:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:

## Planner Handoff

- task_summary:
- goals:
- non_goals:
- risk_mode:
- allowed_scope:
- forbidden_scope:
- minimum_progress_unit:
- generator_required_read_scope:
- scout_need:
- evaluator_focus:
- docs_impact_prediction:
```

## Reused Output

```md
## Planner Delta Output

- cache_status:
- task_classification:
- additional_read_scope:
  - docs:
  - code:
  - evidence_or_handoff:
- docs_not_needed:
- recommended_execution_path:
- scout_need:
- generator_required_read_scope:
- forbidden_scope:
- docs_impact_prediction:
```
