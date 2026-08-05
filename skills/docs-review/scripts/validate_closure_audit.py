#!/usr/bin/env python3
"""Validate a schema-v2 docs-review independent closure audit."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PATH_LINE_RE = re.compile(r"(?:^|[\s;(])[^\s;()]+:\d+(?:-\d+)?")
VALID_OBLIGATIONS = {"full_read", "targeted_search"}
VALID_OUTCOMES = {"verified", "deficiency", "blocked"}
VALID_VERDICTS = {"pass", "deficiencies_found", "blocked"}
VALID_SEVERITIES = {"P0", "P1", "P2", "P3"}
REQUIRED_DEFICIENCY_FIELDS = (
    "finding_id", "severity", "clause_id", "type", "artifact_layer",
    "effect_class", "location", "comparison_evidence",
    "why_main_agent_is_wrong_or_incomplete", "affected_scope",
    "correction_constraint",
)
REQUIRED_BLOCKED_FIELDS = (
    "blocked_check_id", "clause_id", "reason", "required_to_unblock",
)
REQUIRED_RESULT_LISTS = (
    "full_read_files", "targeted_search_files", "searches_performed",
    "deficiency_ids", "blocked_check_ids",
)
REQUIRED_ACCOUNTING_LISTS = (
    "expected_clause_ids", "completed_clause_ids", "required_full_read_files",
    "full_read_files_completed", "required_targeted_search_files",
    "targeted_search_files_completed", "omitted_or_unverifiable",
)


class ClosureAuditError(Exception):
    """Expected command-line, JSON, or manifest-shape failure."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ClosureAuditError(message)


def load_json(path_raw: str, label: str) -> Any:
    try:
        return json.loads(Path(path_raw).expanduser().read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosureAuditError(f"cannot read {label} JSON {path_raw}: {exc}") from exc


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def clause_manifest_sha256(clauses: list[dict[str, Any]]) -> str:
    """Hash clause semantics without the self-referential audit_binding."""
    unbound = copy.deepcopy(clauses)
    for clause in unbound:
        clause.pop("audit_binding", None)
    return canonical_sha256(unbound)


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **extra: Any) -> None:
    issues.append({"type": issue_type, "message": message, **extra})


def string_set(value: Any, label: str, errors: list[dict[str, Any]]) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        add_issue(errors, "invalid_string_list", f"{label} must be a list of non-empty strings")
        return set()
    if len(value) != len(set(value)):
        add_issue(errors, "duplicate_list_entry", f"{label} contains duplicates")
    return set(value)


def normalize_audit_path(value: Any) -> str | None:
    """Normalize one lexical file path without resolving or reading it."""
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    path = Path(value)
    if ".." in path.parts:
        return None
    normalized = path.as_posix()
    if normalized in {"", "."}:
        return None
    return normalized.rstrip("/") or "/"


def path_aliases(value: Any, repository_roots: set[str]) -> set[str]:
    """Return a declared path plus its unambiguous repository-root alias."""
    normalized = normalize_audit_path(value)
    if normalized is None:
        return set()
    aliases = {normalized}
    if not Path(normalized).is_absolute():
        for root in repository_roots:
            aliases.add((Path(root) / normalized).as_posix())
    return aliases


def looks_like_file_scope(value: str, repository_roots: set[str]) -> bool:
    """Distinguish an exact audit file from a directory scope.

    Existing paths are authoritative.  For portable manifests whose target is not
    available to the validator, a suffix denotes a file and a trailing slash (or
    suffix-free value) denotes a directory.
    """
    if value.endswith("/"):
        return False
    path = Path(value)
    candidates = [path] if path.is_absolute() else [Path(root) / path for root in repository_roots]
    for candidate in candidates:
        if candidate.exists():
            return candidate.is_file()
    return bool(path.suffix)


def support_path_contract(
    clauses: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    role_file: str | None = None,
) -> tuple[set[str], set[str], list[tuple[str, set[str]]]]:
    """Build the allowed and required non-coverage path contract.

    Coverage accounting remains exact and repo-relative.  This companion contract
    permits auditors to truthfully enumerate the baseline snapshots, evidence,
    current implementation files, and validated shard reports that the dispatched
    clauses explicitly authorize.  Required entries are alias groups: reporting a
    repo-relative current path or its declared absolute current path satisfies the
    same obligation.
    """
    repository_roots: set[str] = set()
    for clause in clauses:
        artifacts = clause.get("artifacts")
        if isinstance(artifacts, dict):
            root = normalize_audit_path(artifacts.get("repository_root"))
            if root is not None and Path(root).is_absolute():
                repository_roots.add(root)

    allowed_exact: set[str] = set()
    allowed_prefixes: set[str] = set()
    required_groups: list[tuple[str, set[str]]] = []
    seen_required: set[frozenset[str]] = set()

    def allow(value: Any) -> set[str]:
        aliases = path_aliases(value, repository_roots)
        allowed_exact.update(aliases)
        return aliases

    def require(label: str, aliases: set[str]) -> None:
        if not aliases:
            add_issue(
                errors,
                "invalid_dispatched_support_path",
                f"{label} must name an auditable file path",
            )
            return
        marker = frozenset(aliases)
        if marker not in seen_required:
            required_groups.append((label, aliases))
            seen_required.add(marker)

    # The role is part of the exact two-field dispatch and the acknowledgement
    # proves it was read.  Auditors may therefore truthfully include it in
    # paths_examined.  Keep it optional there for compatibility with otherwise
    # valid schema-2 reports that account for it through role_acknowledgement.
    allow(role_file)

    for clause in clauses:
        clause_id = str(clause.get("clause_id", "<unknown>"))

        for index, evidence in enumerate(clause.get("authority_and_evidence", [])):
            if not isinstance(evidence, dict):
                continue
            aliases = allow(evidence.get("path"))
            require(f"{clause_id}.authority_and_evidence[{index}]", aliases)

        artifacts = clause.get("artifacts")
        if isinstance(artifacts, dict):
            before = artifacts.get("before", [])
            if isinstance(before, list):
                for index, entry in enumerate(before):
                    if not isinstance(entry, dict):
                        continue
                    source_aliases = allow(entry.get("source_path"))
                    snapshot_aliases = allow(entry.get("snapshot_path"))
                    allow(entry.get("path"))
                    allow(entry.get("current_path"))
                    require(
                        f"{clause_id}.artifacts.before[{index}]",
                        snapshot_aliases or source_aliases,
                    )
            after = artifacts.get("after", [])
            if isinstance(after, list):
                for index, entry in enumerate(after):
                    if not isinstance(entry, dict):
                        continue
                    aliases: set[str] = set()
                    for field in ("source_path", "current_path", "path"):
                        aliases |= allow(entry.get(field))
                    require(f"{clause_id}.artifacts.after[{index}]", aliases)

        read_scope = clause.get("audit_read_scope", [])
        if isinstance(read_scope, list):
            for index, value in enumerate(read_scope):
                normalized = normalize_audit_path(value)
                if normalized is None:
                    add_issue(
                        errors,
                        "invalid_dispatched_support_path",
                        f"{clause_id}.audit_read_scope[{index}] must be a safe file or directory path",
                    )
                    continue
                aliases = path_aliases(normalized, repository_roots)
                if looks_like_file_scope(value, repository_roots):
                    allowed_exact.update(aliases)
                    require(f"{clause_id}.audit_read_scope[{index}]", aliases)
                else:
                    allowed_prefixes.update(aliases)

        for field in (
            "changed_files",
            "approved_edit_scope",
            "required_consumers",
            "semantic_neighbors",
        ):
            values = clause.get(field, [])
            if isinstance(values, list):
                for value in values:
                    allow(value)

        fact_scope = clause.get("fact_scope")
        subjects = fact_scope.get("subjects", []) if isinstance(fact_scope, dict) else []
        if isinstance(subjects, list):
            for value in subjects:
                normalized = normalize_audit_path(value)
                if normalized is not None and (
                    Path(normalized).is_absolute()
                    or bool(Path(normalized).suffix)
                    or normalized.startswith(("docs/", "src/", "tests/", "test/"))
                ):
                    allow(normalized)

        reports = clause.get("validated_shard_reports", [])
        if isinstance(reports, list):
            for index, report in enumerate(reports):
                if not isinstance(report, dict):
                    continue
                aliases = allow(report.get("path"))
                require(f"{clause_id}.validated_shard_reports[{index}]", aliases)

    return allowed_exact, allowed_prefixes, required_groups


def path_is_authorized(path: str, exact: set[str], prefixes: set[str]) -> bool:
    if path in exact:
        return True
    return any(path.startswith(f"{prefix.rstrip('/')}/") for prefix in prefixes if prefix != "/")


def require_text(obj: dict[str, Any], field: str, label: str, errors: list[dict[str, Any]]) -> str | None:
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        add_issue(errors, "required_field_missing", f"{label}.{field} must be a non-empty string", field=field)
        return None
    return value


def select_dispatch(
    manifest: Any, stage: str, batch_id: str | None
) -> tuple[str, str, str, list[dict[str, Any]]]:
    if not isinstance(manifest, dict) or manifest.get("audit_schema_version") != SCHEMA_VERSION:
        raise ClosureAuditError("audit manifest must be an object with audit_schema_version=2")
    audit_id = manifest.get("audit_id")
    if not isinstance(audit_id, str) or not audit_id:
        raise ClosureAuditError("audit manifest audit_id must be a non-empty string")
    if stage == "shard":
        if not batch_id:
            raise ClosureAuditError("--batch-id is required for --stage shard")
        batches = manifest.get("batches")
        if not isinstance(batches, list):
            raise ClosureAuditError("audit manifest batches must be a list for shard stage")
        matches = [batch for batch in batches if isinstance(batch, dict) and batch.get("batch_id") == batch_id]
        if len(matches) != 1:
            raise ClosureAuditError("shard batch_id must identify exactly one audit-manifest batch")
        dispatch = matches[0].get("dispatch")
        resolved_batch_id = batch_id
    else:
        if batch_id not in (None, "synthesis"):
            raise ClosureAuditError("--batch-id must be omitted or synthesis for --stage synthesis")
        dispatch = manifest.get("synthesis_dispatch")
        resolved_batch_id = "synthesis"
    if not isinstance(dispatch, dict):
        raise ClosureAuditError("selected audit-manifest dispatch must be an object")
    if set(dispatch) != {"role_file", "verification_clauses"}:
        raise ClosureAuditError(
            "selected dispatch must contain exactly role_file and verification_clauses"
        )
    role_file = dispatch.get("role_file")
    if not isinstance(role_file, str) or not Path(role_file).is_file():
        raise ClosureAuditError("selected dispatch role_file must name an existing role")
    clauses = dispatch.get("verification_clauses")
    if not isinstance(clauses, list) or not clauses or not all(isinstance(item, dict) for item in clauses):
        raise ClosureAuditError("selected dispatch verification_clauses must be a non-empty object list")
    return audit_id, resolved_batch_id, role_file, clauses


def expected_contract(clauses: list[dict[str, Any]], errors: list[dict[str, Any]]) -> tuple[set[str], set[str], set[str]]:
    clause_ids: set[str] = set()
    full_read: set[str] = set()
    targeted_search: set[str] = set()
    global_count = 0
    for clause in clauses:
        clause_id = clause.get("clause_id")
        if not isinstance(clause_id, str) or not clause_id:
            add_issue(errors, "clause_id_missing", "every dispatched clause needs clause_id")
            continue
        if clause_id in clause_ids:
            add_issue(errors, "duplicate_clause_id", "dispatched clause id appears more than once", clause_id=clause_id)
        clause_ids.add(clause_id)
        if clause.get("kind") == "global":
            global_count += 1
        targets = clause.get("coverage_targets")
        if not isinstance(targets, list) or not targets:
            add_issue(errors, "coverage_targets_missing", "every dispatched clause needs coverage_targets", clause_id=clause_id)
            continue
        for target in targets:
            if not isinstance(target, dict):
                add_issue(errors, "invalid_coverage_target", "coverage target must be an object", clause_id=clause_id)
                continue
            path, obligation = target.get("path"), target.get("obligation")
            if not isinstance(path, str) or not path or not path.lower().endswith(".md"):
                add_issue(errors, "invalid_coverage_target_path", "coverage target must name an exact Markdown file", clause_id=clause_id)
                continue
            if obligation not in VALID_OBLIGATIONS:
                add_issue(errors, "invalid_coverage_obligation", "coverage obligation is invalid", clause_id=clause_id, path=path)
                continue
            if not isinstance(target.get("sha256"), str) or not SHA256_RE.fullmatch(target["sha256"].lower()):
                add_issue(errors, "invalid_coverage_sha256", "coverage target needs SHA-256", clause_id=clause_id, path=path)
            if not isinstance(target.get("line_count"), int) or isinstance(target.get("line_count"), bool) or target["line_count"] < 0:
                add_issue(errors, "invalid_coverage_line_count", "coverage target line_count must be non-negative integer", clause_id=clause_id, path=path)
            if not isinstance(target.get("reason"), str) or not target["reason"].strip():
                add_issue(errors, "coverage_reason_missing", "coverage target needs a reason", clause_id=clause_id, path=path)
            if obligation == "full_read":
                full_read.add(path)
                targeted_search.discard(path)
            elif path not in full_read:
                targeted_search.add(path)
    if global_count != 1:
        add_issue(errors, "global_clause_count_invalid", "dispatch must contain exactly one global clause", actual=global_count)
    return clause_ids, full_read, targeted_search


def validate_report(
    clauses: list[dict[str, Any]],
    report_payload: Any,
    audit_id: str,
    stage: str,
    batch_id: str,
    role_file: str | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    clause_ids, required_full, required_search = expected_contract(clauses, errors)
    expected_hash = clause_manifest_sha256(clauses)
    for clause in clauses:
        binding = clause.get("audit_binding")
        expected_binding = {
            "audit_id": audit_id,
            "stage": stage,
            "batch_id": batch_id,
            "clause_manifest_sha256": expected_hash,
        }
        if binding != expected_binding:
            add_issue(
                errors,
                "dispatch_binding_invalid",
                "each dispatched clause must carry the exact non-recursive audit binding",
                clause_id=clause.get("clause_id"),
                expected=expected_binding,
                actual=binding,
            )
    if not isinstance(report_payload, dict):
        add_issue(errors, "report_not_object", "report JSON must be an object")
        report_payload = {}
    required_top = {
        "audit_schema_version": SCHEMA_VERSION, "audit_id": audit_id, "stage": stage,
        "batch_id": batch_id, "clause_manifest_sha256": expected_hash,
    }
    for field, expected in required_top.items():
        if field not in report_payload:
            add_issue(errors, "report_binding_field_missing", f"report top level lacks {field}", field=field)
        elif report_payload.get(field) != expected:
            add_issue(errors, "report_binding_mismatch", f"report {field} does not bind to selected manifest", field=field, expected=expected, actual=report_payload.get(field))
    if "closure_audit" not in report_payload or not isinstance(report_payload.get("closure_audit"), dict):
        add_issue(errors, "closure_audit_missing", "report must contain closure_audit object")
        audit: dict[str, Any] = {}
    else:
        audit = report_payload["closure_audit"]
    acknowledgement = audit.get("role_acknowledgement")
    if not isinstance(acknowledgement, dict) or any(acknowledgement.get(field) is not True for field in ("role_file_read", "two_field_input_valid", "read_only")):
        add_issue(errors, "role_acknowledgement_incomplete", "auditor acknowledgement is incomplete")

    results = audit.get("clause_results")
    if not isinstance(results, list):
        add_issue(errors, "clause_results_missing", "closure_audit.clause_results must be a list")
        results = []
    results_by_id: dict[str, dict[str, Any]] = {}
    result_links: dict[str, tuple[set[str], set[str]]] = {}
    aggregate_full: set[str] = set()
    aggregate_search: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            add_issue(errors, "invalid_clause_result", "each clause result must be an object")
            continue
        clause_id = require_text(result, "clause_id", "clause_result", errors)
        if clause_id is None:
            continue
        if clause_id in results_by_id:
            add_issue(errors, "duplicate_clause_result", "clause has more than one terminal result", clause_id=clause_id)
        results_by_id[clause_id] = result
        if result.get("outcome") not in VALID_OUTCOMES:
            add_issue(errors, "invalid_clause_outcome", "clause outcome is invalid", clause_id=clause_id)
        require_text(result, "evidence", f"clause_results[{clause_id}]", errors)
        lists = {field: string_set(result.get(field), f"clause_results[{clause_id}].{field}", errors) for field in REQUIRED_RESULT_LISTS}
        aggregate_full |= lists["full_read_files"]
        aggregate_search |= lists["targeted_search_files"]
        result_links[clause_id] = (lists["deficiency_ids"], lists["blocked_check_ids"])
    for clause_id in sorted(clause_ids - set(results_by_id)):
        add_issue(errors, "clause_result_missing", "dispatched clause has no terminal result", clause_id=clause_id)
    for clause_id in sorted(set(results_by_id) - clause_ids):
        add_issue(errors, "unknown_clause_result", "report has result for undispatched clause", clause_id=clause_id)

    deficiencies = audit.get("main_agent_deficiencies")
    if not isinstance(deficiencies, list):
        add_issue(errors, "invalid_deficiencies", "main_agent_deficiencies must be a list")
        deficiencies = []
    deficiency_ids: set[str] = set()
    deficiency_clause: dict[str, str] = {}
    for deficiency in deficiencies:
        if not isinstance(deficiency, dict):
            add_issue(errors, "invalid_deficiency", "deficiency must be an object")
            continue
        values = {field: require_text(deficiency, field, "main_agent_deficiency", errors) for field in REQUIRED_DEFICIENCY_FIELDS}
        finding_id, clause_id = values["finding_id"], values["clause_id"]
        if deficiency.get("severity") not in VALID_SEVERITIES:
            add_issue(errors, "invalid_deficiency_severity", "deficiency severity must be P0 through P3", finding_id=finding_id)
        if deficiency.get("artifact_layer") not in {"docs", "implementation", "evidence", "process"}:
            add_issue(errors, "invalid_artifact_layer", "deficiency artifact_layer is invalid", finding_id=finding_id)
        if deficiency.get("effect_class") not in {"current_behavior", "reader_contract", "future_risk", "discoverability"}:
            add_issue(errors, "invalid_effect_class", "deficiency effect_class is invalid", finding_id=finding_id)
        if not isinstance(deficiency.get("location"), str) or not re.search(
            r":\d+(?:-\d+)?$", deficiency["location"]
        ):
            add_issue(
                errors,
                "deficiency_location_not_exact",
                "deficiency location must end with an exact path:line or path:start-end",
                finding_id=finding_id,
            )
        if not isinstance(deficiency.get("comparison_evidence"), str) or not PATH_LINE_RE.search(
            deficiency["comparison_evidence"]
        ):
            add_issue(
                errors,
                "comparison_evidence_not_exact",
                "comparison_evidence must cite at least one exact path:line",
                finding_id=finding_id,
            )
        if finding_id:
            if finding_id in deficiency_ids:
                add_issue(errors, "duplicate_deficiency_id", "deficiency id appears more than once", finding_id=finding_id)
            deficiency_ids.add(finding_id)
        if clause_id and clause_id in clause_ids and finding_id:
            deficiency_clause[finding_id] = clause_id
        else:
            add_issue(errors, "deficiency_clause_invalid", "deficiency must reference a dispatched clause", finding_id=finding_id, clause_id=clause_id)
        if deficiency.get("severity") == "P0" and not (
            deficiency.get("artifact_layer") == "implementation"
            and deficiency.get("effect_class") == "current_behavior"
        ):
            add_issue(
                errors,
                "invalid_p0_attribution",
                "P0 is reserved for dangerous current implementation behavior proved by code/evidence",
                finding_id=finding_id,
            )
        if deficiency.get("artifact_layer") == "implementation":
            evidence = deficiency.get("comparison_evidence")
            code_or_evidence_path = re.compile(
                r"(?:[\w.-]+/)*evidence/[\w./-]+(?::\d+)?|[\w./-]+\.(?:py|js|ts|tsx|jsx|java|go|rs|rb|php|cs|kt|swift|sql|yml|yaml|json|sh)(?::\d+)?",
                re.IGNORECASE,
            )
            if not isinstance(evidence, str) or not code_or_evidence_path.search(evidence):
                add_issue(errors, "invalid_implementation_attribution", "implementation finding comparison_evidence must cite code or evidence path", finding_id=finding_id)

    blocked_checks = audit.get("blocked_checks")
    if not isinstance(blocked_checks, list):
        add_issue(errors, "invalid_blocked_checks", "blocked_checks must be a list")
        blocked_checks = []
    blocked_ids: set[str] = set()
    blocked_clause: dict[str, str] = {}
    for blocked in blocked_checks:
        if not isinstance(blocked, dict):
            add_issue(errors, "invalid_blocked_check", "blocked check must be an object")
            continue
        values = {field: require_text(blocked, field, "blocked_check", errors) for field in REQUIRED_BLOCKED_FIELDS}
        blocked_id, clause_id = values["blocked_check_id"], values["clause_id"]
        if blocked_id:
            if blocked_id in blocked_ids:
                add_issue(errors, "duplicate_blocked_check_id", "blocked check id appears more than once", blocked_check_id=blocked_id)
            blocked_ids.add(blocked_id)
        if blocked_id and clause_id and clause_id in clause_ids:
            blocked_clause[blocked_id] = clause_id
        else:
            add_issue(errors, "blocked_check_clause_invalid", "blocked check must reference a dispatched clause", blocked_check_id=blocked_id, clause_id=clause_id)

    linked_deficiencies: set[str] = set()
    linked_blocked: set[str] = set()
    for clause_id, result in results_by_id.items():
        result_deficiencies, result_blocked = result_links.get(clause_id, (set(), set()))
        linked_deficiencies |= result_deficiencies
        linked_blocked |= result_blocked
        for finding_id in result_deficiencies:
            if deficiency_clause.get(finding_id) != clause_id:
                add_issue(errors, "deficiency_result_link_invalid", "clause result links missing or differently scoped deficiency", clause_id=clause_id, finding_id=finding_id)
        for blocked_id in result_blocked:
            if blocked_clause.get(blocked_id) != clause_id:
                add_issue(errors, "blocked_result_link_invalid", "clause result links missing or differently scoped blocked check", clause_id=clause_id, blocked_check_id=blocked_id)
        expected_outcome = "deficiency" if result_deficiencies else "blocked" if result_blocked else "verified"
        if result.get("outcome") != expected_outcome:
            add_issue(errors, "clause_outcome_incoherent", "clause outcome does not match linked IDs", clause_id=clause_id, expected=expected_outcome, actual=result.get("outcome"))
    for finding_id in sorted(deficiency_ids - linked_deficiencies):
        add_issue(errors, "deficiency_not_linked", "deficiency is absent from its clause result", finding_id=finding_id)
    for blocked_id in sorted(blocked_ids - linked_blocked):
        add_issue(errors, "blocked_check_not_linked", "blocked check is absent from its clause result", blocked_check_id=blocked_id)

    accounting = audit.get("coverage_accounting")
    if not isinstance(accounting, dict):
        add_issue(errors, "coverage_accounting_missing", "closure_audit needs coverage_accounting")
        accounting = {}
    accounting_sets = {field: string_set(accounting.get(field), f"coverage_accounting.{field}", errors) for field in REQUIRED_ACCOUNTING_LISTS}
    expected_pairs = (
        ("expected_clause_ids", accounting_sets["expected_clause_ids"], clause_ids),
        ("completed_clause_ids", accounting_sets["completed_clause_ids"], clause_ids),
        ("required_full_read_files", accounting_sets["required_full_read_files"], required_full),
        ("required_targeted_search_files", accounting_sets["required_targeted_search_files"], required_search),
    )
    for field, actual, expected in expected_pairs:
        if actual != expected:
            add_issue(errors, "coverage_accounting_mismatch", f"{field} does not exactly match dispatch", field=field, missing=sorted(expected - actual), extra=sorted(actual - expected))
    for label, actual, expected in (
        ("full_read_files_completed", accounting_sets["full_read_files_completed"], required_full),
        ("targeted_search_files_completed", accounting_sets["targeted_search_files_completed"], required_search),
        ("clause_result_full_read_files", aggregate_full, required_full),
        ("clause_result_targeted_search_files", aggregate_search, required_search),
    ):
        if actual != expected:
            add_issue(
                errors,
                "completed_coverage_mismatch",
                f"{label} must exactly equal the dispatched coverage obligation",
                field=label,
                missing=sorted(expected - actual),
                extra=sorted(actual - expected),
            )
    if accounting_sets["omitted_or_unverifiable"]:
        add_issue(errors, "coverage_obligation_omitted", "omitted coverage makes audit unverifiable", obligations=sorted(accounting_sets["omitted_or_unverifiable"]))

    global_review = audit.get("global_review")
    if not isinstance(global_review, dict):
        add_issue(errors, "global_review_missing", "closure_audit needs global_review")
        global_review = {}
    raw_paths_examined = string_set(global_review.get("paths_examined"), "global_review.paths_examined", errors)
    paths_examined: set[str] = set()
    for raw_path in raw_paths_examined:
        normalized = normalize_audit_path(raw_path)
        if normalized is None:
            add_issue(
                errors,
                "global_path_invalid",
                "global paths_examined entries must be safe exact file paths",
                path=raw_path,
            )
            continue
        if normalized in paths_examined:
            add_issue(
                errors,
                "global_path_duplicate_after_normalization",
                "global paths_examined contains duplicate lexical aliases",
                path=raw_path,
            )
        paths_examined.add(normalized)
    for field in ("search_scopes", "searches_performed"):
        string_set(global_review.get(field), f"global_review.{field}", errors)
    require_text(global_review, "residual_risk", "global_review", errors)
    required_paths = required_full | required_search
    missing_coverage = required_paths - paths_examined
    if missing_coverage:
        add_issue(
            errors,
            "global_coverage_path_not_examined",
            "global paths_examined must include every dispatched coverage target",
            missing=sorted(missing_coverage),
        )
    allowed_exact, allowed_prefixes, required_support = support_path_contract(
        clauses, errors, role_file
    )
    allowed_exact |= required_paths
    for label, aliases in required_support:
        if not (aliases & paths_examined):
            add_issue(
                errors,
                "global_required_support_path_not_examined",
                "global paths_examined omits a required evidence, artifact, or exact read-scope file",
                source=label,
                accepted_paths=sorted(aliases),
            )
    unauthorized = sorted(
        path
        for path in paths_examined
        if not path_is_authorized(path, allowed_exact, allowed_prefixes)
    )
    if unauthorized:
        add_issue(
            errors,
            "global_path_outside_dispatch_scope",
            "global paths_examined contains files not authorized by dispatched clauses",
            paths=unauthorized,
        )

    verdict = audit.get("verdict")
    if verdict not in VALID_VERDICTS:
        add_issue(errors, "invalid_audit_verdict", "closure audit verdict is invalid")
    expected_verdict = "deficiencies_found" if deficiency_ids else "blocked" if blocked_ids else "pass"
    if verdict != expected_verdict:
        add_issue(errors, "audit_verdict_incoherent", "verdict does not match deficiencies and blocked checks", expected=expected_verdict, actual=verdict)
    if not errors and verdict != "pass":
        add_issue(findings, "auditor_reported_non_pass", "independent closure auditor did not return pass", verdict=verdict)

    for issues in (findings, errors):
        issues.sort(key=lambda item: (str(item.get("clause_id", "")), item["type"]))
        for index, issue in enumerate(issues, start=1):
            issue["finding_id"] = f"DCA-{'F' if issues is findings else 'E'}-{index:04d}"
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "docs-review.validate-closure-audit",
        "summary": {"findings": len(findings), "errors": len(errors), "expected_clauses": len(clause_ids), "reported_clause_results": len(results_by_id), "audit_verdict": verdict},
        "findings": findings,
        "errors": errors,
    }


def error_payload(message: str) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "tool": "docs-review.validate-closure-audit", "summary": {"findings": 0, "errors": 1}, "findings": [], "errors": [{"type": "input_error", "message": message}]}


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("shard", "synthesis"))
    parser.add_argument("--audit-manifest", required=True)
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--batch-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        audit_id, batch_id, role_file, clauses = select_dispatch(
            load_json(args.audit_manifest, "audit manifest"), args.stage, args.batch_id
        )
        payload = validate_report(
            clauses,
            load_json(args.report_file, "report"),
            audit_id,
            args.stage,
            batch_id,
            role_file,
        )
        code = 2 if payload["errors"] else 1 if payload["findings"] else 0
    except ClosureAuditError as exc:
        payload, code = error_payload(str(exc)), 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
