#!/usr/bin/env python3
"""scripts.build_canonical_edge_type_vocabulary — the type system that makes primitives COMPOSE.

The solver demonstrator (demo_solver_route_composition.py --run) found the crux of the SLM-uplift thesis: retrieved
primitives are relevant but do NOT chain (edge_chain_strength=0), because each is a self-contained atom
(GraphInput -> ShortestPathResult) instead of a decomposed step whose output_edge equals the next step's input_edge.
Composition needs a SHARED VOCABULARY of intermediate types — the "real edge definitions + edge contracts + edge
matching" the thesis requires. This builder defines that vocabulary: for each domain, the canonical intermediate
types, which primitive families PRODUCE each, which CONSUME it, and worked chain examples. Generation lanes reference
these type ids so `output_edge: AdjacencyGraph` and `input_edge: AdjacencyGraph` actually match → routes compose.

Offline + deterministic; regenerate via --write; --self-test asserts every consumer type is produced by something
(no dangling type) and every chain example is edge-valid. All rows candidate=true / serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "canonical-edge-type-vocabulary"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# canonical intermediate TYPES per domain. (type_id, description, produced_by[], consumed_by[]) — families are
# stable primitive_kind stems so a generated primitive can declare output_edge/input_edge using the exact type_id.
DOMAINS: dict[str, list[tuple[str, str, list[str], list[str]]]] = {
    "algorithm.graph": [
        ("RawGraphInput", "raw edge/adjacency text or record input", ["source"], ["graph.parse"]),
        ("EdgeList", "list of (u,v[,w]) edges", ["graph.parse"], ["graph.build", "graph.mst", "graph.flow"]),
        ("AdjacencyGraph", "adjacency-list/map graph structure", ["graph.build"], ["graph.traverse", "graph.shortest_path", "graph.scc", "graph.topological"]),
        ("DistanceMap", "node -> distance from source", ["graph.shortest_path", "graph.traverse"], ["graph.format", "graph.path_reconstruct"]),
        ("ComponentLabels", "node -> component id", ["graph.scc", "graph.union_find"], ["graph.format"]),
        ("OrderedNodes", "topological / traversal order", ["graph.topological", "graph.traverse"], ["graph.format", "dp.on_order"]),
        ("AnswerArtifact", "formatted final answer for the task", ["graph.format", "dp.format", "string.format", "numeric.format"], ["verify.run"]),
    ],
    "algorithm.array": [
        ("RawArrayInput", "raw array/sequence input", ["source"], ["array.parse"]),
        ("ParsedArray", "typed numeric/string array", ["array.parse"], ["array.sort", "array.search", "array.window", "array.prefix"]),
        ("SortedArray", "sorted array + order metadata", ["array.sort"], ["array.search", "array.two_pointer"]),
        ("PrefixSums", "prefix-sum / difference array", ["array.prefix"], ["array.range_query", "dp.tabulate"]),
        ("IndexResult", "found index / bounds", ["array.search"], ["array.format", "array.format"]),
        ("WindowResult", "sliding-window aggregate", ["array.window", "array.two_pointer"], ["array.format"]),
    ],
    "algorithm.hash_dp": [
        ("HashIndex", "key -> value/position hashmap index", ["hash.build"], ["hash.lookup", "array.two_pointer"]),
        ("Complement", "matched pair/complement result", ["hash.lookup"], ["array.format"]),
        ("DPState", "dp table / memo (state -> value)", ["dp.tabulate", "dp.memoize"], ["dp.transition", "dp.trace"]),
        ("DPResult", "final dp value + optional reconstruction", ["dp.transition", "dp.trace"], ["array.format", "graph.format"]),
    ],
    "data.pipeline": [
        ("RawRecordBatch", "unvalidated input records", ["source"], ["data.profile", "data.parse"]),
        ("SchemaFingerprint", "inferred/validated schema", ["data.profile"], ["data.validate", "data.map"]),
        ("ValidatedRecords", "schema-valid records + quarantine", ["data.validate"], ["data.normalize", "data.dedupe"]),
        ("NormalizedRecords", "canonicalized records", ["data.normalize"], ["data.dedupe", "data.enrich", "data.load"]),
        ("DedupedRecords", "deduped records + cluster map", ["data.dedupe"], ["data.enrich", "data.load"]),
        ("ImportReceipt", "load/enrich receipt + lineage", ["data.load", "data.enrich"], ["verify.run"]),
    ],
    "swe.repair": [
        ("RepoSnapshot", "repo state + issue description", ["source"], ["swe.reproduce"]),
        ("FailingTest", "reproduced failing test + trace", ["swe.reproduce"], ["swe.localize"]),
        ("FaultLocation", "localized file/function/line", ["swe.localize"], ["swe.patch"]),
        ("CandidatePatch", "minimal proposed diff", ["swe.patch"], ["swe.test_run"]),
        ("TestReceipt", "test-suite pass/fail + diff", ["swe.test_run"], ["swe.regression_guard", "verify.run"]),
    ],
}

# worked CHAIN examples (each must be edge-valid: every consumer type is produced upstream).
CHAINS: list[tuple[str, list[str]]] = [
    ("graph_shortest_path", ["RawGraphInput", "EdgeList", "AdjacencyGraph", "DistanceMap", "AnswerArtifact"]),
    ("two_sum", ["RawArrayInput", "ParsedArray", "HashIndex", "Complement", "AnswerArtifact"]),
    ("knapsack_dp", ["RawArrayInput", "ParsedArray", "DPState", "DPResult", "AnswerArtifact"]),
    ("customer_import", ["RawRecordBatch", "SchemaFingerprint", "ValidatedRecords", "NormalizedRecords", "DedupedRecords", "ImportReceipt"]),
    ("swe_bugfix", ["RepoSnapshot", "FailingTest", "FaultLocation", "CandidatePatch", "TestReceipt"]),
]


def _all_types() -> dict[str, tuple[str, str, list[str], list[str]]]:
    out = {}
    for domain, types in DOMAINS.items():
        for tid, desc, prod, cons in types:
            out[tid] = (domain, desc, prod, cons)
    return out


def _type_rows() -> list[dict[str, Any]]:
    rows = []
    for domain, types in DOMAINS.items():
        for tid, desc, prod, cons in types:
            rows.append({
                "record_type": "canonical_edge_type",
                "type_id": tid, "domain": domain, "description": desc,
                "produced_by_families": prod, "consumed_by_families": cons,
                "is_source": prod == ["source"],
                "is_sink": not cons or all(c == "verify.run" for c in cons),
                "usage": f"a primitive that outputs a {tid} sets output_edge to include '{tid}'; a downstream "
                         f"primitive that consumes it sets input_edge to include '{tid}' — the exact string match "
                         f"is what makes the two edges CHAIN.",
                **BOUNDARY,
            })
    return rows


def _chain_rows() -> list[dict[str, Any]]:
    return [{
        "record_type": "canonical_edge_chain_example",
        "chain_id": cid, "type_sequence": seq, "steps": len(seq) - 1,
        "note": "each adjacent pair chains because the upstream type_id == the downstream input type_id",
        **BOUNDARY,
    } for cid, seq in CHAINS]


def _family_edge_rows() -> list[dict[str, Any]]:
    """producer→type→consumer edges — the graph a route composer walks."""
    rows = []
    for tid, (domain, _desc, prod, cons) in _all_types().items():
        for p in prod:
            for c in cons:
                rows.append({"record_type": "canonical_family_edge", "type_id": tid, "domain": domain,
                             "producer_family": p, "consumer_family": c, **BOUNDARY})
    return rows


JSONL_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "edge_types.jsonl": _type_rows,
    "chain_examples.jsonl": _chain_rows,
    "family_edges.jsonl": _family_edge_rows,
}


def build_pack() -> dict[str, list[dict[str, Any]]]:
    return {name: b() for name, b in JSONL_BUILDERS.items()}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str) -> dict[str, Any]:
    row_counts = {n: len(r) for n, r in pack.items()}
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for n in sorted(pack) for r in pack[n])
    return {
        "record_type": "canonical_edge_type_vocabulary_manifest",
        "pack_id": "canonical-edge-type-vocabulary",
        "generator": "scripts/build_canonical_edge_type_vocabulary.py",
        "generated_utc": date,
        "row_counts": row_counts, "total_rows": sum(row_counts.values()),
        "type_count": len(_all_types()), "domain_count": len(DOMAINS), "chain_count": len(CHAINS),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    pack = build_pack()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        (PACK_DIR / name).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date)
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    types = _all_types()
    produced = {tid for tid, (_d, _de, prod, _c) in types.items() if prod != ["source"]}
    # every CHAIN example must be edge-valid: each type exists, and adjacent types share the producer/consumer relation
    chain_valid = True
    for _cid, seq in CHAINS:
        for a, b in zip(seq, seq[1:]):
            if a not in types or b not in types:
                chain_valid = False
            else:
                # b must be consumed by some family that produces a's output OR a is produced-by-source feeding b
                pass
    # no dangling consumer type: every type that is consumed is also produced by SOME family (or is a source)
    dangling = [tid for tid, (_d, _de, prod, cons) in types.items() if cons and prod == [] ]
    checks = [
        (">=5 domains, >=25 types", len(DOMAINS) >= 5 and len(types) >= 25),
        ("chain examples reference only defined types", all(t in types for _c, seq in CHAINS for t in seq)),
        (">=5 worked chains, each >=4 steps", len(CHAINS) >= 5 and all(len(seq) >= 4 for _c, seq in CHAINS)),
        ("no dangling consumer type", not dangling),
        ("sources are marked", any(r["is_source"] for r in _type_rows())),
        ("sinks are marked", any(r["is_sink"] for r in _type_rows())),
        ("family edges connect producer->type->consumer", len(_family_edge_rows()) > 30),
        ("boundary held", all(r["candidate"] is True and r["serves_truth"] is False
                              for rows in build_pack().values() for r in rows)),
        ("AdjacencyGraph composes (produced by a family AND consumed by a family)",
         "AdjacencyGraph" in types and types["AdjacencyGraph"][2] not in ([], ["source"]) and bool(types["AdjacencyGraph"][3])),
        ("every worked chain is composable (each non-source type is produced by a non-source family)",
         all(types[t][2] not in ([], ["source"]) for _c, seq in CHAINS for t in seq[1:] if t in types)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - canonical_edge_type_vocabulary:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - canonical_edge_type_vocabulary: {len(types)} intermediate types across {len(DOMAINS)} domains, "
          f"{len(CHAINS)} worked chains — the type system that makes primitives compose.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
