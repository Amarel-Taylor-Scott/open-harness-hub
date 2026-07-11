#!/usr/bin/env python3
"""Build compact AIDevObserver cards from benchmark task decompositions."""
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
from typing import Any, Iterable

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_MANIFEST_PATH,
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH,
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_EVIDENCE_STATUS,
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR,
    REPO_ROOT,
)

DEFAULT_SUITES_DIR = _resource(AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR)
OUT_PATH = _resource(AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_MANIFEST_PATH)


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
    return text or "unknown"


def _label(value: object) -> str:
    return " ".join(part for part in _slug(value).split("_") if part).title()


def _sha(value: Any, *, n: int = 12) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def _top_counts(values: Iterable[str], *, limit: int = 8) -> list[str]:
    return [item for item, _count in collections.Counter(values).most_common(limit)]


def _mean(values: Iterable[float]) -> float:
    numbers = [float(value) for value in values]
    return round(sum(numbers) / len(numbers), 2) if numbers else 0.0


def _card_common(
    *,
    primitive_id: str,
    kind: str,
    title: str,
    description: str,
    row_group: list[dict[str, Any]],
    group_value: str,
    run_date: str,
    source_path: str,
) -> dict[str, Any]:
    task_ids = [str(row.get("task_id") or "") for row in row_group if str(row.get("task_id") or "")]
    task_families = sorted({str(row.get("task_family") or "") for row in row_group if row.get("task_family")})
    benchmark_lenses = sorted({str(row.get("benchmark_lens") or "") for row in row_group if row.get("benchmark_lens")})
    component_kinds = _top_counts(
        str(component.get("kind") or "")
        for row in row_group
        for component in (row.get("logical_components") or [])
        if isinstance(component, dict) and component.get("kind")
    )
    expected_primitives = _top_counts(
        str(value)
        for row in row_group
        for value in (row.get("expected_primitives") or [])
        if str(value).strip()
    )
    expected_groups = _top_counts(
        str(value)
        for row in row_group
        for value in (row.get("expected_primitive_groups") or [])
        if str(value).strip()
    )
    component_counts = [len(row.get("component_ids") or []) for row in row_group]
    savings = [
        float((row.get("token_usage_plan") or {}).get("estimated_savings_percent") or 0)
        for row in row_group
    ]
    search_terms = sorted({
        "actual_run_required",
        "benchmark",
        "component",
        "component_attribution",
        "decomposition",
        "estimate_only",
        "logical_components",
        "primitive",
        "proof",
        "route",
        "token",
        "token_comparison",
        *benchmark_lenses,
        *task_families,
        *component_kinds,
        *expected_primitives,
        *expected_groups,
    })
    return {
        "record_type": "aidevexplorer_benchmark_decomposition_card",
        "primitive_id": primitive_id,
        "kind": kind,
        "title": title,
        "label": title,
        "slug": _slug(primitive_id),
        "blackbox": {
            "does": (
                f"{description} Top component kinds: {', '.join(component_kinds[:5])}. "
                "Use this card to select benchmark tasks, decompose them into primitive logical components, "
                "and compare baseline versus primitive-route token usage with component attribution."
            ),
        },
        "input_edge": "BenchmarkTaskIntent+TeamContext+PrimitiveRegistry",
        "output_edge": "BenchmarkPrimitiveComponentRoute+TokenComparisonPlan",
        "contract": {
            "input": "BenchmarkTaskIntent+TeamContext+PrimitiveRegistry",
            "output": "BenchmarkPrimitiveComponentRoute+TokenComparisonPlan",
        },
        "core_group_edge": "BenchmarkTaskIntent+PrimitiveRegistry -> BenchmarkPrimitiveComponentRoute+TokenComparisonPlan",
        "hidden_member_edges": [
            "BenchmarkTaskIntent+TeamContext -> TaskAcceptanceContract",
            "TaskAcceptanceContract+PrimitiveRegistry -> PrimitiveRouteCandidateSet",
            "TaskAcceptanceContract+PrimitiveInput -> PrimitiveReceipt",
            "PrimitiveRouteCandidateSet+Template -> AssembledPrimitiveRoute",
            "AssembledPrimitiveRoute+AcceptanceCriteria -> BenchmarkProofReceipt",
            "BaselineTrace+PrimitiveRouteTrace+ComponentAttribution -> TokenComparisonReceipt",
        ],
        "effects": ["benchmark_plan_write", "token_estimate"],
        "runtime_targets": ["local.python", "registry.search"],
        "adapter_mutators": [
            "benchmark_suite_sampler",
            "primitive_component_decomposer",
            "token_usage_meter",
            "proof_gate_attacher",
        ],
        "proof_requirements": [
            "task_coverage_validation",
            "component_visible_edge_validation",
            "candidate_boundary_validation",
            "paired_trace_required_for_real_savings",
        ],
        "common_pitfalls": [
            "treating estimated savings as proof",
            "comparing different task variants",
            "missing component-level attribution",
            "omitting proof requirements from decomposed components",
        ],
        "benchmark_lenses": benchmark_lenses,
        "task_families": task_families,
        "domains": search_terms,
        "blocking_keys": search_terms,
        "task_count": len(row_group),
        "sample_task_ids": task_ids[:10],
        "component_kinds": component_kinds,
        "expected_primitives": expected_primitives,
        "expected_primitive_groups": expected_groups,
        "component_count_avg": _mean(component_counts),
        "estimated_savings_percent_avg": _mean(savings),
        "token_plan_status": "estimate_only_actual_run_required",
        "source_family": AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY,
        "source_evidence_status": AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_EVIDENCE_STATUS,
        "source_ref": {
            "path": source_path,
            "run_date": run_date,
            "group_value": group_value,
        },
        "quality_score": 120,
        "surface_visibility": "public_demo_safe_candidate",
        "candidate": True,
        "serves_truth": False,
        "card_hash": "benchmark-decomposition-card:" + _sha(
            {
                "primitive_id": primitive_id,
                "task_ids": task_ids,
                "component_kinds": component_kinds,
            }
        ),
    }


def _cards_for_group(
    rows: list[dict[str, Any]],
    *,
    field: str,
    kind: str,
    id_prefix: str,
    title_prefix: str,
    description_prefix: str,
    run_date: str,
    source_path: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        value = str(row.get(field) or "").strip()
        if value:
            grouped[value].append(row)
    cards: list[dict[str, Any]] = []
    for value in sorted(grouped):
        cards.append(
            _card_common(
                primitive_id=f"{id_prefix}{_slug(value)}@candidate",
                kind=kind,
                title=f"{title_prefix}: {_label(value)}",
                description=f"{description_prefix} {value} benchmark tasks into reusable primitive components and estimate-only token comparison plans.",
                row_group=grouped[value],
                group_value=value,
                run_date=run_date,
                source_path=source_path,
            )
        )
    return cards


def _cards_for_multivalue_group(
    rows: list[dict[str, Any]],
    *,
    field: str,
    kind: str,
    id_prefix: str,
    title_prefix: str,
    description_prefix: str,
    run_date: str,
    source_path: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        values = row.get(field) or []
        if not isinstance(values, list):
            continue
        for value in values:
            value_text = str(value or "").strip()
            if value_text:
                grouped[value_text].append(row)
    cards: list[dict[str, Any]] = []
    for value in sorted(grouped):
        cards.append(
            _card_common(
                primitive_id=f"{id_prefix}{_slug(value)}@candidate",
                kind=kind,
                title=f"{title_prefix}: {_label(value)}",
                description=(
                    f"{description_prefix} {value} across benchmark tasks and exposes a compact "
                    "primitive-component token comparison plan."
                ),
                row_group=grouped[value],
                group_value=value,
                run_date=run_date,
                source_path=source_path,
            )
        )
    return cards


def build_cards(*, run_date: str, suites_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run_dir = suites_dir / run_date
    source_path = run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME
    manifest_path = run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME
    source_manifest = _read_json(manifest_path)
    rows = _read_jsonl(source_path)
    if len(rows) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("benchmark decomposition rows must cover the full task corpus before card build")
    if source_manifest.get("candidate") is not True or source_manifest.get("serves_truth") is not False:
        raise AssertionError("benchmark decomposition manifest must keep candidate boundary")
    if source_manifest.get("estimate_only") is not True or source_manifest.get("actual_run_required") is not True:
        raise AssertionError("benchmark decomposition manifest must keep token plans estimate-only")
    cards = [
        *_cards_for_group(
            rows,
            field="benchmark_lens",
            kind="benchmark.decomposition.lens",
            id_prefix="bench:aidevexplorer.decomposition.lens.",
            title_prefix="Benchmark Decomposition Lens",
            description_prefix="Aggregates",
            run_date=run_date,
            source_path=str(source_path.relative_to(REPO_ROOT)),
        ),
        *_cards_for_group(
            rows,
            field="task_family",
            kind="benchmark.decomposition.task_family",
            id_prefix="bench:aidevexplorer.decomposition.task_family.",
            title_prefix="Benchmark Decomposition Task Family",
            description_prefix="Aggregates",
            run_date=run_date,
            source_path=str(source_path.relative_to(REPO_ROOT)),
        ),
        *_cards_for_multivalue_group(
            rows,
            field="expected_primitives",
            kind="benchmark.decomposition.expected_primitive",
            id_prefix="bench:aidevexplorer.decomposition.expected_primitive.",
            title_prefix="Benchmark Decomposition Expected Primitive",
            description_prefix="Aggregates tasks that require expected primitive",
            run_date=run_date,
            source_path=str(source_path.relative_to(REPO_ROOT)),
        ),
        *_cards_for_multivalue_group(
            rows,
            field="expected_primitive_groups",
            kind="benchmark.decomposition.expected_group",
            id_prefix="bench:aidevexplorer.decomposition.expected_group.",
            title_prefix="Benchmark Decomposition Expected Group",
            description_prefix="Aggregates tasks that require expected primitive group",
            run_date=run_date,
            source_path=str(source_path.relative_to(REPO_ROOT)),
        ),
    ]
    primitive_ids = [str(card["primitive_id"]) for card in cards]
    if len(primitive_ids) != len(set(primitive_ids)):
        raise AssertionError("benchmark decomposition cards must have unique primitive ids")
    manifest = {
        "record_type": "aidevexplorer_benchmark_decomposition_cards_manifest",
        "run_date": run_date,
        "row_count": len(cards),
        "source_rows": len(rows),
        "source_manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
        "source_decompositions_path": str(source_path.relative_to(REPO_ROOT)),
        "cards_path": AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH,
        "source_family": AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY,
        "source_evidence_status": AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_EVIDENCE_STATUS,
        "kinds": dict(collections.Counter(str(card["kind"]) for card in cards)),
        "candidate": True,
        "serves_truth": False,
        "manifest_hash": "benchmark-decomposition-cards:" + _sha(cards),
    }
    return cards, manifest


def write_cards(cards: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, str]:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        "".join(json.dumps(card, sort_keys=True, separators=(",", ":")) + "\n" for card in cards),
        encoding="utf-8",
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "cards_path": str(OUT_PATH.relative_to(REPO_ROOT)),
        "manifest_path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--suites-dir", default=str(DEFAULT_SUITES_DIR))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        cards, manifest = build_cards(run_date=args.date, suites_dir=Path(args.suites_dir))
        paths = {} if args.check_only else write_cards(cards, manifest)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({**manifest, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
