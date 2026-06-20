#!/usr/bin/env python3
"""scripts.ingest.federal_register_feed — LIVE Federal Register connector (free, no auth).

Third verified free-source connector, on the same proven pattern as `sanctions_feed_live` /
`ecfr_feed` (fetch via `HttpFetcher` / offline `CannedFetcher` → parse → per-record content hash +
lineage → `changed_since` CDC). The Federal Register API publishes newly-issued federal regulatory
documents (rules, proposed rules, notices, presidential docs) with a `publication_date` — a real,
authoritative freshness stream: "a new rule from agency X published on DATE that your cached
regulatory context doesn't have yet."

Source (no auth): ``https://www.federalregister.gov/api/v1/documents.json`` →
``{"count", "results": [{document_number, title, type, publication_date, html_url, agencies}, …]}``
(verified shape). Each document → one record with a stable handle
``ctx://federalregister/document/<document_number>`` + a content hash over its material fields.

Deterministic offline (`CannedFetcher` + a real-format fixture); ``--live`` hits the real API.
Stdlib only; reuses `scrapers.content_hash` (No-Magic-Values). Mirrors the connector pattern.

CLI:
    python3 scripts/ingest/federal_register_feed.py --self-test          # offline, deterministic
    python3 scripts/ingest/federal_register_feed.py --live --demo        # real fetch + summary
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
#: Newest documents, bounded page, only the fields we map (smaller, faster, stable).
FR_DOCS_URL = (
    "https://www.federalregister.gov/api/v1/documents.json"
    "?per_page=20&order=newest"
    "&fields[]=document_number&fields[]=title&fields[]=type"
    "&fields[]=publication_date&fields[]=html_url&fields[]=agencies"
)
SOURCE_HANDLE_PREFIX = "ctx://federalregister/document"
PARSER_ID = "federal_register_feed.documents_json.v1"
_MATERIAL_FIELDS = ("document_number", "title", "type", "publication_date")


@dataclass(frozen=True)
class Lineage:
    source_handle: str
    source_url: str
    parser: str
    retrieved_at: str
    content_hash: str
    documents_total: int
    documents_parsed: int
    documents_skipped: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _doc_hash(d: dict[str, Any]) -> str:
    return content_hash("|".join(str(d.get(f, "")) for f in _MATERIAL_FIELDS))


def fetch_documents(*, fetcher: Fetcher | None = None, url: str = FR_DOCS_URL) -> dict[str, Any]:
    fetcher = fetcher or HttpFetcher()
    fetched = fetcher.fetch(url)
    if fetched.get("status") != 200:
        raise RuntimeError(f"Federal Register fetch returned status {fetched.get('status')!r} for {url!r}")
    fetched["content_hash"] = content_hash(fetched.get("content", ""))
    return fetched


def parse_documents(content: str, *, retrieved_at: str, limit: int | None = None) -> tuple[list[dict[str, Any]], int]:
    """Parse documents.json into per-document records. Returns ``(records, skipped)``."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Federal Register documents.json is not valid JSON: {e}") from e
    results = data.get("results")
    if not isinstance(results, list):
        raise ValueError("Federal Register payload missing a 'results' list")
    records: list[dict[str, Any]] = []
    skipped = 0
    for d in results:
        num = d.get("document_number")
        if not num or not d.get("title"):
            skipped += 1
            continue
        agencies = d.get("agencies") or []
        agency = (agencies[0].get("name") if agencies and isinstance(agencies[0], dict) else None)
        records.append({
            "document_number": num,
            "title": d.get("title", ""),
            "type": d.get("type"),
            "publication_date": d.get("publication_date"),
            "agency": agency,
            "html_url": d.get("html_url"),
            "source_handle": f"{SOURCE_HANDLE_PREFIX}/{num}",
            "content_hash": _doc_hash(d),
            "retrieved_at": retrieved_at,
        })
        if limit is not None and len(records) >= limit:
            break
    return records, skipped


def load_documents(*, fetcher: Fetcher | None = None, url: str = FR_DOCS_URL,
                   limit: int | None = None, bus=None) -> tuple[list[dict[str, Any]], Lineage]:
    fetched = fetch_documents(fetcher=fetcher, url=url)
    retrieved_at = fetched.get("fetched_at", "")
    records, skipped = parse_documents(fetched["content"], retrieved_at=retrieved_at, limit=limit)
    if not records:
        raise RuntimeError("Federal Register fetch parsed to zero documents; refusing empty set")
    lineage = Lineage(
        source_handle=SOURCE_HANDLE_PREFIX, source_url=url, parser=PARSER_ID,
        retrieved_at=retrieved_at, content_hash=fetched["content_hash"],
        documents_total=len(records) + skipped, documents_parsed=len(records), documents_skipped=skipped,
    )
    if bus is not None:  # live-dashboard emit (Source Systems) — non-breaking when bus=None
        bus.publish("source.received", component="federal_register_feed", stage="Source Systems",
                    object_ref=lineage.source_handle,
                    payload={"documents": lineage.documents_parsed, "content_hash": (lineage.content_hash or "")[:12]})
        bus.publish("source_handle.created", component="federal_register_feed", stage="Source Systems",
                    object_ref=lineage.source_handle, payload={"documents_parsed": lineage.documents_parsed})
    return records, lineage


def changed_since(prev_hash_by_handle: dict[str, str], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Diff a prior snapshot → per-document rot signals (new/changed). Deterministic (sorted)."""
    signals: list[dict[str, Any]] = []
    for r in sorted(records, key=lambda x: x["source_handle"]):
        h = r["source_handle"]
        prev = prev_hash_by_handle.get(h)
        if prev is None:
            signals.append({"source_handle": h, "document_number": r["document_number"], "change": "new",
                            "publication_date": r["publication_date"]})
        elif prev != r["content_hash"]:
            signals.append({"source_handle": h, "document_number": r["document_number"], "change": "changed",
                            "publication_date": r["publication_date"]})
    return signals


# ── Real-format offline fixture (verified FR shape; plausible synthetic docs) ──
_FIXTURE = json.dumps({"count": 2, "results": [
    {"document_number": "2026-12345", "title": "Amendment to Export Administration Regulations",
     "type": "Rule", "publication_date": "2026-06-03", "html_url": "https://www.federalregister.gov/d/2026-12345",
     "agencies": [{"id": 1, "name": "Bureau of Industry and Security"}]},
    {"document_number": "2026-12346", "title": "Notice of Sanctions Actions",
     "type": "Notice", "publication_date": "2026-06-03", "html_url": "https://www.federalregister.gov/d/2026-12346",
     "agencies": [{"id": 2, "name": "Office of Foreign Assets Control"}]},
    {"title": "malformed — no document_number"},  # → skipped
]})


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    fetcher = CannedFetcher({FR_DOCS_URL: _FIXTURE})
    records, lineage = load_documents(fetcher=fetcher)

    check("parsed 2 valid documents", lineage.documents_parsed == 2, str(lineage.documents_parsed))
    check("1 malformed doc skipped + counted", lineage.documents_skipped == 1)
    d0 = next((r for r in records if r["document_number"] == "2026-12345"), None)
    check("handle ctx://federalregister/document/<num>", d0 and d0["source_handle"] == "ctx://federalregister/document/2026-12345")
    check("agency + type + pub date carried", d0 and d0["agency"] == "Bureau of Industry and Security"
          and d0["type"] == "Rule" and d0["publication_date"] == "2026-06-03")
    check("lineage content_hash (sha256)", len(lineage.content_hash) == 64)

    # CDC: a prior snapshot where doc 12345 had an older title → 'changed'; the other unchanged.
    prev = {r["source_handle"]: r["content_hash"] for r in records}
    prev["ctx://federalregister/document/2026-12345"] = content_hash("|".join(
        ["2026-12345", "OLD TITLE", "Rule", "2026-06-03"]))
    sigs = changed_since(prev, records)
    changed = [s for s in sigs if s["change"] == "changed"]
    check("CDC isolates exactly the changed document", len(changed) == 1 and changed[0]["document_number"] == "2026-12345", str(changed))
    allnew = changed_since({}, records)
    check("empty prior → all 'new'", len(allnew) == 2 and all(s["change"] == "new" for s in allnew))

    records2, lineage2 = load_documents(fetcher=fetcher)
    check("re-parse byte-identical", records2 == records and lineage2.content_hash == lineage.content_hash)

    print(f"\n{'all federal_register_feed self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _run_live(*, demo: bool) -> int:
    records, lineage = load_documents()
    print("── LIVE Federal Register ingest (lineage) ──")
    print(json.dumps(lineage.as_dict(), indent=2, sort_keys=True))
    if demo:
        print("\n── newest federal documents (the freshness signal) ──")
        for r in records[:5]:
            print(f"  {r['publication_date']}  [{r['type']}]  {r['title'][:70]}  ({r['agency']})  {r['source_handle']}")
        print(f"\n{lineage.documents_parsed} documents ingested; changed_since(prior) emits a per-document rot signal for each new/changed doc.")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Live Federal Register connector (free, no auth; freshness/CDC).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic")
    p.add_argument("--live", action="store_true", help="real fetch of documents.json")
    p.add_argument("--demo", action="store_true", help="with --live: print the newest-documents summary")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.live:
        return _run_live(demo=args.demo)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
