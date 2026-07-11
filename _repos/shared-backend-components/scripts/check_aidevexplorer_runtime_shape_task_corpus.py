#!/usr/bin/env python3
"""Validate the AIDevExplorer runtime-shape reuse task corpus."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_REQUIRED_RUNTIME_SHAPE_TASK_FIELDS,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_MANIFEST_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_RUNTIME_SHAPES,
    AIDEVEXPLORER_TASK_AUDIENCES,
    REPO_ROOT,
)

TASKS_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_MANIFEST_PATH)


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


def _list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def self_test() -> dict[str, Any]:
    rows = _read_jsonl(TASKS_PATH)
    manifest = _read_json(MANIFEST_PATH)
    if len(rows) != AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError(
            f"runtime-shape corpus has {len(rows)} rows; expected "
            f"{AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS}"
        )
    if int(manifest.get("row_count") or 0) != len(rows):
        raise AssertionError("manifest row_count must match task rows")
    if manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must keep serves_truth=false")

    required_fields = set(AIDEVEXPLORER_REQUIRED_RUNTIME_SHAPE_TASK_FIELDS)
    allowed_audiences = set(AIDEVEXPLORER_TASK_AUDIENCES)
    allowed_shapes = set(AIDEVEXPLORER_RUNTIME_SHAPES)
    expected_rows_per_shape = AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS // len(AIDEVEXPLORER_RUNTIME_SHAPES)
    ids: list[str] = []
    audiences: set[str] = set()
    families: set[str] = set()
    shapes: dict[str, int] = {}
    primitive_kinds: set[str] = set()
    core_edges: set[str] = set()
    base_task_keys: set[str] = set()

    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id:
            raise AssertionError("every row must declare id")
        ids.append(row_id)
        missing = sorted(field for field in required_fields if field not in row)
        if missing:
            raise AssertionError(f"{row_id} missing fields: {missing}")
        if row.get("source_kind") != "curated_public_codegen_use_case":
            raise AssertionError(f"{row_id} must be compatible with public use-case ingestion")
        if row.get("corpus_kind") != "aidevexplorer_runtime_shape_reuse_task":
            raise AssertionError(f"{row_id} must declare runtime-shape corpus_kind")
        if row.get("serves_truth") is not False:
            raise AssertionError(f"{row_id} must keep serves_truth=false")
        if row.get("trust") != "candidate":
            raise AssertionError(f"{row_id} must keep trust=candidate")
        audience = str(row.get("audience") or "")
        if audience not in allowed_audiences:
            raise AssertionError(f"{row_id} has unknown audience {audience!r}")
        runtime_shape = str(row.get("runtime_shape") or "")
        if runtime_shape not in allowed_shapes:
            raise AssertionError(f"{row_id} has unknown runtime_shape {runtime_shape!r}")
        if not str(row.get("primitive_kind") or ""):
            raise AssertionError(f"{row_id} must declare primitive_kind")
        if " -> " not in str(row.get("core_group_edge") or ""):
            raise AssertionError(f"{row_id} must declare core_group_edge as visible input -> output")
        if not str(row.get("input_edge") or "") or not str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must declare visible wrapper input/output edges")
        _list(row, "wrapper_edges", row_id, min_len=2)
        _list(row, "hidden_member_edges", row_id, min_len=3)
        _list(row, "likely_primitives", row_id, min_len=4)
        _list(row, "expected_primitive_groups", row_id, min_len=1)
        _list(row, "adapter_mutators", row_id, min_len=1)
        _list(row, "effects", row_id, min_len=1)
        _list(row, "proof_requirements", row_id, min_len=4)
        _list(row, "common_pitfalls", row_id, min_len=5)
        hooks = row.get("aidevexplorer_eval_hooks")
        if not isinstance(hooks, dict):
            raise AssertionError(f"{row_id} must declare aidevexplorer_eval_hooks")
        measurements = set(hooks.get("measurements") or [])
        for measurement in ("core_group_reused", "wrapper_edges_preserved", "runtime_shape_selected"):
            if measurement not in measurements:
                raise AssertionError(f"{row_id} eval hooks missing {measurement}")
        thresholds = hooks.get("success_thresholds")
        if not isinstance(thresholds, dict) or thresholds.get("must_reuse_core_group_edge") is not True:
            raise AssertionError(f"{row_id} must require core group reuse")
        audiences.add(audience)
        families.add(str(row.get("task_family") or ""))
        primitive_kinds.add(str(row.get("primitive_kind") or ""))
        core_edges.add(str(row.get("core_group_edge") or ""))
        base_task_keys.add(
            "|".join(
                str(row.get(field) or "")
                for field in ("task_family", "industry", "business_area", "business_task")
            )
        )
        shapes[runtime_shape] = shapes.get(runtime_shape, 0) + 1

    if len(ids) != len(set(ids)):
        raise AssertionError("runtime-shape task ids must be unique")
    if audiences != allowed_audiences:
        raise AssertionError(f"audience coverage mismatch: {sorted(audiences)}")
    if set(shapes) != allowed_shapes:
        raise AssertionError(f"runtime shape coverage mismatch: {sorted(shapes)}")
    short_shapes = {shape: count for shape, count in shapes.items() if count != expected_rows_per_shape}
    if short_shapes:
        raise AssertionError(f"runtime shape row-count mismatch: {short_shapes}")
    if len(families) != 20:
        raise AssertionError(f"expected 20 task families; got {len(families)}")
    if len(core_edges) < 20:
        raise AssertionError("expected at least one core edge per task family")
    if len(base_task_keys) * len(AIDEVEXPLORER_RUNTIME_SHAPES) != len(rows):
        raise AssertionError("every base business task should be crossed with every runtime shape")

    return {
        "rows": len(rows),
        "base_business_tasks": len(base_task_keys),
        "core_group_edges": len(core_edges),
        "runtime_shapes": dict(sorted(shapes.items())),
        "primitive_kinds": sorted(primitive_kinds),
        "audiences": sorted(audiences),
        "task_families": len(families),
        "source_kind": "curated_public_codegen_use_case",
        "corpus_kind": "aidevexplorer_runtime_shape_reuse_task",
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
