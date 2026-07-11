#!/usr/bin/env python3
"""Validate AIDevExplorer runtime-shape primitive cards for AIDevObserver."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_MANIFEST_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPES,
    REPO_ROOT,
)

CARDS_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_MANIFEST_PATH)

REQUIRED_FIELDS: tuple[str, ...] = (
    "primitive_id",
    "kind",
    "title",
    "input_edge",
    "output_edge",
    "contract",
    "group_contract",
    "blackbox",
    "effects",
    "runtime_shape",
    "runtime_targets",
    "adapter_mutators",
    "mutations",
    "proof_requirements",
    "promotion_blockers",
    "blocking_keys",
    "source_ref",
    "source_family",
    "source_evidence_status",
    "quality_score",
    "candidate",
    "serves_truth",
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


def _list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def self_test() -> dict[str, Any]:
    cards = _read_jsonl(CARDS_PATH)
    manifest = _read_json(MANIFEST_PATH)
    if int(manifest.get("row_count") or 0) != len(cards):
        raise AssertionError("manifest row_count must match card rows")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must remain candidate=true and serves_truth=false")

    allowed_shapes = set(AIDEVEXPLORER_RUNTIME_SHAPES)
    ids: list[str] = []
    shapes: dict[str, int] = {}
    kinds: set[str] = set()
    families: set[str] = set()

    for card in cards:
        card_id = str(card.get("primitive_id") or "")
        if not card_id:
            raise AssertionError("every card must declare primitive_id")
        ids.append(card_id)
        missing = sorted(field for field in REQUIRED_FIELDS if field not in card)
        if missing:
            raise AssertionError(f"{card_id} missing fields: {missing}")
        if card.get("candidate") is not True or card.get("serves_truth") is not False:
            raise AssertionError(f"{card_id} must remain candidate=true and serves_truth=false")
        runtime_shape = str(card.get("runtime_shape") or "")
        if runtime_shape not in allowed_shapes:
            raise AssertionError(f"{card_id} has unknown runtime_shape {runtime_shape!r}")
        contract = card.get("contract")
        if not isinstance(contract, dict) or not contract.get("input") or not contract.get("output"):
            raise AssertionError(f"{card_id} must declare contract input/output")
        group_contract = card.get("group_contract")
        if not isinstance(group_contract, dict):
            raise AssertionError(f"{card_id} must declare group_contract")
        if " -> " not in str(group_contract.get("core_group_edge") or ""):
            raise AssertionError(f"{card_id} must declare core_group_edge")
        _list(group_contract, "wrapper_edges", card_id, min_len=2)
        _list(group_contract, "hidden_member_edges", card_id, min_len=3)
        _list(card, "runtime_targets", card_id, min_len=1)
        _list(card, "adapter_mutators", card_id, min_len=1)
        _list(card, "mutations", card_id, min_len=1)
        _list(card, "proof_requirements", card_id, min_len=4)
        _list(card, "promotion_blockers", card_id, min_len=2)
        _list(card, "blocking_keys", card_id, min_len=8)
        if int(card.get("quality_score") or 0) < 70:
            raise AssertionError(f"{card_id} quality_score should be surfaceable enough for search")
        source_ref = card.get("source_ref")
        if not isinstance(source_ref, dict) or int(source_ref.get("row_count") or 0) <= 0:
            raise AssertionError(f"{card_id} must carry source_ref row_count")
        shapes[runtime_shape] = shapes.get(runtime_shape, 0) + 1
        kinds.add(str(card.get("kind") or ""))
        families.add(str(card.get("source_ref", {}).get("name") or "").split(".", 1)[0])

    if len(ids) != len(set(ids)):
        raise AssertionError("primitive card ids must be unique")
    if set(shapes) != allowed_shapes:
        raise AssertionError(f"runtime shape coverage mismatch: {sorted(shapes)}")
    if len(families) != 20:
        raise AssertionError(f"expected 20 task families; got {len(families)}")
    expected_per_shape = len(families)
    short_shapes = {shape: count for shape, count in shapes.items() if count != expected_per_shape}
    if short_shapes:
        raise AssertionError(f"runtime shape card-count mismatch: {short_shapes}")

    return {
        "cards": len(cards),
        "runtime_shapes": dict(sorted(shapes.items())),
        "primitive_kinds": sorted(kinds),
        "task_families": len(families),
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
