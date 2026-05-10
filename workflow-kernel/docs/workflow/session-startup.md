# Session Startup Protocol

> 最后更新时间：2026-04-30
> 适用范围：所有执行轮的开场检查
> 本文主职责：把执行轮启动时必须先确认的上下文、仓库状态和风险点固定下来
> 推荐下一跳：`workflow/collaboration.md`

## 默认目标

- 先确认上下文，再开始审计和实现。
- 先确认仓库状态和环境健康，再判断本轮风险。
- 先锁清历史合同和非回归点，再进入修改。

## 1. 上下文确认

执行轮默认先读：

1. `AGENTS.md` 或 `CLAUDE.md`
2. `docs/README.md`
3. `docs/handoff/latest.md`
4. 当前轮次直接相关的专题 docs

要求：

- 事实判断优先级始终是 `current code -> 对应专题 docs -> handoff/latest.md -> handoff/archive/`
- 若 docs 与 current code 不一致，以 current code 为准，并在输出中明确指出差异

## 2. git 状态确认

执行轮默认先看：

- `git status`
- `git log --oneline -10`

目标：

- 确认当前工作树是否干净
- 确认最近几轮改动是否可能影响本轮
- 避免把别人的在途改动误当成本轮根因

## 3. 环境健康检查

执行轮默认先跑：

- 项目的静态类型检查命令（如 `npm run typecheck` / `tsc --noEmit` / `mypy` / `cargo check` 等）
- 项目的构建或冒烟命令（如适用）

目标命令在安装本工作流时由人工填入 `docs/workflow/session-startup.md` 的本节，不要由 agent 自行猜测。

目标：

- 区分“仓库本来就坏了”和“本轮引入了新问题”
- 给后续输出里的非回归判断建立基线

如果某项检查当前无法执行，必须说明：

- 为什么没执行
- 这会留下什么验证缺口

## 4. 数据库 / 服务端函数 轮次的额外检查

如果本轮涉及数据库 schema / migration / 行级授权 / 服务端函数（RPC / 存储过程 / serverless 或 edge function 等），startup 阶段还要额外确认：

- 当前最新 migration 序号
- 当前要改的对象最初是在哪个 migration / SQL 对象里定义的
- 后续有没有已经改写过同一对象
- 当前 apply / deploy 状态是否清楚
- 这轮最可能打破的历史合同是什么

输出里至少要能回答：

- 改的是哪个对象
- 语义差异是什么
- 是否需要 deploy / apply
- 当前是否已生效

## 5. 风险确认

执行轮开头默认要先写出：

- 本轮最危险的非回归点
- 本轮最容易误判的历史合同
- 当前如果修错，最可能伤到哪条主链

不要等到实现后才补做这一层判断。

## 6. 适用范围与边界

- 这套 protocol 默认适用于所有执行轮。
- docs-only、plan-only 和 read-only audit 轮不需要强行跑完整的 build / runtime 检查，但仍应先确认上下文和边界。
- 如果 startup 阶段发现根因未锁、实现层不确定或敏感域证据不足，应先切回 `../../workflow/audit-first.md`，不要直接进入 generator 实现。
- 如果某轮用户已经明确提供了其中一部分结果，仍应核对是否足够，不要直接跳过整套 protocol。
