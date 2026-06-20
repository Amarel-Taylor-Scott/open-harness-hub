#!/usr/bin/env python3
"""Export all repo-owned settings registries as database seed rows.

This is the consolidated bridge from Python/YAML seed constants to the
`setting_profile` table. It intentionally emits rows only; loading/upserting
them is a deployment concern.
"""
from __future__ import annotations

import argparse
import ast
import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts._config import (
    ADMIN_DEMO_RUNTIME_SETTINGS,
    BACKEND_FAMILY_TERMS,
    CONTEXT_GATEWAY_RUNTIME_SETTINGS,
    CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS,
    CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS,
    CONTEXT_WORKER_RUNTIME_SETTINGS,
    DEFAULT_CATALOG_ROW_DIR,
    LOAD_PLAN_TERMS,
    OH_CATALOG_ROW_DIR_ENV,
    OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH,
    OBJECT_GOVERNANCE_RUBRIC_ID,
    OBJECT_GOVERNANCE_STANDARD_DOC_PATH,
    REGISTERED_COMPONENT_REF_IDS,
    NODE_RESEARCH_RUNTIME_SETTINGS,
    REPO_ROOT,
    VECTOR_STORAGE_BACKENDS,
)
from scripts.db.model_runtime_registry import setting_profile_seed_rows as model_setting_rows
from scripts.db.vector_config_registry import setting_profile_seed_rows as vector_setting_rows

DEFAULT_SEED_DIR = REPO_ROOT / "db" / "seeds" / "settings-registry"
DEFAULT_SEED_FILE = DEFAULT_SEED_DIR / "setting_profile.jsonl"
DEFAULT_LOAD_SQL = DEFAULT_SEED_DIR / "load-setting-profile.sql"
NODE_RESEARCH_WORKER_PATH = REPO_ROOT / "scripts" / "context_workers" / "workers" / "node_research.py"

ALLOWED_SETTING_KINDS = {
    "model_route",
    "embedding_model",
    "rerank_model",
    "judge_model",
    "vector_index",
    "storage_backend",
    "cloud_backend",
    "threshold",
    "batching",
    "feature_flag",
    "object_default",
    "policy",
    "custom",
}


def _setting_profile_row(
    *,
    tenant_id: str,
    namespace: str,
    setting_key: str,
    setting_kind: str,
    default_value: dict[str, Any],
    owner: str,
    validation: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if setting_kind not in ALLOWED_SETTING_KINDS:
        raise ValueError(f"unsupported setting_kind: {setting_kind}")
    setting_key_id = quote(setting_key, safe="")
    return {
        "setting_profile_id": f"setting://{tenant_id}/{namespace}/{setting_key_id}",
        "tenant_id": tenant_id,
        "namespace": namespace.replace("/", "."),
        "setting_key": setting_key,
        "setting_kind": setting_kind,
        "value_type": "json",
        "default_value": default_value,
        "allowed_values": [],
        "validation": validation or {},
        "source_of_truth": "repo_seed",
        "body": {
            "owner": owner,
            **(body or {}),
        },
    }


def _literal_assignment_from_python(path: Path, name: str) -> Any:
    """Read a top-level literal assignment without importing the module."""
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if isinstance(target, ast.Name) and target.id == name:
            return ast.literal_eval(node.value)
    raise KeyError(f"{name} not found as top-level literal assignment in {path}")


def storage_backend_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for registered storage backends/families."""
    rows: list[dict[str, Any]] = []
    for backend_id, backend in VECTOR_STORAGE_BACKENDS.items():
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="storage.backend",
                setting_key=backend_id,
                setting_kind="storage_backend",
                default_value={"value": backend_id, **deepcopy(backend)},
                owner="scripts._config.VECTOR_STORAGE_BACKENDS",
                validation={"required": ["value", "kind", "trust_boundary"]},
            )
        )
    for family_id, family in BACKEND_FAMILY_TERMS.items():
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="storage.backend_family",
                setting_key=family_id,
                setting_kind="custom",
                default_value={"value": family_id, **deepcopy(family)},
                owner="scripts._config.BACKEND_FAMILY_TERMS",
                validation={"required": ["value", "kind"]},
            )
        )
    return rows


def terminology_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for registered load-plan terms."""
    return [
        _setting_profile_row(
            tenant_id=tenant_id,
            namespace="terminology.load_plan",
            setting_key=term,
            setting_kind="custom",
            default_value={"value": term, **deepcopy(metadata)},
            owner="scripts._config.LOAD_PLAN_TERMS",
            validation={"required": ["value", "kind"]},
            body={
                "migration_note": (
                    "Registered terminology keeps contract/field names out of "
                    "hard-coded backend-setting migration candidates."
                ),
            },
        )
        for term, metadata in sorted(LOAD_PLAN_TERMS.items())
    ]


def component_ref_registry_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for registered repeated component refs."""
    return [
        _setting_profile_row(
            tenant_id=tenant_id,
            namespace="component.ref_registry",
            setting_key=component_id,
            setting_kind="custom",
            default_value={"component_id": component_id, **deepcopy(metadata)},
            owner="scripts._config.REGISTERED_COMPONENT_REF_IDS",
            validation={"required": ["component_id", "component_type", "role", "owner"]},
            body={
                "migration_note": (
                    "Registered component refs can seed/check component_ref rows "
                    "instead of relying on repeated YAML literals."
                ),
            },
        )
        for component_id, metadata in sorted(REGISTERED_COMPONENT_REF_IDS.items())
    ]


def catalog_row_source_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for catalog row-source selection."""
    return [
        _setting_profile_row(
            tenant_id=tenant_id,
            namespace="catalog.row_source",
            setting_key="catalog_row_dir_env",
            setting_kind="custom",
            default_value={"env": OH_CATALOG_ROW_DIR_ENV},
            owner="scripts._config.OH_CATALOG_ROW_DIR_ENV",
            validation={"required": ["env"]},
            body={
                "migration_note": (
                    "Operational consumers should prefer database-shaped catalog "
                    "rows from this env override instead of walking YAML directly."
                ),
            },
        ),
        _setting_profile_row(
            tenant_id=tenant_id,
            namespace="catalog.row_source",
            setting_key="default_catalog_row_dir",
            setting_kind="custom",
            default_value={"path": str(DEFAULT_CATALOG_ROW_DIR.relative_to(REPO_ROOT))},
            owner="scripts._config.DEFAULT_CATALOG_ROW_DIR",
            validation={"required": ["path"]},
            body={
                "migration_note": (
                    "Default database-shaped bridge export used when no row-dir "
                    "override is supplied and components.jsonl exists."
                ),
            },
        ),
    ]


def object_governance_artifact_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for object-governance docs and rubric paths."""
    artifacts = {
        "standard_doc": {
            "path": str(OBJECT_GOVERNANCE_STANDARD_DOC_PATH.relative_to(REPO_ROOT)),
            "purpose": "Business-object governance standard and required context rules.",
            "owner": "scripts._config.OBJECT_GOVERNANCE_STANDARD_DOC_PATH",
        },
        "review_rubric": {
            "path": str(OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH.relative_to(REPO_ROOT)),
            "component_id": OBJECT_GOVERNANCE_RUBRIC_ID,
            "purpose": "Review rubric for object contracts, schemas, layouts, architecture diagrams, and context rules.",
            "owner": "scripts._config.OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH",
        },
    }
    return [
        _setting_profile_row(
            tenant_id=tenant_id,
            namespace="object_governance.artifact",
            setting_key=artifact_id,
            setting_kind="custom",
            default_value=deepcopy(artifact),
            owner=artifact["owner"],
            validation={"required": ["path", "purpose"]},
            body={
                "migration_note": (
                    "Admin/readiness surfaces should read object-governance "
                    "artifact locations from registry rows instead of hard-coded paths."
                ),
            },
        )
        for artifact_id, artifact in sorted(artifacts.items())
    ]


def admin_demo_runtime_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for Baltor admin-demo runtime knobs."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(ADMIN_DEMO_RUNTIME_SETTINGS.items()):
        default = setting["default"]
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.admin_demo.runtime",
                setting_key=setting_key,
                setting_kind=str(setting["setting_kind"]),
                default_value={
                    "value": default,
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                owner=f"scripts._config.ADMIN_DEMO_RUNTIME_SETTINGS.{setting_key}",
                validation={
                    "required": ["value", "env", "value_type"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Admin-demo runtime defaults are repo-seeded settings; "
                        "deployment-owned setting_value rows should override them "
                        "when the demo is hosted."
                    ),
                },
            )
        )
    return rows


def context_gateway_runtime_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for Baltor context gateway/client/cache defaults."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(CONTEXT_GATEWAY_RUNTIME_SETTINGS.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.context_gateway.runtime",
                setting_key=setting_key,
                setting_kind=str(setting["setting_kind"]),
                default_value={
                    "value": setting["default"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                owner=f"scripts._config.CONTEXT_GATEWAY_RUNTIME_SETTINGS.{setting_key}",
                validation={
                    "required": ["value", "env", "value_type"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Context gateway/client/cache defaults are repo-seeded "
                        "settings; hosted deployments should override with "
                        "setting_value rows or environment-controlled settings."
                    ),
                },
            )
        )
    return rows


def context_worker_runtime_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for context worker runtime and queue defaults."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(CONTEXT_WORKER_RUNTIME_SETTINGS.items()):
        validation = {
            "required": ["value", "env", "value_type"],
            "env": setting["env"],
            "value_type": setting["value_type"],
        }
        if setting.get("fallback_env"):
            validation["fallback_env"] = setting["fallback_env"]
        if setting.get("fallback_setting"):
            validation["fallback_setting"] = setting["fallback_setting"]
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.context_worker.runtime",
                setting_key=setting_key,
                setting_kind=str(setting["setting_kind"]),
                default_value={
                    "value": setting["default"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                    **({"fallback_env": setting["fallback_env"]} if setting.get("fallback_env") else {}),
                    **({"fallback_setting": setting["fallback_setting"]} if setting.get("fallback_setting") else {}),
                },
                owner=f"scripts._config.CONTEXT_WORKER_RUNTIME_SETTINGS.{setting_key}",
                validation=validation,
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Context worker runtime defaults are repo-seeded settings; "
                        "distributed deployments should override with setting_value rows "
                        "or environment-controlled settings."
                    ),
                },
            )
        )
    return rows


def context_tool_adapter_runtime_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for optional context adapter defaults."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.context_tool_adapter.runtime",
                setting_key=setting_key,
                setting_kind=str(setting["setting_kind"]),
                default_value={
                    "value": setting["default"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                owner=f"scripts._config.CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS.{setting_key}",
                validation={
                    "required": ["value", "env", "value_type"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Optional tool adapter runtime defaults are repo-seeded "
                        "settings; hosted deployments should override adapter "
                        "enablement, policy gates, and service/model settings "
                        "with setting_value rows."
                    ),
                },
            )
        )
    return rows


def context_tool_adapter_service_endpoint_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for optional service-backed adapter endpoints."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.context_tool_adapter.service_endpoint",
                setting_key=setting_key,
                setting_kind="storage_backend",
                default_value={
                    "value": "",
                    "env": setting["env"],
                    "value_type": "uri",
                    "category": setting["category"],
                },
                owner=f"scripts._config.CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS.{setting_key}",
                validation={
                    "required": ["value", "env", "value_type", "category"],
                    "env": setting["env"],
                    "value_type": "uri",
                    "category": setting["category"],
                },
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Optional adapter service endpoints are repo-seeded "
                        "setting_profile rows. Deployments should keep actual "
                        "endpoint values in setting_value rows or environment, "
                        "not in code or catalog YAML."
                    ),
                },
            )
        )
    return rows


def node_research_runtime_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for node research authorization/defaults."""
    rows: list[dict[str, Any]] = []
    for setting_key, setting in sorted(NODE_RESEARCH_RUNTIME_SETTINGS.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.node_research.runtime",
                setting_key=setting_key,
                setting_kind=str(setting["setting_kind"]),
                default_value={
                    "value": setting["default"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                owner=f"scripts._config.NODE_RESEARCH_RUNTIME_SETTINGS.{setting_key}",
                validation={
                    "required": ["value", "env", "value_type"],
                    "env": setting["env"],
                    "value_type": setting["value_type"],
                },
                body={
                    "description": setting["description"],
                    "migration_note": (
                        "Node research authorization and external-tool defaults "
                        "are repo-seeded settings; deployments should override "
                        "policy gates through setting_value rows."
                    ),
                },
            )
        )
    return rows


def node_research_tool_catalog_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for node-research tool catalog metadata."""
    catalog = _literal_assignment_from_python(NODE_RESEARCH_WORKER_PATH, "TOOL_CATALOG")
    rows: list[dict[str, Any]] = []
    for tool_name, spec in sorted(catalog.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.node_research.tool_catalog",
                setting_key=str(tool_name),
                setting_kind="custom",
                default_value={
                    "tool": tool_name,
                    **deepcopy(spec),
                },
                owner=f"{NODE_RESEARCH_WORKER_PATH.relative_to(REPO_ROOT)}.TOOL_CATALOG.{tool_name}",
                validation={
                    "required": ["tool", "kind", "node_types", "auth_required"],
                    "allowed_kinds": ["api", "cli", "local", "module", "service"],
                },
                body={
                    "description": "Node research tool metadata used for readiness, routing, and authorization preflight.",
                    "migration_note": (
                        "This row is exported from the current worker literal "
                        "without importing/registering workers. The next step is "
                        "to make runtime route selection read a generated/loaded "
                        "tool registry instead of this Python literal."
                    ),
                },
            )
        )
    return rows


def node_research_route_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return setting_profile rows for node-type to research-tool route defaults."""
    routes = _literal_assignment_from_python(NODE_RESEARCH_WORKER_PATH, "NODE_ROUTES")
    rows: list[dict[str, Any]] = []
    for node_type, tools in sorted(routes.items()):
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="baltor.node_research.route",
                setting_key=str(node_type),
                setting_kind="custom",
                default_value={
                    "node_type": node_type,
                    "tools": list(tools),
                },
                owner=f"{NODE_RESEARCH_WORKER_PATH.relative_to(REPO_ROOT)}.NODE_ROUTES.{node_type}",
                validation={
                    "required": ["node_type", "tools"],
                    "tool_catalog_namespace": "baltor.node_research.tool_catalog",
                },
                body={
                    "description": "Default research-tool route for a normalized node type.",
                    "migration_note": (
                        "Routes are exported as settings rows so deployments can "
                        "override node-type routing without changing worker code "
                        "once the runtime loader is introduced."
                    ),
                },
            )
        )
    return rows


def setting_profile_seed_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return all settings registry seed rows in deterministic order."""
    rows: list[dict[str, Any]] = []
    rows.extend(admin_demo_runtime_rows(tenant_id=tenant_id))
    rows.extend(context_gateway_runtime_rows(tenant_id=tenant_id))
    rows.extend(context_tool_adapter_service_endpoint_rows(tenant_id=tenant_id))
    rows.extend(context_tool_adapter_runtime_rows(tenant_id=tenant_id))
    rows.extend(context_worker_runtime_rows(tenant_id=tenant_id))
    rows.extend(node_research_runtime_rows(tenant_id=tenant_id))
    rows.extend(node_research_tool_catalog_rows(tenant_id=tenant_id))
    rows.extend(node_research_route_rows(tenant_id=tenant_id))
    rows.extend(vector_setting_rows(tenant_id=tenant_id))
    rows.extend(model_setting_rows(tenant_id=tenant_id))
    rows.extend(catalog_row_source_rows(tenant_id=tenant_id))
    rows.extend(object_governance_artifact_rows(tenant_id=tenant_id))
    rows.extend(storage_backend_rows(tenant_id=tenant_id))
    rows.extend(terminology_rows(tenant_id=tenant_id))
    rows.extend(component_ref_registry_rows(tenant_id=tenant_id))
    return sorted(rows, key=lambda row: (row["namespace"], row["setting_key"]))


def registry_summary(*, tenant_id: str = "system") -> dict[str, Any]:
    """Return counts and rows for the consolidated settings registry export."""
    rows = setting_profile_seed_rows(tenant_id=tenant_id)
    by_kind: dict[str, int] = {}
    by_namespace: dict[str, int] = {}
    for row in rows:
        by_kind[row["setting_kind"]] = by_kind.get(row["setting_kind"], 0) + 1
        by_namespace[row["namespace"]] = by_namespace.get(row["namespace"], 0) + 1
    duplicates = _duplicate_keys(rows)
    invalid = [row for row in rows if row["setting_kind"] not in ALLOWED_SETTING_KINDS]
    return {
        "tenant_id": tenant_id,
        "row_count": len(rows),
        "by_kind": dict(sorted(by_kind.items())),
        "by_namespace": dict(sorted(by_namespace.items())),
        "duplicate_key_count": len(duplicates),
        "duplicate_keys": duplicates,
        "invalid_setting_kind_count": len(invalid),
        "rows": rows,
    }


def _duplicate_keys(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    duplicates: list[dict[str, str]] = []
    for row in rows:
        key = (row["tenant_id"], row["namespace"], row["setting_key"])
        if key in seen:
            duplicates.append({
                "tenant_id": row["tenant_id"],
                "namespace": row["namespace"],
                "setting_key": row["setting_key"],
            })
        seen.add(key)
    return duplicates


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Settings Registry Export",
        "",
        f"- Tenant: `{summary['tenant_id']}`",
        f"- Rows: {summary['row_count']}",
        f"- Duplicate keys: {summary['duplicate_key_count']}",
        f"- Invalid setting kinds: {summary['invalid_setting_kind_count']}",
        "",
        "## By Kind",
        "",
    ]
    for kind, count in summary["by_kind"].items():
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## By Namespace", ""])
    for namespace, count in summary["by_namespace"].items():
        lines.append(f"- {namespace}: {count}")
    return "\n".join(lines) + "\n"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_load_sql(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sql = """-- Load setting_profile seed rows.
-- Review db/seeds/settings-registry/setting_profile.jsonl before loading.

BEGIN;

CREATE TEMP TABLE tmp_setting_profile_jsonl (
  body jsonb NOT NULL
);

\\copy tmp_setting_profile_jsonl(body) FROM 'db/seeds/settings-registry/setting_profile.jsonl' WITH (FORMAT text);

INSERT INTO setting_profile (
  setting_profile_id,
  tenant_id,
  namespace,
  setting_key,
  setting_kind,
  value_type,
  default_value,
  allowed_values,
  validation,
  source_of_truth,
  body
)
SELECT
  body->>'setting_profile_id',
  body->>'tenant_id',
  body->>'namespace',
  body->>'setting_key',
  body->>'setting_kind',
  body->>'value_type',
  body->'default_value',
  body->'allowed_values',
  body->'validation',
  body->>'source_of_truth',
  body->'body'
FROM tmp_setting_profile_jsonl
ON CONFLICT (tenant_id, namespace, setting_key)
DO UPDATE SET
  setting_kind = EXCLUDED.setting_kind,
  value_type = EXCLUDED.value_type,
  default_value = EXCLUDED.default_value,
  allowed_values = EXCLUDED.allowed_values,
  validation = EXCLUDED.validation,
  source_of_truth = EXCLUDED.source_of_truth,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
"""
    path.write_text(sql, encoding="utf-8")
    return path


def write_default(summary: dict[str, Any]) -> None:
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DEFAULT_SEED_FILE, summary["rows"])
    write_load_sql(DEFAULT_LOAD_SQL)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", default="system", help="Tenant id for seed rows.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--rows-only",
        action="store_true",
        help="Emit only setting_profile seed rows instead of summary metadata.",
    )
    parser.add_argument(
        "--write-default",
        action="store_true",
        help=f"Write {DEFAULT_SEED_DIR.relative_to(REPO_ROOT)}.",
    )
    args = parser.parse_args()

    summary = registry_summary(tenant_id=args.tenant_id)
    if args.write_default:
        write_default(summary)
        print(str(DEFAULT_SEED_DIR.relative_to(REPO_ROOT)))
        return

    payload: Any
    if args.rows_only:
        payload = summary["rows"]
    else:
        payload = summary

    if args.format == "markdown":
        if args.rows_only:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
