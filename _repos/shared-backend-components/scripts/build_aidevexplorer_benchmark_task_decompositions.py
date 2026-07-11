#!/usr/bin/env python3
"""Build primitive-component decompositions for AIDevExplorer benchmark tasks."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR,
    AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT,
    REPO_ROOT,
)
from src.teleon.primitives import (  # noqa: E402
    compare_benchmark_route_token_usage,
    decompose_benchmark_task_to_primitive_components,
)

TASKS_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
DEFAULT_SUITES_DIR = _resource(AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR)

BENCHMARK_LENS_BY_TASK_FAMILY: dict[str, str] = {
    "admin_dashboard": "ui_application_benchmark",
    "agent_tool_permissioning": "agent_tooling_benchmark",
    "ci_hardening": "ci_devops_benchmark",
    "contract_obligation_tracking": "business_workflow_benchmark",
    "crud_api": "api_application_benchmark",
    "csv_import_pipeline": "data_import_benchmark",
    "customer_onboarding_portal": "ui_application_benchmark",
    "data_quality": "data_quality_benchmark",
    "dependency_exception_workflow": "security_governance_benchmark",
    "deployment_readiness": "deployment_readiness_benchmark",
    "devops_cloud": "cloud_infra_benchmark",
    "docs_rag_search": "rag_retrieval_benchmark",
    "frontend_quality": "frontend_quality_benchmark",
    "invoice_approval_workflow": "business_workflow_benchmark",
    "knowledge_base_migration": "content_migration_benchmark",
    "prompt_eval_harness": "llm_eval_benchmark",
    "security_alert_triage": "security_triage_benchmark",
    "tenant_settings": "configuration_benchmark",
    "warehouse_elt": "data_warehouse_benchmark",
    "webhook_ingestion": "event_integration_benchmark",
}

PRIMITIVE_KIND_HINTS: tuple[tuple[str, str], ...] = (
    ("api.", "api_contract"),
    ("auth.", "security_policy"),
    ("audit.", "audit_receipt"),
    ("csv", "data_import"),
    ("db.", "database_change"),
    ("deploy", "deployment_runtime"),
    ("eval", "llm_eval"),
    ("frontend", "frontend_quality"),
    ("rag", "rag_retrieval"),
    ("security", "security_triage"),
    ("webhook", "event_integration"),
)

DECOMPOSITION_POLICY: dict[str, Any] = {
    "min_components": AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS,
    "require_component_kind": True,
    "require_visible_edges": True,
    "require_proof_requirements": True,
    "max_component_token_estimate": 1500,
    "require_candidate_boundary": True,
}

TOKEN_POLICY: dict[str, Any] = {
    "min_savings_percent": AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT,
    "require_component_attribution": True,
    "require_baseline_trace_ref": True,
    "require_primitive_trace_ref": True,
    "require_same_task_id": True,
    "require_candidate_boundary": True,
}

MEASUREMENT_FIELDS: tuple[str, ...] = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "primitive_search_tokens",
    "primitive_component_tokens",
    "custom_code_tokens",
    "proof_tokens",
    "rework_tokens",
    "wall_clock_minutes",
    "test_pass_rate",
)


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _slug(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return text or "component"


def _camel(value: object) -> str:
    parts = [part for part in re.split(r"[^a-zA-Z0-9]+", str(value or "")) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Component"


def _sha(value: Any, *, n: int = 12) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def _suite_index(run_dir: Path) -> dict[str, dict[str, Any]]:
    manifest = _read_json(run_dir / "manifest.json")
    suites = _read_jsonl(run_dir / "suites.jsonl")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("benchmark suite manifest must keep candidate=true and serves_truth=false")
    index: dict[str, dict[str, Any]] = {}
    for suite in suites:
        suite_id = str(suite.get("suite_id") or "")
        suite_index = int(suite.get("suite_index") or 0)
        for task_id in suite.get("task_ids") or []:
            index[str(task_id)] = {
                "suite_id": suite_id,
                "suite_index": suite_index,
            }
    return index


def _primitive_kind(primitive_name: str, fallback_family: str) -> str:
    lowered = primitive_name.lower()
    for needle, kind in PRIMITIVE_KIND_HINTS:
        if needle in lowered:
            return kind
    return f"{_slug(fallback_family)}_primitive"


def _component_token_estimate(component_kind: str, primitive_name: str, position: int) -> int:
    base_by_kind = {
        "api_contract": 360,
        "audit_receipt": 220,
        "data_import": 320,
        "database_change": 340,
        "deployment_runtime": 420,
        "event_integration": 360,
        "frontend_quality": 340,
        "llm_eval": 360,
        "rag_retrieval": 380,
        "security_policy": 360,
        "security_triage": 380,
    }
    base = int(base_by_kind.get(component_kind, 280))
    return base + min(len(primitive_name) * 3, 180) + (position * 12)


def _components_for_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = str(task["id"])
    family = str(task["task_family"])
    expected_primitives = [str(value) for value in task.get("expected_primitives") or [] if str(value).strip()]
    expected_template = str(task.get("expected_template") or "template.primitive_route_assembly")
    components: list[dict[str, Any]] = [
        {
            "component_id": f"comp:{task_id}:task_contract",
            "kind": "benchmark_task_contract",
            "input_edge": "BenchmarkTaskIntent+TeamContext",
            "output_edge": "TaskAcceptanceContract",
            "proof_requirements": ("acceptance_criteria_presence_test", "candidate_boundary_test"),
            "estimated_tokens": 180,
            "candidate": True,
            "serves_truth": False,
        },
        {
            "component_id": f"comp:{task_id}:primitive_route_search",
            "kind": "primitive_route_search",
            "input_edge": "TaskAcceptanceContract+PrimitiveRegistry",
            "output_edge": "PrimitiveRouteCandidateSet",
            "proof_requirements": ("registry_search_smoke_test", "visible_edge_match_test"),
            "estimated_tokens": 260,
            "candidate": True,
            "serves_truth": False,
        },
    ]
    for index, primitive_name in enumerate(expected_primitives, start=1):
        primitive_slug = _slug(primitive_name)
        primitive_type = _camel(primitive_name)
        kind = _primitive_kind(primitive_name, family)
        components.append(
            {
                "component_id": f"comp:{task_id}:{primitive_slug}",
                "kind": kind,
                "input_edge": f"TaskAcceptanceContract+{primitive_type}Input",
                "output_edge": f"{primitive_type}Receipt",
                "proof_requirements": ("component_contract_test", "negative_fixture_test"),
                "estimated_tokens": _component_token_estimate(kind, primitive_name, index),
                "candidate": True,
                "serves_truth": False,
            }
        )
    components.extend(
        [
            {
                "component_id": f"comp:{task_id}:route_assembly",
                "kind": "primitive_route_assembly",
                "input_edge": f"PrimitiveRouteCandidateSet+{_camel(expected_template)}",
                "output_edge": "AssembledPrimitiveRoute",
                "proof_requirements": ("hidden_member_edge_consistency_test", "adapter_mutator_test"),
                "estimated_tokens": 320,
                "candidate": True,
                "serves_truth": False,
            },
            {
                "component_id": f"comp:{task_id}:proof_gate",
                "kind": "proof_gate",
                "input_edge": "AssembledPrimitiveRoute+AcceptanceCriteria",
                "output_edge": "BenchmarkProofReceipt",
                "proof_requirements": ("unit_or_contract_test", "pitfall_regression_test"),
                "estimated_tokens": 340,
                "candidate": True,
                "serves_truth": False,
            },
            {
                "component_id": f"comp:{task_id}:token_meter",
                "kind": "token_usage_measurement",
                "input_edge": "BaselineTrace+PrimitiveRouteTrace+ComponentAttribution",
                "output_edge": "TokenComparisonReceipt",
                "proof_requirements": ("same_task_trace_pair_test", "component_attribution_test"),
                "estimated_tokens": 200,
                "candidate": True,
                "serves_truth": False,
            },
        ]
    )
    return components


def _baseline_token_estimate(task: dict[str, Any], component_count: int) -> int:
    deliverables = len(task.get("expected_deliverables") or [])
    pitfalls = len(task.get("common_pitfalls") or [])
    acceptance = len(task.get("acceptance_criteria") or [])
    return 1400 + (component_count * 420) + (deliverables * 240) + (pitfalls * 160) + (acceptance * 120)


def _decomposition_row(task: dict[str, Any], suite_lookup: dict[str, dict[str, Any]], *, run_date: str) -> dict[str, Any]:
    task_id = str(task["id"])
    components = _components_for_task(task)
    decomposition = decompose_benchmark_task_to_primitive_components(
        {"task_id": task_id, "components": components},
        DECOMPOSITION_POLICY,
    )
    primitive_tokens = sum(int(component["estimated_tokens"]) for component in components) + 300
    baseline_tokens = _baseline_token_estimate(task, len(components))
    comparison = compare_benchmark_route_token_usage(
        {
            "baseline_task_id": task_id,
            "primitive_task_id": task_id,
            "baseline_tokens": baseline_tokens,
            "primitive_route_tokens": primitive_tokens,
            "components": [
                {
                    "component_id": component["component_id"],
                    "tokens": component["estimated_tokens"],
                }
                for component in components
            ],
            "baseline_trace_ref": f"runs/{run_date}/baseline/{task_id}.trace.jsonl",
            "primitive_trace_ref": f"runs/{run_date}/primitive/{task_id}.trace.jsonl",
            "candidate": True,
            "serves_truth": False,
        },
        TOKEN_POLICY,
    )
    if not decomposition.ready:
        raise AssertionError(f"{task_id}: decomposition not ready: {decomposition.blockers}")
    if not comparison.ready:
        raise AssertionError(f"{task_id}: token comparison plan not ready: {comparison.blockers}")
    suite = suite_lookup.get(task_id) or {}
    family = str(task["task_family"])
    lens = BENCHMARK_LENS_BY_TASK_FAMILY.get(family, "software_build_benchmark")
    return {
        "record_type": "aidevexplorer_benchmark_task_primitive_decomposition",
        "run_date": run_date,
        "task_id": task_id,
        "suite_id": suite.get("suite_id"),
        "suite_index": suite.get("suite_index"),
        "benchmark_lens": lens,
        "benchmark_task_type": family,
        "title": task.get("title"),
        "task_family": family,
        "industry": task.get("industry"),
        "audience": task.get("audience"),
        "logical_components": components,
        "component_ids": list(decomposition.component_ids),
        "core_group_edges": list(decomposition.core_group_edges),
        "expected_primitives": list(task.get("expected_primitives") or []),
        "expected_primitive_groups": list(task.get("expected_primitive_groups") or []),
        "decomposition_ready": decomposition.ready,
        "decomposition_hash": decomposition.decomposition_hash,
        "decomposition_blockers": list(decomposition.blockers),
        "token_usage_plan": {
            "estimate_only": True,
            "actual_run_required": True,
            "baseline_token_estimate": comparison.baseline_tokens,
            "primitive_route_token_estimate": comparison.primitive_route_tokens,
            "estimated_savings_percent": comparison.savings_percent,
            "component_token_attribution": [
                {
                    "component_id": component["component_id"],
                    "estimated_tokens": component["estimated_tokens"],
                }
                for component in components
            ],
            "baseline_trace_ref_pattern": f"runs/{run_date}/baseline/{task_id}.trace.jsonl",
            "primitive_trace_ref_pattern": f"runs/{run_date}/primitive/{task_id}.trace.jsonl",
            "comparison_hash": comparison.comparison_hash,
            "comparison_blockers": list(comparison.blockers),
        },
        "measurement_fields": list(MEASUREMENT_FIELDS),
        "promotion_note": "estimated token plans are candidate guidance; promotion requires actual paired trace receipts",
        "candidate": True,
        "serves_truth": False,
    }


def build_decompositions(*, run_date: str, suites_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tasks = _read_jsonl(TASKS_PATH)
    if len(tasks) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("task corpus must be generated and validated before decomposition build")
    task_ids = [str(task["id"]) for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise AssertionError("task corpus must contain unique task ids")
    suite_lookup = _suite_index(suites_dir / run_date)
    if set(suite_lookup) != set(task_ids):
        raise AssertionError("benchmark suites must cover every task before decomposition build")
    rows = [_decomposition_row(task, suite_lookup, run_date=run_date) for task in tasks]
    lens_counts = collections.Counter(str(row["benchmark_lens"]) for row in rows)
    family_counts = collections.Counter(str(row["task_family"]) for row in rows)
    component_counts = [len(row["component_ids"]) for row in rows]
    savings_values = [float((row["token_usage_plan"] or {}).get("estimated_savings_percent") or 0) for row in rows]
    manifest = {
        "record_type": "aidevexplorer_benchmark_task_decomposition_manifest",
        "run_date": run_date,
        "row_count": len(rows),
        "task_corpus_path": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
        "suites_dir": AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR,
        "decompositions_filename": AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME,
        "benchmark_lens_counts": dict(sorted(lens_counts.items())),
        "task_family_counts": dict(sorted(family_counts.items())),
        "component_count_min": min(component_counts),
        "component_count_max": max(component_counts),
        "component_count_avg": round(sum(component_counts) / len(component_counts), 2),
        "estimated_savings_percent_min": min(savings_values),
        "estimated_savings_percent_avg": round(sum(savings_values) / len(savings_values), 2),
        "token_savings_target_percent": AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT,
        "estimate_only": True,
        "actual_run_required": True,
        "candidate": True,
        "serves_truth": False,
        "manifest_hash": "benchmark-task-decompositions:" + _sha(rows),
    }
    return rows, manifest


def write_decompositions(run_date: str, rows: list[dict[str, Any]], manifest: dict[str, Any], suites_dir: Path) -> dict[str, str]:
    run_dir = suites_dir / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    rows_path = run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME
    manifest_path = run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME
    rows_path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "decompositions_path": str(rows_path.relative_to(REPO_ROOT)),
        "decompositions_manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--suites-dir", default=str(DEFAULT_SUITES_DIR))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        suites_dir = Path(args.suites_dir)
        rows, manifest = build_decompositions(run_date=args.date, suites_dir=suites_dir)
        paths = {} if args.check_only else write_decompositions(args.date, rows, manifest, suites_dir)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({**manifest, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
