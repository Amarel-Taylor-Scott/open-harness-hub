#!/usr/bin/env python3
"""Generate first-principles business-operation primitive search scopes.

This creates candidate-only multilingual search scopes by crossing universal
operation atoms with business functions, roles, systems, data objects,
geographies, and technology surfaces.

The output uses the same JSONL shape consumed by
``_repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py``. It does not fetch sources,
copy source bodies, implement primitives, or promote truth. It creates a large
question/search grid so the foundry can ask what each business area actually
does from first principles:

    communicate -> store -> transform -> decide -> route -> prove

Use ``--max-rows 0`` for the full cross-product. Use ``--offset`` and
``--max-rows`` to shard long-running workers.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = _resource("catalog") / "knowledge-packs" / "data" / "aidevobserver-business-operation-scopes"
DEFAULT_SCOPE_FILE = DEFAULT_OUT_DIR / "scopes.jsonl"
DEFAULT_SUMMARY_FILE = DEFAULT_OUT_DIR / "summary.md"
DEFAULT_MAX_ROWS = 25_000

PROVIDERS = (
    "github_code",
    "github_repositories",
    "documentation_search",
    "data_portals",
    "rss_news",
    "forum_search",
    "package_indexes",
)

OPERATION_ATOMS = (
    "observe",
    "identify",
    "collect",
    "validate",
    "communicate",
    "store",
    "retrieve",
    "transform",
    "compute",
    "compare",
    "decide",
    "route",
    "schedule",
    "allocate",
    "approve",
    "transact",
    "fulfill",
    "monitor",
    "measure",
    "report",
    "audit",
    "reconcile",
    "notify",
    "escalate",
    "comply",
    "secure",
    "recover",
    "learn",
)

FUNCTION_AREAS = (
    "sales",
    "marketing",
    "customer support",
    "customer success",
    "finance",
    "accounting",
    "procurement",
    "supply chain",
    "warehouse operations",
    "manufacturing operations",
    "field service",
    "human resources",
    "recruiting",
    "legal",
    "compliance",
    "risk management",
    "information technology",
    "security operations",
    "data analytics",
    "product management",
    "software engineering",
    "facilities",
    "executive operations",
)

ROLES = (
    "executive",
    "director",
    "manager",
    "analyst",
    "coordinator",
    "operator",
    "specialist",
    "engineer",
    "administrator",
    "auditor",
    "planner",
    "agent",
    "field technician",
    "sales representative",
    "support representative",
)

SYSTEMS = (
    "spreadsheet",
    "email",
    "chat",
    "CRM",
    "ERP",
    "HRIS",
    "ATS",
    "ticketing system",
    "data warehouse",
    "document management system",
    "billing system",
    "inventory system",
    "workflow engine",
    "API service",
    "database",
    "file storage",
    "BI dashboard",
    "identity provider",
)

DATA_OBJECTS = (
    "customer",
    "account",
    "contact",
    "lead",
    "opportunity",
    "order",
    "invoice",
    "payment",
    "contract",
    "policy",
    "ticket",
    "case",
    "shipment",
    "asset",
    "employee",
    "candidate",
    "job order",
    "product",
    "vendor",
    "purchase order",
    "work order",
    "event",
    "metric",
    "document",
)

GEOGRAPHIES = (
    "global",
    "United States",
    "European Union",
    "Canada",
    "Latin America",
    "APAC",
    "local municipality",
)

TECHNOLOGIES = (
    "Python",
    "JavaScript",
    "SQL",
    "REST API",
    "webhook",
    "queue",
    "event stream",
    "serverless function",
    "Kubernetes service",
    "SaaS integration",
)

OPERATION_OUTPUTS = {
    "observe": ("observation_event_schema", "source_signal_collector"),
    "identify": ("entity_identifier_schema", "identity_resolution_gate"),
    "collect": ("data_collection_adapter", "intake_form_schema"),
    "validate": ("validation_rule_pack", "schema_quality_gate"),
    "communicate": ("message_payload_adapter", "notification_template"),
    "store": ("record_schema", "artifact_storage_adapter"),
    "retrieve": ("lookup_query_adapter", "search_index_card"),
    "transform": ("normalization_adapter", "field_mapping_mutator"),
    "compute": ("business_metric_calculator", "calculation_proof_fixture"),
    "compare": ("comparison_rule", "diff_report_template"),
    "decide": ("policy_decision_gate", "decision_receipt_schema"),
    "route": ("workflow_router", "queue_routing_rule"),
    "schedule": ("scheduler_trigger", "calendar_availability_adapter"),
    "allocate": ("resource_allocation_policy", "capacity_planning_template"),
    "approve": ("approval_workflow_template", "approval_audit_event"),
    "transact": ("transaction_event_schema", "idempotency_key_policy"),
    "fulfill": ("fulfillment_workflow_template", "status_transition_schema"),
    "monitor": ("monitoring_signal_rule", "alert_threshold_gate"),
    "measure": ("metric_definition", "measurement_window_adapter"),
    "report": ("report_template", "dashboard_metric_card"),
    "audit": ("audit_ledger_event_schema", "control_evidence_checklist"),
    "reconcile": ("reconciliation_rule", "exception_queue_schema"),
    "notify": ("notification_route", "recipient_policy"),
    "escalate": ("escalation_policy", "human_review_packet"),
    "comply": ("compliance_checklist", "jurisdiction_policy_gate"),
    "secure": ("security_control_gate", "access_policy_adapter"),
    "recover": ("recovery_runbook", "rollback_plan_template"),
    "learn": ("feedback_loop_schema", "improvement_signal_extractor"),
}

COMMON_OUTPUTS = (
    "business_operation_question_set",
    "business_operation_edge_candidate",
    "input_output_contract_candidate",
    "system_integration_template",
    "proof_fixture_candidate",
)


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any, *, n: int = 16) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str, *, max_len: int = 120) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:max_len] or "business-operation"


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO))
    except ValueError:
        return str(resolved)


def _queries(row: dict[str, str]) -> list[dict[str, Any]]:
    op = row["operation"]
    area = row["function_area"]
    role = row["role"]
    system = row["system"]
    obj = row["data_object"]
    geo = row["geography"]
    tech = row["technology"]
    english = [
        f"what does {area} {role} do to {op} {obj} using {system} in {geo} input output workflow controls",
        f"{area} {op} {obj} business operation data flow source destination validation audit",
        f"{system} {tech} {obj} {op} API schema automation integration business process",
    ]
    return [
        {"lang": "en", "language": "English", "terms": english},
        {
            "lang": "es",
            "language": "Spanish",
            "terms": [
                f"{area} {role} {op} {obj} {system} flujo datos entrada salida controles",
                f"operacion negocio {area} {obj} {op} API esquema automatizacion",
            ],
        },
        {
            "lang": "pt",
            "language": "Portuguese",
            "terms": [
                f"{area} {role} {op} {obj} {system} fluxo dados entrada saida controles",
                f"operacao negocio {area} {obj} {op} API esquema automacao",
            ],
        },
        {
            "lang": "fr",
            "language": "French",
            "terms": [
                f"{area} {role} {op} {obj} {system} flux donnees entree sortie controles",
                f"operation metier {area} {obj} {op} API schema automatisation",
            ],
        },
        {
            "lang": "zh",
            "language": "Chinese",
            "terms": [
                f"{area} {role} {op} {obj} {system} 数据 流 输入 输出 控制",
                f"业务 操作 {area} {obj} {op} API schema 自动化",
            ],
        },
    ]


def _scope(row: dict[str, str]) -> dict[str, Any]:
    key = "-".join(_slug(row[name], max_len=32) for name in (
        "operation",
        "function_area",
        "role",
        "data_object",
        "system",
        "geography",
        "technology",
    ))
    outputs = sorted(set((*COMMON_OUTPUTS, *OPERATION_OUTPUTS.get(row["operation"], ()))))
    return {
        "id": f"business-operation-{key}",
        "surface_id": "surface-business-operation-first-principles",
        "title": (
            f"{row['function_area']} {row['operation']} {row['data_object']} "
            f"via {row['system']} ({row['role']}, {row['geography']})"
        ),
        "topic_family": "business_operation_first_principles",
        "providers": list(PROVIDERS),
        "queries": _queries(row),
        "candidate_outputs": outputs,
        "source_policy": "metadata_first_first_principles_questions_no_private_business_data",
        "first_principles": {
            "operation": row["operation"],
            "function_area": row["function_area"],
            "role": row["role"],
            "system": row["system"],
            "data_object": row["data_object"],
            "geography": row["geography"],
            "technology": row["technology"],
            "primitive_lens": [
                "communicate_or_transfer_data",
                "store_or_remember_state",
                "transform_or_compute",
                "decide_or_route",
                "prove_or_audit",
            ],
        },
        "serves_truth": False,
    }


AXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("operation", OPERATION_ATOMS),
    ("function_area", FUNCTION_AREAS),
    ("role", ROLES),
    ("system", SYSTEMS),
    ("data_object", DATA_OBJECTS),
    ("geography", GEOGRAPHIES),
    ("technology", TECHNOLOGIES),
)


def _full_cross_product_rows() -> int:
    total = 1
    for _, values in AXES:
        total *= len(values)
    return total


def _row_at(index: int) -> dict[str, str]:
    total = _full_cross_product_rows()
    # 7919 is coprime with the current axis product. This walks the
    # cross-product in a deterministic, high-coverage order, so small slices are
    # not clustered in the first operation/function.
    mixed = (index * 7919) % total
    row: dict[str, str] = {}
    for name, values in AXES:
        row[name] = values[mixed % len(values)]
        mixed //= len(values)
    return row


def generate_scopes(*, offset: int = 0, max_rows: int = DEFAULT_MAX_ROWS) -> list[dict[str, Any]]:
    total = _full_cross_product_rows()
    available = max(0, total - max(0, offset))
    requested = available if max_rows == 0 else min(max_rows, available)
    return [_scope(_row_at(offset + index)) for index in range(requested)]


def write_outputs(scopes: Iterable[dict[str, Any]], *, scope_file: Path, summary_file: Path) -> dict[str, Any]:
    scope_rows = list(scopes)
    scope_file.parent.mkdir(parents=True, exist_ok=True)
    scope_file.write_text("".join(_canon(row) + "\n" for row in scope_rows), encoding="utf-8")
    op_counts: dict[str, int] = {}
    area_counts: dict[str, int] = {}
    for row in scope_rows:
        fp = row.get("first_principles") or {}
        op = str(fp.get("operation") or "unknown")
        area = str(fp.get("function_area") or "unknown")
        op_counts[op] = op_counts.get(op, 0) + 1
        area_counts[area] = area_counts.get(area, 0) + 1
    summary = {
        "record_type": "business_operation_scope_generation",
        "scope_rows": len(scope_rows),
        "scope_file": _display_path(scope_file),
        "summary_file": _display_path(summary_file),
        "operation_counts": dict(sorted(op_counts.items())),
        "function_area_counts": dict(sorted(area_counts.items())),
        "full_cross_product_rows": _full_cross_product_rows(),
        "serves_truth": False,
        "digest": f"sha256:{_sha(scope_rows, n=24)}",
    }
    lines = [
        "# Business Operation First-Principles Search Scopes",
        "",
        "Candidate-only search scopes generated from universal operation axes.",
        "",
        f"- Scope rows written: {summary['scope_rows']}",
        f"- Full cross-product rows available: {summary['full_cross_product_rows']}",
        f"- Serves truth: {str(summary['serves_truth']).lower()}",
        f"- Digest: {summary['digest']}",
        "",
        "## Operation Counts",
    ]
    for operation, count in summary["operation_counts"].items():
        lines.append(f"- `{operation}`: {count}")
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    return summary


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        scopes = generate_scopes(max_rows=10)
        out = root / "scopes.jsonl"
        summary_file = root / "summary.md"
        report = write_outputs(scopes, scope_file=out, summary_file=summary_file)
        files_exist = out.exists() and summary_file.exists()
    check("generates requested scope count", len(scopes) == 10, str(len(scopes)))
    check("all scopes are candidate-only", all(row.get("serves_truth") is False for row in scopes))
    check("queries include first-principles workflow language", any("input output workflow controls" in _canon(row) for row in scopes))
    check("outputs include operation-specific edge candidates", any("source_signal_collector" in row.get("candidate_outputs", []) for row in scopes))
    check("full cross-product is hundreds of thousands", report.get("full_cross_product_rows", 0) > 100_000, str(report.get("full_cross_product_rows")))
    check("summary written", report.get("scope_rows") == 10 and files_exist)
    print("\n" + ("PASS - business operation scope generator" if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate candidate-only first-principles business operation search scopes.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", default=str(DEFAULT_SCOPE_FILE))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_FILE))
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS, help="0 means full cross-product")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    scopes = generate_scopes(offset=max(0, args.offset), max_rows=max(0, args.max_rows))
    report = write_outputs(scopes, scope_file=Path(args.out), summary_file=Path(args.summary))
    print(_canon(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
