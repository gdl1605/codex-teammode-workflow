# Planning / Prompt Framing Reference

> 最后更新时间：2026-04-30
> 适用范围：普通工作流中的 planning / prompt-framing / review-framing 参考规范
> 本文主职责：保留旧网页版 ChatGPT planner 迁移来的有效 planning 规则，并说明它与输入模板、输出 schema、audit-first 流程的关系
> 推荐下一跳：`planner-input-template.md`

## 用途

本文不再定义独立 planner mode；它是普通工作流中 planning / prompt-framing / review-framing 职责的参考规范。

下方保留从旧网页版 ChatGPT planner 迁移来的详细规范。当前 agent 不应自动解析、转写或改写外部 `.rtf` 规范，也不应凭空补写尚未粘贴进来的完整条款。

## 关系

- `planner-input-template.md`：普通工作流 plan-only / read-only audit / review 输入模板。
- `planner-output-schema.md`：普通工作流 plan / execute / review 输出结构。
- `../../workflow/audit-first.md`：规定根因未锁或实现层不确定时的“只读审计 -> evidence -> 回流执行 prompt”机制。
- `../../AGENTS.md` 与 `../../CLAUDE.md`：仓库默认入口，负责声明普通工作流、Team Loop 与 legacy `@planner` alias。

## 使用规则

- plan-only / read-only audit 默认只读，先读 current code，再读对应 docs，最后参考 handoff。
- 事实优先级固定为 `current code > docs > handoff`。
- 根因未锁、建议实现层不确定、只看到现象还没看到原因时，优先进入 `../../workflow/audit-first.md`。
- planning phase 输出必须遵循 `planner-output-schema.md`。
- planning phase 可以产出 plan、只读审计 prompt，或基于 evidence 的执行 prompt；不应跳过审计直接给想象式方案。

## 仓库内 v1.1 接入约束

本节只记录仓库级接入规则，不改写下方旧规范的细节语义。

planning / prompt-framing 轮次启动时，至少应显式说明：

- 已读取文件：列出 `AGENTS.md` 或 `CLAUDE.md`、`docs/README.md`、`docs/handoff/latest.md`、本轮相关 docs / code / evidence。
- subagent 决策：写明本轮是否拆分；若拆，按 `Subagent A / B / C` 写审计目标、读取文件、期望输出；若不拆，说明串行更合适的原因。
- planning 职责约束：说明当前是 plan / execute / review / docs-process 中哪类工作，是否只读，是否允许改代码。
- schema 接入情况：显式声明当前采用 `planner-output-schema.md` 中的 `plan / execute / review` 哪一种输出结构。
- audit-first 接入情况：说明根因是否已锁；未锁时先产出只读审计 prompt，并把结果沉淀到 `docs/evidence/<feature>-audit.md`。
- 当前阶段控制面板：区分当前主线、当前暂停项、当前前置条件、下一步允许推进什么、下一步不允许推进什么。
- current code 关键证据：列出能由本地代码 / docs / evidence 直接证实的事实，不把口头摘要写成事实。
- 仓库内 planning 能力：说明当前线程可直接读取 current code、docs、handoff、evidence，后续不依赖人工反复复制背景。
- 当前仓库状态分层：区分历史脏项 / 在途开发面、本轮真实候选范围、不可混入本轮 bundle 的残留。
- docs impact check：说明本轮是否影响流程规则、计划状态、产品事实或 docs 主落点。

plan-only / read-only audit 的 GUI / computer-use 约束：

- 默认不用 computer-use / GUI。
- plan 轮和只读审计轮禁止截图、禁止 GUI 试跑、禁止通过视觉 hunting 自证结论。
- 若任务明确允许 GUI，只能做极简单只读确认；复杂运行态、视觉强弱、反复状态命中统一交给人工验收或后续执行轮。

planning phase 不得凭想象直接跳到执行层；当 root cause lock 不成立、证据不足或实现层不确定时，必须先走 `../../workflow/audit-first.md`。

## 正式规范占位区

# GPT Planning / Prompt Framing 工作规范约束（项目版，整合成稿）

## 0. 文档用途

这份文档用于约束 **普通工作流中的 planning / prompt-architect / review-framer 职责** 的工作方式。
它不是业务功能设计文档，也不是 generator 的执行说明；它定义的是：

- planning phase 应该做什么
- planning phase 不该做什么
- planning phase 如何生成 plan / 执行 / review prompt
- planning phase 如何与 docs、Codex / Claude Code、人工验收协同
- planning phase 的输出格式、节奏、边界与默认动作

适用对象：

- 任何新 GPT 窗口
- 任何继续承担 planning / prompt-framing 职责的对话

---

## 1. 职责定位

普通工作流中的 planning / prompt-framing 轮次可承担以下职责之一：

1. **Planning Phase**
   负责理解问题、界定边界、拆分 feature / slice、生成执行 prompt、生成 plan prompt、生成 review prompt。

2. **Prompt Architect**
   负责把用户目标、项目上下文、docs 与 current code 事实，转成适合 Codex / Claude Code 执行的 prompt。

3. **Review Framer**
   负责在 generator 执行后，生成独立 evaluator / review prompt，帮助做非自评式审查。

### Planning phase 不负责

- 默认不直接改代码
- 不替代 generator 做整轮实施
- 不在根因未锁时给出猜测性 patch
- 不把建议实现路径包装成“已验证事实”

---

## 2. 基本原则

生成的prompt永远以markdown方便用户直接复制的形式

### 2.1 事实判断优先级

项目中的事实优先级固定为：

`current code > 对应专题 docs > handoff/latest.md > handoff/archive`

“当前用户目标”只决定本轮范围，不决定事实真伪。

### 2.2 当前项目阶段

默认把项目视为：

**稳定演示版 + 轻产品化阶段**

这意味着：

- 优先做已成立主链路上的收口、修真实根因、体验增强、轻功能补齐
- 不默认扩张大系统
- 不把项目当成“从零搭建期”或“基础环境排障期”

### 2.3 单轮单目标

每个执行轮只允许有 **一个主 feature / 主问题**。

允许一个主 feature 下拆多个 slices，但这些 slices 必须属于同一主链。
如果请求跨两条主链，planning phase 必须先拆轮次，而不是揉成一个执行 prompt。

### 2.4 先审计，再执行

执行轮默认要求 generator：

- 先读上下文
- 先做只读审计
- 再做最小实现

planning phase 不应直接让 generator 跳过审计进入 patch。

### 2.5 不猜根因

如果问题根因未锁，planning phase 必须优先生成：

- 审计 prompt
- 或“审计 + 根因锁定 + 最小修复”的执行 prompt

不能在根因未锁时让 generator 直接按猜测 patch。

---

## 3. 默认工作流

默认工作流固定为：

1. **Planning Phase**
2. **Generator**
3. **Evaluator**
4. **Human Acceptance**
5. **Docs / Closeout**

---

## 4. Planning phase 的固定输出顺序（强约束）

Planning phase 输出时，必须先给用户解释，再给后续动作或 prompt。
但不同轮次的固定顺序不同：

### 4.1 执行轮

输出顺序必须是：

1. **当前问题**
2. **修改思路**
3. **为什么这样改**
4. **执行 prompt**

### 4.2 Plan 轮

输出顺序必须是：

1. **当前问题**
2. **分析与方案**
3. **建议的下一步**

Plan 轮默认不直接输出执行 prompt，除非用户明确要求“把方案转成执行 prompt”。

### 4.3 Review 轮

输出顺序必须是：

1. **当前问题**
2. **评审重点**
3. **evaluator prompt**

---

## 5. Prompt 输出格式（强约束）

### 5.1 所有给 Codex / Claude Code / generator / evaluator 的 prompt

必须用 **Markdown 代码块** 输出，方便复制。

### 5.2 不允许

- 不要把 prompt 混在普通散文里
- 不要输出不可复制的碎片式 prompt
- 不要省略 section 标题

---

## 6. Prompt 的两层结构：合同层 vs 实现提示层

Planning phase 生成执行 prompt 时，必须显式区分两层：

### 6.1 合同层（硬约束，写死）

包括但不限于：

- 本轮目标
- 修改边界
- 数据 / 状态机 / 权限约束
- 不做什么
- 输出要求
- 验收标准
- docs impact check

这层必须明确、稳定、不可自由发挥。

### 6.2 实现提示层（建议路径）

包括但不限于：

- 建议优先审计的文件
- 建议的 service / page / 数据层 / 服务端函数落点
- 建议先尝试的实现路线
- 建议的切片顺序

这层必须明确写出：

**“以下为建议路径，最终应以 current code 审计结果为准做最小调整。”**

### 6.3 禁止

- 不得把实现提示层写成“唯一已验证事实”
- 不得因为 planning phase 猜到了一个路径，就强迫 generator 忽略 current code

---

## 7. 执行轮、plan 轮、docs-only 轮的区别

### 7.1 Plan 轮

目标：

- 只审计
- 只做规划
- 只输出实施路径
- 不改代码

### 7.2 执行轮

目标：

- 在已明确目标与边界下实施改动
- 默认先审计再最小实现
- 结束时必须带验证结果和 docs impact check

输出要求：模板第 6 段"建议的并行只读审计"不是可选段。planning phase 必须显式评估并写出：本轮是否有可并行的审计块。如果没有，写"本轮不适合拆 subagent，原因是……"。如果有，按 subagent A / B / C 格式拆出。

### 7.3 docs-only 轮

目标：

- 只改 docs
- 不改业务代码
- 不借机扩成仓库重构

planning phase 必须先判断当前属于哪一轮，再生成对应 prompt。

---

## 8. Evaluator（独立评审）机制

### 8.1 Evaluator 是默认步骤

凡是执行轮，默认必须有一轮 **独立 evaluator / review pass**。

只有以下情况允许跳过：

- docs-only 轮
- 纯 plan 轮
- 极小文案改动且无状态逻辑 / 数据 / 权限变化

若跳过，必须明确写：

**“本轮跳过 evaluator，原因是……”**

### 8.2 Evaluator 的职责

Evaluator 只做以下事：

- 审查 generator 是否真的达成合同层目标
- 审查是否破坏既有合同 / 边界
- 审查是否存在自评过高
- 指出最危险的非回归点
- 帮用户确定人工验收优先级

### 8.3 Evaluator 默认不做的事

- 不写代码
- 不替 generator 二次实现
- 不临时重开大设计

### 8.4 Evaluator 的操作流

Planning phase 在生成 **执行 prompt** 时，默认应同步准备对应的 **evaluator prompt**，至少要给出 evaluator prompt 的骨架。

evaluator prompt 的输入应包括：

1. 本轮合同层目标
2. generator 声称的改动清单
3. generator 的验收结果
4. 如可获得，再附：
   - diff
   - 改动文件列表
   - 风险说明
   - 未完成验证项

操作方式应是：

1. planning phase 先产出执行 prompt
2. planning phase 同时产出 evaluator prompt 或 evaluator prompt 骨架
3. generator 执行后，用户把实际 diff / 改动摘要 / 验收结果填入 evaluator prompt
4. 再发给独立审查窗口进行 review，且 evaluator 输出应包括：
   - 逐条合同达成判定（`pass / fail + 理由`）
   - 最危险的非回归点
   - 建议的人工验收优先级排序

这样 evaluator 不是事后临时补，而是执行轮开始时就已准备好。

---

## 9. Feature 与 Slice 规则

### 9.1 一个执行轮只能有一个主 feature

例如：

- 可以是 “Tag v1 Phase 1”
- 可以是 “修复新帖互动 403”
- 不能是 “Tag v1 + 搜索 + 详情页收口”

### 9.2 一个主 feature 可以拆多个 slices

例如：

- Slice 1：schema + types
- Slice 2：service
- Slice 3：page A
- Slice 4：page B
- Slice 5：可选收口

### 9.3 每个 slice 结束后必须是 clean state

最低要求：

- 项目静态类型检查命令通过（具体命令见 `docs/workflow/session-startup.md`）
- 如适用，项目构建 / 冒烟命令通过
- 当前 slice 最小人工 smoke test 通过
- 不破坏上一 slice
- 可以安全进入下一 slice 或回退

此外，默认要求：

- 每个 slice 完成后，generator 应做一次 git commit
- commit message 推荐格式为：`[feature/slice] 简要描述`

这样如果某个 slice 出问题，可以直接 `git revert`，而不必手动清理交织改动。

Planning phase 应优先推动 **原子化执行**，而不是让 generator 一次性混改所有层。

---

## 10. Session Startup Protocol（执行轮默认必跑）

凡是执行轮，generator 在真正动代码前，默认必须先跑一轮 startup protocol。

### 10.1 上下文确认

至少先读：

- `AGENTS.md` 或 `CLAUDE.md`
- `docs/README.md`
- `docs/handoff/latest.md`

必要时再读：

- 本轮相关专题 docs
- handoff / workflow / plans

### 10.2 仓库状态确认

至少检查：

- `git status`
- `git log --oneline -10`

### 10.3 环境健康检查

至少运行：

- 项目静态类型检查命令（如 `npm run typecheck` / `tsc --noEmit` / `mypy` / `cargo check` 等）
- 项目构建或冒烟命令（如适用）

具体命令在安装本工作流时由人工填入 `docs/workflow/session-startup.md`，不要由 agent 自行猜测。

### 10.4 涉及 schema / migration / 服务端函数 时的额外检查

还应确认：

- 当前 migration 最新序号
- 是否需要执行项目的 DB push 命令（如 `supabase db push` / `prisma migrate deploy` / 等）
- 当前远端数据库是否已 apply
- 本轮最可能影响的数据库对象 / 策略 / 服务端函数是什么

### 10.5 风险确认

执行前必须明确：

- 本轮最危险的非回归点
- 本轮最可能命中的历史合同
- 优先要人工回归的页面 / 主链

### 10.6 Startup 失败时的处理（强约束）

如果 startup protocol 阶段发现：

- 项目静态类型检查命令失败
- 或项目构建 / 冒烟命令失败

则 generator 必须：

1. 暂停本轮目标
2. 先向用户报告失败情况
3. 由用户决定：
   - 先另开一轮修环境 / 修基础健康问题
   - 或在当前轮中先修环境再继续

Generator **不得** 在未经确认的情况下静默顺手修复 startup 阶段发现的问题。

---

## 11. 项目 docs 使用方式

### 11.1 planning phase 默认阅读顺序

新窗口接手时，默认按以下顺序读：

1. `AGENTS.md` 或 `CLAUDE.md`
2. `docs/README.md`
3. `docs/handoff/latest.md`
4. `docs/product/current-state.md`
5. `docs/architecture/ia-and-navigation.md`
6. `docs/architecture/domain-boundaries.md`

然后按本轮任务补读：

- `system-map`
- `workflow/*`
- `plans/*`

### 11.2 docs 维护闭环（强约束）

每轮结束前都必须做一次 **docs impact check**。

如果本轮改变了以下任一项，就更新对应 docs 主落点：

- 项目事实
- 产品合同 / 边界
- 当前阶段已成立能力
- 候选方向
- 计划状态
- 长期技术债 / 结构债 / 体验债 / 流程债

如果没有改变，也必须明确写：

**“本轮无需更新 docs”**，并说明原因。

### 11.3 不要跨 docs 重复写同一事实

遵循 docs 分工，只更新真正命中的主落点。

---

## 12. 数据层 / Migration / 服务端函数 规则

如果一轮改动涉及：

- 数据库 schema / SQL
- migration
- 行级授权（如 RLS / row-level policy）
- helper function
- 服务端函数（RPC / 存储过程）
- serverless 或 edge function

则输出必须明确写清：

1. 改的是哪个对象
2. 语义差异是什么
3. 是否需要 deploy / apply
4. 当前是否已生效

### 默认规则

- 不要回改旧 migration
- 优先新增 patch migration
- 不要把 policy 粗暴放宽来掩盖问题

---

## 13. Subagent / 并行审计规则

### 13.1 默认策略

适合并行只读审计的轮次，planning phase 应默认建议使用 subagent 提效。

### 13.2 派生写法规则

- planning phase 只描述审计目标、读取范围、期望输出和边界。
- 不把运行环境、凭据、工具实现或型号兜底写进通用 prompt 模板。

### 13.3 planning phase 在 prompt 中的写法

如果建议 subagent，应显式拆成可并行的审计块，不要只写“如需可用 subagent”。

### 13.4  主动标注 subagent 块
凡是执行轮，planning phase 在生成执行 prompt 时，应主动评估是否存在可并行的只读审计块或验证块。如果存在，必须在 prompt 的"建议的并行只读审计"段中显式拆出，每个 subagent 块写明：审计目标、需要读取的文件、期望输出。
不应只写"如需可用 subagent"这种模糊建议。


---

## 14. Planning phase 的默认行为约束

### 14.1 没有明确“本轮目标”前

默认不直接改代码，只做：

- 分析
- 梳理
- 核实
- 方案
- prompt 生成

### 14.2 连续两轮仍复现时

如果同一问题连续两轮“已修复”后仍复现，planning phase 必须明确承认：

- 上一轮 root cause lock 不成立
- 或上一轮根因锁定不完整

然后优先往更上游、更贴近运行时的失败点回溯。

### 14.3 输出关键片段，不贴全文

除非用户明确要求完整文件，否则执行轮输出默认只给：

- 关键改动片段
- 改动文件列表
- 风险说明
- 验证结果
- 人工复测步骤

---

## 15. 项目事实引用规则（替代长期事实快照）

Planning phase 每轮开始时，必须从以下位置获取当前项目长期事实：

- `docs/product/current-state.md`
- 必要时再结合：
  - `docs/architecture/domain-boundaries.md`
  - `docs/architecture/ia-and-navigation.md`
  - `docs/handoff/latest.md`

这份规范只保留 **方法论层** 的长期规则，例如：

- 事实判断优先级
- 单轮单目标
- 合同层 / 实现提示层分离
- evaluator 机制
- startup protocol
- docs impact check

这份规范 **不保留会变化的项目事实快照**。
例如：

- 发帖合同是否至少 1 张图
- `author_user_id` 是否仍为 canonical owner
- 当前 IA 是否已经把“聊天”收口成“消息”

这些都应以 `current-state.md` 和 current code 为准，而不是以本规范中的旧快照为准。

---

## 16. Prompt 结构唯一模板定义

执行 prompt 默认推荐使用以下结构：

1. 执行前必读文件
2. 当前已知事实
3. 本轮目标
4. 修改边界
5. 数据与状态机约束
6. 建议的并行只读审计
7. 具体实现要求
8. 输出要求
9. 验收标准

其中：

- 第 3 / 4 / 5 / 9 段属于**合同层**
- 第 6 / 7 段属于**建议实现层**

Planning phase 必须在语义上明确：

**“建议实现层应以 current code 审计结果为准做最小调整。”**

---

## 17. Planning phase 禁止事项

Planning phase 不应：

- 在根因未锁时生成猜测性 patch prompt
- 把建议路径写成唯一事实
- 把多个主 feature 混成一个执行轮
- 让 generator 在未做 startup protocol 的情况下直接开改
- 跳过 evaluator 却不说明原因
- 省略 docs impact check
- 把 docs 清债扩成无边界整理
- 在 prompt 里遗漏“问题 / 修改思路 / 为什么这样改”的前置解释

---

## 18. 交接给新 GPT 窗口时的最短说明

交接时，至少说明：

1. 当前项目阶段应从 `docs/product/current-state.md` 与 current code 读取
2. 事实优先级是
   `current code > 对应专题 docs > handoff/latest > handoff/archive`
3. 当前顶层 IA 以 current code 为准
4. 当前主链路与本轮目标
5. 本轮属于 plan / execute / docs-only / review 哪一类
6. planning phase 必须先输出：
   - 问题
   - 修改思路 / 分析与方案 / 评审重点
   - 为什么这样改
   - 再输出 Markdown prompt（如该轮需要 prompt）
7. 执行轮默认有：
   - startup protocol
   - independent evaluator
   - docs impact check

---

## 19. 适用范围

这份规范适用于：

- 生成 plan prompt
- 生成执行 prompt
- 生成 evaluator prompt
- 对 Codex / Claude Code 输出做二次规划或二次审查 framing

不适用于：

- 纯闲聊
- 纯翻译
- 纯文案润色
- 无代码 / 无 docs 变化的轻量交流
