#!/usr/bin/env python3
"""scripts.multi_path_coverage_bench — coverage is NOT one number from one path. The flat 0.761 was LEXICAL
inverted-index token overlap ALONE; this bench measures every retrieval path we own and their UNION, so the
honest question — "how many dev-task prompts can we cover if we use embeddings + facets + edges + registers,
not just vocabulary?" — gets a real answer.

TWO retrieval modes behind one receipt (multi-path law — the honest mode is the default, the old one is the
labelled fallback):

  * "independent" (DEFAULT, fixed 2026-07-06) — each path retrieves its own top-k from the FULL corpus by its
    own index: lexical from the inverted index, semantic from the PERSISTED embedding store
    (capability_embedding.intent_query's stored-matrix lane — what made this affordable at 112K), facet from
    the persisted per-card feature records. Union coverage is NOT capped by any single path's recall.
  * "rescore" — the pre-fix architecture (a WIDE lexical net surfaces candidates, every path rescores that
    pool). Kept as a labelled row because it measures a real serving shape (cheap-retrieve → rescore) — but
    its union recall is CAPPED at lexical@wide-net recall, which is exactly the flaw the fleet flagged; never
    read a rescore receipt as multi-path coverage.

The paths:

  * lexical   — idf token overlap (scripts.build_primitive_search_index)                 [the current metric]
  * semantic  — blackbox-embedding cosine (scripts.capability_embedding.intent_query)    [meaning, not words]
  * technical — the TECHNICAL register embedding (edges+operations+datatypes)            [engineer vocabulary]
                (rescore-only today: no persisted register store yet — reported as a GAP in independent mode,
                never a fabricated pass; build_primitive_embeddings over register_text(card,"technical") is
                the unlock)
  * facet     — shared operation/datatype facets (scripts.primitive_descriptor)          [capability kind]

A prompt is COVERED by a path if that path's top-k contains a card scoring above the path's relevance floor —
a REACH proxy, not labelled precision (the gold set is roadmap #2). The UNION (covered by ANY path) is the
real coverage; the per-path breakdown shows which path recovers the lexical misses. Every path reuses an
existing proof-gated engine — this bench builds no new retrieval.

    PYTHONPATH=. python3 scripts/multi_path_coverage_bench.py --self-test
    PYTHONPATH=. python3 scripts/multi_path_coverage_bench.py --run [--sample N] [--mode independent|rescore]
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
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: embedder + registers + cosine
from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operation/datatype facets

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_WIDE_NET = 60          # lexical candidates each path rescoring picks from (cheap-retrieve breadth)
_TOP_K = 5              # per-path result depth (matches the coverage receipt)
_SEMANTIC_FLOOR = 0.30  # embedding cosine above which a semantic hit counts as relevant (single-source knob)
_FACET_FLOOR = 1        # >=1 shared operation/datatype facet counts as a facet-relevant hit
_DEFAULT_SAMPLE = 300   # prompts per run (deterministic head of the corpus; --sample overrides)


def _lexical_candidates(prompt: str, index: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The wide lexical net — the cheap retrieve every path rescoring works from."""
    from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
    hits, _stats = search_with_stats(prompt, _WIDE_NET, index)
    return hits


def _path_lexical(prompt: str, cand_cards: list[dict], expected: frozenset[str], cand_hits: list[dict]) -> bool:
    """Lexical coverage: an expected capability token appears in a top-k lexical hit's searchable text."""
    top = cand_hits[:_TOP_K]
    text = " ".join(json.dumps(h, default=str).lower() for h in top)
    return any(t in text for t in expected) if expected else False


def _path_semantic(prompt: str, cand_cards: list[dict], expected: frozenset[str], cand_hits: list[dict]) -> bool:
    """Semantic coverage: the prompt embeds near a candidate's BLACKBOX (meaning, not shared words)."""
    if not cand_cards:
        return False
    q = _emb.embed_text(prompt)
    scored = sorted(((_emb.cosine(q, _emb.embed_text(_emb.blackbox_text(c))), c) for c in cand_cards),
                    key=lambda s: -s[0])[:_TOP_K]
    return bool(scored) and scored[0][0] >= _SEMANTIC_FLOOR


def _path_technical(prompt: str, cand_cards: list[dict], expected: frozenset[str], cand_hits: list[dict]) -> bool:
    """Technical-register coverage: the prompt embeds near a card's TECHNICAL register (edges+ops+datatypes)
    — the engineer-vocabulary axis the plain lexical path cannot see."""
    if not cand_cards:
        return False
    q = _emb.embed_text(prompt)
    scored = sorted(((_emb.cosine(q, _emb.embed_text(_emb.register_text(c, "technical"))), c)
                     for c in cand_cards), key=lambda s: -s[0])[:_TOP_K]
    return bool(scored) and scored[0][0] >= _SEMANTIC_FLOOR


def _path_facet(prompt: str, cand_cards: list[dict], expected: frozenset[str], cand_hits: list[dict]) -> bool:
    """Facet coverage: the prompt's inferred operations/datatypes overlap a candidate's — capability KIND
    match even when the surface words differ (e.g. 'add retry logic' ↔ a card whose operation is 'validate')."""
    prompt_card = {"title": prompt, "blackbox": prompt, "input_edge": "", "output_edge": ""}
    p_ops = _desc.operations(prompt_card) | _desc.datatypes(prompt_card)
    if not p_ops:
        return False
    for c in cand_cards[:_TOP_K * 3]:  # facet match reads a slightly wider band (cheap set ops)
        if len(p_ops & (_desc.operations(c) | _desc.datatypes(c))) >= _FACET_FLOOR:
            return True
    return False


PATHS: dict[str, Callable[..., bool]] = {
    "lexical": _path_lexical,
    "semantic_blackbox": _path_semantic,
    "technical_register": _path_technical,
    "facet_operation": _path_facet,
}


# ── INDEPENDENT retrieval per path (the honest mode) — each path pulls its own top-k from the FULL corpus ─────
def _ind_lexical(prompt: str, expected: frozenset[str], ctx: dict[str, Any]) -> tuple[bool, list[str]]:
    """Full-corpus lexical top-k (the inverted index IS independent retrieval); same hit test as rescore."""
    from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
    hits, _stats = search_with_stats(prompt, _TOP_K, ctx["index"])
    text = " ".join(json.dumps(h, default=str).lower() for h in hits)
    ids = [h.get("primitive_id") for h in hits if h.get("primitive_id")]
    return (any(t in text for t in expected) if expected else False), ids


def _ind_semantic(prompt: str, expected: frozenset[str], ctx: dict[str, Any]) -> tuple[bool, list[str]]:
    """Full-corpus semantic top-k via intent_query — the STORED-MATRIX lane serves this at 112K scale (one
    matmul against the persisted store; ~0.2s/query vs ~19s recompute), which is what makes independent
    semantic retrieval affordable enough to be the default here."""
    hits = _emb.intent_query(prompt, ctx["cards"], k=_TOP_K, path=ctx["embed_path"], store=ctx["store"])
    ids = [h.get("primitive_id") for h in hits if h.get("primitive_id")]
    return (bool(hits) and hits[0]["score"] >= _SEMANTIC_FLOOR), ids


def _ind_facet(prompt: str, expected: frozenset[str], ctx: dict[str, Any]) -> tuple[bool, list[str]]:
    """Full-corpus facet scan over precomputed per-card facet sets (reuses the PERSISTED feature records from
    build_primitive_embeddings when present). Surfaces the first _TOP_K matches in corpus order — reach, not
    ranking (facet overlap is near-binary at _FACET_FLOOR=1)."""
    prompt_card = {"title": prompt, "blackbox": prompt, "input_edge": "", "output_edge": ""}
    p_ops = _desc.operations(prompt_card) | _desc.datatypes(prompt_card)
    if not p_ops:
        return False, []
    surfaced: list[str] = []
    for pid, facets in ctx["facet_sets"]:
        if len(p_ops & facets) >= _FACET_FLOOR:
            surfaced.append(pid)
            if len(surfaced) >= _TOP_K:
                break
    return bool(surfaced), surfaced


#: the independent-retrieval rows. technical_register is ABSENT on purpose (no persisted register store yet) —
#: it is reported in the receipt as a gap, never silently skipped and never fabricated from the lexical pool.
INDEPENDENT_PATHS: dict[str, Callable[..., tuple[bool, list[str]]]] = {
    "lexical": _ind_lexical,
    "semantic_blackbox": _ind_semantic,
    "facet_operation": _ind_facet,
}
INDEPENDENT_GAP_PATHS: tuple[str, ...] = tuple(sorted(set(PATHS) - set(INDEPENDENT_PATHS)))


def _persisted_facets() -> Optional[dict[str, frozenset]]:
    """primitive_id -> operation/datatype facet set from the PERSISTED feature records
    (build_primitive_embeddings --build). None when the store is absent — callers compute per card instead."""
    try:
        from scripts import build_primitive_embeddings as _stored  # noqa: PLC0415
        path = _stored.default_store_dir() / "features.jsonl"
        out: dict[str, frozenset] = {}
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[r["primitive_id"]] = frozenset(r.get("operations") or []) | frozenset(r.get("datatypes") or [])
        return out
    except Exception:  # noqa: BLE001 — no persisted features => compute from the cards (slower, same result)
        return None


def _independent_ctx(cards_by_id: dict[str, dict], index: dict[str, Any] | None,
                     store: Any, embed_path: Optional[str]) -> dict[str, Any]:
    """The shared context the independent paths retrieve from: the full-corpus lexical index, the card list
    (+ store handle) for the semantic lane, and per-card facet sets (persisted features reused when present)."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    cards = list(cards_by_id.values())
    persisted = _persisted_facets()
    facet_sets = [(pid, persisted[pid]) if persisted and pid in persisted
                  else (pid, frozenset(_desc.operations(c) | _desc.datatypes(c)))
                  for pid, c in ((c.get("primitive_id"), c) for c in cards)]
    return {"index": index or build_index(cards), "cards": cards, "facet_sets": facet_sets,
            "store": store, "embed_path": embed_path or _emb.real_text_path(),
            "persisted_facets_used": persisted is not None}


def _measure_independent(prompts: list[dict[str, Any]], cards_by_id: dict[str, dict],
                         index: dict[str, Any] | None, store: Any, embed_path: Optional[str]) -> dict[str, Any]:
    """Per-path + UNION coverage with INDEPENDENT retrieval per path over the FULL corpus — union recall is not
    capped by any single path's pool. Completeness is computed over the union of cards the paths actually
    SURFACED (what a user would see), through the same _capability_fraction as rescore mode (no metric drift)."""
    ctx = _independent_ctx(cards_by_id, index, store, embed_path)
    per_path_hits = {name: 0 for name in INDEPENDENT_PATHS}
    union_hits = 0
    lexical_miss_recovered = 0
    frac_sums = {"lexical": 0.0, "facet": 0.0, "union": 0.0}
    for row in prompts:
        prompt = row["prompt"]
        expected = frozenset(row.get("expected_capabilities") or [])
        covered_by: dict[str, bool] = {}
        surfaced_ids: list[str] = []
        lex_hit_rows: list[dict[str, Any]] = []
        for name, fn in INDEPENDENT_PATHS.items():
            hit, ids = fn(prompt, expected, ctx)
            covered_by[name] = hit
            if hit:
                per_path_hits[name] += 1
            surfaced_ids += [i for i in ids if i not in surfaced_ids]
            if name == "lexical":
                lex_hit_rows = [{"primitive_id": i, **cards_by_id.get(i, {})} for i in ids]
        if any(covered_by.values()):
            union_hits += 1
        if not covered_by["lexical"] and any(v for k, v in covered_by.items() if k != "lexical"):
            lexical_miss_recovered += 1
        surfaced_cards = [cards_by_id[i] for i in surfaced_ids if i in cards_by_id]
        frac = _capability_fraction(expected, surfaced_cards, lex_hit_rows)
        for k in frac_sums:
            frac_sums[k] += frac[k]
    n = len(prompts) or 1
    return {"record_type": "multi_path_coverage_receipt", "retrieval_mode": "independent", "prompts": n,
            "hit_coverage_per_path": {name: round(hits / n, 3) for name, hits in per_path_hits.items()},
            "hit_union_coverage": round(union_hits / n, 3),
            "completeness_mean_fraction": {k: round(v / n, 3) for k, v in frac_sums.items()},
            "lexical_miss_recovered_by_other_paths": round(lexical_miss_recovered / n, 3),
            "independent_gap_paths": list(INDEPENDENT_GAP_PATHS),
            "embed_path": ctx["embed_path"], "persisted_facets_used": ctx["persisted_facets_used"],
            "top_k": _TOP_K, "semantic_floor": _SEMANTIC_FLOOR,
            "note": "INDEPENDENT retrieval per path over the FULL corpus — union recall is NOT capped by a "
                    "lexical pool (the pre-2026-07-06 flaw; mode='rescore' preserves that architecture as a "
                    "labelled fallback). HIT floors are reach proxies, not labelled precision (gold set = "
                    "roadmap #2). Paths in independent_gap_paths run in rescore mode only until their surface "
                    "gets a persisted full-corpus index.", **BOUNDARY}


def _capability_fraction(expected: frozenset[str], cand_cards: list[dict], cand_hits: list[dict]) -> dict[str, float]:
    """The COMPLETENESS metric (what last turn's 0.761 measured): of a prompt's expected capability tokens,
    what fraction does each path connect to a card? Lexical: the token appears in a top-k hit's text. Facet:
    the token maps to an operation/datatype facet present in a candidate. Union: covered by EITHER. This is
    the metric that answers 'why didn't more cards help' — completeness is per-capability, so it moves only
    when a path matches the specific capability word, not when the corpus merely grows."""
    if not expected:
        return {"lexical": 0.0, "facet": 0.0, "union": 0.0}
    top_text = " ".join(json.dumps(h, default=str).lower() for h in cand_hits[:_TOP_K])
    cand_facets: set[str] = set()
    for c in cand_cards[:_TOP_K * 4]:
        cand_facets |= _desc.operations(c) | _desc.datatypes(c)
    prompt_card = {"title": " ".join(expected), "blackbox": " ".join(expected), "input_edge": "", "output_edge": ""}
    lex_cov = {t for t in expected if t in top_text}
    # a capability token is facet-covered if IT maps to an operation/datatype a candidate also has
    tok_facets = {t: (_desc.operations({"title": t, "blackbox": t, "input_edge": "", "output_edge": ""})
                      | _desc.datatypes({"title": t, "blackbox": t, "input_edge": "", "output_edge": ""}))
                  for t in expected}
    fac_cov = {t for t in expected if tok_facets[t] & cand_facets}
    _ = prompt_card
    union = lex_cov | fac_cov
    n = len(expected)
    return {"lexical": len(lex_cov) / n, "facet": len(fac_cov) / n, "union": len(union) / n}


def measure(prompts: list[dict[str, Any]], cards_by_id: dict[str, dict],
            index: dict[str, Any] | None = None, *, mode: str = "independent",
            store: Any = "auto", embed_path: Optional[str] = None) -> dict[str, Any]:
    """Per-path + UNION coverage over the prompts, at TWO levels: (a) HIT — does a path surface any relevant
    card (binary); (b) COMPLETENESS — what fraction of a prompt's capabilities does a path connect (the 0.761
    metric). Also the recovery rate: prompts LEXICAL missed that a non-lexical path caught. ``mode`` picks the
    retrieval architecture: "independent" (default — each path retrieves from the FULL corpus; the honest
    multi-path number) or "rescore" (every path rescores a wide LEXICAL pool — union capped at lexical recall;
    kept as the labelled fallback that measures the cheap-retrieve→rescore serving shape)."""
    if mode == "independent":
        return _measure_independent(prompts, cards_by_id, index, store, embed_path)
    if mode != "rescore":
        raise ValueError(f"unknown mode {mode!r}; modes are ('independent', 'rescore')")
    per_path_hits = {name: 0 for name in PATHS}
    union_hits = 0
    lexical_miss_recovered = 0
    frac_sums = {"lexical": 0.0, "facet": 0.0, "union": 0.0}
    for row in prompts:
        prompt = row["prompt"]
        expected = frozenset(row.get("expected_capabilities") or [])
        cand_hits = _lexical_candidates(prompt, index)
        cand_cards = [cards_by_id[h["primitive_id"]] for h in cand_hits
                      if h.get("primitive_id") in cards_by_id]
        covered_by: dict[str, bool] = {}
        for name, fn in PATHS.items():
            hit = fn(prompt, cand_cards, expected, cand_hits)
            covered_by[name] = hit
            if hit:
                per_path_hits[name] += 1
        if any(covered_by.values()):
            union_hits += 1
        if not covered_by["lexical"] and any(v for k, v in covered_by.items() if k != "lexical"):
            lexical_miss_recovered += 1
        frac = _capability_fraction(expected, cand_cards, cand_hits)
        for k in frac_sums:
            frac_sums[k] += frac[k]
    n = len(prompts) or 1
    return {"record_type": "multi_path_coverage_receipt", "retrieval_mode": "rescore", "prompts": n,
            "hit_coverage_per_path": {name: round(hits / n, 3) for name, hits in per_path_hits.items()},
            "hit_union_coverage": round(union_hits / n, 3),
            "completeness_mean_fraction": {k: round(v / n, 3) for k, v in frac_sums.items()},
            "lexical_miss_recovered_by_other_paths": round(lexical_miss_recovered / n, 3),
            "wide_net": _WIDE_NET, "top_k": _TOP_K, "semantic_floor": _SEMANTIC_FLOOR,
            "note": "RESCORE mode: every path picks from a wide LEXICAL candidate pool, so union coverage is "
                    "CAPPED at lexical@wide-net recall — read this as the value of multi-path RESCORING, never "
                    "as multi-path retrieval coverage (that is mode='independent', the default). HIT = does a "
                    "path surface a relevant card (binary); COMPLETENESS = fraction of a prompt's capabilities "
                    "a path connects (the 0.761 metric).", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # a tiny synthetic corpus where lexical and semantic DISAGREE by construction
    cards = [
        {"primitive_id": "c:retry", "title": "Resilient call wrapper",
         "blackbox": "Wrap a call so it automatically re-attempts with exponential backoff on transient failure.",
         "input_edge": "Call", "output_edge": "ResilientCall", **BOUNDARY},
        {"primitive_id": "c:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering near-identical records.",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch", **BOUNDARY},
    ]
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    by_id = {c["primitive_id"]: c for c in cards}
    prompts = [{"prompt": "add retry logic with exponential backoff to the api client",
                "expected_capabilities": ["retry", "backoff", "exponential"]},
               {"prompt": "collapse redundant entries by clustering near-identical items",
                "expected_capabilities": ["totallynovelword", "anotherunmatchedword"]}]  # thin lexical on purpose
    receipt = measure(prompts, by_id, index, mode="rescore")
    checks.append(("every path reports a coverage number (rescore mode, the preserved fallback)",
                   set(receipt["hit_coverage_per_path"]) == set(PATHS)
                   and receipt["retrieval_mode"] == "rescore"))
    checks.append(("union coverage >= the best single path (union never loses)",
                   receipt["hit_union_coverage"] >= max(receipt["hit_coverage_per_path"].values())))
    # the dedup prompt shares NO expected token with the card (lexical misses) but shares the 'dedup' OPERATION
    # facet — the deterministic non-lexical path recovers it (the real embedding path recovers more, but the
    # offline PROXY embedding is token-based ≈ lexical, so the hermetic recovery claim rests on the facet path)
    dedup = measure([prompts[1]], by_id, index, mode="rescore")
    checks.append(("a thin-word prompt is recovered by the deterministic FACET path when lexical misses",
                   dedup["hit_coverage_per_path"]["lexical"] == 0.0
                   and dedup["hit_coverage_per_path"]["facet_operation"] == 1.0
                   and dedup["hit_union_coverage"] == 1.0
                   and dedup["lexical_miss_recovered_by_other_paths"] == 1.0))
    checks.append(("completeness union fraction >= lexical fraction (multi-path never lowers completeness)",
                   receipt["completeness_mean_fraction"]["union"] >= receipt["completeness_mean_fraction"]["lexical"]))
    checks.append(("determinism (byte-identical twice)",
                   json.dumps(measure(prompts, by_id, index, mode="rescore"), sort_keys=True)
                   == json.dumps(measure(prompts, by_id, index, mode="rescore"), sort_keys=True)))
    checks.append(("receipt is candidate/serves_truth=false", receipt["serves_truth"] is False))

    # ── INDEPENDENT mode (the default; the fleet-flagged fix) — the mutation-grade proof of the flaw + fix:
    # a card that shares ZERO tokens with the prompt (the lexical wide net returns NOTHING, so in rescore mode
    # every path's candidate pool is EMPTY) but shares an operation facet. rescore union = 0.0 (the cap the
    # fleet flagged); independent union = 1.0 (the facet path retrieves from the FULL corpus). Verified pair:
    # 'deduplicate my customer list' ↔ 'Collapse near identical entries' — token overlap ∅, facets {dedup,collection}.
    iso_cards = [
        {"primitive_id": "c:collapse", "title": "Collapse near identical entries",
         "blackbox": "Cluster rows that look alike and keep one canonical row per cluster.",
         "input_edge": "RecordBatch", "output_edge": "CanonicalBatch", **BOUNDARY},
        cards[0],  # the retry card — an unrelated distractor
    ]
    iso_by_id = {c["primitive_id"]: c for c in iso_cards}
    iso_index = build_index(iso_cards)
    iso_prompt = [{"prompt": "deduplicate my customer list", "expected_capabilities": ["deduplicate"]}]
    iso_rescore = measure(iso_prompt, iso_by_id, iso_index, mode="rescore")
    iso_ind = measure(iso_prompt, iso_by_id, iso_index, mode="independent", store=None, embed_path="tokens")
    checks.append(("RESCORE mode is provably capped: an out-of-lexical-pool card is unreachable (union 0.0)",
                   iso_rescore["hit_union_coverage"] == 0.0))
    checks.append(("INDEPENDENT mode recovers it from the FULL corpus (union 1.0 via the facet path)",
                   iso_ind["hit_union_coverage"] == 1.0
                   and iso_ind["hit_coverage_per_path"]["facet_operation"] == 1.0
                   and iso_ind["hit_coverage_per_path"]["lexical"] == 0.0
                   and iso_ind["lexical_miss_recovered_by_other_paths"] == 1.0))
    checks.append(("independent mode names its gap paths (technical_register), never a fabricated pass",
                   iso_ind["retrieval_mode"] == "independent"
                   and list(INDEPENDENT_GAP_PATHS) == iso_ind["independent_gap_paths"]
                   and "technical_register" in iso_ind["independent_gap_paths"]))
    # the semantic path retrieves independently through the STORED-MATRIX lane (hermetic: a store built HERE
    # in tokens space) — a near-copy prompt clears the relevance floor and surfaces the right card top-1
    from scripts import build_primitive_embeddings as _stored  # noqa: PLC0415
    tstore = _stored.build(iso_cards, embed_path="tokens")
    sem_prompt = [{"prompt": "cluster rows that look alike and keep one canonical row",
                   "expected_capabilities": ["cluster"]}]
    sem_ind = measure(sem_prompt, iso_by_id, iso_index, mode="independent", store=tstore, embed_path="tokens")
    checks.append(("independent semantic retrieval works through the stored-matrix lane (floor cleared)",
                   sem_ind["hit_coverage_per_path"]["semantic_blackbox"] == 1.0))
    checks.append(("independent mode is deterministic (byte-identical twice)",
                   json.dumps(measure(iso_prompt, iso_by_id, iso_index, mode="independent", store=None,
                                      embed_path="tokens"), sort_keys=True)
                   == json.dumps(measure(iso_prompt, iso_by_id, iso_index, mode="independent", store=None,
                                         embed_path="tokens"), sort_keys=True)))
    checks.append(("independent union >= best single independent path (union never loses)",
                   iso_ind["hit_union_coverage"] >= max(iso_ind["hit_coverage_per_path"].values())))
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - multi_path_coverage_bench: coverage measured across lexical + semantic-blackbox + "
          "technical-register + facet paths and their UNION, in TWO labelled modes — INDEPENDENT (default: "
          "each path retrieves its own top-k from the FULL corpus, semantic via the persisted stored-matrix "
          "lane; union NOT capped by any pool — proven by a zero-token-overlap card unreachable in rescore "
          "mode, union 0.0, but recovered independently, union 1.0) and RESCORE (the preserved "
          "cheap-retrieve→rescore fallback, explicitly labelled as pool-capped). Gap paths are named, never "
          "fabricated. serves_truth=false.")
    return 0


def _run(sample: int, mode: str) -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    corpus = resource("data") / "dev-intel" / "session_emulation" / "dev_task_prompt_corpus.jsonl"
    prompts = read_jsonl_tolerant(corpus)[:sample]
    if not prompts:
        print("no prompt corpus — run generate_dev_task_prompt_corpus.py --write first")
        return 0
    # load the persisted card corpus once (both modes retrieve over the full card set)
    cards = read_jsonl_tolerant(
        resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl")
    for extra in ("primitive_edge_cards.jsonl",):
        cards += read_jsonl_tolerant(
            resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / extra)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    n_paths = len(INDEPENDENT_PATHS) if mode == "independent" else len(PATHS)
    print(f"measuring {len(prompts)} prompts over {len(by_id)} cards, {n_paths} paths, mode={mode} ...")
    receipt = measure(prompts, by_id, mode=mode)
    out = resource("data") / "dev-intel" / "session_emulation" / "multi_path_coverage_receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print(f"\nwritten: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--sample", type=int, default=_DEFAULT_SAMPLE, help="prompts to measure (default 300)")
    ap.add_argument("--mode", choices=("independent", "rescore"), default="independent",
                    help="retrieval architecture: independent per-path retrieval (honest, default) or "
                         "rescore-a-lexical-pool (the labelled fallback)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.sample, args.mode)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
