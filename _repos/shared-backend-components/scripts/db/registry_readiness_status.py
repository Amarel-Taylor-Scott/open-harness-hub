#!/usr/bin/env python3
"""Emit machine-readable registry/storage readiness status.

This is a non-destructive rollup for long-running improvement work. It combines
hard-coded setting drift, settings registry seed health, object-governance seed
coverage, and rotted-context archive candidates into one status artifact.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_context_storage import build_report
from scripts._config import DEFAULT_DATABASE_URL_ENV
from scripts.db.archive_candidate_registry import registry_summary as archive_candidate_summary
from scripts.db.catalog_operational_view_probe import probe_catalog_operational_views
from scripts.db.catalog_reader_migration_registry import registry_summary as reader_migration_summary
from scripts.db.manifest_import_registry import registry_summary as manifest_import_summary
from scripts.db.object_governance_registry import (
    concrete_seed_coverage,
    package_seed_coverage,
    package_seed_coverage_errors,
)
from scripts.db.object_governance_view_probe import probe_object_governance_views
from scripts.db.settings_registry_export import registry_summary as settings_registry_summary

DEFAULT_OUTPUT = _resource("dist") / "registry-readiness" / "registry-readiness-status.json"


def _severity_buckets(candidates: list[dict[str, Any]]) -> dict[str, int]:
    buckets = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    for candidate in candidates:
        score = int(candidate.get("severity_score") or 0)
        if score >= 5:
            buckets["critical"] += 1
        elif score >= 4:
            buckets["high"] += 1
        elif score >= 3:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets


def _max_severity(candidates: list[dict[str, Any]]) -> int:
    return max((int(candidate.get("severity_score") or 0) for candidate in candidates), default=0)


def readiness_status(
    *,
    tenant_id: str = "system",
    seed_tenant_id: str = "seed",
    database_url: str = "",
) -> dict[str, Any]:
    """Return a consolidated readiness status for registry/config migration."""
    audit = build_report()
    hardcoded = audit["hardcoded_settings"]
    rotted = audit["rotted_context_candidates"]
    settings = settings_registry_summary(tenant_id=tenant_id)
    archive_candidates = archive_candidate_summary(tenant_id=seed_tenant_id)
    reader_migration = reader_migration_summary(tenant_id=seed_tenant_id)
    manifest_import = manifest_import_summary()
    object_governance = package_seed_coverage(tenant_id=seed_tenant_id)
    concrete_object_governance = concrete_seed_coverage(tenant_id=seed_tenant_id)
    object_governance_errors = package_seed_coverage_errors(tenant_id=seed_tenant_id)
    object_governance_views = probe_object_governance_views(database_url=database_url)
    catalog_views = probe_catalog_operational_views(database_url=database_url)

    hardcoded_clean = (
        int(hardcoded["unregistered_repeated_model_literal_count"]) == 0
        and int(hardcoded["unregistered_repeated_backend_literal_count"]) == 0
        and int(hardcoded["repeated_vector_dimension_count"]) == 0
        and int(hardcoded.get("private_runtime_setting_resolver_bypass_count") or 0) == 0
    )
    settings_clean = (
        int(settings["duplicate_key_count"]) == 0
        and int(settings["invalid_setting_kind_count"]) == 0
    )
    object_governance_seed_clean = not object_governance_errors
    object_governance_views_clean = bool(object_governance_views["schema_ready"]) and (
        bool(object_governance_views["database_ready"]) if database_url else True
    )
    catalog_views_clean = bool(catalog_views["schema_ready"]) and (
        bool(catalog_views["database_ready"]) if database_url else True
    )
    archive_registry_integrity_clean = (
        int(archive_candidates["duplicate_key_count"]) == 0
        and int(archive_candidates["missing_source_hash_count"]) == 0
    )
    rotted_candidates = rotted.get("candidates") or []

    return {
        "kind": "baltor.registry-readiness-status",
        "repo": str(ROOT),
        "status": {
            "ready": (
                hardcoded_clean
                and settings_clean
                and object_governance_seed_clean
                and object_governance_views_clean
                and catalog_views_clean
                and archive_registry_integrity_clean
            ),
            "hardcoded_settings_clean": hardcoded_clean,
            "settings_registry_clean": settings_clean,
            "object_governance_seed_coverage_clean": object_governance_seed_clean,
            "object_governance_operational_views_clean": object_governance_views_clean,
            "catalog_operational_views_clean": catalog_views_clean,
            "archive_candidate_registry_integrity_clean": archive_registry_integrity_clean,
            "rotted_context_candidates_present": bool(rotted_candidates),
        },
        "settings_registry": {
            "tenant_id": tenant_id,
            "row_count": settings["row_count"],
            "duplicate_key_count": settings["duplicate_key_count"],
            "invalid_setting_kind_count": settings["invalid_setting_kind_count"],
            "by_kind": settings["by_kind"],
            "by_namespace": settings["by_namespace"],
        },
        "hardcoded_settings": {
            "unregistered_repeated_model_literal_count": hardcoded["unregistered_repeated_model_literal_count"],
            "unregistered_repeated_backend_literal_count": hardcoded["unregistered_repeated_backend_literal_count"],
            "repeated_vector_dimension_count": hardcoded["repeated_vector_dimension_count"],
            "private_runtime_setting_resolver_bypass_count": hardcoded.get("private_runtime_setting_resolver_bypass_count") or 0,
            "private_runtime_setting_resolver_bypasses": hardcoded.get("private_runtime_setting_resolver_bypasses") or [],
            "approved_runtime_setting_wrapper_count": hardcoded.get("approved_runtime_setting_wrapper_count") or 0,
            "approved_runtime_setting_wrappers": hardcoded.get("approved_runtime_setting_wrappers") or [],
            "migration_candidate_count": len(hardcoded.get("migration_candidates") or []),
            "registered_repeated_model_literal_groups": hardcoded["repeated_model_literal_count"],
            "registered_repeated_backend_literal_groups": hardcoded["repeated_backend_literal_count"],
        },
        "object_governance": {
            "tenant_id": seed_tenant_id,
            "coverage": object_governance,
            "concrete_coverage": concrete_object_governance,
            "operational_views": object_governance_views,
            "coverage_error_count": len(object_governance_errors),
            "coverage_errors": object_governance_errors,
        },
        "catalog_operational_views": catalog_views,
        "archive_candidate_registry": {
            "tenant_id": seed_tenant_id,
            "row_count": archive_candidates["row_count"],
            "duplicate_key_count": archive_candidates["duplicate_key_count"],
            "missing_source_hash_count": archive_candidates["missing_source_hash_count"],
            "max_severity_score": archive_candidates["max_severity_score"],
            "by_status": archive_candidates["by_status"],
            "by_source_kind": archive_candidates["by_source_kind"],
            "by_suggested_action": archive_candidates["by_suggested_action"],
            "severity_buckets": archive_candidates["severity_buckets"],
        },
        "manifest_import_registry": {
            "batch_id": manifest_import["batch_id"],
            "batch_count": manifest_import["batch_count"],
            "record_count": manifest_import["record_count"],
            "flagged_record_count": manifest_import["flagged_record_count"],
            "duplicate_record_key_count": manifest_import["duplicate_record_key_count"],
            "missing_manifest_hash_count": manifest_import["missing_manifest_hash_count"],
            "by_import_status": manifest_import["by_import_status"],
            "by_recommended_action": manifest_import["by_recommended_action"],
        },
        "catalog_reader_migration_registry": {
            "tenant_id": seed_tenant_id,
            "row_count": reader_migration["row_count"],
            "migration_candidate_count": reader_migration["migration_candidate_count"],
            "review_count": reader_migration["review_count"],
            "tracked_followup_count": reader_migration["tracked_followup_count"],
            "duplicate_key_count": reader_migration["duplicate_key_count"],
            "by_classification": reader_migration["by_classification"],
            "by_migration_status": reader_migration["by_migration_status"],
        },
        "rotted_context": {
            "candidate_count": rotted["candidate_count"],
            "severity_buckets": _severity_buckets(rotted_candidates),
            "max_severity_score": _max_severity(rotted_candidates),
            "top_candidates": rotted_candidates[:25],
            "archive_policy": rotted["archive_policy"],
        },
        "yaml_manifest_count": audit["yaml_manifests"]["manifest_count"],
        "database_migration_hint": {
            "settings": hardcoded["database_migration_hint"],
            "manifests": audit["yaml_manifests"]["database_migration_hint"],
        },
    }


def render_markdown(status: dict[str, Any]) -> str:
    state = status["status"]
    settings = status["settings_registry"]
    hardcoded = status["hardcoded_settings"]
    object_governance = status["object_governance"]
    catalog_views = status["catalog_operational_views"]
    archive_candidates = status["archive_candidate_registry"]
    manifest_import = status["manifest_import_registry"]
    reader_migration = status["catalog_reader_migration_registry"]
    rotted = status["rotted_context"]
    lines = [
        "# Registry Readiness Status",
        "",
        f"- Ready: `{state['ready']}`",
        f"- Hard-coded settings clean: `{state['hardcoded_settings_clean']}`",
        f"- Settings registry clean: `{state['settings_registry_clean']}`",
        f"- Object-governance seed coverage clean: `{state['object_governance_seed_coverage_clean']}`",
        f"- Object-governance operational views clean: `{state['object_governance_operational_views_clean']}`",
        f"- Catalog operational views clean: `{state['catalog_operational_views_clean']}`",
        f"- Archive candidate registry integrity clean: `{state['archive_candidate_registry_integrity_clean']}`",
        f"- Rotted context candidates present: `{state['rotted_context_candidates_present']}`",
        "",
        "## Settings Registry",
        "",
        f"- Rows: {settings['row_count']}",
        f"- Duplicate keys: {settings['duplicate_key_count']}",
        f"- Invalid setting kinds: {settings['invalid_setting_kind_count']}",
        "",
        "## Hard-Coded Settings",
        "",
        f"- Unregistered repeated model literal groups: {hardcoded['unregistered_repeated_model_literal_count']}",
        f"- Unregistered repeated backend literal groups: {hardcoded['unregistered_repeated_backend_literal_count']}",
        f"- Repeated unregistered vector dimension groups: {hardcoded['repeated_vector_dimension_count']}",
        f"- Private runtime setting resolver bypasses: {hardcoded['private_runtime_setting_resolver_bypass_count']}",
        f"- Approved runtime setting resolver wrappers: {hardcoded['approved_runtime_setting_wrapper_count']}",
        f"- Migration candidates: {hardcoded['migration_candidate_count']}",
        "",
        "## Object Governance",
        "",
        f"- Coverage errors: {object_governance['coverage_error_count']}",
    ]
    for table, report in sorted(object_governance["coverage"].items()):
        lines.append(
            f"- {table}: {report['row_count']} row(s), "
            f"{report['family_count']} covered familie(s), "
            f"{len(report['missing_required_families'])} missing"
        )
    lines.extend([
        "",
        "### Concrete Object Coverage",
        "",
    ])
    for table, report in sorted(object_governance["concrete_coverage"].items()):
        lines.append(
            f"- {table}: {report['row_count']} row(s), "
            f"{report['object_type_count']} covered object type(s), "
            f"{len(report['missing_object_types'])} missing"
        )
    operational_views = object_governance["operational_views"]
    lines.extend([
        "",
        "### Operational Views",
        "",
        f"- Schema ready: `{operational_views['schema_ready']}`",
        f"- Database mode: `{operational_views['database_probe']['mode']}`",
        f"- Database ready: `{operational_views['database_ready']}`",
    ])
    for view in operational_views["schema_views"]:
        lines.append(f"- {view['name']}: schema present `{view['present']}`")
    lines.extend([
        "",
        "## Catalog Operational Views",
        "",
        f"- Schema ready: `{catalog_views['schema_ready']}`",
        f"- Database mode: `{catalog_views['database_probe']['mode']}`",
        f"- Database ready: `{catalog_views['database_ready']}`",
    ])
    for view in catalog_views["schema_views"]:
        lines.append(f"- {view['name']}: schema present `{view['present']}`")
    lines.extend([
        "",
        "## Archive Candidate Registry",
        "",
        f"- Rows: {archive_candidates['row_count']}",
        f"- Duplicate keys: {archive_candidates['duplicate_key_count']}",
        f"- Missing source hashes: {archive_candidates['missing_source_hash_count']}",
        f"- Max severity score: {archive_candidates['max_severity_score']}",
    ])
    for bucket, count in archive_candidates["severity_buckets"].items():
        lines.append(f"- {bucket}: {count}")
    lines.extend([
        "",
        "## Manifest Import Registry",
        "",
        f"- Batch id: `{manifest_import['batch_id']}`",
        f"- Batches: {manifest_import['batch_count']}",
        f"- Records: {manifest_import['record_count']}",
        f"- Flagged records: {manifest_import['flagged_record_count']}",
        f"- Duplicate record keys: {manifest_import['duplicate_record_key_count']}",
        f"- Missing manifest hashes: {manifest_import['missing_manifest_hash_count']}",
    ])
    for action, count in manifest_import["by_recommended_action"].items():
        lines.append(f"- {action}: {count}")
    lines.extend([
        "",
        "## Catalog Reader Migration Registry",
        "",
        f"- Rows: {reader_migration['row_count']}",
        f"- Migration candidates: {reader_migration['migration_candidate_count']}",
        f"- Review rows: {reader_migration['review_count']}",
        f"- Tracked followups: {reader_migration['tracked_followup_count']}",
        f"- Duplicate keys: {reader_migration['duplicate_key_count']}",
    ])
    for status_name, count in reader_migration["by_migration_status"].items():
        lines.append(f"- {status_name}: {count}")
    lines.extend([
        "",
        "## Rotted Context",
        "",
        f"- Candidates: {rotted['candidate_count']}",
        f"- Max severity score: {rotted['max_severity_score']}",
    ])
    for bucket, count in rotted["severity_buckets"].items():
        lines.append(f"- {bucket}: {count}")
    return "\n".join(lines) + "\n"


def write_status(path: Path, status: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def gate_failures(
    status: dict[str, Any],
    *,
    require_ready: bool = False,
    require_live_database: bool = False,
    max_rotted_severity: int | None = None,
    max_archive_registry_severity: int | None = None,
    require_archive_registry_integrity: bool = False,
) -> list[str]:
    """Return operator-selected readiness gate failures."""
    failures: list[str] = []
    if require_ready and not status["status"]["ready"]:
        failed = [
            key
            for key, value in sorted(status["status"].items())
            if key.endswith("_clean") and not value
        ]
        suffix = f": {', '.join(failed)}" if failed else ""
        failures.append(f"registry readiness is not clean{suffix}")
    if require_live_database:
        view_groups = (
            ("object-governance", status["object_governance"]["operational_views"]),
            ("catalog", status["catalog_operational_views"]),
        )
        for label, operational_views in view_groups:
            if operational_views["database_ready"]:
                continue
            database_probe = operational_views["database_probe"]
            error = database_probe.get("error")
            mode = database_probe.get("mode")
            detail = f" mode={mode}"
            if error:
                detail = f"{detail}; error={error}"
            failures.append(f"{label} operational views are not live-database ready;{detail}")
    if max_rotted_severity is not None:
        max_observed = int(status["rotted_context"]["max_severity_score"])
        if max_observed > max_rotted_severity:
            failures.append(
                "rotted-context severity exceeds gate: "
                f"max_observed={max_observed}; allowed={max_rotted_severity}"
            )
    if max_archive_registry_severity is not None:
        max_observed = int(status["archive_candidate_registry"]["max_severity_score"])
        if max_observed > max_archive_registry_severity:
            failures.append(
                "archive-candidate registry severity exceeds gate: "
                f"max_observed={max_observed}; allowed={max_archive_registry_severity}"
            )
    if require_archive_registry_integrity and not status["status"]["archive_candidate_registry_integrity_clean"]:
        archive_registry = status["archive_candidate_registry"]
        failures.append(
            "archive-candidate registry integrity is not clean: "
            f"duplicate_keys={archive_registry['duplicate_key_count']}; "
            f"missing_source_hashes={archive_registry['missing_source_hash_count']}"
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", default="system", help="Tenant id for setting_profile seed rows.")
    parser.add_argument("--seed-tenant-id", default="seed", help="Tenant id for object-governance seed rows.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get(DEFAULT_DATABASE_URL_ENV, ""),
        help=(
            "Optional Postgres URL for live object-governance view probing. "
            f"Defaults to ${DEFAULT_DATABASE_URL_ENV} when set."
        ),
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument(
        "--write-default",
        action="store_true",
        help=f"Write {DEFAULT_OUTPUT.relative_to(ROOT)} and print the path.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero when the consolidated readiness status is not clean.",
    )
    parser.add_argument(
        "--require-live-database",
        action="store_true",
        help=(
            "Exit non-zero unless object-governance and catalog operational "
            "views are present and countable in the configured database."
        ),
    )
    parser.add_argument(
        "--max-rotted-severity",
        type=int,
        choices=range(0, 6),
        metavar="0..5",
        help=(
            "Exit non-zero when the rotted-context audit reports a candidate "
            "above this severity score. This is non-destructive and never "
            "archives files."
        ),
    )
    parser.add_argument(
        "--max-archive-registry-severity",
        type=int,
        choices=range(0, 6),
        metavar="0..5",
        help=(
            "Exit non-zero when the context_archive_candidate registry export "
            "reports a candidate above this severity score. This checks the "
            "database seed/export surface, not file moves."
        ),
    )
    parser.add_argument(
        "--require-archive-registry-integrity",
        action="store_true",
        help=(
            "Exit non-zero when context_archive_candidate seed/export rows "
            "have duplicate keys or missing source hashes."
        ),
    )
    args = parser.parse_args(argv)

    status = readiness_status(
        tenant_id=args.tenant_id,
        seed_tenant_id=args.seed_tenant_id,
        database_url=args.database_url,
    )
    if args.write_default:
        path = write_status(DEFAULT_OUTPUT, status)
        print(str(path.relative_to(ROOT)))
    elif args.format == "markdown":
        print(render_markdown(status), end="")
    else:
        print(json.dumps(status, indent=2, sort_keys=True))

    failures = gate_failures(
        status,
        require_ready=args.require_ready,
        require_live_database=args.require_live_database,
        max_rotted_severity=args.max_rotted_severity,
        max_archive_registry_severity=args.max_archive_registry_severity,
        require_archive_registry_integrity=args.require_archive_registry_integrity,
    )
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
