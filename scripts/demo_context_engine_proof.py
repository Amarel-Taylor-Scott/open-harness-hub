#!/usr/bin/env python3
"""demo_context_engine_proof — the whole Baltor Context Engine in one runnable proof.

Ties the three proven modules into a single end-to-end demonstration of the thesis —
*decompose raw sources into addressable objects → verify against the authoritative source →
keep it fresh* — with source handles and a held-out promotion boundary throughout:

  1. **Decomposition** (`scripts.ingest.document_decompose`): a policy document becomes a
     recursive tree of addressable, typed objects; a claim attaches to a LEAF paragraph and
     expansion returns exactly that node (the whole doc never enters a window).
  2. **Verification** (`scripts.ingest.sanctions_feed_live` → `scripts.pipeline.verified_context_flow`):
     an internal screening doc claiming a really-LISTED entity is CLEAR is caught as a would-be
     sanctions violation and HELD OUT of the served corpus; the verified claim is served.
  3. **Context rot** (`scripts.ingest.context_rot`): the cached, served context is re-assessed —
     a changed upstream hash forces a refresh, a fresh pack item serves — so freshness is decided
     per item, not "the doc is stale".

Default run is **fully offline + deterministic** (CannedFetcher + a fixed ``now_s``), so it is a
real reproducible proof — not a mock. ``--live`` flips step 2 to a REAL OFAC SDN fetch (network).
Composes the shipped, self-tested modules; re-implements nothing. Stdlib only.

CLI:
    python3 scripts/demo_context_engine_proof.py            # offline, deterministic
    python3 scripts/demo_context_engine_proof.py --self-test
    python3 scripts/demo_context_engine_proof.py --live --limit 300
"""
from __future__ import annotations

import argparse

# Repo-root importable under direct invocation (this file is <root>/scripts/…; root is 2 up).
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.foundry.scrapers import CannedFetcher, content_hash
from scripts.ingest import context_rot
from scripts.ingest.document_decompose import (
    KIND_HEADING, KIND_PARAGRAPH, CannedParser, decompose, expand, resolve,
)
from scripts.ingest.sanctions_feed import LIVE_SANCTIONS_SOURCES
from scripts.ingest.sanctions_feed_live import POSITIONAL_CSV_SOURCE, fetch_live_records
from scripts.pipeline import verified_context_flow
from scripts.sanctions.sanctions_freshness import STATUS_CLEAR, STATUS_LISTED

#: A fixed epoch second so the offline run is deterministic (No clock — proof discipline).
DEMO_NOW_S = 1_000_000_000

#: Real-FORMAT, synthetic-CONTENT OFAC SDN snippet for the offline path (invented SYN ids).
_OFFLINE_SDN_CSV = (
    '9001,"SYNTHETIC TRADING CO., LTD.",-0- ,"DEMO-PROGRAM",-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- \n'
    '9002,"EXAMPLE LOGISTICS GROUP",-0- ,"DEMO-PROGRAM",-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- \n'
)


def _decompose_thread() -> dict:
    """Step 1: decompose a policy doc; cite a leaf; expand to exactly that node."""
    parsed = {"pages": [
        {"page_no": 1, "blocks": [
            {"kind": KIND_HEADING, "ordinal": 0, "text": "Sanctions Screening Policy", "confidence": 0.99},
            {"kind": KIND_PARAGRAPH, "ordinal": 1, "confidence": 0.97,
             "text": "All counterparties must be screened against the current authoritative list before onboarding.",
             "bbox": {"x": 112.4, "y": 204.8, "width": 392.1, "height": 44.6, "unit": "pt"}},
        ]},
    ]}
    tree = decompose("acme", "screening-policy", CannedParser(parsed, version="1").parse(None),
                     parser="canned", parser_version="1")
    cited = "ctx://acme/doc/screening-policy#page=0001&block=02"
    node = resolve(tree, cited)
    ex = expand(tree, cited, with_parent=True)
    return {"tree": tree, "cited_handle": cited, "cited_text": node.text if node else None,
            "expanded_kind": ex["node"]["kind"], "parent_kind": ex["parent"]["kind"],
            "node_count": len(tree.nodes)}


def _verify_thread(*, live: bool, limit: int | None) -> dict:
    """Step 2: ingest the authoritative list (offline fixture or LIVE OFAC) → verified-context flow."""
    if live:
        records, lineage = fetch_live_records(POSITIONAL_CSV_SOURCE, limit=limit)
        list_version = lineage.list_version
        e_clear, e_listed = records[0], records[1]
    else:
        fetcher = CannedFetcher({LIVE_SANCTIONS_SOURCES[POSITIONAL_CSV_SOURCE]["url"]: _OFFLINE_SDN_CSV})
        records, lineage = fetch_live_records(POSITIONAL_CSV_SOURCE, fetcher=fetcher, limit=limit)
        list_version = lineage.list_version
        e_clear, e_listed = records[0], records[1]

    internal_claims = [
        {  # WRONG: internal doc calls a really-listed entity CLEAR, citing an older snapshot
            "claim_id": f"internal-{e_clear['entity_id']}-clearance",
            "entity_id": e_clear["entity_id"], "status": STATUS_CLEAR,
            "cites_list_version": "OFAC-SDN-LIVE-2020-01-01+00000000",
            "text": f"Internal screening: {e_clear['name']} is CLEAR for onboarding.",
        },
        {  # CORRECT: internal doc calls a listed entity LISTED, citing the current snapshot
            "claim_id": f"internal-{e_listed['entity_id']}-block",
            "entity_id": e_listed["entity_id"], "status": STATUS_LISTED,
            "cites_list_version": list_version,
            "text": f"Internal screening: {e_listed['name']} is LISTED; block transactions.",
        },
    ]
    bundle = verified_context_flow.run(records, internal_claims)
    return {"lineage": lineage, "bundle": bundle, "list_version": list_version,
            "entities_ingested": lineage.rows_parsed}


def _rot_thread(list_version: str, *, now_s: int) -> dict:
    """Step 3: re-assess the cached served context — one item's upstream changed → refresh."""
    snapshot_hash = content_hash(f"OFAC SDN snapshot {list_version}")
    items = [
        # the served pack — fresh, no change signal → serve
        (context_rot.CachedItem("ctx://baltor/pack/screening", "pack",
                                now_s - context_rot.SECONDS_PER_HOUR, content_hash("served pack v1")),
         {"current_content_hash": content_hash("served pack v1")}),
        # the OFAC raw snapshot the pack was verified against — upstream changed → refresh
        (context_rot.CachedItem("ctx://ofac/sdn", "raw_snapshot",
                                now_s - 2 * context_rot.SECONDS_PER_HOUR, snapshot_hash),
         {"current_content_hash": content_hash(f"OFAC SDN snapshot {list_version} + new designation")}),
    ]
    return context_rot.assess_pack(items, now_s=now_s)


def run_demo(*, live: bool = False, limit: int | None = None, now_s: int = DEMO_NOW_S) -> dict:
    d = _decompose_thread()
    v = _verify_thread(live=live, limit=limit)
    r = _rot_thread(v["list_version"], now_s=now_s)
    summary = v["bundle"]["summary"]
    violations = v["bundle"]["verification_report"]["would_be_violations"]
    return {"decompose": d, "verify": v, "rot": r,
            "headline": (
                f"CONTEXT ENGINE PROOF ({'LIVE' if live else 'offline'}): "
                f"decomposed a policy doc → {d['node_count']} addressable objects, cited a leaf and "
                f"expanded to exactly that {d['expanded_kind']}; "
                f"ingested {v['entities_ingested']} entities from {v['list_version']}, "
                f"verified {summary['claims_served']}/{summary['claims_total']} claims and HELD OUT "
                f"{len(violations)} would-be sanctions violation(s) with provenance; "
                f"rot check → {r['headline']}."
            )}


def _print_demo(res: dict) -> None:
    d, v, r = res["decompose"], res["verify"], res["rot"]
    print("── 1. DECOMPOSITION ──")
    print(f"  doc → {d['node_count']} objects; cited leaf {d['cited_handle']}")
    print(f"  expansion returned a {d['expanded_kind']} (parent: {d['parent_kind']}); text: {d['cited_text']!r}")
    print("\n── 2. VERIFICATION (ingest → assure → serve) ──")
    print(f"  {v['bundle']['summary']['headline']}")
    for viol in v["bundle"]["verification_report"]["would_be_violations"]:
        print(f"  HELD OUT: {viol['claim_id']} — {viol['detail']}")
    print("\n── 3. CONTEXT ROT (per-item freshness) ──")
    for a in r["assessments"]:
        print(f"  {a['handle']}: {a['state']} → {a['action']} ({a['reason']})")
    print(f"\n{res['headline']}")


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    res = run_demo(live=False)
    d, v, r = res["decompose"], res["verify"], res["rot"]

    # Step 1 — decomposition contract.
    check("doc decomposed to >=3 addressable objects", d["node_count"] >= 3, str(d["node_count"]))
    check("cited leaf is a paragraph; expansion returns exactly it", d["expanded_kind"] == KIND_PARAGRAPH and d["parent_kind"] == "page")

    # Step 2 — verification + held-out promotion boundary.
    summary = v["bundle"]["summary"]
    check("exactly 1 would-be violation held out", summary["would_be_violations"] == 1, str(summary["would_be_violations"]))
    check("the violation is NOT in the served llms.txt",
          "SYNTHETIC TRADING CO., LTD. is CLEAR" not in v["bundle"]["served"]["llms_txt"])
    check("the correct claim WAS served", summary["claims_served"] == 1)

    # Step 3 — context rot.
    check("rot held nothing blocking but flagged the changed snapshot for refresh",
          r["servable"] is True and "ctx://ofac/sdn" in r["refresh_handles"], str(r["refresh_handles"]))

    # Determinism — the whole offline proof re-runs identically.
    res2 = run_demo(live=False)
    check("end-to-end offline demo is deterministic", res2["headline"] == res["headline"])

    print(f"\n{'all demo_context_engine_proof self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baltor Context Engine — one runnable end-to-end proof.")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic assertions")
    p.add_argument("--live", action="store_true", help="step 2 fetches the REAL OFAC SDN list")
    p.add_argument("--limit", type=int, default=300, help="cap parsed sanctions rows (demo speed)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    _print_demo(run_demo(live=args.live, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
