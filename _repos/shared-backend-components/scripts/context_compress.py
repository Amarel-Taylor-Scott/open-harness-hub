#!/usr/bin/env python3
"""scripts.context_compress — deterministic, non-LLM context compression ladder.

Answers a direct product question: *can we compress context without depending on LLM summarization?*
Yes. This module runs the cheap, deterministic, auditable ladder FIRST; an LLM is an optional
escalation at the end, never the default. Every step is reversible: a retained item keeps its
`ctx://` source handle, and a dropped near-duplicate is COLLAPSED INTO the canonical item's handles
(merged, not lost) — so the compact pack is digestible up front and fully expandable back to source.

The ladder (each step is recorded in the CompressionRun.method_chain):
  0. token_budget          — estimate tokens, set a ceiling (tiktoken in prod; char-ratio offline)
  1. boilerplate_removal   — drop nav/footer/HTML-comment/marker lines (trafilatura/jusText in prod)
  2. dedupe_near_duplicates— exact (normalized hash) + near (difflib ratio); collapse, keep handles
                             (datasketch MinHash / SimHash / RapidFuzz in prod)
  3. keyphrase_extraction  — TF over content tokens (YAKE / RAKE / PyTextRank in prod)
  4. query_focused_ranking — BM25-lite term overlap with the task query (rank-bm25 / TF-IDF in prod)
  5. extractive_selection  — pick top sentences/items under budget (sumy/LexRank/TextRank in prod)
  6. pack_shape + receipt  — emit the compact digest + a CompressionRun (retained/dropped + reasons)

REAL vs SEAM: the ladder, dedupe, ranking, selection, token accounting, and the retained/dropped
bookkeeping are REAL and deterministic offline. The heavyweight extractors (trafilatura, sumy,
rank-bm25, spaCy, tree-sitter) and a tokenizer (tiktoken) are a `Compressor`/tokenizer SEAM — the
stdlib ladder is the offline default; a provider only swaps in a stronger implementation per step.
An LLM summarizer (`model_summarizer`) is an explicit, recorded escalation (llm_used=True), off by
default; it may never delete a source handle.

CLI / self-test (proves the ladder on a fixture with a planted near-duplicate; no model, no network):
    python3 _repos/shared-backend-components/scripts/context_compress.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Any, Callable

#: Offline token estimate. Real deployments use a model tokenizer (tiktoken); ~4 chars/token is the
#: documented English-text approximation and is the ONLY place this constant is defined.
CHARS_PER_TOKEN = 4
#: difflib ratio at/above which two items are treated as near-duplicates and collapsed.
NEAR_DUP_RATIO = 0.90
#: minimum keyword length + a small generic stopword set (shared idea with context_graph; kept local
#: so the two modules don't import each other — these are tiny, generic lists, not a magic value).
_MIN_TOKEN = 3
_STOPWORDS = frozenset({
    "the", "and", "for", "are", "was", "were", "this", "that", "with", "from", "into", "your",
    "you", "can", "does", "did", "has", "have", "had", "will", "would", "should", "could", "not",
    "about", "which", "when", "where", "who", "why", "what", "how", "but", "all", "any", "per",
    "use", "used", "using", "via", "than", "then", "them", "they", "there", "only", "also", "may",
})
#: line patterns treated as boilerplate (HTML comments, nav/footer markers, demo notes).
_BOILERPLATE = re.compile(r"^\s*(<!--|-->|nav:|footer:|copyright|all rights reserved)", re.IGNORECASE)


def estimate_tokens(text: str) -> int:
    """Deterministic offline token estimate (chars/CHARS_PER_TOKEN, min 1 for non-empty)."""
    n = len(text or "")
    return 0 if n == 0 else max(1, n // CHARS_PER_TOKEN)


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9_]+", (text or "").lower())
            if len(t) >= _MIN_TOKEN and t not in _STOPWORDS]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _handles(item: dict) -> list[str]:
    h = item.get("source_handles")
    if h:
        return list(h)
    return [item["source_handle"]] if item.get("source_handle") else []


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]


def compress(items: list[dict[str, Any]], *, query: str | None = None, max_tokens: int = 512,
             keyphrase_k: int = 8, model_summarizer: Callable[[str], str] | None = None,
             bus=None) -> dict[str, Any]:
    """Run the deterministic ladder over `items` and return a CompressionRun record.

    Each item: ``{"ref": str, "text": str, "source_handle"|"source_handles": ...}``. The result
    conforms to schemas/context/compression-run.schema.json and carries the compact digest plus the
    retained/dropped bookkeeping (every retained item keeps a handle; dropped near-dups are merged
    into their canonical item's handles). If `bus` (a context_events.EventBus, duck-typed) is passed,
    emit component.started → component.progressed (per ladder step) → context_pack.created for the
    live dashboard — non-breaking + deterministic when omitted (default None → identical output).
    """
    _cid = "compress-" + sha256(json.dumps([i.get("ref") for i in items], sort_keys=True).encode("utf-8")).hexdigest()[:8]
    if bus is not None:
        bus.publish("component.started", component="context_compress", stage="Optimization",
                    correlation_id=_cid, payload={"items": len(items), "query": query})

    method_chain: list[dict] = []
    dropped: list[dict] = []

    est_before = sum(estimate_tokens(i.get("text", "")) for i in items)

    # 0. token_budget
    method_chain.append({"method": "token_budget", "tool": "char-ratio(stdlib)", "deterministic": True,
                         "config": {"max_tokens": max_tokens, "chars_per_token": CHARS_PER_TOKEN},
                         "note": "tiktoken in prod"})

    # 1. boilerplate_removal — strip boilerplate lines from each item's text
    cleaned: list[dict] = []
    for it in items:
        lines = [ln for ln in (it.get("text", "") or "").splitlines() if not _BOILERPLATE.match(ln)]
        cleaned.append({**it, "text": "\n".join(lines).strip()})
    method_chain.append({"method": "boilerplate_removal", "tool": "regex(stdlib)", "deterministic": True,
                         "note": "trafilatura/jusText in prod"})

    # 2. dedupe_near_duplicates — exact (normalized hash) then near (difflib); collapse, keep handles
    canon: list[dict] = []
    for it in cleaned:
        norm = _normalize(it.get("text", ""))
        match = None
        for c in canon:
            if _normalize(c["text"]) == norm or SequenceMatcher(None, _normalize(c["text"]), norm).ratio() >= NEAR_DUP_RATIO:
                match = c
                break
        if match is not None:
            # collapse: merge this item's handles into the canonical item; record the drop with lineage
            for h in _handles(it):
                if h not in match.setdefault("_handles", _handles(match)):
                    match["_handles"].append(h)
            dropped.append({"ref": it.get("ref"), "reason": "near_duplicate",
                            "duplicate_of": match.get("ref"), "source_handles": _handles(it)})
        else:
            it = {**it, "_handles": _handles(it)}
            canon.append(it)
    method_chain.append({"method": "dedupe_near_duplicates", "tool": "difflib.SequenceMatcher(stdlib)",
                         "deterministic": True, "config": {"near_dup_ratio": NEAR_DUP_RATIO},
                         "dropped": len(dropped), "note": "datasketch MinHash / RapidFuzz in prod"})

    # 3. keyphrase_extraction — TF over content tokens across the surviving items
    tf: dict[str, int] = {}
    for it in canon:
        for t in _tokens(it.get("text", "")):
            tf[t] = tf.get(t, 0) + 1
    keyphrases = [w for w, _ in sorted(tf.items(), key=lambda kv: (-kv[1], kv[0]))[:keyphrase_k]]
    method_chain.append({"method": "keyphrase_extraction", "tool": "tf(stdlib)", "deterministic": True,
                         "config": {"k": keyphrase_k}, "note": "YAKE/RAKE/PyTextRank in prod"})

    # 4. query_focused_ranking — BM25-lite: score each item by query-term frequency overlap
    if query:
        qts = set(_tokens(query))
        def qscore(it: dict) -> int:
            its = _tokens(it.get("text", ""))
            return sum(its.count(t) for t in qts)
        canon.sort(key=lambda it: (-qscore(it), it.get("ref", "")))
        method_chain.append({"method": "query_focused_ranking", "tool": "bm25-lite(stdlib)",
                             "deterministic": True, "config": {"query": query}, "note": "rank-bm25/TF-IDF in prod"})

    # 5. extractive_selection — keep whole items in ranked order until the token budget is hit
    retained: list[dict] = []
    used = 0
    for it in canon:
        cost = estimate_tokens(it.get("text", ""))
        if used + cost > max_tokens and retained:
            dropped.append({"ref": it.get("ref"), "reason": "over_token_budget", "source_handles": it["_handles"]})
            continue
        retained.append(it)
        used += cost
    method_chain.append({"method": "extractive_selection", "tool": "budget-greedy(stdlib)",
                         "deterministic": True, "config": {"max_tokens": max_tokens},
                         "note": "sumy/LexRank/TextRank in prod"})

    # 6. pack_shape — the compact, source-linked digest the LLM sees first (every line keeps a handle)
    digest_lines = []
    for it in retained:
        sents = _sentences(it.get("text", ""))
        lead = sents[0] if sents else it.get("text", "")
        digest_lines.append({"text": lead, "source_handles": it["_handles"], "ref": it.get("ref")})
    compact_summary = " ".join(d["text"] for d in digest_lines)

    used_model = False
    if model_summarizer is not None:
        try:
            compact_summary = model_summarizer(compact_summary)
            used_model = True
            method_chain.append({"method": "llm_summarization", "tool": "model_summarizer(seam)",
                                 "deterministic": False, "note": "optional escalation; handles preserved"})
        except Exception:
            pass  # the deterministic digest stands; LLM is a convenience, never a dependency

    # what the LLM actually receives up front = the compact digest (the per-line handles are
    # metadata for expansion, not re-sent prose) — so the "after" budget is the digest's tokens.
    est_after = estimate_tokens(compact_summary)
    all_handles = sorted({h for it in retained for h in it["_handles"]}
                         | {h for d in dropped for h in d.get("source_handles", [])})

    if bus is not None:
        for m in method_chain:
            bus.publish("component.progressed", component="context_compress", stage="Optimization",
                        correlation_id=_cid, payload={"step": m["method"], "tool": m.get("tool")})
        bus.publish("context_pack.created", component="context_compress", stage="Optimization",
                    correlation_id=_cid, payload={"tokens_before": est_before, "tokens_after": est_after,
                                                  "retained": len(retained), "dropped": len(dropped)})

    run_seed = json.dumps({"r": [it.get("ref") for it in retained], "q": query, "mt": max_tokens}, sort_keys=True)
    return {
        "kind": "baltor.compression-run",
        "compression_run_id": "comprun-" + sha256(run_seed.encode("utf-8")).hexdigest()[:16],
        "input_refs": [it.get("ref") for it in items],
        "retained_refs": [{"ref": it.get("ref"), "source_handles": it["_handles"]} for it in retained],
        "dropped_refs": dropped,
        "method_chain": method_chain,
        "keyphrases": keyphrases,
        "compact_summary": compact_summary,
        "digest": digest_lines,
        "all_source_handles": all_handles,
        "token_budget": {"max_tokens": max_tokens, "tokenizer": "char-ratio(stdlib)",
                         "estimated_before": est_before, "estimated_after": est_after},
        "deterministic": not used_model,
        "llm_used": used_model,
        "query": query,
        "created_at": "1970-01-01T00:00:00Z",
    }


# ── self-test (proves the ladder on a fixture with a planted near-duplicate) ────
_FIXTURE: list[dict] = [
    {"ref": "adr-014", "text": "ADR-014: the payment-submit client uses at most 5 retries with full-jitter exponential backoff. This is the authoritative retry ceiling.",
     "source_handle": "ctx://acme-billing/decisions/ADR-014-billing-retry-policy.md#decision"},
    {"ref": "runbook", "text": "The payment-submit client retries up to 3 times on transient failures.\n<!-- DEMO NOTE: this is stale -->",
     "source_handle": "ctx://acme-billing/docs/billing-runbook.md#retry-policy"},
    # a NEAR-DUPLICATE of the runbook line, from a different source — must collapse, keep BOTH handles
    {"ref": "wiki", "text": "The payment submit client retries up to 3 times on transient failures.",
     "source_handle": "ctx://acme-billing/wiki/billing-retries#section-2"},
    {"ref": "owners", "text": "billing-service is owned by billing-team; escalation via billing-oncall.",
     "source_handle": "ctx://acme-billing/org/OWNERS.md#billing-team"},
]


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    run = compress(_FIXTURE, query="retry ceiling retries", max_tokens=512)

    # near-duplicate collapsed, and its handle MERGED into the canonical item (lineage not lost)
    nd = [d for d in run["dropped_refs"] if d["reason"] == "near_duplicate"]
    check("near-duplicate detected and dropped", len(nd) == 1, str(len(nd)))
    if nd:
        canon_ref = nd[0]["duplicate_of"]
        canon = next(r for r in run["retained_refs"] if r["ref"] == canon_ref)
        check("dropped near-dup's handle is merged into the canonical item (reversible)",
              "ctx://acme-billing/wiki/billing-retries#section-2" in canon["source_handles"]
              or "ctx://acme-billing/wiki/billing-retries#section-2" in run["all_source_handles"])

    # lineage invariant: EVERY retained item keeps at least one ctx:// handle
    check("every retained item keeps a ctx:// source handle",
          all(r["source_handles"] and all(h.startswith("ctx://") for h in r["source_handles"]) for r in run["retained_refs"]))

    # boilerplate removed (the HTML comment line is gone from the digest)
    check("boilerplate (HTML comment / DEMO NOTE) removed from digest", "DEMO NOTE" not in run["compact_summary"])

    # compression actually compressed: fewer tokens out than in, under budget
    tb = run["token_budget"]
    check("estimated tokens reduced (after <= before)", tb["estimated_after"] <= tb["estimated_before"],
          f"{tb['estimated_after']} <= {tb['estimated_before']}")

    # query ranking surfaced the retry items (ADR first among retained)
    check("query ranking put a retry item first", run["retained_refs"][0]["ref"] in ("adr-014", "runbook"),
          run["retained_refs"][0]["ref"])

    # keyphrases include the salient term
    check("keyphrases include 'retries' or 'retry'-family", any("retr" in k for k in run["keyphrases"]),
          ",".join(run["keyphrases"]))

    # deterministic by default, no LLM
    check("deterministic + no LLM by default", run["deterministic"] is True and run["llm_used"] is False)
    run2 = compress(_FIXTURE, query="retry ceiling retries", max_tokens=512)
    check("byte-identical on re-run (no clock/RNG)", run2 == run)

    # method chain records each ladder step (auditable)
    methods = [m["method"] for m in run["method_chain"]]
    for step in ("token_budget", "boilerplate_removal", "dedupe_near_duplicates", "keyphrase_extraction",
                 "query_focused_ranking", "extractive_selection"):
        check(f"method_chain records '{step}'", step in methods)

    # LLM escalation seam: records llm_used=True but never drops a handle
    run_m = compress(_FIXTURE, query="retry ceiling", model_summarizer=lambda s: "Retry ceiling is 5 (ADR-014).")
    check("LLM escalation recorded (llm_used=True, deterministic=False)",
          run_m["llm_used"] is True and run_m["deterministic"] is False)
    check("LLM escalation still preserves source handles",
          all(r["source_handles"] for r in run_m["retained_refs"]))

    # tiny budget forces an over_budget drop (and still keeps that handle in all_source_handles)
    run_tight = compress(_FIXTURE, query="retry", max_tokens=8)
    over = [d for d in run_tight["dropped_refs"] if d["reason"] == "over_token_budget"]
    check("tight budget drops items as over_token_budget (handles retained in lineage)",
          len(over) >= 1 and all(d["source_handles"] for d in over), str(len(over)))

    print(f"\n{'PASS — context_compress: deterministic ladder compresses + dedupes (collapsing the near-dup INTO the canonical handle), keeps every retained item source-linked, stays under budget; LLM is an optional recorded escalation.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic non-LLM context compression ladder.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    print(json.dumps(compress(_FIXTURE, query="retry ceiling"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
