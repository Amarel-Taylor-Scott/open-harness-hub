#!/usr/bin/env python3
"""Validate AIDevExplorer benchmark decomposition search cards."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_MANIFEST_PATH,
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH,
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    REPO_ROOT,
)
from src.teleon.observer.registry_search import (  # noqa: E402
    load_benchmark_decomposition_primitive_count,
    search_edge_foundry_primitives,
)

CARDS_PATH = _resource(AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_MANIFEST_PATH)
EXPECTED_CARD_KIND_FIELDS = {
    "benchmark.decomposition.lens": ("benchmark_lens", "scalar"),
    "benchmark.decomposition.task_family": ("task_family", "scalar"),
    "benchmark.decomposition.expected_primitive": ("expected_primitives", "list"),
    "benchmark.decomposition.expected_group": ("expected_primitive_groups", "list"),
}
SEARCH_SMOKES = (
    (
        "csv import primitive token comparison file.read_csv_artifact record.identity_dedupe",
        "bench:aidevexplorer.decomposition.expected_primitive.file_read_csv_artifact@candidate",
    ),
    (
        "rag citations benchmark primitive token proof retrieve.search_index",
        "bench:aidevexplorer.decomposition.expected_group.grp_rag_docs_search_candidate@candidate",
    ),
    (
        "openapi api endpoint json schema benchmark primitive api.validate_json_schema",
        "bench:aidevexplorer.decomposition.expected_primitive.api_validate_json_schema@candidate",
    ),
    (
        "queue worker webhook idempotency token comparison queue.enqueue_job",
        "bench:aidevexplorer.decomposition.expected_primitive.queue_enqueue_job@candidate",
    ),
)


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


def _expected_kind_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for kind, (field, shape) in EXPECTED_CARD_KIND_FIELDS.items():
        values: set[str] = set()
        for row in rows:
            if shape == "scalar":
                value = str(row.get(field) or "").strip()
                if value:
                    values.add(value)
            elif shape == "list":
                for value in row.get(field) or []:
                    value_text = str(value or "").strip()
                    if value_text:
                        values.add(value_text)
            else:
                raise AssertionError(f"unsupported expected card field shape: {shape}")
        counts[kind] = len(values)
    return counts


def _run_search_smokes() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for query, expected_id in SEARCH_SMOKES:
        hits = search_edge_foundry_primitives(query, limit=5, visibility_scope="public")
        hit_ids = [str(hit.get("primitive_id") or "") for hit in hits]
        if expected_id not in hit_ids:
            raise AssertionError(f"search smoke failed for {query!r}: expected {expected_id}, got {hit_ids}")
        hit = next(row for row in hits if row.get("primitive_id") == expected_id)
        if hit.get("candidate") is not True or hit.get("serves_truth") is not False:
            raise AssertionError(f"{expected_id}: search hit must keep candidate=true and serves_truth=false")
        results.append(
            {
                "query": query,
                "expected_id": expected_id,
                "rank": hit_ids.index(expected_id) + 1,
                "score": hit.get("score"),
            }
        )
    return results


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    cards = _read_jsonl(CARDS_PATH)
    source_path = _resource(str(manifest.get("source_decompositions_path") or ""))
    source_rows = _read_jsonl(source_path)
    expected_kind_counts = _expected_kind_counts(source_rows)
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must keep candidate=true and serves_truth=false")
    if manifest.get("source_family") != AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY:
        raise AssertionError("manifest source_family mismatch")
    if int(manifest.get("source_rows") or 0) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("manifest must point to the full decomposition corpus")
    if len(source_rows) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("source decomposition rows must cover the full task corpus")
    if int(manifest.get("row_count") or 0) != len(cards):
        raise AssertionError("manifest row_count mismatch")
    if manifest.get("kinds") != expected_kind_counts:
        raise AssertionError(f"manifest kind counts mismatch: {manifest.get('kinds')} != {expected_kind_counts}")
    kinds: dict[str, int] = {}
    primitive_ids: set[str] = set()
    for card in cards:
        primitive_id = str(card.get("primitive_id") or "")
        if not primitive_id:
            raise AssertionError("card missing primitive_id")
        if primitive_id in primitive_ids:
            raise AssertionError(f"duplicate primitive_id: {primitive_id}")
        primitive_ids.add(primitive_id)
        if card.get("candidate") is not True or card.get("serves_truth") is not False:
            raise AssertionError(f"{primitive_id}: card must keep candidate=true and serves_truth=false")
        if card.get("source_family") != AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY:
            raise AssertionError(f"{primitive_id}: source_family mismatch")
        kind = str(card.get("kind") or "")
        if kind not in EXPECTED_CARD_KIND_FIELDS:
            raise AssertionError(f"{primitive_id}: unexpected kind {kind}")
        kinds[kind] = kinds.get(kind, 0) + 1
        contract = card.get("contract")
        if not isinstance(contract, dict) or not contract.get("input") or not contract.get("output"):
            raise AssertionError(f"{primitive_id}: missing contract input/output")
        if not card.get("input_edge") or not card.get("output_edge"):
            raise AssertionError(f"{primitive_id}: missing visible edge")
        if not card.get("hidden_member_edges"):
            raise AssertionError(f"{primitive_id}: missing hidden member edges")
        if not card.get("proof_requirements"):
            raise AssertionError(f"{primitive_id}: missing proof requirements")
        if card.get("token_plan_status") != "estimate_only_actual_run_required":
            raise AssertionError(f"{primitive_id}: token plans must not be presented as measured proof")
        if int(card.get("task_count") or 0) <= 0:
            raise AssertionError(f"{primitive_id}: task_count must be positive")
        if float(card.get("estimated_savings_percent_avg") or 0) <= 0:
            raise AssertionError(f"{primitive_id}: missing estimated savings summary")
    if kinds != expected_kind_counts:
        raise AssertionError(f"unexpected kind counts: {kinds}")
    loaded_count = load_benchmark_decomposition_primitive_count()
    if loaded_count != len(cards):
        raise AssertionError(f"registry loader count mismatch: expected {len(cards)}, got {loaded_count}")
    search_smokes = _run_search_smokes()
    return {
        "cards": len(cards),
        "kinds": kinds,
        "source_rows": manifest.get("source_rows"),
        "registry_loader_count": loaded_count,
        "search_smokes": search_smokes,
        "candidate": True,
        "serves_truth": False,
    }


def main() -> int:
    try:
        result = self_test()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
