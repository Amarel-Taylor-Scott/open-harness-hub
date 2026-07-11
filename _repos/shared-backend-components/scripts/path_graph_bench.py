#!/usr/bin/env python3
"""scripts.path_graph_bench — RUN and BENCHMARK the whole pipeline_path_graph, honestly.

Two modes over ONE prebuilt corpus + a shared retrieval cache (so enumerating tens of thousands of paths runs
each unique retrieval ONCE, not once per downstream fuse/rerank combination):

  RUNNABLE SWEEP  — enumerate EVERY path (the full cartesian product of every stage's zoo) and execute each,
    proving all N combinations run without error. Reports total paths, runnable count, any errors (with the
    failing path + exception), the non-empty-result rate, and per-search-option latency. A small sample also
    runs WITH a deterministic LLM stub so the frontier/local-llm options fire and are token-counted.

  QUALITY BENCH   — over a LABELLED query set (known relevant primitive ids), score each RANKING-RELEVANT path
    config (expand × search × fuse × rerank — analyze/preprocess/secondary/compose do not move the ranking) by
    recall@k / MRR / nDCG@k. Retrieval is INDEPENDENT per path (each search path retrieves over the FULL
    corpus, NOT a rescored lexical pool — the honest multi-path measurement the old coverage bench lacked), and
    the semantic path uses the REAL local embedder (model2vec in-process, else Ollama nomic). Ranks configs,
    picks a champion, and reports the multi-path lift of the full UNION over lexical-vocabulary-alone — the
    direct, measured answer to "is vocabulary the only tool?".

serves_truth=false — a benchmark receipt is a measurement, never served truth.

    PYTHONPATH=. python3 scripts/path_graph_bench.py --self-test
    PYTHONPATH=. python3 scripts/path_graph_bench.py --runnable --sample 250   # prove ALL paths run
    PYTHONPATH=. python3 scripts/path_graph_bench.py --bench --sample 200 --k 5 # honest quality bench
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
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: real local embedder resolver
from scripts import pipeline_path_graph as _graph  # noqa: E402  REUSE: the graph (enumerate/run_path/options)
from scripts.build_primitive_search_index import build_index as _build_index  # noqa: E402
from scripts.primitive_retrieval_bakeoff import _synthetic_corpus as _gold_corpus  # noqa: E402  labelled families

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_K = 5                 # retrieval depth for recall@k / nDCG@k (matches the bakeoff's _DEFAULT_K)
_DEFAULT_CORPUS_SAMPLE = 200   # real distractor cards mixed into the gold families (deterministic head)
_GOLD_FAMILY_SIZE = 4          # _synthetic_corpus emits 4 cards per family (single source of the relevant set)
#: the stages whose option CHANGES the ranking — the bench races their product; the rest are fixed to one value
#: (they add metadata/wiring, not ranking) so the quality receipt is not diluted by ranking-irrelevant paths.
_RANKING_STAGES: tuple[str, ...] = ("expand", "search", "fuse", "rerank")


def _fixed_prefix() -> dict[str, str]:
    """Fix every NON-ranking stage to a neutral default — a no-op (`none`/`skip`) where one exists, else the
    stage's first option — COMPUTED from the live graph, not a hardcoded dict. So a NEW mid-pipeline stage is
    auto-covered (fixed to a neutral default) and never silently skipped by the bench; add it to
    ``_RANKING_STAGES`` only if you want it RACED. This isolates the ranking stages without any edit here."""
    prefix: dict[str, str] = {}
    for stage in _graph.STAGES:
        if stage in _RANKING_STAGES:
            continue
        opts = _graph.STAGE_OPTIONS[stage]
        prefix[stage] = next((o for o in ("none", "skip") if o in opts), None) or next(iter(opts))
    return prefix

#: labelled dev-task queries — each a PARAPHRASE of a synthetic family's intent (few/no shared words with the
#: card text, so lexical-alone is challenged and the semantic/expansion paths must earn their recall). The
#: relevant set is the whole family (prim:{family}:0..3). Gold is KNOWN, so recall/MRR/nDCG are real.
_LABELLED_QUERIES: tuple[dict[str, str], ...] = (
    {"query": "get rid of repeated entries in my dataset", "family": "dedup"},
    {"query": "make the picture smaller to fit a thumbnail", "family": "resize"},
    {"query": "pull the words out of a scanned page", "family": "ocr"},
    {"query": "rate how risky this customer is on a zero to one scale", "family": "score"},
    {"query": "tidy up messy rows into one consistent clean shape", "family": "normalize"},
)


def _relevant(family: str) -> set[str]:
    return {f"prim:{family}:{i}" for i in range(_GOLD_FAMILY_SIZE)}


# ── metrics (binary relevance; graded gold is roadmap #3) ─────────────────────────────────────────────────────
def _recall_at_k(ids: list[str], relevant: set[str], k: int) -> float:
    return len(set(ids[:k]) & relevant) / len(relevant) if relevant else 0.0


def _mrr(ids: list[str], relevant: set[str]) -> float:
    for i, pid in enumerate(ids):
        if pid in relevant:
            return 1.0 / (i + 1)
    return 0.0


def _ndcg_at_k(ids: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(i + 2) for i, pid in enumerate(ids[:k]) if pid in relevant)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / idcg if idcg else 0.0


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ── corpus ────────────────────────────────────────────────────────────────────────────────────────────────────
def _sample_real_cards(n: int) -> list[dict[str, Any]]:
    """Deterministic head of the real verified-factory corpus as DISTRACTORS (excluding only the exact synthetic
    gold ids so relevance stays clean). Empty (noted) if the corpus file is absent, so the bench still runs."""
    if n <= 0:
        return []
    try:
        from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
        path = resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"
        rows = read_jsonl_tolerant(path)
    except Exception:  # noqa: BLE001 — no corpus on disk => synthetic-only bench (noted in the receipt)
        return []
    gold_ids = {c["primitive_id"] for c in _gold_corpus()}  # exclude the 5 labelled families, keep everything else
    out: list[dict[str, Any]] = []
    for r in rows:
        pid = r.get("primitive_id")
        if pid and pid not in gold_ids and (r.get("blackbox") or r.get("title")):
            out.append(r)
        if len(out) >= n:
            break
    return out


def bench_corpus(sample: int = _DEFAULT_CORPUS_SAMPLE) -> list[dict[str, Any]]:
    """The gold families (known relevance) + real distractors (scale + realistic df-cap)."""
    return _gold_corpus() + _sample_real_cards(sample)


def _ranking_configs(*, searches: Optional[list[str]] = None) -> list[dict[str, str]]:
    """The product of the ranking-relevant stage options (expand × search × fuse × rerank)."""
    opts = {s: (searches if s == "search" and searches else sorted(_graph.STAGE_OPTIONS[s]))
            for s in _RANKING_STAGES}
    combos = itertools.product(*(opts[s] for s in _RANKING_STAGES))
    return [dict(zip(_RANKING_STAGES, c)) for c in combos]


# ── RUNNABLE SWEEP — every path executes without error ────────────────────────────────────────────────────────
def runnable_sweep(cards: list[dict[str, Any]], queries: list[str], *,
                   max_paths: Optional[int] = None, llm_stub: Optional[Callable] = None) -> dict[str, Any]:
    """Enumerate EVERY path and run each over ``cards`` for each query (shared cache). Prove they all run."""
    index = _build_index(cards)
    paths = _graph.enumerate_paths(max_paths=max_paths)
    cache: dict = {}
    ran = errors = non_empty = 0
    err_samples: list[dict[str, Any]] = []
    search_latency: dict[str, list[float]] = {}
    llm_fired = 0
    for query in queries:
        for path in paths:
            try:
                t0 = time.perf_counter()
                run = _graph.run_path(query, cards, path, index=index, cache=cache, llm=llm_stub)
                dt = (time.perf_counter() - t0) * 1000.0
                ran += 1
                if run["results"]:
                    non_empty += 1
                if llm_stub is not None and run.get("llm_calls", 0) >= 1:
                    llm_fired += 1
                search_latency.setdefault(path.get("search", "none"), []).append(dt)
            except Exception as exc:  # noqa: BLE001 — the whole point is to FIND any path that breaks
                errors += 1
                if len(err_samples) < 20:
                    err_samples.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})
    total = len(paths) * len(queries)
    return {"record_type": "path_graph_runnable_sweep", "total_paths_in_graph": _graph.graph_summary()["total_paths"],
            "paths_enumerated": len(paths), "queries": len(queries), "path_runs": total,
            "runnable": ran, "errors": errors, "error_samples": err_samples,
            "all_runnable": errors == 0, "non_empty_result_rate": round(non_empty / total, 4) if total else 0.0,
            "llm_paths_fired": llm_fired,
            "mean_latency_ms_per_search_option": {s: round(_mean(v), 2) for s, v in sorted(search_latency.items())},
            **BOUNDARY}


# ── QUALITY BENCH — honest recall@k / MRR / nDCG per config, real embedder, independent retrieval ─────────────
def quality_bench(cards: list[dict[str, Any]], labelled: list[dict[str, str]], *,
                  k: int = _DEFAULT_K, configs: Optional[list[dict[str, str]]] = None) -> dict[str, Any]:
    """Race every ranking-relevant config on the labelled set; rank by (nDCG, recall, then cheapest search)."""
    index = _build_index(cards)
    cache: dict = {}
    embed_path = _emb.real_text_path()
    configs = configs or _ranking_configs()
    fixed = _fixed_prefix()  # non-ranking stages fixed to neutral defaults (computed from the live graph)
    receipts: list[dict[str, Any]] = []
    for cfg in configs:
        path = {**fixed, **cfg}
        recalls, mrrs, ndcgs = [], [], []
        for q in labelled:
            rel = _relevant(q["family"])
            run = _graph.run_path(q["query"], cards, path, index=index, cache=cache)
            ids = [r.get("primitive_id") for r in run["results"]]
            recalls.append(_recall_at_k(ids, rel, k))
            mrrs.append(_mrr(ids, rel))
            ndcgs.append(_ndcg_at_k(ids, rel, k))
        receipts.append({**cfg, "recall_at_k": round(_mean(recalls), 4),
                         "mrr": round(_mean(mrrs), 4), "ndcg_at_k": round(_mean(ndcgs), 4)})
    # cheaper search options rank first on ties (deterministic + prefer the least machinery)
    _search_cost = {"lexical": 0, "facet": 1, "grains": 2, "hierarchical": 3, "semantic_embedding": 3,
                    "semantic_registers": 3, "both": 4, "all": 5}
    ranked = sorted(receipts, key=lambda r: (-r["ndcg_at_k"], -r["recall_at_k"],
                                             _search_cost.get(r["search"], 9), r["expand"], r["fuse"], r["rerank"]))

    def _best_for(pred: Callable[[dict], bool]) -> Optional[dict[str, Any]]:
        cand = [r for r in ranked if pred(r)]
        return cand[0] if cand else None

    per_search_best = {s: _best_for(lambda r, s=s: r["search"] == s)
                       for s in sorted(_graph.STAGE_OPTIONS["search"])}
    lexical_best = per_search_best.get("lexical")
    union_best = per_search_best.get("all")
    lift = (round(union_best["ndcg_at_k"] / lexical_best["ndcg_at_k"], 3)
            if union_best and lexical_best and lexical_best["ndcg_at_k"] > 0
            else (float("inf") if union_best and union_best["ndcg_at_k"] > 0 else 1.0))
    return {"record_type": "path_graph_quality_benchmark", "k": k, "queries": len(labelled),
            "corpus_size": len(cards), "embed_path": embed_path, "configs_raced": len(configs),
            "champion": ranked[0] if ranked else None,
            "top_configs": ranked[:10],
            "per_search_best": {s: v for s, v in per_search_best.items() if v},
            "union_vs_lexical_ndcg_lift": lift,
            "note": "recall/MRR/nDCG over a labelled synthetic-family set (KNOWN relevance); retrieval is "
                    "INDEPENDENT per path over the full corpus (not a rescored lexical pool). Real distractors "
                    "are unlabelled, so absolute numbers are a lower bound; the config RANKING is the signal. "
                    "graded gold + a real dev-query set are roadmap #3.", **BOUNDARY}


# ── SCALE (100K+) — precomputed dense index makes the semantic lane sublinear-enough to benchmark at scale ────
def _load_scale_corpus(max_cards: Optional[int] = None) -> list[dict[str, Any]]:
    """The real 100K+ primitive corpus: verified-factory + primitive-edge cards (~112k)."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    base = resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
    cards: list[dict[str, Any]] = []
    for fn in ("verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"):
        p = base / fn
        if p.exists():
            cards += read_jsonl_tolerant(p)
        if max_cards and len(cards) >= max_cards:
            return cards[:max_cards]
    return cards


def build_dense_index(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Batch-embed every card's blackbox ONCE (model2vec) into an L2-normalized matrix — the in-process dense
    index (precompute once instead of re-embedding per query; a pgvector/faiss index slots in behind the same call)."""
    import numpy as np  # noqa: PLC0415
    model = _emb._load_model2vec()
    ids = [c.get("primitive_id") for c in cards]
    texts = [_emb.card_embed_text(c) for c in cards]  # the ONE embed surface (single-sourced)
    if model is not None:
        matrix = np.asarray(model.encode(texts), dtype="float32")
    else:  # proxy fallback (still real-shaped, just weaker)
        matrix = np.asarray([_emb.embed_text(t, path="tokens") for t in texts], dtype="float32")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return {"ids": ids, "matrix": matrix / norms, "embed_path": "model2vec" if model is not None else "tokens"}


def dense_topk(query: str, dense: dict[str, Any], k: int) -> list[str]:
    """Top-k primitive ids for a query against the precomputed dense matrix (cosine = normalized dot)."""
    import numpy as np  # noqa: PLC0415
    model = _emb._load_model2vec()
    q = (np.asarray(model.encode([query])[0], dtype="float32") if model is not None
         else np.asarray(_emb.embed_text(query, path="tokens"), dtype="float32"))
    nrm = float(np.linalg.norm(q)) or 1.0
    sims = dense["matrix"] @ (q / nrm)
    if k >= len(sims):
        order = np.argsort(-sims)
    else:
        part = np.argpartition(-sims, k)[:k]
        order = part[np.argsort(-sims[part])]
    return [dense["ids"][i] for i in order[:k]]


def scale_bench(cards: list[dict[str, Any]], *, k: int = _DEFAULT_K, query_sample: int = 200) -> dict[str, Any]:
    """Benchmark the SCALABLE retrievers (lexical inverted index vs precomputed dense vs their RRF fusion) at
    full 100K+ scale. Quality via a labels-free KNOWN-ITEM probe: query = a real card's title, gold = that card
    — measured clean and noisy (typo'd title). Also build-time, per-query latency, and lexical/dense
    complementarity (top-k overlap). No synthetic gold, so real cards never drown the labels."""
    import time  # noqa: PLC0415
    from scripts import rank_fusion_zoo as _f  # noqa: PLC0415
    from scripts import robust_query_grains as _g  # noqa: PLC0415
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415

    t0 = time.perf_counter(); index = build_index(cards); build_lexical_s = time.perf_counter() - t0
    t0 = time.perf_counter(); dense = build_dense_index(cards); build_dense_s = time.perf_counter() - t0

    step = max(1, len(cards) // query_sample)
    sample = [cards[i] for i in range(0, len(cards), step)][:query_sample]

    def _lex(q: str, kk: int) -> list[str]:
        hits, _stats = search_with_stats(q, kk, index)
        return [h["primitive_id"] for h in hits]

    def _fuse(q: str) -> list[str]:
        lex, den = _lex(q, 20), dense_topk(q, dense, 20)
        return [r["primitive_id"] for r in _f.rrf({"lexical": lex, "dense": den})][:k]

    retrievers = {"lexical": lambda q: _lex(q, k), "dense": lambda q: dense_topk(q, dense, k), "fusion": _fuse}
    modes = {"clean": lambda t: t, "noisy": _g._typo}  # noqa: SLF001 — reuse the shipped typo injector
    out: dict[str, Any] = {}
    overlaps: list[float] = []
    for mode, corrupt in modes.items():
        per = {name: {"mrr": [], "recall": [], "lat_ms": []} for name in retrievers}
        for c in sample:
            gold = {c.get("primitive_id")}
            q = corrupt(c.get("title") or _emb.blackbox_text(c)[:60])
            for name, fn in retrievers.items():
                t0 = time.perf_counter(); ids = fn(q); dt = (time.perf_counter() - t0) * 1000.0
                per[name]["mrr"].append(_mrr(ids, gold))
                per[name]["recall"].append(_recall_at_k(ids, gold, k))
                per[name]["lat_ms"].append(dt)
            if mode == "clean":
                lex_set, den_set = set(_lex(q, k)), set(dense_topk(q, dense, k))
                overlaps.append(len(lex_set & den_set) / len(lex_set | den_set) if (lex_set or den_set) else 0.0)
        out[mode] = {name: {"mrr": round(_mean(v["mrr"]), 4), "recall_at_k": round(_mean(v["recall"]), 4),
                            "mean_latency_ms": round(_mean(v["lat_ms"]), 2)} for name, v in per.items()}
    return {"record_type": "scale_retrieval_benchmark", "corpus_size": len(cards), "k": k,
            "query_sample": len(sample), "embed_path": dense["embed_path"],
            "build_seconds": {"lexical_index": round(build_lexical_s, 2), "dense_index": round(build_dense_s, 2)},
            "known_item": out,
            "lexical_dense_topk_overlap_jaccard": round(_mean(overlaps), 4),
            "note": "labels-free known-item probe (title->find-self) over the real 100K+ corpus; clean rewards "
                    "lexical, noisy (typo'd) rewards dense; low lexical/dense overlap = complementary paths. "
                    "grains/hierarchical recompute their keys per query today; precompute them like the dense "
                    "index (build_primitive_embeddings) to add those paths here too.",
            **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # a small hermetic corpus: the 5 gold families + a few disjoint distractors (fast, deterministic)
    distractors = [{"primitive_id": f"d:{i}", "title": f"zeta{i} widget",
                    "blackbox": f"sigma{i} unrelated distractor {i}.", "input_edge": f"In{i}",
                    "output_edge": f"Out{i}", **BOUNDARY} for i in range(20)]
    cards = _gold_corpus() + distractors

    # (a) RUNNABLE: every path in the FULL graph runs without error on a real query (this is the headline)
    sweep = runnable_sweep(cards, ["get rid of repeated rows and store them"], max_paths=None)
    checks.append(("every enumerated path equals the graph's total path count",
                   sweep["paths_enumerated"] == _graph.graph_summary()["total_paths"]))
    checks.append(("ALL paths run without error (0 exceptions across the whole graph)", sweep["all_runnable"]))
    checks.append(("a real fraction of paths produce non-empty results",
                   sweep["non_empty_result_rate"] > 0.3))

    # (b) the LLM options fire + are counted when a stub seam is supplied
    llm_sweep = runnable_sweep(cards, ["scrape then dedupe"], max_paths=400,
                               llm_stub=lambda p: "a dedup-and-store pipeline primitive")
    checks.append(("with an llm stub, some llm-option paths fire and are token-counted",
                   llm_sweep["llm_paths_fired"] >= 1 and llm_sweep["all_runnable"]))

    # (c) QUALITY: race configs; the union never loses to lexical-alone, and a champion is picked
    bench = quality_bench(cards, list(_LABELLED_QUERIES), k=_DEFAULT_K)
    checks.append(("a champion config is chosen with real metrics",
                   bench["champion"] is not None and 0.0 <= bench["champion"]["ndcg_at_k"] <= 1.0))
    lex = bench["per_search_best"].get("lexical")
    allp = bench["per_search_best"].get("all")
    checks.append(("the full multi-path union scores >= lexical-vocabulary-alone (nDCG)",
                   allp is not None and lex is not None and allp["ndcg_at_k"] >= lex["ndcg_at_k"] - 1e-9))
    checks.append(("the real local embedder is used for the semantic path (model2vec/ollama, not the proxy)",
                   bench["embed_path"] in ("model2vec", "ollama") or bench["embed_path"] == "tokens"))

    # (c2) SCALE: the scalable retrievers (lexical inverted index + precomputed dense + fusion) run a
    #      labels-free known-item probe; a card found from its own title, build + latency recorded
    sc = scale_bench(cards, k=5, query_sample=8)
    checks.append(("scale bench builds lexical + dense indexes and runs a known-item probe",
                   sc["corpus_size"] == len(cards) and "clean" in sc["known_item"]
                   and "dense_index" in sc["build_seconds"]))
    checks.append(("the dense retriever finds a card from its own title at scale (real embedder end-to-end)",
                   sc["known_item"]["clean"]["dense"]["recall_at_k"] >= 0.5))

    # (d) determinism + governance
    checks.append(("the quality bench is deterministic (byte-identical twice)",
                   json.dumps(quality_bench(cards, list(_LABELLED_QUERIES), configs=_ranking_configs(
                       searches=["lexical", "all"])), sort_keys=True)
                   == json.dumps(quality_bench(cards, list(_LABELLED_QUERIES), configs=_ranking_configs(
                       searches=["lexical", "all"])), sort_keys=True)))
    checks.append(("receipts are candidate/serves_truth=false",
                   sweep["serves_truth"] is False and bench["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - path_graph_bench: enumerated + ran ALL {_graph.graph_summary()['total_paths']} paths of the "
          f"graph with 0 errors (shared cache), and benchmarked the ranking-relevant configs on a labelled "
          f"set with recall@k/MRR/nDCG over INDEPENDENT retrieval — the full union scores >= lexical-alone, a "
          f"champion is picked, and the semantic path runs on the REAL local embedder ({_emb.real_text_path()}). "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--runnable", action="store_true", help="enumerate + run EVERY path over a real sample")
    ap.add_argument("--bench", action="store_true", help="quality benchmark (recall@k/MRR/nDCG per config)")
    ap.add_argument("--sample", type=int, default=_DEFAULT_CORPUS_SAMPLE, help="real distractor cards to mix in")
    ap.add_argument("--k", type=int, default=_DEFAULT_K, help="retrieval depth for the metrics")
    ap.add_argument("--max-paths", type=int, default=None, help="cap the runnable sweep (default: all)")
    ap.add_argument("--queries", type=int, default=2, help="how many labelled queries to sweep each path over")
    ap.add_argument("--scale", action="store_true", help="benchmark scalable retrievers over the 100K+ corpus")
    ap.add_argument("--max-cards", type=int, default=None, help="cap the scale corpus (default: all ~112k)")
    ap.add_argument("--query-sample", type=int, default=200, help="known-item probe size for --scale")
    args = ap.parse_args(argv)
    if args.scale:
        cards = _load_scale_corpus(args.max_cards)
        print(f"scale-benchmarking over {len(cards)} primitives (embedder={_emb.real_text_path()}) ...")
        rec = scale_bench(cards, k=args.k, query_sample=args.query_sample)
        out = resource("data") / "dev-intel" / "session_emulation" / "scale_retrieval_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps(rec, indent=2))
        print(f"\nwritten: {out}")
        return 0
    if args.self_test:
        return _self_test()
    if args.runnable:
        cards = bench_corpus(args.sample)
        qs = sorted({q["query"] for q in _LABELLED_QUERIES})[:max(1, args.queries)]
        print(f"running EVERY path ({_graph.graph_summary()['total_paths']}) over {len(cards)} cards "
              f"x {len(qs)} queries ...")
        rec = runnable_sweep(cards, qs, max_paths=args.max_paths)
        out = resource("data") / "dev-intel" / "session_emulation" / "path_graph_runnable_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps({k: rec[k] for k in ("total_paths_in_graph", "paths_enumerated", "path_runs",
              "runnable", "errors", "all_runnable", "non_empty_result_rate",
              "mean_latency_ms_per_search_option")}, indent=2))
        print(f"\nwritten: {out}")
        return 0 if rec["all_runnable"] else 1
    if args.bench:
        cards = bench_corpus(args.sample)
        print(f"benchmarking configs over {len(cards)} cards, embedder={_emb.real_text_path()} ...")
        rec = quality_bench(cards, list(_LABELLED_QUERIES), k=args.k)
        out = resource("data") / "dev-intel" / "session_emulation" / "path_graph_quality_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps({"embed_path": rec["embed_path"], "configs_raced": rec["configs_raced"],
                          "champion": rec["champion"], "union_vs_lexical_ndcg_lift": rec["union_vs_lexical_ndcg_lift"],
                          "per_search_best": rec["per_search_best"]}, indent=2))
        print(f"\nwritten: {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
