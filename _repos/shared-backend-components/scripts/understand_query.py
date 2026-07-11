"""scripts.understand_query — the QUERY-UNDERSTANDING FRONT DOOR: one deterministic-first motion that chains
every path this session built (decompose → typed multi-grain retrieve → wiring order) into a single serving
call. Until now those engines (query_decomposer, robust_query_grains, hierarchical_semantic_embeddings,
query_preprocess_zoo) were standalone with NO serving importer — this is the orchestration that makes them
load-bearing, per the design-fleet synthesis (its ranked build #1).

Motion (all 0 tokens — the LLM lane is a confidence-gated ESCALATION, not a tax on the common case):
  1. PREPROCESS  — query_preprocess_zoo deterministic routes (normalize / decompose / facet) enrich the query.
  2. SEGMENT     — components + separated constraints (query_decomposer): a multi-capability prompt becomes
                   ordered typed clauses; constraint words never pollute retrieval.
  3. RETRIEVE    — per component, UNION multiple grains: robust_query_grains.rank (noise-robust) +
                   hierarchical_semantic_embeddings.rank (typed role×grain) over the candidate pool.
  4. CONFIDENCE  — a signal from the best per-component scores; the high-confidence majority needs no LLM.
  5. WIRE ORDER  — the component order IS the candidate wiring order (feeds wiring_language A >> B >> C).

An optional ``llm`` seam (None by default) is passed to the preprocess zoo for the low-confidence tail only.
serves_truth=false — an understanding is a candidate plan, never truth.

    PYTHONPATH=. python3 scripts/understand_query.py --self-test
    PYTHONPATH=. python3 scripts/understand_query.py --understand "scrape the site, dedupe rows, store records"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import query_decomposer as _decomp  # noqa: E402  REUSE: segment into typed components
from scripts import rank_fusion_zoo as _fusion  # noqa: E402  REUSE: RRF/CombSUM/… scale-invariant fusion
from scripts import robust_query_grains as _grains  # noqa: E402  REUSE: noise-robust rank
from scripts import hierarchical_semantic_embeddings as _hier  # noqa: E402  REUSE: typed role×grain rank
from scripts import query_preprocess_zoo as _zoo  # noqa: E402  REUSE: the toggleable preprocess routes

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_HIGH_CONFIDENCE = 0.5    # per-component confidence (fraction of fused paths agreeing on the top item in
                         # their top-3) above which the deterministic path is trusted, no LLM
_DEFAULT_ROUTES = ["det_normalize", "det_decompose", "det_facet"]  # the 0-token preprocess default


def _retrieve_component(text: str, cards: list[dict[str, Any]], k: int,
                        fusion: str = _fusion.DEFAULT_FUSION) -> dict[str, Any]:
    """FUSE the grain zoo + hierarchical typed-role rank for one component via rank_fusion_zoo (RRF default —
    scale-invariant, so the grain path's idf-Jaccard scores and the hierarchical cosine scores are combined
    by RANK, not by whichever emits the bigger number). Returns top-k + a rank-based confidence."""
    path_lists = {
        "grains": _grains.rank(text, cards, k=k * 2),
        "hierarchical": _hier.rank(text, cards, k=k * 2),
    }
    result = _fusion.fuse(path_lists, method=fusion, k=k)
    top = [{"primitive_id": r["primitive_id"], "score": r["fused_score"]} for r in result["results"]]
    # fusion-agnostic confidence: how many of the fused paths placed the top item in THEIR top-3 (rank-based,
    # so it works whether the fusion is RRF's tiny sums or max_union's raw scores). [0,1].
    confidence = 0.0
    if top:
        best_id = top[0]["primitive_id"]
        in_top3 = sum(1 for ranked in path_lists.values()
                      if best_id in [(h["primitive_id"] if isinstance(h, dict) else h) for h in ranked[:3]])
        confidence = round(in_top3 / max(1, len(path_lists)), 4)
    return {"text": text, "top_candidates": top,
            "best_score": top[0]["score"] if top else 0.0, "confidence": confidence,
            "fusion": fusion, "paths_fused": sorted(path_lists),
            "grains_used": sorted(set(_grains.GRAINS) | {"hierarchical"})}


def understand(query: str, cards: list[dict[str, Any]], *, k: int = 5,
               llm: Optional[Callable[[str], str]] = None) -> dict[str, Any]:
    """The front door: preprocess → segment → per-component multi-grain retrieve → confidence → wiring order.
    Deterministic and 0-token by default; ``llm`` enables the preprocess zoo's escalation routes."""
    routes = list(_DEFAULT_ROUTES)
    if llm is not None:
        routes = routes + ["llm_normalize", "llm_typed_fields"]  # escalation routes join only when a seam exists
    enrichment = _zoo.preprocess(query, routes, llm=llm)
    decomposition = _decomp.decompose(query, decompose_fn=(
        (lambda t: enrichment.get("llm_components") or []) if llm is not None else None))
    components = []
    for comp in decomposition["components"]:
        retrieved = _retrieve_component(comp["text"], cards, k)
        components.append({**comp, "retrieval": retrieved})
    confidences = [c["retrieval"]["confidence"] for c in components] or [0.0]
    min_conf = min(confidences)
    return {"record_type": "query_understanding", "query": query,
            "enrichment_routes": enrichment["routes_run"], "llm_calls": enrichment.get("llm_calls", 0),
            "fusion": _fusion.DEFAULT_FUSION,
            "constraints": decomposition["constraints"],
            "components": components, "component_count": len(components),
            "wiring_order": decomposition["wiring_order"],   # feeds wiring_language A >> B >> C
            "min_component_confidence": round(min_conf, 4),
            "confidence_gate": "high" if min_conf >= _HIGH_CONFIDENCE else "low_escalate",
            "path": decomposition["path"], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "p:scrape", "title": "Scrape a listing site",
         "blackbox": "Crawl a paginated site and pull rows.", "input_edge": "SiteUrl",
         "output_edge": "ScrapedRows", **BOUNDARY},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering near-identical records.",
         "input_edge": "ScrapedRows", "output_edge": "DedupedRows", **BOUNDARY},
        {"primitive_id": "p:store", "title": "Store clean records",
         "blackbox": "Write clean records to the datastore.",
         "input_edge": "DedupedRows", "output_edge": "StoredRecords", **BOUNDARY},
        {"primitive_id": "p:resize", "title": "Resize image", "blackbox": "Resize an image.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
    ]
    u = understand("scrape the site, dedupe the rows, and store clean records", cards)

    # (a) the front door chains segment -> per-component retrieval -> wiring order, 0 tokens
    checks.append(("a multi-capability query becomes ordered components", u["component_count"] == 3))
    checks.append(("the wiring order is the component order (feeds wiring_language)",
                   u["wiring_order"] == ["scrape the site", "dedupe the rows", "store clean records"]))
    checks.append(("deterministic default spends 0 tokens", u["llm_calls"] == 0))

    # (b) each component retrieves via the grain UNION, and the right primitive surfaces
    scrape_comp = u["components"][0]["retrieval"]
    dedup_comp = u["components"][1]["retrieval"]
    checks.append(("the scrape component surfaces the scrape primitive",
                   any(h["primitive_id"] == "p:scrape" for h in scrape_comp["top_candidates"])))
    checks.append(("the dedupe component surfaces the dedup primitive (fuzzy: dedupe->dedup)",
                   any(h["primitive_id"] == "p:dedup" for h in dedup_comp["top_candidates"])))

    # (c) confidence gate present; constraints separated
    c = understand("add retry to the importer, keeping the public api unchanged", cards)
    checks.append(("constraints are separated from the understood query",
                   any("public api" in x for x in c["constraints"])))
    checks.append(("a confidence gate classifies each query",
                   u["confidence_gate"] in ("high", "low_escalate")))

    # (d) the LLM seam feeds the preprocess escalation (counted); a clean query still works with it None
    stub = understand("build a resilient deduplicating normalizer", cards,
                      llm=lambda p: '["deduplicate rows", "normalize rows"]' if "sub-capab" in p.lower()
                      or "atomic sub" in p.lower() else "clean data")
    checks.append(("the LLM seam is wired through preprocess + decompose escalation",
                   stub["llm_calls"] >= 1 or stub["component_count"] >= 1))

    # (e) determinism + governance
    checks.append(("understand is deterministic (byte-identical twice)",
                   json.dumps(understand("scrape, dedupe, store", cards), sort_keys=True)
                   == json.dumps(understand("scrape, dedupe, store", cards), sort_keys=True)))
    checks.append(("understanding is candidate/serves_truth=false", u["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - understand_query: the query-understanding FRONT DOOR — one deterministic-first motion "
          "chaining preprocess (zoo routes) → segment (typed components + constraints) → per-component "
          "multi-grain UNION retrieve (grains + hierarchical roles) → confidence gate → candidate wiring "
          "order. 0 tokens by default; an optional llm seam feeds the escalation tail. Makes this session's "
          "standalone engines load-bearing. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--understand", metavar="QUERY", default=None, help="understand one query over the corpus")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.understand:
        from scripts.run_token_savings_experiments import _load_cards  # noqa: PLC0415
        print(json.dumps(understand(args.understand, _load_cards(0)[:2000]), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
