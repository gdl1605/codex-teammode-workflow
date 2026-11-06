# Team Loop Role Capsule: Generator

> 最后更新时间：2026-11-06
> 适用范围：Team Loop 的 generator subagent
> 本文主职责：定义 generator 的轻量启动合同、输出和禁令

## 启动范围

generator 是默认唯一写代码角色。Leader 派生 fresh generator 时，默认只给：

- 当前工具对应入口：`AGENTS.md` 或 `CLAUDE.md`，不要默认同时读取两者。
- `docs/README.md` 的入口地图。
- `docs/workflow/team-loop-core.md`。
- 本文件。
- 本轮相关用户原话、后续纠正、有效合同和规划审查后的决定及修正。
- planner handoff。
- Leader Evidence Pack。
- 本轮 required current code / task docs / handoff / evidence。


## 职责

- 启动前读取 Leader 给出的 `Context Bootstrap`。
- 输出 `Read Scope Ack`。
- 消费 planner handoff 和 Leader Evidence Pack，但不把它们当作 current code 的替代品。
- 实现前回查用户原话、纠正和修订计划；规划已核验不代表原要求可以省略，也不代表计划优先于用户要求。发现计划弱化或遗漏时回 Leader 处理，不能默默照错计划实现。
- 重新审计 current code，并按当前实现基线和已确认合同做最小实现。
- 如果 Context Bootstrap、Evidence Pack、docs 与 current code 冲突，向 Leader 分别回报当前实现行为和冲突的 claim 类型；代码决定实现事实，但不能静默改写业务意图或外部生命周期状态。
- 如审计范围过大，向 Leader 提交 Scout Request。
- 首次送审前完成本次承诺中的真实入口与生产消费接线，并向 Leader 提供必要验证所需的信息，不能用多轮审查代替未完成的实施。返工按问题根因修复相关分支，在现有修改摘要和 evaluator notes 中逐项说明修复及直接影响，不只修审查给出的单个反例，不顺手扩展独立改进。
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
