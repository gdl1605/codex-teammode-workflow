# Workflow Update Policy

> 最后更新时间：2026-06-03
> 适用范围：把新版 Codex-teammode Workflow 覆盖到已安装旧工作流的目标项目
> 本文主职责：定义哪些内容可覆盖、哪些只能合并、哪些永不覆盖
> 推荐下一跳：目标项目中的 `codex-teammode-workflow/UPDATE_MANIFEST.md`

## 核心原则

升级不是把新版文件全量复制进目标项目。

升级只替换开源工作流拥有的内核区域；目标项目自己的事实、规则和手改内容默认保留。

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

它们使用 `overwrite-if-clean`：只有目标文件没有本地改动时才覆盖；如果目标文件被手改过，必须报告冲突或生成 `.new` 提案。

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
    strategy: overwrite-if-clean
    installed_sha256: <sha256 after update>
```

后续升级用 `installed_sha256` 判断目标文件是否被本地手改：

- 当前 hash 等于 `installed_sha256`：可以安全覆盖。
- 当前 hash 不等于 `installed_sha256`：不能静默覆盖，必须生成冲突报告或 `.new`。

## 旧项目接入

如果旧项目没有 `.codex-teammode-version`：

1. 先按 `UPDATE_MANIFEST.md` 分类文件。
2. 对 mixed files，只在已有 managed block 时替换；没有 block 就输出建议，不直接改。
3. 对 workflow kernel 文件，只有在确认像未改动的旧内核文件时才覆盖。
4. 对无法确认的文件，生成 `.new` 或冲突报告。
5. 用户确认后再写入 `.codex-teammode-version`，作为后续升级基线。

## 输出要求

每次升级结束时必须输出：

- 旧版本 / 新版本。
- updated files。
- created files。
- managed blocks updated。
- conflicts 或 `.new` proposals。
- never-overwrite paths skipped。
- marker file status。
- manual migration notes。
- docs impact check。
