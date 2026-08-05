#!/usr/bin/env python3
"""Validate docs-review v2 plans, baselines, approved scope, and post-apply state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from scan_docs import (
    DocsReviewError,
    JsonArgumentParser,
    SCHEMA_VERSION,
    SCANNER_SHA256,
    error_payload,
    resolve_roots,
    scan_docs,
)


PLAN_SCHEMA_VERSION = 2
VALID_PHASES = ("plan", "pre-apply", "post-apply")
READ_ONLY_PHASES = {"plan", "pre-apply"}
VALID_RESOLUTIONS = {"resolved", "unresolved"}
VALID_RISKS = {"high", "medium", "low"}
VALID_VERDICTS = {"consistent", "partially_consistent", "blocked"}
VALID_CLAIM_TYPES = {
    "implementation_fact",
    "data_contract",
    "business_intent",
    "deployment_fact",
    "acceptance_fact",
    "legal_fact",
    "release_fact",
    "documentation_fact",
}
VALID_AUTHORITY_KINDS = {
    "repository_evidence",
    "human_resolution",
    "canonical_contract",
    "deployment_evidence",
    "acceptance_evidence",
    "legal_confirmation",
    "unresolved",
}
VALID_LIFECYCLE_AXES = {
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
}
ENVIRONMENT_BOUND_AXES = {
    "migration_applied",
    "deployed",
    "runtime_smoked",
    "legal_accepted",
    "released",
}
VALID_GROUP_BASIS_KINDS = {
    "repository_evidence",
    "human_resolution",
    "dated_historical_scope",
    "deterministic_rule",
    "unresolved_claim",
}
VALID_FINDING_DISPOSITIONS = {
    "resolve_by_edit",
    "verified_historical",
    "false_positive",
    "retain_unresolved",
}
EXPECTED_POST_STATE = {
    "resolve_by_edit": "absent",
    "verified_historical": "present",
    "false_positive": "present",
    "retain_unresolved": "present",
}
VALID_FALSE_POSITIVE_REASONS = {
    "scanner_pattern_not_semantic",
    "generated_or_example_content",
    "intentionally_external_reference",
    "historical_scope_already_explicit",
    "bounded_scope_exception",
}
VALID_HISTORY_KINDS = {"dated_heading", "dated_sentence"}
VALID_IDENTIFIER_KINDS = {"route", "field", "rpc", "migration", "doc_path"}
VALID_COVERAGE_DISPOSITIONS = {
    "retained",
    "replaced",
    "moved",
    "historical",
    "removed_duplicate",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROTOCOL_TEXT_RE = re.compile(
    r"(?i)(?:\bclaim[_ -]?id\b|\baudit[_ -]?id\b|\bbatch[_ -]?id\b|"
    r"\bDR-[A-Z0-9_-]+\b|稳定锚点)"
)
GENERIC_SEMANTICS_RE = re.compile(
    r"(?i)^(?:resolve|handle|process|fix|edit|remove|update|处理|解决|修改|删除|更新)"
    r"(?:\s+the)?\s*(?:finding|occurrence|issue|文档|条目|问题|该类型)?[。.!]?$"
)
AUDIT_TEMPLATE_SEMANTICS_RE = re.compile(
    r"(?i)(?:\bfinding(?:[_ -]?type)?\b|\boccurrences?\b|\bscanner\b|"
    r"\bresolve_by_edit\b|该类型|此类型|处理(?:本|该)?(?:条|项)?(?:发现|条目|问题))"
)
MIGRATION_SUBJECT_RE = re.compile(r"(?i)(?:\b\d{3,}[_-][\w.-]+|migrations?/[^\s]+\.sql$)")
IDENTIFIER_PATTERNS = {
    "route": re.compile(r"^(?:/|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./:{}?=&-]*$"),
    "field": re.compile(r"^[A-Za-z_][A-Za-z0-9_.\[\]-]*$"),
    "rpc": re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$"),
    "migration": re.compile(r"^(?:[A-Za-z0-9_./-]*\d{3,}[A-Za-z0-9_.-]*\.sql|\d{3,}_[A-Za-z0-9_.-]+)$"),
    "doc_path": re.compile(r"^[A-Za-z0-9_./ \-\u0080-\uffff]+\.md(?:#[A-Za-z0-9_./ \-\u0080-\uffff]+)?$"),
}
MAJOR_REDUCTION_RATIO = 0.60
MAJOR_HEADING_REDUCTION_RATIO = 0.50


def load_plan(path_raw: str) -> dict[str, Any]:
    path = Path(path_raw).expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocsReviewError(f"cannot read plan JSON {path_raw}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocsReviewError("plan JSON must be an object")
    return payload


def normalize_repo_path(raw: str, repo_root: Path, label: str) -> tuple[str, Path]:
    value = Path(raw)
    if value.is_absolute() or any(part == ".." for part in value.parts):
        raise DocsReviewError(f"{label} must be a safe repo-relative path: {raw}")
    resolved = (repo_root / value).resolve(strict=False)
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise DocsReviewError(f"{label} escapes the repository: {raw}") from exc
    return value.as_posix(), resolved


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise DocsReviewError(f"cannot hash file {path}: {exc}") from exc


def add_finding(findings: list[dict[str, Any]], finding_type: str, message: str, **extra: Any) -> None:
    findings.append({"type": finding_type, "message": message, **extra})


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(is_nonempty_string(item) for item in value)
    )


def is_canonical_doc(path: Path, docs_root: Path) -> bool:
    try:
        relative = path.relative_to(docs_root)
    except ValueError:
        return False
    if len(relative.parts) == 1 and relative.name.lower() == "readme.md":
        return True
    first = relative.parts[0].lower() if relative.parts else ""
    if first in {"architecture", "contracts", "domain", "domains", "product"}:
        return True
    return len(relative.parts) == 2 and first == "handoff" and relative.name.lower() == "latest.md"


def validate_reference(
    reference: Any,
    *,
    repo_root: Path,
    baseline: dict[str, Any],
    findings: list[dict[str, Any]],
    group_id: str,
    phase: str,
) -> None:
    if not isinstance(reference, dict):
        add_finding(findings, "invalid_group_reference", "basis reference must be an object", group_id=group_id)
        return
    raw_path = reference.get("path")
    digest = reference.get("sha256")
    proves = reference.get("proves")
    if not is_nonempty_string(raw_path):
        add_finding(findings, "group_reference_path_missing", "basis reference needs a repo-relative path", group_id=group_id)
        return
    normalized, resolved = normalize_repo_path(raw_path, repo_root, "basis reference")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest.lower()):
        add_finding(findings, "group_reference_hash_invalid", "basis reference needs an exact SHA-256", group_id=group_id, file=normalized)
    if not is_nonempty_string(proves) or GENERIC_SEMANTICS_RE.fullmatch(proves.strip()):
        add_finding(findings, "group_reference_proof_missing", "basis reference must state the bounded fact it proves", group_id=group_id, file=normalized)
    if normalized not in baseline:
        add_finding(findings, "group_reference_not_baselined", "every repository evidence file must be included in baseline_manifest", group_id=group_id, file=normalized)
    if phase in READ_ONLY_PHASES:
        if not resolved.is_file():
            add_finding(findings, "group_reference_missing", "basis reference file is missing", group_id=group_id, file=normalized)
        elif isinstance(digest, str) and SHA256_RE.fullmatch(digest.lower()):
            actual = sha256_file(resolved)
            if actual != digest.lower():
                add_finding(findings, "group_reference_drift", "basis reference SHA-256 does not match current evidence", group_id=group_id, file=normalized, expected_sha256=digest.lower(), actual_sha256=actual)


def validate_claims(
    claims: Any, findings: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    claims_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(claims, list):
        add_finding(findings, "missing_plan_claims", "plan must contain a claims list")
        return claims_by_id
    for claim in claims:
        if not isinstance(claim, dict):
            add_finding(findings, "invalid_plan_claim", "each plan claim must be an object")
            continue
        claim_id = claim.get("claim_id")
        if not is_nonempty_string(claim_id):
            add_finding(findings, "missing_claim_id", "each temporary claim needs a claim_id")
            continue
        if claim_id in claims_by_id:
            add_finding(findings, "duplicate_plan_claim_id", "claim_id appears more than once", claim_id=claim_id)
        claims_by_id[claim_id] = claim
        if claim.get("claim_type") not in VALID_CLAIM_TYPES:
            add_finding(findings, "invalid_claim_type", "claim_type must select an evidence route", claim_id=claim_id)
        if claim.get("resolution") not in VALID_RESOLUTIONS:
            add_finding(findings, "claim_without_disposition", "claim resolution must be resolved or unresolved", claim_id=claim_id)
        if claim.get("risk") not in VALID_RISKS:
            add_finding(findings, "invalid_claim_risk", "claim risk must be high, medium, or low", claim_id=claim_id)

        authority = claim.get("authority")
        if not isinstance(authority, dict):
            add_finding(findings, "claim_authority_missing", "claim needs an explicit authority object", claim_id=claim_id)
        else:
            if authority.get("kind") not in VALID_AUTHORITY_KINDS:
                add_finding(findings, "invalid_claim_authority", "authority.kind is unsupported", claim_id=claim_id)
            if not is_nonempty_string(authority.get("resolution_id")):
                add_finding(findings, "authority_resolution_id_missing", "authority needs the exact resolution/evidence identifier", claim_id=claim_id)
            if claim.get("resolution") == "unresolved" and authority.get("kind") != "unresolved":
                add_finding(findings, "unresolved_claim_authority_mismatch", "unresolved claims must use unresolved authority", claim_id=claim_id)

        scope = claim.get("scope")
        if not isinstance(scope, dict):
            add_finding(findings, "claim_scope_missing", "claim needs explicit platform, environment, subject, lifecycle, and date scope", claim_id=claim_id)
            continue
        platforms = scope.get("platforms")
        environments = scope.get("environments")
        subjects = scope.get("subjects")
        axes = scope.get("lifecycle_axes")
        effective_date = scope.get("effective_date")
        if not is_string_list(platforms):
            add_finding(findings, "invalid_claim_platform_scope", "scope.platforms must be a string list", claim_id=claim_id)
        if not is_string_list(environments):
            add_finding(findings, "invalid_claim_environment_scope", "scope.environments must be a string list", claim_id=claim_id)
        if not is_string_list(subjects, allow_empty=False):
            add_finding(findings, "invalid_claim_subject_scope", "scope.subjects must name at least one exact object", claim_id=claim_id)
        if not isinstance(axes, list) or not all(axis in VALID_LIFECYCLE_AXES for axis in axes):
            add_finding(findings, "invalid_claim_lifecycle_scope", "scope.lifecycle_axes contains an unsupported axis", claim_id=claim_id)
            axes = []
        if not isinstance(effective_date, str) or not ISO_DATE_RE.fullmatch(effective_date):
            add_finding(findings, "invalid_claim_effective_date", "scope.effective_date must be YYYY-MM-DD", claim_id=claim_id)
        axes_set = set(axes)
        if axes_set & ENVIRONMENT_BOUND_AXES:
            if not is_string_list(environments, allow_empty=False) or any(value.lower() in {"unknown", "all", "any"} for value in environments if isinstance(value, str)):
                add_finding(findings, "environment_bound_fact_is_ambiguous", "migration/deploy/runtime/legal/release facts need exact target environments", claim_id=claim_id, lifecycle_axes=sorted(axes_set & ENVIRONMENT_BOUND_AXES))
        if "migration_applied" in axes_set and is_string_list(subjects, allow_empty=False):
            if not any(MIGRATION_SUBJECT_RE.search(subject) for subject in subjects):
                add_finding(findings, "migration_subject_is_ambiguous", "migration_applied authority must name the exact migration file or numbered migration", claim_id=claim_id)
    return claims_by_id


def validate_resolution_groups(
    groups: Any,
    *,
    repo_root: Path,
    baseline: dict[str, Any],
    approved: set[str],
    claims_by_id: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
    phase: str,
) -> dict[str, dict[str, Any]]:
    groups_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(groups, list):
        add_finding(findings, "missing_resolution_groups", "plan must contain a resolution_groups list")
        return groups_by_id
    for group in groups:
        if not isinstance(group, dict):
            add_finding(findings, "invalid_resolution_group", "each resolution group must be an object")
            continue
        group_id = group.get("group_id")
        if not is_nonempty_string(group_id):
            add_finding(findings, "resolution_group_id_missing", "resolution group needs a group_id")
            continue
        if group_id in groups_by_id:
            add_finding(findings, "duplicate_resolution_group", "group_id appears more than once", group_id=group_id)
        groups_by_id[group_id] = group
        claim_id = group.get("claim_id")
        if not is_nonempty_string(claim_id) or claim_id not in claims_by_id:
            add_finding(findings, "resolution_group_claim_missing", "resolution group must bind one known claim_id", group_id=group_id, claim_id=claim_id)
        if not is_nonempty_string(group.get("subject")):
            add_finding(findings, "resolution_group_subject_missing", "resolution group needs a bounded business/technical subject", group_id=group_id)
        semantics = group.get("intended_semantics")
        if (
            not is_nonempty_string(semantics)
            or len(semantics.strip()) < 12
            or GENERIC_SEMANTICS_RE.fullmatch(semantics.strip())
            or AUDIT_TEMPLATE_SEMANTICS_RE.search(semantics)
            or PROTOCOL_TEXT_RE.search(semantics)
        ):
            add_finding(findings, "resolution_group_semantics_missing", "resolution group needs the intended post-edit fact, not a handling template", group_id=group_id)

        targets = group.get("target_docs")
        normalized_targets: list[str] = []
        if not is_string_list(targets, allow_empty=False):
            add_finding(findings, "resolution_group_targets_missing", "resolution group needs at least one approved target doc", group_id=group_id)
        else:
            for raw_path in targets:
                normalized, resolved = normalize_repo_path(raw_path, repo_root, "resolution target")
                normalized_targets.append(normalized)
                if normalized not in approved:
                    add_finding(findings, "resolution_group_target_not_approved", "resolution group target must be in approved_files", group_id=group_id, file=normalized)
                if resolved.suffix.lower() != ".md":
                    add_finding(findings, "resolution_group_target_not_markdown", "resolution group targets may contain docs only", group_id=group_id, file=normalized)
        group["_normalized_targets"] = normalized_targets

        basis = group.get("basis")
        if not isinstance(basis, dict):
            add_finding(findings, "resolution_group_basis_missing", "resolution group needs structured evidence, human authority, or unresolved basis", group_id=group_id)
            continue
        kind = basis.get("kind")
        if kind not in VALID_GROUP_BASIS_KINDS:
            add_finding(findings, "invalid_resolution_group_basis", "resolution group basis kind is unsupported", group_id=group_id)
        references = basis.get("references", [])
        if not isinstance(references, list):
            add_finding(findings, "invalid_group_references", "basis.references must be a list", group_id=group_id)
            references = []
        if kind in {"repository_evidence", "dated_historical_scope"} and not references:
            add_finding(findings, "resolution_group_evidence_missing", "this basis kind requires at least one hashed repository reference", group_id=group_id)
        if kind == "human_resolution" and not is_nonempty_string(basis.get("resolution_id")):
            add_finding(findings, "human_resolution_id_missing", "human_resolution basis needs the exact user decision id", group_id=group_id)
        if kind == "deterministic_rule" and not is_nonempty_string(basis.get("rule_id")):
            add_finding(findings, "deterministic_rule_id_missing", "deterministic_rule basis needs a stable rule id", group_id=group_id)
        if kind == "unresolved_claim" and claim_id in claims_by_id and claims_by_id[claim_id].get("resolution") != "unresolved":
            add_finding(findings, "unresolved_basis_claim_resolved", "unresolved_claim basis must bind an unresolved claim", group_id=group_id, claim_id=claim_id)
        for reference in references:
            validate_reference(reference, repo_root=repo_root, baseline=baseline, findings=findings, group_id=group_id, phase=phase)

        if claim_id in claims_by_id and kind == "human_resolution":
            authority = claims_by_id[claim_id].get("authority", {})
            if authority.get("kind") != "human_resolution" or authority.get("resolution_id") != basis.get("resolution_id"):
                add_finding(findings, "human_resolution_authority_mismatch", "group human decision must exactly match the claim authority resolution_id", group_id=group_id, claim_id=claim_id)
    return groups_by_id


def validate_identifier(value: Any, kind: Any) -> bool:
    if kind not in VALID_IDENTIFIER_KINDS or not is_nonempty_string(value):
        return False
    if PROTOCOL_TEXT_RE.search(value):
        return False
    if kind == "doc_path":
        if value != value.strip() or any(
            char.isspace() and char != " " for char in value
        ):
            return False
    elif any(char.isspace() for char in value):
        return False
    return bool(IDENTIFIER_PATTERNS[kind].fullmatch(value))


def validate_coverage_manifest(
    coverage: Any,
    *,
    approved: set[str],
    repo_root: Path,
    docs_root: Path,
    findings: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    coverage_by_file: dict[str, dict[str, Any]] = {}
    if coverage is None:
        coverage = {}
    if not isinstance(coverage, dict):
        add_finding(findings, "invalid_coverage_manifest", "coverage_manifest must be an object keyed by canonical doc path")
        coverage = {}
    for raw_path, entry in coverage.items():
        if not isinstance(raw_path, str):
            add_finding(findings, "invalid_coverage_file", "coverage paths must be strings", file=raw_path)
            continue
        normalized, _ = normalize_repo_path(raw_path, repo_root, "coverage file")
        if normalized not in approved:
            add_finding(findings, "coverage_file_not_approved", "coverage may describe approved docs only", file=normalized)
        if not isinstance(entry, dict):
            add_finding(findings, "invalid_coverage_entry", "coverage entry must be an object", file=normalized)
            continue
        coverage_by_file[normalized] = entry
        baseline_metrics = entry.get("baseline")
        if not isinstance(baseline_metrics, dict):
            add_finding(findings, "missing_coverage_baseline", "coverage entry needs baseline metrics", file=normalized)
        else:
            for metric in ("line_count", "heading_count", "path_reference_count"):
                value = baseline_metrics.get(metric)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    add_finding(findings, "invalid_coverage_baseline_metric", "coverage baseline metrics must be non-negative integers", file=normalized, metric=metric)

        identifiers = entry.get("required_identifiers")
        if not isinstance(identifiers, list):
            add_finding(findings, "invalid_required_identifiers", "required_identifiers must be a list of real technical identifiers", file=normalized)
        else:
            seen_identifiers: set[tuple[str, str]] = set()
            for identifier in identifiers:
                if not isinstance(identifier, dict):
                    add_finding(findings, "invalid_required_identifier", "each required identifier must be an object", file=normalized)
                    continue
                kind = identifier.get("kind")
                value = identifier.get("value")
                if not validate_identifier(value, kind):
                    add_finding(findings, "invalid_required_identifier", "literal coverage is limited to route, field, RPC, migration, and doc path identifiers", file=normalized, kind=kind, value=value)
                if not is_nonempty_string(identifier.get("reason")):
                    add_finding(findings, "required_identifier_reason_missing", "required identifier needs a bounded coverage reason", file=normalized, value=value)
                key = (str(kind), str(value))
                if key in seen_identifiers:
                    add_finding(findings, "duplicate_required_identifier", "required identifier is duplicated", file=normalized, kind=kind, value=value)
                seen_identifiers.add(key)

        semantics = entry.get("semantic_claims")
        if not isinstance(semantics, list):
            add_finding(findings, "invalid_semantic_claims", "semantic_claims must be a list for independent audit", file=normalized)
        else:
            for semantic in semantics:
                if not isinstance(semantic, dict) or not is_nonempty_string(semantic.get("claim_id")) or not is_nonempty_string(semantic.get("meaning")) or not is_nonempty_string(semantic.get("owner")):
                    add_finding(findings, "invalid_semantic_claim", "semantic claims need claim_id, natural-language meaning, and owner", file=normalized)

        removed_claims = entry.get("removed_claims", [])
        if not isinstance(removed_claims, list):
            add_finding(findings, "invalid_removed_claims", "removed_claims must be a list", file=normalized)
        else:
            for removed in removed_claims:
                if not isinstance(removed, dict) or not is_nonempty_string(removed.get("claim_id")) or removed.get("disposition") not in VALID_COVERAGE_DISPOSITIONS:
                    add_finding(findings, "invalid_removed_claim", "removed claim needs claim_id and a valid disposition", file=normalized)
                    continue
                if removed.get("disposition") in {"moved", "historical", "removed_duplicate"} and not is_nonempty_string(removed.get("destination")):
                    add_finding(findings, "removed_claim_destination_missing", "moved/historical/duplicate claims need a destination owner", file=normalized, claim_id=removed.get("claim_id"))
        allow_major = entry.get("allow_major_reduction", False)
        if not isinstance(allow_major, bool):
            add_finding(findings, "invalid_major_reduction_flag", "allow_major_reduction must be boolean", file=normalized)
        if allow_major and not is_nonempty_string(entry.get("reduction_reason")):
            add_finding(findings, "major_reduction_reason_missing", "approved major reduction needs a reason", file=normalized)

    for normalized in sorted(approved):
        _, resolved = normalize_repo_path(normalized, repo_root, "approved file")
        if is_canonical_doc(resolved, docs_root) and normalized not in coverage_by_file:
            add_finding(findings, "canonical_coverage_missing", "approved canonical doc has no coverage manifest entry", file=normalized)
    return coverage_by_file


def historical_scope_matches(
    disposition: dict[str, Any], source: dict[str, Any], repo_root: Path
) -> bool:
    scope = disposition.get("historical_scope")
    if not isinstance(scope, dict) or scope.get("kind") not in VALID_HISTORY_KINDS:
        return False
    if scope.get("path") != source.get("file") or not isinstance(scope.get("line"), int):
        return False
    date = scope.get("date")
    marker = scope.get("marker")
    if not isinstance(date, str) or not ISO_DATE_RE.fullmatch(date) or not is_nonempty_string(marker):
        return False
    try:
        lines = (repo_root / source["file"]).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError, KeyError):
        return False
    line = scope["line"]
    if line < 1 or line > len(lines) or marker not in lines[line - 1] or date not in lines[line - 1]:
        return False
    source_line = source.get("line")
    if not isinstance(source_line, int) or line > source_line:
        return False
    if scope["kind"] == "dated_heading":
        section = source.get("section", {})
        return section.get("heading_line") == line and section.get("heading") == lines[line - 1].lstrip("# ").strip()
    return line == source_line


def validate_finding_dispositions(
    dispositions: Any,
    *,
    scan_payload: dict[str, Any],
    groups_by_id: dict[str, dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
    approved: set[str],
    repo_root: Path,
    findings: list[dict[str, Any]],
    phase: str,
) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    if not isinstance(dispositions, list):
        add_finding(findings, "invalid_finding_dispositions", "finding_dispositions must be a list")
        dispositions = []
    scanned = {
        item.get("finding_key"): item
        for item in scan_payload.get("findings", [])
        if is_nonempty_string(item.get("finding_key"))
    }
    for entry in dispositions:
        if not isinstance(entry, dict):
            add_finding(findings, "invalid_finding_disposition", "each finding disposition must be an object")
            continue
        key = entry.get("finding_key")
        if not is_nonempty_string(key):
            add_finding(findings, "finding_disposition_without_key", "each disposition needs an exact finding_key")
            continue
        if key in by_key:
            add_finding(findings, "duplicate_finding_disposition", "finding_key appears more than once", finding_key=key)
        by_key[key] = entry
        disposition = entry.get("disposition")
        if disposition not in VALID_FINDING_DISPOSITIONS:
            add_finding(findings, "invalid_finding_disposition_value", "unsupported disposition", finding_key=key)
            continue
        if entry.get("expected_post_state") != EXPECTED_POST_STATE[disposition]:
            add_finding(findings, "invalid_expected_post_state", "expected_post_state must match disposition semantics", finding_key=key, disposition=disposition)
        group_id = entry.get("group_id")
        group = groups_by_id.get(group_id)
        if group is None:
            add_finding(findings, "finding_resolution_group_missing", "every finding must bind a structured resolution group", finding_key=key, group_id=group_id)
        source = scanned.get(key)
        if phase in READ_ONLY_PHASES:
            if source is None:
                add_finding(findings, "stale_finding_disposition", "disposition does not match the current baseline scan", finding_key=key)
                continue
            if entry.get("source_fingerprint") != source.get("source_fingerprint"):
                add_finding(findings, "finding_source_fingerprint_mismatch", "disposition fingerprint does not exactly match the scanner finding", finding_key=key, expected=source.get("source_fingerprint"), actual=entry.get("source_fingerprint"))
            if disposition == "resolve_by_edit":
                if source.get("file") not in approved or group is None or source.get("file") not in group.get("_normalized_targets", []):
                    add_finding(findings, "resolve_by_edit_target_mismatch", "resolve_by_edit must bind the finding's approved source doc and intended semantics", finding_key=key, file=source.get("file"), group_id=group_id)
            elif disposition == "verified_historical":
                if not historical_scope_matches(entry, source, repo_root):
                    add_finding(findings, "verified_historical_scope_invalid", "verified_historical needs the nearest dated heading or dated sentence scope", finding_key=key)
            elif disposition == "false_positive":
                if entry.get("reason_code") not in VALID_FALSE_POSITIVE_REASONS:
                    add_finding(findings, "false_positive_reason_invalid", "false_positive needs an explicit supported reason_code", finding_key=key)
                if group is not None and not group.get("basis", {}).get("references"):
                    add_finding(findings, "false_positive_evidence_missing", "false_positive must bind hashed evidence, not a free-text waiver", finding_key=key, group_id=group_id)
            elif disposition == "retain_unresolved":
                claim_id = entry.get("unresolved_claim_id")
                claim = claims_by_id.get(claim_id)
                if claim is None or claim.get("resolution") != "unresolved":
                    add_finding(findings, "unresolved_finding_claim_missing", "retain_unresolved must bind an unresolved claim", finding_key=key, claim_id=claim_id)
                marker = entry.get("business_gap")
                if not isinstance(marker, dict) or marker.get("path") not in approved or not is_nonempty_string(marker.get("marker")) or PROTOCOL_TEXT_RE.search(str(marker.get("marker", ""))):
                    add_finding(findings, "unresolved_business_gap_invalid", "retain_unresolved needs an approved doc and business-readable gap marker without audit protocol text", finding_key=key)

    if phase in READ_ONLY_PHASES:
        for key in sorted(set(scanned) - set(by_key)):
            source = scanned[key]
            add_finding(findings, "scan_finding_without_disposition", "each deterministic finding needs an exact structured disposition", finding_key=key, file=source.get("file"), line=source.get("line"), source_type=source.get("type"))
    else:
        for key, source in sorted(scanned.items()):
            entry = by_key.get(key)
            if entry is None:
                add_finding(findings, "unaccounted_post_apply_finding", "post-apply scan contains an unapproved finding", finding_key=key, file=source.get("file"), line=source.get("line"), source_type=source.get("type"))
            elif entry.get("disposition") == "resolve_by_edit":
                add_finding(findings, "scan_finding_not_resolved", "finding marked resolve_by_edit is still present", finding_key=key, file=source.get("file"), line=source.get("line"), source_type=source.get("type"))

    if phase == "post-apply":
        remaining_keys = set(scanned)
        for key, entry in by_key.items():
            disposition = entry.get("disposition")
            if EXPECTED_POST_STATE.get(disposition) == "present" and key not in remaining_keys:
                add_finding(findings, "retained_finding_missing", "finding approved to remain disappeared; re-review rather than silently treating it as resolved", finding_key=key, disposition=disposition)
    return by_key


def validate_plan(
    plan: dict[str, Any], repo_root: Path, docs_root: Path, scan_payload: dict[str, Any], phase: str
) -> tuple[list[dict[str, Any]], set[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if plan.get("plan_schema_version") != PLAN_SCHEMA_VERSION:
        add_finding(findings, "unsupported_plan_schema", "docs-review v1 plans cannot be applied; restart from Plan Mode with plan_schema_version 2", expected=PLAN_SCHEMA_VERSION, actual=plan.get("plan_schema_version"))
    if plan.get("decision_complete") is not True:
        add_finding(findings, "plan_not_decision_complete", "plan must explicitly be decision_complete before apply")
    scanner_manifest = plan.get("scanner_manifest")
    if not isinstance(scanner_manifest, dict) or scanner_manifest.get("schema_version") != SCHEMA_VERSION or scanner_manifest.get("scanner_sha256") != SCANNER_SHA256:
        add_finding(findings, "scanner_drift", "plan finding keys were produced by a different scanner version", expected=scan_payload.get("scanner_manifest"), actual=scanner_manifest)

    baseline = plan.get("baseline_manifest")
    if not isinstance(baseline, dict) or not baseline:
        add_finding(findings, "missing_baseline_manifest", "plan must contain a non-empty baseline_manifest")
        baseline = {}
    for raw_path, expected_hash in baseline.items():
        if not isinstance(raw_path, str) or not isinstance(expected_hash, str):
            add_finding(findings, "invalid_baseline_entry", "baseline paths and hashes must be strings", file=raw_path)
            continue
        normalized, resolved = normalize_repo_path(raw_path, repo_root, "baseline file")
        expected = expected_hash.lower()
        if not SHA256_RE.fullmatch(expected):
            add_finding(findings, "invalid_baseline_hash", "baseline hash must be SHA-256", file=normalized)
        elif phase in READ_ONLY_PHASES:
            if not resolved.is_file():
                add_finding(findings, "baseline_drift", "baseline file is missing before apply", file=normalized, expected_sha256=expected, actual_sha256=None)
            else:
                actual = sha256_file(resolved)
                if actual != expected:
                    add_finding(findings, "baseline_drift", "baseline file changed before apply", file=normalized, expected_sha256=expected, actual_sha256=actual)

    approved: set[str] = set()
    approved_files = plan.get("approved_files")
    if not isinstance(approved_files, list):
        add_finding(findings, "missing_approved_files", "plan must contain approved_files")
        approved_files = []
    for raw_path in approved_files:
        if not isinstance(raw_path, str):
            add_finding(findings, "invalid_approved_file", "approved paths must be strings", file=raw_path)
            continue
        normalized, resolved = normalize_repo_path(raw_path, repo_root, "approved file")
        try:
            resolved.relative_to(docs_root)
        except ValueError:
            add_finding(findings, "approved_file_outside_docs", "approval may contain docs only", file=normalized)
            continue
        if resolved.suffix.lower() != ".md":
            add_finding(findings, "approved_file_not_markdown", "approved file must be Markdown", file=normalized)
            continue
        if normalized in approved:
            add_finding(findings, "duplicate_approved_file", "approved file appears more than once", file=normalized)
        approved.add(normalized)

    claims_by_id = validate_claims(plan.get("claims"), findings)
    verdict = plan.get("verdict")
    if verdict not in VALID_VERDICTS:
        add_finding(findings, "invalid_verdict", "verdict must be consistent, partially_consistent, or blocked")
    if verdict == "consistent" and any(claim.get("resolution") == "unresolved" for claim in claims_by_id.values()):
        add_finding(findings, "unsafe_consistent_verdict", "consistent cannot retain unresolved claims")
    if phase == "pre-apply" and verdict == "blocked":
        add_finding(findings, "apply_blocked_by_verdict", "a blocked plan cannot enter apply")

    groups_by_id = validate_resolution_groups(plan.get("resolution_groups"), repo_root=repo_root, baseline=baseline, approved=approved, claims_by_id=claims_by_id, findings=findings, phase=phase)
    coverage_by_file = validate_coverage_manifest(plan.get("coverage_manifest"), approved=approved, repo_root=repo_root, docs_root=docs_root, findings=findings)
    dispositions_by_key = validate_finding_dispositions(plan.get("finding_dispositions"), scan_payload=scan_payload, groups_by_id=groups_by_id, claims_by_id=claims_by_id, approved=approved, repo_root=repo_root, findings=findings, phase=phase)
    return findings, approved, claims_by_id, coverage_by_file, dispositions_by_key


def validate_coverage_post_state(
    coverage_by_file: dict[str, dict[str, Any]], scan_payload: dict[str, Any], repo_root: Path, phase: str
) -> list[dict[str, Any]]:
    inventory = {item["path"]: item for item in scan_payload.get("inventory", [])}
    findings: list[dict[str, Any]] = []
    for path, entry in sorted(coverage_by_file.items()):
        item = inventory.get(path)
        if item is None:
            add_finding(findings, "coverage_file_missing", "coverage file is absent from docs inventory", file=path)
            continue
        baseline = entry.get("baseline")
        if not isinstance(baseline, dict):
            continue
        current = item.get("semantic_metrics", {})
        if phase in READ_ONLY_PHASES:
            for metric in ("line_count", "heading_count", "path_reference_count"):
                expected = baseline.get(metric)
                actual = current.get(metric)
                if isinstance(expected, int) and expected != actual:
                    add_finding(findings, "coverage_baseline_mismatch", "coverage metrics do not match the plan baseline", file=path, metric=metric, expected=expected, actual=actual)
            continue
        try:
            content = (repo_root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise DocsReviewError(f"cannot read coverage file {path}: {exc}") from exc
        for identifier in entry.get("required_identifiers", []):
            if isinstance(identifier, dict):
                value = identifier.get("value")
                if is_nonempty_string(value) and value not in content:
                    add_finding(findings, "required_identifier_missing", "required technical identifier is missing after apply", file=path, kind=identifier.get("kind"), value=value)
        if entry.get("allow_major_reduction") is True:
            continue
        thresholds = {"line_count": MAJOR_REDUCTION_RATIO, "heading_count": MAJOR_HEADING_REDUCTION_RATIO, "path_reference_count": MAJOR_REDUCTION_RATIO}
        for metric, ratio in thresholds.items():
            before = baseline.get(metric)
            after = current.get(metric)
            if isinstance(before, int) and before > 0 and isinstance(after, int) and after < before * ratio:
                add_finding(findings, "canonical_coverage_shrink", "canonical coverage dropped beyond the approved threshold", file=path, metric=metric, baseline=before, current=after, threshold=ratio)
    return findings


def validate_changed_files(changed_raw: list[str], repo_root: Path, docs_root: Path, approved: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    changed: list[str] = []
    for raw_path in changed_raw:
        normalized, resolved = normalize_repo_path(raw_path, repo_root, "changed file")
        try:
            resolved.relative_to(docs_root)
        except ValueError:
            add_finding(findings, "changed_file_outside_docs", "apply changed a path outside docs", file=normalized)
        if normalized not in approved:
            add_finding(findings, "changed_file_outside_approved_list", "changed file is not approved", file=normalized)
        changed.append(normalized)
    return findings, changed


def validate_unresolved_business_gaps(dispositions: dict[str, dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for key, entry in dispositions.items():
        if entry.get("disposition") != "retain_unresolved":
            continue
        gap = entry.get("business_gap", {})
        path = gap.get("path")
        marker = gap.get("marker")
        if not is_nonempty_string(path) or not is_nonempty_string(marker):
            continue
        try:
            content = (repo_root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = ""
        if marker not in content:
            add_finding(findings, "unresolved_business_gap_missing", "approved business-readable unresolved gap is missing after apply", finding_key=key, file=path)
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--docs-root", default="docs", help="Repo-relative docs root")
    parser.add_argument("--scope", help="Optional Markdown file/directory scope")
    parser.add_argument("--phase", choices=VALID_PHASES, default="post-apply")
    parser.add_argument("--plan-file", help="Temporary approved docs-review v2 plan JSON")
    parser.add_argument("--changed-file", action="append", default=[], help="Repo-relative path changed by apply; repeat for each path")
    return parser


def validate(args: argparse.Namespace) -> dict[str, Any]:
    repo_root, docs_root, _, _ = resolve_roots(args.repo_root, args.docs_root, args.scope)
    scan_payload = scan_docs(args.repo_root, args.docs_root, args.scope)
    findings: list[dict[str, Any]] = []
    approved: set[str] = set()
    claims_by_id: dict[str, dict[str, Any]] = {}
    coverage_by_file: dict[str, dict[str, Any]] = {}
    dispositions_by_key: dict[str, dict[str, Any]] = {}
    plan: dict[str, Any] | None = None

    if args.phase == "plan" and not args.plan_file:
        raise DocsReviewError("--phase plan requires --plan-file")
    if args.plan_file:
        plan = load_plan(args.plan_file)
        plan_findings, approved, claims_by_id, coverage_by_file, dispositions_by_key = validate_plan(plan, repo_root, docs_root, scan_payload, args.phase)
        findings.extend(plan_findings)
        findings.extend(validate_coverage_post_state(coverage_by_file, scan_payload, repo_root, args.phase))
    elif args.changed_file:
        raise DocsReviewError("--changed-file requires --plan-file")

    changed: list[str] = []
    if args.phase == "post-apply" and plan is not None:
        if not args.changed_file:
            add_finding(findings, "changed_file_list_missing", "post-apply validation requires at least one --changed-file")
        changed_findings, changed = validate_changed_files(args.changed_file, repo_root, docs_root, approved)
        findings.extend(changed_findings)
        findings.extend(validate_unresolved_business_gaps(dispositions_by_key, repo_root))

    preexisting_scan_findings: list[dict[str, Any]] = []
    if args.phase == "post-apply" and plan is None:
        for source in scan_payload["findings"]:
            copied = dict(source)
            copied["source_finding_id"] = copied.pop("finding_id", None)
            findings.append(copied)
    else:
        preexisting_scan_findings = scan_payload["findings"]

    findings.sort(key=lambda item: (item.get("file", ""), item.get("line", 0), item.get("claim_id", ""), item["type"]))
    for index, finding in enumerate(findings, start=1):
        finding["finding_id"] = f"DRV-{index:04d}"
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_schema_version": PLAN_SCHEMA_VERSION,
        "scanner_manifest": scan_payload["scanner_manifest"],
        "tool": "docs-review.validate",
        "phase": args.phase,
        "repo_root": str(repo_root),
        "docs_root": docs_root.relative_to(repo_root).as_posix(),
        "scope": scan_payload["scope"],
        "summary": {
            "findings": len(findings),
            "preexisting_scan_findings": len(preexisting_scan_findings),
            "changed_files": len(changed),
            "coverage_files": len(coverage_by_file),
            "finding_dispositions": len(dispositions_by_key),
            "resolution_groups": len(plan.get("resolution_groups", [])) if isinstance(plan, dict) and isinstance(plan.get("resolution_groups"), list) else 0,
        },
        "approved_files": sorted(approved),
        "coverage_files": sorted(coverage_by_file),
        "finding_disposition_keys": sorted(dispositions_by_key),
        "changed_files": changed,
        "preexisting_scan_findings": preexisting_scan_findings,
        "findings": findings,
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        payload = validate(args)
        code = 1 if payload["findings"] else 0
    except (DocsReviewError, FileNotFoundError, RuntimeError, OSError) as exc:
        payload = error_payload(str(exc), tool="docs-review.validate")
        code = 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
