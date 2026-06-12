#!/usr/bin/env python3
"""Showcase: COMMON-CONTROL resolution from M&A news — related-party transactions across deal chains.

The other half of the owner's relationship-network ask, focused on MERGERS & ACQUISITIONS NEWS over
time: resolve every company to its CURRENT ultimate parent by chaining acquisitions in date order,
then detect when the two counterparties to a transaction are actually under COMMON CONTROL — a
related-party transaction that must be disclosed (and a classic transfer-pricing / round-tripping /
self-dealing risk).

Structural gap (durability: aggregation + freshness/temporal): a frontier model (a) doesn't know
post-cutoff deals, (b) can't transitively chain acquirer-of-acquirer ownership, and (c) misses that
today's "arm's-length" vendor was acquired by the customer's parent last quarter. Ultimate-parent
resolution is a temporal graph walk over a governed deal ledger, not recall — and the answer CHANGES
with the as-of date, which a static model can't track.

Composition (real `scripts/processors` callables + deterministic temporal ownership resolution):
  1. _apply_deals_asof       — order M&A events by date, apply ≤ as-of, build the ownership map
  2. _ultimate_parent        — chain each entity to its root parent (cycle-guarded) — the domain step
  3. graphrag_retrieve       — present the control subgraph around the transaction
  4. _common_control         — same ultimate parent on both sides → related-party transaction
  5. source_precedence_select— a signed registry filing governs over a scraped M&A news article
  6. escalate_human + deliver_report — flag the related-party transaction with the control chain

Run:  python3 scripts/showcase_pipelines/common_control_resolver.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.graphrag_retrieve import run as graph_run
from scripts.processors.retrieval.source_precedence_select import run as precedence_run
from scripts.processors.deliver.escalate_human import run as escalate_run
from scripts.processors.deliver.deliver_report import run as report_run


def _apply_deals_asof(deals: list[dict[str, Any]], as_of: str) -> dict[str, str]:
    """Ownership map (child → immediate parent) from every acquisition closed on/before ``as_of``.
    Date-ordered so a later deal supersedes an earlier one (deterministic; dates are ISO strings)."""
    owner: dict[str, str] = {}
    for d in sorted(deals, key=lambda x: x["date"]):
        if d["date"] <= as_of:
            owner[d["target"]] = d["acquirer"]              # latest acquirer wins
    return owner


def _ultimate_parent(entity: str, owner: dict[str, str]) -> tuple[str, list[str]]:
    """Walk child→parent to the root (the ultimate controller), returning the chain. Cycle-guarded."""
    chain = [entity]
    seen = {entity}
    cur = entity
    while cur in owner and owner[cur] not in seen:
        cur = owner[cur]
        chain.append(cur)
        seen.add(cur)
    return cur, chain


def _common_control(a: str, b: str, owner: dict[str, str]) -> dict[str, Any]:
    """Two DISTINCT parties are under common control iff they resolve to the same ultimate root
    (whether that root is a third-party parent or one party owning the other)."""
    pa, ca = _ultimate_parent(a, owner)
    pb, cb = _ultimate_parent(b, owner)
    under = a != b and pa == pb
    return {"under_common_control": under, "ultimate_parent": pa if under else None,
            "chain_a": ca, "chain_b": cb, "root_a": pa, "root_b": pb}


def run(*, transaction: dict[str, Any], ma_events: list[dict[str, Any]],
        sources: list[dict[str, Any]], as_of: str | None = None) -> dict[str, Any]:
    """Resolve ultimate control of both sides of ``transaction`` as of ``as_of`` and flag self-dealing."""
    trace: list[dict[str, Any]] = []
    buyer, seller = transaction["buyer"], transaction["seller"]
    as_of = as_of or transaction.get("date") or max((d["date"] for d in ma_events), default="9999-12-31")

    # 1+2. ownership as-of → ultimate parents.
    owner = _apply_deals_asof(ma_events, as_of)
    cc = _common_control(buyer, seller, owner)
    related = cc["under_common_control"]
    trace.append({"step": "ultimate_parent_asof", "as_of": as_of, "buyer_root": cc["root_a"],
                  "seller_root": cc["root_b"], "buyer_chain": cc["chain_a"], "seller_chain": cc["chain_b"]})

    # 3. control subgraph around the two parties.
    nodes = {n: {} for n in set(owner) | set(owner.values()) | {buyer, seller}}
    edges = [{"source": child, "relation": "acquired_by", "target": par} for child, par in owner.items()]
    sub = graph_run(query=f"who controls {buyer} and {seller}",
                    graph={"nodes": nodes, "edges": edges}, max_hops=4)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"])})

    # 4. which source governs.
    prec = precedence_run(candidates=sources)
    governing = prec["selected"][0]["id"] if prec["selected"] else None
    trace.append({"step": "source_precedence_select", "governing": governing})

    # 5. flag the related-party transaction.
    queue: list[dict] = []
    ticket = None
    if related:
        ticket = escalate_run(result={"transaction": f"{buyer} ⇄ {seller}", "ultimate_parent": cc["ultimate_parent"],
                                      "buyer_chain": cc["chain_a"], "seller_chain": cc["chain_b"],
                                      "governing_source": governing},
                              reason="gate_fired",
                              enqueue=lambda t: (queue.append(t), {"ref": f"rpt-{len(queue):04d}"})[1])["ticket"]
    result = {"title": "Common-control / related-party transaction review",
              "answer": (f"RELATED-PARTY TRANSACTION — both sides controlled by {cc['ultimate_parent']}"
                         if related else "arm’s-length — no common control as of " + as_of),
              "details": {"buyer": buyer, "seller": seller, "as_of": as_of,
                          "buyer_chain": " → ".join(cc["chain_a"]), "seller_chain": " → ".join(cc["chain_b"])},
              "citations": [governing] if governing else []}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"under_common_control": related, "ultimate_parent": cc["ultimate_parent"], "as_of": as_of,
            "buyer_chain": cc["chain_a"], "seller_chain": cc["chain_b"],
            "escalated": ticket is not None, "ticket": ticket["queue_ref"] if ticket else None,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC M&A news ledger (public-shape; proves the mechanism). ParentCo rolls up both an arm's-length
# "vendor" and its "customer" over two deals — so a 2025-09 transaction between them is self-dealing.
_MA_EVENTS = [
    {"acquirer": "ParentCo", "target": "AlphaVendor", "date": "2025-01-15", "source": "registry-filing@2025"},
    {"acquirer": "ParentCo", "target": "BetaCustomer", "date": "2025-06-20", "source": "ma-news@2025"},
    {"acquirer": "OtherGroup", "target": "GammaCo", "date": "2024-11-01", "source": "registry-filing@2024"},
]
_TRANSACTION = {"buyer": "BetaCustomer", "seller": "AlphaVendor", "date": "2025-09-01",
                "description": "BetaCustomer purchases services from AlphaVendor"}
_SOURCES = [
    {"id": "corp-registry@2026-06-12", "text": "state corporate registry filings (signed, current)",
     "source_kind": "source_of_law", "signed": True, "valid_through": 2_000_000.0, "as_of": 1_000_000.0},
    {"id": "ma-news-scrape@old", "text": "scraped M&A news articles", "source_kind": "secondary_report",
     "signed": False, "valid_through": 500_000.0, "as_of": 1_000_000.0},
]


def _self_test() -> int:
    # As of the transaction date, both sides roll up to ParentCo → RELATED-PARTY (self-dealing).
    out = run(transaction=_TRANSACTION, ma_events=_MA_EVENTS, sources=_SOURCES)
    assert out["under_common_control"] is True, out
    assert out["ultimate_parent"] == "ParentCo", out
    assert out["buyer_chain"] == ["BetaCustomer", "ParentCo"] and out["seller_chain"] == ["AlphaVendor", "ParentCo"]
    assert out["escalated"] is True and out["ticket"]
    assert "RELATED-PARTY" in out["report_markdown"]
    # TEMPORAL: as of 2025-03 (BEFORE ParentCo acquired BetaCustomer) they are NOT under common control.
    early = run(transaction=_TRANSACTION, ma_events=_MA_EVENTS, sources=_SOURCES, as_of="2025-03-01")
    assert early["under_common_control"] is False and early["escalated"] is False, early
    assert "arm’s-length" in early["report_markdown"]
    # A transaction between genuinely independent entities is NOT flagged.
    indep = run(transaction={"buyer": "GammaCo", "seller": "AlphaVendor", "date": "2025-12-01"},
                ma_events=_MA_EVENTS, sources=_SOURCES)
    assert indep["under_common_control"] is False, indep  # OtherGroup vs ParentCo
    # Signed registry governs over scraped news.
    gov = next(t for t in out["trace"] if t["step"] == "source_precedence_select")["governing"]
    assert gov == "corp-registry@2026-06-12"
    # Derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(transaction=_TRANSACTION, ma_events=_MA_EVENTS, sources=_SOURCES), sort_keys=True) == \
           json.dumps(run(transaction=_TRANSACTION, ma_events=_MA_EVENTS, sources=_SOURCES), sort_keys=True)
    print("PASS — common_control_resolver: chain M&A deals by date → ultimate parent; a 'vendor' and a "
          "'customer' both rolled up to ParentCo over two deals are flagged as a RELATED-PARTY "
          "transaction (escalated) — but NOT before the second deal closed (temporal/as-of), and not "
          "for truly independent parties; signed registry governs; the self-dealing a bare model misses")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Common-control / related-party transaction showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(transaction=_TRANSACTION, ma_events=_MA_EVENTS, sources=_SOURCES)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
