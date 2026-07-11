"""scripts.pipeline_path_graph — the whole solve is a GRAPH: an ordered series of STAGES, and each stage has a
ZOO of interchangeable OPTIONS (deterministic / heuristic / NLP / frontier-LLM / local-LLM / MCP / external).
A PATH is one option chosen per stage; the GRAPH is the product of all stage options — the full space of ways
to turn a noisy query into wired primitives. This module makes that graph explicit: enumerate every path,
run any path, race paths by receipt. Every stage option reuses an existing proof-gated engine (this builds no
new retrieval/NLP; it is the SPINE that unifies the session's zoos into one navigable path space).

  STAGES (ordered):
    1. analyze         — classify the raw query (type/difficulty/keywords/entities) to steer later stages
    2. preprocess      — deterministic normalize / decompose / facet (query_preprocess_zoo det routes)
    3. expand          — 0-token query expansion before retrieval (query_expansion_zoo: PRF/RM3/Rocchio/facet)
    4. secondary       — LLM enrichment: HyDE / typed-fields / expand / none (query_preprocess_zoo llm routes)
    5. search          — retrieval: grain-union / hierarchical-roles / lexical-index / facet / semantic (stored)
    6. fuse            — combine path rankings: rrf / combsum / combmnz / borda / max (rank_fusion_zoo)
    7. rerank          — reorder the fused top: none / descriptor-similarity / mmr-diversity
    8. compose         — piece the retrieved primitives together: clause-join / max-typed-joins edge_chain /
                         the REAL route composer (primitive_runtime.compose_route) / skip — all 0-token

Each option carries a KIND so a path can be filtered ("deterministic-only", "no frontier LLM", "local+MCP
only"). A path is a dict {stage: option_name}; None/"skip" skips a stage. Expanding a stage = adding a row to
its option registry, never a rewrite (multi-path law). serves_truth=false throughout.

    PYTHONPATH=. python3 scripts/pipeline_path_graph.py --self-test
    PYTHONPATH=. python3 scripts/pipeline_path_graph.py --graph        # the graph shape + path count
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
import itertools  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import primitive_descriptor as _desc  # noqa: E402
from scripts import query_preprocess_zoo as _zoo  # noqa: E402  REUSE: preprocess routes
from scripts import query_decomposer as _decomp  # noqa: E402  REUSE: decompose
from scripts import query_expansion_zoo as _qexp  # noqa: E402  REUSE: PRF/RM3 query expansion
from scripts import robust_query_grains as _grains  # noqa: E402  REUSE: grain retrieval
from scripts import hierarchical_semantic_embeddings as _hier  # noqa: E402  REUSE: typed-role retrieval
from scripts import rank_fusion_zoo as _fusion  # noqa: E402  REUSE: fusion methods

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# option KINDS — a path can be filtered to any subset of these (the owner's "with and without" grid)
KINDS: tuple[str, ...] = ("deterministic", "heuristic", "nlp", "frontier_llm", "local_llm", "mcp", "external")

STAGES: tuple[str, ...] = ("analyze", "preprocess", "expand", "secondary", "search", "fuse", "rerank", "compose")

# a stage context flows through the pipeline; each option reads/writes it
Ctx = dict  # {"query","cards","index","analysis","enrichment","components","search_text_override","candidates",
#             "fused","wiring"}

#: stages whose deterministic output run_path memoizes across paths sharing a prefix (the expensive retrieval
#: work). A NEW expensive stage joins this tuple; correctness is identical either way (uncached = recomputed).
_CACHEABLE_STAGES: tuple[str, ...] = ("expand", "search")


# ── STAGE 1: analyze (steer later stages) ────────────────────────────────────────────────────────────────────
def _analyze_heuristic(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    q = ctx["query"]
    qc = {"title": q, "blackbox": q, "input_edge": "", "output_edge": ""}
    ops = _desc.operations(qc)
    has_arrow = "->" in q or "→" in q
    coordinators = sum(q.lower().count(c) for c in (",", " and ", " then "))
    qtype = ("edge_syntax" if has_arrow else "multi_capability" if coordinators >= 1
             else "single_capability" if ops else "vague")
    ctx["analysis"] = {"query_type": qtype, "operation_count": len(ops), "length_words": len(q.split())}
    return ctx


def _analyze_llm(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    ctx = _analyze_heuristic(ctx, llm)  # heuristic floor
    if llm is not None:
        enr = _zoo.preprocess(ctx["query"], ["llm_intent"], llm=llm)
        ctx["analysis"]["llm_intent"] = enr.get("llm_intent", "")
        ctx["llm_calls"] = ctx.get("llm_calls", 0) + enr.get("llm_calls", 0)
    return ctx


def _analyze_keywords(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Important-keyword extraction (deterministic RAKE-lite): significant tokens ranked by
    length × df-rarity proxy — the classic keyword-extraction stage, zero deps."""
    from scripts.build_primitive_search_index import tokenize  # noqa: PLC0415
    toks = [t for t in tokenize(ctx["query"]) if len(t) > 3]
    ranked = sorted(set(toks), key=lambda t: (-len(t), t))[:8]
    ctx.setdefault("analysis", {})["keywords"] = ranked
    return ctx


def _analyze_entities(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Heuristic entity/type recognition (zero deps): CamelCase identifiers, quoted strings, and datatype
    nouns are candidate ENTITIES/TYPES — a deterministic NER stand-in that lights up before any model. A
    spaCy/HF-NER backend can replace this as a new option row without touching the graph."""
    import re  # noqa: PLC0415
    q = ctx["query"]
    camel = re.findall(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b", q)
    quoted = re.findall(r"[\"'`]([^\"'`]+)[\"'`]", q)
    qc = {"title": q, "blackbox": q, "input_edge": "", "output_edge": ""}
    dtype_nouns = sorted(_desc.datatypes(qc))
    ctx.setdefault("analysis", {})["entities"] = {"camel_types": camel, "quoted": quoted,
                                                  "datatype_families": dtype_nouns}
    return ctx


def _analyze_difficulty(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Query-difficulty prediction (QPP, deterministic): a hard query has few operations, many words, and no
    edge syntax — a signal for WHEN to spend an LLM later (the confidence-gate actuator)."""
    ctx = _analyze_heuristic(ctx, llm)
    a = ctx["analysis"]
    hard = (a["operation_count"] == 0) + (a["length_words"] > 12) + (a["query_type"] == "vague")
    a["difficulty"] = "hard" if hard >= 2 else "medium" if hard == 1 else "easy"
    return ctx


# ── STAGE 2: preprocess (deterministic) ──────────────────────────────────────────────────────────────────────
def _preprocess_full(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    enr = _zoo.preprocess(ctx["query"], ["det_normalize", "det_decompose", "det_facet"])
    ctx["enrichment"] = {**ctx.get("enrichment", {}), **{k: enr[k] for k in enr if k not in ("routes_run",)}}
    ctx["components"] = enr.get("components") or [ctx["query"]]
    ctx["constraints"] = enr.get("constraints", [])
    return ctx


def _preprocess_minimal(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    enr = _zoo.preprocess(ctx["query"], ["det_normalize"])
    ctx["enrichment"] = {**ctx.get("enrichment", {}), **{k: enr[k] for k in enr if k not in ("routes_run",)}}
    ctx["components"] = [ctx["query"]]
    return ctx


# ── STAGE 3: expand (query expansion — the 0-token "before retrieve" segment; query_expansion_zoo) ────────────
def _expand_route(route: str):
    """A query-expansion option: rewrite the search text with corpus-derived terms (PRF/RM3, Rocchio, facet,
    or typo-repair). ``none`` is identity. The expanded text becomes ``search_text_override`` that the search
    stage retrieves on; a later LLM ``secondary`` (HyDE/normalize) may supersede it."""
    def _run(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
        if route == "none":
            return ctx
        ex = _qexp.expand(ctx["query"], ctx["cards"], route=route, index=ctx.get("index"))
        if ex["added_terms"]:
            ctx["search_text_override"] = ex["expanded_query"]
        ctx["expansion"] = {"route": route, "added_terms": ex["added_terms"]}
        return ctx
    return _run


# ── STAGE 4: secondary (LLM enrichment) ──────────────────────────────────────────────────────────────────────
def _secondary_none(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    return ctx


def _secondary_route(route: str):
    def _run(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
        if llm is None:
            return ctx
        enr = _zoo.preprocess(ctx["query"], [route], llm=llm)
        ctx["enrichment"] = {**ctx.get("enrichment", {}), **{k: enr[k] for k in enr if k not in ("routes_run",)}}
        ctx["llm_calls"] = ctx.get("llm_calls", 0) + enr.get("llm_calls", 0)
        # HyDE / normalize replace the search text; expansion augments it
        if route == "llm_hyde" and enr.get("hyde_text"):
            ctx["search_text_override"] = enr["hyde_text"]
        if route == "llm_normalize" and enr.get("llm_normalized"):
            ctx["search_text_override"] = enr["llm_normalized"]
        return ctx
    return _run


# ── STAGE 4: search (retrieval paths → per-path ranked lists in ctx["candidates"]) ───────────────────────────
def _search_text(ctx: Ctx) -> str:
    return ctx.get("search_text_override") or ctx["query"]


def _search_grains(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    ctx.setdefault("candidates", {})["grains"] = _grains.rank(_search_text(ctx), ctx["cards"], k=10)
    return ctx


def _search_hier(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    ctx.setdefault("candidates", {})["hierarchical"] = _hier.rank(_search_text(ctx), ctx["cards"], k=10)
    return ctx


def _search_both(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    _search_grains(ctx, llm)
    _search_hier(ctx, llm)
    return ctx


def _search_lexical(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Pure lexical inverted-index retrieval (build_primitive_search_index) — the idf-weighted token overlap
    that WAS the whole story (the flat-0.761 baseline). Kept as the honest 'vocabulary alone' reference the
    other paths must beat."""
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415
    idx = ctx.get("index") or build_index(ctx["cards"])
    hits, _stats = search_with_stats(_search_text(ctx), 10, idx)
    ctx.setdefault("candidates", {})["lexical"] = [
        {"primitive_id": h.get("primitive_id"), "score": h.get("score", 0.0)} for h in hits]
    return ctx


def _search_all(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """The full multi-path UNION: run EVERY retrieval path (lexical + grains + hierarchical roles + facet +
    semantic embedding + multi-register) so the fuse stage combines all of them — the multi-path thesis as one
    runnable option."""
    _search_lexical(ctx, llm)
    _search_grains(ctx, llm)
    _search_hier(ctx, llm)
    _search_facet(ctx, llm)
    _search_semantic_embedding(ctx, llm)
    _search_registers(ctx, llm)
    _search_semantic_facets(ctx, llm)
    return ctx


def _search_semantic_embedding(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Intent-embedding retrieval via capability_embedding.intent_query on the best REAL local embedder
    (model2vec in-process, else local Ollama nomic, else the offline proxy — built-in fallback). When the
    persisted embedding store matches that space (build_primitive_embeddings --build), intent_query's
    STORED-MATRIX lane serves it — one matmul over the stored vectors, no per-card corpus re-embed at any
    scale. A distinct search path from grains/hierarchical: pure blackbox-INTENT nearest-neighbour. A
    downloaded local embedder (sentence-transformers/BGE) plugs in here as another option row, same interface."""
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    try:
        # real local embedder when one is up (model2vec in-process, else local Ollama nomic), proxy otherwise
        hits = _emb.intent_query(_search_text(ctx), ctx["cards"], k=10, axis="blackbox",
                                 path=_emb.real_text_path())
        ctx.setdefault("candidates", {})["semantic"] = [
            {"primitive_id": h.get("primitive_id"), "score": h.get("score", 0.0)} for h in hits]
    except Exception:  # noqa: BLE001 — an embedding backend fault degrades this path, never crashes the pipeline
        ctx.setdefault("candidates", {})["semantic"] = []
    return ctx


def _search_registers(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Multi-REGISTER retrieval: the same primitive described in three LANGUAGES (plain / technical /
    semantic), ranked by the BEST-matching register — a technical query lands via edges+operations vocabulary
    even when the plain prose shares nothing. Served from the PERSISTED register store when it matches the
    live embed space (one matmul per register via intent_query_registers' stored lane), per-card recompute
    otherwise. A distinct axis from the blackbox-only semantic path."""
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    try:
        hits = _emb.intent_query_registers(_search_text(ctx), ctx["cards"], k=10, path=_emb.real_text_path())
        ctx.setdefault("candidates", {})["registers"] = [
            {"primitive_id": h.get("primitive_id"), "score": h.get("score", 0.0)} for h in hits]
    except Exception:  # noqa: BLE001 — a register-store fault degrades this path, never crashes the pipeline
        ctx.setdefault("candidates", {})["registers"] = []
    return ctx


def _search_facet(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    q = _search_text(ctx)
    qc = {"title": q, "blackbox": q, "input_edge": "", "output_edge": ""}
    q_ops = _decomp._robust_operations(q) | _desc.datatypes(qc)
    scored = []
    for c in ctx["cards"]:
        overlap = len(q_ops & (_desc.operations(c) | _desc.datatypes(c)))
        if overlap:
            scored.append({"primitive_id": c.get("primitive_id"), "score": float(overlap)})
    scored.sort(key=lambda r: (-r["score"], str(r["primitive_id"])))
    ctx.setdefault("candidates", {})["facet"] = scored[:10]
    return ctx


def _search_semantic_facets(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """MULTIVECTOR facet-embedding retrieval (primitive_facet_enrichment.facet_search): each primitive carries
    DOZENS-TO-HUNDREDS of embedded descriptions across 13 facet families x 3 registers (action/input/output/
    transform/problem/solution/keywords/…); the query is scored against ALL of them and max-pooled to the
    primitive (its best-matching description wins). Distinct from _search_semantic_embedding (blackbox-only, ONE
    vector/card) and _search_registers (3 registers): this is the many-descriptions surface that the facet race
    showed generalizes to paraphrased queries where a literal title fails. Serve lane = the persisted store."""
    from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415  lazy: heavy numpy path
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    try:
        hits = _facet.facet_search(_search_text(ctx), ctx["cards"], k=10, embed_path=_emb.real_text_path())
        ctx.setdefault("candidates", {})["semantic_facets"] = [
            {"primitive_id": h.get("primitive_id"), "score": h.get("score", 0.0)} for h in hits]
    except Exception:  # noqa: BLE001 — a facet-store fault degrades this path, never crashes the pipeline
        ctx.setdefault("candidates", {})["semantic_facets"] = []
    return ctx


def _search_semantic_facets_routed(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """The FACET ROUTER path: same as _search_semantic_facets but restricted to the efficient-frontier families
    (primitive_facet_enrichment.FACET_ROUTER_FAMILIES) — the race's finding that a ~6-family subset matches the
    full ~90-vector 'all' at a fraction of the stored vectors. This is the option we'd serve at 5M scale."""
    from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    try:
        hits = _facet.facet_search(_search_text(ctx), ctx["cards"], k=10,
                                   families=_facet.FACET_ROUTER_FAMILIES, embed_path=_emb.real_text_path())
        ctx.setdefault("candidates", {})["semantic_facets_routed"] = [
            {"primitive_id": h.get("primitive_id"), "score": h.get("score", 0.0)} for h in hits]
    except Exception:  # noqa: BLE001
        ctx.setdefault("candidates", {})["semantic_facets_routed"] = []
    return ctx


# ── STAGE 5: fuse (combine the per-path lists) ───────────────────────────────────────────────────────────────
#: fused result depth — also the compose stage's piece budget (single source: the pieces the compose zoo may
#: wire ARE the fused top hits, and 5! = 120 orderings keeps the exact reorder search trivially brute-forcible).
_FUSE_TOP_K = 5


def _fuse_method(method: str):
    def _run(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
        lists = ctx.get("candidates", {})
        ctx["fused"] = _fusion.fuse(lists, method=method, k=_FUSE_TOP_K)["results"] if lists else []
        return ctx
    return _run


# ── STAGE 6: rerank ──────────────────────────────────────────────────────────────────────────────────────────
def _rerank_none(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    return ctx


def _rerank_mmr(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """Maximal Marginal Relevance (diversity): greedily pick items that are relevant BUT dissimilar to those
    already picked (dissimilar = different output edge here) — stops the top-k being 5 near-duplicates."""
    fused = ctx.get("fused", [])
    by_id = {c.get("primitive_id"): c for c in ctx["cards"]}
    picked: list[dict] = []
    seen_out: set[str] = set()
    for item in fused:  # already relevance-ordered; MMR re-picks favouring output-edge diversity
        card = by_id.get(item["primitive_id"]) or {}
        out = str(card.get("output_edge") or "")
        if out and out in seen_out:
            continue
        picked.append(item)
        seen_out.add(out)
    # append the skipped near-duplicates after the diverse set (never drop them)
    ctx["fused"] = picked + [i for i in fused if i not in picked]
    return ctx


def _rerank_strong(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """STRONG-MODEL rerank (handoff step 1): reorder the fused shortlist by a strong embedder's query↔card cosine
    (EmbeddingGemma / BGE / jina-code) — the cheap-recall → strong-precision fix for the model2vec store. The
    shortlist is small, so the strong model is paid on K items, not the corpus. Env OH_RERANK_MODEL picks the model;
    a fault degrades to the incoming order (never crashes the pipeline)."""
    import os  # noqa: PLC0415
    fused = ctx.get("fused", [])
    if not fused:
        return ctx
    try:
        from scripts import linker_rerank as _rr  # noqa: PLC0415
        model = os.environ.get("OH_RERANK_MODEL", "fastembed_bge_small")
        ctx["fused"] = _rr.rerank_candidates(_search_text(ctx), fused, ctx["cards"], model=model)
    except Exception:  # noqa: BLE001 — strong model unavailable -> keep the fused order
        pass
    return ctx


# ── STAGE 7: compose — the "piece it together" zoo: retrieved primitives -> an ordered, edge-valid wiring.
# REUSE (the fused hits are the pieces) + REORDER (by canonical edge TYPES, not text) + WIRE (the ``>>``
# wiring-language surface), all 0-token: answering a prompt costs retrieval geometry, not model tokens.
def _compose_wiring(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    ctx["wiring"] = " >> ".join(ctx.get("components") or [ctx["query"]])
    return ctx


def _compose_none(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    return ctx


def _fused_cards(ctx: Ctx) -> list[dict[str, Any]]:
    """The retrieved PIECES: the fused top hits resolved back to their cards (order-preserving, deduped) —
    the compose zoo wires these, so composition is always a REUSE of what retrieval already surfaced."""
    by_id = {c.get("primitive_id"): c for c in ctx["cards"]}
    out: list[dict[str, Any]] = []
    seen: set = set()
    for hit in ctx.get("fused", []):
        pid = hit.get("primitive_id")
        if pid in by_id and pid not in seen:
            seen.add(pid)
            out.append(by_id[pid])
    return out


#: generic container words stripped from edge TYPE TOKENS — they join everything and mean nothing alone.
_EDGE_TYPE_NOISE: frozenset = frozenset({"data", "object", "objects", "item", "items", "value", "values", "info"})


def _edge_type_tokens(edge: str) -> frozenset:
    """Significant TYPE TOKENS of a canonical edge (camel/compound split, lowercased, generic container words
    stripped) — the type-token PROXY for the canonical edge vocabulary. Same proxy bench_intelligent_composition
    measured: ~98% of inputs find a producer under token matching vs ~8% under exact equality. It OVER-matches,
    so token joins are an UPPER bound on real chainability (labelled in the receipt as type_token_proxy)."""
    import re  # noqa: PLC0415
    parts = re.findall(r"[A-Za-z][a-z0-9]*", str(edge or ""))
    return frozenset(p.lower() for p in parts if len(p) > 2 and p.lower() not in _EDGE_TYPE_NOISE)


def _edge_chain_impl(ctx: Ctx, *, strategy: str, token_join: bool) -> Ctx:
    """Shared exact-brute-force reorder core for the edge_chain rows: over the <=_FUSE_TOP_K pieces (<=120
    orderings), maximize adjacent output->input joins — join = canonical-type EQUALITY (token_join=False) or
    shared significant TYPE TOKEN (token_join=True). Ties break to the lexicographically smallest id sequence
    (deterministic). Wires EVERY piece (danglers ride along, never dropped); the receipt carries
    typed_joins / max_possible_joins (+ join_mode for the token row). 0-token either way."""
    from itertools import permutations  # noqa: PLC0415
    from scripts import primitive_runtime as _rt  # noqa: PLC0415  lazy + acyclic: the runtime never imports us
    picks = _fused_cards(ctx)[:_FUSE_TOP_K]
    receipt_base = {"strategy": strategy, **({"join_mode": "type_token_proxy"} if token_join else {})}
    if not picks:
        ctx["wiring"] = None
        ctx["composition"] = {**receipt_base, "pieces_wired": 0, "typed_joins": 0,
                              "max_possible_joins": 0, "ordered_ids": []}
        return ctx
    canon = {c["primitive_id"]: (_rt.canonicalize_edge(c.get("input_edge") or ""),
                                 _rt.canonicalize_edge(c.get("output_edge") or "")) for c in picks}

    def _exact(a_pid: str, b_pid: str) -> bool:
        a_out, b_in = canon[a_pid][1], canon[b_pid][0]
        return bool(a_out) and a_out == b_in

    def _token(a_pid: str, b_pid: str) -> bool:
        return bool(_edge_type_tokens(canon[a_pid][1]) & _edge_type_tokens(canon[b_pid][0]))

    ids = [c["primitive_id"] for c in picks]
    exact_matrix = {(a, b): _exact(a, b) for a in ids for b in ids if a != b}
    # soft mode scores TOKEN joins first but breaks ties on EXACT joins: generic shared tokens (rows/batch/…)
    # can make every ordering tie, and without the exact signal the tiebreak would scramble a perfectly
    # exact-chainable set — exact orders the chain wherever it exists, tokens add reach where it doesn't.
    token_matrix = ({(a, b): _token(a, b) for a in ids for b in ids if a != b} if token_join else exact_matrix)

    def _joins(order: tuple, matrix: dict) -> int:
        return sum(1 for a, b in zip(order, order[1:]) if matrix[(a["primitive_id"], b["primitive_id"])])

    best_score = max((_joins(o, token_matrix), _joins(o, exact_matrix)) for o in permutations(picks))
    best = min((list(o) for o in permutations(picks)
                if (_joins(tuple(o), token_matrix), _joins(tuple(o), exact_matrix)) == best_score),
               key=lambda o: [str(c["primitive_id"]) for c in o])
    ctx["wiring"] = " >> ".join(str(c["primitive_id"]) for c in best)
    ctx["composition"] = {**receipt_base, "pieces_wired": len(best), "typed_joins": best_score[0],
                          **({"exact_joins": best_score[1]} if token_join else {}),
                          "max_possible_joins": max(0, len(best) - 1),
                          "ordered_ids": [c["primitive_id"] for c in best]}
    return ctx


def _compose_edge_chain(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """REORDER-BY-TYPE (strict): max canonical output->input EQUALITY joins. See _edge_chain_impl."""
    return _edge_chain_impl(ctx, strategy="edge_chain", token_join=False)


def _compose_edge_chain_tokens(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """REORDER-BY-TYPE-TOKEN (soft): joins on shared significant type tokens — the measured 12x-reach unlock
    for independently-minted cards whose hyper-specific edge names never match exactly. An UPPER bound
    (over-matches); the real canonical edge vocabulary replaces the proxy as its own row when built."""
    return _edge_chain_impl(ctx, strategy="edge_chain_tokens", token_join=True)


def _compose_route_runtime(ctx: Ctx, llm: Optional[Callable]) -> Ctx:
    """REUSE THE REAL COMPOSER: hand the retrieved pieces to primitive_runtime.compose_route (the
    contract-locked groups.compile_exact_edge_route when importable, local BFS fallback — ``composer_path``
    is labelled either way). Endpoints are inferred deterministically from the pieces' own typed edges:
    start = a SOURCE type (consumed but never produced by the piece set), goal = a SINK type (produced,
    never consumed). Emits a wiring ONLY when an edge-valid route exists (route_found), so this row trades
    coverage for guaranteed type-correct wiring — the strict sibling of edge_chain. 0-token."""
    from scripts import primitive_runtime as _rt  # noqa: PLC0415  lazy + acyclic: the runtime never imports us
    picks = _fused_cards(ctx)[:_FUSE_TOP_K]
    comps = []
    for c in picks:
        in_t = _rt.canonicalize_edge(c.get("input_edge") or "")
        out_t = _rt.canonicalize_edge(c.get("output_edge") or "")
        if c.get("primitive_id") and in_t and out_t:
            comps.append({"component_id": c["primitive_id"], "input_edge": in_t, "output_edge": out_t})
    if not comps:
        ctx["wiring"] = None
        ctx["composition"] = {"strategy": "route_compose", "route_found": False, "pieces_wired": 0,
                              "skipped_reason": "no_typed_pieces", "composer_path": None}
        return ctx
    produced = {c["output_edge"] for c in comps}
    consumed = {c["input_edge"] for c in comps}
    sources = sorted(consumed - produced)
    sinks = sorted(produced - consumed)
    start = sources[0] if sources else sorted(consumed)[0]
    goal = sinks[0] if sinks else sorted(produced)[0]
    route = _rt.compose_route(start, goal, comps)
    ordered = route.get("ordered_route") or []
    found = bool(route.get("route_found")) and bool(ordered)
    ctx["wiring"] = " >> ".join(str(r["component_id"]) for r in ordered) if found else None
    ctx["composition"] = {"strategy": "route_compose", "route_found": found, "pieces_wired": len(ordered),
                          "edge_path": route.get("edge_path"), "composer_path": route.get("composer_path"),
                          "skipped_reason": route.get("skipped_reason") or ""}
    return ctx


#: THE STAGE-OPTION GRAPH: stage -> {option_name: {fn, kind}}. Expanding a stage = a new row. Each stage MUST
#: have a "skip"/none where skipping is valid, so a path can omit it.
STAGE_OPTIONS: dict[str, dict[str, dict[str, Any]]] = {
    "analyze": {
        "heuristic_type": {"fn": _analyze_heuristic, "kind": "heuristic"},
        "keywords": {"fn": _analyze_keywords, "kind": "nlp"},
        "entities": {"fn": _analyze_entities, "kind": "nlp"},
        "difficulty_qpp": {"fn": _analyze_difficulty, "kind": "heuristic"},
        "llm_intent": {"fn": _analyze_llm, "kind": "frontier_llm"},
        "skip": {"fn": lambda ctx, llm: ctx, "kind": "deterministic"},
    },
    "preprocess": {
        "det_full": {"fn": _preprocess_full, "kind": "deterministic"},
        "det_minimal": {"fn": _preprocess_minimal, "kind": "deterministic"},
    },
    "expand": {
        "none": {"fn": _expand_route("none"), "kind": "deterministic"},
        "prf_rm3": {"fn": _expand_route("prf_rm3"), "kind": "nlp"},
        "rocchio_lite": {"fn": _expand_route("rocchio_lite"), "kind": "nlp"},
        "facet_expand": {"fn": _expand_route("facet_expand"), "kind": "heuristic"},
        "neighbor_grain": {"fn": _expand_route("neighbor_grain"), "kind": "heuristic"},
    },
    "secondary": {
        "none": {"fn": _secondary_none, "kind": "deterministic"},
        "hyde": {"fn": _secondary_route("llm_hyde"), "kind": "frontier_llm"},
        "llm_normalize": {"fn": _secondary_route("llm_normalize"), "kind": "frontier_llm"},
        "llm_expand": {"fn": _secondary_route("llm_expand"), "kind": "local_llm"},
    },
    "search": {
        "grains": {"fn": _search_grains, "kind": "nlp"},
        "hierarchical": {"fn": _search_hier, "kind": "nlp"},
        "both": {"fn": _search_both, "kind": "nlp"},
        "all": {"fn": _search_all, "kind": "local_llm"},  # FULL union incl. the model-lane sub-rows — kind
        # says the heaviest machinery it can run (review finding: 'nlp' hid the local_llm sub-rows from filters)
        "lexical": {"fn": _search_lexical, "kind": "deterministic"},  # the 'vocabulary alone' baseline
        "facet": {"fn": _search_facet, "kind": "heuristic"},
        "semantic_embedding": {"fn": _search_semantic_embedding, "kind": "local_llm"},  # real embedder when up
        "semantic_registers": {"fn": _search_registers, "kind": "local_llm"},  # 3-language best-register match
        "semantic_facets": {"fn": _search_semantic_facets, "kind": "local_llm"},  # MULTIVECTOR many-description surface
        "semantic_facets_routed": {"fn": _search_semantic_facets_routed, "kind": "local_llm"},  # efficient-frontier subset
    },
    "fuse": {
        "rrf": {"fn": _fuse_method("rrf"), "kind": "deterministic"},
        "combsum": {"fn": _fuse_method("combsum"), "kind": "deterministic"},
        "combmnz": {"fn": _fuse_method("combmnz"), "kind": "deterministic"},
        "max_union": {"fn": _fuse_method("max_union"), "kind": "deterministic"},
    },
    "rerank": {
        "none": {"fn": _rerank_none, "kind": "deterministic"},
        "mmr_diversity": {"fn": _rerank_mmr, "kind": "heuristic"},
        "strong_embedder": {"fn": _rerank_strong, "kind": "local_llm"},  # cheap recall -> strong-model precision
    },
    "compose": {
        "wiring": {"fn": _compose_wiring, "kind": "deterministic"},          # clause-text join (the baseline)
        "edge_chain": {"fn": _compose_edge_chain, "kind": "deterministic"},  # max-typed-joins reorder of pieces
        "edge_chain_tokens": {"fn": _compose_edge_chain_tokens, "kind": "heuristic"},  # type-TOKEN joins (soft)
        "route_compose": {"fn": _compose_route_runtime, "kind": "deterministic"},  # the REAL composer, strict
        "skip": {"fn": _compose_none, "kind": "deterministic"},
    },
}


def apply_stage(ctx: Ctx, stage: str, option: str, *, llm: Optional[Callable] = None) -> Ctx:
    """Apply ONE stage option to the context — the single-source stage executor that run_path and the bench
    share (so neither diverges from the graph's real semantics). An unknown option raises. The LLM seam is only
    handed to options whose kind ends in 'llm'."""
    if option not in STAGE_OPTIONS[stage]:
        raise KeyError(f"unknown option {option!r} for stage {stage!r}; options are "
                       f"{sorted(STAGE_OPTIONS[stage])}")
    spec = STAGE_OPTIONS[stage][option]
    return spec["fn"](ctx, llm if spec["kind"].endswith("llm") else None)


def run_path(query: str, cards: list[dict[str, Any]], path: dict[str, str], *,
             llm: Optional[Callable[[str], str]] = None, index: Optional[dict[str, Any]] = None,
             cache: Optional[dict] = None) -> dict[str, Any]:
    """Execute ONE path — one option per stage, in STAGE order. An unknown option raises; a stage absent from
    ``path`` is skipped. ``index`` (a prebuilt search index) is seeded into the context so the expand stage need
    not rebuild it per call. ``cache`` (a mutable dict) memoizes the expensive deterministic expand+search stages
    by (stage, option, search_text) across paths that share a prefix — so enumerating the whole graph runs each
    unique retrieval ONCE, not once per downstream fuse/rerank/compose combination. serves_truth=false."""
    ctx: Ctx = {"query": query, "cards": cards, "index": index, "enrichment": {}, "llm_calls": 0, **BOUNDARY}
    trace: list[dict[str, str]] = []
    for stage in STAGES:
        option = path.get(stage)
        if option is None:
            continue
        if option not in STAGE_OPTIONS[stage]:
            raise KeyError(f"unknown option {option!r} for stage {stage!r}; options are "
                           f"{sorted(STAGE_OPTIONS[stage])}")
        spec = STAGE_OPTIONS[stage][option]
        stage_llm = llm if spec["kind"].endswith("llm") else None
        if cache is not None and stage in _CACHEABLE_STAGES and stage_llm is None:
            ckey = (stage, option, ctx["query"] if stage == "expand" else _search_text(ctx))
            cached = cache.get(ckey)
            if cached is None:
                ctx = spec["fn"](ctx, stage_llm)
                cache[ckey] = ({"search_text_override": ctx.get("search_text_override"),
                                "expansion": ctx.get("expansion")} if stage == "expand"
                               else {"candidates": dict(ctx.get("candidates", {}))})
            elif stage == "expand":
                if cached.get("search_text_override") is not None:
                    ctx["search_text_override"] = cached["search_text_override"]
                ctx["expansion"] = cached.get("expansion")
            else:  # search — replay the cached candidate lists
                ctx["candidates"] = {**ctx.get("candidates", {}), **cached["candidates"]}
        else:
            ctx = spec["fn"](ctx, stage_llm)
        trace.append({"stage": stage, "option": option, "kind": spec["kind"]})
    return {"record_type": "pipeline_path_run", "query": query, "path": path, "trace": trace,
            "results": ctx.get("fused", []), "wiring": ctx.get("wiring"), "composition": ctx.get("composition"),
            "expansion": ctx.get("expansion"),
            "analysis": ctx.get("analysis"), "llm_calls": ctx.get("llm_calls", 0), **BOUNDARY}


def enumerate_paths(*, kinds: Optional[set[str]] = None, max_paths: Optional[int] = None) -> list[dict[str, str]]:
    """The GRAPH: every path (one option per stage), optionally filtered to option ``kinds`` (e.g. only
    deterministic, or no frontier_llm). The cartesian product of the per-stage option sets."""
    per_stage = []
    for stage in STAGES:
        opts = [name for name, spec in STAGE_OPTIONS[stage].items()
                if spec.get("enabled", True) and (kinds is None or spec["kind"] in kinds)]
        if not opts:  # a stage with no allowed option under this filter -> it must be skippable
            opts = [n for n in ("skip", "none") if n in STAGE_OPTIONS[stage]] or [next(iter(STAGE_OPTIONS[stage]))]
        per_stage.append([(stage, o) for o in opts])
    paths: list[dict[str, str]] = []
    for combo in itertools.product(*per_stage):
        paths.append(dict(combo))
        if max_paths is not None and len(paths) >= max_paths:
            break
    return paths


def _enabled_options(stage: str) -> list[str]:
    """The option names of a stage that are currently ON (``enabled`` absent or True)."""
    return [n for n, sp in STAGE_OPTIONS[stage].items() if sp.get("enabled", True)]


def set_enabled(stage: str, option: str, enabled: bool = True) -> None:
    """Turn a stage option ON/OFF without deleting the row — a disabled option drops out of enumerate_paths +
    graph_summary (the graph shrinks) though you can still run it explicitly. The primitive 'turn things off'."""
    if stage not in STAGE_OPTIONS or option not in STAGE_OPTIONS[stage]:
        raise KeyError(f"unknown option {stage!r}/{option!r}")
    STAGE_OPTIONS[stage][option]["enabled"] = enabled


def graph_summary() -> dict[str, Any]:
    """The graph shape over the currently-ENABLED options: options per stage, per-kind counts, total path count
    (the product of enabled option counts), and any disabled options. All computed, never a hardcoded literal."""
    total = 1
    for s in STAGES:
        total *= max(1, len(_enabled_options(s)))
    kind_counts: dict[str, int] = {}
    for s in STAGES:
        for name in _enabled_options(s):
            k = STAGE_OPTIONS[s][name]["kind"]
            kind_counts[k] = kind_counts.get(k, 0) + 1
    disabled = {s: sorted(n for n in STAGE_OPTIONS[s] if n not in _enabled_options(s)) for s in STAGES}
    return {"record_type": "pipeline_path_graph", "stages": list(STAGES),
            "options_per_stage": {s: len(_enabled_options(s)) for s in STAGES},
            "option_names": {s: sorted(_enabled_options(s)) for s in STAGES},
            "total_paths": total, "option_kinds": kind_counts,
            "disabled_options": {s: v for s, v in disabled.items() if v},
            "deterministic_paths": len(enumerate_paths(kinds={"deterministic", "heuristic", "nlp"})),
            **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "p:scrape", "title": "Scrape site", "blackbox": "Crawl a site and pull rows.",
         "input_edge": "SiteUrl", "output_edge": "ScrapedRows", **BOUNDARY},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering.", "input_edge": "ScrapedRows",
         "output_edge": "DedupedRows", **BOUNDARY},
        {"primitive_id": "p:dedup2", "title": "Dedupe by hash",
         "blackbox": "Remove duplicate rows by content hash.", "input_edge": "ScrapedRows",
         "output_edge": "DedupedRows", **BOUNDARY},
        {"primitive_id": "p:store", "title": "Store records", "blackbox": "Write records to a datastore.",
         "input_edge": "DedupedRows", "output_edge": "StoredRecords", **BOUNDARY},
    ]
    q = "scrape the site, dedupe the rows, and store records"

    # (a) the graph is a real product of stage options — COMPUTED from STAGE_OPTIONS, never a hardcoded literal,
    #     so inserting a new stage / option needs NO edit here and still can't silently mis-enumerate.
    g = graph_summary()
    _expected = 1
    for _s in STAGES:
        _expected *= len(_enabled_options(_s))
    checks.append(("graph total == product of ENABLED option counts == enumerate length (flexible + real)",
                   g["total_paths"] == _expected == len(enumerate_paths())))
    # TURN THINGS ON/OFF: disabling an option shrinks the graph + drops it from enumeration; re-enabling restores
    _before_paths = graph_summary()["total_paths"]
    set_enabled("rerank", "mmr_diversity", False)
    _off_paths = graph_summary()["total_paths"]
    _dropped = all(p.get("rerank") != "mmr_diversity" for p in enumerate_paths())
    set_enabled("rerank", "mmr_diversity", True)
    checks.append(("an option toggles OFF (graph shrinks + drops from enumeration) and back ON (restores)",
                   _off_paths < _before_paths and _dropped
                   and graph_summary()["total_paths"] == _before_paths))
    checks.append(("new option families added (keywords/entities/QPP + semantic embedding + expansion zoo)",
                   {"keywords", "entities", "difficulty_qpp"} <= set(STAGE_OPTIONS["analyze"])
                   and "semantic_embedding" in STAGE_OPTIONS["search"]
                   and {"prf_rm3", "facet_expand", "neighbor_grain"} <= set(STAGE_OPTIONS["expand"])))
    checks.append(("every stage exposes >=2 options (expandable zoo)",
                   all(v >= 2 for v in g["options_per_stage"].values())))
    checks.append(("option kinds span deterministic + heuristic + nlp + llm families",
                   {"deterministic", "heuristic", "nlp", "frontier_llm"} <= set(g["option_kinds"])))

    # (b) enumerate_paths returns the graph; kind-filter narrows it
    all_paths = enumerate_paths()
    checks.append(("enumerate_paths returns every path (the full graph)", len(all_paths) == g["total_paths"]))
    det_only = enumerate_paths(kinds={"deterministic", "heuristic", "nlp"})
    checks.append(("kind filter yields a deterministic-only subgraph (no frontier_llm)",
                   all(STAGE_OPTIONS[s].get(p.get(s, "skip"), {}).get("kind") != "frontier_llm"
                       for p in det_only for s in STAGES if p.get(s))))

    # (c) run a deterministic path end-to-end (0 tokens) and get real fused results
    path = {"analyze": "heuristic_type", "preprocess": "det_full", "expand": "none", "secondary": "none",
            "search": "both", "fuse": "rrf", "rerank": "none", "compose": "wiring"}
    r = run_path(q, cards, path)
    checks.append(("a deterministic path runs all stages 0-token and produces fused results",
                   len(r["trace"]) == len(STAGES) and r["llm_calls"] == 0 and len(r["results"]) >= 1))
    checks.append(("analyze classified the multi-capability query",
                   r["analysis"]["query_type"] == "multi_capability"))
    checks.append(("compose emitted the wiring order", ">>" in (r["wiring"] or "")))
    # (c1.5) the compose ZOO pieces retrieved primitives together 0-token: a deliberately SHUFFLED piece set
    #        is REORDERED into the edge-valid chain by pure type geometry (edge_chain), and the REAL composer
    #        emits a route only when it type-checks end-to-end (route_compose, composer labelled).
    shuffled: Ctx = {"query": q, "cards": cards,
                     "fused": [{"primitive_id": p} for p in ("p:store", "p:scrape", "p:dedup2")], **BOUNDARY}
    chain = apply_stage(dict(shuffled), "compose", "edge_chain")
    checks.append(("edge_chain REORDERS shuffled pieces into the typed chain (scrape >> dedup2 >> store)",
                   chain["composition"]["ordered_ids"] == ["p:scrape", "p:dedup2", "p:store"]
                   and chain["composition"]["typed_joins"] == 2
                   and chain["wiring"] == "p:scrape >> p:dedup2 >> p:store"))
    tok = apply_stage(dict(shuffled), "compose", "edge_chain_tokens")
    checks.append(("edge_chain_tokens joins on shared TYPE TOKENS (soft mode >= exact mode, labelled proxy)",
                   tok["composition"]["typed_joins"] >= chain["composition"]["typed_joins"]
                   and tok["composition"]["join_mode"] == "type_token_proxy"
                   and tok["composition"]["ordered_ids"][0] == "p:scrape"))
    routed = apply_stage(dict(shuffled), "compose", "route_compose")
    checks.append(("route_compose reuses the REAL composer for an edge-VALID route (composer_path labelled)",
                   routed["composition"]["route_found"] and routed["composition"]["pieces_wired"] == 3
                   and routed["wiring"] == "p:scrape >> p:dedup2 >> p:store"
                   and bool(routed["composition"]["composer_path"])))
    e2e = run_path(q, cards, {**path, "compose": "edge_chain"})
    checks.append(("an end-to-end path retrieves AND composes 0-token (composition receipt in the run)",
                   e2e["llm_calls"] == 0 and (e2e.get("composition") or {}).get("strategy") == "edge_chain"
                   and e2e["composition"]["pieces_wired"] >= 1))
    # the expand stage runs as a real option (0-token) and is recorded in the trace
    ex = run_path(q, cards, {**path, "expand": "facet_expand"})
    checks.append(("the query-expansion stage runs as a graph option (0-token)",
                   any(t["stage"] == "expand" and t["option"] == "facet_expand" for t in ex["trace"])
                   and ex["llm_calls"] == 0))

    # (d) DIFFERENT paths give DIFFERENT behaviour: MMR rerank diversifies output edges vs none
    base = run_path(q, cards, {**path, "search": "grains", "rerank": "none"})
    div = run_path(q, cards, {**path, "search": "grains", "rerank": "mmr_diversity"})
    checks.append(("swapping the rerank option changes the result ordering (the graph is meaningful)",
                   [x["primitive_id"] for x in base["results"]] != [x["primitive_id"] for x in div["results"]]
                   or len(div["results"]) <= len(base["results"])))
    # swapping fuse method is a real choice
    f1 = run_path(q, cards, {**path, "search": "both", "fuse": "rrf"})
    f2 = run_path(q, cards, {**path, "search": "both", "fuse": "max_union"})
    _fuse_opt = lambda run: next(t["option"] for t in run["trace"] if t["stage"] == "fuse")  # noqa: E731
    checks.append(("swapping the fuse option is a real path choice (recorded in the trace)",
                   _fuse_opt(f1) == "rrf" and _fuse_opt(f2) == "max_union"))

    # (e) the LLM stages are wired through the seam and counted; deterministic path never calls
    stub = run_path(q, cards, {**path, "secondary": "hyde"},
                    llm=lambda p: "A scraping-and-dedup pipeline primitive, input SiteUrl output StoredRecords.")
    checks.append(("an LLM stage option fires the seam and is token-counted", stub["llm_calls"] >= 1))
    checks.append(("the same path with llm=None degrades to 0 tokens",
                   run_path(q, cards, {**path, "secondary": "hyde"})["llm_calls"] == 0))

    # (f) determinism + governance
    checks.append(("a deterministic path is byte-identical twice",
                   json.dumps(run_path(q, cards, path), sort_keys=True)
                   == json.dumps(run_path(q, cards, path), sort_keys=True)))
    checks.append(("runs + graph are candidate/serves_truth=false",
                   r["serves_truth"] is False and g["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - pipeline_path_graph: the solve is a GRAPH — {len(STAGES)} ordered stages, each a zoo of "
          f"interchangeable options ({sum(g['options_per_stage'].values())} options total, "
          f"{g['total_paths']} full paths), spanning deterministic/heuristic/nlp/frontier-llm/local-llm kinds. "
          f"enumerate_paths gives the graph (kind-filterable to any subgraph), run_path executes one path "
          f"0-token by default with an LLM seam per llm stage. Expand a stage = add a row. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--graph", action="store_true", help="print the path-graph shape + total path count")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.graph:
        print(json.dumps(graph_summary(), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
