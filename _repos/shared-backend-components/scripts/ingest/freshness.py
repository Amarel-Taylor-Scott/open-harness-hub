#!/usr/bin/env python3
"""Ingest freshness — the OFFICIAL-SITE UPDATE CHECKER (CDC) for the governed corpus.

Poll every registered authoritative source (`data/source-registry.jsonl`), compare each
page's content hash to the **last seen** hash, and emit a change event:

  - ``new``       — never polled before (first sighting)
  - ``changed``   — the source moved since last poll  ⇒  the corpus is stale
  - ``unchanged`` — identical to last poll

A ``changed``/``new`` event is exactly the CDC signal the recurring-revenue layer sells:
the corpus must be re-fed and subscribers get a refresh/revocation alert. When run with
``--enqueue`` (or ``check_all(..., enqueue=True)``) each such event puts a
``{"kind": "reingest", "source": entry}`` job on the broker (`scripts.foundry.queues.from_env`)
so a worker re-ingests the source via `scripts.ingest.feed`.

This builds ON TOP of the foundry — NO reinvention:
  - fetchers + the CDC primitive: `scripts.foundry.scrapers` (HttpFetcher/CannedFetcher,
    content_hash, detect_change);
  - the source registry loader: `scripts.ingest.load_registry`;
  - the job broker: `scripts.foundry.queues.from_env` (sqlite local → redis cloud).

**State** is a small JSON file mapping ``url → {content_hash, name, event, checked_at}``;
its path comes from env (``OH_FRESHNESS_STATE``, default ``dist/freshness-state.json``) so
local→cloud/containers are env-only and nothing is hardcoded. (We keep last-seen state in
a compact file rather than a store row family because freshness is one mutable row PER URL
— an upsert-by-url JSON map — not an append-only emit; the store's row families stay the
ingest output, this is the poller's cursor.)

stdlib + the foundry only. Run ``python -m scripts.ingest.freshness --self-test`` (offline)
or ``--check`` / ``--check --enqueue`` (live, needs the registry + network).
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from scripts.foundry import queues
from scripts.foundry.scrapers import Fetcher, HttpFetcher, content_hash, detect_change
from scripts.ingest import load_registry

# State file path — env-only (12-factor); never hardcode the location in logic.
STATE_ENV = "OH_FRESHNESS_STATE"
DEFAULT_STATE_PATH = "dist/freshness-state.json"
# The job a changed/new source enqueues so a worker re-feeds it (consumed by scripts.ingest.feed).
REINGEST_KIND = "reingest"


def state_path(path: str | Path | None = None) -> Path:
    """Resolve the state-file path: explicit arg → ``OH_FRESHNESS_STATE`` → default."""
    return Path(path or os.environ.get(STATE_ENV) or DEFAULT_STATE_PATH)


def load_state(path: str | Path | None = None) -> dict[str, dict]:
    """Read the url → last-seen-state map (``{}`` if it doesn't exist yet)."""
    p = state_path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(state: dict[str, dict], path: str | Path | None = None) -> Path:
    """Persist the url → last-seen-state map (atomic-ish: write temp, replace)."""
    p = state_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def check_source(entry: dict, prev_hash: str | None, *, fetcher: Fetcher | None = None) -> dict:
    """Fetch ``entry['url']``, hash it, and CDC-compare to ``prev_hash``.

    Returns ``{url, name, event, content_hash, checked_at}`` where ``event`` is one of
    ``new`` | ``changed`` | ``unchanged`` (from `scrapers.detect_change`). A fetch error
    (network down / non-200) surfaces as ``event='error'`` with the detail, never a crash —
    a poller must keep going across the rest of the registry.
    """
    fetcher = fetcher or HttpFetcher()
    url = entry.get("url", "")
    name = entry.get("name", "")
    try:
        fetched = fetcher.fetch(url)
    except Exception as exc:  # noqa: BLE001 — keep polling the rest of the registry
        return {"url": url, "name": name, "event": "error", "content_hash": None,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": f"{type(exc).__name__}: {exc}"}
    if fetched.get("status") != 200:
        return {"url": url, "name": name, "event": "error", "content_hash": None,
                "checked_at": fetched.get("fetched_at"),
                "error": f"status {fetched.get('status')}"}
    cdc = detect_change(prev_hash, fetched.get("content", ""))
    return {"url": url, "name": name, "event": cdc["event"], "content_hash": cdc["content_hash"],
            "checked_at": fetched.get("fetched_at")}


def check_all(registry: list[dict] | None = None, *, store=None, fetcher: Fetcher | None = None,
              enqueue: bool = False, state_file: str | Path | None = None) -> list[dict]:
    """Check every registered source against stored state, update state, return the events.

    For each source: look up its last-seen hash in the JSON state file, `check_source`,
    then upsert the new state. When ``enqueue=True`` and the event is ``new`` or ``changed``,
    put a ``{"kind": "reingest", "source": entry}`` job on the broker so a worker re-feeds it.

    ``registry`` defaults to `load_registry()`; ``store`` is accepted for signature
    compatibility (state persists to the JSON file) but unused here. The broker is
    `queues.from_env()` unless a queue is injected (tests pass an InMemoryQueue).
    """
    registry = registry if registry is not None else load_registry()
    state = load_state(state_file)
    queue = None  # lazily resolved only if we actually need to enqueue (no broker side effects otherwise)
    events: list[dict] = []
    for entry in registry:
        url = entry.get("url", "")
        prev = (state.get(url) or {}).get("content_hash")
        ev = check_source(entry, prev, fetcher=fetcher)
        events.append(ev)
        if ev["event"] == "error":
            continue  # don't overwrite a good last-seen hash with a transient failure
        # upsert this url's cursor
        state[url] = {"content_hash": ev["content_hash"], "name": ev["name"],
                      "event": ev["event"], "checked_at": ev["checked_at"]}
        if enqueue and ev["event"] in ("new", "changed"):
            if queue is None:
                queue = store if _is_queue(store) else queues.from_env()
            queue.enqueue({"kind": REINGEST_KIND, "source": entry})
    save_state(state, state_file)
    return events


def _is_queue(obj) -> bool:
    """True if ``obj`` quacks like a `queues` broker (so a test can pass one as `store=`)."""
    return obj is not None and callable(getattr(obj, "enqueue", None))


# ── CLI ────────────────────────────────────────────────────────────────────────


def _check(args: argparse.Namespace) -> int:
    """Live: poll every registered source, print one event per line, summarize."""
    registry = load_registry(args.registry)
    if not registry:
        print(json.dumps({"note": f"no registry at {args.registry}; add gap-keyword→source rows to enable freshness"}))
        return 0
    events = check_all(registry, fetcher=HttpFetcher(), enqueue=args.enqueue, state_file=args.state)
    for ev in events:
        print(json.dumps(ev, sort_keys=True))
    changed = [e for e in events if e["event"] in ("new", "changed")]
    print(json.dumps({"checked": len(events), "changed": len(changed),
                      "errors": sum(1 for e in events if e["event"] == "error"),
                      "enqueued": len(changed) if args.enqueue else 0,
                      "state": str(state_path(args.state))}, sort_keys=True))
    return 0


def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    from scripts.foundry.scrapers import CannedFetcher

    entry = {"keywords": ["philippines", "aml"], "url": "https://bsp.gov.ph/aml",
             "author": "Bangko Sentral ng Pilipinas", "license": "Government work (PH)",
             "source_kind": "regulation", "gov": True, "name": "PH AML thresholds (BSP)"}
    registry = [entry]
    page_v1 = "BSP Circular 1230: cash-withdrawal scrutiny threshold is PHP 1,000,000."
    page_v2 = page_v1.replace("1,000,000", "2,000,000")  # the threshold moved ⇒ a 'changed' event

    with tempfile.TemporaryDirectory() as tmp:
        sf = Path(tmp) / "freshness-state.json"

        # check_source against a single page, no prior state ⇒ 'new'
        ev_new = check_source(entry, None, fetcher=CannedFetcher({entry["url"]: page_v1}))
        check("check_source first sighting ⇒ 'new'", ev_new["event"] == "new", str(ev_new))
        check("check_source returns url/name/hash/checked_at",
              ev_new["url"] == entry["url"] and ev_new["name"] == entry["name"]
              and bool(ev_new["content_hash"]) and bool(ev_new["checked_at"]))
        check("content_hash matches scrapers.content_hash", ev_new["content_hash"] == content_hash(page_v1))

        # same content as last-seen ⇒ 'unchanged'
        ev_same = check_source(entry, ev_new["content_hash"], fetcher=CannedFetcher({entry["url"]: page_v1}))
        check("check_source same hash ⇒ 'unchanged'", ev_same["event"] == "unchanged", str(ev_same))

        # changed content vs last-seen ⇒ 'changed'
        ev_chg = check_source(entry, ev_new["content_hash"], fetcher=CannedFetcher({entry["url"]: page_v2}))
        check("check_source moved page ⇒ 'changed'", ev_chg["event"] == "changed", str(ev_chg))

        # fetch failure ⇒ 'error', never a crash (CannedFetcher has no page for this url)
        ev_err = check_source({"url": "https://nope.example/x", "name": "n"}, None,
                              fetcher=CannedFetcher({entry["url"]: page_v1}))
        check("fetch failure ⇒ 'error' (no crash)", ev_err["event"] == "error" and "error" in ev_err, str(ev_err))

        # ── check_all drives state across three polls (v1→v1→v2) ──
        # 1) first poll: cold state ⇒ 'new', and state is persisted
        ev1 = check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v1}), state_file=sf)
        check("check_all first poll ⇒ 'new'", len(ev1) == 1 and ev1[0]["event"] == "new", str(ev1))
        check("state file written", sf.exists())
        saved = load_state(sf)
        check("state stores last-seen hash by url",
              saved.get(entry["url"], {}).get("content_hash") == content_hash(page_v1), str(saved))

        # 2) second poll, SAME page ⇒ 'unchanged'
        ev2 = check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v1}), state_file=sf)
        check("check_all unchanged page ⇒ 'unchanged'", ev2[0]["event"] == "unchanged", str(ev2))

        # 3) third poll, CHANGED page ⇒ 'changed', and state advances to v2's hash
        ev3 = check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v2}), state_file=sf)
        check("check_all moved page ⇒ 'changed'", ev3[0]["event"] == "changed", str(ev3))
        check("state advanced to new hash",
              load_state(sf).get(entry["url"], {}).get("content_hash") == content_hash(page_v2))

        # ── enqueue: an InMemory/Sqlite queue receives a reingest job on a CHANGE ──
        q = queues.SqliteQueue(str(Path(tmp) / "q.sqlite"), key="freshness-test")
        # cold state in a fresh file ⇒ a 'new' event ⇒ should enqueue when enqueue=True
        ev_enq = check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v1}),
                           enqueue=True, state_file=Path(tmp) / "enq-state.json", store=q)
        check("enqueue change ⇒ event new/changed", ev_enq[0]["event"] in ("new", "changed"), str(ev_enq))
        check("queue received exactly one reingest job", q.depth() == 1, str(q.depth()))
        job = q.pull()
        check("job kind == 'reingest'", job.get("kind") == REINGEST_KIND, str(job))
        check("job carries the full source entry", job.get("source", {}).get("url") == entry["url"], str(job))

        # an UNCHANGED source must NOT enqueue (no needless re-ingest / no false refresh alert)
        ev_noenq = check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v1}),
                             enqueue=True, state_file=Path(tmp) / "enq-state.json", store=q)
        check("unchanged source ⇒ no enqueue", ev_noenq[0]["event"] == "unchanged" and q.depth() == 0, str(ev_noenq))

        # enqueue=False must never touch the broker (queue stays empty)
        q2 = queues.SqliteQueue(str(Path(tmp) / "q2.sqlite"), key="freshness-test-2")
        check_all(registry, fetcher=CannedFetcher({entry["url"]: page_v2}),
                  enqueue=False, state_file=Path(tmp) / "noenq-state.json", store=q2)
        check("enqueue=False ⇒ broker untouched", q2.depth() == 0)

        # ── state-path resolution is env-only ──
        check("explicit arg wins for state_path", state_path(sf) == sf)
        saved_env = os.environ.pop(STATE_ENV, None)
        try:
            os.environ[STATE_ENV] = str(Path(tmp) / "from-env.json")
            check("OH_FRESHNESS_STATE drives state_path",
                  state_path() == Path(tmp) / "from-env.json")
            os.environ.pop(STATE_ENV, None)
            check("default state_path falls back to dist/", str(state_path()) == DEFAULT_STATE_PATH)
        finally:
            if saved_env is not None:
                os.environ[STATE_ENV] = saved_env

        # corrupt/missing state must degrade to {} (a poller can't be wedged by a bad cursor file)
        bad = Path(tmp) / "bad.json"
        bad.write_text("{ not json", encoding="utf-8")
        check("corrupt state file ⇒ {} (no crash)", load_state(bad) == {})
        check("missing state file ⇒ {}", load_state(Path(tmp) / "absent.json") == {})

    print(f"\n{'all freshness self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Official-site update checker (CDC) for the governed corpus.")
    p.add_argument("--self-test", action="store_true", help="run the offline self-test and exit")
    p.add_argument("--check", action="store_true", help="poll registered sources for changes (live)")
    p.add_argument("--enqueue", action="store_true",
                   help="enqueue a reingest job for each new/changed source (with --check)")
    p.add_argument("--state", default=None,
                   help=f"state file path (default: ${STATE_ENV} or {DEFAULT_STATE_PATH})")
    p.add_argument("--registry", default=None, help="registry path (default: data/source-registry.jsonl)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.check:
        return _check(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
