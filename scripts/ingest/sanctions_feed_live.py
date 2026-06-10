#!/usr/bin/env python3
"""scripts.ingest.sanctions_feed_live — the network-permitted LIVE fetch for the seam.

``scripts.ingest.sanctions_feed`` is the connector: it owns the real feed URLs
(``LIVE_SANCTIONS_SOURCES``) and the real raw-column→record mapping (``normalize``),
and it proves both offline against a synthetic fixture. But it was written in a
network-blocked environment, so it deliberately makes the actual fetch a SEAM that
RAISES — its own docstring says *"a deployment that wires the real fetcher would
implement that branch in a network-permitted environment."*

**This module is that implementation.** It is purely additive — it imports the
connector's sources + ``normalize`` (single source of truth, never duplicated) and
adds only the two things the seam lacked:

  1. a real HTTP fetch (reusing the foundry ``HttpFetcher``; ``urllib`` follows the
     treasury.gov → sanctionslistservice redirect), and
  2. a parser for OFAC's **positional** SDN CSV (no header row) into the raw-row dicts
     ``normalize`` already knows how to map.

So the field mapping, the record contract, and the downstream scorer
(``sanctions_freshness``) / flow (``verified_context_flow``) are all the proven
existing code; this module only closes the fetch. Every fetched batch carries
:class:`Lineage` (source handle, URL, parser id, retrieval time, SHA-256 content hash
= the CDC identity, row accounting) so a parsed entity is auditable back to the fetch.

The self-test runs OFFLINE+deterministically against a :class:`CannedFetcher` with a
real-FORMAT (synthetic-CONTENT) SDN snippet — so CI needs no network. The real fetch
is exercised only via ``--live``.

Stdlib only. CLI:
    python3 scripts/ingest/sanctions_feed_live.py --self-test          # offline
    python3 scripts/ingest/sanctions_feed_live.py --live --limit 800   # real fetch
    python3 scripts/ingest/sanctions_feed_live.py --live --demo --limit 800
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any

# Repo-root importability under direct invocation (mirrors the sibling connector).
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Compose the EXISTING connector (its sources + mapping are the single source of truth)
# and the foundry scraper (real HTTP + the CDC content hash). Nothing re-implemented.
from scripts.foundry.scrapers import CannedFetcher, Fetcher, HttpFetcher, content_hash
from scripts.ingest.sanctions_feed import (
    DEFAULT_SOURCE,
    LIVE_SANCTIONS_SOURCES,
    REQUIRED_RECORD_FIELDS,
    normalize,
)

# ── Constants (single source of truth; No-Magic-Values) ──────────────────────

#: OFAC's SDN.CSV is POSITIONAL (no header). Column order per OFAC's published layout.
#: We read by index; the raw-row keys we emit are the connector's OFAC ``raw_columns``
#: names ("ent_num"/"SDN_Name"/"Program") so ``normalize`` maps them unchanged.
SDN_COL_ENT_NUM = 0
SDN_COL_NAME = 1
SDN_COL_TYPE = 2
SDN_COL_PROGRAM = 3

#: OFAC's null sentinel — a literal ``-0-`` (often trailing-spaced) means "no value".
OFAC_NULL = "-0-"

#: Source key whose positional-CSV parser is implemented here. BIS/EU ship header CSVs
#: (different parse) — declared in the connector, not yet wired here (raise, don't fake).
POSITIONAL_CSV_SOURCE = "ofac_sdn"

#: Parser identity (bump if the positional layout interpretation changes).
PARSER_ID = "sanctions_feed_live.sdn_csv.v1"


@dataclass(frozen=True)
class Lineage:
    """Auditable provenance for one live-fetched-and-parsed sanctions batch."""

    source_handle: str
    source_key: str
    source_url: str
    parser: str
    retrieved_at: str
    content_hash: str
    list_version: str
    list_date: str
    rows_parsed: int
    rows_skipped: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── parsing the positional OFAC SDN CSV ───────────────────────────────────────


def _clean(value: str | None) -> str:
    """Strip whitespace and collapse OFAC's ``-0-`` null sentinel to empty."""
    v = (value or "").strip()
    return "" if v == OFAC_NULL else v


def _derive_list_version(retrieved_at: str, hash_hex: str) -> str:
    """Deterministic version label for a live SDN snapshot.

    The OFAC export carries no inline version, so a snapshot's identity is its
    retrieval date + a short content hash: identical bytes → identical version (CDC
    stable); a changed list → a new version. Date-prefixed so the scorer's version
    key orders snapshots in time.
    """
    date = (retrieved_at or "")[:10] or "unknown"
    return f"OFAC-SDN-LIVE-{date}+{hash_hex[:8]}"


def sdn_csv_to_raw_rows(
    content: str, *, list_version: str, publish_date: str, limit: int | None = None
) -> tuple[list[dict[str, str]], int]:
    """Positional SDN CSV → raw-row dicts keyed by the connector's OFAC raw columns.

    Each emitted row is ``{"ent_num","SDN_Name","Program","_list_version","_publish_date"}``
    — exactly what ``sanctions_feed.normalize(row, source="ofac_sdn")`` consumes. The
    per-fetch ``list_version``/``publish_date`` are injected into every row (the CSV has
    no such field). Rows with no usable ent_num/name are skipped; the skip count is
    returned (no silent truncation). Returns ``(raw_rows, skipped)``.
    """
    raw_rows: list[dict[str, str]] = []
    skipped = 0
    reader = csv.reader(io.StringIO(content))
    for row in reader:
        if not row or len(row) <= SDN_COL_PROGRAM:
            skipped += 1
            continue
        ent_num = _clean(row[SDN_COL_ENT_NUM])
        name = _clean(row[SDN_COL_NAME])
        program = _clean(row[SDN_COL_PROGRAM])
        if not ent_num or not name or not program:
            # normalize() requires all three; a row missing one is malformed, not mapped.
            skipped += 1
            continue
        raw_rows.append({
            "ent_num": f"OFAC-{ent_num}",  # stable entity id across snapshots
            "SDN_Name": name,
            "Program": program,
            "_list_version": list_version,
            "_publish_date": publish_date,
        })
        if limit is not None and len(raw_rows) >= limit:
            break
    return raw_rows, skipped


# ── the live entrypoint ───────────────────────────────────────────────────────


def fetch_live_records(
    source: str = DEFAULT_SOURCE,
    *,
    fetcher: Fetcher | None = None,
    limit: int | None = None,
    bus=None,
) -> tuple[list[dict[str, str]], Lineage]:
    """Fetch + parse a live sanctions feed into records + :class:`Lineage`.

    Records go straight into ``sanctions_freshness.parse_list`` /
    ``verified_context_flow.run``. Only ``ofac_sdn`` (positional CSV) is wired here;
    ``bis_entity_list`` / ``eu_consolidated`` raise ``NotImplementedError`` (their
    header-CSV parse is the next increment — declared in the connector, not faked).

    Raises:
      KeyError:            unknown ``source``.
      NotImplementedError: a declared source whose live parse isn't wired yet.
      RuntimeError:        non-200 fetch, or a fetch that parsed to zero records
                           (fail closed — an empty list makes every claim look clear).
    """
    if source not in LIVE_SANCTIONS_SOURCES:
        raise KeyError(f"unknown sanctions source {source!r}; known: {sorted(LIVE_SANCTIONS_SOURCES)}")
    if source != POSITIONAL_CSV_SOURCE:
        raise NotImplementedError(
            f"live parse for {source!r} not wired yet (header-CSV); "
            f"only {POSITIONAL_CSV_SOURCE!r} is implemented. URL is declared in the connector."
        )

    url = LIVE_SANCTIONS_SOURCES[source]["url"]
    fetcher = fetcher or HttpFetcher()
    fetched = fetcher.fetch(url)
    if fetched.get("status") != 200:
        raise RuntimeError(f"sanctions fetch returned status {fetched.get('status')!r} for {url!r}")

    content = fetched.get("content", "")
    chash = content_hash(content)
    retrieved_at = fetched.get("fetched_at", "")
    list_version = _derive_list_version(retrieved_at, chash)
    publish_date = retrieved_at[:10]

    raw_rows, skipped = sdn_csv_to_raw_rows(
        content, list_version=list_version, publish_date=publish_date, limit=limit
    )
    # Map each raw row through the EXISTING, proven connector mapping.
    records = [normalize(row, source=source) for row in raw_rows]
    if not records:
        raise RuntimeError(
            f"live {source!r} fetch parsed to zero records ({len(content)} bytes, {skipped} skipped); "
            "refusing to hand an empty list to the verifier"
        )

    lineage = Lineage(
        source_handle=f"ctx://{source.replace('_', '/')}",
        source_key=source,
        source_url=url,
        parser=PARSER_ID,
        retrieved_at=retrieved_at,
        content_hash=chash,
        list_version=list_version,
        list_date=publish_date,
        rows_parsed=len(records),
        rows_skipped=skipped,
    )
    if bus is not None:  # live-dashboard emit (Source Systems stage) — non-breaking when bus=None
        bus.publish("source.received", component="sanctions_feed_live", stage="Source Systems",
                    object_ref=lineage.source_handle,
                    payload={"source": source, "records": len(records), "content_hash": (chash or "")[:12]})
        bus.publish("source_handle.created", component="sanctions_feed_live", stage="Source Systems",
                    object_ref=lineage.source_handle, payload={"list_version": list_version})
    return records, lineage


# ── A real-FORMAT, synthetic-CONTENT SDN snippet for the offline self-test ────
# Real OFAC SDN CSV LAYOUT (positional, -0- nulls, quoted comma-bearing names);
# invented ent_nums/names (NOT real designations).
_FIXTURE_SDN_CSV = (
    '9001,"SYNTHETIC TRADING CO., LTD.",-0- ,"DEMO-PROGRAM",-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,"a.k.a. \'STC\'."\n'
    '9002,"EXAMPLE LOGISTICS GROUP",individual ,"DEMO-PROGRAM",-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- \n'
    '9003,"PLACEHOLDER HOLDINGS",-0- ,"DEMO-PROGRAM-2",-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- \n'
    ',,,,\n'                                   # a malformed/blank row → must be skipped
    '9004,"MISSING PROGRAM CO.",-0- ,-0- ,-0- \n'  # null program → skipped (normalize needs it)
)


def _self_test() -> int:
    from scripts.sanctions import sanctions_freshness
    from scripts.sanctions.sanctions_freshness import STATUS_CLEAR
    from scripts.pipeline import verified_context_flow

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    fetcher = CannedFetcher({LIVE_SANCTIONS_SOURCES[POSITIONAL_CSV_SOURCE]["url"]: _FIXTURE_SDN_CSV})
    records, lineage = fetch_live_records(POSITIONAL_CSV_SOURCE, fetcher=fetcher)

    # ── parsing: 3 good rows; 2 malformed skipped (no silent truncation). ──
    check("parsed 3 valid records", len(records) == 3, str(len(records)))
    check("2 malformed rows skipped + accounted", lineage.rows_skipped == 2, str(lineage.rows_skipped))
    check("entity_id = OFAC-<ent_num>", records[0]["entity_id"] == "OFAC-9001", records[0]["entity_id"])
    check("quoted comma-bearing name parsed", records[0]["name"] == "SYNTHETIC TRADING CO., LTD.", records[0]["name"])
    check("program from col 3", records[0]["program"] == "DEMO-PROGRAM", records[0]["program"])

    # ── lineage is complete + auditable. ──
    check("lineage content_hash (sha256)", len(lineage.content_hash) == 64)
    check("lineage version is date+hash derived", lineage.list_version.startswith("OFAC-SDN-LIVE-"), lineage.list_version)
    check("source handle ctx://ofac/sdn", lineage.source_handle == "ctx://ofac/sdn", lineage.source_handle)

    # ── records are accepted by the REAL scorer contract + carry the live version. ──
    parsed = sanctions_freshness.parse_list(records)
    check("parse_list accepts live records", parsed["count"] == 3, str(parsed["count"]))
    check("parse_list carries the live version", parsed["list_version"] == lineage.list_version)

    # ── END-TO-END: a CLEAR claim on a LISTED entity → would-be violation, HELD OUT. ──
    internal_claims = [{
        "claim_id": "internal-stc-clearance",
        "entity_id": "OFAC-9001",
        "status": STATUS_CLEAR,
        "cites_list_version": "OFAC-SDN-LIVE-2020-01-01+00000000",  # older snapshot
        "text": "Internal screening: SYNTHETIC TRADING CO., LTD. is CLEAR for onboarding.",
    }]
    bundle = verified_context_flow.run(records, internal_claims)
    viol = bundle["verification_report"]["would_be_violations"]
    check("CLEAR-on-listed is a would-be violation", len(viol) == 1, str(len(viol)))
    check("would-be violation HELD OUT of served corpus",
          "internal-stc-clearance" in bundle["verification_report"]["held_out_claim_ids"])
    check("cleared-but-listed claim absent from served llms.txt",
          "SYNTHETIC TRADING CO., LTD. is CLEAR" not in bundle["served"]["llms_txt"])

    # ── determinism on identical bytes (CDC stable). ──
    records2, lineage2 = fetch_live_records(POSITIONAL_CSV_SOURCE, fetcher=fetcher)
    check("identical bytes → identical version (CDC)", lineage2.list_version == lineage.list_version)
    check("re-parse byte-identical", records2 == records)

    # ── unwired sources raise (declared, not faked). ──
    for s in ("bis_entity_list", "eu_consolidated"):
        raised = False
        try:
            fetch_live_records(s, fetcher=fetcher)
        except NotImplementedError:
            raised = True
        check(f"{s} live parse not faked (raises)", raised)

    print(f"\n{'all sanctions_feed_live self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _run_live_demo(*, limit: int | None) -> int:
    """REAL fetch of the live OFAC SDN list + run the verified-context flow against it."""
    from scripts.sanctions.sanctions_freshness import STATUS_CLEAR, STATUS_LISTED
    from scripts.pipeline import verified_context_flow

    records, lineage = fetch_live_records(POSITIONAL_CSV_SOURCE, limit=limit)
    print("── LIVE OFAC SDN ingest (lineage) ──")
    print(json.dumps(lineage.as_dict(), indent=2, sort_keys=True))

    e_clear, e_listed = records[0], records[1]
    older = "OFAC-SDN-LIVE-2020-01-01+00000000"
    internal_claims = [
        {  # an internal doc WRONGLY calls a really-listed entity "clear" → would-be violation
            "claim_id": f"internal-{e_clear['entity_id']}-clearance",
            "entity_id": e_clear["entity_id"], "status": STATUS_CLEAR,
            "cites_list_version": older,
            "text": f"Internal screening: {e_clear['name']} is CLEAR for onboarding.",
        },
        {  # an internal doc correctly calls a listed entity "listed" → served
            "claim_id": f"internal-{e_listed['entity_id']}-block",
            "entity_id": e_listed["entity_id"], "status": STATUS_LISTED,
            "cites_list_version": lineage.list_version,
            "text": f"Internal screening: {e_listed['name']} is LISTED; block transactions.",
        },
    ]
    bundle = verified_context_flow.run(records, internal_claims)
    print("\n── verified-context flow against the LIVE list ──")
    print(bundle["summary"]["headline"])
    for v in bundle["verification_report"]["would_be_violations"]:
        print(f"  WOULD-BE VIOLATION: {v['claim_id']} — {v['detail']}")
    print(f"  list entities ingested: {lineage.rows_parsed} (skipped {lineage.rows_skipped})")
    print(f"  served claims: {bundle['summary']['claims_served']}/{bundle['summary']['claims_total']}")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Live OFAC SDN fetch (closes the sanctions_feed seam).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic (CannedFetcher)")
    p.add_argument("--live", action="store_true", help="REAL fetch of the OFAC SDN list")
    p.add_argument("--demo", action="store_true", help="with --live: run the verified-context flow")
    p.add_argument("--limit", type=int, default=None, help="cap parsed rows (demo speed)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.live:
        if args.demo:
            return _run_live_demo(limit=args.limit)
        records, lineage = fetch_live_records(limit=args.limit)
        print(json.dumps({"lineage": lineage.as_dict(), "sample": records[:3]}, indent=2, sort_keys=True))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
