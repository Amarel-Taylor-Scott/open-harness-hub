#!/usr/bin/env python3
"""scripts.query_expansion_zoo — a ZOO of QUERY-EXPANSION paths: the "before retrieve" segment that enriches a
thin / terse / vocabulary-mismatched query with corpus-derived terms so the downstream retrieval (grains /
hierarchical / lexical) has more signal to match on. Named the #1 genuinely-absent 0-token technique by this
repo's own IR/NLP survey (data/dev-intel/adversarial_findings/ir-nlp-best-practices-2026-07-06.json, lens 0:
"Pseudo-relevance feedback (PRF/RM3) — the one named technique both genuinely absent and 0-token").

A new STAGE in the path graph (sits between preprocess and search): each route takes a raw query + the corpus
and returns an EXPANDED query (a strict superset of the original terms — expansion never drops what the user
typed), so it drops straight into understand_query._retrieve_component or pipeline_path_graph's search stage.
Every route is 0-token deterministic and reuses a shipped, proof-gated engine — this module adds no new
retrieval or embedding math; it is pure query rewriting over existing idf / facets / trigrams.

  none          — identity (the baseline the others must beat; keeps the zoo honest).
  prf_rm3       — Pseudo-Relevance Feedback (RM3, Lavrenko & Croft): retrieve the top feedback docs with the
                  free lexical path, score each candidate term by Σ_d rel(d)·P(t|d)·idf(t), add the top terms.
                  The classic "the top hits are mostly relevant, so borrow their vocabulary" move.
  rocchio_lite  — positive-only Rocchio centroid: add the most FREQUENT significant terms across the feedback
                  docs (no idf, no negative feedback) — a different (recall-leaning) bias than RM3.
  facet_expand  — controlled-vocabulary expansion: add the query's canonical operation/datatype FACET words
                  (primitive_descriptor), so "collapse duplicates" gains "dedup" with zero retrieval.
  neighbor_grain— variant/typo repair: for each query token, add the char-trigram-nearest CORPUS term
                  (robust_query_grains trigrams), so "idempotant"→"idempotent", "retru"→"retry" reach the
                  canonical vocabulary the index actually indexes.

``expand(query, cards, route=...)`` returns the expanded query + the added terms + their weights;
``race_expansions(labelled, cards)`` races every route by recall@k (champion by recall then parsimony) and
keeps the losers as labelled fallbacks — the multi-path law applied to query expansion. serves_truth=false —
an expanded query is a candidate rewrite, never truth.

    PYTHONPATH=. python3 scripts/query_expansion_zoo.py --self-test
    PYTHONPATH=. python3 scripts/query_expansion_zoo.py --expand "throttle the outbound api" --route prf_rm3
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
from typing import Any, Callable  # noqa: E402

from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: canonical operation/datatype facets
from scripts import robust_query_grains as _grains  # noqa: E402  REUSE: char-trigram variant matching
from scripts.build_primitive_search_index import (  # noqa: E402  REUSE: the ONE tokenizer + index (real idf)
    build_index as _build_index, search_with_stats as _search, tokenize as _tokenize,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_FB_DOCS = 5            # pseudo-relevance feedback depth (top-N docs assumed mostly-relevant; RM3 default band)
_FB_TERMS = 8           # expansion terms added (m); enough to bridge vocabulary, few enough to avoid drift
_MIN_TERM_LEN = 4       # a candidate expansion term must be this long (drops short function words / noise)
_NEIGHBOR_FLOOR = 0.5   # char-trigram Jaccard for a query token to snap to a corpus term (variant repair)
_NEIGHBOR_LEN_TOL = 2   # only compare tokens whose length differs by <= this (bounds the neighbour scan)


def _doc_text(card: dict[str, Any]) -> str:
    return f"{card.get('title') or ''} {card.get('blackbox') or ''} " \
           f"{card.get('input_edge') or ''} {card.get('output_edge') or ''}"


def _significant(text: str) -> list[str]:
    """The ONE tokenizer, filtered to terms long enough to carry topical signal."""
    return [t for t in _tokenize(text) if len(t) >= _MIN_TERM_LEN]


# ── the expansion routes: each (query, cards_by_id, index, fb_docs, fb_terms) -> [(term, weight), ...] ────────
def _expand_none(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                 fb_docs: int, fb_terms: int) -> list[tuple[str, float]]:
    return []


def _feedback_docs(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                   fb_docs: int) -> list[tuple[dict[str, Any], float]]:
    """The pseudo-relevant set: the top lexical hits, each with its retrieval score (the rel(d) weight)."""
    hits, _stats = _search(query, fb_docs, index)
    out: list[tuple[dict[str, Any], float]] = []
    for h in hits:
        card = cards_by_id.get(h.get("primitive_id"))
        if card is not None:
            out.append((card, float(h.get("score", 0.0))))
    return out


def _expand_prf_rm3(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                    fb_docs: int, fb_terms: int) -> list[tuple[str, float]]:
    """RM3: weight(t) = Σ_d rel(d)·P(t|d)·idf(t) over the feedback docs, rel(d) the normalized retrieval score,
    P(t|d)=tf(t,d)/|d|. Original query terms are excluded (we ADD vocabulary, never re-weight what's there)."""
    fb = _feedback_docs(query, cards_by_id, index, fb_docs)
    if not fb:
        return []
    idf: dict[str, float] = index.get("idf", {})
    q_terms = set(_significant(query))
    total_rel = sum(rel for _c, rel in fb) or 1.0
    weights: dict[str, float] = {}
    for card, rel in fb:
        toks = _significant(_doc_text(card))
        if not toks:
            continue
        n = len(toks)
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        norm_rel = rel / total_rel
        for t, c in tf.items():
            if t in q_terms:
                continue
            weights[t] = weights.get(t, 0.0) + norm_rel * (c / n) * idf.get(t, 1.0)
    ranked = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))[:fb_terms]
    return [(t, round(w, 6)) for t, w in ranked]


def _expand_rocchio_lite(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                         fb_docs: int, fb_terms: int) -> list[tuple[str, float]]:
    """Positive-only Rocchio: raw term frequency summed across the feedback docs (no idf, no negatives) — a
    recall-leaning centroid that favours COMMON feedback vocabulary where RM3 favours SELECTIVE vocabulary."""
    fb = _feedback_docs(query, cards_by_id, index, fb_docs)
    q_terms = set(_significant(query))
    freq: dict[str, int] = {}
    for card, _rel in fb:
        for t in set(_significant(_doc_text(card))):  # doc-frequency across the feedback set
            if t not in q_terms:
                freq[t] = freq.get(t, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:fb_terms]
    return [(t, float(c)) for t, c in ranked]


def _expand_facet(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                  fb_docs: int, fb_terms: int) -> list[tuple[str, float]]:
    """Controlled-vocabulary expansion: the query's canonical operation/datatype facet WORDS (no retrieval) —
    bridges paraphrase to the indexed canonical term ('collapse duplicates' -> 'dedup')."""
    qc = {"title": query, "blackbox": query, "input_edge": "", "output_edge": ""}
    facets = (_desc.operations(qc) | _desc.datatypes(qc)) - set(_significant(query))
    return [(t, 1.0) for t in sorted(facets)][:fb_terms]


def _expand_neighbor_grain(query: str, cards_by_id: dict[str, dict], index: dict[str, Any],
                           fb_docs: int, fb_terms: int) -> list[tuple[str, float]]:
    """Variant/typo repair: snap each query token to the char-trigram-nearest CORPUS term it is NOT already,
    so a garbled token reaches the canonical vocabulary the index holds. Bounded by a length tolerance."""
    vocab = list(index.get("idf", {}) or index.get("df", {}))
    q_terms = [t for t in _significant(query)]
    q_set = set(q_terms)
    added: dict[str, float] = {}
    for qt in q_terms:
        qg = _grains._char_ngrams(qt)
        best_term, best_score = None, _NEIGHBOR_FLOOR
        for v in vocab:
            if v in q_set or abs(len(v) - len(qt)) > _NEIGHBOR_LEN_TOL:
                continue
            s = _grains._jaccard(qg, _grains._char_ngrams(v))
            if s > best_score or (s == best_score and best_term is not None and v < best_term):
                best_term, best_score = v, s
        if best_term is not None and best_term != qt:
            added[best_term] = max(added.get(best_term, 0.0), round(best_score, 4))
    ranked = sorted(added.items(), key=lambda kv: (-kv[1], kv[0]))[:fb_terms]
    return list(ranked)


#: the expansion zoo — route name -> fn. understand_query / pipeline_path_graph pick one; a bench races them.
EXPANSIONS: dict[str, Callable[..., list[tuple[str, float]]]] = {
    "none": _expand_none,
    "prf_rm3": _expand_prf_rm3,
    "rocchio_lite": _expand_rocchio_lite,
    "facet_expand": _expand_facet,
    "neighbor_grain": _expand_neighbor_grain,
}
DEFAULT_EXPANSION = "prf_rm3"  # single-source default: the research-standard PRF, 0-token


def expand(query: str, cards: list[dict[str, Any]], *, route: str = DEFAULT_EXPANSION,
           index: dict[str, Any] | None = None, fb_docs: int = _FB_DOCS,
           fb_terms: int = _FB_TERMS) -> dict[str, Any]:
    """Expand ``query`` by ``route`` over ``cards``. The result's ``expanded_query`` is a strict SUPERSET of the
    original (added terms appended), so it drops into any text retriever. serves_truth=false."""
    if route not in EXPANSIONS:
        raise ValueError(f"unknown expansion route {route!r}; routes are {sorted(EXPANSIONS)}")
    cards_by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    if index is None:
        index = _build_index(cards)
    weighted = EXPANSIONS[route](query, cards_by_id, index, fb_docs, fb_terms)
    added = [t for t, _w in weighted]
    expanded = f"{query} {' '.join(added)}".strip() if added else query
    return {"record_type": "query_expansion", "route": route, "original_query": query,
            "added_terms": added, "term_weights": {t: w for t, w in weighted},
            "expanded_query": expanded, "expansion_count": len(added), **BOUNDARY}


def race_expansions(labelled: list[dict[str, Any]], cards: list[dict[str, Any]], *, k: int = 5) -> dict[str, Any]:
    """Race every expansion route on labelled queries — each {"query": str, "relevant": [id, ...]}. Receipt:
    recall@k of retrieving the EXPANDED query + mean terms added; champion = highest recall then FEWEST added
    terms (parsimony — expansion that helps least-invasively wins ties). Losers kept as labelled fallbacks."""
    index = _build_index(cards)
    receipts: list[dict[str, Any]] = []
    for name in EXPANSIONS:
        recalls, added_counts = [], []
        for q in labelled:
            relevant = set(q.get("relevant", []))
            ex = expand(q["query"], cards, route=name, index=index)
            hits, _stats = _search(ex["expanded_query"], k, index)
            ids = {h.get("primitive_id") for h in hits}
            recalls.append(len(ids & relevant) / len(relevant) if relevant else 0.0)
            added_counts.append(ex["expansion_count"])
        receipts.append({"route": name,
                         "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
                         "mean_terms_added": round(sum(added_counts) / len(added_counts), 2) if added_counts else 0.0})
    ranked = sorted(receipts, key=lambda r: (-r["recall_at_k"], r["mean_terms_added"], r["route"]))
    return {"record_type": "expansion_race_receipt", "k": k, "queries": len(labelled),
            "receipts": ranked, "champion": ranked[0]["route"] if ranked else None,
            "fallbacks": [r["route"] for r in ranked[1:]], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # a corpus where the TARGET shares NO word with the query but the feedback docs bridge the vocabulary:
    # query "throttle …" retrieves the two throttle cards, which also say "rate limit requests per second",
    # and the target says exactly that WITHOUT "throttle" — so only PRF can reach it.
    cards = [
        {"primitive_id": "c:thr1", "title": "Throttle outbound calls",
         "blackbox": "Throttle requests by enforcing a rate limit of requests per second using a token bucket window.",
         "input_edge": "Call", "output_edge": "ThrottledCall", **BOUNDARY},
        {"primitive_id": "c:thr2", "title": "Api throttler",
         "blackbox": "Throttle the outbound api by rate limiting requests per second with a sliding window.",
         "input_edge": "ApiCall", "output_edge": "ThrottledCall", **BOUNDARY},
        {"primitive_id": "c:target", "title": "Requests guard",
         "blackbox": "Enforce a rate limit on requests per second with a leaky bucket, rejecting excess.",
         "input_edge": "Request", "output_edge": "GuardedRequest", **BOUNDARY},
        {"primitive_id": "c:resize", "title": "Resize image", "blackbox": "Resize an image to dimensions.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
        {"primitive_id": "c:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering near-identical records.",
         "input_edge": "Batch", "output_edge": "DedupedBatch", **BOUNDARY},
    ]
    # the index df-cap (DOC_FREQUENCY_CAP_FRACTION = 5%) drops any token appearing in > 5% of docs — so PRF is
    # only exercised realistically on a corpus where the bridge vocabulary is SELECTIVE. Pad with
    # disjoint-vocabulary distractors so the shared "rate limit requests per second bucket" terms stay under the
    # cap (as they are in the real 34k corpus), not capped out as they would be in a 5-card toy index.
    cards += [{"primitive_id": f"c:pad{i}", "title": f"zeta{i} kappa{i} widget",
               "blackbox": f"sigma{i} omega{i} an unrelated distractor record numbered {i}.",
               "input_edge": f"In{i}", "output_edge": f"Out{i}", **BOUNDARY} for i in range(75)]
    index = _build_index(cards)
    by_id = {c["primitive_id"]: c for c in cards}
    query = "throttle the outbound api"

    # (a) the original query MISSES the target (it shares no word with it)
    base_hits, _ = _search(query, 3, index)
    base_ids = {h["primitive_id"] for h in base_hits}
    checks.append(("the raw query lexically misses the target (no shared word)", "c:target" not in base_ids))

    # (b) PRF/RM3 harvests the feedback docs' bridging vocabulary and adds it
    rm3 = expand(query, cards, route="prf_rm3", index=index)
    checks.append(("prf_rm3 adds corpus terms", rm3["expansion_count"] >= 1))
    checks.append(("prf_rm3 harvests the bridge vocabulary from the feedback docs",
                   any(t in rm3["added_terms"] for t in ("rate", "limit", "requests", "second", "bucket"))))

    # (c) retrieving the EXPANDED query now recovers the lexically-missed target
    exp_hits, _ = _search(rm3["expanded_query"], 3, index)
    checks.append(("the expanded query recovers the target the raw query missed",
                   "c:target" in {h["primitive_id"] for h in exp_hits}))

    # (d) expansion is a strict SUPERSET — it never drops the user's own terms
    checks.append(("the expanded query is a superset of the original (no dropped terms)",
                   all(w in rm3["expanded_query"].split() for w in query.split())))

    # (e) facet_expand adds a canonical operation word for a paraphrase (controlled vocabulary, 0 retrieval)
    fac = expand("collapse the duplicate rows", cards, route="facet_expand", index=index)
    checks.append(("facet_expand maps a paraphrase to the canonical operation term (dedup)",
                   "dedup" in fac["added_terms"]))

    # (f) neighbor_grain repairs a typo'd token to the canonical corpus term
    nb = expand("throtle outbund calls", cards, route="neighbor_grain", index=index)
    checks.append(("neighbor_grain snaps a typo to the canonical corpus token (throtle->throttle)",
                   "throttle" in nb["added_terms"]))

    # (g) the race ranks every route and picks a champion by recall then parsimony
    labelled = [{"query": query, "relevant": ["c:target", "c:thr1", "c:thr2"]},
                {"query": "remove duplicate rows", "relevant": ["c:dedup"]}]
    race = race_expansions(labelled, cards, k=3)
    checks.append(("the race ranks every route and picks a champion",
                   race["champion"] in EXPANSIONS and len(race["fallbacks"]) == len(EXPANSIONS) - 1))
    checks.append(("an expansion route beats or ties the no-expansion baseline on recall",
                   next(r["recall_at_k"] for r in race["receipts"] if r["route"] == race["champion"])
                   >= next(r["recall_at_k"] for r in race["receipts"] if r["route"] == "none")))

    # (h) determinism + governance
    checks.append(("expansion is deterministic (byte-identical twice)",
                   json.dumps(expand(query, cards, index=index), sort_keys=True)
                   == json.dumps(expand(query, cards, index=index), sort_keys=True)))
    checks.append(("expansion is candidate/serves_truth=false", rm3["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - query_expansion_zoo: {len(EXPANSIONS)} query-expansion routes (none / prf_rm3 / rocchio_lite "
          f"/ facet_expand / neighbor_grain) — the 0-token 'before retrieve' segment. PRF/RM3 harvests the "
          f"feedback docs' bridging vocabulary and RECOVERS a target the raw query lexically missed; "
          f"facet_expand maps paraphrase to the canonical operation term; neighbor_grain repairs typos to the "
          f"corpus vocabulary; every expansion is a strict superset of the original and the race picks the "
          f"route by recall@k then parsimony. Reuses the shipped idf / facets / trigrams. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--expand", metavar="QUERY", default=None, help="expand one query over the corpus")
    ap.add_argument("--route", default=DEFAULT_EXPANSION, choices=sorted(EXPANSIONS), help="expansion route")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.expand:
        from scripts.run_token_savings_experiments import _load_cards  # noqa: PLC0415
        cards = _load_cards(0)[:2000]
        print(json.dumps(expand(args.expand, cards, route=args.route), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
