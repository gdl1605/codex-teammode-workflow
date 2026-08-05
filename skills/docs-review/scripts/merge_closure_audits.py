#!/usr/bin/env python3
"""Merge validated shard reports and prepare a fresh synthesis-auditor dispatch."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from validate_closure_audit import (
    ClosureAuditError,
    JsonArgumentParser,
    canonical_sha256,
    clause_manifest_sha256,
    load_json,
    select_dispatch,
    validate_report,
)


SCHEMA_VERSION = 2


class MergeError(Exception):
    """Invalid merge input or unverifiable audit coverage."""


def digest_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise MergeError(f"cannot hash raw auditor report {path}: {exc}") from exc


def computed_reuse_key(dispatch: dict[str, Any]) -> str:
    role_file = Path(dispatch["role_file"])
    try:
        role_hash = hashlib.sha256(role_file.read_bytes()).hexdigest()
    except OSError as exc:
        raise MergeError(f"cannot hash dispatched role file {role_file}: {exc}") from exc
    clauses = copy.deepcopy(dispatch["verification_clauses"])
    for clause in clauses:
        clause.pop("audit_binding", None)
    return canonical_sha256(
        {"role_file_sha256": role_hash, "verification_clauses": clauses}
    )


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **extra: Any) -> None:
    issues.append({"type": issue_type, "message": message, **extra})


def manifest_batches(manifest: Any, issues: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict) or manifest.get("audit_schema_version") != SCHEMA_VERSION:
        raise MergeError("audit manifest must use audit_schema_version 2")
    if not isinstance(manifest.get("audit_id"), str) or not manifest["audit_id"]:
        raise MergeError("audit manifest needs a non-empty audit_id")
    batches = manifest.get("batches")
    if not isinstance(batches, list) or not batches:
        raise MergeError("audit manifest must contain at least one shard batch")
    result: dict[str, dict[str, Any]] = {}
    assigned: list[tuple[str, str, str]] = []
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("batch_id"), str) or not batch["batch_id"]:
            add_issue(issues, "invalid_batch", "every batch needs a non-empty batch_id")
            continue
        batch_id = batch["batch_id"]
        if batch_id in result:
            add_issue(issues, "duplicate_batch", "batch_id appears more than once", batch_id=batch_id)
        result[batch_id] = batch
        try:
            _, _, _, clauses = select_dispatch(manifest, "shard", batch_id)
        except ClosureAuditError as exc:
            raise MergeError(str(exc)) from exc
        expected_clause_hash = clause_manifest_sha256(clauses)
        if batch.get("clause_manifest_sha256") != expected_clause_hash:
            add_issue(
                issues,
                "batch_clause_hash_mismatch",
                "batch clause_manifest_sha256 does not match its unbound clauses",
                batch_id=batch_id,
            )
        dispatch = batch["dispatch"]
        if batch.get("input_sha256") != canonical_sha256(dispatch):
            add_issue(
                issues,
                "batch_input_hash_mismatch",
                "batch input_sha256 does not match its exact two-field dispatch",
                batch_id=batch_id,
            )
        if batch.get("reuse_key") != computed_reuse_key(dispatch):
            add_issue(
                issues,
                "batch_reuse_key_mismatch",
                "batch reuse_key does not bind its role and unbound clause dependencies",
                batch_id=batch_id,
            )
        full = batch.get("full_read_files")
        targeted = batch.get("targeted_search_files")
        if not isinstance(full, list) or not all(isinstance(path, str) and path for path in full):
            add_issue(issues, "invalid_batch_coverage", "full_read_files must be a string list", batch_id=batch_id)
            full = []
        if not isinstance(targeted, list) or not all(isinstance(path, str) and path for path in targeted):
            add_issue(issues, "invalid_batch_coverage", "targeted_search_files must be a string list", batch_id=batch_id)
            targeted = []
        for path in full:
            assigned.append((path, "full_read", batch_id))
        for path in targeted:
            assigned.append((path, "targeted_search", batch_id))

    coverage = manifest.get("coverage")
    if not isinstance(coverage, dict):
        add_issue(issues, "coverage_manifest_missing", "audit manifest needs aggregate coverage")
        coverage = {}
    expected: dict[str, str] = {}
    for field, obligation in (("full_read_files", "full_read"), ("targeted_search_files", "targeted_search")):
        entries = coverage.get(field)
        if not isinstance(entries, list):
            add_issue(issues, "invalid_aggregate_coverage", f"coverage.{field} must be a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                add_issue(issues, "invalid_aggregate_coverage_entry", "aggregate coverage entries need paths", obligation=obligation)
                continue
            path = entry["path"]
            if path in expected:
                add_issue(issues, "aggregate_coverage_overlap", "coverage path appears under more than one obligation", file=path)
            expected[path] = obligation

    counts = Counter(path for path, _, _ in assigned)
    for path, count in sorted(counts.items()):
        if count != 1:
            add_issue(issues, "batch_coverage_overlap", "each coverage path must belong to exactly one batch", file=path, assignments=count)
    actual = {path: obligation for path, obligation, _ in assigned}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    wrong = sorted(path for path in set(actual) & set(expected) if actual[path] != expected[path])
    if missing or extra or wrong:
        add_issue(issues, "batch_coverage_union_mismatch", "batch coverage union must exactly equal the aggregate manifest", missing=missing, extra=extra, wrong_obligation=wrong)
    return result


def raw_reports(paths: list[str], label: str) -> list[tuple[Path, dict[str, Any]]]:
    result: list[tuple[Path, dict[str, Any]]] = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        payload = load_json(str(path), label)
        if not isinstance(payload, dict):
            raise MergeError(f"{label} must be a JSON object: {path}")
        result.append((path, payload))
    return result


def validate_one_report(
    manifest: dict[str, Any],
    batch_id: str,
    path: Path,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        audit_id, resolved_batch_id, role_file, clauses = select_dispatch(
            manifest, "shard", batch_id
        )
    except ClosureAuditError as exc:
        raise MergeError(str(exc)) from exc
    result = validate_report(
        clauses,
        payload,
        audit_id,
        "shard",
        resolved_batch_id,
        role_file,
    )
    provenance = {
        "path": str(path),
        "sha256": digest_file(path),
        "source_audit_id": audit_id,
        "source_batch_id": batch_id,
        "verdict": payload.get("closure_audit", {}).get("verdict"),
    }
    return result, provenance


def index_current_reports(
    manifest: dict[str, Any],
    batches: dict[str, dict[str, Any]],
    reports: list[tuple[Path, dict[str, Any]]],
    structural_errors: list[dict[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    indexed: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    for path, payload in reports:
        batch_id = payload.get("batch_id")
        if not isinstance(batch_id, str) or batch_id not in batches:
            add_issue(structural_errors, "unknown_report_batch", "raw report does not identify a current batch", report_file=str(path), batch_id=batch_id)
            continue
        if batch_id in indexed:
            add_issue(structural_errors, "duplicate_batch_report", "a current batch has more than one raw report", batch_id=batch_id)
            continue
        validation, provenance = validate_one_report(manifest, batch_id, path, payload)
        if validation["errors"]:
            add_issue(structural_errors, "invalid_shard_report", "raw shard report failed structural validation", batch_id=batch_id, report_file=str(path), validation_errors=validation["errors"])
        indexed[batch_id] = (payload, validation, provenance)
    return indexed


def reusable_reports(
    current_batches: dict[str, dict[str, Any]],
    previous_manifest: dict[str, Any] | None,
    previous_reports: list[tuple[Path, dict[str, Any]]],
    structural_errors: list[dict[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    if previous_manifest is None:
        if previous_reports:
            add_issue(structural_errors, "previous_manifest_missing", "previous reports require --previous-audit-manifest")
        return {}
    previous_issues: list[dict[str, Any]] = []
    previous_batches = manifest_batches(previous_manifest, previous_issues)
    structural_errors.extend(previous_issues)
    previous_index = index_current_reports(previous_manifest, previous_batches, previous_reports, structural_errors)
    by_reuse_key: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    for previous_batch_id, triple in previous_index.items():
        previous_batch = previous_batches[previous_batch_id]
        reuse_key = previous_batch.get("reuse_key")
        _, validation, _ = triple
        if isinstance(reuse_key, str) and reuse_key and not validation["errors"] and not validation["findings"]:
            if reuse_key in by_reuse_key:
                add_issue(structural_errors, "ambiguous_reuse_key", "more than one previous batch has the same reuse_key", reuse_key=reuse_key)
            by_reuse_key[reuse_key] = triple

    reusable: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    for current_batch_id, batch in current_batches.items():
        reuse_key = batch.get("reuse_key")
        if isinstance(reuse_key, str) and reuse_key in by_reuse_key:
            payload, validation, provenance = by_reuse_key[reuse_key]
            provenance = dict(provenance)
            provenance.update({"current_batch_id": current_batch_id, "reused": True, "reuse_key": reuse_key})
            reusable[current_batch_id] = (payload, validation, provenance)
    return reusable


def unbound_clause(clause: dict[str, Any]) -> dict[str, Any]:
    cloned = copy.deepcopy(clause)
    cloned.pop("audit_binding", None)
    return cloned


def synthesis_obligation(target: dict[str, Any]) -> str | None:
    explicit = target.get("synthesis_obligation")
    if explicit in {"full_read", "targeted_search", "none"}:
        return None if explicit == "none" else explicit
    return "targeted_search"


SPLIT_UNION_LIST_FIELDS = (
    "changed_files",
    "approved_edit_scope",
    "audit_read_scope",
    "required_consumers",
    "semantic_neighbors",
    "authority_and_evidence",
)


def canonical_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def unique_sorted(values: list[Any]) -> list[Any]:
    by_value = {canonical_value(value): copy.deepcopy(value) for value in values}
    return [by_value[key] for key in sorted(by_value)]


def pop_list(obj: dict[str, Any], field: str, clause_id: str) -> tuple[bool, list[Any]]:
    if field not in obj:
        return False, []
    value = obj.pop(field)
    if not isinstance(value, list):
        raise MergeError(f"split clause {clause_id} field {field} must be a list")
    return True, value


def merge_split_clause_metadata(
    existing: dict[str, Any], incoming: dict[str, Any], clause_id: str
) -> dict[str, Any]:
    """Reconstitute one clause from intentionally scope-pruned shard copies."""
    left = copy.deepcopy(existing)
    right = copy.deepcopy(incoming)
    union_fields: dict[str, list[Any]] = {}
    for field in SPLIT_UNION_LIST_FIELDS:
        left_present, left_values = pop_list(left, field, clause_id)
        right_present, right_values = pop_list(right, field, clause_id)
        if left_present or right_present:
            union_fields[field] = unique_sorted(left_values + right_values)

    left_scope = left.pop("fact_scope", None)
    right_scope = right.pop("fact_scope", None)
    merged_scope: dict[str, Any] | None = None
    if left_scope is not None or right_scope is not None:
        if not isinstance(left_scope, dict) or not isinstance(right_scope, dict):
            raise MergeError(f"split clause fact_scope shape differs across batches: {clause_id}")
        left_subjects_present, left_subjects = pop_list(left_scope, "subjects", clause_id)
        right_subjects_present, right_subjects = pop_list(right_scope, "subjects", clause_id)
        if left_scope != right_scope:
            raise MergeError(f"split clause fact_scope authority differs across batches: {clause_id}")
        merged_scope = copy.deepcopy(left_scope)
        if left_subjects_present or right_subjects_present:
            merged_scope["subjects"] = unique_sorted(left_subjects + right_subjects)

    left_artifacts = left.pop("artifacts", None)
    right_artifacts = right.pop("artifacts", None)
    merged_artifacts: dict[str, Any] | None = None
    if left_artifacts is not None or right_artifacts is not None:
        if not isinstance(left_artifacts, dict) or not isinstance(right_artifacts, dict):
            raise MergeError(f"split clause artifacts shape differs across batches: {clause_id}")
        left_before_present, left_before = pop_list(left_artifacts, "before", clause_id)
        right_before_present, right_before = pop_list(right_artifacts, "before", clause_id)
        left_after_present, left_after = pop_list(left_artifacts, "after", clause_id)
        right_after_present, right_after = pop_list(right_artifacts, "after", clause_id)
        if left_artifacts != right_artifacts:
            raise MergeError(f"split clause artifact roots differ across batches: {clause_id}")
        merged_artifacts = copy.deepcopy(left_artifacts)
        if left_before_present or right_before_present:
            merged_artifacts["before"] = unique_sorted(left_before + right_before)
        if left_after_present or right_after_present:
            merged_artifacts["after"] = unique_sorted(left_after + right_after)

    if left != right:
        raise MergeError(f"split clause semantic metadata differs across batches: {clause_id}")
    merged = copy.deepcopy(left)
    merged.update(union_fields)
    if merged_scope is not None:
        merged["fact_scope"] = merged_scope
    if merged_artifacts is not None:
        merged["artifacts"] = merged_artifacts
    return merged


def build_synthesis_clauses(
    manifest: dict[str, Any],
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    clauses_by_id: dict[str, dict[str, Any]] = {}
    targets_by_clause: dict[str, dict[str, dict[str, Any]]] = {}
    for batch in manifest["batches"]:
        for raw_clause in batch["dispatch"]["verification_clauses"]:
            clause = unbound_clause(raw_clause)
            clause_id = clause.get("clause_id")
            if not isinstance(clause_id, str) or not clause_id:
                raise MergeError("all shard clauses need clause_id before synthesis")
            raw_targets = clause.pop("coverage_targets", [])
            if clause_id in clauses_by_id:
                clauses_by_id[clause_id] = merge_split_clause_metadata(
                    clauses_by_id[clause_id], clause, clause_id
                )
            else:
                clauses_by_id[clause_id] = clause
            target_map = targets_by_clause.setdefault(clause_id, {})
            for target in raw_targets:
                if not isinstance(target, dict) or not isinstance(target.get("path"), str):
                    raise MergeError(f"invalid split coverage target in clause {clause_id}")
                obligation = synthesis_obligation(target)
                if obligation is None:
                    continue
                normalized = copy.deepcopy(target)
                normalized["obligation"] = obligation
                normalized.pop("synthesis_obligation", None)
                existing = target_map.get(normalized["path"])
                if existing is None or (existing.get("obligation") == "targeted_search" and obligation == "full_read"):
                    target_map[normalized["path"]] = normalized

    synthesized: list[dict[str, Any]] = []
    for clause_id in sorted(clauses_by_id):
        targets = sorted(targets_by_clause.get(clause_id, {}).values(), key=lambda item: item["path"])
        if not targets:
            continue
        clause = clauses_by_id[clause_id]
        clause["coverage_targets"] = targets
        synthesized.append(clause)
    globals_ = [clause for clause in synthesized if clause.get("kind") == "global"]
    if len(globals_) != 1:
        raise MergeError("synthesis requires exactly one reconstituted global clause")
    globals_[0]["validated_shard_reports"] = reports
    return synthesized


def human_gate(
    report_entries: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    deficiencies: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    report_files: list[dict[str, Any]] = []
    correction_files: set[str] = set()
    for batch_id, (payload, _, provenance) in sorted(report_entries.items()):
        report_files.append(provenance)
        audit = payload.get("closure_audit", {})
        for item in audit.get("main_agent_deficiencies", []):
            deficiencies.append(copy.deepcopy(item))
            location = item.get("location") if isinstance(item, dict) else None
            if isinstance(location, str):
                correction_files.add(location.split(":", 1)[0])
        blocked.extend(copy.deepcopy(audit.get("blocked_checks", [])))
    baseline: dict[str, str] = {}
    coverage = manifest.get("coverage", {})
    for field in ("full_read_files", "targeted_search_files"):
        for entry in coverage.get(field, []):
            if isinstance(entry, dict) and isinstance(entry.get("path"), str) and isinstance(entry.get("sha256"), str):
                baseline[entry["path"]] = entry["sha256"]
    boundaries = [
        {
            "finding_id": item.get("finding_id"),
            "artifact_layer": item.get("artifact_layer"),
            "location": item.get("location"),
            "affected_scope": item.get("affected_scope"),
            "correction_constraint": item.get("correction_constraint"),
        }
        for item in deficiencies
        if isinstance(item, dict)
    ]
    return {
        "status": "user_approval_required",
        "reason": "one or more independent shard auditors reported a deficiency or blocked check",
        "raw_report_files": report_files,
        "deficiencies": deficiencies,
        "blocked_checks": blocked,
        "proposed_correction_scope": sorted(correction_files),
        "post_apply_baseline": dict(sorted(baseline.items())),
        "finding_boundaries": boundaries,
        "instruction": "Do not edit in this audit round. Report these raw deficiencies to the user and wait for approval.",
    }


def merge(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    manifest = load_json(args.audit_manifest, "audit manifest")
    structural_errors: list[dict[str, Any]] = []
    batches = manifest_batches(manifest, structural_errors)
    current = index_current_reports(manifest, batches, raw_reports(args.report_file, "raw shard report"), structural_errors)

    previous_manifest = load_json(args.previous_audit_manifest, "previous audit manifest") if args.previous_audit_manifest else None
    reusable = reusable_reports(
        batches,
        previous_manifest,
        raw_reports(args.previous_report_file, "previous raw shard report"),
        structural_errors,
    )
    selected: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    for batch_id in batches:
        if batch_id in current:
            payload, validation, provenance = current[batch_id]
            provenance.update({"current_batch_id": batch_id, "reused": False, "reuse_key": batches[batch_id].get("reuse_key")})
            selected[batch_id] = (payload, validation, provenance)
        elif batch_id in reusable:
            selected[batch_id] = reusable[batch_id]
        else:
            add_issue(structural_errors, "missing_batch_report", "each current batch needs one fresh or safely reusable raw report", batch_id=batch_id)

    if structural_errors:
        return 2, {
            "audit_schema_version": SCHEMA_VERSION,
            "tool": "docs-review.merge_closure_audits",
            "audit_id": manifest.get("audit_id") if isinstance(manifest, dict) else None,
            "verdict": "invalid",
            "synthesis_dispatch": None,
            "human_gate": None,
            "validated_shard_reports": [],
            "errors": structural_errors,
        }

    nonpass = {batch_id: triple for batch_id, triple in selected.items() if triple[1]["findings"]}
    if nonpass:
        return 1, {
            "audit_schema_version": SCHEMA_VERSION,
            "tool": "docs-review.merge_closure_audits",
            "audit_id": manifest["audit_id"],
            "verdict": "human_gate_required",
            "synthesis_dispatch": None,
            "human_gate": human_gate(nonpass, manifest),
            "validated_shard_reports": [triple[2] for _, triple in sorted(selected.items())],
            "errors": [],
        }

    report_refs = [triple[2] for _, triple in sorted(selected.items())]
    clauses = build_synthesis_clauses(manifest, report_refs)
    synthesis_hash = clause_manifest_sha256(clauses)
    for clause in clauses:
        clause["audit_binding"] = {
            "audit_id": manifest["audit_id"],
            "stage": "synthesis",
            "batch_id": "synthesis",
            "clause_manifest_sha256": synthesis_hash,
        }
    synthesis_dispatch = {
        "role_file": manifest.get("synthesis_role_file"),
        "verification_clauses": clauses,
    }
    if not isinstance(synthesis_dispatch["role_file"], str) or not Path(synthesis_dispatch["role_file"]).is_file():
        raise MergeError("audit manifest synthesis_role_file must name the existing packaged role")
    return 0, {
        "audit_schema_version": SCHEMA_VERSION,
        "tool": "docs-review.merge_closure_audits",
        "audit_id": manifest["audit_id"],
        "verdict": "ready_for_fresh_synthesis",
        "batches": manifest["batches"],
        "synthesis_clause_manifest_sha256": synthesis_hash,
        "synthesis_dispatch": synthesis_dispatch,
        "human_gate": None,
        "validated_shard_reports": report_refs,
        "report_reuse": {
            "fresh_batches": sorted(batch_id for batch_id, triple in selected.items() if triple[2]["reused"] is False),
            "reused_batches": sorted(batch_id for batch_id, triple in selected.items() if triple[2]["reused"] is True),
            "synthesis_reuse_allowed": False,
        },
        "errors": [],
    }


def error_payload(message: str) -> dict[str, Any]:
    return {
        "audit_schema_version": SCHEMA_VERSION,
        "tool": "docs-review.merge_closure_audits",
        "audit_id": None,
        "verdict": "invalid",
        "synthesis_dispatch": None,
        "human_gate": None,
        "validated_shard_reports": [],
        "errors": [{"type": "input_error", "message": message}],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--audit-manifest", required=True)
    parser.add_argument("--report-file", action="append", default=[])
    parser.add_argument("--previous-audit-manifest")
    parser.add_argument("--previous-report-file", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        code, payload = merge(build_parser().parse_args(argv))
    except (MergeError, ClosureAuditError, OSError) as exc:
        code, payload = 2, error_payload(str(exc))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
