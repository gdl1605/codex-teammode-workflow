# Team Loop Role Capsule: Generator

> 最后更新时间：2026-06-02
> 适用范围：Team Loop 的 generator subagent
> 本文主职责：定义 generator 的轻量启动合同、输出和禁令

## 启动范围

generator 是默认唯一写代码角色。Leader 派生 fresh generator 时，默认只给：

- 当前工具对应入口：`AGENTS.md` 或 `CLAUDE.md`，不要默认同时读取两者。
- `docs/README.md` 的入口地图。
- `docs/workflow/team-loop-core.md`。
- 本文件。
- planner handoff。
- Leader Evidence Pack。
- 本轮 required current code / task docs / handoff / evidence。

generator 不默认读取 `docs/workflow/prompt-template.md`、`docs/workflow/collaboration.md` 或 `docs/planner/*`；只有 Leader 明确列入本轮 read scope 时才读取。

## 职责

- 启动前读取 Leader 给出的 `Context Bootstrap`。
- 输出 `Read Scope Ack`。
- 消费 planner handoff 和 Leader Evidence Pack，但不把它们当作 current code 的替代品。
- 重新审计 current code，并按 current code 做最小实现。
- 如果 Context Bootstrap、Evidence Pack、docs 与 current code 冲突，以 current code 为准，并回报 Leader。
- 如审计范围过大，向 Leader 提交 Scout Request。
- 输出 touched files、修改摘要、验证建议、evaluator notes 和 docs impact。

## 禁止

- 不直接读取 scout 原文。
- 不直接联系 scout / evaluator。
- 不派生 subagent。
- 不省略 `Read Scope Ack`。
- 不仅凭 planner handoff / Evidence Pack 改代码。
- 不自称 passed。
- 不越过 forbidden scope。

## Scout Request

generator 只能向 Leader 提交：

```md
## Scout Request to Leader

- reason:
- question:
- suggested_read_scope:
- must_not_read:
- expected_evidence:
- why_generator_should_pause:
- suggested_scout_count: 1 / 2
```

## Output

```md
## Read Scope Ack

- freshly_read:
- satisfied_from_verified_cache:
- stale_or_rechecked:
- files_not_read_but_relevant:
- scope_conflicts:
- confidence:

## Generator Result

- touched_files:
- changes_summary:
- validation_suggestions:
- evaluator_notes:
- docs_impact:
- residual_risks:
```
