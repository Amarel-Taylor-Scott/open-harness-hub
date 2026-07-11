#!/usr/bin/env python3
"""Verify primitive route fixtures against lifecycle cards and retrieval.

Route fixtures are useful only if they remain compact, candidate-only, and
reachable by AIDevObserver search. This verifier checks the generated fixture
corpus without executing or promoting any primitive.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_FIXTURE_DIR = _resource("data") / "dev-intel" / "primitive_route_fixtures"
DEFAULT_SEARCH_CARDS = _resource("data") / "dev-intel" / "primitive_source_lifecycle" / "primitive_search_cards.jsonl"
DEFAULT_REPORT = DEFAULT_FIXTURE_DIR / "verification_report.json"
DEFAULT_RESULTS = DEFAULT_FIXTURE_DIR / "verification_results.jsonl"
DEFAULT_SEARCH_SAMPLE_PER_KIND = 1
DEFAULT_SEARCH_LIMIT = 20
DEFAULT_MIN_SEARCH_HIT_RATE = 0.5
DEFAULT_MAX_ERRORS_IN_REPORT = 80
RAW_CODE_LINE_PATTERNS = (
    re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE),
    re.compile(r"^\s*class\s+\w+", re.MULTILINE),
    re.compile(r"^\s*import\s+[\w.]+", re.MULTILINE),
    re.compile(r"^\s*from\s+[\w.]+\s+import\s+", re.MULTILINE),
)
VALID_FIXTURE_KINDS = {"direct_reuse", "mutator_reuse", "edge_chain"}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path} line {line_no}: {exc}") from exc
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canon(row) + "\n")
            count += 1
    return count


def _card_contract(card: dict[str, Any]) -> dict[str, str]:
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return {
        "input": str(card.get("input_edge") or contract.get("input") or ""),
        "output": str(card.get("output_edge") or contract.get("output") or ""),
    }


def _bundle_text_by_fixture(bundle_rows: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(row.get("fixture_id")): str(row.get("candidate_bundle") or "")
        for row in bundle_rows
        if row.get("fixture_id")
    }


def _cards_by_id(cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(card.get("primitive_id")): card
        for card in cards
        if card.get("primitive_id")
    }


def _fixture_error(fixture: dict[str, Any], code: str, detail: str) -> dict[str, Any]:
    return {
        "fixture_id": fixture.get("fixture_id"),
        "fixture_kind": fixture.get("fixture_kind"),
        "code": code,
        "detail": detail,
        "candidate": True,
        "serves_truth": False,
    }


def _component_mutators(component: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for mutation in component.get("mutations") or []:
        if isinstance(mutation, dict) and mutation.get("mutator"):
            out.add(str(mutation["mutator"]))
    return out


def _structural_errors(
    fixture: dict[str, Any],
    *,
    cards_by_id: dict[str, dict[str, Any]],
    bundle_text: str,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    fixture_id = str(fixture.get("fixture_id") or "")
    kind = str(fixture.get("fixture_kind") or "")
    components = fixture.get("components") if isinstance(fixture.get("components"), list) else []
    recipe = fixture.get("expected_recipe") if isinstance(fixture.get("expected_recipe"), dict) else {}
    nodes = recipe.get("nodes") if isinstance(recipe.get("nodes"), list) else []
    plan_delta = fixture.get("expected_plan_delta") if isinstance(fixture.get("expected_plan_delta"), dict) else {}

    if not fixture_id:
        errors.append(_fixture_error(fixture, "missing_fixture_id", "fixture_id is required"))
    if kind not in VALID_FIXTURE_KINDS:
        errors.append(_fixture_error(fixture, "invalid_fixture_kind", f"kind={kind!r}"))
    if fixture.get("candidate") is not True or fixture.get("serves_truth") is not False:
        errors.append(_fixture_error(fixture, "truth_boundary_violation", "fixture must remain candidate-only"))
    if recipe.get("candidate") is not True or recipe.get("serves_truth") is not False:
        errors.append(_fixture_error(fixture, "recipe_truth_boundary_violation", "recipe must remain candidate-only"))
    if recipe.get("model_calls") != 0 or recipe.get("coding_harness_invoked") is not False:
        errors.append(_fixture_error(fixture, "fixture_not_deterministic", "fixtures must describe deterministic route reuse"))
    if not components:
        errors.append(_fixture_error(fixture, "missing_components", "at least one component is required"))
    if not nodes:
        errors.append(_fixture_error(fixture, "missing_nodes", "at least one expected recipe node is required"))
    if not bundle_text:
        errors.append(_fixture_error(fixture, "missing_candidate_bundle", "CandidateBundle row is required"))
    elif any(pattern.search(bundle_text) for pattern in RAW_CODE_LINE_PATTERNS):
        errors.append(_fixture_error(fixture, "candidate_bundle_contains_code", "CandidateBundle should expose compact edges, not source code"))

    component_by_alias = {
        str(component.get("alias")): component
        for component in components
        if component.get("alias")
    }
    component_ids = {str(component.get("primitive_id")) for component in components if component.get("primitive_id")}
    for component in components:
        primitive_id = str(component.get("primitive_id") or "")
        contract = component.get("contract") if isinstance(component.get("contract"), dict) else {}
        if component.get("candidate") is not True or component.get("serves_truth") is not False:
            errors.append(_fixture_error(fixture, "component_truth_boundary_violation", primitive_id))
        if not primitive_id:
            errors.append(_fixture_error(fixture, "component_missing_primitive_id", str(component.get("alias") or "")))
            continue
        card = cards_by_id.get(primitive_id)
        if not card:
            errors.append(_fixture_error(fixture, "component_not_in_lifecycle_search_cards", primitive_id))
            continue
        if card.get("serves_truth") is not False:
            errors.append(_fixture_error(fixture, "search_card_truth_boundary_violation", primitive_id))
        card_contract = _card_contract(card)
        if str(contract.get("input") or "") != card_contract["input"]:
            errors.append(_fixture_error(fixture, "component_input_edge_mismatch", primitive_id))
        if str(contract.get("output") or "") != card_contract["output"]:
            errors.append(_fixture_error(fixture, "component_output_edge_mismatch", primitive_id))
        if bundle_text and str(component.get("alias") or "") not in bundle_text:
            errors.append(_fixture_error(fixture, "candidate_bundle_missing_alias", str(component.get("alias") or "")))
        if bundle_text and card_contract["input"] and card_contract["input"] not in bundle_text:
            errors.append(_fixture_error(fixture, "candidate_bundle_missing_input_edge", card_contract["input"]))
        if bundle_text and card_contract["output"] and card_contract["output"] not in bundle_text:
            errors.append(_fixture_error(fixture, "candidate_bundle_missing_output_edge", card_contract["output"]))

    node_ids = {str(node.get("id")) for node in nodes if node.get("id")}
    for node in nodes:
        alias = str(node.get("candidate_alias") or "")
        primitive_id = str(node.get("primitive_id") or "")
        if node.get("candidate") is not True or node.get("serves_truth") is not False:
            errors.append(_fixture_error(fixture, "node_truth_boundary_violation", primitive_id))
        if alias not in component_by_alias:
            errors.append(_fixture_error(fixture, "node_unknown_candidate_alias", alias))
        if primitive_id and primitive_id not in component_ids:
            errors.append(_fixture_error(fixture, "node_unknown_primitive_id", primitive_id))
        for dep in node.get("depends_on") or []:
            if str(dep) not in node_ids:
                errors.append(_fixture_error(fixture, "node_unknown_dependency", str(dep)))

    if kind == "direct_reuse" and fixture.get("required_mutator"):
        errors.append(_fixture_error(fixture, "direct_fixture_has_mutator", str(fixture.get("required_mutator"))))
    if kind == "mutator_reuse":
        required = str(fixture.get("required_mutator") or "")
        if not required:
            errors.append(_fixture_error(fixture, "mutator_fixture_missing_required_mutator", "required_mutator is required"))
        if required and not any(required in _component_mutators(component) for component in components):
            errors.append(_fixture_error(fixture, "required_mutator_not_on_component", required))
        if required and not any(str(node.get("mutator") or "") == required for node in nodes):
            errors.append(_fixture_error(fixture, "required_mutator_not_on_node", required))
    if kind == "edge_chain":
        if len(nodes) < 2:
            errors.append(_fixture_error(fixture, "edge_chain_too_short", "edge_chain requires at least two nodes"))
        else:
            for left, right in zip(nodes, nodes[1:]):
                if str(left.get("output") or "") != str(right.get("input") or ""):
                    errors.append(_fixture_error(fixture, "edge_chain_contract_gap", f"{left.get('output')} != {right.get('input')}"))
                if str(left.get("id") or "") not in [str(dep) for dep in right.get("depends_on") or []]:
                    errors.append(_fixture_error(fixture, "edge_chain_missing_dependency", str(right.get("id") or "")))

    bindings = plan_delta.get("b") if isinstance(plan_delta.get("b"), list) else []
    if plan_delta.get("v") != 1 or plan_delta.get("p") != "pairs" or plan_delta.get("t") != 0:
        errors.append(_fixture_error(fixture, "invalid_expected_plan_delta_header", _canon(plan_delta)))
    if len(bindings) != len(nodes):
        errors.append(_fixture_error(fixture, "expected_plan_delta_binding_count_mismatch", str(len(bindings))))
    return errors


def _selected_search_fixtures(fixtures: list[dict[str, Any]], *, per_kind: int) -> list[dict[str, Any]]:
    if per_kind <= 0:
        return []
    by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fixture in fixtures:
        by_kind[str(fixture.get("fixture_kind") or "")].append(fixture)
    selected: list[dict[str, Any]] = []
    for kind in sorted(by_kind):
        selected.extend(by_kind[kind][:per_kind])
    return selected


def _run_search_checks(fixtures: list[dict[str, Any]], *, per_kind: int, search_limit: int) -> list[dict[str, Any]]:
    selected = _selected_search_fixtures(fixtures, per_kind=per_kind)
    if not selected:
        return []
    from src.teleon.observer import registry_search

    registry_search._GLOBAL_PRIMITIVE_CACHE.clear()  # noqa: SLF001 - verifier owns fresh corpus boundary.
    rows: list[dict[str, Any]] = []
    for fixture in selected:
        expected_ids = {
            str(component.get("primitive_id"))
            for component in fixture.get("components") or []
            if component.get("primitive_id")
        }
        hits = registry_search.search_reusable_primitives(
            str(fixture.get("prompt") or ""),
            limit=search_limit,
            requested_input=fixture.get("input_edge"),
            requested_output=fixture.get("output_edge"),
            visibility_scope="public",
        )
        hit_ids = [str(hit.get("primitive_id") or "") for hit in hits]
        matched_ids = sorted(expected_ids & set(hit_ids))
        rows.append({
            "fixture_id": fixture.get("fixture_id"),
            "fixture_kind": fixture.get("fixture_kind"),
            "expected_primitive_ids": sorted(expected_ids),
            "hit_primitive_ids": hit_ids[:search_limit],
            "matched_primitive_ids": matched_ids,
            "hit": bool(matched_ids),
            "hit_count": len(hits),
            "visibility_scope": "public",
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def verify_route_fixtures(
    *,
    fixture_dir: Path,
    search_cards_path: Path,
    report_path: Path,
    results_path: Path,
    search_sample_per_kind: int,
    search_limit: int,
    min_search_hit_rate: float,
    write: bool = True,
) -> dict[str, Any]:
    fixture_path = fixture_dir / "route_fixtures.jsonl"
    bundle_path = fixture_dir / "candidate_bundles.jsonl"
    fixtures = _read_jsonl(fixture_path)
    bundle_rows = _read_jsonl(bundle_path)
    cards = _read_jsonl(search_cards_path)
    bundle_by_fixture = _bundle_text_by_fixture(bundle_rows)
    cards_by_id = _cards_by_id(cards)

    structural_errors: list[dict[str, Any]] = []
    fixture_results: list[dict[str, Any]] = []
    for fixture in fixtures:
        errors = _structural_errors(
            fixture,
            cards_by_id=cards_by_id,
            bundle_text=bundle_by_fixture.get(str(fixture.get("fixture_id") or ""), ""),
        )
        structural_errors.extend(errors)
        fixture_results.append({
            "fixture_id": fixture.get("fixture_id"),
            "fixture_kind": fixture.get("fixture_kind"),
            "structural_error_count": len(errors),
            "candidate": True,
            "serves_truth": False,
        })

    search_results = _run_search_checks(
        fixtures,
        per_kind=search_sample_per_kind,
        search_limit=search_limit,
    )
    search_checked = len(search_results)
    search_hits = sum(1 for row in search_results if row.get("hit"))
    search_hit_rate = (search_hits / search_checked) if search_checked else 1.0
    bundle_ids = set(bundle_by_fixture)
    fixture_ids = {str(row.get("fixture_id") or "") for row in fixtures if row.get("fixture_id")}
    missing_bundles = sorted(fixture_ids - bundle_ids)
    extra_bundles = sorted(bundle_ids - fixture_ids)
    kind_counts = Counter(str(row.get("fixture_kind") or "") for row in fixtures)
    ok = (
        bool(fixtures)
        and not structural_errors
        and not missing_bundles
        and not extra_bundles
        and search_hit_rate >= min_search_hit_rate
        and all(row.get("serves_truth") is False for row in fixtures + bundle_rows + cards)
    )
    report = {
        "record_type": "primitive_route_fixture_verification_report",
        "created_at": _utc(),
        "fixture_dir": str(fixture_dir),
        "search_cards_path": str(search_cards_path),
        "fixtures_checked": len(fixtures),
        "candidate_bundles_checked": len(bundle_rows),
        "search_cards_checked": len(cards),
        "fixture_kind_counts": dict(sorted(kind_counts.items())),
        "structural_error_count": len(structural_errors),
        "missing_candidate_bundle_count": len(missing_bundles),
        "extra_candidate_bundle_count": len(extra_bundles),
        "search_sample_per_kind": search_sample_per_kind,
        "search_limit": search_limit,
        "search_checked": search_checked,
        "search_hits": search_hits,
        "search_hit_rate": round(search_hit_rate, 4),
        "min_search_hit_rate": min_search_hit_rate,
        "sample_errors": structural_errors[:DEFAULT_MAX_ERRORS_IN_REPORT],
        "missing_candidate_bundles": missing_bundles[:DEFAULT_MAX_ERRORS_IN_REPORT],
        "extra_candidate_bundles": extra_bundles[:DEFAULT_MAX_ERRORS_IN_REPORT],
        "search_results": search_results,
        "ok": ok,
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        _write_jsonl(results_path, [*fixture_results, *search_results])
    return report


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture_dir = root / "fixtures"
        fixture_dir.mkdir()
        search_cards_path = root / "cards.jsonl"
        report_path = root / "report.json"
        results_path = root / "results.jsonl"
        card_a = {
            "record_type": "primitive_search_card",
            "primitive_id": "prim:a",
            "label": "normalize_a",
            "contract": {"input": "RawA", "output": "CleanA"},
            "input_edge": "RawA",
            "output_edge": "CleanA",
            "source_evidence_status": "source_backed",
            "mutations": [{
                "mutator": "map_sequence",
                "target_edge_template": {"input": "list[RawA]", "output": "list[CleanA]"},
                "candidate": True,
                "serves_truth": False,
            }],
            "candidate": True,
            "serves_truth": False,
        }
        card_b = {
            "record_type": "primitive_search_card",
            "primitive_id": "prim:b",
            "label": "resolve_b",
            "contract": {"input": "CleanA", "output": "ResolvedB"},
            "input_edge": "CleanA",
            "output_edge": "ResolvedB",
            "source_evidence_status": "source_backed",
            "mutations": [],
            "candidate": True,
            "serves_truth": False,
        }
        fixtures = [{
            "record_type": "primitive_route_fixture",
            "fixture_id": "fixture:chain",
            "fixture_kind": "edge_chain",
            "prompt": "Build a deterministic route from RawA to ResolvedB.",
            "input_edge": "RawA",
            "output_edge": "ResolvedB",
            "components": [
                {"alias": "P0", "primitive_id": "prim:a", "contract": {"input": "RawA", "output": "CleanA"}, "mutations": card_a["mutations"], "candidate": True, "serves_truth": False},
                {"alias": "P1", "primitive_id": "prim:b", "contract": {"input": "CleanA", "output": "ResolvedB"}, "mutations": [], "candidate": True, "serves_truth": False},
            ],
            "expected_plan_delta": {"v": 1, "p": "pairs", "t": 0, "b": [[0, 0], [1, 1]], "r": [], "g": []},
            "expected_recipe": {
                "nodes": [
                    {"id": "normalize", "candidate_alias": "P0", "primitive_id": "prim:a", "input": "RawA", "output": "CleanA", "depends_on": [], "candidate": True, "serves_truth": False},
                    {"id": "resolve", "candidate_alias": "P1", "primitive_id": "prim:b", "input": "CleanA", "output": "ResolvedB", "depends_on": ["normalize"], "candidate": True, "serves_truth": False},
                ],
                "model_calls": 0,
                "coding_harness_invoked": False,
                "candidate": True,
                "serves_truth": False,
            },
            "candidate": True,
            "serves_truth": False,
        }]
        bundles = [{
            "record_type": "primitive_route_candidate_bundle",
            "fixture_id": "fixture:chain",
            "candidate_bundle": "Q route\nO ResolvedB\nT0 lifecycle_route_fixture\nS0 normalize RawA>CleanA\nS1 resolve CleanA>ResolvedB\nC0.0 P0 RawA>CleanA\nC1.0 P1 CleanA>ResolvedB\n",
            "candidate": True,
            "serves_truth": False,
        }]
        _write_jsonl(search_cards_path, [card_a, card_b])
        _write_jsonl(fixture_dir / "route_fixtures.jsonl", fixtures)
        _write_jsonl(fixture_dir / "candidate_bundles.jsonl", bundles)
        report = verify_route_fixtures(
            fixture_dir=fixture_dir,
            search_cards_path=search_cards_path,
            report_path=report_path,
            results_path=results_path,
            search_sample_per_kind=0,
            search_limit=DEFAULT_SEARCH_LIMIT,
            min_search_hit_rate=DEFAULT_MIN_SEARCH_HIT_RATE,
            write=True,
        )
        assert report["ok"] is True
        assert report["fixtures_checked"] == 1
        assert report["structural_error_count"] == 0
        assert report_path.exists()
        assert results_path.exists()
    print("PASS - primitive route fixture verifier: fixture corpus structure, CandidateBundles, edges, mutators, and candidate-only boundaries verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument("--search-cards", default=str(DEFAULT_SEARCH_CARDS))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--search-sample-per-kind", type=int, default=DEFAULT_SEARCH_SAMPLE_PER_KIND)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--min-search-hit-rate", type=float, default=DEFAULT_MIN_SEARCH_HIT_RATE)
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    report = verify_route_fixtures(
        fixture_dir=Path(args.fixture_dir),
        search_cards_path=Path(args.search_cards),
        report_path=Path(args.report),
        results_path=Path(args.results),
        search_sample_per_kind=0 if args.skip_search else args.search_sample_per_kind,
        search_limit=args.search_limit,
        min_search_hit_rate=args.min_search_hit_rate,
        write=True,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
