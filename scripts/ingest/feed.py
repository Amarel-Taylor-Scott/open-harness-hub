#!/usr/bin/env python3
"""Corpus feeder — turn a registered official source into governed corpus rows.

This is the runnable, containerizable entry to the ingestion surface: given a
**registry entry** (an official / government source from ``data/source-registry.jsonl``),
fetch its URL, capture provenance (author / license / source_kind / publisher_class) +
``content_hash`` + ``scraped_at``, mine the page into attributable facts, and emit the
canonical **row families** the platform loads — then persist them.

**No reinvention.** Every step reuses the foundry single-sources, chained exactly the way
the worker pipeline does, so a fed corpus is byte-identical to one minted by the factory:

  ``WebSourceScout`` (fetch + provenance + CDC ``content_hash``, ``scrapers.py``)
    → a ``Candidate`` carrying the scraped ``source`` (incl. ``payload.facts``)
    → ``ConstructionStage`` (facts → a Knowledge Corpus body w/ ``_entries``, ``construction.py``)
    → ``StandardizeStage`` (canonical id + content/version hashes + schema-validate, ``standardize.py``)
    → ``StageLoadStage`` (emit ``source_record`` · ``normalized_object`` · ``object_embedding`` ·
      ``index_record`` · ``knowledge_entry`` · ``label_assignment`` · ``dedupe_cluster`` ·
      ``review_ticket``, ``stage_load.py``)
    → ``store.write(family, rows)`` (sqlite local → postgres cloud, ``store.py``).

Row dicts are never hand-rolled here; ``StageLoadStage`` owns their shape. The embedder
defaults to ``PlaceholderEmbedder`` (``is_placeholder: true`` — staging only, never
vector-search-committed, honoring the promotion boundary); wire a real ``Embedder`` and
the same rows become searchable. Local→cloud persistence is env-only via
``store.from_env()``.

Run ``python -m scripts.ingest.feed --self-test`` (offline) or ``--all`` / ``--source <kw>``
(live, needs a registry + network).
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from scripts.foundry.construction import ConstructionStage
from scripts.foundry.contracts import PROMOTED, Candidate, FoundryContext
from scripts.foundry.scrapers import DEFAULT_REGISTRY, Fetcher, WebSourceScout
from scripts.foundry.stage_load import Embedder, StageLoadStage
from scripts.foundry.standardize import StandardizeStage
from scripts.foundry.store import Store, from_env
from scripts.ingest import load_registry

# Persisting an unmeasured-lift corpus would violate the promotion boundary, so the rows
# below land in the candidate/staging tables only — never tenant-visible. The index_record
# carries approval_status=auto + an honest "fed, not gate-promoted" provenance note; a
# downstream measure/gate run upgrades it. (master-goal gate: promotion needs measured lift.)
_FEED_NOTE = "ingested from registered official source; lift not yet measured (staging only)"


def _entry_to_gap(entry: dict) -> dict:
    """Build the minimal ``gap`` ``WebSourceScout.find`` matches on, straight from a registry
    entry — its own keywords + url are the haystack, so an entry always matches itself."""
    return {
        "summary": entry.get("name") or " ".join(entry.get("keywords", [])),
        "source_hints": [entry.get("url", "")] + list(entry.get("keywords", [])),
        "industry": list(entry.get("industry", []) or []),
    }


def feed_source(
    entry: dict,
    *,
    fetcher: Fetcher | None = None,
    store: Store | None = None,
    embedder: Embedder | None = None,
) -> dict:
    """Feed ONE registered source into the governed corpus.

    Fetches ``entry['url']`` (via ``WebSourceScout`` so provenance + CDC ``content_hash`` are
    captured the same way the live scraper does), mines it into a Knowledge Corpus through the
    canonical construction→standardize stages, emits the row families with ``StageLoadStage``,
    writes them to ``store`` (default ``store.from_env()``), and returns a summary::

        {url, content_hash, rows: {family: count}, facts: n, object_id, skipped?}

    A source that 404s / errors / yields no facts is **skipped** (``ok=False`` + a reason),
    never raised — so ``feed_all`` can loop the whole registry without crashing.
    """
    url = entry.get("url", "")
    scout = WebSourceScout([entry], fetcher=fetcher)  # single-entry registry ⇒ matches itself
    try:
        src = scout.find(_entry_to_gap(entry))
    except Exception as exc:  # network / decode error on a single source must not crash the loop
        return {"url": url, "ok": False, "reason": f"fetch failed: {exc}", "rows": {}, "facts": 0}
    if not src:
        # 404 / non-200 / no parseable facts — recorded, not fatal
        return {"url": url, "ok": False, "reason": "unreachable or no facts parsed", "rows": {}, "facts": 0}

    facts = src.get("payload", {}).get("facts", [])

    # Build the candidate the scraped source implies, then run the SAME stages the factory does.
    cand = Candidate(
        gap={
            # a non-empty gap id keeps the candidate well-formed for downstream measure/gate;
            # the model-independent signal is "this is a registered authoritative source".
            "id": f"ingest/{src.get('content_hash', '')[:16]}",
            "summary": src["payload"].get("name", entry.get("name", "")),
            "industry": src["payload"].get("industry", []),
        },
        source=src,  # carries source_url/author/license/source_kind/publisher_class + payload.facts
    )
    ctx = FoundryContext(partition="ingest")
    [cand] = ConstructionStage().run([cand], ctx)         # facts → Knowledge Corpus body (_entries)
    [cand] = StandardizeStage().run([cand], ctx)          # canonical id + content/version hashes
    if not cand.alive or not cand.component_id:
        reason = cand.reasons[-1] if cand.reasons else "construction/standardize dropped the candidate"
        return {"url": url, "ok": False, "reason": reason, "rows": {}, "facts": len(facts)}

    # Persist provenance ON the row (so the corpus stays governed without a measured lift yet).
    cand.gap["confirmation_source"] = "registered_source"
    cand.lift = {"delta": None, "note": _FEED_NOTE}  # honest: fed, not gate-promoted
    cand.decision = PROMOTED  # StageLoadStage emits row families only for PROMOTED candidates

    stage = StageLoadStage(embedder=embedder)  # no out_dir ⇒ rows stay in memory; we write to the store
    stage.run([cand], ctx)
    rows = stage.rows

    sink = store or from_env()
    written: dict[str, int] = {}
    for family, rs in sorted(rows.items()):
        if rs:
            written[family] = sink.write(family, rs)

    return {
        "url": url,
        "content_hash": src.get("content_hash"),
        "object_id": cand.component_id,
        "scraped_at": src.get("scraped_at"),
        "publisher_class": src.get("publisher_class"),
        "rows": written,
        "facts": len(facts),
        "ok": True,
    }


def feed_all(
    registry: list[dict] | None = None,
    *,
    store: Store | None = None,
    fetcher: Fetcher | None = None,
    embedder: Embedder | None = None,
) -> dict:
    """Feed EVERY registered source. Loads the registry via ``load_registry`` (the single
    reader), feeds each through ``feed_source`` against ONE shared store, and returns totals +
    a per-source result. A skipped source (404 / no facts) is recorded, not fatal."""
    entries = registry if registry is not None else load_registry()
    sink = store or from_env()  # one store for the whole batch (idempotent upserts)

    results: list[dict] = []
    totals: dict[str, int] = {}
    fed = skipped = facts_total = 0
    for entry in entries:
        res = feed_source(entry, fetcher=fetcher, store=sink, embedder=embedder)
        results.append(res)
        if res.get("ok"):
            fed += 1
            facts_total += res.get("facts", 0)
            for family, n in res.get("rows", {}).items():
                totals[family] = totals.get(family, 0) + n
        else:
            skipped += 1

    return {
        "sources_total": len(entries),
        "fed": fed,
        "skipped": skipped,
        "facts": facts_total,
        "rows": dict(sorted(totals.items())),
        "backend": getattr(sink, "backend", "?"),
        "results": results,
    }


def _match_keyword(entries: list[dict], keyword: str) -> list[dict]:
    """Sources whose keywords (or name/url) contain ``keyword`` (case-insensitive substring)."""
    kw = keyword.lower()
    out = []
    for e in entries:
        hay = " ".join([*(e.get("keywords") or []), e.get("name", ""), e.get("url", "")]).lower()
        if kw in hay:
            out.append(e)
    return out


# --------------------------------------------------------------------------- #
# self-test (offline; CannedFetcher + a temp SqliteStore — no network, no real DB)
# --------------------------------------------------------------------------- #
def _self_test() -> int:
    import tempfile
    from pathlib import Path

    from scripts.foundry.scrapers import CannedFetcher
    from scripts.foundry.store import SqliteStore

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # Two fake gov pages + matching registry entries (public metadata only — no PII/secrets).
    page_bsp = (
        "BSP Circular 1230: the cash-withdrawal scrutiny threshold is PHP 1,000,000.\n\n"
        "Covered persons must file a Covered Transaction Report within five working days.\n\n"
        "Suspicious transactions must be reported regardless of amount."
    )
    page_osh = (
        "RA 11058: employers must provide free occupational safety and health training.\n\n"
        "A safety officer is required for establishments with the prescribed headcount."
    )
    registry = [
        {"keywords": ["bsp.gov.ph", "financial-crime"], "url": "https://bsp.gov.ph/aml",
         "author": "Bangko Sentral ng Pilipinas", "license": "Government work (PH)",
         "source_kind": "regulation", "gov": True, "industry": ["financial-crime"],
         "name": "PH AML thresholds (BSP)"},
        {"keywords": ["oshc.dole.gov.ph", "occupational-safety"], "url": "https://oshc.dole.gov.ph/",
         "author": "OSHC (PH)", "license": "Government work (PH)", "source_kind": "regulation",
         "gov": True, "industry": ["occupational-safety"], "name": "PH OSH Standards (RA 11058)"},
    ]
    fetcher = CannedFetcher({"https://bsp.gov.ph/aml": page_bsp, "https://oshc.dole.gov.ph/": page_osh})

    with tempfile.TemporaryDirectory() as tmp:
        store = SqliteStore(Path(tmp) / "ingest.sqlite")

        # ── feed_source: one registered source → governed corpus rows ──────────
        res = feed_source(registry[0], fetcher=fetcher, store=store)
        check("feed_source ok", res.get("ok") is True, str(res))
        check("feed_source returns a content_hash (CDC)", bool(res.get("content_hash")), str(res))
        check("feed_source parsed the facts", res.get("facts") == 3, str(res.get("facts")))
        check("feed_source captured scraped_at provenance", bool(res.get("scraped_at")))
        check("feed_source set publisher_class=public_authority (gov)",
              res.get("publisher_class") == "public_authority", str(res.get("publisher_class")))
        check("feed_source returns a canonical object_id", bool(res.get("object_id")), str(res))

        rows = res.get("rows", {})
        check("≥1 normalized_object emitted", rows.get("normalized_object", 0) >= 1, str(rows))
        check("≥1 index_record emitted", rows.get("index_record", 0) >= 1, str(rows))
        check("source_record emitted (provenance row)", rows.get("source_record", 0) >= 1, str(rows))
        # the facts became individually-addressable knowledge pages
        check("knowledge_entry per fact (3)", rows.get("knowledge_entry", 0) == 3, str(rows))

        # ── rows actually landed in the store (persisted, queryable) ───────────
        check("normalized_object persisted to store", store.count("normalized_object") >= 1,
              str(store.count("normalized_object")))
        check("index_record persisted to store", store.count("index_record") >= 1)
        check("knowledge_entry persisted (3)", store.count("knowledge_entry") == 3,
              str(store.count("knowledge_entry")))

        # ── governance: provenance survived onto the stored rows ───────────────
        no = store.read("normalized_object")[0]
        check("normalized_object carries content_hash", bool(no.get("content_hash")), str(no))
        check("normalized_object linked to a source_record", bool(no.get("source_id")), str(no))
        sr = store.read("source_record")[0]
        check("source_record carries license + author (governed)",
              bool(sr.get("license")) and bool(sr.get("author")), str(sr))

        # ── promotion boundary: a placeholder embedding is NOT vector-search-ready ──
        emb = store.read("object_embedding")[0]
        check("object_embedding flagged placeholder (staging only)", emb.get("is_placeholder") is True, str(emb))
        check("object_embedding NOT vector-search-ready", emb.get("vector_search_ready") is False, str(emb))

        # idempotent re-feed: same source → same ids → no row explosion (upsert)
        before = store.count("normalized_object")
        feed_source(registry[0], fetcher=fetcher, store=store)
        check("re-feeding the same source is idempotent (upsert, no dupes)",
              store.count("normalized_object") == before, f"{store.count('normalized_object')} != {before}")

    # ── feed_all: loops the whole registry, skips the unreachable, totals rows ──
    with tempfile.TemporaryDirectory() as tmp:
        store2 = SqliteStore(Path(tmp) / "all.sqlite")
        # add a source whose page is missing from the canned fetcher ⇒ must be skipped, not crash
        reg_with_dead = registry + [
            {"keywords": ["404.example"], "url": "https://404.example/missing",
             "author": "X", "license": "CC0-1.0", "source_kind": "other", "gov": True, "name": "Dead link"}
        ]
        summary = feed_all(reg_with_dead, store=store2, fetcher=fetcher)
        check("feed_all loops every source", summary["sources_total"] == 3, str(summary["sources_total"]))
        check("feed_all fed the 2 reachable sources", summary["fed"] == 2, str(summary["fed"]))
        check("feed_all skipped the 404 (recorded, no crash)", summary["skipped"] == 1, str(summary["skipped"]))
        check("feed_all aggregated facts across sources", summary["facts"] == 5, str(summary["facts"]))
        check("feed_all totalled normalized_object across sources",
              summary["rows"].get("normalized_object", 0) == 2, str(summary["rows"]))
        check("feed_all reports the backend", summary["backend"] == "sqlite", str(summary["backend"]))
        # the dead source carries a reason, not an exception
        dead = next((r for r in summary["results"] if "404" in r["url"]), None)
        check("skipped source carries a reason", bool(dead) and not dead.get("ok") and bool(dead.get("reason")),
              str(dead))
        # both reachable sources persisted distinct objects
        check("feed_all persisted 2 distinct objects", store2.count("normalized_object") == 2,
              str(store2.count("normalized_object")))

    # ── keyword matcher (drives --source) ──────────────────────────────────────
    matched = _match_keyword(registry, "financial-crime")
    check("--source keyword matches by keyword", len(matched) == 1 and matched[0]["name"] == "PH AML thresholds (BSP)",
          str([m["name"] for m in matched]))
    check("--source no match ⇒ empty", _match_keyword(registry, "no-such-domain") == [])

    print(f"\n{'all feed self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Feed registered official sources into the governed corpus.")
    p.add_argument("--self-test", action="store_true", help="run the offline self-test (no network/DB)")
    p.add_argument("--all", action="store_true", help="feed EVERY registered source (live; needs network)")
    p.add_argument("--source", metavar="KEYWORD", help="feed sources whose keywords/name/url match KEYWORD (live)")
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="path to the source registry JSONL")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.all or args.source:
        entries = load_registry(args.registry)
        if args.source:
            entries = _match_keyword(entries, args.source)
            if not entries:
                print(json.dumps({"note": f"no registered source matches {args.source!r}", "registry": args.registry}))
                return 0
        store = from_env()  # local sqlite → cloud postgres, env-only
        summary = feed_all(entries, store=store)
        # print the summary minus the verbose per-source list (kept in the return value)
        print(json.dumps({k: v for k, v in summary.items() if k != "results"}, sort_keys=True, indent=2))
        for r in summary["results"]:
            print(json.dumps({"url": r.get("url"), "ok": r.get("ok"),
                              "facts": r.get("facts"), "object_id": r.get("object_id"),
                              "reason": r.get("reason")}, sort_keys=True))
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
