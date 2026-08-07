#!/usr/bin/env python3
"""Prepare bounded, deterministic shard inputs for a docs closure audit.

The script deliberately does not read a business project's documents beyond the exact
Markdown files named by the clause manifest.  It validates those declarations before
making any subagent dispatch payloads.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
DEFAULT_MAX_BATCH_BYTES = 120_000
DEFAULT_MAX_BATCH_LINES = 2_000


class PrepareError(Exception):
    """An invalid CLI argument, path, or JSON input."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PrepareError(message)


def canonical_json(value: Any) -> bytes:
    """Return the single serialization used by all report hashes."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def add_finding(
    findings: list[dict[str, Any]], finding_type: str, message: str, **extra: Any
) -> None:
    findings.append({"type": finding_type, "message": message, **extra})


def error_payload(message: str) -> dict[str, Any]:
    return {
        "audit_schema_version": SCHEMA_VERSION,
        "tool": "docs-review.prepare_closure_audit",
        "audit_id": None,
        "clause_manifest_sha256": None,
        "repository_root": None,
        "budget": {},
        "coverage": {"full_read_files": [], "targeted_search_files": []},
        "batches": [],
        "synthesis_role_file": None,
        "findings": [],
        "errors": [{"type": "input_error", "message": message}],
    }


def existing_directory(raw_path: str, label: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_dir():
        raise PrepareError(f"{label} must be an existing directory: {raw_path}")
    return path.resolve()


def existing_file(raw_path: str, label: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_file():
        raise PrepareError(f"{label} must be an existing file: {raw_path}")
    return path.resolve()


def load_clauses(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrepareError(f"cannot read clauses JSON {path}: {exc}") from exc
    clauses = payload.get("verification_clauses") if isinstance(payload, dict) else payload
    if not isinstance(clauses, list) or not clauses:
        raise PrepareError(
            "clauses JSON must be a non-empty list or an object with verification_clauses"
        )
    if not all(isinstance(clause, dict) for clause in clauses):
        raise PrepareError("every verification clause must be an object")
    return clauses


def load_plan_scope(path: Path) -> tuple[set[str], set[str]]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrepareError(f"cannot read plan JSON {path}: {exc}") from exc
    if not isinstance(plan, dict) or plan.get("plan_schema_version") != 3:
        raise PrepareError("plan file must use plan_schema_version 3")
    manifest = plan.get("audit_scope_manifest")
    approved = plan.get("approved_files")
    if not isinstance(manifest, dict) or not isinstance(approved, list):
        raise PrepareError("plan file needs audit_scope_manifest and approved_files")
    expected: set[str] = set()
    for raw_path, entry in manifest.items():
        if not isinstance(raw_path, str) or not isinstance(entry, dict):
            raise PrepareError("invalid audit_scope_manifest entry in plan file")
        if entry.get("post_state") == "present":
            expected.add(Path(raw_path).as_posix())
        elif entry.get("post_state") != "absent":
            raise PrepareError("audit scope post_state must be present or absent")
    approved_paths = {
        Path(path).as_posix() for path in approved if isinstance(path, str)
    }
    if len(approved_paths) != len(approved):
        raise PrepareError("approved_files must contain only path strings")
    return expected, approved_paths


def validate_plan_bound_coverage(
    clauses: list[dict[str, Any]],
    targets: dict[str, dict[str, Any]],
    expected_paths: set[str],
    approved_paths: set[str],
    findings: list[dict[str, Any]],
) -> None:
    actual_paths = set(targets)
    if actual_paths != expected_paths:
        add_finding(
            findings,
            "plan_audit_scope_coverage_mismatch",
            "closure coverage must exactly match post-present audit_scope_manifest paths",
            missing=sorted(expected_paths - actual_paths),
            extra=sorted(actual_paths - expected_paths),
        )
    global_clauses = [clause for clause in clauses if clause.get("kind") == "global"]
    if len(global_clauses) != 1:
        add_finding(
            findings,
            "global_clause_count_invalid",
            "closure input must contain exactly one global clause",
            actual=len(global_clauses),
        )
    else:
        global_paths = {
            target.get("path")
            for target in global_clauses[0].get("coverage_targets", [])
            if isinstance(target, dict) and isinstance(target.get("path"), str)
        }
        if global_paths != expected_paths:
            add_finding(
                findings,
                "global_clause_scope_mismatch",
                "the global clause must enumerate the complete post-apply audit scope",
                missing=sorted(expected_paths - global_paths),
                extra=sorted(global_paths - expected_paths),
            )
    for path in sorted((approved_paths & expected_paths) & actual_paths):
        if targets[path].get("obligation") != "full_read":
            add_finding(
                findings,
                "approved_file_not_full_read",
                "every post-present approved edit path requires full_read closure coverage",
                file=path,
            )


def safe_target_path(repo_root: Path, path_value: Any) -> tuple[str, Path]:
    if not isinstance(path_value, str) or not path_value:
        raise PrepareError("coverage target path must be a non-empty repo-relative .md path")
    relative = Path(path_value)
    if relative.is_absolute() or ".." in relative.parts or not path_value.lower().endswith(".md"):
        raise PrepareError(f"coverage target path must be repo-relative .md: {path_value}")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise PrepareError(f"coverage target path escapes repository root: {path_value}") from exc
    if not resolved.is_file():
        raise PrepareError(f"coverage target file does not exist: {path_value}")
    # Preserve the portable slash spelling in dispatch data.
    return relative.as_posix(), resolved


def line_count(data: bytes) -> int:
    return len(data.splitlines())


def validate_and_aggregate(
    clauses: list[dict[str, Any]], repo_root: Path, findings: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """Validate target declarations and aggregate their strongest obligations."""
    targets: dict[str, dict[str, Any]] = {}
    path_clause_ids: dict[str, set[str]] = {}
    for index, clause in enumerate(clauses):
        clause_id = clause.get("clause_id")
        if not isinstance(clause_id, str) or not clause_id:
            add_finding(
                findings,
                "clause_id_missing",
                "every verification clause needs a non-empty clause_id",
                clause_index=index,
            )
            clause_id = f"__clause_index_{index}"
        raw_targets = clause.get("coverage_targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            add_finding(
                findings,
                "coverage_targets_missing",
                "every verification clause needs non-empty coverage_targets",
                clause_id=clause_id,
            )
            continue
        for target in raw_targets:
            if not isinstance(target, dict):
                add_finding(
                    findings,
                    "invalid_coverage_target",
                    "coverage target must be an object",
                    clause_id=clause_id,
                )
                continue
            path_value = target.get("path")
            try:
                path, absolute_path = safe_target_path(repo_root, path_value)
            except PrepareError:
                # A manifest pointing outside the declared root is an input/path error,
                # not a condition an auditor could independently verify.
                raise
            obligation = target.get("obligation")
            if obligation not in {"full_read", "targeted_search"}:
                add_finding(
                    findings,
                    "invalid_coverage_obligation",
                    "coverage obligation must be full_read or targeted_search",
                    clause_id=clause_id,
                    path=path,
                )
                continue
            expected_hash = target.get("sha256")
            expected_lines = target.get("line_count")
            if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
                char not in "0123456789abcdefABCDEF" for char in expected_hash
            ):
                add_finding(
                    findings,
                    "invalid_coverage_sha256",
                    "coverage target needs a 64-character SHA-256",
                    clause_id=clause_id,
                    path=path,
                )
                continue
            if not isinstance(expected_lines, int) or isinstance(expected_lines, bool) or expected_lines < 0:
                add_finding(
                    findings,
                    "invalid_coverage_line_count",
                    "coverage target line_count must be a non-negative integer",
                    clause_id=clause_id,
                    path=path,
                )
                continue
            try:
                data = absolute_path.read_bytes()
                # A non-UTF-8 markdown target is not usable as an audit input.
                data.decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                add_finding(
                    findings,
                    "coverage_file_unreadable",
                    f"coverage target cannot be read as UTF-8: {exc}",
                    clause_id=clause_id,
                    path=path,
                )
                continue
            actual_hash = sha256(data)
            actual_lines = line_count(data)
            if expected_hash.lower() != actual_hash:
                add_finding(
                    findings,
                    "coverage_sha256_mismatch",
                    "coverage target SHA-256 does not match the current file",
                    clause_id=clause_id,
                    path=path,
                    expected=expected_hash.lower(),
                    actual=actual_hash,
                )
                continue
            if expected_lines != actual_lines:
                add_finding(
                    findings,
                    "coverage_line_count_mismatch",
                    "coverage target line_count does not match the current file",
                    clause_id=clause_id,
                    path=path,
                    expected=expected_lines,
                    actual=actual_lines,
                )
                continue
            entry = targets.setdefault(
                path,
                {
                    "path": path,
                    "sha256": actual_hash,
                    "line_count": actual_lines,
                    "bytes": len(data),
                    "obligation": obligation,
                },
            )
            if obligation == "full_read":
                entry["obligation"] = "full_read"
            path_clause_ids.setdefault(path, set()).add(clause_id)
    return targets, path_clause_ids


def coverage_view(targets: dict[str, dict[str, Any]], obligation: str) -> list[dict[str, Any]]:
    return [
        {
            "path": entry["path"],
            "sha256": entry["sha256"],
            "line_count": entry["line_count"],
            "bytes": entry["bytes"],
        }
        for entry in sorted(targets.values(), key=lambda item: item["path"])
        if entry["obligation"] == obligation
    ]


def make_batches(
    targets: dict[str, dict[str, Any]],
    path_clause_ids: dict[str, set[str]],
    max_bytes: int,
    max_lines: int,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full = [entry for entry in targets.values() if entry["obligation"] == "full_read"]
    for entry in full:
        if entry["bytes"] > max_bytes or entry["line_count"] > max_lines:
            add_finding(
                findings,
                "oversized_full_read_file",
                "full_read file exceeds the per-batch budget",
                path=entry["path"],
                bytes=entry["bytes"],
                line_count=entry["line_count"],
                max_batch_bytes=max_bytes,
                max_batch_lines=max_lines,
            )
    if findings:
        return []

    batches: list[dict[str, Any]] = []
    for entry in sorted(full, key=lambda item: (-item["bytes"], -item["line_count"], item["path"])):
        chosen: dict[str, Any] | None = None
        for batch in batches:
            if (
                batch["_bytes"] + entry["bytes"] <= max_bytes
                and batch["_lines"] + entry["line_count"] <= max_lines
            ):
                chosen = batch
                break
        if chosen is None:
            chosen = {
                "batch_id": f"DRB-{len(batches) + 1:03d}",
                "full_read_files": [],
                "targeted_search_files": [],
                "_bytes": 0,
                "_lines": 0,
                "_clause_ids": set(),
            }
            batches.append(chosen)
        chosen["full_read_files"].append(entry["path"])
        chosen["_bytes"] += entry["bytes"]
        chosen["_lines"] += entry["line_count"]
        chosen["_clause_ids"].update(path_clause_ids[entry["path"]])

    targeted = sorted(
        (entry for entry in targets.values() if entry["obligation"] == "targeted_search"),
        key=lambda item: item["path"],
    )
    if targeted and not batches:
        batches.append(
            {
                "batch_id": "DRB-001",
                "full_read_files": [],
                "targeted_search_files": [],
                "_bytes": 0,
                "_lines": 0,
                "_clause_ids": set(),
            }
        )
    for entry in targeted:
        related = [
            batch
            for batch in batches
            if batch["_clause_ids"] & path_clause_ids[entry["path"]]
        ]
        candidates = related or batches
        chosen = min(
            candidates,
            key=lambda batch: (
                len(batch["targeted_search_files"]),
                batch["_bytes"],
                batch["batch_id"],
            ),
        )
        chosen["targeted_search_files"].append(entry["path"])
        chosen["_clause_ids"].update(path_clause_ids[entry["path"]])
    return batches


def repo_relative_markdown(value: Any, repo_root: Path) -> str | None:
    """Return a canonical repo-relative Markdown path, if ``value`` names one."""
    if not isinstance(value, str) or not value.lower().endswith(".md"):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(repo_root)
        except (OSError, ValueError):
            return ""
    if ".." in candidate.parts:
        return ""
    return candidate.as_posix()


def repo_relative_scope(value: Any, repo_root: Path) -> str | None:
    """Normalize a possible repository scope without requiring it to exist."""
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(repo_root)
        except (OSError, ValueError):
            return None
    if ".." in candidate.parts:
        return None
    normalized = candidate.as_posix().rstrip("/")
    return normalized or "."


def path_is_within_scope(path: str, scope: str) -> bool:
    return scope == "." or path == scope or path.startswith(f"{scope}/")


def prune_path_values(
    value: Any,
    selected_paths: set[str],
    all_coverage_paths: set[str],
    repo_root: Path,
    *,
    materialize_directories: bool,
) -> Any:
    """Prune document references while retaining non-document semantic values.

    A broad repository scope is never copied when it covers a manifest Markdown
    target.  Instead, it becomes the exact selected target paths beneath it.
    """
    if not isinstance(value, list):
        return copy.deepcopy(value)
    result: list[Any] = []
    for item in value:
        if isinstance(item, str):
            markdown_path = repo_relative_markdown(item, repo_root)
            if markdown_path is not None:
                if markdown_path in selected_paths:
                    result.append(markdown_path)
                elif markdown_path == "" and Path(item).is_absolute():
                    # An explicitly named external Markdown evidence file is not a
                    # repository docs target and therefore remains a support path.
                    result.append(copy.deepcopy(item))
                continue
            if materialize_directories:
                scope = repo_relative_scope(item, repo_root)
                covered = (
                    sorted(
                        path
                        for path in all_coverage_paths
                        if scope is not None and path_is_within_scope(path, scope)
                    )
                    if scope is not None
                    else []
                )
                if covered:
                    result.extend(path for path in covered if path in selected_paths)
                    continue
            # Exact code/evidence paths and non-path semantic subjects survive.
            result.append(copy.deepcopy(item))
            continue
        if isinstance(item, dict):
            path_value = item.get("path", item.get("source_path"))
            markdown_path = repo_relative_markdown(path_value, repo_root)
            if markdown_path is not None:
                if markdown_path in selected_paths:
                    cloned = copy.deepcopy(item)
                    if "path" in cloned:
                        cloned["path"] = markdown_path
                    elif "source_path" in cloned:
                        cloned["source_path"] = markdown_path
                    result.append(cloned)
                elif (
                    markdown_path == ""
                    and isinstance(path_value, str)
                    and Path(path_value).is_absolute()
                ):
                    result.append(copy.deepcopy(item))
                continue
        result.append(copy.deepcopy(item))

    deduplicated: list[Any] = []
    seen: set[bytes] = set()
    for item in result:
        marker = canonical_json(item)
        if marker not in seen:
            deduplicated.append(item)
            seen.add(marker)
    return deduplicated


def artifact_matches_selected(
    entry: Any, selected_paths: set[str], repo_root: Path
) -> bool:
    if not isinstance(entry, dict):
        return False
    for field in ("source_path", "current_path", "path"):
        markdown_path = repo_relative_markdown(entry.get(field), repo_root)
        if markdown_path in selected_paths:
            return True
    return False


def prune_clause_to_batch(
    clause: dict[str, Any],
    selected_paths: set[str],
    all_coverage_paths: set[str],
    repo_root: Path,
) -> dict[str, Any]:
    """Copy a clause while bounding all document-bearing fields to one shard."""
    cloned = copy.deepcopy(clause)
    for field in (
        "changed_files",
        "approved_edit_scope",
        "required_consumers",
        "semantic_neighbors",
    ):
        if field in cloned:
            cloned[field] = prune_path_values(
                cloned[field],
                selected_paths,
                all_coverage_paths,
                repo_root,
                materialize_directories=True,
            )
    if "audit_read_scope" in cloned:
        cloned["audit_read_scope"] = prune_path_values(
            cloned["audit_read_scope"],
            selected_paths,
            all_coverage_paths,
            repo_root,
            materialize_directories=True,
        )
    if "authority_and_evidence" in cloned:
        cloned["authority_and_evidence"] = prune_path_values(
            cloned["authority_and_evidence"],
            selected_paths,
            all_coverage_paths,
            repo_root,
            materialize_directories=False,
        )
    fact_scope = cloned.get("fact_scope")
    if isinstance(fact_scope, dict) and "subjects" in fact_scope:
        fact_scope["subjects"] = prune_path_values(
            fact_scope["subjects"],
            selected_paths,
            all_coverage_paths,
            repo_root,
            materialize_directories=False,
        )
    artifacts = cloned.get("artifacts")
    if isinstance(artifacts, dict):
        for stage in ("before", "after"):
            entries = artifacts.get(stage)
            if isinstance(entries, list):
                artifacts[stage] = [
                    copy.deepcopy(entry)
                    for entry in entries
                    if artifact_matches_selected(entry, selected_paths, repo_root)
                ]
    return cloned


def dispatch_clauses(
    clauses: list[dict[str, Any]],
    selected_paths: set[str],
    aggregated_targets: dict[str, dict[str, Any]],
    repo_root: Path,
    audit_id: str,
    batch_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for clause in clauses:
        raw_targets = clause.get("coverage_targets")
        if not isinstance(raw_targets, list):
            continue
        selected: list[dict[str, Any]] = []
        seen_paths: set[str] = set()
        for target in raw_targets:
            if not isinstance(target, dict) or target.get("path") not in selected_paths:
                continue
            path = target["path"]
            if path in seen_paths:
                continue
            # The aggregate obligation is authoritative: an individual clause may
            # request a weaker search, but it must not dilute a required full read.
            normalized = copy.deepcopy(target)
            normalized["obligation"] = aggregated_targets[path]["obligation"]
            selected.append(normalized)
            seen_paths.add(path)
        if not selected:
            continue
        cloned = prune_clause_to_batch(
            clause,
            selected_paths,
            set(aggregated_targets),
            repo_root,
        )
        cloned["coverage_targets"] = selected
        cloned["audit_binding"] = {
            "audit_id": audit_id,
            "stage": "shard",
            "batch_id": batch_id,
        }
        result.append(cloned)
    return result


def unbound_clauses(clauses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return semantic clauses without their self-describing report binding."""
    result = copy.deepcopy(clauses)
    for clause in result:
        clause.pop("audit_binding", None)
    return result


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = existing_directory(args.repo_root, "repo root")
    clauses_path = existing_file(args.clauses_file, "clauses file")
    plan_path = existing_file(args.plan_file, "plan file")
    shard_role = existing_file(args.shard_role_file, "shard role file")
    synthesis_role = existing_file(args.synthesis_role_file, "synthesis role file")
    clauses = load_clauses(clauses_path)
    expected_scope, approved_paths = load_plan_scope(plan_path)
    manifest_hash = sha256(canonical_json(clauses))
    audit_id = f"DRA-{manifest_hash[:16].upper()}"
    findings: list[dict[str, Any]] = []
    targets, path_clause_ids = validate_and_aggregate(clauses, repo_root, findings)
    validate_plan_bound_coverage(
        clauses, targets, expected_scope, approved_paths, findings
    )
    batches = make_batches(
        targets,
        path_clause_ids,
        args.max_batch_bytes,
        args.max_batch_lines,
        findings,
    )
    if findings:
        batches = []
    else:
        for batch in batches:
            selected_paths = set(batch["full_read_files"]) | set(batch["targeted_search_files"])
            dispatch = {
                "role_file": str(shard_role),
                "verification_clauses": dispatch_clauses(
                    clauses,
                    selected_paths,
                    targets,
                    repo_root,
                    audit_id,
                    batch["batch_id"],
                ),
            }
            batch_manifest_hash = sha256(
                canonical_json(unbound_clauses(dispatch["verification_clauses"]))
            )
            for clause in dispatch["verification_clauses"]:
                clause["audit_binding"]["clause_manifest_sha256"] = batch_manifest_hash
            batch["dispatch"] = dispatch
            batch["clause_manifest_sha256"] = batch_manifest_hash
            batch["input_sha256"] = sha256(canonical_json(dispatch))
            batch["reuse_key"] = sha256(
                canonical_json(
                    {
                        "role_file_sha256": sha256(shard_role.read_bytes()),
                        "verification_clauses": unbound_clauses(
                            dispatch["verification_clauses"]
                        ),
                    }
                )
            )
            del batch["_bytes"]
            del batch["_lines"]
            del batch["_clause_ids"]
    return {
        "audit_schema_version": SCHEMA_VERSION,
        "tool": "docs-review.prepare_closure_audit",
        "audit_id": audit_id,
        "clause_manifest_sha256": manifest_hash,
        "repository_root": str(repo_root),
        "budget": {
            "max_batch_bytes": args.max_batch_bytes,
            "max_batch_lines": args.max_batch_lines,
        },
        "coverage": {
            "full_read_files": coverage_view(targets, "full_read"),
            "targeted_search_files": coverage_view(targets, "targeted_search"),
        },
        "batches": batches,
        "synthesis_role_file": str(synthesis_role),
        "findings": findings,
        "errors": [],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--clauses-file", required=True)
    parser.add_argument("--plan-file", required=True)
    parser.add_argument("--shard-role-file", required=True)
    parser.add_argument("--synthesis-role-file", required=True)
    parser.add_argument("--max-batch-bytes", type=int, default=DEFAULT_MAX_BATCH_BYTES)
    parser.add_argument("--max-batch-lines", type=int, default=DEFAULT_MAX_BATCH_LINES)
    args = parser.parse_args(argv)
    if args.max_batch_bytes <= 0:
        raise PrepareError("--max-batch-bytes must be greater than zero")
    if args.max_batch_lines <= 0:
        raise PrepareError("--max-batch-lines must be greater than zero")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        payload = build_report(parse_args(argv))
    except PrepareError as exc:
        print(json.dumps(error_payload(str(exc)), ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 1 if payload["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
