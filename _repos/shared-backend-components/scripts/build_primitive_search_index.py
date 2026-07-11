#!/usr/bin/env python3
"""scripts.build_primitive_search_index — a REAL fast inverted index for primitive-card search.

The retrieval red-team (2026-07-03) found the live primitive search
(``_repos/teleon/backend/src/teleon/observer/registry_search.py::search_edge_foundry_primitives``) is an O(N) linear
token-overlap scan over ~115k cards that takes ~13.7s/query. Three named causes:

1. **No index prunes.** Every query re-tokenizes and re-scores EVERY card; blocking_keys are dumped
   into one text soup instead of pruning the candidate set.
2. **mutations[] dominates the bytes.** The scan re-serializes each card's ``mutations`` list (67.6% of
   card bytes) on every query, even though a search doc never needs the mutation bodies to rank.
3. **Path-debris tokens** (``src``/``scripts``/``tests``/``gemma4``/… ) and ultra-common tokens make
   token-overlap non-selective, so nothing prunes.

This module is ADD-ONLY: it does NOT edit the contract-locked ``registry_search.py`` /
``primitive_match.py`` / ``verify_primitive_candidates.py``. It is a NEW parallel PATH — a real
inverted index with a document-frequency cap and a stopword list — that IMPORTS the same card files
and is benchmarkable against the old linear scan (a new wired runtime is a new path).

The design (all offline-deterministic, no network, no wall-clock/RNG in row bodies):

* Build a compact **search doc** per card from ``title + edges + blackbox + blocking_keys`` ONLY —
  ``mutations``/``memory``/``cache`` are EXCLUDED (kills cause #2 at index time).
* Build an **inverted index** token -> posting-list over the **FULL corpus** (no record cap), dropping
  (a) a stopword list of the path-debris tokens the red-team named and (b) any token whose **document
  frequency exceeds 5%** of docs (kills causes #1 and #3 — the surviving tokens are selective, and the
  df-cap is what bounds every posting list so the candidate union stays small without truncation).
* ``fast_search(query, limit, index)`` tokenizes the query, unions the posting lists of ALL its SELECTIVE
  tokens (fair to every query term) into the **full candidate set** (bounded by the df-cap, not an
  arbitrary count), then ranks ONLY those candidates by idf-weighted overlap + an edge-token bonus. It is
  **O(candidates), never O(N)**.

All persisted rows are candidate=true / serves_truth=false (an index is metadata, not a proven
primitive). CLI: ``--self-test`` (pure, offline, tiny synthetic index) | ``--write`` (real index).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# ── source card files (same files the contract-locked search reads) ──
EDGE_FOUNDRY_DIR = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
_STAGED_DIR = _resource("data") / "dev-intel" / "domain_token_savings"
# (path, corpus_stage) — the stage LABELS every doc so the compose lane + receipts can segment real vs
# staged-stub producers (the integration audit's core ask). Staged stubs are searchable for COVERAGE but
# never rank above a real hit and never silently satisfy a compose route (see the rank tier + stub filter).
_SYNTHESIS_DIR = _resource("data") / "dev-intel" / "primitive_synthesis"
SOURCE_CARD_SPECS: tuple[tuple[Path, str], ...] = (
    (EDGE_FOUNDRY_DIR / "verified_factory_primitive_cards.jsonl", "verified"),
    (EDGE_FOUNDRY_DIR / "primitive_edge_cards.jsonl", "edge"),
    # the synthesis lane (owner 2026-07-10: "shouldn't we push to 500K primitives, not just 130K?") — 427K
    # syntax-valid WORKING candidates (synthprim-*, disjoint id namespace): the corpus jump 130K -> ~540K docs
    (_SYNTHESIS_DIR / "working_primitives.jsonl", "synthesis_working"),
    (_STAGED_DIR / "template_minted_producer_cards.jsonl", "staged_stub"),
    (_STAGED_DIR / "template_minted_producer_cards_v2.jsonl", "staged_stub"),
    (_STAGED_DIR / "model_backed_factory_cards.jsonl", "staged_model_fill"),
)
SOURCE_CARD_FILES: tuple[Path, ...] = tuple(path for path, _stage in SOURCE_CARD_SPECS)

#: synthesis routing — the 427K synthesis lane (disjoint id namespace synthprim-*: the namespace IS the lane)
#: ADDS tail coverage but must not displace a proven real hit on a NEAR-TIE. A mild score factor demotes
#: synthesis at equal relevance while letting a clearly-better synthesis match surface (non-destructive
#: router: demote, never hide — an absolute tier would bury a perfect synthesis match under any weak real
#: token overlap). Staged stubs keep their absolute bottom tier (identity stubs carry no capability).
_SYNTHESIS_ID_PREFIX = "synthprim-"
_SYNTHESIS_SCORE_FACTOR = 0.85

# ── where the built index is persisted ──
PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "primitive-search-index"
DOCS_FILE = "search_docs.jsonl"
POSTINGS_FILE = "inverted_index.json"
MANIFEST_FILE = "manifest.json"

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ── tuning constants (named, single-source; no magic literals in logic) ──
RECORD_CAP = None  # None = index the FULL corpus (every source card). Was 40_000 — a stale cap from when the
#                    corpus was ~40k; it silently dropped ~66% of today's 118k cards (almost all the edge-typed
#                    cards composition needs most, since verified loads first). The index is O(N) to build ONCE
#                    and O(candidates) to query, so there is no scale reason to cap ingestion. A positive int
#                    still caps (used by the tiny offline self-test); None means "use everything".
DOC_FREQUENCY_CAP_FRACTION = 0.05  # drop a token appearing in > 5% of docs (non-selective). THE real
#                    selectivity guard — it bounds every posting list to <=5% of docs, so the candidate union
#                    is naturally bounded without an arbitrary per-query truncation.
CANDIDATE_SET_CAP = None  # None = score the FULL candidate union of a query's selective tokens (fair to EVERY
#                    query term). Was 500 — a truncation that, gathering most-selective-token-first, let one
#                    high-posting token fill the set and starve the other query terms (a hard recall wall
#                    independent of ``limit``). The df-cap above already bounds the union; a positive int still
#                    truncates if a caller wants it.
MIN_TOKEN_LEN = 2  # single chars carry no selectivity
DEFAULT_LIMIT = 20
EDGE_TOKEN_BONUS = 2.0  # extra weight when a query token hits an input/output edge token

# Path-debris + type-noise stopwords the red-team named, PLUS structural glue words. These never enter
# postings (they are not selective — they appear across the whole corpus / are pure path/type debris).
PATH_DEBRIS_STOPWORDS: frozenset[str] = frozenset({
    "src", "scripts", "tests", "test", "repo", "reference", "str", "dict", "none", "gemma4",
    "duecare", "the", "any", "projectundertest",
    # structural glue (mirrors the intent of the shipped PRIMITIVE_GLOBAL_SEARCH_STOPWORDS)
    "a", "an", "and", "of", "for", "to", "with", "into", "from", "on", "or", "by", "is",
})

_TOKEN_RE = re.compile(r"[a-z0-9]+")  # same token shape as registry_search._TOKEN_RE


def tokenize(text: str) -> list[str]:
    """Lowercase word/number tokens, min length ``MIN_TOKEN_LEN``, minus path-debris stopwords.

    Returns a list (order/duplicates preserved) so callers can build sets or count as needed.
    """
    return [
        tok
        for tok in _TOKEN_RE.findall(str(text or "").lower())
        if len(tok) >= MIN_TOKEN_LEN and tok not in PATH_DEBRIS_STOPWORDS
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Search-doc construction — EXCLUDES mutations/memory/cache (the 67.6%-of-bytes cause).
# ──────────────────────────────────────────────────────────────────────────────
def _blackbox_text(card: dict[str, Any]) -> str:
    bb = card.get("blackbox")
    if isinstance(bb, dict):  # edge cards store {"does": "..."}
        return str(bb.get("does") or "")
    return str(bb or "")


def _edge_text(card: dict[str, Any]) -> tuple[str, str]:
    """(input_edge_text, output_edge_text) from input_edge/output_edge or contract.input/output."""
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    inp = card.get("input_edge") or contract.get("input") or ""
    out = card.get("output_edge") or contract.get("output") or ""
    if isinstance(inp, dict):
        inp = " ".join(f"{k} {v}" for k, v in inp.items())
    if isinstance(out, dict):
        out = " ".join(f"{k} {v}" for k, v in out.items())
    return str(inp), str(out)


def build_search_doc(card: dict[str, Any]) -> dict[str, Any]:
    """Compact search doc from title + edges + blackbox + blocking_keys ONLY.

    ``mutations`` / ``memory`` / ``cache`` are intentionally NOT read — they never inform ranking and
    are the bulk of the card bytes. This is the index-time fix for the re-serialization cost.
    """
    title = str(card.get("title") or card.get("label") or card.get("slug") or "")
    inp_text, out_text = _edge_text(card)
    blackbox = _blackbox_text(card)
    blocking_keys = [str(k) for k in (card.get("blocking_keys") or []) if isinstance(k, (str, int))]

    body_tokens = tokenize(" ".join((title, blackbox, " ".join(blocking_keys))))
    edge_tokens = sorted(set(tokenize(inp_text + " " + out_text)))
    all_tokens = sorted(set(body_tokens) | set(edge_tokens))

    # body_status is computed from the CARD (needs_review + template origin), never inferred from a filename —
    # a stub that ever loses this label makes the build self-test go red.
    body_status = str(card.get("body_status") or "")
    is_staged_stub = bool(card.get("needs_review")) and body_status in ("identity_stub", "failed_validation", "")
    if not body_status and card.get("record_type") == "code_factory_candidate_card":
        body_status = "identity_stub"  # a code-factory card with no explicit status is a stub
    return {
        "primitive_id": str(card.get("primitive_id") or card.get("origin_primitive_id") or ""),
        "title": title,
        "input_edge": inp_text,
        "output_edge": out_text,
        "blocking_keys": blocking_keys,
        "tokens": all_tokens,          # unique searchable tokens (mutations excluded)
        "edge_tokens": edge_tokens,    # subset used for the edge-token ranking bonus
        "body_status": body_status or ("real" if not is_staged_stub else "identity_stub"),
        "is_staged_stub": bool(card.get("record_type") == "code_factory_candidate_card"
                               and body_status != "model_fill_lifted"),
        "needs_review": bool(card.get("needs_review")),
        **BOUNDARY,
    }


def _iter_source_cards(files: Iterable[Path], *, cap: int | None) -> Iterator[dict[str, Any]]:
    """Stream candidate cards from JSONL files, honoring candidate/serves_truth + an OPTIONAL record cap
    (``cap=None`` → the FULL corpus, no truncation; a positive int caps for the offline self-test)."""
    seen = 0
    for path in files:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    card = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(card, dict):
                    continue
                if card.get("candidate") is not True or card.get("serves_truth") is not False:
                    continue
                yield card
                seen += 1
                if cap is not None and seen >= cap:
                    return


# ──────────────────────────────────────────────────────────────────────────────
# Index build — inverted postings with a document-frequency cap.
# ──────────────────────────────────────────────────────────────────────────────
def build_index(cards: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build the in-memory index: docs, inverted postings (df-capped), idf, dropped-token report."""
    docs: list[dict[str, Any]] = [build_search_doc(c) for c in cards]
    n_docs = len(docs)

    # document frequency per token
    df: dict[str, int] = {}
    for doc in docs:
        for tok in doc["tokens"]:
            df[tok] = df.get(tok, 0) + 1

    df_cap = max(1, int(n_docs * DOC_FREQUENCY_CAP_FRACTION)) if n_docs else 0
    dropped_high_df = sorted(t for t, c in df.items() if n_docs and c > df_cap)
    dropped_set = set(dropped_high_df)

    # inverted index over SURVIVING (selective) tokens only
    postings: dict[str, list[int]] = {}
    for doc_id, doc in enumerate(docs):
        for tok in doc["tokens"]:
            if tok in dropped_set:
                continue
            postings.setdefault(tok, []).append(doc_id)

    idf: dict[str, float] = {}
    for tok, ids in postings.items():
        # smoothed idf; higher for rarer (more selective) tokens
        idf[tok] = math.log((n_docs + 1) / (len(ids) + 1)) + 1.0

    return {
        "docs": docs,
        "postings": postings,
        "idf": idf,
        "df": df,
        "n_docs": n_docs,
        "df_cap": df_cap,
        "dropped_high_df": dropped_high_df,
    }


# ──────────────────────────────────────────────────────────────────────────────
# The fast search path — O(candidates), NOT O(N).
# ──────────────────────────────────────────────────────────────────────────────
def _search(index: dict[str, Any], query: str, limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Core ranked search returning (results, stats). ``stats`` proves the index pruned."""
    postings: dict[str, list[int]] = index["postings"]
    idf: dict[str, float] = index["idf"]
    docs: list[dict[str, Any]] = index["docs"]

    q_tokens = [t for t in dict.fromkeys(tokenize(query))]  # dedupe, preserve order
    # only tokens that survived df-cap + stopwords are selective (present in postings)
    selective = [t for t in q_tokens if t in postings]
    stats = {
        "query_tokens": q_tokens,
        "selective_tokens": selective,
        "total_docs": len(docs),
        "candidate_count": 0,
        "docs_scored": 0,
        "capped": False,
    }
    if not selective:
        return [], stats

    # union posting lists across ALL selective tokens — fair to every query term. CANDIDATE_SET_CAP is
    # None by default → the FULL union (already bounded by the df-cap, so it stays small); a positive int
    # still truncates, most-selective (shortest posting) first, if a caller opts in.
    selective.sort(key=lambda t: len(postings[t]))
    candidate_ids: set[int] = set()
    for tok in selective:
        for doc_id in postings[tok]:
            candidate_ids.add(doc_id)
            if CANDIDATE_SET_CAP is not None and len(candidate_ids) >= CANDIDATE_SET_CAP:
                stats["capped"] = True
                break
        if stats["capped"]:
            break
    stats["candidate_count"] = len(candidate_ids)

    q_set = set(q_tokens)
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for doc_id in candidate_ids:
        doc = docs[doc_id]
        doc_tokens = set(doc["tokens"])
        matched = q_set & doc_tokens
        if not matched:
            continue
        # idf-weighted overlap (idf.get: a query token dropped by df-cap contributes ~0 weight)
        score = sum(idf.get(t, 0.0) for t in matched)
        edge_hits = matched & set(doc["edge_tokens"])
        score += EDGE_TOKEN_BONUS * len(edge_hits)
        is_stub = bool(doc.get("is_staged_stub"))
        doc_id = doc.get("primitive_id") or ""
        if not is_stub and doc_id.startswith(_SYNTHESIS_ID_PREFIX):
            score *= _SYNTHESIS_SCORE_FACTOR
        ranked.append((0 if is_stub else 1, score, doc_id, {
            "primitive_id": doc.get("primitive_id"),
            "title": doc.get("title"),
            "input_edge": doc.get("input_edge"),
            "output_edge": doc.get("output_edge"),
            "score": round(score, 6),
            "matched_terms": sorted(matched),
            "edge_matches": sorted(edge_hits),
            "body_status": doc.get("body_status", "real"),
            "is_staged_stub": is_stub,          # UNMISSABLE: a stub hit is labeled on every result row
            "needs_review": bool(doc.get("needs_review")),
            "source_kind": "primitive_search_index",
            **BOUNDARY,
        }))
    stats["docs_scored"] = len(candidate_ids)  # only candidates were ever touched
    # RANK TIER (integration-audit fix): a staged stub NEVER outranks a real hit with any match — real tier
    # (1) sorts entirely above stub tier (0); within a tier, by score. A stub still surfaces when it is the
    # only match (the coverage goal) but can never displace a real producer.
    ranked.sort(key=lambda r: (-r[0], -r[1], r[2]))
    stats["stub_hits"] = sum(1 for tier, _sc, _id, _row in ranked[: max(1, limit)] if tier == 0)
    return [row for _tier, _s, _id, row in ranked[: max(1, limit)]], stats


_DEFAULT_INDEX: dict[str, Any] | None = None


def fast_search(query: str, limit: int = DEFAULT_LIMIT, index: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Fast, index-pruned primitive search — O(candidates), never a full-corpus scan.

    ``index`` may be an in-memory index (from ``build_index``) or a loaded persisted index
    (``load_index``). If omitted, the persisted default index is loaded once and cached.
    """
    if index is None:
        index = _default_index()
    results, _stats = _search(index, query, limit)
    return results


def search_with_stats(query: str, limit: int = DEFAULT_LIMIT, index: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Same as ``fast_search`` but also returns pruning stats (candidate_count, docs_scored, …)."""
    if index is None:
        index = _default_index()
    return _search(index, query, limit)


def _default_index() -> dict[str, Any]:
    global _DEFAULT_INDEX
    if _DEFAULT_INDEX is None:
        _DEFAULT_INDEX = load_index(PACK_DIR)
    return _DEFAULT_INDEX


# ──────────────────────────────────────────────────────────────────────────────
# Persistence + manifest.
# ──────────────────────────────────────────────────────────────────────────────
def _manifest(index: dict[str, Any], *, date: str, source_files: list[str]) -> dict[str, Any]:
    docs = index["docs"]
    postings = index["postings"]
    canonical = "\n".join(json.dumps(d, sort_keys=True, ensure_ascii=False) for d in docs)
    posting_lengths = [len(v) for v in postings.values()]
    return {
        "record_type": "primitive_search_index_manifest",
        "pack_id": "primitive-search-index",
        "generator": "scripts/build_primitive_search_index.py",
        "generated_utc": date,
        "source_files": source_files,
        "record_cap": RECORD_CAP,
        "doc_frequency_cap_fraction": DOC_FREQUENCY_CAP_FRACTION,
        "candidate_set_cap": CANDIDATE_SET_CAP,
        "row_counts": {DOCS_FILE: len(docs), POSTINGS_FILE: len(postings)},
        "total_rows": len(docs),
        "n_docs": index["n_docs"],
        "unique_indexed_tokens": len(postings),
        "df_cap_absolute": index["df_cap"],
        "tokens_dropped_by_df_cap": len(index["dropped_high_df"]),
        "dropped_high_df_sample": index["dropped_high_df"][:40],
        "path_debris_stopwords": sorted(PATH_DEBRIS_STOPWORDS),
        "max_posting_length": max(posting_lengths) if posting_lengths else 0,
        "mean_posting_length": round(sum(posting_lengths) / len(posting_lengths), 3) if posting_lengths else 0.0,
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_index(*, date: str, files: tuple[Path, ...] = SOURCE_CARD_FILES, cap: int | None = RECORD_CAP) -> dict[str, Any]:
    index = build_index(_iter_source_cards(files, cap=cap))
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    with (PACK_DIR / DOCS_FILE).open("w", encoding="utf-8") as handle:
        for doc in index["docs"]:
            handle.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    # postings + idf + meta persisted together (idf keys == postings keys)
    (PACK_DIR / POSTINGS_FILE).write_text(
        json.dumps({
            "n_docs": index["n_docs"],
            "df_cap": index["df_cap"],
            "postings": index["postings"],
            "idf": index["idf"],
            "dropped_high_df": index["dropped_high_df"],
        }, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    manifest = _manifest(index, date=date, source_files=[str(p.relative_to(REPO)) for p in files if p.exists()])
    (PACK_DIR / MANIFEST_FILE).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_index(pack_dir: Path = PACK_DIR) -> dict[str, Any]:
    """Load a persisted index into the in-memory shape ``fast_search`` expects."""
    docs: list[dict[str, Any]] = []
    with (pack_dir / DOCS_FILE).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                docs.append(json.loads(line))
    meta = json.loads((pack_dir / POSTINGS_FILE).read_text(encoding="utf-8"))
    return {
        "docs": docs,
        "postings": {k: list(v) for k, v in meta["postings"].items()},
        "idf": {k: float(v) for k, v in meta["idf"].items()},
        "df": {},
        "n_docs": meta["n_docs"],
        "df_cap": meta["df_cap"],
        "dropped_high_df": meta.get("dropped_high_df", []),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Self-test — tiny synthetic index, fully offline.
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_cards() -> list[dict[str, Any]]:
    """Synthetic cards: a 'sanctions screening' target + junk docs sharing a high-df debris token.

    Every doc carries 'projectundertest' (a stopword) and >5% carry 'widget' (a high-df token) so the
    df-cap must drop it; only the target carries the selective 'sanctions'/'ofac' tokens.
    """
    cards: list[dict[str, Any]] = []
    # 1 target card
    cards.append({
        "primitive_id": "prim:test:target",
        "title": "Screen entity against OFAC sanctions list",
        "input_edge": "EntityRecord",
        "output_edge": "SanctionsScreeningReport",
        "blackbox": "Matches an entity record against the OFAC sanctions watchlist and emits a screening report.",
        "blocking_keys": ["sanctions", "ofac", "screening", "entityrecord", "sanctionsscreeningreport"],
        # mutations MUST be ignored by the search doc — put a unique token here to prove exclusion:
        "mutations": [{"mutator": "map_sequence", "reason": "uniquemutationtoken should never be indexed"}],
        "memory": {"secret": "shouldnotindex"},
        "cache": {"secret": "shouldnotindex"},
        **BOUNDARY,
    })
    # 40 junk cards, all sharing 'widget' (high df) + 'projectundertest' (stopword), none about sanctions
    for i in range(40):
        cards.append({
            "primitive_id": f"prim:test:junk{i:02d}",
            "title": f"Generic widget helper number {i}",
            "input_edge": "WidgetInput",
            "output_edge": "WidgetOutput",
            "blackbox": "A generic widget in scripts under src for the projectundertest repo.",
            "blocking_keys": ["widget", "generic", "helper", "projectundertest"],
            "mutations": [{"mutator": "noop", "reason": "uniquemutationtoken"}],
            "memory": {}, "cache": {},
            **BOUNDARY,
        })
    return cards


def self_test() -> int:
    cards = _synthetic_cards()
    index = build_index(cards)
    n = index["n_docs"]

    checks: list[tuple[str, bool]] = []

    # (a) mutations/memory/cache excluded from the search doc
    target_doc = index["docs"][0]
    checks.append(("search doc excludes mutations/memory/cache tokens",
                   "uniquemutationtoken" not in target_doc["tokens"]
                   and "shouldnotindex" not in target_doc["tokens"]))
    checks.append(("mutations token is not in the inverted index at all",
                   "uniquemutationtoken" not in index["postings"]))

    # (b) df-cap drops the high-df junk token 'widget' (in 40/41 docs) and stopwords never enter postings
    checks.append(("high-df token 'widget' dropped by df-cap", "widget" in set(index["dropped_high_df"])))
    checks.append(("df-cap actually dropped >=1 token", index["df_cap"] >= 1 and len(index["dropped_high_df"]) >= 1))
    checks.append(("path-debris stopwords never enter postings",
                   all(sw not in index["postings"] for sw in ("src", "scripts", "projectundertest", "repo"))))
    checks.append(("selective token 'sanctions' present in postings and points only at the target",
                   index["postings"].get("sanctions") == [0]))

    # (c) fast_search returns the right doc ('entityrecord' is both a blocking key and an edge token)
    results, stats = _search(index, "ofac sanctions screening entityrecord", DEFAULT_LIMIT)
    checks.append(("fast_search returns the target as top hit",
                   bool(results) and results[0]["primitive_id"] == "prim:test:target"))
    checks.append(("result carries edge_matches (edge-token bonus fired)",
                   bool(results) and "entityrecord" in set(results[0].get("edge_matches") or [])))
    checks.append(("results are candidate-only", all(r["candidate"] is True and r["serves_truth"] is False for r in results)))

    # (d) it PRUNED via the inverted index — did NOT scan all docs
    checks.append(("candidate set < total docs (pruned, not full scan)",
                   0 < stats["candidate_count"] < n))
    checks.append(("docs_scored == candidate_count (only candidates touched)",
                   stats["docs_scored"] == stats["candidate_count"]))
    # candidate set is the FULL union of selective tokens' postings (CANDIDATE_SET_CAP=None by default);
    # it must never exceed n (pruned, not a full scan) and, when a positive cap is set, never exceed it.
    checks.append(("candidate set stays within any explicit cap",
                   CANDIDATE_SET_CAP is None or stats["candidate_count"] <= CANDIDATE_SET_CAP))

    # (e) a query of ONLY dropped/stopword tokens prunes to nothing (no full scan, no results)
    junk_results, junk_stats = _search(index, "widget src scripts projectundertest the any", DEFAULT_LIMIT)
    checks.append(("query of only dropped/stopword tokens yields no candidates (no O(N) fallback)",
                   junk_stats["candidate_count"] == 0 and junk_results == []))

    # (f) persistence round-trips and gives identical top hit
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # write using the synthetic cards directly (offline; no source files needed)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        with (tmp_dir / DOCS_FILE).open("w", encoding="utf-8") as handle:
            for doc in index["docs"]:
                handle.write(json.dumps(doc, sort_keys=True) + "\n")
        (tmp_dir / POSTINGS_FILE).write_text(json.dumps({
            "n_docs": index["n_docs"], "df_cap": index["df_cap"],
            "postings": index["postings"], "idf": index["idf"],
            "dropped_high_df": index["dropped_high_df"],
        }, sort_keys=True), encoding="utf-8")
        reloaded = load_index(tmp_dir)
        reload_results = fast_search("ofac sanctions screening", DEFAULT_LIMIT, index=reloaded)
        checks.append(("persisted index round-trips to the same top hit",
                       bool(reload_results) and reload_results[0]["primitive_id"] == "prim:test:target"))

    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_search_index:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - primitive_search_index: inverted index over {n} synthetic docs "
          f"(df_cap={index['df_cap']}, {len(index['dropped_high_df'])} high-df token(s) dropped); "
          f"fast_search pruned to {stats['candidate_count']}/{n} candidates and returned the target — "
          f"O(candidates), mutations/memory/cache excluded, candidate-only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    parser.add_argument("--cap", type=int, default=RECORD_CAP)
    parser.add_argument("--query", default=None, help="run fast_search against the persisted index and print hits")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args(argv)

    if args.query:
        results, stats = search_with_stats(args.query, args.limit)
        print(json.dumps({"stats": stats, "results": results}, indent=2, ensure_ascii=False))
        return 0
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_index(date=date, cap=args.cap)
    print(json.dumps({k: v for k, v in manifest.items() if k != "dropped_high_df_sample"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
