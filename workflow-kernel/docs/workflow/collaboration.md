# 协作规范

> 最后更新时间：2026-05-02
> 适用范围：长期协作规则、审计顺序、证据优先、根因锁定
> 本文主职责：只写跨轮次都要遵守的规则
> 推荐下一跳：`workflow/session-startup.md`

## 基本原则

- 没有明确本轮目标前，默认不改代码
- plan 轮只出方案，不改代码
- 执行轮先审计，再最小实现
- 每轮只做一个主目标
- 已确认事实与推测必须分开写
- 继承背景、当前用户描述、本轮已验证事实必须分层

## 普通工作流轮次

- 当前仓库默认只有两个顶层 AI 工作流：普通工作流与 Team Loop。
- 普通工作流覆盖 `plan-only`、`read-only audit`、`docs-only`、`execute`、`review` 轮次。
- `@planner` 或“帮我做一轮方案”只作为历史兼容入口，等价于普通工作流中的 `plan-only` 或 `read-only audit` 轮，不再表示独立 planner 模式。
- 普通工作流中的 planning 阶段负责做问题收口、边界确认、合同层 / 建议实现层拆分、执行 prompt framing 和 review framing。
- 根因未锁、建议实现层不确定、只看到现象不是原因时，普通工作流先进入 `read-only audit` / `audit-first`，不直接进入 generator 实现。
- Team Loop 派生 subagent 时的项目知识启动包、read scope 回执和 evidence 回流，以 [`workflow/team-loop.md`](team-loop.md) 为主；根因未锁时同时遵守根目录 [`../../workflow/audit-first.md`](../../workflow/audit-first.md)。

## 执行轮默认闭环

- 执行轮默认按 `planning phase -> generator -> evaluator -> human acceptance` 理解。
- `planning phase`
  - 锁本轮问题、边界、合同层与建议实现层。
  - 必要时产出执行 prompt 或 review prompt。
- `generator`
  - 按当前代码事实做最小实现，不把 planning 阶段的建议路径硬写成唯一事实。
- `evaluator`
  - 独立复核行为回归、边界偏移、遗漏验证和文档影响。
- `human acceptance`
  - 用人工复测清单确认主链、非回归点和剩余风险。

## evaluator 默认规则

- 只要是执行轮，默认应有独立 evaluator / review pass。
- evaluator 可以由独立线程、独立模型、独立 review 阶段承担，但不应和生成实现完全混成同一步。
- 以下轮次允许跳过独立 evaluator：
  - plan-only 轮
  - docs-only 轮
  - 纯交接、背景补齐、只读审计轮
  - 本轮产物本身就是 review / evaluator 结果的轮次
- 若执行轮确实跳过独立 evaluator，输出里必须明确说明原因，而不是默认省略。

## session-startup

- 所有执行轮开头都应先跑一遍 startup protocol。
- startup protocol 单独沉淀在 [`workflow/session-startup.md`](session-startup.md)。
- 若本轮涉及数据库 schema / migration / 行级授权 / 服务端函数，startup 阶段就应把历史对象链、当前 apply 状态和最危险非回归点先锁清。

## 修改边界

- 默认最小必要修改
- 默认主修点先限定到核心文件
- 默认不要扩模块
- 默认不要顺手重构
- 默认不要因为“可能有问题”就先动数据库 schema / migration / 行级授权 / 服务端函数
- 只有在明确被真实阻塞时，才允许最小连带修改

## 排查顺序

“分析并修复”类轮次固定按下面顺序推进：

1. 运行态现象
2. 真实调用链
3. 文件、helper、服务端函数、数据返回面
4. 最小修复点

## 共享根因规则

- 多页面、多角色同时出现同一异常时，先确认是不是共用同一条 service、查询、资源授权、服务端函数或状态来源
- 如果共用，优先修一处共享根因
- 不接受在多个页面分别追加局部补丁

## 单轮单 feature

- 每轮默认只做一个 feature 或一个共享根因。
- 如果 feature 过大，可以拆成多个 slice，但每个 slice 仍应服务同一主目标。
- 不要把“顺手一起做”写成合理范围扩张。

## slice 与 clean state

- feature 可拆 slice，但 slice 结束后必须尽量回到 clean state。
- clean state 至少意味着：
  - 当前 slice 的代码、类型、文档和配置不处于明显半成品状态
  - 下一个 slice 不依赖“先记住这段手工补丁别忘了”才能继续
  - 能做的验证已经做，做不了的验证已明确说明原因
- 如果当前 slice 结束后仍是脆弱中间态，应先收口或明确阻塞，不要继续扩下一块。

## 根因锁定规则

- 根因锁不死时，不要先试着修一次
- 应停在当前证据链、已排除项、缺失证据和下一步最小核实点
- 连续两轮“已修复”后仍然复现时，必须明确承认上一轮 root cause lock 不成立
- 若异常表现为点击后还没真正发请求就失败，优先核实按钮绑定、事件参数透传、受控输入回写和编译产物中的中间访问
- 若异常表现为空格或回车被吞、光标回跳，优先核实 `v-model.trim`、输入阶段格式化和受控输入回写

## 证据要求

- 如果输出里要写“remote 已证实”或“远程已确认”，至少应尽量拿到 response body、具体 path 或关键 payload、调用点三项中的大部分
- 缺少证据时，必须明确说明当前结论仍属于代码级或日志级推断
- 不允许把推断包装成已证实根因

## 禁止项

- 不要只改页面文案遮住真实状态
- 不要只让当前页看起来像成功，刷新后又失效
- 不要只靠 fallback 掩盖本应修通的读取合同
- 不要把单点资源预览需求顺手扩成完整资源系统重构
- 不要把已修复问题重新写成 blocker

## 多版本资源链路

- 当资源同时存在“轻量展示版”与“完整原始版”时，要把它们当作两条不同职责链路处理
- 常规列表 / 缩略展示默认读轻量展示版
- 点击放大 / 详情 / 下载读完整原始版
- 涉及多版本资源、授权派生、轻量版 vs. 完整版等场景时，必须显式区分链路

## 文案与状态机

- 不允许只改文案，不核实真实状态机
- 按钮文案必须和真实动作一致
- 交互补齐必须与现有业务语义一致，不新增平行流程

## 数据层 / 服务端函数 / hosted 行为

- 一旦一轮改动涉及数据库 schema、服务端函数（RPC / 存储过程 / serverless 或 edge function 等）或 hosted 行为，输出里必须说明对象、语义差异、是否需要 deploy / apply、是否已经生效
- 默认新增 patch migration，不回改历史 migration

## docs impact check

- 执行轮结束前必须做 `docs impact check`。
- 如果本轮改变了项目事实、产品合同 / 边界、当前阶段已成立能力、候选方向 / 后置方向、计划状态或长期债务，必须更新对应 docs 主落点。
- 如果本轮没有改变这些内容，也要在输出里明确写“本轮无需更新 docs”及原因。
- `docs impact check` 的具体落点判断继续以 [`workflow/docs-maintenance.md`](docs-maintenance.md) 为准。
