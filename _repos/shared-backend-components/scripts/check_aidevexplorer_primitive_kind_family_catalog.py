#!/usr/bin/env python3
"""Validate the AIDevExplorer primitive-kind family catalog."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_MANIFEST_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS,
    AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY,
    REPO_ROOT,
)

CATALOG_PATH = _resource(AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_MANIFEST_PATH)

REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "primitive_kind",
    "title",
    "input_edge",
    "output_edge",
    "visible_edge",
    "hidden_member_edges",
    "effects",
    "adapter_mutators",
    "proof_requirements",
    "common_pitfalls",
    "domains",
    "runtime_targets",
    "example_tasks",
    "source_family",
    "source_evidence_status",
    "trust",
    "candidate",
    "serves_truth",
)

REQUIRED_KINDS: tuple[str, ...] = (
    "api.endpoint",
    "service.group",
    "webhook.handler",
    "queue.consumer",
    "cron.job",
    "cli.command",
    "workflow.step",
    "kubernetes.job",
    "dashboard",
    "rag.pipeline",
    "llm.tool",
    "db.migration",
    "integration.connector",
    "security.compliance.workflow",
    "terraform.module",
    "github.action",
    "contract.test",
    "mock.server",
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
    rows = _read_jsonl(CATALOG_PATH)
    manifest = _read_json(MANIFEST_PATH)
    if int(manifest.get("row_count") or 0) != len(rows):
        raise AssertionError("manifest row_count must match rows")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must remain candidate=true and serves_truth=false")
    if len(rows) < 40:
        raise AssertionError("primitive-kind family catalog should contain at least 40 rows")

    ids: list[str] = []
    kinds: set[str] = set()
    domains: set[str] = set()
    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id:
            raise AssertionError("every row must declare id")
        ids.append(row_id)
        missing = sorted(field for field in REQUIRED_FIELDS if field not in row)
        if missing:
            raise AssertionError(f"{row_id} missing fields: {missing}")
        if row.get("candidate") is not True or row.get("serves_truth") is not False:
            raise AssertionError(f"{row_id} must remain candidate=true and serves_truth=false")
        if row.get("trust") != "candidate":
            raise AssertionError(f"{row_id} must keep trust=candidate")
        if row.get("source_family") != AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY:
            raise AssertionError(f"{row_id} has unexpected source_family")
        if row.get("source_evidence_status") != AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS:
            raise AssertionError(f"{row_id} has unexpected source_evidence_status")
        visible_edge = str(row.get("visible_edge") or "")
        if " -> " not in visible_edge:
            raise AssertionError(f"{row_id} must declare visible input -> output edge")
        if str(row.get("input_edge") or "") not in visible_edge or str(row.get("output_edge") or "") not in visible_edge:
            raise AssertionError(f"{row_id} visible edge must contain input/output edge text")
        _list(row, "hidden_member_edges", row_id, min_len=3)
        _list(row, "effects", row_id, min_len=1)
        _list(row, "adapter_mutators", row_id, min_len=1)
        _list(row, "proof_requirements", row_id, min_len=3)
        _list(row, "common_pitfalls", row_id, min_len=3)
        _list(row, "domains", row_id, min_len=1)
        _list(row, "runtime_targets", row_id, min_len=1)
        _list(row, "example_tasks", row_id, min_len=2)
        kinds.add(str(row.get("primitive_kind") or ""))
        domains.update(str(domain) for domain in row.get("domains") or [])

    if len(ids) != len(set(ids)):
        raise AssertionError("primitive-kind family ids must be unique")
    missing_kinds = sorted(set(REQUIRED_KINDS) - kinds)
    if missing_kinds:
        raise AssertionError(f"missing required primitive kinds: {missing_kinds}")
    if len(domains) < 15:
        raise AssertionError("primitive-kind family catalog should span at least 15 domains")

    return {
        "rows": len(rows),
        "primitive_kinds": len(kinds),
        "domains": len(domains),
        "required_kind_coverage": len(REQUIRED_KINDS),
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
