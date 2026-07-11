#!/usr/bin/env python3
"""Export database seed rows for required object-governance families.

The object governance package makes business/database objects explicit database
contracts instead of loose YAML prose. This exporter owns the baseline
`object_governance_profile` rows expected by release drift checks.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._config import (
    OBJECT_GOVERNANCE_CONCRETE_OBJECTS,
    OBJECT_GOVERNANCE_FAMILY_PROFILES,
    OBJECT_GOVERNANCE_REQUIRED_FAMILIES,
    OBJECT_GOVERNANCE_RUBRIC_ID,
)

DEFAULT_SEED_DIR = _resource("db") / "seeds" / "object-governance"
DEFAULT_PROFILE_SEED = DEFAULT_SEED_DIR / "object_governance_profile.jsonl"
DEFAULT_CONCRETE_PROFILE_SEED = DEFAULT_SEED_DIR / "concrete_object_governance_profile.jsonl"
DEFAULT_CONTRACT_SEED = DEFAULT_SEED_DIR / "object_contract.jsonl"
DEFAULT_CONCRETE_CONTRACT_SEED = DEFAULT_SEED_DIR / "concrete_object_contract.jsonl"
DEFAULT_SCHEMA_SEED = DEFAULT_SEED_DIR / "object_schema_profile.jsonl"
DEFAULT_CONCRETE_SCHEMA_SEED = DEFAULT_SEED_DIR / "concrete_object_schema_profile.jsonl"
DEFAULT_LAYOUT_SEED = DEFAULT_SEED_DIR / "object_layout_profile.jsonl"
DEFAULT_CONCRETE_LAYOUT_SEED = DEFAULT_SEED_DIR / "concrete_object_layout_profile.jsonl"
DEFAULT_DIAGRAM_SEED = DEFAULT_SEED_DIR / "object_architecture_diagram.jsonl"
DEFAULT_CONCRETE_DIAGRAM_SEED = DEFAULT_SEED_DIR / "concrete_object_architecture_diagram.jsonl"
DEFAULT_CONTEXT_RULE_SEED = DEFAULT_SEED_DIR / "object_context_rule.jsonl"
DEFAULT_CONCRETE_CONTEXT_RULE_SEED = DEFAULT_SEED_DIR / "concrete_object_context_rule.jsonl"
PROFILE_VERSION = "0.1.0"

PACKAGE_SEED_FILES = {
    "object_governance_profile": DEFAULT_PROFILE_SEED,
    "object_contract": DEFAULT_CONTRACT_SEED,
    "object_schema_profile": DEFAULT_SCHEMA_SEED,
    "object_layout_profile": DEFAULT_LAYOUT_SEED,
    "object_architecture_diagram": DEFAULT_DIAGRAM_SEED,
    "object_context_rule": DEFAULT_CONTEXT_RULE_SEED,
}
CONCRETE_PROFILE_VERSION = "0.1.0"
CONCRETE_SEED_FILES = {
    "object_governance_profile": DEFAULT_CONCRETE_PROFILE_SEED,
    "object_contract": DEFAULT_CONCRETE_CONTRACT_SEED,
    "object_schema_profile": DEFAULT_CONCRETE_SCHEMA_SEED,
    "object_layout_profile": DEFAULT_CONCRETE_LAYOUT_SEED,
    "object_architecture_diagram": DEFAULT_CONCRETE_DIAGRAM_SEED,
    "object_context_rule": DEFAULT_CONCRETE_CONTEXT_RULE_SEED,
}
SCHEMA_KIND_PRIORITY = (
    "document",
    "relational",
    "event",
    "wide_columnar",
    "long_attribute",
    "graph",
    "vector_metadata",
)


def _profile_id(*, tenant_id: str, family: str) -> str:
    return f"ogp:{tenant_id}:{family}"


def _schema_ref(family: str) -> str:
    return f"schema://baltor/object-governance/{family.replace('_', '-')}/baseline"


def _contract_ref(family: str) -> str:
    return f"contract://baltor/object-governance/{family.replace('_', '-')}/baseline"


def _layout_ref(family: str) -> str:
    return f"layout://baltor/object-governance/{family.replace('_', '-')}/admin-detail"


def _diagram_ref(family: str) -> str:
    return f"diagram://baltor/object-governance/{family.replace('_', '-')}/storage-mapping"


def _context_rules(family: str) -> list[str]:
    prefix = f"rule://baltor/object-governance/{family.replace('_', '-')}"
    return [
        f"{prefix}/source-of-truth-required",
        f"{prefix}/required-context-fields",
        f"{prefix}/schema-evolution-policy",
        f"{prefix}/cloud-storage-mapping",
    ]


def _object_slug(object_type: str) -> str:
    return object_type.replace("_", "-")


def _schema_kind_for(family_profile: dict[str, Any]) -> str:
    styles = [str(style) for style in family_profile.get("schema_styles") or []]
    for candidate in SCHEMA_KIND_PRIORITY:
        if candidate in styles:
            return candidate
    return "document"


def object_governance_profile_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return deterministic seed rows for object_governance_profile."""
    rows: list[dict[str, Any]] = []
    for family in OBJECT_GOVERNANCE_REQUIRED_FAMILIES:
        profile = deepcopy(OBJECT_GOVERNANCE_FAMILY_PROFILES[family])
        object_type = profile["object_type"]
        rows.append(
            {
                "object_governance_profile_id": _profile_id(tenant_id=tenant_id, family=family),
                "tenant_id": tenant_id,
                "object_type": object_type,
                "object_family": family,
                "display_name": profile["display_name"],
                "description": profile["description"],
                "owner_team": "platform-architecture",
                "steward": "object-governance",
                "lifecycle": {
                    "status": "active",
                    "version": PROFILE_VERSION,
                    "source": "scripts.db.object_governance_registry",
                },
                "required_rubrics": [OBJECT_GOVERNANCE_RUBRIC_ID],
                "required_contracts": [_contract_ref(family)],
                "required_schemas": [_schema_ref(family)],
                "required_layouts": [_layout_ref(family)],
                "required_diagrams": [_diagram_ref(family)],
                "required_context_rules": _context_rules(family),
                "required_relationships": profile["required_relationships"],
                "required_dimensions": profile["required_dimensions"],
                "required_events": [
                    f"{object_type}.created",
                    f"{object_type}.updated",
                    f"{object_type}.governance_reviewed",
                ],
                "database_mapping": profile["database_mapping"],
                "cloud_mapping": {
                    "compatible_backends": profile["cloud_compatibility"],
                    "deployment_note": "Map to managed cloud services without changing the object contract.",
                },
                "policy": {
                    "unknown_attributes": "preserve_under_facets",
                    "source_of_truth_required": True,
                    "schema_changes": "additive_unless_contract_reviewed",
                    "large_payloads": "object_storage_or_external_uri",
                },
                "body": {
                    "schema_styles": profile["schema_styles"],
                    "registry_owner": "scripts._config.OBJECT_GOVERNANCE_FAMILY_PROFILES",
                    "notes": [
                        "Generated seed row. Do not hand-edit without updating the registry.",
                        "Rubrics, masks, transformers, contracts, layouts, and diagrams can be modeled as context objects.",
                    ],
                },
            }
        )
    return rows


def _concrete_items() -> list[dict[str, Any]]:
    return [deepcopy(item) for item in OBJECT_GOVERNANCE_CONCRETE_OBJECTS]


def concrete_object_governance_profile_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return deterministic seed rows for concrete object_governance_profile records."""
    rows: list[dict[str, Any]] = []
    for item in OBJECT_GOVERNANCE_CONCRETE_OBJECTS:
        family = str(item["object_family"])
        family_profile = OBJECT_GOVERNANCE_FAMILY_PROFILES[family]
        object_type = str(item["object_type"])
        object_slug = object_type.replace("_", "-")
        family_slug = family.replace("_", "-")
        rows.append(
            {
                "object_governance_profile_id": f"ogp:{tenant_id}:object:{object_type}",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "object_family": family,
                "display_name": item["display_name"],
                "description": item["description"],
                "owner_team": item.get("owner_team") or family_profile.get("owner_team") or "platform-architecture",
                "steward": "object-governance",
                "lifecycle": {
                    "status": "draft_seed",
                    "version": CONCRETE_PROFILE_VERSION,
                    "source": "scripts._config.OBJECT_GOVERNANCE_CONCRETE_OBJECTS",
                    "inherits_family_profile": family_profile["object_type"],
                },
                "required_rubrics": [OBJECT_GOVERNANCE_RUBRIC_ID],
                "required_contracts": [f"contract://baltor/object-governance/{object_slug}/baseline"],
                "required_schemas": [f"schema://baltor/object-governance/{object_slug}/baseline"],
                "required_layouts": [f"layout://baltor/object-governance/{object_slug}/admin-detail"],
                "required_diagrams": [f"diagram://baltor/object-governance/{object_slug}/relationship-map"],
                "required_context_rules": [
                    f"rule://baltor/object-governance/{object_slug}/required-context",
                    f"rule://baltor/object-governance/{object_slug}/policy-boundary",
                    f"rule://baltor/object-governance/{object_slug}/lineage-required",
                ],
                "required_relationships": item["required_relationships"],
                "required_dimensions": item["required_dimensions"],
                "required_events": item["required_events"],
                "database_mapping": item["database_mapping"],
                "cloud_mapping": {
                    "inherits_family": family_slug,
                    "compatible_backends": family_profile["cloud_compatibility"],
                    "schema_styles": family_profile["schema_styles"],
                },
                "policy": {
                    "source_of_truth_required": True,
                    "acl_before_model": family in {"account_management", "context", "identity", "policy", "connection"},
                    "raw_sensitive_fields_require_mask": True,
                    "audit_required": True,
                },
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "family_profile_object_type": family_profile["object_type"],
                    "registry_owner": "scripts._config.OBJECT_GOVERNANCE_CONCRETE_OBJECTS",
                    "next_required_rows": [
                        "object_contract",
                        "object_schema_profile",
                        "object_layout_profile",
                        "object_architecture_diagram",
                        "object_context_rule",
                    ],
                },
            }
        )
    return rows


def concrete_object_contract_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return baseline concrete object_contract rows for object governance."""
    rows: list[dict[str, Any]] = []
    for item in _concrete_items():
        object_type = str(item["object_type"])
        object_slug = _object_slug(object_type)
        family = str(item["object_family"])
        contract_kind = str(item.get("contract_kind") or "context")
        rows.append(
            {
                "object_contract_id": f"oc:{tenant_id}:object:{object_type}:{contract_kind}",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "contract_kind": contract_kind,
                "name": f"{object_slug}-baseline-{contract_kind}-contract",
                "version": CONCRETE_PROFILE_VERSION,
                "applies_to_actions": item.get("contract_actions") or [
                    "create",
                    "read",
                    "update",
                    "index",
                    "retrieve",
                    "audit",
                ],
                "inputs": {
                    "required": item.get("contract_inputs_required") or [
                        "tenant_id",
                        f"{object_type}_id",
                        "source_of_truth",
                        "policy_context",
                    ],
                    "optional": item.get("contract_inputs_optional") or [
                        "facets",
                        "relationships",
                        "dimensions",
                        "lineage_refs",
                    ],
                },
                "outputs": {
                    "required": item.get("contract_outputs_required") or [
                        "governed_object_row",
                        "audit_event",
                        "source_handle_or_database_ref",
                    ],
                },
                "invariants": item.get("contract_invariants") or [
                    "source of truth is declared before runtime use",
                    "ACL and policy context are evaluated before model access",
                    "lineage and audit references are retained for material changes",
                ],
                "failure_modes": item.get("contract_failure_modes") or [
                    "object row exists without required context rules",
                    "derived projection treated as canonical source",
                    "sensitive fields exposed without mask contract",
                ],
                "compatibility": {
                    "object_family": family,
                    "storage_styles": OBJECT_GOVERNANCE_FAMILY_PROFILES[family]["schema_styles"],
                    "cloud": OBJECT_GOVERNANCE_FAMILY_PROFILES[family]["cloud_compatibility"],
                },
                "policy": {
                    "source_of_truth_required": True,
                    "audit_required": True,
                    "mask_sensitive_fields": True,
                },
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "specialization_level": item.get("specialization_level", "generic"),
                    "registry_owner": "scripts._config.OBJECT_GOVERNANCE_CONCRETE_OBJECTS",
                    "description": item["description"],
                },
            }
        )
    return rows


def concrete_object_schema_profile_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return baseline concrete object_schema_profile rows."""
    rows: list[dict[str, Any]] = []
    for item in _concrete_items():
        object_type = str(item["object_type"])
        object_slug = _object_slug(object_type)
        family = str(item["object_family"])
        family_profile = OBJECT_GOVERNANCE_FAMILY_PROFILES[family]
        schema_kind = str(item.get("schema_kind") or _schema_kind_for(family_profile))
        rows.append(
            {
                "object_schema_profile_id": f"osp:{tenant_id}:object:{object_type}:baseline",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "schema_kind": schema_kind,
                "schema_ref": f"schema://baltor/object-governance/{object_slug}/baseline",
                "version": CONCRETE_PROFILE_VERSION,
                "required_fields": item.get("schema_required_fields") or [
                    f"{object_type}_id",
                    "tenant_id",
                    "lifecycle_state",
                    "source_of_truth",
                    "audit_refs",
                ],
                "optional_fields": item.get("schema_optional_fields") or [
                    "facets",
                    "relationships",
                    "dimension_values",
                    "lineage_refs",
                    "cloud_mapping",
                    "policy",
                ],
                "promoted_indexes": item.get("schema_promoted_indexes") or [
                    "tenant_id",
                    f"{object_type}_id",
                    "lifecycle_state",
                    "source_of_truth",
                ],
                "validation": {
                    "unknown_attributes_preserved_under_facets": True,
                    "source_of_truth_required": True,
                    "policy_context_required": True,
                    **(item.get("schema_validation") or {}),
                },
                "evolution_policy": {
                    "additive_fields_allowed": True,
                    "breaking_changes_require_contract_review": True,
                    "deprecated_fields_remain_readable": True,
                    **(item.get("schema_evolution_policy") or {}),
                },
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "specialization_level": item.get("specialization_level", "generic"),
                    "object_family": family,
                    "family_schema_styles": family_profile["schema_styles"],
                    "database_mapping": item["database_mapping"],
                },
            }
        )
    return rows


def concrete_object_layout_profile_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return baseline concrete object_layout_profile rows."""
    rows: list[dict[str, Any]] = []
    for item in _concrete_items():
        object_type = str(item["object_type"])
        rows.append(
            {
                "object_layout_profile_id": f"olp:{tenant_id}:object:{object_type}:admin",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "layout_kind": "admin_detail",
                "version": CONCRETE_PROFILE_VERSION,
                "audience": "object_steward",
                "sections": item.get("layout_sections") or [
                    "overview",
                    "source_of_truth",
                    "relationships",
                    "dimensions",
                    "lifecycle",
                    "policy",
                    "lineage",
                    "audit",
                ],
                "actions": item.get("layout_actions") or [
                    "view_object",
                    "open_source_of_truth",
                    "view_relationships",
                    "view_audit",
                    "export_governance_package",
                ],
                "masks": item.get("layout_masks") or [
                    "mask_sensitive_fields_by_role",
                    "hide_secret_values",
                    "hide_unapproved_raw_context",
                ],
                "accessibility": {
                    "sections_have_headings": True,
                    "risk_states_have_text": True,
                    "relationship_tables_have_headers": True,
                },
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "specialization_level": item.get("specialization_level", "generic"),
                    "layout_goal": f"show operational governance state for {object_type}",
                },
            }
        )
    return rows


def concrete_object_architecture_diagram_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return baseline concrete object_architecture_diagram rows."""
    rows: list[dict[str, Any]] = []
    for item in _concrete_items():
        object_type = str(item["object_type"])
        display_name = str(item["display_name"])
        relationships = [str(value) for value in item["required_relationships"][:3]]
        relationship_lines = "\n".join(
            f"  Object -->|{relationship}| Related{index}[Related Object {index}]"
            for index, relationship in enumerate(relationships, start=1)
        )
        rows.append(
            {
                "object_architecture_diagram_id": f"oad:{tenant_id}:object:{object_type}:relationship-map",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "diagram_kind": "relationship",
                "title": f"{display_name} governance relationship map",
                "version": CONCRETE_PROFILE_VERSION,
                "diagram_format": "mermaid",
                "diagram_text": (
                    "flowchart LR\n"
                    f"  Source[Source of Truth] --> Object[{display_name}]\n"
                    f"{relationship_lines}\n"
                    f"  Object --> Audit[Audit Event]\n"
                    f"  Object --> Policy[Policy Decision]"
                ),
                "diagram_uri": None,
                "related_objects": [object_type, *relationships],
                "source_handles": [
                    "docs://architecture/baltor-business-object-governance-standard#governance-package"
                ],
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "object_family": item["object_family"],
                },
            }
        )
    return rows


def concrete_object_context_rule_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return baseline concrete object_context_rule rows."""
    rows: list[dict[str, Any]] = []
    for item in _concrete_items():
        object_type = str(item["object_type"])
        rows.append(
            {
                "object_context_rule_id": f"ocr:{tenant_id}:object:{object_type}:required-context",
                "tenant_id": tenant_id,
                "object_type": object_type,
                "rule_kind": "required_context",
                "name": f"{_object_slug(object_type)}-required-context",
                "severity": "blocker",
                "applies_to_actions": [
                    "create",
                    "read",
                    "index",
                    "retrieve",
                    "mutate",
                    "export",
                ],
                "condition": {"when": f"{object_type}_is_used_by_runtime_or_agent"},
                "requirement": {
                    "must_load": item.get("context_rule_must_load") or [
                        f"{object_type}_id",
                        "tenant_id",
                        "source_of_truth",
                        "lifecycle_state",
                        "policy_context",
                        "audit_refs",
                    ],
                    "must_forbid": item.get("context_rule_must_forbid") or [
                        "plaintext_secrets",
                        "unapproved_raw_sensitive_context",
                        "unversioned_policy_override",
                    ],
                },
                "evidence_required": (
                    f"{item['display_name']} context must prove source of truth, "
                    "policy boundary, lifecycle state, and audit lineage before "
                    "agents or hosted workflows use it."
                ),
                "body": {
                    "seed_scope": "concrete_object_baseline",
                    "specialization_level": item.get("specialization_level", "generic"),
                    "required_dimensions": item["required_dimensions"],
                    "required_relationships": item["required_relationships"],
                },
            }
        )
    return rows


def summary(*, tenant_id: str = "seed") -> dict[str, Any]:
    rows = object_governance_profile_rows(tenant_id=tenant_id)
    concrete_rows = concrete_object_governance_profile_rows(tenant_id=tenant_id)
    families = [row["object_family"] for row in rows]
    missing = [family for family in OBJECT_GOVERNANCE_REQUIRED_FAMILIES if family not in families]
    seed_coverage = package_seed_coverage(tenant_id=tenant_id)
    return {
        "tenant_id": tenant_id,
        "row_count": len(rows),
        "concrete_object_row_count": len(concrete_rows),
        "families": families,
        "missing_required_families": missing,
        "seed_path": str(DEFAULT_PROFILE_SEED.relative_to(ROOT)),
        "concrete_seed_path": str(DEFAULT_CONCRETE_PROFILE_SEED.relative_to(ROOT)),
        "seed_coverage": seed_coverage,
        "concrete_seed_coverage": concrete_seed_coverage(tenant_id=tenant_id),
        "rows": rows,
        "concrete_rows": concrete_rows,
    }


def render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Object Governance Registry",
        "",
        f"- Tenant: `{report['tenant_id']}`",
        f"- Rows: {report['row_count']}",
        f"- Concrete object rows: {report['concrete_object_row_count']}",
        f"- Missing required families: {len(report['missing_required_families'])}",
        f"- Default seed path: `{report['seed_path']}`",
        f"- Concrete seed path: `{report['concrete_seed_path']}`",
        "",
        "## Families",
        "",
    ]
    for family in report["families"]:
        lines.append(f"- {family}")
    lines.extend(["", "## Seed Coverage", ""])
    coverage = report.get("seed_coverage") or {}
    for table, table_report in sorted(coverage.items()):
        missing = table_report.get("missing_required_families") or []
        lines.append(
            "- {table}: {rows} row(s), {family_count} covered familie(s), "
            "{missing_count} missing".format(
                table=table,
                rows=table_report.get("row_count", 0),
                family_count=table_report.get("family_count", 0),
                missing_count=len(missing),
            )
        )
    lines.extend(["", "## Concrete Seed Coverage", ""])
    concrete_coverage = report.get("concrete_seed_coverage") or {}
    for table, table_report in sorted(concrete_coverage.items()):
        missing = table_report.get("missing_object_types") or []
        lines.append(
            "- {table}: {rows} row(s), {object_count} covered object type(s), "
            "{missing_count} missing".format(
                table=table,
                rows=table_report.get("row_count", 0),
                object_count=table_report.get("object_type_count", 0),
                missing_count=len(missing),
            )
        )
    return "\n".join(lines) + "\n"


def write_default_seed(*, tenant_id: str = "seed") -> Path:
    rows = object_governance_profile_rows(tenant_id=tenant_id)
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_PROFILE_SEED.write_text(render_jsonl(rows), encoding="utf-8")
    return DEFAULT_PROFILE_SEED


def write_concrete_seed(*, tenant_id: str = "seed") -> Path:
    rows = concrete_object_governance_profile_rows(tenant_id=tenant_id)
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONCRETE_PROFILE_SEED.write_text(render_jsonl(rows), encoding="utf-8")
    return DEFAULT_CONCRETE_PROFILE_SEED


def write_concrete_package_seeds(*, tenant_id: str = "seed") -> list[Path]:
    """Write all concrete object-governance seed row files."""
    writers: list[tuple[Path, list[dict[str, Any]]]] = [
        (DEFAULT_CONCRETE_PROFILE_SEED, concrete_object_governance_profile_rows(tenant_id=tenant_id)),
        (DEFAULT_CONCRETE_CONTRACT_SEED, concrete_object_contract_rows(tenant_id=tenant_id)),
        (DEFAULT_CONCRETE_SCHEMA_SEED, concrete_object_schema_profile_rows(tenant_id=tenant_id)),
        (DEFAULT_CONCRETE_LAYOUT_SEED, concrete_object_layout_profile_rows(tenant_id=tenant_id)),
        (DEFAULT_CONCRETE_DIAGRAM_SEED, concrete_object_architecture_diagram_rows(tenant_id=tenant_id)),
        (DEFAULT_CONCRETE_CONTEXT_RULE_SEED, concrete_object_context_rule_rows(tenant_id=tenant_id)),
    ]
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    for path, rows in writers:
        path.write_text(render_jsonl(rows), encoding="utf-8")
    return [path for path, _ in writers]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _families_from_rows(rows: list[dict[str, Any]]) -> set[str]:
    families = {str(row["object_family"]) for row in rows if row.get("object_family")}
    if families:
        return families
    object_type_to_family = {
        profile["object_type"]: family
        for family, profile in OBJECT_GOVERNANCE_FAMILY_PROFILES.items()
    }
    return {
        object_type_to_family[str(row["object_type"])]
        for row in rows
        if row.get("object_type") in object_type_to_family
    }


def _object_types_from_rows(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row["object_type"]) for row in rows if row.get("object_type")}


def package_seed_coverage(*, tenant_id: str = "seed") -> dict[str, Any]:
    """Return table-level coverage for the object-governance seed package."""
    report: dict[str, Any] = {}
    required = set(OBJECT_GOVERNANCE_REQUIRED_FAMILIES)
    for table, path in PACKAGE_SEED_FILES.items():
        try:
            rows = [
                row for row in _load_jsonl(path)
                if row.get("tenant_id", tenant_id) == tenant_id
            ]
        except json.JSONDecodeError as exc:
            report[table] = {
                "path": str(path.relative_to(ROOT)),
                "row_count": 0,
                "family_count": 0,
                "missing_required_families": sorted(required),
                "error": f"invalid JSONL: {exc}",
            }
            continue
        families = _families_from_rows(rows)
        report[table] = {
            "path": str(path.relative_to(ROOT)),
            "row_count": len(rows),
            "family_count": len(families),
            "families": sorted(families),
            "missing_required_families": sorted(required - families),
        }
    return report


def concrete_seed_coverage(*, tenant_id: str = "seed") -> dict[str, Any]:
    """Return table-level object-type coverage for concrete seed files."""
    report: dict[str, Any] = {}
    required = {str(item["object_type"]) for item in OBJECT_GOVERNANCE_CONCRETE_OBJECTS}
    for table, path in CONCRETE_SEED_FILES.items():
        try:
            rows = [
                row for row in _load_jsonl(path)
                if row.get("tenant_id", tenant_id) == tenant_id
            ]
        except json.JSONDecodeError as exc:
            report[table] = {
                "path": str(path.relative_to(ROOT)),
                "row_count": 0,
                "object_type_count": 0,
                "missing_object_types": sorted(required),
                "error": f"invalid JSONL: {exc}",
            }
            continue
        object_types = _object_types_from_rows(rows)
        report[table] = {
            "path": str(path.relative_to(ROOT)),
            "row_count": len(rows),
            "object_type_count": len(object_types),
            "object_types": sorted(object_types),
            "missing_object_types": sorted(required - object_types),
        }
    return report


def package_seed_coverage_errors(*, tenant_id: str = "seed") -> list[str]:
    """Return human-readable coverage errors for required package seed files."""
    errors: list[str] = []
    coverage = package_seed_coverage(tenant_id=tenant_id)
    for table, table_report in sorted(coverage.items()):
        missing = table_report.get("missing_required_families") or []
        if table_report.get("error"):
            errors.append(f"{table}: {table_report['error']}")
        if missing:
            errors.append(
                f"{table}: missing required families {', '.join(missing)} "
                f"in {table_report['path']}"
            )
    concrete_coverage = concrete_seed_coverage(tenant_id=tenant_id)
    for table, table_report in sorted(concrete_coverage.items()):
        missing = table_report.get("missing_object_types") or []
        if table_report.get("error"):
            errors.append(f"concrete {table}: {table_report['error']}")
        if missing:
            errors.append(
                f"concrete {table}: missing object types {', '.join(missing)} "
                f"in {table_report['path']}"
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", default="seed", help="Tenant id for seed rows.")
    parser.add_argument("--format", choices=("json", "jsonl", "markdown"), default="json")
    parser.add_argument("--rows-only", action="store_true", help="Emit rows instead of summary metadata.")
    parser.add_argument(
        "--concrete-objects",
        action="store_true",
        help="Emit concrete object_governance_profile rows instead of family baseline rows.",
    )
    parser.add_argument(
        "--check-seed-coverage",
        action="store_true",
        help="Exit non-zero when required object-governance seed files are missing families.",
    )
    parser.add_argument(
        "--write-default-seeds",
        action="store_true",
        help=f"Write {DEFAULT_PROFILE_SEED.relative_to(ROOT)} from the registry.",
    )
    parser.add_argument(
        "--write-concrete-seeds",
        action="store_true",
        help=f"Write {DEFAULT_CONCRETE_PROFILE_SEED.relative_to(ROOT)} from the registry.",
    )
    parser.add_argument(
        "--write-concrete-package-seeds",
        action="store_true",
        help="Write all concrete object-governance package seed files from the registry.",
    )
    args = parser.parse_args()

    if args.write_default_seeds:
        path = write_default_seed(tenant_id=args.tenant_id)
        print(str(path.relative_to(ROOT)))
        return

    if args.write_concrete_seeds:
        path = write_concrete_seed(tenant_id=args.tenant_id)
        print(str(path.relative_to(ROOT)))
        return

    if args.write_concrete_package_seeds:
        for path in write_concrete_package_seeds(tenant_id=args.tenant_id):
            print(str(path.relative_to(ROOT)))
        return

    if args.check_seed_coverage:
        errors = package_seed_coverage_errors(tenant_id=args.tenant_id)
        if errors:
            for error in errors:
                print(error)
            raise SystemExit(1)
        print("object governance seed coverage ok")
        return

    rows = (
        concrete_object_governance_profile_rows(tenant_id=args.tenant_id)
        if args.concrete_objects
        else object_governance_profile_rows(tenant_id=args.tenant_id)
    )
    payload: Any = rows if args.rows_only else summary(tenant_id=args.tenant_id)
    if args.format == "markdown":
        if args.rows_only:
            print(render_jsonl(rows), end="")
        else:
            print(render_markdown(payload), end="")
    elif args.format == "jsonl":
        print(render_jsonl(rows), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
