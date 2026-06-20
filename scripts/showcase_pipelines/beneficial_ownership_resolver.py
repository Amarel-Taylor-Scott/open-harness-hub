#!/usr/bin/env python3
"""Showcase: AUTHORITATIVE beneficial-ownership resolution + the OFAC 50% rule (merger-heavy industries).

The owner's M&A / evolving-ownership-hierarchy ask, taken to the regulated edge. In industries that
consolidate constantly — staffing/employment agencies, real-estate brokerages — "who controls whom"
changes every quarter, the claims come from sources of WILDLY different authority (an SEC 8-K vs a press
rumor vs a vendor DB), and the answer has to be CURRENT and PROVABLE. Then the kicker: OFAC's **50% rule**
— an entity ≥50%-owned (directly or through a chain of ≥50% links) by a blocked person is ITSELF blocked,
even if it never appears on the SDN list. Get the control graph wrong and you either trade with a
sanctioned entity or wrongly freeze a clean one.

Structural gap (durability: aggregation + freshness/temporal + source-authority): a frontier model (a)
doesn't know post-cutoff deals, (b) can't transitively propagate sanctions down a ≥50% ownership chain,
and (c) has no notion of which CONFLICTING ownership claim is authoritative — it can't tell an SEC filing
from a blog. Resolving the authoritative current owner is a governed, source-ranked, temporal graph walk,
not recall.

Composition (the REAL source-authority classifier + real `scripts/processors` callables + deterministic
ownership/50%-rule logic; the ONE simulated seam would be a model call — there is none here):
  1. source_authority.classify  — EARN each ownership claim's authority from its publisher/domain (SEC
                                   filing governs over a press rumor); flip the publisher → the owner flips
  2. _resolve_owners            — per subject, the highest-authority claim ≤ as-of governs; rest held out
  3. _ultimate_parent           — chain child→parent to the controlling root (cycle-guarded)
  4. _ofac_50_percent_rule      — propagate SDN-blocked status DOWN every ≥50% ownership edge (inherited)
  5. graphrag_retrieve          — present the control subgraph
  6. escalate_human + deliver_report — flag every blocked-by-inheritance entity with its proof chain

Run:  python3 scripts/showcase_pipelines/beneficial_ownership_resolver.py [--self-test]
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

from scripts.artifact_graph.source_authority import classify
from scripts.processors.retrieval.graphrag_retrieve import run as graph_run
from scripts.processors.deliver.escalate_human import run as escalate_run
from scripts.processors.deliver.deliver_report import run as report_run

_CONTROL_THRESHOLD = 50.0  # OFAC 50% rule: ownership ≥ this (per ≥50% control link) propagates blocked status


def _resolve_owners(signals: list[dict[str, Any]], as_of: str) -> tuple[dict[str, dict], list[dict]]:
    """Per subject, the GOVERNING ownership claim is the one whose source has the highest EARNED authority
    (ties → most recent effective date). Returns (resolved {subject: {...}}, held_out_claims). Authority is
    classified from each claim's publisher/domain via source_authority — never assumed."""
    by_subject: dict[str, list[dict]] = {}
    for s in signals:
        if s["date"] <= as_of:
            auth = classify(publisher=s.get("publisher", ""), source_uri=s.get("source_uri", ""), signed=s.get("signed"))
            by_subject.setdefault(s["subject"], []).append({**s, "_rank": auth["rank"], "_basis": auth["basis"], "_tier": auth["tier"]})
    resolved: dict[str, dict] = {}
    held_out: list[dict] = []
    for subject, claims in by_subject.items():
        # highest authority wins; tie → latest effective date; stable by (parent) for determinism
        claims.sort(key=lambda c: (c["_rank"], c["date"], c["parent"]), reverse=True)
        winner = claims[0]
        resolved[subject] = {"parent": winner["parent"], "pct": float(winner["pct"]), "date": winner["date"],
                             "authority_basis": winner["_basis"], "authority_tier": winner["_tier"]}
        for c in claims[1:]:
            held_out.append({"subject": subject, "claimed_parent": c["parent"], "date": c["date"],
                             "reason_held_out": f"lower authority — {c['_basis']}"})
    return resolved, held_out


def _ultimate_parent(entity: str, owner: dict[str, dict]) -> tuple[str, list[str]]:
    """Walk child→parent to the controlling root, returning the chain. Cycle-guarded."""
    chain, seen, cur = [entity], {entity}, entity
    while cur in owner and owner[cur]["parent"] not in seen:
        cur = owner[cur]["parent"]
        chain.append(cur)
        seen.add(cur)
    return cur, chain


def _ofac_50_percent_rule(owner: dict[str, dict], blocked: set[str]) -> dict[str, dict]:
    """Propagate SDN-blocked status DOWN every ownership edge whose stake ≥ 50% (OFAC 50% rule): an entity
    a blocked person controls through a chain of ≥50% links is ITSELF blocked, even if unlisted. Returns
    {entity: {blocked_via, chain, pct_path}} for every entity blocked by inheritance (not directly listed)."""
    # children-of map for ≥50% control edges
    controls: dict[str, list[tuple[str, float]]] = {}
    for child, info in owner.items():
        if info["pct"] >= _CONTROL_THRESHOLD:
            controls.setdefault(info["parent"], []).append((child, info["pct"]))
    inherited: dict[str, dict] = {}
    for root in blocked:
        stack = [(root, [root], [])]
        seen = {root}
        while stack:
            node, chain, pcts = stack.pop()
            for child, pct in sorted(controls.get(node, [])):
                if child in seen:
                    continue
                seen.add(child)
                new_chain, new_pcts = chain + [child], pcts + [pct]
                if child not in blocked:  # inherited (not itself listed)
                    inherited[child] = {"blocked_via": root, "chain": new_chain, "pct_path": new_pcts}
                stack.append((child, new_chain, new_pcts))
    return inherited


def run(*, ownership_signals: list[dict[str, Any]], blocked_entities: list[str],
        as_of: str | None = None) -> dict[str, Any]:
    """Resolve the authoritative current ownership graph as of ``as_of`` and apply the OFAC 50% rule."""
    trace: list[dict[str, Any]] = []
    as_of = as_of or max((s["date"] for s in ownership_signals), default="9999-12-31")
    blocked = set(blocked_entities)

    # 1+2. EARN the governing ownership claim per subject from its source authority.
    owner, held_out = _resolve_owners(ownership_signals, as_of)
    trace.append({"step": "source_authority.classify + resolve_owners", "as_of": as_of,
                  "resolved": {k: {"parent": v["parent"], "pct": v["pct"], "tier": v["authority_tier"]} for k, v in owner.items()},
                  "held_out": held_out})

    # 3. ultimate controllers.
    roots = {e: _ultimate_parent(e, owner) for e in owner}
    trace.append({"step": "ultimate_parent", "chains": {e: " → ".join(c) for e, (_, c) in roots.items()}})

    # 4. OFAC 50% rule — propagate blocked status down ≥50% chains.
    inherited = _ofac_50_percent_rule(owner, blocked)
    trace.append({"step": "ofac_50_percent_rule", "directly_blocked": sorted(blocked),
                  "blocked_by_inheritance": {k: {"via": v["blocked_via"], "chain": " → ".join(v["chain"]),
                                                 "pct_path": v["pct_path"]} for k, v in inherited.items()}})

    # 5. control subgraph.
    nodes = {n: {} for n in set(owner) | {v["parent"] for v in owner.values()} | blocked}
    edges = [{"source": child, "relation": f"owned_{int(info['pct'])}pct_by", "target": info["parent"]}
             for child, info in owner.items()]
    sub = graph_run(query="resolve ultimate control + sanctions inheritance",
                    graph={"nodes": nodes, "edges": edges}, max_hops=5)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"])})

    # 6. flag every blocked-by-inheritance entity with its proof chain.
    queue: list[dict] = []
    tickets = []
    for entity, info in sorted(inherited.items()):
        t = escalate_run(result={"entity": entity, "blocked_via_SDN": info["blocked_via"],
                                 "ownership_chain": " → ".join(info["chain"]), "pct_path": info["pct_path"],
                                 "rule": "OFAC 50% rule (≥50% chain → blocked by inheritance)"},
                         reason="gate_fired",
                         enqueue=lambda x: (queue.append(x), {"ref": f"sanctions-{len(queue):04d}"})[1])["ticket"]
        tickets.append(t["queue_ref"])

    n_blocked = len(inherited)
    result = {"title": "Beneficial-ownership resolution + OFAC 50% rule",
              "answer": (f"{n_blocked} entity(ies) BLOCKED BY INHERITANCE (≥50% owned by an SDN-listed person): "
                         + ", ".join(sorted(inherited)) if inherited
                         else "no entity blocked by the 50% rule as of " + as_of),
              "details": {"as_of": as_of,
                          "resolved_owners": {k: f"{v['parent']} ({int(v['pct'])}%, {v['authority_tier']})" for k, v in owner.items()},
                          "blocked_by_inheritance": {k: " → ".join(v["chain"]) for k, v in inherited.items()},
                          "held_out_claims": [f"{h['subject']} ⟵ {h['claimed_parent']} ({h['reason_held_out']})" for h in held_out]},
              "citations": sorted({owner[e]["authority_basis"] for e in owner})}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"as_of": as_of, "resolved_owners": owner, "held_out_claims": held_out,
            "blocked_by_inheritance": inherited, "directly_blocked": sorted(blocked),
            "escalated": bool(tickets), "tickets": tickets,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC ownership ledger (public-shape; proves the mechanism). A staffing roll-up: Meridian Staffing
# Holdings consolidates independent agencies; its ultimate owner "Volkov Holdings" is on the (synthetic)
# SDN list — so the agencies Meridian ≥50%-controls are blocked by inheritance, even though unlisted.
_SIGNALS = [
    # an SEC 8-K (sec.gov, signed) — AUTHORITATIVE — vs an earlier press rumor (unlisted blog) — HELD OUT.
    {"subject": "Apex Staffing", "parent": "Meridian Staffing Holdings", "pct": 60, "date": "2025-06-01",
     "publisher": "U.S. SEC (8-K)", "source_uri": "https://www.sec.gov/Archives/edgar/data/meridian/8k.htm", "signed": True},
    {"subject": "Apex Staffing", "parent": "RivalGroup", "pct": 55, "date": "2025-05-01",
     "publisher": "StaffingDealRumors", "source_uri": "https://staffingdealrumors.example.com/apex", "signed": False},
    # Volkov Holdings (SDN) owns 70% of Meridian → ≥50% → control flows down.
    {"subject": "Meridian Staffing Holdings", "parent": "Volkov Holdings", "pct": 70, "date": "2024-01-10",
     "publisher": "U.S. SEC (SC 13D)", "source_uri": "https://www.sec.gov/Archives/edgar/data/meridian/sc13d.htm", "signed": True},
    # Beacon Staffing is only 40%-owned by Meridian → < 50% → NOT blocked by inheritance.
    {"subject": "Beacon Staffing", "parent": "Meridian Staffing Holdings", "pct": 40, "date": "2025-03-15",
     "publisher": "U.S. SEC (8-K)", "source_uri": "https://www.sec.gov/Archives/edgar/data/beacon/8k.htm", "signed": True},
]
_BLOCKED = ["Volkov Holdings"]   # synthetic OFAC SDN entry (clearly synthetic; real SDN fetch is a seam)


def _self_test() -> int:
    out = run(ownership_signals=_SIGNALS, blocked_entities=_BLOCKED)

    # 1. SOURCE AUTHORITY EARNED: the SEC 8-K governs Apex's parent, the blog rumor is HELD OUT.
    assert out["resolved_owners"]["Apex Staffing"]["parent"] == "Meridian Staffing Holdings", out["resolved_owners"]
    assert "official_agency" in out["resolved_owners"]["Apex Staffing"]["authority_tier"]
    assert any(h["claimed_parent"] == "RivalGroup" for h in out["held_out_claims"]), out["held_out_claims"]

    # 2. OFAC 50% RULE: Apex is blocked BY INHERITANCE (Volkov 70% → Meridian 60% → Apex, both ≥50%).
    assert "Apex Staffing" in out["blocked_by_inheritance"], out["blocked_by_inheritance"]
    assert out["blocked_by_inheritance"]["Apex Staffing"]["blocked_via"] == "Volkov Holdings"
    assert out["blocked_by_inheritance"]["Apex Staffing"]["chain"] == ["Volkov Holdings", "Meridian Staffing Holdings", "Apex Staffing"]
    # 3. the 40%-owned Beacon is NOT blocked (link below the 50% control threshold).
    assert "Beacon Staffing" not in out["blocked_by_inheritance"], out["blocked_by_inheritance"]
    assert out["escalated"] is True and out["tickets"]
    assert "BLOCKED BY INHERITANCE" in out["report_markdown"]

    # 4. FLIP THE SOURCE: if the rumor had been the SEC filing and vice versa, the owner FLIPS — proving the
    #    decision is EARNED from provenance, not the deal itself.
    flipped = [dict(s) for s in _SIGNALS]
    for s in flipped:
        if s["subject"] == "Apex Staffing" and s["parent"] == "RivalGroup":
            s["publisher"], s["source_uri"], s["signed"] = "U.S. SEC (8-K)", "https://www.sec.gov/x.htm", True
        elif s["subject"] == "Apex Staffing" and s["parent"] == "Meridian Staffing Holdings":
            s["publisher"], s["source_uri"], s["signed"] = "StaffingDealRumors", "https://staffingdealrumors.example.com/x", False
    out_f = run(ownership_signals=flipped, blocked_entities=_BLOCKED)
    assert out_f["resolved_owners"]["Apex Staffing"]["parent"] == "RivalGroup", out_f["resolved_owners"]
    # with RivalGroup (not under Volkov) as Apex's parent, Apex is NO LONGER blocked by inheritance.
    assert "Apex Staffing" not in out_f["blocked_by_inheritance"]

    # 5. TEMPORAL: as of 2025-05-15 (before the 2025-06-01 SEC acquisition) Apex is not yet under Meridian.
    early = run(ownership_signals=_SIGNALS, blocked_entities=_BLOCKED, as_of="2025-05-15")
    assert early["resolved_owners"].get("Apex Staffing", {}).get("parent") in (None, "RivalGroup"), early["resolved_owners"]

    # 6. derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(ownership_signals=_SIGNALS, blocked_entities=_BLOCKED), sort_keys=True) == \
           json.dumps(run(ownership_signals=_SIGNALS, blocked_entities=_BLOCKED), sort_keys=True)

    print("PASS — beneficial_ownership_resolver: the SEC 8-K (earned authority) governs Apex's parent over a "
          "press rumor (held out); the OFAC 50% rule propagates Volkov's SDN block down the ≥50% chain so Apex "
          "is BLOCKED BY INHERITANCE while the 40%-owned Beacon is not; flip the publisher and the owner (and the "
          "block) flips — authority is EARNED, not assumed; temporal as-of resolution; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Beneficial-ownership resolution + OFAC 50% rule showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(ownership_signals=_SIGNALS, blocked_entities=_BLOCKED)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
