#!/usr/bin/env python3
"""scripts.full_corpus_search_index — make ALL ~1.17M primitive records SEARCHABLE (candidate-only) and
MEASURE the honest lift AND precision impact of doing so.

Today only ~112,731 primitive cards are searchable (verified_factory 34,289 + primitive_edge 78,442, in
``data/dev-intel/aidevobserver_edge_foundry/``) — the index the ``primitive_search`` MCP queries. The repo
actually holds ≈1.17M primitive-bearing rows; the un-indexed mass is disjoint synthetic/candidate namespaces:

  * seed codeblocks  ~1,010,025  ``data/dev-intel/primitive_codeblocks/**/*.jsonl`` (prim_seed_primitive_*)
  * drafts           ~37,674     ``data/dev-intel/aidevobserver_context_foundry/primitive_drafts.jsonl``
  * gap-fill         ~17,111     ``data/dev-intel/domain_token_savings/template_minted_producer_cards*.jsonl``

This module is ADD-ONLY. It does NOT edit the contract-locked ``build_primitive_search_index`` — it REUSES its
builder (``build_index`` / ``build_search_doc``), its query path (``search_with_stats`` / ``fast_search``), its
persisted-index file format, and its ``load_index``. It adds three things on top:

  1. ``unify_corpus(specs)`` — a STREAMING generator that reads every namespace and normalizes each row to the
     search-doc card shape ``build_search_doc`` consumes. The indexed searchable text is
     ``title + input_edge + output_edge + problem_solution_core + family + industry`` — the multi-KB ``code``
     body is NEVER indexed (it bloats the index without helping intent search); the card's ``primitive_id`` is
     the stable handle back to the full source row. Typed ``input_edge``/``output_edge`` are preserved for
     composition joins.
  2. Content-key DEDUP (``canonical_id`` over title+edges+core) so the REAL distinct count is reported at full
     scale, verifying the 100%-distinct sample generalizes.
  3. A SEPARATE persisted index tier (``catalog/knowledge-packs/data/primitive-search-index-fullcorpus/``) built
     over the unified docs — added ALONGSIDE the curated 112K default (which is NEVER overwritten), swappable by
     config. Plus optional embeddings over the expanded set via ``build_primitive_embeddings`` (``--embeddings``).

Then it MEASURES, honestly, whether 1.17M-searchable HELPS or HURTS:

  * REACH LIFT — fraction of intent queries with ≥1 hit on the full corpus vs the 112K baseline, and how many
    baseline MISSES the full corpus recovers.
  * PRECISION IMPACT — on a LABELLED query set (saas_requirements_suite + dev_task_prompt_corpus), does adding
    ~1M seed cards BURY good hits? P@1 / P@k / MRR are computed on BOTH indexes with the same relevance test.
    If precision drops, the receipt says so plainly and recommends keeping seed cards in the candidate tier
    behind a flag rather than as the default.

Every emitted row is candidate=true / serves_truth=false (an index is metadata, never a proven primitive).

    PYTHONPATH=. python3 scripts/full_corpus_search_index.py --self-test
    PYTHONPATH=. python3 scripts/full_corpus_search_index.py --build            # the full ~1.17M run
    PYTHONPATH=. python3 scripts/full_corpus_search_index.py --build --embeddings --embed-limit 200000
    PYTHONPATH=. python3 scripts/full_corpus_search_index.py --query "screen entity against OFAC sanctions"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/build_primitive_embeddings.py) ───────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()  # add every _repos/*/backend so `from src.teleon...` resolves bare

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import gc  # noqa: E402
import hashlib  # noqa: E402  (scripts-plane content digest for the manifest; the no-hashlib law is scoped to src/**)
import json  # noqa: E402
from typing import Any, Callable, Iterable, Iterator, Optional  # noqa: E402

from scripts import build_primitive_search_index as _bpsi  # noqa: E402  REUSE: builder + query + format + load
from scripts._jsonl import iter_jsonl_tolerant  # noqa: E402  REUSE: the one streaming JSONL reader
from src.teleon.experiments.ids import canonical_id  # noqa: E402  REUSE: the one id/dedup-key authority

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "full_corpus_search_index"

# ── source namespaces (single source of the paths) ──────────────────────────────────────────────────────────
_EDGE_FOUNDRY = resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
_STAGED = resource("data") / "dev-intel" / "domain_token_savings"
_CODEBLOCKS_DIR = resource("data") / "dev-intel" / "primitive_codeblocks"
_DRAFTS_FILE = resource("data") / "dev-intel" / "aidevobserver_context_foundry" / "primitive_drafts.jsonl"

# ── persisted tiers ─────────────────────────────────────────────────────────────────────────────────────────
CURATED_PACK_DIR = _bpsi.PACK_DIR  # the 112K default — read only, NEVER overwritten here
FULLCORPUS_PACK_DIR = _bpsi._resource("catalog") / "knowledge-packs" / "data" / "primitive-search-index-fullcorpus"
RECEIPT_DIR = resource("data") / "dev-intel" / "full_corpus_search_index"
EMBED_OUT_DIRNAME = "primitive-embeddings-fullcorpus"  # under dist/ (build artifact; regenerated)

# ── measurement knobs (named, single-source) ────────────────────────────────────────────────────────────────
DEFAULT_TOP_K = 5           # per-query result depth for reach + precision (matches the existing benches)
DEFAULT_QUERY_SAMPLE = 400  # labelled queries per run (deterministic head; --sample-queries overrides)
PRECISION_TOLERANCE = 0.01  # P@1 drop below this counts as "no material regression" (verdict tolerance)


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Normalizers — one row of any namespace -> the slim search-doc card shape `build_search_doc` consumes.
# The code body is NEVER carried (memory + index bloat); primitive_id is the handle back to the source row.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _bb_str(blackbox: Any) -> str:
    """A card blackbox as a plain string (edge cards store {'does': ...}; others store a str)."""
    if isinstance(blackbox, dict):
        return str(blackbox.get("does") or "")
    return str(blackbox or "")


def _psc_text(psc: Any) -> str:
    """The intent-bearing text of a codeblock's ``problem_solution_core`` dict (fit/avoid/failure/composition +
    the human-action intent) — the code body is deliberately excluded."""
    if not isinstance(psc, dict):
        return str(psc or "")
    parts: list[str] = []
    for key in ("fit_when", "avoid_when", "failure_modes", "composition_notes"):
        val = psc.get(key)
        if isinstance(val, str):
            parts.append(val)
    hac = psc.get("human_action_core")
    if isinstance(hac, dict):
        for key in ("action_intent", "actor_role", "handoff_boundary"):
            val = hac.get(key)
            if isinstance(val, str):
                parts.append(val)
    return " ".join(parts)


def _slim(primitive_id: Any, title: Any, input_edge: Any, output_edge: Any, blackbox: Any,
          blocking_keys: Any, *, record_type: str = "", body_status: str = "",
          needs_review: bool = False, corpus_stage: str = "") -> dict[str, Any]:
    """The slim card: exactly the fields `build_search_doc` reads, plus a corpus_stage label + BOUNDARY. No
    ``code``, no ``mutations``, no ``generated_source`` — those never inform ranking and are the bulk of bytes."""
    return {
        "primitive_id": str(primitive_id or ""),
        "title": str(title or ""),
        "input_edge": input_edge if isinstance(input_edge, (str, dict)) else str(input_edge or ""),
        "output_edge": output_edge if isinstance(output_edge, (str, dict)) else str(output_edge or ""),
        "blackbox": blackbox,  # str or {"does": ...}; build_search_doc + _bb_str both handle either
        "blocking_keys": [k for k in (blocking_keys or []) if isinstance(k, (str, int))],
        "record_type": str(record_type or ""),
        "body_status": str(body_status or ""),
        "needs_review": bool(needs_review),
        "corpus_stage": corpus_stage,
        **BOUNDARY,
    }


def _norm_passthrough(card: dict[str, Any], corpus_stage: str) -> dict[str, Any]:
    """verified / edge / gap-fill — already carry title + edges + blackbox + blocking_keys."""
    return _slim(
        card.get("primitive_id") or card.get("origin_primitive_id"),
        card.get("title"), card.get("input_edge"), card.get("output_edge"),
        card.get("blackbox"), card.get("blocking_keys"),
        record_type=card.get("record_type", ""), body_status=card.get("body_status", ""),
        needs_review=bool(card.get("needs_review")), corpus_stage=corpus_stage,
    )


def _norm_codeblock(card: dict[str, Any], corpus_stage: str) -> dict[str, Any]:
    """seed codeblock — searchable text = title + edges + problem_solution_core + family + industry (NO code)."""
    core = " ".join(x for x in (_psc_text(card.get("problem_solution_core")),
                                str(card.get("family") or ""), str(card.get("industry") or "")) if x)
    return _slim(card.get("primitive_id") or card.get("codeblock_id"), card.get("title"),
                 card.get("input_edge"), card.get("output_edge"), core, [],
                 record_type=card.get("record_type", ""), corpus_stage=corpus_stage)


def _norm_draft(card: dict[str, Any], corpus_stage: str) -> dict[str, Any]:
    """draft — no blackbox; edges come from contract; searchable text = title + slug + edges."""
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    core = " ".join(str(x) for x in (card.get("title"), card.get("slug")) if x)
    return _slim(card.get("primitive_id"), card.get("title"), contract.get("input", ""),
                 contract.get("output", ""), core, [],
                 record_type=card.get("record_type", ""), corpus_stage=corpus_stage)


# ── (path, corpus_stage, normalizer) specs — codeblocks expanded via glob at call time ──────────────────────
CorpusSpec = tuple[Path, str, Callable[[dict[str, Any], str], dict[str, Any]]]

CURATED_SPECS: tuple[CorpusSpec, ...] = (
    (_EDGE_FOUNDRY / "verified_factory_primitive_cards.jsonl", "verified", _norm_passthrough),
    (_EDGE_FOUNDRY / "primitive_edge_cards.jsonl", "edge", _norm_passthrough),
)
_EXPANSION_FILE_SPECS: tuple[CorpusSpec, ...] = (
    (_STAGED / "template_minted_producer_cards.jsonl", "gap_fill", _norm_passthrough),
    (_STAGED / "template_minted_producer_cards_v2.jsonl", "gap_fill", _norm_passthrough),
    (_DRAFTS_FILE, "draft", _norm_draft),
)


def _codeblock_specs() -> list[CorpusSpec]:
    """One spec per codeblock JSONL file (recursive, sorted — deterministic order)."""
    return [(p, "seed_codeblock", _norm_codeblock)
            for p in sorted(_CODEBLOCKS_DIR.rglob("*.jsonl"))]


def all_specs(*, include_curated: bool = True, include_expansion: bool = True,
             include_codeblocks: bool = True) -> list[CorpusSpec]:
    """The chosen namespace specs. Baseline = curated only; full corpus = curated + expansion + codeblocks."""
    specs: list[CorpusSpec] = []
    if include_curated:
        specs += list(CURATED_SPECS)
    if include_expansion:
        specs += list(_EXPANSION_FILE_SPECS)
        if include_codeblocks:
            specs += _codeblock_specs()
    return specs


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# unify + dedup — streaming generators (never hold a whole namespace, never a code body).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def unify_corpus(specs: Iterable[CorpusSpec], *, cap: Optional[int] = None,
                 stats: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:
    """Stream every row of every spec, normalized to the slim search-doc card shape. ``cap`` (int) bounds the
    TOTAL rows (for cheap test builds); ``stats`` (dict) accumulates per-namespace raw counts. One row in memory
    at a time; code bodies are dropped by the normalizers, never yielded."""
    seen = 0
    # NB: `stats or {}` is WRONG here — an empty dict is falsy, so it would return a throwaway. Guard on `is not None`.
    per_ns: dict[str, int] = stats.setdefault("per_namespace_raw", {}) if stats is not None else {}
    for path, corpus_stage, norm in specs:
        for card in iter_jsonl_tolerant(path):
            doc = norm(card, corpus_stage)
            if not doc["primitive_id"]:
                continue  # a row with no id has no stable handle — skip (counted out of distinct)
            per_ns[corpus_stage] = per_ns.get(corpus_stage, 0) + 1
            yield doc
            seen += 1
            if cap is not None and seen >= cap:
                if stats is not None:
                    stats["total_raw"] = seen
                return
    if stats is not None:
        stats["total_raw"] = seen


def _content_key(doc: dict[str, Any]) -> str:
    """The canonical content key — title + edges + core text (blackbox), via canonical_id. Two rows that are the
    same capability (regardless of id/source) collapse to one distinct document."""
    inp, out = _bpsi._edge_text(doc)  # REUSE the same edge extraction the index build uses
    return canonical_id("fckey", doc.get("title", ""), inp, out, _bb_str(doc.get("blackbox")))


def dedup(docs: Iterable[dict[str, Any]], *, stats: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:
    """Yield the FIRST occurrence of each content key; drop exact-capability duplicates. ``stats`` accumulates
    distinct + duplicates. The ``seen`` set holds only 16-hex content digests (compact at 1.17M scale)."""
    seen: set[str] = set()
    distinct = 0
    duplicates = 0
    for doc in docs:
        key = _content_key(doc)[-16:]  # the hash suffix only — compact
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        distinct += 1
        yield doc
    if stats is not None:
        stats["distinct_after_dedup"] = distinct
        stats["duplicates_collapsed"] = duplicates


def build_tier_index(specs: Iterable[CorpusSpec], *, cap: Optional[int] = None,
                     stats: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Build an in-memory inverted index over the (deduped, unified) namespace specs by REUSING the
    contract-locked ``build_primitive_search_index.build_index`` — the same df-capped, mutation-excluding builder
    the curated 112K index uses. Streams: only slim docs + postings are retained, never a code body."""
    stats = stats if stats is not None else {}
    return _bpsi.build_index(dedup(unify_corpus(specs, cap=cap, stats=stats), stats=stats))


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Persistence — the full-corpus tier, in the SAME file format load_index/fast_search read (swappable by config).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def persist_tier(index: dict[str, Any], pack_dir: Path, *, date: str,
                 source_files: list[str], stats: dict[str, Any]) -> dict[str, Any]:
    """Write search_docs.jsonl + inverted_index.json + manifest.json to ``pack_dir`` (a SEPARATE dir from the
    curated default). Mirrors build_primitive_search_index's on-disk shape so ``_bpsi.load_index(pack_dir)`` and
    ``fast_search(..., index=...)`` work unchanged."""
    pack_dir.mkdir(parents=True, exist_ok=True)
    with (pack_dir / _bpsi.DOCS_FILE).open("w", encoding="utf-8") as handle:
        for doc in index["docs"]:
            handle.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    (pack_dir / _bpsi.POSTINGS_FILE).write_text(
        json.dumps({
            "n_docs": index["n_docs"], "df_cap": index["df_cap"],
            "postings": index["postings"], "idf": index["idf"],
            "dropped_high_df": index["dropped_high_df"],
        }, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    canonical = "\n".join(json.dumps(d, sort_keys=True, ensure_ascii=False) for d in index["docs"])
    posting_lengths = [len(v) for v in index["postings"].values()]
    manifest = {
        "record_type": "full_corpus_search_index_manifest",
        "schema_version": SCHEMA_VERSION,
        "pack_id": "primitive-search-index-fullcorpus",
        "generator": "scripts/full_corpus_search_index.py",
        "generated_utc": date,
        "source_files": source_files,
        "total_raw_rows": stats.get("total_raw"),
        "distinct_after_dedup": stats.get("distinct_after_dedup"),
        "duplicates_collapsed": stats.get("duplicates_collapsed"),
        "per_namespace_raw": stats.get("per_namespace_raw"),
        "n_docs": index["n_docs"],
        "doc_frequency_cap_fraction": _bpsi.DOC_FREQUENCY_CAP_FRACTION,
        "df_cap_absolute": index["df_cap"],
        "unique_indexed_tokens": len(index["postings"]),
        "tokens_dropped_by_df_cap": len(index["dropped_high_df"]),
        "max_posting_length": max(posting_lengths) if posting_lengths else 0,
        "mean_posting_length": round(sum(posting_lengths) / len(posting_lengths), 3) if posting_lengths else 0.0,
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "curated_default_index_dir": str(CURATED_PACK_DIR),  # untouched — the full tier is ADDITIVE
        **BOUNDARY,
    }
    (pack_dir / _bpsi.MANIFEST_FILE).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Honest measurement — REACH LIFT + PRECISION IMPACT on the SAME labelled queries over BOTH indexes.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _stage_of(primitive_id: str) -> str:
    """The corpus namespace a hit came from, read from its id prefix — so precision can attribute what a hit is
    (and, when a good hit is buried, WHICH namespace buried it)."""
    pid = str(primitive_id or "")
    if pid.startswith("prim:vf:"):
        return "verified"
    if pid.startswith("prim:candidate:"):
        return "draft"
    if pid.startswith("prim:"):
        return "edge"
    if pid.startswith("prim_seed_primitive_"):
        return "seed_codeblock"
    if pid.startswith("codefactory-"):
        return "gap_fill"
    return "other"


def load_labelled_queries(sample: Optional[int] = DEFAULT_QUERY_SAMPLE) -> list[dict[str, Any]]:
    """Labelled intent queries (query text + expected capability tokens) from the two on-disk suites. Each row:
    ``{"text": str, "expected": frozenset[str]}``. Deterministic head; missing files contribute nothing."""
    out: list[dict[str, Any]] = []
    saas = resource("data") / "dev-intel" / "session_emulation" / "saas_requirements_suite.jsonl"
    for row in iter_jsonl_tolerant(saas):
        toks = frozenset(str(t).lower() for t in (row.get("expected_tokens") or []))
        if row.get("query") and toks:
            out.append({"text": str(row["query"]), "expected": toks})
    devtask = resource("data") / "dev-intel" / "session_emulation" / "dev_task_prompt_corpus.jsonl"
    for row in iter_jsonl_tolerant(devtask):
        toks = frozenset(str(t).lower() for t in (row.get("expected_capabilities") or []))
        if row.get("prompt") and toks:
            out.append({"text": str(row["prompt"]), "expected": toks})
    return out[:sample] if sample else out


def _hit_relevant(hit: dict[str, Any], expected: frozenset[str]) -> bool:
    """A hit is relevant if any expected capability token appears in its title/edges (the same reach-proxy
    relevance the multi_path_coverage_bench uses — NOT a promotion of truth, a retrieval-quality proxy)."""
    text = " ".join(str(hit.get(f, "")) for f in ("title", "input_edge", "output_edge")).lower()
    return any(t in text for t in expected)


def measure_index(index: dict[str, Any], queries: list[dict[str, Any]], *, k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Reach + precision of one index on the labelled queries. Returns reach (≥1 hit), hit_rate (≥1 RELEVANT hit
    in top-k), P@1, P@k, MRR, and the top-1 corpus-stage distribution (what is winning)."""
    n = len(queries) or 1
    with_hit = 0
    with_relevant = 0
    p1 = 0
    pk_sum = 0.0
    mrr_sum = 0.0
    stage_top1: dict[str, int] = {}
    relevant_query_ids: set[int] = set()
    for qi, q in enumerate(queries):
        hits, _stats = _bpsi.search_with_stats(q["text"], k, index)
        if hits:
            with_hit += 1
            top_stage = _stage_of(hits[0].get("primitive_id"))
            stage_top1[top_stage] = stage_top1.get(top_stage, 0) + 1
        expected = q["expected"]
        rel_flags = [_hit_relevant(h, expected) for h in hits[:k]]
        if any(rel_flags):
            with_relevant += 1
            relevant_query_ids.add(qi)
        if rel_flags and rel_flags[0]:
            p1 += 1
        pk_sum += (sum(1 for f in rel_flags if f) / k)  # standard P@k (k in the denominator)
        first_rel = next((i for i, f in enumerate(rel_flags) if f), None)
        if first_rel is not None:
            mrr_sum += 1.0 / (first_rel + 1)
    return {
        "queries": n,
        "reach_any_hit": round(with_hit / n, 4),
        "hit_rate_relevant_in_topk": round(with_relevant / n, 4),
        "p_at_1": round(p1 / n, 4),
        "p_at_k": round(pk_sum / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "top1_stage_distribution": dict(sorted(stage_top1.items())),
        "_relevant_query_ids": relevant_query_ids,  # internal — dropped before the receipt is written
        "k": k,
    }


def compare_lift_precision(baseline: dict[str, Any], full: dict[str, Any]) -> dict[str, Any]:
    """The honest verdict: reach lift (upside) + precision impact (the risk), and a plain recommendation on
    whether the full-corpus index should become the default or stay a candidate tier behind a flag."""
    base_rel: set[int] = baseline.get("_relevant_query_ids", set())
    full_rel: set[int] = full.get("_relevant_query_ids", set())
    recovered = len(full_rel - base_rel)   # queries the baseline missed that the full corpus now covers
    lost = len(base_rel - full_rel)        # queries the baseline covered that the full corpus now MISSES (buried)
    p1_delta = round(full["p_at_1"] - baseline["p_at_1"], 4)
    pk_delta = round(full["p_at_k"] - baseline["p_at_k"], 4)
    mrr_delta = round(full["mrr"] - baseline["mrr"], 4)
    reach_delta = round(full["reach_any_hit"] - baseline["reach_any_hit"], 4)

    precision_regressed = (p1_delta < -PRECISION_TOLERANCE) or (mrr_delta < -PRECISION_TOLERANCE) or (lost > recovered)
    if precision_regressed:
        verdict = ("KEEP CURATED 112K AS DEFAULT; full-corpus is a CANDIDATE TIER behind a flag. Adding the "
                   "~1M seed/draft/gap-fill rows measurably BURIES good hits (P@1/MRR dropped or more labelled "
                   "queries lost their relevant top-hit than were gained). The full-corpus index is persisted "
                   "and searchable for reach/coverage, but must not replace the curated default for precision-"
                   "sensitive serving.")
    elif reach_delta > 0 and p1_delta >= -PRECISION_TOLERANCE:
        verdict = ("FULL-CORPUS IS SAFE TO SERVE (reach improved with no material precision loss). Still ship it "
                   "as the separate additive tier so the curated default stays the rollback target; promote to "
                   "default only after a labelled-precision gate on a larger gold set.")
    else:
        verdict = ("NEUTRAL: no material reach lift and no material precision loss on this labelled set. Keep the "
                   "curated 112K as default; the full-corpus tier adds recall headroom but no measured win here.")
    return {
        "reach_lift": {
            "baseline_reach_any_hit": baseline["reach_any_hit"],
            "full_reach_any_hit": full["reach_any_hit"],
            "reach_delta": reach_delta,
            "baseline_relevant_hit_rate": baseline["hit_rate_relevant_in_topk"],
            "full_relevant_hit_rate": full["hit_rate_relevant_in_topk"],
            "queries_recovered_by_full_corpus": recovered,
            "queries_lost_to_burial": lost,
        },
        "precision_impact": {
            "baseline_p_at_1": baseline["p_at_1"], "full_p_at_1": full["p_at_1"], "p_at_1_delta": p1_delta,
            "baseline_p_at_k": baseline["p_at_k"], "full_p_at_k": full["p_at_k"], "p_at_k_delta": pk_delta,
            "baseline_mrr": baseline["mrr"], "full_mrr": full["mrr"], "mrr_delta": mrr_delta,
            "full_top1_stage_distribution": full["top1_stage_distribution"],
            "baseline_top1_stage_distribution": baseline["top1_stage_distribution"],
            "tolerance": PRECISION_TOLERANCE,
            "precision_regressed": precision_regressed,
        },
        "verdict": verdict,
    }


def _strip_internal(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if not k.startswith("_")}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Optional embeddings over the expanded set (REUSE build_primitive_embeddings) — bounded, separate store dir.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def build_fullcorpus_embeddings(*, embed_limit: Optional[int] = None, embed_path: Optional[str] = None) -> dict[str, Any]:
    """Persist embeddings + feature records over the unified full corpus by REUSING build_primitive_embeddings.
    Bounded by ``embed_limit`` (a 1.17M float32 matrix is ~1.2GB, so a cap is the norm). Separate store dir so
    the curated ``dist/primitive-embeddings`` store is untouched."""
    from scripts import build_primitive_embeddings as _emb  # noqa: PLC0415
    specs = all_specs()
    cards = list(unify_corpus(specs, cap=embed_limit))  # slim cards (no code body) — card_embed_text uses blackbox
    out_dir = resource("dist") / EMBED_OUT_DIRNAME
    store = _emb.build(cards, embed_path=embed_path)
    manifest = _emb.persist(store, out_dir)
    return {"embedded": store["count"], "embed_model": store["embed_model"], "dim": store["dim"],
            "store_dir": str(out_dir), "manifest": manifest}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# The full --build run.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def run_build(*, cap: Optional[int] = None, sample_queries: Optional[int] = DEFAULT_QUERY_SAMPLE,
              k: int = DEFAULT_TOP_K, with_embeddings: bool = False, embed_limit: Optional[int] = None,
              embed_path: Optional[str] = None) -> dict[str, Any]:
    """Build the full-corpus index, persist it alongside the curated default, and measure reach + precision vs
    the 112K baseline. Peak memory is bounded by building the baseline FIRST and freeing it before the full run."""
    date = _dt.datetime.now(_dt.timezone.utc).isoformat()
    queries = load_labelled_queries(sample_queries)

    # Phase A — the 112K curated baseline (built the SAME way for an apples-to-apples comparison), measured, freed.
    print("[phase A] building curated baseline index (verified + edge) ...", flush=True)
    base_stats: dict[str, Any] = {}
    base_index = build_tier_index(CURATED_SPECS, cap=cap, stats=base_stats)
    print(f"[phase A] baseline n_docs={base_index['n_docs']}; measuring {len(queries)} labelled queries ...", flush=True)
    baseline_metrics = measure_index(base_index, queries, k=k)
    del base_index
    gc.collect()

    # Phase B — the full corpus (curated + seed + draft + gap-fill), persisted, measured. Peak memory lives here.
    print("[phase B] building FULL-CORPUS index (curated + seed codeblocks + drafts + gap-fill) ...", flush=True)
    full_stats: dict[str, Any] = {}
    full_index = build_tier_index(all_specs(), cap=cap, stats=full_stats)
    print(f"[phase B] full n_docs={full_index['n_docs']} "
          f"(raw={full_stats.get('total_raw')}, distinct={full_stats.get('distinct_after_dedup')}); persisting ...",
          flush=True)
    source_files = [str(p) for p, _s, _n in all_specs()][:8] + ["... + codeblock shards"]
    manifest = persist_tier(full_index, FULLCORPUS_PACK_DIR, date=date, source_files=source_files, stats=full_stats)
    full_metrics = measure_index(full_index, queries, k=k)

    embeddings_summary: Optional[dict[str, Any]] = None
    if with_embeddings:
        print(f"[phase C] embeddings over the expanded set (limit={embed_limit}) ...", flush=True)
        embeddings_summary = build_fullcorpus_embeddings(embed_limit=embed_limit, embed_path=embed_path)

    comparison = compare_lift_precision(baseline_metrics, full_metrics)
    distinct = full_stats.get("distinct_after_dedup", 0)
    total_raw = full_stats.get("total_raw", 0)
    receipt = {
        "record_type": "full_corpus_search_index_receipt",
        "schema_version": SCHEMA_VERSION,
        "generated_utc": date,
        "total_records": total_raw,
        "per_namespace_raw": full_stats.get("per_namespace_raw"),
        "distinct_after_dedup": distinct,
        "duplicates_collapsed": full_stats.get("duplicates_collapsed"),
        "distinct_rate": round(distinct / total_raw, 6) if total_raw else 0.0,
        "distinct_sample_generalizes": (full_stats.get("duplicates_collapsed", 0) / (total_raw or 1)) < 0.02,
        "indexed_count": full_index["n_docs"],
        "n_docs": full_index["n_docs"],
        "unique_indexed_tokens": len(full_index["postings"]),
        "df_cap_absolute": full_index["df_cap"],
        "baseline_curated_n_docs": base_stats.get("distinct_after_dedup"),
        "labelled_queries": len(queries),
        "baseline_metrics": _strip_internal(baseline_metrics),
        "full_metrics": _strip_internal(full_metrics),
        "lift": comparison["reach_lift"],
        "precision_impact": comparison["precision_impact"],
        "verdict": comparison["verdict"],
        "curated_index_dir": str(CURATED_PACK_DIR),
        "fullcorpus_index_dir": str(FULLCORPUS_PACK_DIR),
        "content_sha256": manifest["content_sha256"],
        "embeddings": embeddings_summary,
        **BOUNDARY,
    }
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    (RECEIPT_DIR / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                              encoding="utf-8")
    return receipt


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Self-test — offline, deterministic, mutation-gated (a small synthetic multi-namespace corpus).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _synthetic_specs(tmp: Path) -> tuple[list[CorpusSpec], Path]:
    """Write a tiny multi-namespace corpus (edge + seed codeblock + draft + gap-fill + an exact DUP) to tmp and
    return its specs. A seed-only token ('phytoplankton') proves seeds become searchable; the DUP proves dedup."""
    edge = tmp / "edge.jsonl"
    edge.write_text("\n".join(json.dumps(r) for r in [
        {"primitive_id": "prim:e001", "title": "Screen entity against OFAC sanctions",
         "input_edge": "EntityRecord", "output_edge": "SanctionScreeningResult",
         "blackbox": {"does": "Match an entity against the OFAC SDN sanctions watchlist."},
         "blocking_keys": ["sanctions", "ofac", "screening"], **BOUNDARY},
        {"primitive_id": "prim:e002", "title": "Deduplicate records",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch",
         "blackbox": {"does": "Cluster near-identical rows and keep one canonical row."}, **BOUNDARY},
    ]) + "\n", encoding="utf-8")
    seed = tmp / "seed.jsonl"
    seed.write_text("\n".join(json.dumps(r) for r in [
        {"primitive_id": "prim_seed_primitive_0000001", "codeblock_id": "cb:1",
         "title": "classify phytoplankton imagery",  # UNIQUE seed-only token
         "input_edge": "ImageBatch", "output_edge": "SpeciesLabelBatch",
         "code": "x" * 5000,  # a big body that must NOT be indexed
         "family": "marine_vision", "industry": "research",
         "problem_solution_core": {"fit_when": "Use to label plankton microscopy images.",
                                   "failure_modes": "class_imbalance"},
         "record_type": "primitive_codeblock_candidate", **BOUNDARY},
        {"primitive_id": "prim_seed_primitive_0000002", "title": "scaffold billing service",
         "input_edge": "UserIntent", "output_edge": "ProjectScaffold", "code": "y" * 5000,
         "family": "project_scaffold", "industry": "horizontal_saas",
         "problem_solution_core": {"fit_when": "Use for a reusable project scaffold."},
         "record_type": "primitive_codeblock_candidate", **BOUNDARY},
    ]) + "\n", encoding="utf-8")
    draft = tmp / "draft.jsonl"
    draft.write_text(json.dumps(
        {"primitive_id": "prim:candidate:surface-data-gov:dataset-descriptor",
         "title": "Data.gov dataset descriptor primitive", "slug": "data-gov.dataset-descriptor",
         "contract": {"input": "DatasetSource", "output": "DatasetDescriptor"},
         "record_type": "primitive_opportunity"}) + "\n", encoding="utf-8")
    gap = tmp / "gap.jsonl"
    gap.write_text("\n".join(json.dumps(r) for r in [
        {"primitive_id": "codefactory-aaaa1111", "title": "transform grants search response",
         "input_edge": "GrantsGovSearchResponse", "output_edge": "GrantsSearchHttpResponse",
         "blackbox": "Generated narrow transform.", "blocking_keys": ["grants", "transform"],
         "record_type": "code_factory_candidate_card", "needs_review": True, **BOUNDARY},
        # an EXACT capability duplicate of prim:e002 (different id/source) — dedup must collapse it
        {"primitive_id": "codefactory-dup00002", "title": "Deduplicate records",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch",
         "blackbox": "Cluster near-identical rows and keep one canonical row.",
         "record_type": "code_factory_candidate_card", **BOUNDARY},
    ]) + "\n", encoding="utf-8")
    specs: list[CorpusSpec] = [
        (edge, "edge", _norm_passthrough),
        (seed, "seed_codeblock", _norm_codeblock),
        (draft, "draft", _norm_draft),
        (gap, "gap_fill", _norm_passthrough),
    ]
    curated_only: list[CorpusSpec] = [(edge, "edge", _norm_passthrough)]
    return specs, edge, curated_only  # type: ignore[return-value]


def self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        specs, _edge, curated_only = _synthetic_specs(tmp)  # type: ignore[misc]

        # unify streams every namespace, normalized; the big `code` body is NEVER carried through
        stats: dict[str, Any] = {}
        unified = list(unify_corpus(specs, stats=stats))
        checks.append(("unify streams all namespaces (edge 2 + seed 2 + draft 1 + gap 2 = 7 raw rows)",
                       len(unified) == 7 and stats["total_raw"] == 7))
        checks.append(("code body is NOT carried into the unified doc (no multi-KB body in RAM/index)",
                       all("code" not in d for d in unified)
                       and all(len(json.dumps(d)) < 1000 for d in unified)))
        checks.append(("per-namespace raw counts recorded",
                       stats["per_namespace_raw"].get("seed_codeblock") == 2
                       and stats["per_namespace_raw"].get("edge") == 2))

        # dedup collapses the exact-capability duplicate (mutation gate: a no-op dedup keeps 6, this asserts 5)
        dstats: dict[str, Any] = {}
        deduped = list(dedup(unify_corpus(specs), stats=dstats))
        checks.append(("dedup collapses the exact-capability duplicate (7 raw -> 6 distinct)",
                       dstats["distinct_after_dedup"] == 6 and dstats["duplicates_collapsed"] == 1
                       and len(deduped) == 6))

        # build the full index; a SEED-ONLY token must be findable (mutation gate: drop seeds and this fails)
        full_stats: dict[str, Any] = {}
        full_index = build_tier_index(specs, stats=full_stats)
        seed_hits = _bpsi.fast_search("phytoplankton imagery species", 5, index=full_index)
        checks.append(("a SEED codeblock becomes findable (its unique token retrieves it)",
                       bool(seed_hits) and seed_hits[0]["primitive_id"] == "prim_seed_primitive_0000001"))
        checks.append(("the seed hit's edges are preserved for composition joins",
                       bool(seed_hits) and seed_hits[0]["input_edge"] == "ImageBatch"
                       and seed_hits[0]["output_edge"] == "SpeciesLabelBatch"))
        checks.append(("every indexed doc is candidate-only (serves_truth=false)",
                       all(d["candidate"] is True and d["serves_truth"] is False for d in full_index["docs"])))
        checks.append(("the code body's filler token never entered the inverted index",
                       "xxxxx" not in " ".join(full_index["postings"].keys())))

        # persistence round-trips through the REUSED load_index + fast_search (swappable tier)
        pack = tmp / "fullcorpus-index"
        persist_tier(full_index, pack, date="2026-07-08", source_files=["synthetic"], stats=full_stats)
        reloaded = _bpsi.load_index(pack)
        reload_hits = _bpsi.fast_search("ofac sanctions screening", 5, index=reloaded)
        checks.append(("persisted full-corpus tier round-trips (load_index + fast_search)",
                       bool(reload_hits) and reload_hits[0]["primitive_id"] == "prim:e001"))
        checks.append(("persisted to a SEPARATE dir — the curated default dir is untouched",
                       pack != CURATED_PACK_DIR and (pack / _bpsi.DOCS_FILE).exists()))

        # the lift + precision measure COMPUTES on both indexes (baseline curated-only vs full)
        queries = [
            {"text": "screen an entity against the OFAC sanctions list", "expected": frozenset({"sanction", "ofac", "screen"})},
            {"text": "classify phytoplankton imagery by species", "expected": frozenset({"phytoplankton", "classify", "species"})},
            {"text": "deduplicate my records", "expected": frozenset({"deduplicate", "dedup"})},
        ]
        base_index = build_tier_index(curated_only)
        base_m = measure_index(base_index, queries)
        full_m = measure_index(full_index, queries)
        cmp = compare_lift_precision(base_m, full_m)
        checks.append(("lift/precision measure computes real numbers in [0,1]",
                       0.0 <= full_m["p_at_1"] <= 1.0 and 0.0 <= full_m["reach_any_hit"] <= 1.0
                       and isinstance(cmp["verdict"], str) and len(cmp["verdict"]) > 20))
        checks.append(("full corpus recovers a query the 112K-shaped baseline could not (the phytoplankton seed)",
                       cmp["reach_lift"]["queries_recovered_by_full_corpus"] >= 1))
        checks.append(("precision_impact reports P@1/MRR deltas + the top-1 stage distribution",
                       "p_at_1_delta" in cmp["precision_impact"]
                       and "full_top1_stage_distribution" in cmp["precision_impact"]))

        # determinism: two builds of the same synthetic corpus produce a byte-identical doc set
        idx_a = build_tier_index(specs)
        idx_b = build_tier_index(specs)
        h = lambda ix: hashlib.sha256(  # noqa: E731
            "\n".join(json.dumps(d, sort_keys=True) for d in ix["docs"]).encode()).hexdigest()
        checks.append(("deterministic: identical corpus -> byte-identical index docs", h(idx_a) == h(idx_b)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - full_corpus_search_index: unify streams every namespace (edge/seed/draft/gap-fill) into the "
          "search-doc shape WITHOUT the code body, dedup collapses exact-capability duplicates, the REUSED "
          "df-capped builder indexes them into a SEPARATE persisted tier (curated 112K default untouched), a "
          "seed card becomes findable + candidate-only, persistence round-trips, and reach-lift + precision-"
          "impact are measured on the same labelled queries over both indexes. serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true", help="the full ~1.17M run (index + persist + measure)")
    ap.add_argument("--query", metavar="TEXT", default=None,
                    help="run fast_search against the PERSISTED full-corpus tier and print hits")
    ap.add_argument("--limit", type=int, default=None, help="cap total rows (cheap test build; default: all)")
    ap.add_argument("--sample-queries", type=int, default=DEFAULT_QUERY_SAMPLE, help="labelled queries to measure")
    ap.add_argument("--k", type=int, default=DEFAULT_TOP_K, help="top-k depth for reach + precision")
    ap.add_argument("--embeddings", action="store_true", help="also persist embeddings over the expanded set")
    ap.add_argument("--embed-limit", type=int, default=None, help="cap rows embedded (a 1.17M matrix is ~1.2GB)")
    ap.add_argument("--embed-path", default=None, help="embed backend (model2vec|ollama|tokens); default: best local")
    args = ap.parse_args(argv)

    if args.query:
        index = _bpsi.load_index(FULLCORPUS_PACK_DIR)
        results, stats = _bpsi.search_with_stats(args.query, args.k, index)
        print(json.dumps({"stats": stats, "results": results}, indent=2, ensure_ascii=False))
        return 0
    if args.self_test and not args.build:
        return self_test()
    if args.build:
        receipt = run_build(cap=args.limit, sample_queries=args.sample_queries, k=args.k,
                            with_embeddings=args.embeddings, embed_limit=args.embed_limit, embed_path=args.embed_path)
        summary = {k: receipt[k] for k in (
            "total_records", "distinct_after_dedup", "duplicates_collapsed", "distinct_rate", "indexed_count",
            "n_docs", "unique_indexed_tokens", "per_namespace_raw", "lift", "precision_impact", "verdict",
            "fullcorpus_index_dir") if k in receipt}
        print("\n" + json.dumps(summary, indent=2, ensure_ascii=False))
        print("\nrunning self-test to confirm the module is green ...")
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
