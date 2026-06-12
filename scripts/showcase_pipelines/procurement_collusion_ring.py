#!/usr/bin/env python3
"""Showcase: PROCUREMENT collusion / bid-rigging ring detection — a relationship network over tenders.

Another relationship-network use case: a bid-rigging ring is a set of "competing" vendors who
secretly coordinate — they rotate who wins across tenders and submit COVER BIDS (deliberately high
losing bids) to simulate competition. Seen one tender at a time it looks like a fair auction; the
ring only shows up when you AGGREGATE across many tenders.

Structural gap (durability: AGGREGATION + pattern over a corpus): a frontier model scores each tender
in isolation and calls it competitive. The ring is a property of the whole bid history — who always
bids together, whether wins rotate inside that group, and whether the losing group bids cluster just
above the winner (the cover-bid tell). That is deterministic aggregation over a governed bid ledger.

Composition (real `scripts/processors` callables + deterministic bid-pattern aggregation):
  1. _cobid_graph            — vendors who repeatedly bid on the SAME tenders → a co-bidding graph
  2. _ring_signals          — within a frequent co-bidding group: do wins ROTATE, and are the losing
                              group bids COVER BIDS (tightly just above the winner)? — the domain step
  3. graphrag_retrieve       — present the co-bidding subgraph
  4. source_precedence_select— a signed award notice governs over a scraped tender-aggregator feed
  5. escalate_human + deliver_report — flag the ring with the rotation + cover-bid evidence

Run:  python3 scripts/showcase_pipelines/procurement_collusion_ring.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from itertools import combinations
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.graphrag_retrieve import run as graph_run
from scripts.processors.retrieval.source_precedence_select import run as precedence_run
from scripts.processors.deliver.escalate_human import run as escalate_run
from scripts.processors.deliver.deliver_report import run as report_run

#: A vendor pair must co-bid on at least this many tenders to count as a persistent relationship.
MIN_COBIDS = 3
#: A losing bid within this fraction ABOVE the winning bid is a likely "cover bid" (fake competition).
COVER_BID_BAND = 0.05
#: A group is flagged as a ring when this share of its tenders shows the cover-bid pattern.
COVER_BID_SHARE = 0.6


def _cobid_graph(tenders: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Count, for each vendor pair, how many tenders they BOTH bid on (the co-bidding relationship)."""
    counts: dict[tuple[str, str], int] = {}
    for t in tenders:
        vendors = sorted({b["vendor"] for b in t["bids"]})
        for a, b in combinations(vendors, 2):
            counts[(a, b)] = counts.get((a, b), 0) + 1
    return counts


def _ring_group(cobids: dict[tuple[str, str], int]) -> list[str]:
    """The connected set of vendors linked by frequent (>= MIN_COBIDS) co-bidding."""
    adj: dict[str, set[str]] = {}
    for (a, b), n in cobids.items():
        if n >= MIN_COBIDS:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    if not adj:
        return []
    # largest connected component (the candidate ring)
    seen: set[str] = set()
    best: list[str] = []
    for start in adj:
        if start in seen:
            continue
        stack, comp = [start], []
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            comp.append(v)
            stack.extend(adj[v] - seen)
        if len(comp) > len(best):
            best = comp
    return sorted(best)


def _ring_signals(tenders: list[dict[str, Any]], group: list[str]) -> dict[str, Any]:
    """Within the candidate group: do wins ROTATE, and how many tenders show the COVER-BID pattern?"""
    gset = set(group)
    group_tenders = [t for t in tenders if gset.issubset({b["vendor"] for b in t["bids"]})]
    winners = [t["winner"] for t in group_tenders if t.get("winner") in gset]
    rotates = len(set(winners)) >= 2  # the win moves around the group, not one persistent winner
    cover = 0
    for t in group_tenders:
        win_amt = min(b["amount"] for b in t["bids"] if b["vendor"] == t["winner"])
        losers = [b["amount"] for b in t["bids"] if b["vendor"] in gset and b["vendor"] != t["winner"]]
        if losers and all(win_amt < a <= win_amt * (1 + COVER_BID_BAND) for a in losers):
            cover += 1
    cover_share = cover / len(group_tenders) if group_tenders else 0.0
    return {"group_tenders": len(group_tenders), "wins_rotate": rotates,
            "cover_bid_tenders": cover, "cover_bid_share": round(cover_share, 3),
            "winners": sorted(set(winners))}


def run(*, tenders: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect a bid-rigging ring across ``tenders`` and flag it with rotation + cover-bid evidence."""
    trace: list[dict[str, Any]] = []

    # 1. co-bidding graph → candidate ring group.
    cobids = _cobid_graph(tenders)
    group = _ring_group(cobids)
    trace.append({"step": "cobid_graph", "frequent_pairs": sum(1 for n in cobids.values() if n >= MIN_COBIDS),
                  "candidate_group": group})

    # 2. ring signals (rotation + cover bids).
    signals = _ring_signals(tenders, group) if group else {"group_tenders": 0, "wins_rotate": False,
                                                            "cover_bid_share": 0.0, "winners": []}
    is_ring = bool(group) and signals["wins_rotate"] and signals["cover_bid_share"] >= COVER_BID_SHARE
    trace.append({"step": "ring_signals", **signals, "is_ring": is_ring})

    # 3. co-bidding subgraph.
    nodes = {v: {} for v in {b["vendor"] for t in tenders for b in t["bids"]}}
    edges = [{"source": a, "relation": "co_bids", "target": b} for (a, b), n in cobids.items() if n >= MIN_COBIDS]
    if group:
        sub = graph_run(query=f"who bids with {group[0]}", graph={"nodes": nodes, "edges": edges}, max_hops=3)["subgraph"]
        trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"])})

    # 4. which source governs.
    prec = precedence_run(candidates=sources)
    governing = prec["selected"][0]["id"] if prec["selected"] else None
    trace.append({"step": "source_precedence_select", "governing": governing})

    # 5. flag the ring.
    queue: list[dict] = []
    ticket = None
    if is_ring:
        ticket = escalate_run(result={"ring": group, "rotating_winners": signals["winners"],
                                      "cover_bid_share": signals["cover_bid_share"], "governing_source": governing},
                              reason="gate_fired",
                              enqueue=lambda t: (queue.append(t), {"ref": f"col-{len(queue):04d}"})[1])["ticket"]
    result = {"title": "Procurement collusion / bid-rigging review",
              "answer": (f"BID-RIGGING RING — {len(group)} vendors, rotating winners, "
                         f"{signals['cover_bid_share']:.0%} cover-bid tenders" if is_ring
                         else "no ring pattern detected (bids look competitive)"),
              "details": {"ring": group, "wins_rotate": signals["wins_rotate"],
                          "cover_bid_share": signals["cover_bid_share"], "rotating_winners": signals["winners"]},
              "citations": [governing] if governing else []}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"is_ring": is_ring, "ring": group, "signals": signals,
            "escalated": ticket is not None, "ticket": ticket["queue_ref"] if ticket else None,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC tender ledger (public-shape; proves the mechanism). RingCo/BidCo/CovCo rotate wins and
# submit cover bids 1–3% above the winner; FairVendor is an honest outsider who sometimes undercuts.
def _t(tid, winner, bids):
    return {"id": tid, "winner": winner, "bids": [{"vendor": v, "amount": a} for v, a in bids]}


_TENDERS = [
    _t("T1", "RingCo", [("RingCo", 100), ("BidCo", 102), ("CovCo", 103)]),
    _t("T2", "BidCo", [("RingCo", 121), ("BidCo", 120), ("CovCo", 122)]),
    _t("T3", "CovCo", [("RingCo", 152), ("BidCo", 151), ("CovCo", 150)]),
    _t("T4", "RingCo", [("RingCo", 130), ("BidCo", 133), ("CovCo", 132)]),
    _t("T5", "FairVendor", [("RingCo", 145), ("BidCo", 147), ("FairVendor", 119)]),  # honest outsider undercuts
]
_SOURCES = [
    {"id": "award-notice@2026-06-12", "text": "official contract award notices (signed, current)",
     "source_kind": "source_of_law", "signed": True, "valid_through": 2_000_000.0, "as_of": 1_000_000.0},
    {"id": "tender-aggregator@old", "text": "scraped tender-aggregator feed", "source_kind": "secondary_report",
     "signed": False, "valid_through": 500_000.0, "as_of": 1_000_000.0},
]


def _self_test() -> int:
    out = run(tenders=_TENDERS, sources=_SOURCES)
    # The three colluders are caught: they co-bid repeatedly, wins rotate among them, and their losing
    # bids are cover bids (just above the winner).
    assert out["is_ring"] is True, out
    assert out["ring"] == ["BidCo", "CovCo", "RingCo"], out["ring"]
    assert out["signals"]["wins_rotate"] is True
    assert set(out["signals"]["winners"]) == {"BidCo", "CovCo", "RingCo"}
    assert out["signals"]["cover_bid_share"] >= COVER_BID_SHARE, out["signals"]
    assert out["escalated"] is True and out["ticket"]
    assert "BID-RIGGING RING" in out["report_markdown"]
    # The honest outsider is NOT in the ring (it genuinely undercuts; it's not a rotating cover-bidder).
    assert "FairVendor" not in out["ring"]
    # Control: a fully competitive ledger (no rotation, real undercutting) is NOT flagged.
    competitive = [
        _t("C1", "A", [("A", 100), ("B", 130), ("C", 145)]),
        _t("C2", "A", [("A", 110), ("B", 140), ("C", 150)]),
        _t("C3", "A", [("A", 105), ("B", 135), ("C", 160)]),
    ]
    comp = run(tenders=competitive, sources=_SOURCES)
    assert comp["is_ring"] is False, comp  # one persistent winner, big gaps → no rotation, no cover bids
    # Signed award notice governs over the scraped feed.
    gov = next(t for t in out["trace"] if t["step"] == "source_precedence_select")["governing"]
    assert gov == "award-notice@2026-06-12"
    # Derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(tenders=_TENDERS, sources=_SOURCES), sort_keys=True) == \
           json.dumps(run(tenders=_TENDERS, sources=_SOURCES), sort_keys=True)
    print("PASS — procurement_collusion_ring: aggregate bids across tenders → co-bidding group whose "
          "wins ROTATE and whose losing bids are COVER BIDS (just above the winner) → flagged "
          "bid-rigging ring (RingCo/BidCo/CovCo), the honest undercutter excluded, a competitive "
          "ledger not flagged; signed award notice governs; the ring a per-tender model can't see")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Procurement collusion / bid-rigging showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(tenders=_TENDERS, sources=_SOURCES)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
