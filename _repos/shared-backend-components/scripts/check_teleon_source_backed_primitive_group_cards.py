#!/usr/bin/env python3
"""Validate Teleon source-backed primitive group cards."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH,
    REPO_ROOT,
)
from src.teleon.primitives import groups as primitive_groups  # noqa: E402

CARDS_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH)
TEST_PATH = _resource(AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH)

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
    "runtime_targets",
    "adapter_mutators",
    "mutations",
    "proof_requirements",
    "proof_refs",
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
    test_text = TEST_PATH.read_text(encoding="utf-8")
    if int(manifest.get("row_count") or 0) != len(cards):
        raise AssertionError("manifest row_count must match card rows")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must remain candidate=true and serves_truth=false")
    if len(cards) < 7:
        raise AssertionError("expected at least seven source-backed group cards")

    ids: list[str] = []
    function_names: set[str] = set()
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
        if card.get("source_family") != AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY:
            raise AssertionError(f"{card_id} has unexpected source_family")
        if card.get("source_evidence_status") != "source_backed":
            raise AssertionError(f"{card_id} must be source_backed")
        source_ref = card.get("source_ref")
        if not isinstance(source_ref, dict):
            raise AssertionError(f"{card_id} must declare source_ref")
        function_name = str(source_ref.get("name") or "")
        if not hasattr(primitive_groups, function_name):
            raise AssertionError(f"{card_id} source function not importable: {function_name}")
        function_names.add(function_name)
        if int(source_ref.get("line") or 0) <= 0:
            raise AssertionError(f"{card_id} must declare source line")
        contract = card.get("contract")
        if not isinstance(contract, dict) or not contract.get("input") or not contract.get("output"):
            raise AssertionError(f"{card_id} must declare contract input/output")
        group_contract = card.get("group_contract")
        if not isinstance(group_contract, dict):
            raise AssertionError(f"{card_id} must declare group_contract")
        _list(group_contract, "hidden_member_edges", card_id, min_len=4)
        _list(card, "runtime_targets", card_id, min_len=1)
        _list(card, "adapter_mutators", card_id, min_len=2)
        _list(card, "mutations", card_id, min_len=2)
        _list(card, "proof_requirements", card_id, min_len=4)
        proof_refs = _list(card, "proof_refs", card_id, min_len=1)
        for proof_ref in proof_refs:
            proof_name = str(proof_ref.get("name") or "") if isinstance(proof_ref, dict) else ""
            method_name = proof_name.rsplit(".", 1)[-1]
            if not proof_name or (proof_name not in test_text and method_name not in test_text):
                raise AssertionError(f"{card_id} proof ref is not present in unit test file")
        if int(card.get("quality_score") or 0) < 90:
            raise AssertionError(f"{card_id} quality score should reflect unit-tested source backing")

    if len(ids) != len(set(ids)):
        raise AssertionError("source-backed group card ids must be unique")

    return {
        "cards": len(cards),
        "source_functions": sorted(function_names),
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
