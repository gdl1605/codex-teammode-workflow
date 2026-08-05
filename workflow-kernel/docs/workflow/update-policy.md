# Workflow Update Policy

> 最后更新时间：2026-08-04
> 适用范围：把新版 Codex-teammode Workflow 覆盖到已安装旧工作流的目标项目
> 本文主职责：定义哪些内容可覆盖、哪些只能合并、哪些永不覆盖
> 推荐下一跳：目标项目中的 `codex-teammode-workflow/UPDATE_MANIFEST.md`

## 核心原则

升级不是把新版文件全量复制进目标项目。

升级会原地替换开源工作流拥有的内核文件；目标项目自己的事实、规则和 managed block 外的内容默认保留。

## 文件归属

### 可覆盖的 workflow kernel

这些文件只承载工作流规则，不应承载目标项目业务事实：

```text
docs/workflow/collaboration.md
docs/workflow/docs-maintenance.md
docs/workflow/session-startup.md
docs/workflow/prompt-template.md
docs/workflow/team-loop-core.md
docs/workflow/team-loop.md
docs/workflow/team-loop-roles/**
docs/workflow/update-policy.md
docs/planner/**
workflow/audit-first.md
```

它们使用 `replace-workflow`：目标文件存在时直接原地替换为新版包里的文件；目标文件缺失时直接创建。

不要为这些 workflow-owned 文件生成 `.new`。旧工作流文件就是要被新版工作流替换，不能在同一目录里留下旧版和新版两份规则。

如果旧升级尝试已经留下了同名 `<target>.new`，在原目标文件完成原地替换后，应删除这些 stale `.new` 文件，并在输出中列出。

### 只能 managed-block 更新的混合文件

这些文件可能同时包含工作流规则和目标项目自己的规则：

```text
AGENTS.md
CLAUDE.md
docs/README.md
```

只能替换 managed block 中的工作流内容，不能覆盖 block 外的目标项目内容。

managed block 格式：

```md
<!-- codex-teammode:managed:start scope=<scope> version=<version> -->
... workflow-owned content ...
<!-- codex-teammode:managed:end -->
```

### 永不覆盖的目标项目事实

这些路径属于目标项目：

```text
docs/product/**
docs/architecture/**
docs/handoff/**
docs/plans/**
docs/evidence/**
```

新版工作流不能自动改写这些文件。若新版本需要目标项目配合调整，只能输出 manual migration note。

### 只留在 package 的可选 skill

`skills/docs-review/**` 使用 `package-only`。目标项目升级只更新
`codex-teammode-workflow/` 包内源码，不得把它复制进目标根 docs，也不得安装或覆盖
用户的个人 / 全局 skill 目录。

若新版包含新的 `docs-review`，升级输出只给出手动动作：从新版源码仓库显式运行
`install.sh --install-docs-review ...`。内容不同时仍需用户另加 `--force-skill`，且安装器
只备份和替换精确的 `docs-review` 目录。

v2 skill 必须整体刷新，包含 schema-4 scanner、schema-2 plan/report validator、shard
preparer / merger 与 shard / synthesis 两份角色合同。不得把 v1 临时计划或 closure report
继续用于 apply；发现旧 schema 时应回到 Plan Mode 重新运行 `$docs-review`。

## 版本标记

目标项目升级后应写入：

```text
docs/workflow/.codex-teammode-version
```

建议内容：

```yaml
version: <workflow-kernel/VERSION>
updated_at: <ISO-8601 timestamp>
update_schema: 1
package_source: codex-teammode-workflow
managed_files:
  docs/workflow/team-loop.md:
    strategy: replace-workflow
    installed_sha256: <sha256 after update>
```

后续升级可用 `installed_sha256` 做报告：

- 当前 hash 等于 `installed_sha256`：说明上次升级后未改动。
- 当前 hash 不等于 `installed_sha256` 且策略为 `replace-workflow`：仍然原地替换，但在输出中说明本地 workflow 编辑已被新版替换。
- 当前 hash 不等于 `installed_sha256` 且策略为 `managed-block`：只替换 managed block，保留 block 外内容。

## 旧项目接入

如果旧项目没有 `.codex-teammode-version`：

1. 先按 `UPDATE_MANIFEST.md` 分类文件。
2. 对 mixed files，只在已有 managed block 时替换；没有 block 就输出建议，不直接改。
3. 对 workflow kernel 文件，按 `replace-workflow` 原地替换，不生成 `.new`。
4. 清理 workflow kernel 对应的 stale `<target>.new` 文件。
5. 对 `create-if-missing` 文件，只创建缺失项。
6. 对 `never-overwrite` 路径，完全跳过。
7. 对 `package-only` skill，只保留包内源码并报告可选手动安装，不修改个人 skill。
8. 升级后写入 `.codex-teammode-version`，作为后续升级基线。

## 输出要求

每次升级结束时必须输出：

- 旧版本 / 新版本。
- updated files。
- created files。
- managed blocks updated。
- workflow-owned files replaced in place。
- stale workflow `.new` files removed。
- mixed-file conflicts requiring human review。
- never-overwrite paths skipped。
- package-only paths retained / optional skill manual action。
- marker file status。
- manual migration notes。
- docs impact check。
