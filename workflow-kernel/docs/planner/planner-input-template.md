# 普通工作流输入模板

> 最后更新时间：2026-04-30
> 适用范围：普通工作流的 plan-only / read-only audit / review 输入模板
> 本文主职责：提供可复制的 plan / audit / review 输入骨架
> 推荐下一跳：`planner-output-schema.md`

## 使用方式

当用户需要普通工作流中的 plan-only、read-only audit 或 review framing 时，可复制下面模板。`@planner` 或“帮我做一轮方案”只作为历史兼容入口，等价于 `plan-only` 或 `read-only audit`，不再表示独立 planner 模式。

plan-only / read-only audit 默认只读，除非后续明确切换为执行轮。

```md
@planner

# 本轮目标

- 用户目标：
- 背景 / 已知事实：
- 本轮类型：plan / execute / review
- 本轮应采用的输出 schema：plan / execute / review / 由 planning phase 判断后声明

# 已知限制

- 是否允许改代码：否 / 是，范围：
- 是否允许改 docs：否 / 是，范围：
- 是否允许运行命令：否 / 是，范围：
- 是否允许 GUI / computer-use：默认否；若允许，范围和次数上限：
- 是否允许拆分 subagent：允许 / 不允许 / 由 planning phase 判断后显式说明
- 若允许 subagent，普通工作流中仅作为并行只读审计建议；只有 Team Loop 才由 Leader 正式调度 subagent。
- 建议并行审计块：
  - Subagent A：
  - Subagent B：
  - Subagent C：

# 当前阶段控制面板

- 当前主线：
- 当前暂停项：
- 当前前置条件：
- 下一步允许推进：
- 下一步不允许推进：
- 是否需要先走 audit-first：是 / 否 / 由 planning phase 判断

# 当前关注范围

- 页面 / 模块：
- 业务链路：
- 相关服务 / 数据表 / 服务端函数：
- 明确不纳入范围：

# 风险边界

- 产品合同：
- 数据 / 状态机边界：
- 权限 / 行级授权 / 后端边界：
- 图片 / 文件 / 存储边界：
- 已知历史脏项或候选残留：
- 当前 worktree 是否需要分层说明：否 / 是
- 历史脏项 / 在途开发面：
- 本轮真实候选范围：

# 必读材料

- 必读 docs：
  - `AGENTS.md` 或 `CLAUDE.md`
  - `docs/README.md`
  - `docs/handoff/latest.md`
  - `docs/product/current-state.md`
  - `docs/architecture/domain-boundaries.md`
- 必读代码：
  -
- 必读 evidence：
  -

# 输出要求

- 输出结构：按 `docs/planner/planner-output-schema.md`
- 是否需要 Evaluator Bundle：是 / 否
- 是否需要详细人工验收清单：是 / 否
- 是否需要产出只读审计 prompt：是 / 否
- 是否需要产出执行 prompt：是 / 否
```

## 填写提示

- 如果根因未锁，请把本轮类型写成 `plan` 或 `review`，并要求 planning phase 先走 `../../workflow/audit-first.md`。
- 如果当前只看到现象，不要在输入里写死根因。
- 如果有历史候选或脏 worktree，请在“已知历史脏项或候选残留”里先列出，避免混入本轮 bundle。
- 如果不确定是否要拆 subagent，不要留空；让 planning phase 明确输出“拆 / 不拆”和原因。
- 如果不确定是否允许 GUI / computer-use，默认写“否”，复杂验证交给人工或后续执行轮。
- 如果当前项目主线、暂停项、前置条件很关键，优先填“当前阶段控制面板”，避免 planning phase 只写泛泛背景。
- 如果后续要进入执行轮，planning phase 应先基于 current code 和 evidence 输出执行 prompt，而不是直接写实现。
