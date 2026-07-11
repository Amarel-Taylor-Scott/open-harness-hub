#!/usr/bin/env python3
"""Generate route fixtures from primitive lifecycle search cards.

This is the bridge from "we have many searchable primitive cards" to
"AIDevObserver can repeatedly test realistic reuse routes." It does not execute
or promote primitives. It emits candidate-only fixtures that assert a planner or
deterministic compiler should reuse specific source-backed cards instead of
rewriting code.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]

DEFAULT_SEARCH_CARDS = _resource("data") / "dev-intel" / "primitive_source_lifecycle" / "primitive_search_cards.jsonl"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "primitive_route_fixtures"
DEFAULT_DIRECT_LIMIT = 160
DEFAULT_MUTATOR_LIMIT = 160
DEFAULT_CHAIN_LIMIT = 120
DEFAULT_MAX_CHAIN_CANDIDATES_PER_EDGE = 40
GENERIC_EDGE_TOKENS = {"", "Any", "AnyJson", "None", "unknown"}
MUTATOR_PRIORITY = {
    "map_sequence": 10,
    "output_wrapper": 20,
    "input_envelope_wrapper": 30,
    "field_rename": 40,
    "field_project": 50,
    "schema_validator_inserter": 60,
    "type_cast": 70,
    "cache_wrapper": 80,
    "retry_wrapper": 90,
    "idempotency_wrapper": 100,
    "cli_wrapper": 110,
    "api_endpoint_wrapper": 120,
    "cloud_function_wrapper": 130,
    "k8s_job_wrapper": 140,
    "k8s_deployment_wrapper": 150,
    "k8s_cronjob_wrapper": 160,
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any, *, n: int = 24) -> str:
    raw = value if isinstance(value, str) else _canon(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:n]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:80] or "route"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path} line {i}: {exc}") from exc
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canon(row) + "\n")
            count += 1
    return count


def _quality(card: dict[str, Any]) -> int:
    try:
        return int(card.get("quality_score") or 0)
    except (TypeError, ValueError):
        return 0


def _edge(value: Any) -> str:
    return str(value or "").strip()


def _contract(card: dict[str, Any]) -> dict[str, str]:
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return {
        "input": _edge(card.get("input_edge") or contract.get("input")),
        "output": _edge(card.get("output_edge") or contract.get("output")),
    }


def _is_generic_edge(value: str) -> bool:
    return value in GENERIC_EDGE_TOKENS or value.startswith("Any+")


def _usable_card(card: dict[str, Any]) -> bool:
    contract = _contract(card)
    return (
        card.get("serves_truth") is False
        and card.get("source_evidence_status") == "source_backed"
        and bool(card.get("primitive_id"))
        and bool(contract["input"])
        and bool(contract["output"])
        and not _is_generic_edge(contract["input"])
        and not _is_generic_edge(contract["output"])
    )


def _component(card: dict[str, Any], *, alias: str) -> dict[str, Any]:
    contract = _contract(card)
    return {
        "alias": alias,
        "primitive_id": card.get("primitive_id"),
        "label": card.get("label"),
        "contract": contract,
        "blackbox": card.get("blackbox"),
        "effects": card.get("effects") or [],
        "runtime_targets": card.get("runtime_targets") or [],
        "source_ref": card.get("source_ref"),
        "source_surface_id": card.get("source_surface_id"),
        "source_family": card.get("source_family"),
        "mutations": card.get("mutations") or [],
        "quality_score": _quality(card),
        "candidate": True,
        "serves_truth": False,
    }


def _node_from_component(component: dict[str, Any], *, node_id: str, depends_on: list[str] | None = None) -> dict[str, Any]:
    contract = component.get("contract") or {}
    return {
        "id": node_id,
        "candidate_alias": component["alias"],
        "primitive_id": component.get("primitive_id"),
        "input": contract.get("input"),
        "output": contract.get("output"),
        "depends_on": depends_on or [],
        "candidate": True,
        "serves_truth": False,
    }


def _candidate_bundle(fixture: dict[str, Any]) -> str:
    rows = [
        f"Q {fixture['prompt']}",
        f"O {fixture['output_edge']}",
        "T0 lifecycle_route_fixture",
        "",
    ]
    for index, node in enumerate(fixture["expected_recipe"]["nodes"]):
        rows.append(
            f"S{index} {node['id']} {node['input']}>{node['output']} "
            "req:source_backed,serves_truth_false"
        )
    rows.append("")
    for index, component in enumerate(fixture["components"]):
        mutations = component.get("mutations") or []
        mutator_ids = ",".join(
            str(m.get("mutator"))
            for m in mutations
            if isinstance(m, dict) and m.get("mutator")
        ) or "-"
        source_ref = component.get("source_ref") or {}
        contract = component.get("contract") or {}
        rows.append(
            f"C{index}.0 {component['alias']} {contract.get('input')}>{contract.get('output')} "
            f"q:{component.get('quality_score', 0)} tools:{mutator_ids} "
            f"src:{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}"
        )
    if fixture.get("required_mutator"):
        rows.append(f"R0 {fixture['required_mutator']} required")
    rows.extend(["", "Return PlanDelta JSON only."])
    return "\n".join(rows) + "\n"


def _base_fixture(*, kind: str, prompt: str, components: list[dict[str, Any]], nodes: list[dict[str, Any]], required_mutator: str | None = None) -> dict[str, Any]:
    output_edge = str(nodes[-1].get("output") if nodes else "ImplementationPlan")
    fixture_id = f"route_fixture:{kind}:{_sha({'prompt': prompt, 'nodes': nodes, 'mutator': required_mutator})}"
    return {
        "record_type": "primitive_route_fixture",
        "fixture_id": fixture_id,
        "fixture_kind": kind,
        "prompt": prompt,
        "input_edge": str(nodes[0].get("input") if nodes else "DeveloperIntent"),
        "output_edge": output_edge,
        "components": components,
        "required_mutator": required_mutator,
        "expected_plan_delta": {
            "v": 1,
            "p": "pairs",
            "t": 0,
            "b": [[index, index] for index in range(len(nodes))],
            "r": [[0, required_mutator]] if required_mutator else [],
            "g": [],
        },
        "expected_recipe": {
            "kind": "deterministic_route_fixture_recipe",
            "nodes": nodes,
            "model_calls": 0,
            "coding_harness_invoked": False,
            "candidate": True,
            "serves_truth": False,
        },
        "proof_assertions": [
            "all_components_source_backed",
            "all_components_serves_truth_false",
            "candidate_bundle_contains_edges",
            "planner_context_uses_compact_cards_only",
            "harness_must_not_rewrite_selected_primitives",
        ],
        "candidate": True,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _direct_fixture(card: dict[str, Any]) -> dict[str, Any]:
    component = _component(card, alias="P0")
    contract = component["contract"]
    prompt = (
        f"Build a deterministic route that reuses `{component['label']}` to transform "
        f"{contract['input']} into {contract['output']} without rewriting the primitive."
    )
    return _base_fixture(
        kind="direct_reuse",
        prompt=prompt,
        components=[component],
        nodes=[_node_from_component(component, node_id=_slug(str(component["label"] or "reuse")))],
    )


def _mutator_fixture(card: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    component = _component(card, alias="P0")
    target = mutation.get("target_edge_template") if isinstance(mutation.get("target_edge_template"), dict) else {}
    input_edge = str(target.get("input") or component["contract"]["input"])
    output_edge = str(target.get("output") or component["contract"]["output"])
    mutator = str(mutation.get("mutator") or "deterministic_mutator")
    prompt = (
        f"Build a deterministic route that applies `{mutator}` to `{component['label']}` "
        f"so the route handles {input_edge} and returns {output_edge}."
    )
    node = _node_from_component(component, node_id=f"{_slug(mutator)}_{_slug(str(component['label'] or 'reuse'))}")
    node["input"] = input_edge
    node["output"] = output_edge
    node["mutator"] = mutator
    return _base_fixture(
        kind="mutator_reuse",
        prompt=prompt,
        components=[component],
        nodes=[node],
        required_mutator=mutator,
    )


def _chain_fixture(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    c0 = _component(first, alias="P0")
    c1 = _component(second, alias="P1")
    n0 = _node_from_component(c0, node_id=_slug(str(c0["label"] or "step_1")))
    n1 = _node_from_component(c1, node_id=_slug(str(c1["label"] or "step_2")), depends_on=[n0["id"]])
    prompt = (
        f"Build a two-step deterministic route: reuse `{c0['label']}` to produce "
        f"{c0['contract']['output']}`, then reuse `{c1['label']}` to produce {c1['contract']['output']}."
    )
    return _base_fixture(
        kind="edge_chain",
        prompt=prompt,
        components=[c0, c1],
        nodes=[n0, n1],
    )


def build_route_fixtures(
    search_cards: list[dict[str, Any]],
    *,
    direct_limit: int,
    mutator_limit: int,
    chain_limit: int,
    max_chain_candidates_per_edge: int = DEFAULT_MAX_CHAIN_CANDIDATES_PER_EDGE,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cards = [card for card in search_cards if _usable_card(card)]
    cards.sort(key=lambda card: (-_quality(card), str(card.get("label") or ""), str(card.get("primitive_id") or "")))

    fixtures: list[dict[str, Any]] = []
    direct_cards = cards[:direct_limit] if direct_limit else cards
    fixtures.extend(_direct_fixture(card) for card in direct_cards)

    mutation_pairs: list[tuple[int, str, dict[str, Any], dict[str, Any]]] = []
    for card in cards:
        for mutation in card.get("mutations") or []:
            if not isinstance(mutation, dict) or not mutation.get("mutator"):
                continue
            mutation_pairs.append((
                MUTATOR_PRIORITY.get(str(mutation.get("mutator")), 999),
                str(card.get("primitive_id") or ""),
                card,
                mutation,
            ))
    mutation_pairs.sort(key=lambda item: (item[0], -_quality(item[2]), item[1]))
    selected_mutations = mutation_pairs[:mutator_limit] if mutator_limit else mutation_pairs
    for _, _, card, mutation in selected_mutations:
        fixtures.append(_mutator_fixture(card, mutation))

    by_input: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        by_input[_contract(card)["input"]].append(card)
    for edge in by_input:
        by_input[edge] = by_input[edge][:max_chain_candidates_per_edge]

    chains: list[tuple[int, str, dict[str, Any], dict[str, Any]]] = []
    for first in cards:
        out_edge = _contract(first)["output"]
        if _is_generic_edge(out_edge):
            continue
        for second in by_input.get(out_edge, []):
            if first.get("primitive_id") == second.get("primitive_id"):
                continue
            chains.append((
                -(_quality(first) + _quality(second)),
                f"{first.get('primitive_id')}->{second.get('primitive_id')}",
                first,
                second,
            ))
    chains.sort(key=lambda item: (item[0], item[1]))
    selected_chains = chains[:chain_limit] if chain_limit else chains
    fixtures.extend(_chain_fixture(first, second) for _, _, first, second in selected_chains)

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for fixture in fixtures:
        if fixture["fixture_id"] in seen:
            continue
        seen.add(fixture["fixture_id"])
        unique.append(fixture)

    bundle_rows = [
        {
            "record_type": "primitive_route_candidate_bundle",
            "fixture_id": fixture["fixture_id"],
            "fixture_kind": fixture["fixture_kind"],
            "candidate_bundle": _candidate_bundle(fixture),
            "candidate": True,
            "serves_truth": False,
            "created_at": fixture["created_at"],
        }
        for fixture in unique
    ]
    return unique, bundle_rows


def write_route_fixture_artifacts(
    search_cards_path: Path,
    out_dir: Path,
    *,
    direct_limit: int,
    mutator_limit: int,
    chain_limit: int,
    write: bool = True,
) -> dict[str, Any]:
    cards = _read_jsonl(search_cards_path)
    fixtures, bundles = build_route_fixtures(
        cards,
        direct_limit=direct_limit,
        mutator_limit=mutator_limit,
        chain_limit=chain_limit,
    )
    by_kind = Counter(str(row.get("fixture_kind")) for row in fixtures)
    component_sources = Counter(
        str(component.get("source_surface_id") or "unknown")
        for fixture in fixtures
        for component in fixture.get("components") or []
    )
    manifest = {
        "record_type": "primitive_route_fixture_manifest",
        "created_at": _utc(),
        "search_cards_path": str(search_cards_path),
        "out_dir": str(out_dir),
        "search_cards_read": len(cards),
        "route_fixtures": len(fixtures),
        "candidate_bundles": len(bundles),
        "fixture_kind_counts": dict(sorted(by_kind.items())),
        "component_source_counts": dict(sorted(component_sources.items())),
        "limits": {
            "direct": direct_limit,
            "mutator": mutator_limit,
            "chain": chain_limit,
        },
        "artifacts": {
            "route_fixtures": str(out_dir / "route_fixtures.jsonl"),
            "candidate_bundles": str(out_dir / "candidate_bundles.jsonl"),
            "summary": str(out_dir / "summary.md"),
            "manifest": str(out_dir / "manifest.json"),
        },
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(out_dir / "route_fixtures.jsonl", fixtures)
        _write_jsonl(out_dir / "candidate_bundles.jsonl", bundles)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        _write_summary(out_dir / "summary.md", manifest, fixtures)
    return manifest


def _write_summary(path: Path, manifest: dict[str, Any], fixtures: list[dict[str, Any]]) -> None:
    lines = [
        "# Primitive Route Fixtures",
        "",
        f"- Updated: `{manifest['created_at']}`",
        f"- Search cards read: `{manifest['search_cards_read']}`",
        f"- Route fixtures: `{manifest['route_fixtures']}`",
        f"- CandidateBundles: `{manifest['candidate_bundles']}`",
        f"- Serves truth: `{manifest['serves_truth']}`",
        "",
        "## Fixture Kinds",
        "",
        "```json",
        json.dumps(manifest["fixture_kind_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Component Sources",
        "",
        "```json",
        json.dumps(manifest["component_source_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Example Fixtures",
        "",
    ]
    for fixture in fixtures[:12]:
        lines.extend([
            f"- `{fixture['fixture_id']}`",
            f"  - kind: `{fixture['fixture_kind']}`",
            f"  - prompt: {fixture['prompt']}",
            f"  - components: `{len(fixture.get('components') or [])}`",
        ])
    lines.extend([
        "",
        "## Boundary",
        "",
        "These fixtures are candidate-only benchmark/planning artifacts. They do not execute source, promote primitives, or claim truth.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cards_path = root / "cards.jsonl"
        out_dir = root / "out"
        cards = [
            {
                "record_type": "primitive_search_card",
                "primitive_id": "prim:normalize-name",
                "label": "normalize_company_name",
                "contract": {"input": "RawCompanyName", "output": "NormalizedCompanyName"},
                "input_edge": "RawCompanyName",
                "output_edge": "NormalizedCompanyName",
                "blackbox": "Normalize company names.",
                "source_evidence_status": "source_backed",
                "source_surface_id": "edge-foundry",
                "source_ref": {"path": "src/company.py", "line": 4, "name": "normalize_company_name"},
                "quality_score": 90,
                "mutations": [{
                    "mutator": "map_sequence",
                    "target_edge_template": {
                        "input": "list[RawCompanyName]",
                        "output": "list[NormalizedCompanyName]",
                    },
                    "candidate": True,
                    "serves_truth": False,
                }],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "record_type": "primitive_search_card",
                "primitive_id": "prim:resolve-company",
                "label": "resolve_company",
                "contract": {"input": "NormalizedCompanyName", "output": "CompanyProfile"},
                "input_edge": "NormalizedCompanyName",
                "output_edge": "CompanyProfile",
                "blackbox": "Resolve normalized company names.",
                "source_evidence_status": "source_backed",
                "source_surface_id": "edge-foundry",
                "source_ref": {"path": "src/company.py", "line": 9, "name": "resolve_company"},
                "quality_score": 88,
                "mutations": [],
                "candidate": True,
                "serves_truth": False,
            },
        ]
        _write_jsonl(cards_path, cards)
        manifest = write_route_fixture_artifacts(
            cards_path,
            out_dir,
            direct_limit=2,
            mutator_limit=2,
            chain_limit=2,
            write=True,
        )
        fixtures = _read_jsonl(out_dir / "route_fixtures.jsonl")
        bundles = _read_jsonl(out_dir / "candidate_bundles.jsonl")
        assert manifest["serves_truth"] is False
        assert manifest["route_fixtures"] == 4
        assert manifest["fixture_kind_counts"]["direct_reuse"] == 2
        assert manifest["fixture_kind_counts"]["mutator_reuse"] == 1
        assert manifest["fixture_kind_counts"]["edge_chain"] == 1
        assert len(bundles) == len(fixtures)
        assert all(row["serves_truth"] is False for row in fixtures + bundles)
        chain = next(row for row in fixtures if row["fixture_kind"] == "edge_chain")
        assert len(chain["expected_recipe"]["nodes"]) == 2
        assert chain["expected_recipe"]["nodes"][1]["depends_on"] == [chain["expected_recipe"]["nodes"][0]["id"]]
        mut = next(row for row in fixtures if row["fixture_kind"] == "mutator_reuse")
        assert mut["required_mutator"] == "map_sequence"
        assert "list[RawCompanyName]" in _canon(mut)
        assert (out_dir / "summary.md").exists()
        assert (out_dir / "manifest.json").exists()
    print("PASS - primitive route fixture foundry: lifecycle search cards -> direct, mutator, and edge-chain route fixtures; candidate-only.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-cards", default=str(DEFAULT_SEARCH_CARDS))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--direct-limit", type=int, default=DEFAULT_DIRECT_LIMIT)
    parser.add_argument("--mutator-limit", type=int, default=DEFAULT_MUTATOR_LIMIT)
    parser.add_argument("--chain-limit", type=int, default=DEFAULT_CHAIN_LIMIT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    manifest = write_route_fixture_artifacts(
        Path(args.search_cards),
        Path(args.out_dir),
        direct_limit=args.direct_limit,
        mutator_limit=args.mutator_limit,
        chain_limit=args.chain_limit,
        write=True,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
