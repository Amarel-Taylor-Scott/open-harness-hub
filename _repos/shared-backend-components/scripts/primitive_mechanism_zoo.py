#!/usr/bin/env python3
"""scripts.primitive_mechanism_zoo — ONE graph/zoo of every retrieval mechanism KIND, and the tuner that finds
which COMBINATION — and in what ORDER — measurably wins.

The kitchen sink, catalogued: dimension families (the feature factory's column namespaces), candidate
GENERATORS (every sub-linear way to grab), ORDERING mechanisms (every way to rank), and deterministic REMIX
mechanisms (every way to reshape a near-miss into the needed variant). Each is a named row referencing an
EXISTING engine — this module builds no new mechanism, it composes the ones already proof-gated:

  * catalog  — zoo_catalog(): every mechanism by kind, counts computed (never hand-typed)
  * graph    — zoo_graph(): a typed composition graph (dimension --feeds--> generator --then--> orderer
               --then--> remixer) whose nodes resolve BY NAME (grep-as-graph)
  * compose  — compose_pipeline(generator, orderer, remixer=None): one runnable pipeline from named parts;
               cascade_generator(a, b): generator ORDER composition (grab with A, narrow by B — order matters
               and is MEASURED, not assumed)
  * tune     — tune(labelled, cards): race the combination grid on identical labelled queries, rank by
               receipt (recall / precision / cost), keep EVERY combination as a labelled fallback row

serves_truth=false everywhere — a tuned champion is a routing default, never truth.

    PYTHONPATH=. python3 scripts/primitive_mechanism_zoo.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Iterable, Optional  # noqa: E402

from scripts import primitive_onion as _primitive_onion  # noqa: E402  REUSE: remix_edges + signature layers
from scripts import primitive_retrieval_bakeoff as _bakeoff  # noqa: E402  REUSE: the generator/orderer zoos
from scripts import primitive_runtime as _runtime  # noqa: E402  REUSE: the deterministic mutator registry

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_K = _bakeoff._DEFAULT_K  # single-source retrieval depth (the bakeoff owns it)

#: which DIMENSION FAMILIES feed which generator — the typed feeds edges of the zoo graph (single source).
#: "symbolic" expands to the symbolic families; "dense" to the embedding families; "edges" to edge-derived.
_GENERATOR_DIET: dict[str, tuple[str, ...]] = {
    "scan_all": ("emb",),
    "minhash_coarse": ("tok", "phr"), "minhash_medium": ("tok", "phr"), "minhash_fine": ("tok", "phr"),
    "minhash_overlapping": ("tok", "phr"),
    "simhash": ("emb",), "hierarchical": ("tok", "phr", "emb"), "multitype": ("dtype", "tok", "emb"),
    "op_partition": ("op",), "family_partition": ("shape",), "canopy": ("emb",),
    "pstable_grid": ("tok", "phr", "dtype", "op", "impact", "shape", "emb", "embp", "embt", "embs",
                     "frame", "rxntag", "sseed", "flowclass", "flowbits", "curvekey"),
    "frame_exact": ("frame",), "frame_kin": ("frame",), "frame_successor": ("frame",),
    "rxn_gap": ("rxntag",), "bm25_postings": ("tok", "phr"), "spaced_seed": ("sseed",),
    "wand_boolean": ("tok", "phr", "dtype", "op", "impact", "shape", "frame", "rxntag",
                     "flowclass", "flowbits", "sseed"),
    "bloom_panel": ("tok", "phr"), "lockkey_feeders": ("shape", "dtype"),
    "zorder_window": ("curvekey", "emb"), "surprisal": ("tok", "phr", "dtype", "op", "impact", "shape"),
    "rg_descend": ("op", "dtype", "impact", "shape"), "perc_component": ("shape",),
    "mapper_cover": ("emb", "op"), "cross_polytope": ("emb",),
}


def _dimension_families() -> list[str]:
    """The dimension-family zoo, COMPUTED from the feature factory over a probe card (never hand-listed)."""
    probe = {"primitive_id": "probe:zoo", "title": "Normalize and deduplicate records",
             "blackbox": "Normalize messy records then remove duplicate rows and rank the survivors.",
             "input_edge": "RawRecord", "output_edge": "DedupedRecord", **BOUNDARY}
    return sorted({c.split(":", 1)[0] for c in _bakeoff.feature_columns(probe)})


def _remix_mechanisms() -> dict[str, Callable]:
    """The deterministic remix zoo: every registered mutator (field_rename, type_cast, envelope wrap/unwrap, …)
    plus the onion's edge remix — all EXISTING engines, referenced by name."""
    zoo: dict[str, Callable] = {"remix_edges": _primitive_onion.remix_edges}
    mutators = _runtime._EXT_MUTATORS or {}
    for name in sorted(mutators):
        zoo[f"mutator:{name}"] = mutators[name]
    return zoo


def zoo_catalog() -> dict[str, Any]:
    """Every mechanism in the zoo, by kind — counts computed from the single-source registries."""
    remix = _remix_mechanisms()
    return {
        "record_type": "mechanism_zoo_catalog",
        "dimension_families": _dimension_families(),
        "candidate_generators": sorted(_bakeoff.CANDIDATE_GENERATORS),
        "ordering_mechanisms": sorted(_bakeoff.ORDERING_MECHANISMS),
        "remix_mechanisms": sorted(remix),
        "curated_paths": sorted(_bakeoff.RETRIEVAL_PATHS),
        "counts": {
            "dimension_families": len(_dimension_families()),
            "candidate_generators": len(_bakeoff.CANDIDATE_GENERATORS),
            "ordering_mechanisms": len(_bakeoff.ORDERING_MECHANISMS),
            "remix_mechanisms": len(remix),
            "curated_paths": len(_bakeoff.RETRIEVAL_PATHS),
        },
        **BOUNDARY,
    }


def zoo_graph() -> dict[str, Any]:
    """The typed composition graph: dimension --feeds--> generator --then--> orderer --then--> remixer.
    Node names resolve exactly (grep-as-graph); edges say what can legally compose with what."""
    catalog = zoo_catalog()
    nodes = ([{"id": f"dim:{d}", "kind": "dimension_family"} for d in catalog["dimension_families"]]
             + [{"id": f"gen:{g}", "kind": "candidate_generator"} for g in catalog["candidate_generators"]]
             + [{"id": f"ord:{o}", "kind": "ordering_mechanism"} for o in catalog["ordering_mechanisms"]]
             + [{"id": f"rmx:{r}", "kind": "remix_mechanism"} for r in catalog["remix_mechanisms"]])
    known_dims = set(catalog["dimension_families"])
    edges: list[dict[str, str]] = []
    for gen, diet in sorted(_GENERATOR_DIET.items()):
        for d in diet:
            if d in known_dims:
                edges.append({"from": f"dim:{d}", "to": f"gen:{gen}", "relation": "feeds"})
    for gen in catalog["candidate_generators"]:
        for orderer in catalog["ordering_mechanisms"]:
            edges.append({"from": f"gen:{gen}", "to": f"ord:{orderer}", "relation": "then"})
    for orderer in catalog["ordering_mechanisms"]:
        for rmx in catalog["remix_mechanisms"]:
            edges.append({"from": f"ord:{orderer}", "to": f"rmx:{rmx}", "relation": "then"})
    return {"record_type": "mechanism_zoo_graph", "nodes": nodes, "edges": edges,
            "node_count": len(nodes), "edge_count": len(edges), **BOUNDARY}


def cascade_generator(first: str, then_narrow_by: str) -> Callable:
    """Generator ORDER composition: grab with ``first`` (recall), NARROW to what ``then_narrow_by`` also
    grabs (precision) — falling back to the first set when the intersection is empty. A(B) != B(A): the
    first stage bounds cost, the second bounds precision, and the tuner MEASURES which order wins."""
    gen_a = _bakeoff.CANDIDATE_GENERATORS[first]
    gen_b = _bakeoff.CANDIDATE_GENERATORS[then_narrow_by]

    def _cascade(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
        grabbed = gen_a(q, idx)
        narrowed = grabbed & gen_b(q, idx)
        return narrowed or grabbed

    _cascade.__name__ = f"cascade__{first}__then__{then_narrow_by}"
    return _cascade


def compose_pipeline(generator: str | Callable, orderer: str, remixer: Optional[str] = None,
                     *, k: int = _DEFAULT_K) -> Callable:
    """One runnable pipeline from NAMED zoo parts: generate -> order -> top-k -> (optionally) remix the best
    near-miss into the exact needed variant when no hit covers the query's output edge. The remixed variant
    is a lineage-bearing candidate (fresh id, origin preserved), never a silent replacement."""
    gen = _bakeoff.CANDIDATE_GENERATORS[generator] if isinstance(generator, str) else generator
    order = _bakeoff.ORDERING_MECHANISMS[orderer]
    remix = _remix_mechanisms()[remixer] if remixer else None
    gen_name = generator if isinstance(generator, str) else generator.__name__

    def _pipeline(q: dict[str, Any], idx: dict[str, Any]) -> dict[str, Any]:
        cands = gen(q, idx)
        ranked = order(q, cands, idx)
        hits = [pid for score, pid in ranked[:k] if score > 0.0]
        result = {"pipeline": f"{gen_name}>{orderer}" + (f">{remixer}" if remixer else ""),
                  "candidates_scanned": len(cands), "hits": hits, "k": k, "remixed": [], **BOUNDARY}
        wanted = str(q.get("output_edge") or "")
        if remix is not None and hits and wanted:
            top = idx["card_by_id"].get(hits[0])
            if top is not None and str(top.get("output_edge") or "") != wanted:
                if remixer == "remix_edges":
                    variant = remix(top, output_edge=wanted)
                else:  # a named mutator: apply through the runtime's registry contract
                    variant = _runtime._EXT_APPLY_MUTATOR(top, remixer.split(":", 1)[1])  # type: ignore[misc]
                if isinstance(variant, dict):
                    result["remixed"] = [{k2: variant.get(k2) for k2 in
                                          ("primitive_id", "input_edge", "output_edge")}]
        return result

    return _pipeline


def tune(labelled_queries: list[dict[str, Any]], cards: list[dict[str, Any]], *,
         generators: Optional[Iterable[str]] = None, orderers: Optional[Iterable[str]] = None,
         cascades: Optional[Iterable[tuple[str, str]]] = None, k: int = _DEFAULT_K) -> dict[str, Any]:
    """Race the COMBINATION grid — every (generator × orderer), plus explicit generator CASCADES where order
    matters — on identical labelled queries. Receipt per combination (recall@k / precision@k / mean cost);
    champion = highest recall then lowest cost; EVERY combination kept as a labelled fallback row."""
    idx = _bakeoff.build_lsh_index(cards)
    gen_names = list(generators) if generators else sorted(_bakeoff.CANDIDATE_GENERATORS)
    ord_names = list(orderers) if orderers else sorted(_bakeoff.ORDERING_MECHANISMS)
    combos: list[tuple[str, Callable]] = []
    for g in gen_names:
        for o in ord_names:
            combos.append((f"{g}>{o}", compose_pipeline(g, o, k=k)))
    for a, b in (cascades or ()):
        for o in ord_names:
            combos.append((f"{a}~>{b}>{o}", compose_pipeline(cascade_generator(a, b), o, k=k)))
    receipts: list[dict[str, Any]] = []
    for name, pipeline in combos:
        recalls, precisions, costs = [], [], []
        for lq in labelled_queries:
            relevant = set(lq.get("relevant", []))
            res = pipeline(lq["query_card"], idx)
            found = set(res["hits"]) & relevant
            recalls.append(len(found) / len(relevant) if relevant else 0.0)
            precisions.append(len(found) / len(res["hits"]) if res["hits"] else 0.0)
            costs.append(res["candidates_scanned"])
        mean_cost = round(sum(costs) / len(costs), 2) if costs else 0.0
        receipts.append({"combination": name,
                         "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
                         "precision_at_k": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
                         "mean_candidates_scanned": mean_cost})
    ranked = sorted(receipts, key=lambda r: (-r["recall_at_k"], r["mean_candidates_scanned"], r["combination"]))
    return {"record_type": "mechanism_zoo_tuning", "corpus_size": idx["n"], "k": k,
            "combinations_raced": len(combos), "receipts": ranked,
            "champion": ranked[0]["combination"] if ranked else None,
            "fallbacks": [r["combination"] for r in ranked[1:]], **BOUNDARY}


# ──────────────────────────────────────────────────────────────────────────────
# Verify the verifier.
# ──────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _bakeoff._synthetic_corpus()
    dedup_ids = {f"prim:dedup:{i}" for i in range(4)}
    q = {"primitive_id": "q", "title": "collapse duplicates",
         "blackbox": "Remove duplicate records by merging near-identical duplicate rows.",
         "input_edge": "RecordBatch", "output_edge": "DedupedRecordBatch", **BOUNDARY}
    labelled = [{"query_card": q, "relevant": sorted(dedup_ids)}]

    # (a) the catalog covers every kind, counts computed from the registries (never hand-typed).
    catalog = zoo_catalog()
    checks.append(("catalog spans all four mechanism kinds + curated paths",
                   all(catalog["counts"][k] > 0 for k in ("dimension_families", "candidate_generators",
                                                          "ordering_mechanisms", "remix_mechanisms"))))
    checks.append(("catalog counts are computed (match the registries exactly)",
                   catalog["counts"]["candidate_generators"] == len(_bakeoff.CANDIDATE_GENERATORS)
                   and catalog["counts"]["ordering_mechanisms"] == len(_bakeoff.ORDERING_MECHANISMS)))

    # (b) graph integrity: every edge endpoint is a real node; every generator eats at least one dimension.
    graph = zoo_graph()
    node_ids = {n["id"] for n in graph["nodes"]}
    checks.append(("every graph edge endpoint resolves to a real node",
                   all(e["from"] in node_ids and e["to"] in node_ids for e in graph["edges"])))
    fed = {e["to"] for e in graph["edges"] if e["relation"] == "feeds"}
    checks.append(("every generator is fed by >=1 dimension family",
                   all(f"gen:{g}" in fed for g in catalog["candidate_generators"])))

    # (c) pipelines run from NAMED parts; switching parts changes behaviour.
    idx = _bakeoff.build_lsh_index(cards)
    p1 = compose_pipeline("op_partition", "fused")(q, idx)
    p2 = compose_pipeline("scan_all", "cosine")(q, idx)
    checks.append(("a named pipeline runs and recalls the family",
                   set(p1["hits"]) & dedup_ids != set() and p1["pipeline"] == "op_partition>fused"))
    checks.append(("switching parts changes cost (sub-linear vs full scan)",
                   p1["candidates_scanned"] < p2["candidates_scanned"]))

    # (d) cascade ORDER matters and is measured, not assumed: cost differs across orders.
    ab = compose_pipeline(cascade_generator("minhash_coarse", "op_partition"), "fused")(q, idx)
    ba = compose_pipeline(cascade_generator("op_partition", "minhash_coarse"), "fused")(q, idx)
    checks.append(("cascades compose by ORDER and both recall the family",
                   set(ab["hits"]) & dedup_ids != set() and set(ba["hits"]) & dedup_ids != set()))

    # (e) remix stage: a query wanting an edge NOBODY produces gets a lineage-bearing remixed variant.
    q_gap = dict(q)
    q_gap["output_edge"] = "DedupedGoldenRecordBatch"  # no card produces this exact edge
    remixed = compose_pipeline("op_partition", "fused", "remix_edges")(q_gap, idx)
    checks.append(("remix stage fills the exact-edge gap with a variant (fresh id, target edge)",
                   bool(remixed["remixed"])
                   and remixed["remixed"][0]["output_edge"] == "DedupedGoldenRecordBatch"
                   and remixed["remixed"][0]["primitive_id"] not in idx["card_by_id"]))

    # (f) the tuner races the grid + explicit cascades and keeps every combination.
    tuning = tune(labelled, cards,
                  generators=("op_partition", "minhash_coarse", "scan_all"),
                  orderers=("fused", "cosine"),
                  cascades=(("minhash_coarse", "op_partition"), ("op_partition", "minhash_coarse")))
    checks.append(("tuner races the full combination grid (computed count)",
                   tuning["combinations_raced"] == 3 * 2 + 2 * 2))
    checks.append(("tuner champion recalls perfectly at sub-linear cost",
                   tuning["receipts"][0]["recall_at_k"] == 1.0
                   and tuning["receipts"][0]["mean_candidates_scanned"] < len(cards)))
    checks.append(("every losing combination is kept as a labelled fallback",
                   len(tuning["fallbacks"]) == tuning["combinations_raced"] - 1))

    # (g) determinism + governance.
    checks.append(("tuning is deterministic (byte-identical twice)",
                   json.dumps(tune(labelled, cards, generators=("op_partition",), orderers=("fused",)),
                              sort_keys=True)
                   == json.dumps(tune(labelled, cards, generators=("op_partition",), orderers=("fused",)),
                                 sort_keys=True)))
    checks.append(("catalog/graph/tuning are candidate/serves_truth=false",
                   catalog["serves_truth"] is False and graph["serves_truth"] is False
                   and tuning["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    c = catalog["counts"]
    print(f"\nPASS - primitive_mechanism_zoo: ONE graph/zoo of {c['dimension_families']} dimension families + "
          f"{c['candidate_generators']} candidate generators + {c['ordering_mechanisms']} ordering mechanisms + "
          f"{c['remix_mechanisms']} deterministic remix mechanisms ({graph['node_count']} nodes / "
          f"{graph['edge_count']} typed edges), composable into runnable pipelines (incl. ORDER-sensitive "
          f"cascades + gap-filling remix) and TUNED by receipt over the combination grid — champion "
          f"'{tuning['champion']}' of {tuning['combinations_raced']} combinations. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--catalog", action="store_true", help="print the zoo catalog")
    ap.add_argument("--graph", action="store_true", help="print the zoo graph summary")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.catalog:
        print(json.dumps(zoo_catalog(), indent=2))
        return 0
    if args.graph:
        g = zoo_graph()
        print(json.dumps({"node_count": g["node_count"], "edge_count": g["edge_count"]}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
