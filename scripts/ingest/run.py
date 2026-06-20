#!/usr/bin/env python3
"""Ingest runner — the freshness→feed loop that keeps the governed corpus current.

This is the wired, containerizable entry point that ties the ingestion surface together:

    freshness.check_all (CDC: which official sources are new / changed?)
        → for each new/changed source: feed.feed_source (re-ingest → governed corpus rows)
            → store.write(family, rows) (sqlite local → postgres cloud, env-only)

It is the autonomous half of the recurring-revenue layer: a source that moved since the
last poll is **stale**, so the runner re-feeds exactly that source (and only that source —
``unchanged`` sources are skipped, no needless work, no false refresh alert). Run it
``--once`` (one pass, e.g. a cron tick) or ``--loop --interval <s>`` (a long-running
worker/sidecar that polls forever).

**No reinvention.** Every step is an existing single-source, imported and chained — the
CDC poller (`scripts.ingest.freshness`), the corpus feeder (`scripts.ingest.feed`), the
registry loader (`scripts.ingest.load_registry`), and env-only persistence
(`scripts.foundry.store.from_env`). The runner adds only the loop + the change→feed wiring;
it owns no row shapes, no fetch logic, and no hashing of its own.

Optionally ``--enqueue`` also puts a ``{"kind": "reingest", "source": entry}`` job on the
broker (`scripts.foundry.queues.from_env`) per change, so a separate worker fleet can do
the heavy feed out-of-band (KEDA-scaled) instead of inline — the same change event drives
both paths. Inline feeding is the default (zero extra services); enqueue is the
decoupled/cloud path.

stdlib + the foundry/ingest single-sources only; NO new pip deps. Local→cloud is env-only.
Run ``python -m scripts.ingest.run --self-test`` (offline) or ``--once`` / ``--loop`` (live).
"""
from __future__ import annotations

import argparse
import json
import os
import time

from scripts.foundry.scrapers import Fetcher, HttpFetcher
from scripts.foundry.stage_load import Embedder
from scripts.foundry.store import Store, from_env
from scripts.ingest import load_registry
from scripts.ingest.feed import feed_source
from scripts.ingest.freshness import check_all

# A source whose freshness event is one of these is STALE ⇒ re-feed it; everything else
# (``unchanged`` / ``error``) is left alone. Single source for "what triggers a feed".
FEEDABLE_EVENTS = ("new", "changed")

# Loop cadence (seconds between freshness passes). Env-overridable (12-factor) so containers
# tune it without a code change; the default is a polite hourly-ish poll for gov sources that
# rarely move intraday. Named constant + unit so the value lives in exactly one place.
INTERVAL_ENV = "OH_INGEST_INTERVAL"
DEFAULT_INTERVAL_S = 3600  # seconds (1 hour); official sources rarely change faster


def _interval_default() -> float:
    """Resolve the loop interval default: ``$OH_INGEST_INTERVAL`` (seconds) → builtin default."""
    raw = os.environ.get(INTERVAL_ENV)
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return float(DEFAULT_INTERVAL_S)


def run_once(
    registry: list[dict] | None = None,
    *,
    store: Store | None = None,
    fetcher: Fetcher | None = None,
    embedder: Embedder | None = None,
    enqueue: bool = False,
    queue=None,
    state_file: str | os.PathLike | None = None,
) -> dict:
    """One freshness→feed pass over the registry.

    Polls every registered source via `freshness.check_all` (which advances the last-seen
    CDC state), then re-feeds **only** the sources whose event is ``new``/``changed`` via
    `feed.feed_source`, writing the row families to one shared ``store``. ``unchanged`` and
    ``error`` sources are skipped. When ``enqueue=True`` the same change events are also put
    on the broker (a worker fleet can feed them out-of-band).

    All collaborators are injectable so the whole pass runs offline in the self-test
    (CannedFetcher + a temp SqliteStore + an InMemory/Sqlite queue + a tmp state file).
    Returns::

        {checked, changed, errors, fed, skipped, facts, rows: {family: n},
         backend, results: [feed_source summary, ...]}
    """
    entries = registry if registry is not None else load_registry()
    sink = store or from_env()  # one store for the whole pass (idempotent upserts)
    by_url = {e.get("url", ""): e for e in entries}  # map a change event back to its full entry

    # CDC: which sources moved? (state advances here; enqueue side-effects are opt-in)
    events = check_all(
        entries, fetcher=fetcher, enqueue=enqueue, store=queue, state_file=state_file
    )

    results: list[dict] = []
    totals: dict[str, int] = {}
    fed = skipped = errors = facts_total = 0
    for ev in events:
        event = ev.get("event")
        if event == "error":
            errors += 1
            continue
        if event not in FEEDABLE_EVENTS:
            continue  # unchanged ⇒ nothing to re-ingest
        entry = by_url.get(ev.get("url", ""))
        if entry is None:  # event without a matching registry entry — defensive, shouldn't happen
            skipped += 1
            continue
        res = feed_source(entry, fetcher=fetcher, store=sink, embedder=embedder)
        res["event"] = event  # carry the CDC reason onto the feed result
        results.append(res)
        if res.get("ok"):
            fed += 1
            facts_total += res.get("facts", 0)
            for family, n in res.get("rows", {}).items():
                totals[family] = totals.get(family, 0) + n
        else:
            skipped += 1

    changed = sum(1 for e in events if e.get("event") in FEEDABLE_EVENTS)
    return {
        "checked": len(events),
        "changed": changed,
        "errors": errors,
        "fed": fed,
        "skipped": skipped,
        "facts": facts_total,
        "rows": dict(sorted(totals.items())),
        "backend": getattr(sink, "backend", "?"),
        "results": results,
    }


def run_loop(
    registry: list[dict] | None = None,
    *,
    store: Store | None = None,
    fetcher: Fetcher | None = None,
    embedder: Embedder | None = None,
    enqueue: bool = False,
    queue=None,
    state_file: str | os.PathLike | None = None,
    interval_s: float | None = None,
    max_passes: int | None = None,
    sleep=time.sleep,
    on_pass=None,
) -> list[dict]:
    """Repeat `run_once` every ``interval_s`` seconds (the long-running sidecar/worker mode).

    Resolves the registry + store ONCE and reuses them across passes (so state + the store
    accumulate). ``max_passes`` bounds the loop (``None`` = forever, for production;
    the self-test passes a small int so it terminates). ``sleep`` is injectable so the
    self-test runs instantly. ``on_pass(summary)`` is an optional per-pass callback (the CLI
    uses it to print each pass). Returns the per-pass summaries.
    """
    entries = registry if registry is not None else load_registry()
    sink = store or from_env()  # resolve once; reused across passes
    interval = _interval_default() if interval_s is None else float(interval_s)

    summaries: list[dict] = []
    passes = 0
    while max_passes is None or passes < max_passes:
        summary = run_once(
            entries, store=sink, fetcher=fetcher, embedder=embedder,
            enqueue=enqueue, queue=queue, state_file=state_file,
        )
        summaries.append(summary)
        passes += 1
        if on_pass is not None:
            on_pass(summary)
        if max_passes is not None and passes >= max_passes:
            break
        sleep(interval)
    return summaries


# --------------------------------------------------------------------------- #
# self-test (offline; CannedFetcher + a temp SqliteStore + InMemory/Sqlite queue + tmp state)
# --------------------------------------------------------------------------- #
def _self_test() -> int:
    import tempfile
    from pathlib import Path

    from scripts.foundry import queues
    from scripts.foundry.scrapers import CannedFetcher, content_hash
    from scripts.foundry.store import SqliteStore
    from scripts.ingest.freshness import REINGEST_KIND, load_state

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # One fake gov page + a matching registry entry (public metadata only — no PII/secrets).
    url = "https://bsp.gov.ph/aml"
    page_v1 = (
        "BSP Circular 1230: the cash-withdrawal scrutiny threshold is PHP 1,000,000.\n\n"
        "Covered persons must file a Covered Transaction Report within five working days.\n\n"
        "Suspicious transactions must be reported regardless of amount."
    )
    page_v2 = page_v1.replace("1,000,000", "2,000,000")  # the threshold moved ⇒ a 'changed' event
    entry = {
        "keywords": ["bsp.gov.ph", "financial-crime"], "url": url,
        "author": "Bangko Sentral ng Pilipinas", "license": "Government work (PH)",
        "source_kind": "regulation", "gov": True, "industry": ["financial-crime"],
        "name": "PH AML thresholds (BSP)",
    }
    registry = [entry]

    with tempfile.TemporaryDirectory() as tmp:
        store = SqliteStore(Path(tmp) / "ingest.sqlite")
        sf = Path(tmp) / "freshness-state.json"

        # ── pass 1: cold state ⇒ 'new' ⇒ the source is fed and rows land in the store ──
        s1 = run_once(registry, store=store, fetcher=CannedFetcher({url: page_v1}), state_file=sf)
        check("pass 1 polled the source", s1["checked"] == 1, str(s1))
        check("pass 1 saw a change (new)", s1["changed"] == 1, str(s1))
        check("pass 1 fed the changed source", s1["fed"] == 1, str(s1))
        check("pass 1 reports the backend", s1["backend"] == "sqlite", str(s1))
        check("pass 1 emitted normalized_object rows", s1["rows"].get("normalized_object", 0) >= 1, str(s1["rows"]))
        check("rows LANDED in the store (normalized_object)", store.count("normalized_object") >= 1,
              str(store.count("normalized_object")))
        check("rows LANDED in the store (index_record)", store.count("index_record") >= 1)
        check("knowledge pages landed (knowledge_entry == 3)", store.count("knowledge_entry") == 3,
              str(store.count("knowledge_entry")))
        # the feed result carried the CDC reason
        check("feed result carries the CDC event", s1["results"] and s1["results"][0].get("event") == "new",
              str(s1["results"]))
        # freshness state advanced to v1's hash
        check("state advanced to the fetched hash",
              load_state(sf).get(url, {}).get("content_hash") == content_hash(page_v1), str(load_state(sf)))

        # ── pass 2: SAME page ⇒ 'unchanged' ⇒ NO feed (no needless re-ingest), no row growth ──
        before = store.count("normalized_object")
        s2 = run_once(registry, store=store, fetcher=CannedFetcher({url: page_v1}), state_file=sf)
        check("pass 2 sees no change (unchanged)", s2["changed"] == 0, str(s2))
        check("pass 2 feeds nothing", s2["fed"] == 0, str(s2))
        check("unchanged ⇒ store rows do not grow", store.count("normalized_object") == before,
              f"{store.count('normalized_object')} != {before}")

        # ── pass 3: CHANGED page ⇒ 'changed' ⇒ re-fed (idempotent upsert, same object id) ──
        s3 = run_once(registry, store=store, fetcher=CannedFetcher({url: page_v2}), state_file=sf)
        check("pass 3 detects the moved page (changed)", s3["changed"] == 1, str(s3))
        check("pass 3 re-fed the changed source", s3["fed"] == 1, str(s3))
        check("re-feed is idempotent (same object id ⇒ no row explosion)",
              store.count("normalized_object") == before, f"{store.count('normalized_object')} != {before}")
        check("state advanced to the new hash",
              load_state(sf).get(url, {}).get("content_hash") == content_hash(page_v2))

    # ── error isolation: an unreachable source surfaces as an error, never a crash, no feed ──
    with tempfile.TemporaryDirectory() as tmp:
        store_e = SqliteStore(Path(tmp) / "err.sqlite")
        dead = {"keywords": ["404"], "url": "https://404.example/missing", "name": "Dead", "gov": True,
                "license": "CC0-1.0", "source_kind": "other"}
        se = run_once([entry, dead], store=store_e,
                      fetcher=CannedFetcher({url: page_v1}), state_file=Path(tmp) / "err-state.json")
        check("an unreachable source ⇒ counted as error (no crash)", se["errors"] == 1, str(se))
        check("the reachable source still fed despite the dead one", se["fed"] == 1, str(se))

    # ── --enqueue path: a change ALSO drops a reingest job on the broker ──
    with tempfile.TemporaryDirectory() as tmp:
        store_q = SqliteStore(Path(tmp) / "q-store.sqlite")
        q = queues.SqliteQueue(str(Path(tmp) / "q.sqlite"), key="ingest-run-test")
        sq = run_once(registry, store=store_q, fetcher=CannedFetcher({url: page_v1}),
                      enqueue=True, queue=q, state_file=Path(tmp) / "enq-state.json")
        check("enqueue path still feeds inline", sq["fed"] == 1, str(sq))
        check("enqueue path dropped one reingest job on the broker", q.depth() == 1, str(q.depth()))
        job = q.pull()
        check("enqueued job kind == 'reingest'", job.get("kind") == REINGEST_KIND, str(job))
        check("enqueued job carries the source entry", job.get("source", {}).get("url") == url, str(job))

    # ── run_loop: bounded passes, an injected instant sleep, state carries across passes ──
    with tempfile.TemporaryDirectory() as tmp:
        store_l = SqliteStore(Path(tmp) / "loop.sqlite")
        sf_l = Path(tmp) / "loop-state.json"
        # both passes serve the SAME page ⇒ pass 1 feeds (new), pass 2 is unchanged.
        sleeps: list[float] = []
        summaries = run_loop(
            registry, store=store_l, fetcher=CannedFetcher({url: page_v1}),
            state_file=sf_l, interval_s=0, max_passes=2, sleep=lambda s: sleeps.append(s),
        )
        check("run_loop ran exactly max_passes", len(summaries) == 2, str(len(summaries)))
        check("run_loop pass 1 fed (new)", summaries[0]["fed"] == 1, str(summaries[0]))
        check("run_loop pass 2 fed nothing (state carried ⇒ unchanged)", summaries[1]["fed"] == 0, str(summaries[1]))
        check("run_loop did NOT sleep after the final pass", len(sleeps) == 1, str(sleeps))
        check("run_loop store has exactly one object (no dupes across passes)",
              store_l.count("normalized_object") == 1, str(store_l.count("normalized_object")))

    # ── interval default resolution is env-only ──
    saved = os.environ.pop(INTERVAL_ENV, None)
    try:
        check("interval default falls back to builtin", _interval_default() == float(DEFAULT_INTERVAL_S))
        os.environ[INTERVAL_ENV] = "5"
        check("OH_INGEST_INTERVAL overrides the default", _interval_default() == 5.0)
        os.environ[INTERVAL_ENV] = "not-a-number"
        check("a bad OH_INGEST_INTERVAL degrades to the default (no crash)",
              _interval_default() == float(DEFAULT_INTERVAL_S))
    finally:
        os.environ.pop(INTERVAL_ENV, None)
        if saved is not None:
            os.environ[INTERVAL_ENV] = saved

    print(f"\n{'all run self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _print_summary(summary: dict) -> None:
    """Print one pass: the headline counts, then one line per fed source."""
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, sort_keys=True))
    for r in summary["results"]:
        print(json.dumps({"url": r.get("url"), "event": r.get("event"), "ok": r.get("ok"),
                          "facts": r.get("facts"), "object_id": r.get("object_id"),
                          "reason": r.get("reason")}, sort_keys=True))


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Ingest runner — the freshness→feed loop (re-feed sources that moved)."
    )
    p.add_argument("--self-test", action="store_true", help="run the offline self-test (no network/DB)")
    p.add_argument("--once", action="store_true", help="run ONE freshness→feed pass (live; needs network)")
    p.add_argument("--loop", action="store_true", help="poll + feed forever every --interval seconds (live)")
    p.add_argument("--interval", type=float, default=None,
                   help=f"seconds between passes with --loop (default: ${INTERVAL_ENV} or {DEFAULT_INTERVAL_S})")
    p.add_argument("--enqueue", action="store_true",
                   help="also enqueue a reingest job per change (for an out-of-band worker fleet)")
    p.add_argument("--max-passes", type=int, default=None,
                   help="bound --loop to N passes then exit (default: run forever)")
    p.add_argument("--registry", default=None, help="registry path (default: data/source-registry.jsonl)")
    p.add_argument("--state", default=None, help="freshness state file (default: $OH_FRESHNESS_STATE)")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.once or args.loop:
        registry = load_registry(args.registry)
        if not registry:
            print(json.dumps({"note": f"no registry at {args.registry or 'data/source-registry.jsonl'}; "
                              "add gap-keyword→source rows to enable ingestion"}))
            return 0
        store = from_env()  # local sqlite → cloud postgres, env-only
        if args.loop:
            run_loop(registry, store=store, enqueue=args.enqueue, interval_s=args.interval,
                     max_passes=args.max_passes, state_file=args.state, on_pass=_print_summary)
        else:
            _print_summary(run_once(registry, store=store, enqueue=args.enqueue, state_file=args.state))
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
