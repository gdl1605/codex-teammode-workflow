#!/usr/bin/env python3
"""Deterministically inventory Markdown docs and emit review candidates as JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


SCHEMA_VERSION = 5
SCANNER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DATE_RE = re.compile(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)")
UPDATED_AT_RE = re.compile(
    r"(?:updated[_ -]?at|last[_ -]?updated|最后更新时间|更新时间)\s*[:：]\s*"
    r"(20\d{2}-\d{2}-\d{2})",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
BULLET_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$")
CLAIM_ID_RE = re.compile(
    r"(?:claim[_ -]?id|冲突\s*id|事实\s*id)\s*[:：=]\s*[`\"']?([A-Za-z0-9._-]+)",
    re.IGNORECASE,
)
DOCS_REVIEW_PROTOCOL_LEAK_RE = re.compile(
    r"(?:^\s*>?\s*(?:稳定锚点|stable\s+anchor)\s*[:：])|"
    r"(?:(?:claim[_ -]?id|冲突\s*id|事实\s*id)\s*[:：=]\s*[`\"']?DR[-_][A-Za-z0-9._-]+)|"
    r"(?:(?:audit|batch)[_ -]?id\s*[:：=])",
    re.IGNORECASE,
)

REPOSITORY_PATH_PREFIXES = {
    ".agents",
    "docs",
    "platform-overlays",
    "scripts",
    "skills",
    "src",
    "supabase",
    "tests",
    "workflow",
}
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")

TERM_GROUPS = {
    "status": (
        "planned",
        "candidate",
        "pending",
        "implemented",
        "validated",
        "evaluator_passed",
        "migration_applied",
        "deployed",
        "runtime_smoked",
        "human_accepted",
        "legal_accepted",
        "released",
        "accepted",
        "completed",
        "当前",
        "候选",
        "计划中",
        "待定",
        "待执行",
        "已实现",
        "已验证",
        "已验收",
        "已完成",
        "已应用",
        "已部署",
        "已发布",
    ),
    "platform": (
        "H5",
        "web",
        "mp-weixin",
        "mini-program",
        "小程序",
        "shared",
        "共享",
        "iOS",
        "Android",
    ),
    "environment": (
        "local",
        "development",
        "dev",
        "test",
        "staging",
        "production",
        "prod",
        "hosted",
        "runtime",
        "本地",
        "测试环境",
        "预发",
        "生产环境",
        "线上",
    ),
}

CURRENT_CANDIDATE_TERMS = ("candidate", "proposed", "proposal", "候选", "拟议", "提案")
ACTIVE_COMPLETION_TERMS = (
    "accepted",
    "completed",
    "human_accepted",
    "已验收",
    "已完成",
)
DOMAIN_RUNTIME_TERMS = (
    "migration_applied",
    "deployed",
    "deployment",
    "runtime_smoked",
    "released",
    "已应用",
    "已部署",
    "已上线",
    "已发布",
)
NAVIGATION_HINT_RE = re.compile(
    r"(?:推荐下一跳|下一跳|下一步|继续阅读|参见|详见|"
    r"(?:设计源|source|文档|目录|路径).{0,12}(?:入口|路径|目录|root)|"
    r"(?:入口|主落点)\s*[:：]|next\s*(?:step|hop)|see\s+also)",
    re.IGNORECASE,
)
FROZEN_SCOPE_RE = re.compile(
    r"(?:首版|发布|release).{0,16}(?:功能)?范围.{0,8}(?:已)?冻结|"
    r"(?:release|feature)\s+scope.{0,12}frozen",
    re.IGNORECASE,
)
RELEASE_SCOPE_RE = re.compile(
    r"(?:release_scope|release\s+scope|首版范围|发布范围)\s*[:：=]\s*"
    r"([A-Za-z_\-]+|首版内|首版外|上架后|并行不阻塞|未解决)",
    re.IGNORECASE,
)
RELEASE_BLOCKING_RE = re.compile(
    r"(?:release_blocking|release\s+blocking|是否阻塞(?:首版|发布|上架))\s*[:：=]\s*"
    r"(true|false|unknown|yes|no|是|否|未知)",
    re.IGNORECASE,
)
ACTIVE_PLAN_SINGLETON_RE = re.compile(
    r"(?:唯一|仅有|only\s+(?:one|the\s+following)).{0,20}(?:active|活跃)"
    r"|(?:active|活跃).{0,20}(?:唯一|仅有|only\s+one)",
    re.IGNORECASE,
)
VALID_RELEASE_SCOPES = {
    "included",
    "excluded",
    "post_release",
    "parallel_non_blocking",
    "unresolved",
    "首版内",
    "首版外",
    "上架后",
    "并行不阻塞",
    "未解决",
}
VALID_RELEASE_BLOCKING = {"true", "false", "unknown", "yes", "no", "是", "否", "未知"}
COMPLETED_RISK_STATUS_RE = re.compile(
    r"(?:\b(?:candidate|proposed|in\s+progress|todo)\b|"
    r"\bpending\s+(?:apply|deployment|migration|execution|acceptance)\b|"
    r"(?:当前|仍|计划).{0,16}\bactive\b|\bactive\s+plan\b|"
    r"候选|待(?:执行|应用|apply|部署|上线|发布|验收|确认)|等待|尚未|"
    r"仍需|还需|需要\s*(?:apply|执行|应用|部署|上线|发布|验收|确认)|"
    r"不是\s*(?:accepted|已验收(?:生产)?事实)|"
    r"(?:下一步|后续动作|next\s*step))",
    re.IGNORECASE,
)
COMPLETED_CURRENT_STATUS_RE = re.compile(
    r"(?:当前(?:状态|阶段|终态|仍|尚|待|需|需要)|"
    r"目前(?:仍|尚|为|是)?|现状|\bcurrent\s+(?:status|state)\b|"
    r"\bstill\b)",
    re.IGNORECASE,
)
COMPLETED_CLOSED_STATUS_RE = re.compile(
    r"(?:completed|archived|human_accepted|已完成|已归档|已验收|验收通过)",
    re.IGNORECASE,
)
HISTORICAL_CONTEXT_RE = re.compile(
    r"(?:历史(?:状态|实现|记录|快照|口径)?|曾经|当时|旧口径|截至|"
    r"已被.{0,20}取代|superseded|historical(?:\s+snapshot)?)",
    re.IGNORECASE,
)
HISTORICAL_SECTION_RE = re.compile(
    r"(?:历史|旧(?:状态|口径|实现|计划)?|原始(?:状态|计划)?|此前|"
    r"实施前|执行前|落地前|迁移前|验收前|归档快照|"
    r"截至\s*20\d{2}-\d{2}-\d{2}|"
    r"(?:phase|round|loop)\s*[A-Z0-9][A-Z0-9._-]*|"
    r"(?:implementation\s+audit|closeout|cleanup|启动\s*checklist|startup\s+checklist|"
    r"docs\s+impact(?:\s+计划)?)|"
    r"(?:stale|planned).{0,20}(?:entries|snapshot|matrix)|"
    r"historical|legacy|previous|before\s+(?:implementation|migration|acceptance))",
    re.IGNORECASE,
)
ARCHIVE_OVERLAY_NOTICE_RE = re.compile(
    r"(?:正文|下文|以下(?:内容|章节)?|后续(?:内容|章节)?|全文).{0,36}"
    r"(?:历史|归档|快照|不再代表当前)",
    re.IGNORECASE,
)
LIFECYCLE_INDIRECTION_RE = re.compile(
    r"(?:按|依照).{0,18}(?:evidence|计划|plan).{0,18}(?:读取|判断)|"
    r"read.{0,18}(?:evidence|plan).{0,18}independent",
    re.IGNORECASE,
)
LIFECYCLE_AXIS_TERMS = (
    "planned",
    "implemented",
    "validated",
    "evaluator_passed",
    "migration_applied",
    "deployed",
    "runtime_smoked",
    "human_accepted",
    "legal_accepted",
    "released",
)
MIN_DUPLICATE_BLOCK_LENGTH = 80
MIN_LONG_BULLET_LENGTH = 80
MIN_TABLE_ROWS = 4
MIN_TABLE_NORMALIZED_LENGTH = 80
NEAR_TABLE_ROW_OVERLAP = 0.82


class DocsReviewError(Exception):
    """Expected argument, path, or read failure."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise DocsReviewError(message)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _validate_relative(raw: str, label: str) -> Path:
    value = Path(raw)
    if value.is_absolute():
        raise DocsReviewError(f"{label} must be relative to the repository: {raw}")
    if any(part == ".." for part in value.parts):
        raise DocsReviewError(f"{label} may not contain '..': {raw}")
    return value


def resolve_roots(
    repo_root_raw: str, docs_root_raw: str, scope_raw: str | None
) -> tuple[Path, Path, Path, str | None]:
    repo_root = Path(repo_root_raw).expanduser().resolve(strict=True)
    if not repo_root.is_dir():
        raise DocsReviewError(f"repo root is not a directory: {repo_root_raw}")

    docs_relative = _validate_relative(docs_root_raw, "docs root")
    docs_candidate = repo_root / docs_relative
    try:
        docs_root = docs_candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise DocsReviewError(f"docs root does not exist: {docs_root_raw}") from exc
    if not docs_root.is_dir() or not _is_within(docs_root, repo_root):
        raise DocsReviewError("docs root must resolve to a directory inside the repository")

    if scope_raw is None:
        return repo_root, docs_root, docs_root, None

    scope_relative = _validate_relative(scope_raw, "scope")
    repo_candidate = repo_root / scope_relative
    docs_candidate = docs_root / scope_relative
    lexical_candidate: Path | None = None
    for candidate in (repo_candidate, docs_candidate):
        if not candidate.exists():
            continue
        try:
            resolved_candidate = candidate.resolve(strict=True)
        except (FileNotFoundError, RuntimeError):
            continue
        if _is_within(resolved_candidate, docs_root):
            lexical_candidate = candidate
            break
    if lexical_candidate is None:
        raise DocsReviewError(
            "scope does not resolve to a path inside docs; resolve domain tokens through "
            f"the docs index first: {scope_raw}"
        )
    try:
        scope = lexical_candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise DocsReviewError(f"scope cannot be resolved safely: {scope_raw}") from exc
    if not _is_within(scope, docs_root):
        raise DocsReviewError("scope must resolve inside the docs root")
    if not scope.is_dir() and not (scope.is_file() and scope.suffix.lower() == ".md"):
        raise DocsReviewError("scope must be a directory or Markdown file")
    return repo_root, docs_root, scope, _relative(scope, repo_root)


def collect_markdown_files(scope: Path, docs_root: Path) -> list[Path]:
    if scope.is_file():
        return [scope]

    markdown_files: list[Path] = []
    for current_raw, dirs, files in os.walk(scope, followlinks=False):
        current = Path(current_raw)
        safe_dirs: list[str] = []
        for name in sorted(dirs):
            candidate = current / name
            if candidate.is_symlink():
                try:
                    target = candidate.resolve(strict=True)
                except (FileNotFoundError, RuntimeError) as exc:
                    raise DocsReviewError(f"unreadable symlink: {candidate}") from exc
                if not _is_within(target, docs_root):
                    raise DocsReviewError(f"symlink escapes docs root: {candidate}")
                continue
            safe_dirs.append(name)
        dirs[:] = safe_dirs

        for name in sorted(files):
            candidate = current / name
            if candidate.suffix.lower() != ".md":
                continue
            if candidate.is_symlink():
                try:
                    target = candidate.resolve(strict=True)
                except (FileNotFoundError, RuntimeError) as exc:
                    raise DocsReviewError(f"unreadable symlink: {candidate}") from exc
                if not _is_within(target, docs_root):
                    raise DocsReviewError(f"symlink escapes docs root: {candidate}")
            markdown_files.append(candidate)
    return sorted(markdown_files, key=lambda item: item.as_posix())


def read_markdown(path: Path) -> tuple[str, list[str], bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DocsReviewError(f"cannot read UTF-8 Markdown file {path}: {exc}") from exc
    return text, text.splitlines(), raw


def valid_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def extract_dates(lines: list[str]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    header: dict[str, Any] | None = None
    for number, line in enumerate(lines[:40], start=1):
        match = UPDATED_AT_RE.search(line)
        if match:
            header = {
                "value": match.group(1),
                "line": number,
                "valid": valid_iso_date(match.group(1)) is not None,
            }
            break

    body_dates: list[tuple[date, str, int]] = []
    header_line = header["line"] if header else None
    for number, line in enumerate(lines, start=1):
        if number == header_line:
            continue
        for value in DATE_RE.findall(line):
            parsed = valid_iso_date(value)
            if parsed is not None:
                body_dates.append((parsed, value, number))
    if not body_dates:
        return header, None
    latest = max(body_dates, key=lambda item: (item[0], item[2]))
    return header, {"value": latest[1], "line": latest[2]}


def extract_headings(lines: list[str]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append(
                {"level": len(match.group(1)), "text": match.group(2).strip(), "line": number}
            )
    return headings


def section_for_line(
    headings: list[dict[str, Any]], line_number: int
) -> dict[str, Any]:
    current = {"heading": "<document preamble>", "heading_line": 1}
    for heading in headings:
        if heading["line"] > line_number:
            break
        current = {
            "heading": heading["text"],
            "heading_line": heading["line"],
        }
    return current


def historical_context_by_line(lines: list[str]) -> dict[int, bool]:
    """Return heading-scoped historical context without trusting a file-level disclaimer."""
    context: dict[int, bool] = {}
    heading_stack: list[tuple[int, bool]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            context[number] = False
            continue
        if in_fence:
            context[number] = False
            continue
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            inherited = heading_stack[-1][1] if heading_stack else False
            # A document title is not a license to reinterpret every later deep-linked
            # section. Only a section-level heading establishes inherited history.
            scoped = inherited or (
                level > 1 and HISTORICAL_SECTION_RE.search(heading.group(2)) is not None
            )
            heading_stack.append((level, scoped))
        section_historical = heading_stack[-1][1] if heading_stack else False
        context[number] = section_historical or HISTORICAL_CONTEXT_RE.search(line) is not None
    return context


def _link_destination(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    if re.search(r"\s+[\"']", value):
        value = re.split(r"\s+[\"']", value, maxsplit=1)[0]
    return value


def extract_links(
    lines: list[str], source: Path, repo_root: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links: list[dict[str, Any]] = []
    broken: list[dict[str, Any]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(line):
            label = match.group(1).strip()
            raw_target = _link_destination(match.group(2))
            parsed = urlsplit(raw_target)
            if (
                not raw_target
                or raw_target.startswith("#")
                or parsed.scheme.lower() in {"http", "https", "mailto", "tel", "data"}
                or raw_target.startswith("//")
            ):
                continue
            path_part = unquote(parsed.path)
            if not path_part:
                continue
            candidate = (
                repo_root / path_part.lstrip("/")
                if path_part.startswith("/")
                else source.parent / path_part
            )
            resolved = candidate.resolve(strict=False)
            link = {
                "label": label,
                "target": raw_target,
                "line": number,
                "resolved_path": (
                    _relative(resolved, repo_root) if _is_within(resolved, repo_root) else None
                ),
                "exists": resolved.exists() and _is_within(resolved, repo_root),
            }
            links.append(link)
            if not link["exists"]:
                broken.append(link)
    return links, broken


def _clean_inline_path(raw: str) -> str | None:
    raw_value = raw.strip()
    if re.search(r"[<>*?{}\[\]]", raw_value):
        return None
    value = raw_value.strip("\"'")
    if not value or "\n" in value:
        return None
    if re.search(r"\s/|/\s", value):
        return None
    if value.startswith(("http://", "https://", "mailto:", "data:")):
        return None
    value = value.split("#", 1)[0].split("?", 1)[0].rstrip(".,;:：，。；")
    if not value or value in {"/", "./"}:
        return None
    known_prefix = re.match(
        r"^(?:\.{1,2}/|architecture/|contracts/|docs/|evidence/|handoff/|"
        r"pages/|planner/|plans/|platform-overlays/|product/|scripts/|skills/|"
        r"src/|supabase/|tests/|workflow/)",
        value,
        re.IGNORECASE,
    )
    known_suffix = re.search(
        r"\.(?:css|html|js|json|jsx|md|mjs|py|scss|sql|ts|tsx|vue|yaml|yml)$",
        value,
        re.IGNORECASE,
    )
    if "/" not in value and known_suffix is None:
        return None
    if known_prefix is None and known_suffix is None and value.count("/") < 2:
        return None
    return value


def _resolve_inline_path(
    raw_path: str, source: Path, repo_root: Path, docs_root: Path
) -> tuple[str | None, bool]:
    value = Path(raw_path)
    if value.is_absolute():
        return None, False

    docs_prefixes = {
        "architecture",
        "contracts",
        "domain",
        "evidence",
        "handoff",
        "planner",
        "plans",
        "product",
        "workflow",
    }
    repo_prefixes = {
        "docs",
        "platform-overlays",
        "scripts",
        "skills",
        "src",
        "supabase",
        "tests",
    }
    first = value.parts[0] if value.parts else ""
    candidates: list[Path] = []
    if first in repo_prefixes:
        candidates.append(repo_root / value)
    if first in docs_prefixes:
        candidates.append(docs_root / value)
    candidates.extend((source.parent / value, docs_root / value, repo_root / value))

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if not _is_within(resolved, repo_root):
            continue
        if resolved.exists():
            return _relative(resolved, repo_root), True
    return None, False


def extract_inline_path_references(
    lines: list[str], source: Path, repo_root: Path, docs_root: Path
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    historical_contexts = historical_context_by_line(lines)
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        historical_context = historical_contexts.get(number, False)
        navigation = NAVIGATION_HINT_RE.search(line) is not None and not historical_context
        for match in INLINE_CODE_RE.finditer(line):
            raw_path = _clean_inline_path(match.group(1))
            if raw_path is None:
                continue
            resolved_path, exists = _resolve_inline_path(
                raw_path, source, repo_root, docs_root
            )
            references.append(
                {
                    "raw": raw_path,
                    "line": number,
                    "navigation_context": navigation,
                    "historical_context": historical_context,
                    "is_markdown_path": raw_path.lower().endswith(".md"),
                    "resolved_path": resolved_path,
                    "exists": exists,
                }
            )
    return references


def _path_integrity_value(raw: str) -> str | None:
    value = raw.strip().strip("\"'")
    if not value or "\n" in value:
        return None
    if value.startswith(("http://", "https://", "mailto:", "data:")):
        return None
    return value.split("#", 1)[0].split("?", 1)[0].rstrip(".,;:：，。；")


def _is_machine_specific_absolute_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return normalized.startswith(
        ("/Users/", "/home/", "/private/", "/tmp/", "/var/", "/opt/")
    ) or WINDOWS_ABSOLUTE_PATH_RE.match(value) is not None


def _repository_pattern_anchor(value: str) -> Path | None:
    """Return the deterministic repository prefix before a glob, if any."""
    if re.search(r"<[^>]+>|\{[^}]+\}", value):
        return None
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if not parts or parts[0] not in REPOSITORY_PATH_PREFIXES:
        return None
    static_parts: list[str] = []
    saw_pattern = False
    for part in parts:
        if re.search(r"[*?\[\]]", part):
            saw_pattern = True
            break
        if part:
            static_parts.append(part)
    if not saw_pattern or not static_parts:
        return None
    return Path(*static_parts)


def extract_path_integrity_findings(
    lines: list[str],
    source: Path,
    repo_root: Path,
    docs_root: Path,
) -> list[dict[str, Any]]:
    """Find portability and repository-inventory gaps missed by link-only checks."""
    findings: list[dict[str, Any]] = []
    repo_path = _relative(source, repo_root)
    docs_index = source == docs_root / "README.md"
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in INLINE_CODE_RE.finditer(line):
            value = _path_integrity_value(match.group(1))
            if value is None:
                continue
            if _is_machine_specific_absolute_path(value):
                findings.append(
                    {
                        "type": "machine_specific_absolute_path",
                        "file": repo_path,
                        "line": number,
                        "message": "inline path is tied to one developer machine",
                        "evidence": {"raw": value},
                    }
                )
                continue

            pattern_anchor = _repository_pattern_anchor(value)
            if pattern_anchor is not None:
                resolved = (repo_root / pattern_anchor).resolve(strict=False)
                if not _is_within(resolved, repo_root) or not resolved.exists():
                    findings.append(
                        {
                            "type": "missing_repository_path_reference",
                            "file": repo_path,
                            "line": number,
                            "message": (
                                "repository path pattern has no existing static prefix: "
                                f"{value}"
                            ),
                            "evidence": {
                                "raw": value,
                                "static_prefix": pattern_anchor.as_posix(),
                            },
                        }
                    )
                continue

            if (
                docs_index
                and value.endswith("/")
                and not re.search(r"[<>*?{}\[\]]", value)
                and not value.startswith(("./", "../", "/"))
            ):
                relative = Path(value)
                candidate = (
                    repo_root / relative
                    if relative.parts and relative.parts[0] == docs_root.name
                    else docs_root / relative
                )
                resolved = candidate.resolve(strict=False)
                if not _is_within(resolved, docs_root) or not resolved.is_dir():
                    findings.append(
                        {
                            "type": "missing_docs_index_directory",
                            "file": repo_path,
                            "line": number,
                            "message": f"docs index lists a directory that does not exist: {value}",
                            "evidence": {"raw": value},
                        }
                    )
    return findings


def extract_lifecycle_tables(lines: list[str], path: str) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("|"):
            continue
        lowered = line.lower()
        axes = [axis for axis in LIFECYCLE_AXIS_TERMS if axis in lowered]
        if len(axes) >= 3:
            tables.append({"file": path, "line": number, "axes": axes, "text": line.strip()})
    return tables


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if term and all(ord(char) < 128 for char in term) and term[0].isalnum() and term[-1].isalnum():
        return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


TERM_PATTERNS = {
    group: [(term, _term_pattern(term)) for term in terms]
    for group, terms in TERM_GROUPS.items()
}


def extract_term_signals(lines: list[str], path: str) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {group: [] for group in TERM_GROUPS}
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for group, patterns in TERM_PATTERNS.items():
            for term, pattern in patterns:
                if pattern.search(line):
                    result[group].append(
                        {"file": path, "line": number, "term": term, "text": line.strip()}
                    )
    return result


def extract_claim_ids(lines: list[str], path: str) -> list[dict[str, Any]]:
    claim_ids: list[dict[str, Any]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in CLAIM_ID_RE.finditer(line):
            claim_ids.append({"file": path, "line": number, "claim_id": match.group(1)})
    return claim_ids


def normalize_block(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", normalized)
    normalized = re.sub(r"[`*_~>#|]", "", normalized)
    normalized = re.sub(r"[^\w]+", "", normalized, flags=re.UNICODE)
    return normalized


def extract_blocks(lines: list[str], path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocks: list[dict[str, Any]] = []
    long_bullets: list[dict[str, Any]] = []
    paragraph: list[str] = []
    paragraph_start = 0
    table: list[str] = []
    table_start = 0
    in_fence = False
    in_frontmatter = bool(lines and lines[0].strip() == "---")

    def flush() -> None:
        nonlocal paragraph, paragraph_start
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            normalized = normalize_block(text)
            if len(normalized) >= MIN_DUPLICATE_BLOCK_LENGTH:
                blocks.append(
                    {
                        "kind": "paragraph",
                        "file": path,
                        "line": paragraph_start,
                        "text": text,
                        "normalized": normalized,
                    }
                )
        paragraph = []
        paragraph_start = 0

    def flush_table() -> None:
        nonlocal table, table_start
        if table:
            substantive_rows = [
                row
                for row in table
                if not re.fullmatch(r"\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?", row)
            ]
            row_fingerprints = [normalize_block(row) for row in substantive_rows]
            row_fingerprints = [row for row in row_fingerprints if row]
            text = "\n".join(table)
            normalized = normalize_block(text)
            if (
                len(row_fingerprints) >= MIN_TABLE_ROWS
                and len(normalized) >= MIN_TABLE_NORMALIZED_LENGTH
            ):
                blocks.append(
                    {
                        "kind": "table",
                        "file": path,
                        "line": table_start,
                        "text": text,
                        "normalized": normalized,
                        "row_fingerprints": row_fingerprints,
                    }
                )
        table = []
        table_start = 0

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if in_frontmatter:
            if number > 1 and stripped == "---":
                in_frontmatter = False
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush()
            flush_table()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("|"):
            flush()
            if not table:
                table_start = number
            table.append(stripped)
            continue
        flush_table()
        bullet = BULLET_RE.match(line)
        if bullet:
            flush()
            text = bullet.group(1).strip()
            normalized = normalize_block(text)
            if len(normalized) >= MIN_LONG_BULLET_LENGTH:
                occurrence = {
                    "kind": "long_bullet",
                    "file": path,
                    "line": number,
                    "text": text,
                    "normalized": normalized,
                }
                blocks.append(occurrence)
                long_bullets.append({key: value for key, value in occurrence.items() if key != "normalized"})
            continue
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("<!--")
            or re.fullmatch(r"[-=]{3,}", stripped)
        ):
            flush()
            continue
        if not paragraph:
            paragraph_start = number
        paragraph.append(stripped)
    flush()
    flush_table()
    return blocks, long_bullets


def _completed_plan_line_is_stale(line: str) -> bool:
    prose = LINK_RE.sub("", line)
    prose = INLINE_CODE_RE.sub(
        lambda match: "" if _clean_inline_path(match.group(1)) else match.group(1), prose
    )
    if COMPLETED_RISK_STATUS_RE.search(prose):
        return True
    if not COMPLETED_CURRENT_STATUS_RE.search(prose):
        return False
    return COMPLETED_CLOSED_STATUS_RE.search(prose) is None


def _line_matches(line: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if _term_pattern(term).search(line)]


def _is_current_state(relative_to_docs: Path) -> bool:
    return relative_to_docs.stem.lower().replace("_", "-") == "current-state"


def _is_active_plan(relative_to_docs: Path) -> bool:
    lowered = [part.lower() for part in relative_to_docs.parts[:-1]]
    return (
        "plans" in lowered
        and "active" in lowered
        and relative_to_docs.name.lower() != "readme.md"
    )


def _active_plan_index_findings(
    *,
    docs_root: Path,
    repo_root: Path,
    scope: Path,
    active_plans: dict[str, dict[str, Any]],
    links_by_source: dict[str, list[dict[str, Any]]],
    source_contexts: dict[str, tuple[list[str], list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Reconcile the active-plan directory with its canonical index.

    This check is intentionally global: a narrowed scan cannot prove that it has
    seen every sibling plan.  The index may link to completed/supporting files,
    but every live plan file must be named by at least one resolved index link.
    """
    if scope != docs_root or not active_plans:
        return []

    index_path = _relative(docs_root / "plans" / "active" / "README.md", repo_root)
    findings: list[dict[str, Any]] = []
    if index_path not in source_contexts:
        first_plan = sorted(active_plans)[0]
        return [
            {
                "type": "active_plan_index_missing",
                "file": first_plan,
                "line": 1,
                "message": "active plans exist but plans/active/README.md is missing",
                "evidence": {
                    "expected_index": index_path,
                    "active_plans": sorted(active_plans),
                },
            }
        ]

    indexed_plans = {
        link["resolved_path"]
        for link in links_by_source.get(index_path, [])
        if link.get("exists") and link.get("resolved_path") in active_plans
    }
    for missing_path in sorted(set(active_plans) - indexed_plans):
        findings.append(
            {
                "type": "active_plan_missing_from_index",
                "file": index_path,
                "line": 1,
                "message": "active plan file is not listed by the active-plan index",
                "evidence": {
                    "active_plan": missing_path,
                    "indexed_active_plans": sorted(indexed_plans),
                },
            }
        )

    lines, _ = source_contexts[index_path]
    for number, line in enumerate(lines, start=1):
        if ACTIVE_PLAN_SINGLETON_RE.search(line) and len(active_plans) != 1:
            findings.append(
                {
                    "type": "active_plan_count_contradiction",
                    "file": index_path,
                    "line": number,
                    "message": (
                        "active-plan index claims a single active plan but the directory "
                        f"contains {len(active_plans)}"
                    ),
                    "evidence": {
                        "active_plans": sorted(active_plans),
                        "source_text": line.strip(),
                    },
                }
            )
    return findings


def _is_completed_plan(relative_to_docs: Path) -> bool:
    lowered = [part.lower() for part in relative_to_docs.parts[:-1]]
    return (
        "plans" in lowered
        and "completed" in lowered
        and relative_to_docs.name.lower() != "readme.md"
    )


def _is_domain_doc(relative_to_docs: Path) -> bool:
    if not relative_to_docs.parts:
        return False
    first = relative_to_docs.parts[0].lower()
    if first in {"architecture", "domain", "domains", "contracts"}:
        return True
    return first == "product" and _is_current_state(relative_to_docs)


def _candidate_findings(
    lines: list[str], repo_path: str, relative_to_docs: Path
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    historical_contexts = historical_context_by_line(lines)
    active_completion_sections: dict[int, dict[str, Any]] = {}
    completed_sections: dict[int, dict[str, Any]] = {}
    current_heading_line = 1
    current_heading_text = "<document preamble>"
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            current_heading_line = number
            current_heading_text = heading.group(2).strip()
        if _is_current_state(relative_to_docs):
            matched = _line_matches(line, CURRENT_CANDIDATE_TERMS)
            if matched:
                findings.append(
                    {
                        "type": "current_state_candidate",
                        "file": repo_path,
                        "line": number,
                        "terms": matched,
                        "message": "current-state contains candidate/proposal language",
                        "evidence": line.strip(),
                    }
                )
        if _is_active_plan(relative_to_docs):
            matched = _line_matches(line, ACTIVE_COMPLETION_TERMS)
            if matched:
                section = active_completion_sections.setdefault(
                    current_heading_line,
                    {
                        "heading": current_heading_text,
                        "heading_line": current_heading_line,
                        "lines": [],
                        "terms": set(),
                        "samples": [],
                    },
                )
                section["lines"].append(number)
                section["terms"].update(matched)
                if len(section["samples"]) < 5:
                    section["samples"].append(line.strip())
        if _is_domain_doc(relative_to_docs):
            matched = _line_matches(line, DOMAIN_RUNTIME_TERMS)
            if matched:
                findings.append(
                    {
                        "type": "domain_runtime_status",
                        "file": repo_path,
                        "line": number,
                        "terms": matched,
                        "message": "stable domain/current doc contains apply/deploy/runtime status",
                        "evidence": line.strip(),
                    }
                )
        if line.lstrip().startswith("|") and LIFECYCLE_INDIRECTION_RE.search(line):
            findings.append(
                {
                    "type": "lifecycle_status_indirection",
                    "file": repo_path,
                    "line": number,
                    "terms": [],
                    "message": "lifecycle value is deferred to another plan/evidence instead of recorded",
                    "evidence": line.strip(),
                }
            )
        if (
            _is_completed_plan(relative_to_docs)
            and _completed_plan_line_is_stale(line)
            and not historical_contexts.get(number, False)
        ):
            section = completed_sections.setdefault(
                current_heading_line,
                {
                    "heading": current_heading_text,
                    "heading_line": current_heading_line,
                    "lines": [],
                    "samples": [],
                },
            )
            section["lines"].append(number)
            if len(section["samples"]) < 5:
                section["samples"].append(line.strip())
    for section in active_completion_sections.values():
        findings.append(
            {
                "type": "active_plan_completion",
                "file": repo_path,
                "line": section["heading_line"],
                "terms": sorted(section["terms"]),
                "message": "active plan section contains accepted/completed language",
                "evidence": {
                    "section_heading": section["heading"],
                    "section_line": section["heading_line"],
                    "occurrence_count": len(section["lines"]),
                    "lines": section["lines"],
                    "samples": section["samples"],
                },
            }
        )
    for section in completed_sections.values():
        findings.append(
            {
                "type": "completed_plan_stale_lifecycle",
                "file": repo_path,
                "line": section["heading_line"],
                "terms": [],
                "message": (
                    "completed plan section retains unscoped present/current/candidate/"
                    "pending or next-step language"
                ),
                "evidence": {
                    "section_heading": section["heading"],
                    "section_line": section["heading_line"],
                    "occurrence_count": len(section["lines"]),
                    "lines": section["lines"],
                    "samples": section["samples"],
                },
            }
        )
    return findings


def _without_volatile_locations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_volatile_locations(item)
            for key, item in value.items()
            if key not in {"line", "finding_id", "finding_key"}
        }
    if isinstance(value, list):
        return [_without_volatile_locations(item) for item in value]
    return value


def scan_docs(repo_root_raw: str, docs_root_raw: str = "docs", scope_raw: str | None = None) -> dict[str, Any]:
    repo_root, docs_root, scope, scope_display = resolve_roots(
        repo_root_raw, docs_root_raw, scope_raw
    )
    files = collect_markdown_files(scope, docs_root)
    inventory: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    signals: dict[str, list[dict[str, Any]]] = {
        "status_terms": [],
        "platform_terms": [],
        "environment_terms": [],
        "long_bullets": [],
        "duplicate_blocks": [],
        "claim_ids": [],
        "inline_path_references": [],
        "path_integrity_findings": [],
        "lifecycle_tables": [],
        "frozen_scope": [],
        "active_plan_release_scope": [],
    }
    all_blocks: list[dict[str, Any]] = []
    active_plans: dict[str, dict[str, Any]] = {}
    source_contexts: dict[str, tuple[list[str], list[dict[str, Any]]]] = {}
    links_by_source: dict[str, list[dict[str, Any]]] = {}

    for path in files:
        text, lines, raw = read_markdown(path)
        repo_path = _relative(path, repo_root)
        relative_to_docs = path.relative_to(docs_root)
        updated_at, latest_body_date = extract_dates(lines)
        headings = extract_headings(lines)
        source_contexts[repo_path] = (lines, headings)
        links, broken_links = extract_links(lines, path, repo_root)
        links_by_source[repo_path] = links
        inline_paths = extract_inline_path_references(lines, path, repo_root, docs_root)
        path_integrity_findings = extract_path_integrity_findings(
            lines, path, repo_root, docs_root
        )
        term_signals = extract_term_signals(lines, repo_path)
        blocks, long_bullets = extract_blocks(lines, repo_path)
        claim_ids = extract_claim_ids(lines, repo_path)
        lifecycle_tables = extract_lifecycle_tables(lines, repo_path)
        unique_path_references = sorted({item["raw"] for item in inline_paths})

        frozen_occurrences: list[dict[str, Any]] = []
        release_scopes: list[dict[str, Any]] = []
        release_blocking: list[dict[str, Any]] = []
        in_fence = False
        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if DOCS_REVIEW_PROTOCOL_LEAK_RE.search(line):
                findings.append(
                    {
                        "type": "docs_review_protocol_leak",
                        "file": repo_path,
                        "line": number,
                        "message": (
                            "target docs contain docs-review-only claim or audit metadata"
                        ),
                        "evidence": line.strip(),
                    }
                )
            if FROZEN_SCOPE_RE.search(line):
                frozen_occurrences.append(
                    {"file": repo_path, "line": number, "text": line.strip()}
                )
            for match in RELEASE_SCOPE_RE.finditer(line):
                release_scopes.append(
                    {"file": repo_path, "line": number, "value": match.group(1).lower()}
                )
            for match in RELEASE_BLOCKING_RE.finditer(line):
                release_blocking.append(
                    {"file": repo_path, "line": number, "value": match.group(1).lower()}
                )

        inventory.append(
            {
                "path": repo_path,
                "line_count": len(lines),
                "size_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "updated_at": updated_at,
                "latest_body_date": latest_body_date,
                "headings": headings,
                "internal_links": links,
                "semantic_metrics": {
                    "line_count": len(lines),
                    "heading_count": len(headings),
                    "path_reference_count": len(unique_path_references),
                },
            }
        )
        signals["status_terms"].extend(term_signals["status"])
        signals["platform_terms"].extend(term_signals["platform"])
        signals["environment_terms"].extend(term_signals["environment"])
        signals["long_bullets"].extend(long_bullets)
        signals["claim_ids"].extend(claim_ids)
        signals["inline_path_references"].extend(
            {"file": repo_path, **item} for item in inline_paths
        )
        signals["path_integrity_findings"].extend(path_integrity_findings)
        findings.extend(path_integrity_findings)
        signals["lifecycle_tables"].extend(lifecycle_tables)
        signals["frozen_scope"].extend(frozen_occurrences)
        signals["active_plan_release_scope"].extend(release_scopes)
        all_blocks.extend(blocks)

        if _is_active_plan(relative_to_docs):
            active_plans[repo_path] = {
                "release_scope": release_scopes,
                "release_blocking": release_blocking,
            }

        for link in broken_links:
            findings.append(
                {
                    "type": "broken_internal_link",
                    "file": repo_path,
                    "line": link["line"],
                    "message": f"internal link target does not exist: {link['target']}",
                    "evidence": link,
                }
            )
        for link in links:
            label = link.get("label", "")
            resolved_path = link.get("resolved_path") or ""
            link_line = lines[link["line"] - 1] if link["line"] <= len(lines) else ""
            if (
                "/active/" in label
                and "/completed/" in resolved_path
                and not HISTORICAL_CONTEXT_RE.search(link_line)
            ):
                findings.append(
                    {
                        "type": "stale_link_label_path",
                        "file": repo_path,
                        "line": link["line"],
                        "message": "link label names an active path but target resolves under completed",
                        "evidence": link,
                    }
                )
        for reference in inline_paths:
            if (
                (reference["navigation_context"] or reference["is_markdown_path"])
                and not reference["exists"]
                and not reference["historical_context"]
            ):
                finding_type = (
                    "broken_navigation_path"
                    if reference["navigation_context"]
                    else "broken_inline_markdown_reference"
                )
                findings.append(
                    {
                        "type": finding_type,
                        "file": repo_path,
                        "line": reference["line"],
                        "message": (
                            "inline Markdown reference does not resolve: "
                            f"{reference['raw']}"
                        ),
                        "evidence": reference,
                    }
                )
            if (
                _is_completed_plan(relative_to_docs)
                and not reference["historical_context"]
                and re.search(r"(?:^|/)plans/active/", reference["raw"])
            ):
                findings.append(
                    {
                        "type": "completed_plan_active_navigation",
                        "file": repo_path,
                        "line": reference["line"],
                        "message": "completed plan navigation still points to plans/active",
                        "evidence": reference,
                    }
                )
        if updated_at and not updated_at["valid"]:
            findings.append(
                {
                    "type": "invalid_header_date",
                    "file": repo_path,
                    "line": updated_at["line"],
                    "message": f"header updated_at is not a valid date: {updated_at['value']}",
                    "evidence": updated_at,
                }
            )
        elif updated_at and latest_body_date:
            header_date = valid_iso_date(updated_at["value"])
            body_date = valid_iso_date(latest_body_date["value"])
            if header_date and body_date and header_date < body_date:
                findings.append(
                    {
                        "type": "stale_header_date",
                        "file": repo_path,
                        "line": updated_at["line"],
                        "message": "header updated_at is earlier than the latest body date",
                        "evidence": {"updated_at": updated_at, "latest_body_date": latest_body_date},
                    }
                )
        candidate_findings = _candidate_findings(lines, repo_path, relative_to_docs)
        findings.extend(candidate_findings)
        if _is_completed_plan(relative_to_docs):
            archive_notices = [
                {"line": number, "text": line.strip()}
                for number, line in enumerate(lines[:40], start=1)
                if ARCHIVE_OVERLAY_NOTICE_RE.search(line)
            ]
            stale_lines = [
                finding
                for finding in candidate_findings
                if finding["type"] == "completed_plan_stale_lifecycle"
            ]
            if archive_notices and stale_lines:
                findings.append(
                    {
                        "type": "completed_plan_header_only_archive_overlay",
                        "file": repo_path,
                        "line": archive_notices[0]["line"],
                        "message": (
                            "file-level archive notice does not scope stale present-tense "
                            "claims in the body"
                        ),
                        "evidence": {
                            "archive_notice": archive_notices[0],
                            "stale_body_lines": [item["line"] for item in stale_lines],
                        },
                    }
                )

    active_index_findings = _active_plan_index_findings(
        docs_root=docs_root,
        repo_root=repo_root,
        scope=scope,
        active_plans=active_plans,
        links_by_source=links_by_source,
        source_contexts=source_contexts,
    )
    findings.extend(active_index_findings)

    if signals["frozen_scope"]:
        frozen_evidence = signals["frozen_scope"][0]
        for repo_path, metadata in sorted(active_plans.items()):
            if not metadata["release_scope"]:
                findings.append(
                    {
                        "type": "active_plan_release_scope_missing",
                        "file": repo_path,
                        "line": 1,
                        "message": "release scope is frozen but active plan has no release_scope",
                        "evidence": {"frozen_scope": frozen_evidence},
                    }
                )
            else:
                for marker in metadata["release_scope"]:
                    if marker["value"] not in VALID_RELEASE_SCOPES:
                        findings.append(
                            {
                                "type": "active_plan_release_scope_invalid",
                                "file": repo_path,
                                "line": marker["line"],
                                "message": "active plan has an unsupported release_scope value",
                                "evidence": marker,
                            }
                        )
            if not metadata["release_blocking"]:
                findings.append(
                    {
                        "type": "active_plan_release_blocking_missing",
                        "file": repo_path,
                        "line": 1,
                        "message": "release scope is frozen but active plan has no release_blocking value",
                        "evidence": {"frozen_scope": frozen_evidence},
                    }
                )
            else:
                for marker in metadata["release_blocking"]:
                    if marker["value"] not in VALID_RELEASE_BLOCKING:
                        findings.append(
                            {
                                "type": "active_plan_release_blocking_invalid",
                                "file": repo_path,
                                "line": marker["line"],
                                "message": "active plan has an unsupported release_blocking value",
                                "evidence": marker,
                            }
                        )

    grouped_blocks: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in all_blocks:
        grouped_blocks[block["normalized"]].append(block)
    for normalized, occurrences in sorted(grouped_blocks.items()):
        if len(occurrences) < 2:
            continue
        public_occurrences = [
            {
                key: value
                for key, value in item.items()
                if key not in {"normalized", "row_fingerprints"}
            }
            for item in occurrences
        ]
        duplicate = {
            "match_kind": "exact_normalized",
            "normalized_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "normalized_length": len(normalized),
            "occurrences": public_occurrences,
        }
        signals["duplicate_blocks"].append(duplicate)
        first = public_occurrences[0]
        findings.append(
            {
                "type": "duplicate_normalized_block",
                "file": first["file"],
                "line": first["line"],
                "message": f"normalized prose/table block appears {len(occurrences)} times",
                "evidence": duplicate,
            }
        )

    table_blocks = [block for block in all_blocks if block["kind"] == "table"]
    for left_index, left in enumerate(table_blocks):
        left_rows = set(left.get("row_fingerprints", []))
        for right in table_blocks[left_index + 1 :]:
            if left["normalized"] == right["normalized"]:
                continue
            right_rows = set(right.get("row_fingerprints", []))
            shared = left_rows & right_rows
            denominator = max(len(left_rows), len(right_rows))
            if len(shared) < MIN_TABLE_ROWS or denominator == 0:
                continue
            similarity = len(shared) / denominator
            if similarity < NEAR_TABLE_ROW_OVERLAP:
                continue
            occurrences = [
                {
                    key: value
                    for key, value in item.items()
                    if key not in {"normalized", "row_fingerprints"}
                }
                for item in (left, right)
            ]
            duplicate = {
                "match_kind": "near_table_rows",
                "similarity": round(similarity, 4),
                "shared_rows": len(shared),
                "occurrences": occurrences,
            }
            signals["duplicate_blocks"].append(duplicate)
            findings.append(
                {
                    "type": "duplicate_near_table_block",
                    "file": left["file"],
                    "line": left["line"],
                    "message": "Markdown tables share most substantive rows",
                    "evidence": duplicate,
                }
            )

    findings.sort(key=lambda item: (item.get("file", ""), item.get("line", 0), item["type"]))
    fingerprint_counts: dict[str, int] = defaultdict(int)
    for index, finding in enumerate(findings, start=1):
        finding["finding_id"] = f"DRS-{index:04d}"
        stable_evidence = _without_volatile_locations(finding.get("evidence"))
        source_lines, source_headings = source_contexts.get(
            finding.get("file", ""), ([], [])
        )
        source_line = finding.get("line")
        if not isinstance(source_line, int) or source_line < 1:
            source_line = 1
        source_text = (
            source_lines[source_line - 1].strip()
            if source_line <= len(source_lines)
            else ""
        )
        section = section_for_line(source_headings, source_line)
        source_material = json.dumps(
            {
                "type": finding.get("type"),
                "file": finding.get("file"),
                "line": source_line,
                "source_text": source_text,
                "section": section,
                "evidence": stable_evidence,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        finding["source_fingerprint"] = hashlib.sha256(
            source_material.encode("utf-8")
        ).hexdigest()
        finding["section"] = section
        raw_fingerprint = json.dumps(
            {
                "type": finding.get("type"),
                "file": finding.get("file"),
                "evidence": stable_evidence,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()[:20]
        fingerprint_counts[digest] += 1
        finding["finding_key"] = f"DRSK-{digest}-{fingerprint_counts[digest]:02d}"

    docs_root_display = _relative(docs_root, repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "scanner_manifest": {
            "schema_version": SCHEMA_VERSION,
            "scanner_sha256": SCANNER_SHA256,
        },
        "tool": "docs-review.scan",
        "repo_root": str(repo_root),
        "docs_root": docs_root_display,
        "scope": scope_display or docs_root_display,
        "summary": {
            "markdown_files": len(inventory),
            "findings": len(findings),
            "broken_internal_links": sum(
                1 for item in findings if item["type"] == "broken_internal_link"
            ),
            "duplicate_blocks": len(signals["duplicate_blocks"]),
            "broken_navigation_paths": sum(
                1
                for item in findings
                if item["type"]
                in {"broken_navigation_path", "broken_inline_markdown_reference"}
            ),
            "machine_specific_paths": sum(
                1
                for item in findings
                if item["type"] == "machine_specific_absolute_path"
            ),
            "missing_repository_paths": sum(
                1
                for item in findings
                if item["type"]
                in {
                    "missing_repository_path_reference",
                    "missing_docs_index_directory",
                }
            ),
            "completed_plan_stale_lifecycle": sum(
                1 for item in findings if item["type"] == "completed_plan_stale_lifecycle"
            ),
            "release_scope_gaps": sum(
                1
                for item in findings
                if item["type"]
                in {"active_plan_release_scope_missing", "active_plan_release_blocking_missing"}
            ),
            "active_plan_index_gaps": sum(
                1
                for item in findings
                if item["type"]
                in {
                    "active_plan_index_missing",
                    "active_plan_missing_from_index",
                    "active_plan_count_contradiction",
                }
            ),
        },
        "inventory": inventory,
        "signals": signals,
        "findings": findings,
        "errors": [],
    }


def error_payload(message: str, tool: str = "docs-review.scan") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scanner_manifest": {
            "schema_version": SCHEMA_VERSION,
            "scanner_sha256": SCANNER_SHA256,
        },
        "tool": tool,
        "summary": {"findings": 0, "errors": 1},
        "inventory": [],
        "signals": {},
        "findings": [],
        "errors": [{"message": message}],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument(
        "--docs-root", default="docs", help="Repo-relative docs root (default: docs)"
    )
    parser.add_argument(
        "--scope", help="Optional repo- or docs-relative Markdown file/directory scope"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        payload = scan_docs(args.repo_root, args.docs_root, args.scope)
        code = 1 if payload["findings"] else 0
    except (DocsReviewError, FileNotFoundError, RuntimeError, OSError) as exc:
        payload = error_payload(str(exc))
        code = 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
