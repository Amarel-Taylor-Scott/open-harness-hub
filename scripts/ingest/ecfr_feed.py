#!/usr/bin/env python3
"""scripts.ingest.ecfr_feed — the LIVE eCFR Versioner connector (freshness showpiece).

The second verified free-source connector, on the same proven pattern as
``sanctions_feed_live`` (fetch via ``HttpFetcher`` / offline ``CannedFetcher`` → parse →
per-record content hash + lineage). Where the sanctions connector proves *contradiction*
(an entity is LISTED), eCFR proves **freshness/CDC**: the eCFR Versioner publishes, per CFR
Title, ``latest_amended_on`` and ``up_to_date_as_of`` — so a cached regulatory context can be
shown *stale at the title level* ("Title 31 was amended on a newer date than your cache").
That is the "current ≠ correct" wedge made real on a free, no-auth, authoritative source.

Source (no auth): ``https://www.ecfr.gov/api/versioner/v1/titles.json`` → ``{"titles": [{number,
name, latest_amended_on, latest_issue_date, up_to_date_as_of, reserved}, …]}`` (verified shape,
50 titles). Each non-reserved title → one freshness record with a stable handle
``ctx://ecfr/title/<N>`` and a content hash over its material freshness fields (the CDC identity).
``changed_since`` diffs a prior snapshot → the per-title rot signals that feed
``scripts.ingest.context_rot`` / a refresh queue.

Deterministic offline (``CannedFetcher`` + a real-format fixture); ``--live`` hits real eCFR.
Stdlib only; reuses ``scrapers.content_hash`` (No-Magic-Values). Mirrors the connector pattern.

CLI:
    python3 scripts/ingest/ecfr_feed.py --self-test          # offline, deterministic
    python3 scripts/ingest/ecfr_feed.py --live               # real fetch (50 titles)
    python3 scripts/ingest/ecfr_feed.py --live --demo        # real fetch + freshness summary
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.foundry.scrapers import CannedFetcher, Fetcher, HttpFetcher, content_hash

# ── Constants (single source of truth; No-Magic-Values) ──────────────────────
ECFR_TITLES_URL = "https://www.ecfr.gov/api/versioner/v1/titles.json"
SOURCE_HANDLE_PREFIX = "ctx://ecfr/title"
PARSER_ID = "ecfr_feed.titles_json.v1"

#: Per-title material freshness fields hashed for the CDC identity (a change in any of these =
#: the cached title context is stale). Order fixed for a stable hash.
_MATERIAL_FIELDS = ("number", "name", "latest_amended_on", "up_to_date_as_of")


@dataclass(frozen=True)
class Lineage:
    source_handle: str
    source_url: str
    parser: str
    retrieved_at: str
    content_hash: str          # hash of the whole payload (snapshot identity)
    titles_total: int
    titles_parsed: int
    titles_reserved_skipped: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _title_hash(t: dict[str, Any]) -> str:
    return content_hash("|".join(str(t.get(f, "")) for f in _MATERIAL_FIELDS))


def fetch_titles(*, fetcher: Fetcher | None = None, url: str = ECFR_TITLES_URL) -> dict[str, Any]:
    """Fetch titles.json; returns the scraper dict + ``content_hash``. Raises on non-200."""
    fetcher = fetcher or HttpFetcher()
    fetched = fetcher.fetch(url)
    if fetched.get("status") != 200:
        raise RuntimeError(f"eCFR fetch returned status {fetched.get('status')!r} for {url!r}")
    fetched["content_hash"] = content_hash(fetched.get("content", ""))
    return fetched


def parse_titles(content: str, *, retrieved_at: str) -> tuple[list[dict[str, Any]], int]:
    """Parse titles.json into per-title freshness records. Returns ``(records, reserved_skipped)``.

    Reserved titles carry no content and are skipped (the count is returned — no silent drop).
    Raises ``ValueError`` on malformed JSON / missing ``titles``.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"eCFR titles.json is not valid JSON: {e}") from e
    titles = data.get("titles")
    if not isinstance(titles, list):
        raise ValueError("eCFR payload missing a 'titles' list")
    records: list[dict[str, Any]] = []
    reserved = 0
    for t in sorted(titles, key=lambda x: int(x.get("number", 0))):
        if t.get("reserved"):
            reserved += 1
            continue
        num = t.get("number")
        records.append({
            "title_number": num,
            "name": t.get("name", ""),
            "latest_amended_on": t.get("latest_amended_on"),
            "latest_issue_date": t.get("latest_issue_date"),
            "up_to_date_as_of": t.get("up_to_date_as_of"),
            "source_handle": f"{SOURCE_HANDLE_PREFIX}/{num}",
            "content_hash": _title_hash(t),
            "retrieved_at": retrieved_at,
        })
    return records, reserved


def load_titles(*, fetcher: Fetcher | None = None, url: str = ECFR_TITLES_URL, bus=None) -> tuple[list[dict[str, Any]], Lineage]:
    """Fetch + parse the eCFR title freshness records + :class:`Lineage`. Raises on empty parse.

    If `bus` (a context_events.EventBus, duck-typed) is passed, emit source.received +
    source_handle.created (Source Systems) — non-breaking + byte-identical when omitted."""
    fetched = fetch_titles(fetcher=fetcher, url=url)
    retrieved_at = fetched.get("fetched_at", "")
    records, reserved = parse_titles(fetched["content"], retrieved_at=retrieved_at)
    if not records:
        raise RuntimeError("eCFR fetch parsed to zero non-reserved titles; refusing empty freshness set")
    lineage = Lineage(
        source_handle=SOURCE_HANDLE_PREFIX,
        source_url=url,
        parser=PARSER_ID,
        retrieved_at=retrieved_at,
        content_hash=fetched["content_hash"],
        titles_total=len(records) + reserved,
        titles_parsed=len(records),
        titles_reserved_skipped=reserved,
    )
    if bus is not None:  # live-dashboard emit (Source Systems) — non-breaking when bus=None
        bus.publish("source.received", component="ecfr_feed", stage="Source Systems",
                    object_ref=lineage.source_handle,
                    payload={"titles": lineage.titles_parsed, "content_hash": (lineage.content_hash or "")[:12]})
        bus.publish("source_handle.created", component="ecfr_feed", stage="Source Systems",
                    object_ref=lineage.source_handle, payload={"titles_parsed": lineage.titles_parsed})
    return records, lineage


def changed_since(prev_hash_by_handle: dict[str, str], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Diff a prior snapshot (handle → content_hash) against fresh records → per-title rot signals.

    Emits ``new`` (handle unseen) / ``changed`` (hash differs) signals — the freshness showpiece:
    "this CFR title was amended since your cache". Deterministic (sorted by handle).
    """
    signals: list[dict[str, Any]] = []
    for r in sorted(records, key=lambda x: x["source_handle"]):
        h = r["source_handle"]
        prev = prev_hash_by_handle.get(h)
        if prev is None:
            signals.append({"source_handle": h, "title_number": r["title_number"], "change": "new",
                            "latest_amended_on": r["latest_amended_on"]})
        elif prev != r["content_hash"]:
            signals.append({"source_handle": h, "title_number": r["title_number"], "change": "changed",
                            "latest_amended_on": r["latest_amended_on"]})
    return signals


# ── Real-format offline fixture (verified eCFR shape; values plausible, not live) ──
_FIXTURE = json.dumps({"titles": [
    {"number": 1, "name": "General Provisions", "latest_amended_on": "2022-12-29",
     "latest_issue_date": "2024-05-17", "up_to_date_as_of": "2026-06-02", "reserved": False},
    {"number": 31, "name": "Money and Finance: Treasury", "latest_amended_on": "2026-05-30",
     "latest_issue_date": "2026-06-01", "up_to_date_as_of": "2026-06-02", "reserved": False},
    {"number": 35, "name": "Reserved", "latest_amended_on": None,
     "latest_issue_date": None, "up_to_date_as_of": None, "reserved": True},
]})


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    fetcher = CannedFetcher({ECFR_TITLES_URL: _FIXTURE})
    records, lineage = load_titles(fetcher=fetcher)

    check("parsed 2 non-reserved titles", lineage.titles_parsed == 2, str(lineage.titles_parsed))
    check("reserved title skipped + counted", lineage.titles_reserved_skipped == 1)
    t31 = next((r for r in records if r["title_number"] == 31), None)
    check("Title 31 handle ctx://ecfr/title/31", t31 and t31["source_handle"] == "ctx://ecfr/title/31", str(t31))
    check("freshness fields carried", t31 and t31["latest_amended_on"] == "2026-05-30" and t31["up_to_date_as_of"] == "2026-06-02")
    check("lineage content_hash (sha256)", len(lineage.content_hash) == 64)

    # ── CDC: a prior snapshot where Title 31 had an OLDER amendment date → 'changed' ──
    prev = {r["source_handle"]: r["content_hash"] for r in records}
    prev["ctx://ecfr/title/31"] = content_hash("|".join(["31", "Money and Finance: Treasury", "2026-01-15", "2026-02-01"]))
    sigs = changed_since(prev, records)
    changed = [s for s in sigs if s["change"] == "changed"]
    check("CDC detects exactly Title 31 changed", len(changed) == 1 and changed[0]["title_number"] == 31, str(changed))
    check("unchanged Title 1 not flagged", not any(s["title_number"] == 1 for s in sigs))

    # ── new-snapshot (no prior) → all 'new' ──
    allnew = changed_since({}, records)
    check("empty prior → all titles 'new'", len(allnew) == 2 and all(s["change"] == "new" for s in allnew))

    # ── determinism ──
    records2, lineage2 = load_titles(fetcher=fetcher)
    check("re-parse byte-identical", records2 == records and lineage2.content_hash == lineage.content_hash)

    print(f"\n{'all ecfr_feed self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _run_live(*, demo: bool) -> int:
    records, lineage = load_titles()
    print("── LIVE eCFR titles ingest (lineage) ──")
    print(json.dumps(lineage.as_dict(), indent=2, sort_keys=True))
    if demo:
        recent = sorted((r for r in records if r["latest_amended_on"]),
                        key=lambda r: r["latest_amended_on"], reverse=True)[:5]
        print("\n── 5 most-recently-amended CFR titles (the freshness signal) ──")
        for r in recent:
            print(f"  Title {r['title_number']:>2} — {r['name']}: amended {r['latest_amended_on']} "
                  f"(up to date as of {r['up_to_date_as_of']})  {r['source_handle']}")
        print(f"\n{lineage.titles_parsed} titles ingested; {lineage.titles_reserved_skipped} reserved skipped. "
              f"changed_since(prior snapshot) would emit a per-title rot signal for each amended title.")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Live eCFR Versioner connector (freshness/CDC showpiece).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic")
    p.add_argument("--live", action="store_true", help="real fetch of eCFR titles.json")
    p.add_argument("--demo", action="store_true", help="with --live: print the freshness summary")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.live:
        return _run_live(demo=args.demo)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
