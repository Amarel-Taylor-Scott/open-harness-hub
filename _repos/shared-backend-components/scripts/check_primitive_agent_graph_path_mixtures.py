#!/usr/bin/env python3
"""Validate the primitive agent graph path mixture seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-agent-graph-path-mixtures")
CUSTOMIZATION_DIR = _resource("catalog/knowledge-packs/data/primitive-customization-overlays")
MANIFEST_PATH = PACK_DIR / "manifest.json"

ID_FIELDS = {
    "agent_role_id",
    "path_family_id",
    "mixture_id",
    "playbook_id",
    "overlay_id",
    "path_family",
}
ID_LIST_FIELDS = {
    "agent_sequence",
    "agent_nodes",
    "specialized_primitive_refs",
    "troubleshooting_playbooks",
    "country_industry_overlays",
}
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)
REQUIRED_ROUTE_VARIANTS = {"cheap", "balanced", "quality"}


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
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
    if not rows:
        raise AssertionError(f"{path}: expected at least one row")
    return rows


def _require_candidate_boundary(row: dict[str, Any], row_id: str) -> None:
    if row.get("candidate") is not True:
        raise AssertionError(f"{row_id} must keep candidate=true")
    if row.get("serves_truth") is not False:
        raise AssertionError(f"{row_id} must keep serves_truth=false")


def _require_list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def _require_dict(row: dict[str, Any], field: str, row_id: str) -> dict[str, Any]:
    value = row.get(field)
    if not isinstance(value, dict) or not value:
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _assert_version_free_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be stable and version-free: {value!r}")


def _check_id_fields(row: dict[str, Any], row_id: str) -> None:
    for field in ID_FIELDS:
        value = row.get(field)
        if isinstance(value, str):
            _assert_version_free_id(value, row_id, field)
    for field in ID_LIST_FIELDS:
        value = row.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _assert_version_free_id(item, row_id, field)


def _primary_ids(rows: list[dict[str, Any]], field: str) -> set[str]:
    ids = {str(row.get(field) or "") for row in rows}
    if "" in ids:
        raise AssertionError(f"every {field} row must declare a non-empty id")
    if len(ids) != len(rows):
        raise AssertionError(f"{field} values must be unique")
    return ids


def _load_specialized_primitive_ids() -> set[str]:
    path = CUSTOMIZATION_DIR / "specialized_primitives.jsonl"
    if not path.exists():
        return set()
    return _primary_ids(_read_jsonl(path), "primitive_id")


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise AssertionError("manifest must declare files")

    agent_roles = _read_jsonl(PACK_DIR / str(files.get("agent_roles")))
    path_families = _read_jsonl(PACK_DIR / str(files.get("path_families")))
    graph_path_mixtures = _read_jsonl(PACK_DIR / str(files.get("graph_path_mixtures")))
    troubleshooting = _read_jsonl(PACK_DIR / str(files.get("troubleshooting_playbooks")))
    country_overlays = _read_jsonl(PACK_DIR / str(files.get("country_industry_overlays")))

    agent_role_ids = _primary_ids(agent_roles, "agent_role_id")
    path_family_ids = _primary_ids(path_families, "path_family_id")
    mixture_ids = _primary_ids(graph_path_mixtures, "mixture_id")
    playbook_ids = _primary_ids(troubleshooting, "playbook_id")
    country_overlay_ids = _primary_ids(country_overlays, "overlay_id")
    specialized_primitive_ids = _load_specialized_primitive_ids()

    all_primary_ids = agent_role_ids | path_family_ids | mixture_ids | playbook_ids | country_overlay_ids
    if len(all_primary_ids) != sum(len(ids) for ids in (agent_role_ids, path_family_ids, mixture_ids, playbook_ids, country_overlay_ids)):
        raise AssertionError("agent path mixture ids must be unique across row families")

    for row in agent_roles:
        row_id = str(row["agent_role_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if "->" in str(row.get("input_edge") or "") or "->" in str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must keep input_edge and output_edge separate")
        _require_list(row, "responsibilities", row_id, min_len=3)
        if not str(row.get("handoff_contract") or ""):
            raise AssertionError(f"{row_id} must declare handoff_contract")

    for row in path_families:
        row_id = str(row["path_family_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if "->" in str(row.get("input_edge") or "") or "->" in str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must keep input_edge and output_edge separate")
        for agent_id in _require_list(row, "agent_sequence", row_id, min_len=4):
            if agent_id not in agent_role_ids:
                raise AssertionError(f"{row_id} references unknown agent role {agent_id!r}")
        _require_list(row, "best_for", row_id, min_len=3)
        _require_list(row, "route_variants", row_id, min_len=3)
        if not str(row.get("fallback_policy") or ""):
            raise AssertionError(f"{row_id} must declare fallback_policy")

    for row in troubleshooting:
        row_id = str(row["playbook_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        steps = _require_list(row, "ordered_steps", row_id, min_len=5)
        step_text = " ".join(str(step) for step in steps)
        for required in ("reproduce", "isolate", "emit"):
            if required not in step_text:
                raise AssertionError(f"{row_id} troubleshooting steps must include {required}")
        _require_list(row, "repair_mutators", row_id)
        _require_list(row, "proof_receipts", row_id, min_len=3)
        if not str(row.get("escalation_policy") or ""):
            raise AssertionError(f"{row_id} must declare escalation_policy")

    country_scopes: set[str] = set()
    industry_scopes: set[str] = set()
    for row in country_overlays:
        row_id = str(row["overlay_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        countries = _require_list(row, "country_scope", row_id)
        industries = _require_list(row, "industry_scope", row_id)
        country_scopes.update(str(country) for country in countries)
        industry_scopes.update(str(industry) for industry in industries)
        _require_list(row, "adds_to_path", row_id, min_len=3)
        _require_list(row, "proof_requirements", row_id, min_len=3)
        _require_list(row, "human_review_triggers", row_id)
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} source_refs should stay empty until verified")
        if row.get("source_evidence_status") != "unverified_intake_requires_source_ref_resolution":
            raise AssertionError(f"{row_id} must keep unverified intake source status")

    if len(country_scopes - {"global"}) < 8:
        raise AssertionError("expected at least 8 non-global country or region scopes")
    if len(industry_scopes) < 12:
        raise AssertionError("expected at least 12 industry scopes")

    for row in graph_path_mixtures:
        row_id = str(row["mixture_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if row.get("path_family") not in path_family_ids:
            raise AssertionError(f"{row_id} references unknown path_family {row.get('path_family')!r}")
        for agent_id in _require_list(row, "agent_nodes", row_id, min_len=5):
            if agent_id not in agent_role_ids:
                raise AssertionError(f"{row_id} references unknown agent role {agent_id!r}")
        for primitive_id in row.get("specialized_primitive_refs") or []:
            if primitive_id not in specialized_primitive_ids:
                raise AssertionError(f"{row_id} references unknown specialized primitive {primitive_id!r}")
        for playbook_id in _require_list(row, "troubleshooting_playbooks", row_id):
            if playbook_id not in playbook_ids:
                raise AssertionError(f"{row_id} references unknown troubleshooting playbook {playbook_id!r}")
        for overlay_id in row.get("country_industry_overlays") or []:
            if overlay_id not in country_overlay_ids:
                raise AssertionError(f"{row_id} references unknown country/industry overlay {overlay_id!r}")
        _require_list(row, "graph_path", row_id, min_len=5)
        route_variants = _require_dict(row, "route_variants", row_id)
        if set(route_variants) != REQUIRED_ROUTE_VARIANTS:
            raise AssertionError(f"{row_id} route_variants must be {sorted(REQUIRED_ROUTE_VARIANTS)}")
        for variant, steps in route_variants.items():
            if not isinstance(steps, list) or len(steps) < 2:
                raise AssertionError(f"{row_id} route variant {variant} must have at least 2 steps")
        _require_list(row, "industry_scope", row_id)
        _require_list(row, "country_scope", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=4)
        _require_list(row, "negative_memory_queries", row_id, min_len=4)

    mixture_industries = {industry for row in graph_path_mixtures for industry in row["industry_scope"]}
    mixture_countries = {country for row in graph_path_mixtures for country in row["country_scope"]}
    if len(mixture_industries) < 12:
        raise AssertionError("graph path mixtures should cover at least 12 industry labels")
    if len(mixture_countries - {"global"}) < 4:
        raise AssertionError("graph path mixtures should cover at least 4 non-global country or region scopes")

    return {
        "agent_roles": len(agent_roles),
        "path_families": len(path_families),
        "graph_path_mixtures": len(graph_path_mixtures),
        "troubleshooting_playbooks": len(troubleshooting),
        "country_industry_overlays": len(country_overlays),
        "candidate": True,
        "serves_truth": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run validation checks")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
