# 普通工作流输出 Schema

> 最后更新时间：2026-04-30
> 适用范围：普通工作流的 plan / execute / review 输出结构
> 本文主职责：让普通工作流中的 planning、执行和 review 输出可审查、可交接、可回流
> 推荐下一跳：`../../workflow/audit-first.md`

## 通用原则

- 输出必须基于 `current code > docs > handoff`。
- 已验证事实、推断、建议实现层必须分开。
- 每轮开头必须显式声明：当前按 `plan / execute / review` 哪一种 schema 输出。
- 每轮都必须显式说明 subagent 决策：拆分时写 `Subagent A / B / C`，不拆时写原因。
- 每轮都应包含“当前阶段控制面板”：当前主线、暂停项、前置条件、下一步允许推进、下一步不允许推进。
- 每轮都应分层表达仓库状态：历史脏项 / 在途开发面、本轮真实候选范围、不可混入本轮 bundle 的残留。
- plan-only / read-only audit 轮默认不使用 computer-use / GUI；若本轮允许，必须写明范围、次数和为什么不能转人工。
- 如果根因未锁，先产出只读审计 prompt，并按 `../../workflow/audit-first.md` 沉淀 evidence。
- 不把 planning 阶段的建议路径伪装成 current code 事实。
- 若输出执行 prompt，必须让 generator 在执行前重新审计 current code。
- 不允许只总结原则而不给结构。

## Plan 轮输出结构

适用场景：

- 用户要求“做一轮方案”。
- 当前还不应改代码。
- 需要判断是否进入执行轮。

必须包含：

1. `A. Startup 结果`
   - 说明已读文件、git 状态、是否有历史脏项。
2. `B. Subagent 决策`
   - 说明拆 / 不拆；若拆，列出各 subagent 的审计目标、读取文件、期望输出。
3. `C. 当前阶段控制面板`
   - 写清当前主线、暂停项、前置条件、下一步允许推进和不允许推进。
4. `D. 问题定义`
   - 写清当前现象、目标、非目标。
5. `E. Current code 证据`
   - 列出代码、docs、evidence 的可证实事实。
6. `F. 根因判断`
   - 区分确定项、推断项、`HUMAN_CHECK_REQUIRED`。
7. `G. 审计 / 证据需求`
   - 说明是否需要先走 audit-first，evidence 应沉淀到哪里。
8. `H. 推荐阶段 / 切片`
   - 给出执行顺序、P0/P1/P2、进入下一阶段门槛。
9. `I. 风险边界`
   - 允许修改、禁止修改、只读核对文件。
10. `J. 人工验收 / HUMAN_CHECK_REQUIRED`
   - 列出人工需要看什么、阻断条件是什么。
11. `K. Docs impact 计划`
   - 后续执行轮需要更新哪些 docs，哪些不该动。
12. `L. 给 human / 下一轮的结论`
   - 用短结论说明是否建议进入执行轮。

与 evidence 的关系：

- 若证据不足，应产出只读审计 prompt。
- 若已有 evidence，应引用 `docs/evidence/<feature>-audit.md` 或对应 evidence README。

## 执行轮输出结构

适用场景：

- 用户明确要求 implement / generator。
- 已有足够 plan 或 evidence。
- 本轮允许按边界改文件。

必须包含：

1. `A. Startup 结果`
   - 已读文件、git status、git log、必要验证命令。
2. `B. Subagent 决策与审计结果`
   - 说明是否拆分；若不拆，说明原因。
3. `C. 当前阶段控制面板`
   - 写清当前主线、暂停项、前置条件、下一步允许推进和不允许推进。
4. `D. 审计结论摘要`
   - 当前真实问题、为什么本轮需要做、哪些延后。
5. `E. 修改边界`
   - 允许修改、禁止修改、只读核对文件；分清合同层和实现提示层。
6. `F. 实际修改`
   - 文件列表、每个文件改什么、明确没做什么。
7. `G. 兼容 / 边界策略`
   - 说明如何不破坏产品合同、状态机、权限、复杂资源链路等。
8. `H. 验证结果`
   - typecheck/build/命令结果；docs-only 轮说明为什么不跑。
9. `I. Evaluator Bundle`
   - 给独立 evaluator 接手的摘要。
10. `J. 详细人工验收清单`
   - 按“操作步骤 / 预期结果”写。
11. `K. 非回归风险`
   - 最危险点和重点回归动作。
12. `L. Docs impact check`
   - 更新了哪些 docs，为什么；没更新哪些，为什么。
13. `M. Closeout`
   - 是否完成、是否具备进入下一阶段、未通过时停留在哪个阶段。

与 docs 的关系：

- 改变计划状态、流程规则、产品合同或阶段口径时，必须更新对应 docs 主落点。
- docs-only / process 轮默认不跑 typecheck/build，除非误改代码或用户明确要求。

## Review 轮输出结构

适用场景：

- 用户要求 review / evaluator。
- 需要独立复核候选 diff。
- 不应默认改代码。

必须包含：

1. `A. Verdict`
   - `pass / partial / request changes`，并说明是否阻断。
2. `B. Review 范围`
   - 说明审查的 commit / diff / 文件范围，以及历史脏项和本轮候选是否分清。
3. `C. 合同层逐项核对`
   - 对用户目标 / 修改边界 / 禁止项 / 验收标准逐条判定。
4. `D. Findings`
   - 按严重度列出 bug、回归、遗漏测试、合同偏移。
5. `E. 最危险的非回归点`
   - 写最可能被误伤的链路、页面、状态机或 docs 口径。
6. `F. Evidence / References`
   - 引用 current code、docs、evidence。
7. `G. Testing / Verification Gaps`
   - 说明哪些验证没做或不能做。
8. `H. 人工验收建议`
   - 若涉及运行态或视觉判断，给人工验收步骤和阻断条件。
9. `I. Docs / closeout 判断`
   - 判断 docs 是否诚实反映本轮状态，是否具备 closeout 条件。

Review 轮规则：

- Findings 优先，摘要次之。
- 没有 findings 时要明确写“未发现阻断问题”，并说明残余风险。
- 不把个人偏好写成阻断，除非它违反合同、业务逻辑或可访问性 / 可用性。
