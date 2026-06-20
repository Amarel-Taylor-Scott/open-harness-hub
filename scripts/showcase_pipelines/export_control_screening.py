#!/usr/bin/env python3
"""Showcase: BIS export-control screening — the authoritative Entity List vs a stale vendor screening DB.

Before an export ships, the end-user must be screened against the BIS Entity List (and friends). The trap:
a third-party screening database returns "no adverse match" while the authoritative BIS Entity List (just
updated) shows the end-user is LISTED → a license is required, and shipping without one is a criminal EAR
violation. Which source governs is decisive, and it is EARNED: the BIS Entity List (bis.doc.gov, official
agency) outranks a vendor screening DB (an unlisted commercial domain).

Structural gap (durability: source-authority + freshness): a frontier model doesn't know post-cutoff Entity
List additions and can't tell the authoritative list from a vendor's cached copy — it will clear an export
it shouldn't. The screen is a governed comparison against the authoritative list, not recall.

Composition (the REAL source-authority classifier + real processors + deterministic determination logic;
the ONE simulated seam would be a model call — there is none):
  1. source_authority.classify  — EARN each screening source's authority (BIS Entity List governs)
  2. _screen                     — per end-user, the highest-authority determination governs; stale "clear"s held out
  3. graphrag_retrieve          — present the export → end-user → screening graph
  4. escalate_human + deliver_report — flag every license-required export with its proof

Run:  python3 scripts/showcase_pipelines/export_control_screening.py [--self-test]
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


def _screen(signals: list[dict[str, Any]]) -> tuple[dict[str, dict], list[dict]]:
    """Per end-user, the GOVERNING screening determination is the one whose source has the highest EARNED
    authority (ties → most recent). A lower-authority determination that CONTRADICTS the governing one
    (e.g. a vendor DB 'clear' against an Entity-List 'listed') is HELD OUT — never relied on to clear an export."""
    by_eu: dict[str, list[dict]] = {}
    for s in signals:
        a = classify(publisher=s.get("publisher", ""), source_uri=s.get("source_uri", ""), signed=s.get("signed"))
        by_eu.setdefault(s["end_user"], []).append({**s, "_rank": a["rank"], "_basis": a["basis"], "_tier": a["tier"]})
    governing: dict[str, dict] = {}
    held_out: list[dict] = []
    for eu, ss in by_eu.items():
        ss.sort(key=lambda s: (s["_rank"], s.get("date", ""), s["determination"]), reverse=True)
        win = ss[0]
        governing[eu] = {"determination": win["determination"], "list_name": win.get("list_name", ""),
                         "authority_basis": win["_basis"], "tier": win["_tier"]}
        for s in ss[1:]:
            if s["determination"] != win["determination"]:
                held_out.append({"end_user": eu, "determination": s["determination"],
                                 "reason_held_out": f"contradicts the higher-authority screen — {s['_basis']}"})
    return governing, held_out


def run(*, exports: list[dict[str, Any]], screening_signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Screen each export's end-user; a governing 'listed' determination → license required (blocked)."""
    trace: list[dict[str, Any]] = []
    governing, held_out = _screen(screening_signals)
    trace.append({"step": "source_authority.classify + screen",
                  "governing": {eu: {"determination": g["determination"], "tier": g["tier"]} for eu, g in governing.items()},
                  "held_out": held_out})

    decisions = []
    for e in exports:
        g = governing.get(e["end_user"], {"determination": "unscreened", "authority_basis": "no screening source", "list_name": ""})
        required = g["determination"] == "listed"
        decisions.append({"export_id": e["export_id"], "item": e.get("item", ""), "eccn": e.get("eccn", ""),
                          "destination": e.get("destination", ""), "end_user": e["end_user"],
                          "license_required": required, "list_name": g["list_name"], "basis": g["authority_basis"]})

    nodes = {n: {} for e in exports for n in (e["export_id"], e["end_user"])}
    edges = [{"source": e["export_id"], "relation": "ships_to", "target": e["end_user"]} for e in exports]
    sub = graph_run(query="screen exports against the authoritative Entity List",
                    graph={"nodes": nodes, "edges": edges}, max_hops=3)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"])})

    queue: list[dict] = []
    tickets = []
    blocked = [d for d in decisions if d["license_required"]]
    for d in sorted(blocked, key=lambda x: x["export_id"]):
        t = escalate_run(result={"export_id": d["export_id"], "end_user": d["end_user"], "eccn": d["eccn"],
                                 "destination": d["destination"], "on_list": d["list_name"],
                                 "rule": "EAR — license required for a listed end-user", "authority": d["basis"]},
                         reason="gate_fired",
                         enqueue=lambda x: (queue.append(x), {"ref": f"bis-{len(queue):04d}"})[1])["ticket"]
        tickets.append(t["queue_ref"])

    result = {"title": "BIS export-control screening",
              "answer": (f"{len(blocked)} export(s) require a LICENSE (end-user on the authoritative Entity List): "
                         + ", ".join(sorted(d["export_id"] for d in blocked)) if blocked
                         else "no license required — all end-users clear on the authoritative screen"),
              "details": {"decisions": {d["export_id"]: ("LICENSE REQUIRED" if d["license_required"] else "ok")
                                        + f" — {d['end_user']}" for d in decisions},
                          "held_out_stale_clears": [f"{h['end_user']}: {h['determination']} ({h['reason_held_out']})" for h in held_out]},
              "citations": sorted({g["authority_basis"] for g in governing.values()})}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"decisions": decisions, "governing": governing, "held_out": held_out,
            "escalated": bool(tickets), "tickets": tickets, "blocked_export_ids": sorted(d["export_id"] for d in blocked),
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC screening set (public-shape). The BIS Entity List (bis.doc.gov) shows Sinotech LISTED; a stale
# vendor screening DB says it's clear → BIS governs → license required. A genuinely clean end-user clears.
_EXPORTS = [
    {"export_id": "EXP-001", "item": "RF signal generator", "eccn": "3A001", "destination": "CN", "end_user": "Sinotech Microelectronics"},
    {"export_id": "EXP-002", "item": "oscilloscope", "eccn": "EAR99", "destination": "CH", "end_user": "Helvetia Instruments AG"},
]
_SIGNALS = [
    {"end_user": "Sinotech Microelectronics", "determination": "listed", "list_name": "BIS Entity List", "date": "2025-06",
     "publisher": "Bureau of Industry and Security", "source_uri": "https://www.bis.doc.gov/entity-list", "signed": True},
    {"end_user": "Sinotech Microelectronics", "determination": "clear", "list_name": "vendor cache", "date": "2025-01",
     "publisher": "ScreenFast DB", "source_uri": "https://screenfast-db.example.com/lookup", "signed": False},
    {"end_user": "Helvetia Instruments AG", "determination": "clear", "list_name": "BIS Entity List", "date": "2025-06",
     "publisher": "Bureau of Industry and Security", "source_uri": "https://www.bis.doc.gov/entity-list", "signed": True},
]


def _self_test() -> int:
    out = run(exports=_EXPORTS, screening_signals=_SIGNALS)

    # 1. EARNED authority: the BIS Entity List governs; the stale vendor "clear" is HELD OUT.
    assert out["governing"]["Sinotech Microelectronics"]["determination"] == "listed", out["governing"]
    assert "official_agency" in out["governing"]["Sinotech Microelectronics"]["tier"]
    assert any(h["end_user"] == "Sinotech Microelectronics" and h["determination"] == "clear" for h in out["held_out"]), out["held_out"]

    # 2. the listed end-user's export REQUIRES A LICENSE (blocked + escalated); the clean one is ok.
    assert "EXP-001" in out["blocked_export_ids"] and "EXP-002" not in out["blocked_export_ids"], out["blocked_export_ids"]
    assert out["escalated"] is True and out["tickets"]
    assert "LICENSE" in out["report_markdown"]

    # 3. FLIP THE SOURCE: if the vendor DB had been the BIS list and vice versa, the stale "clear" would govern
    #    and EXP-001 would (wrongly) clear — proving the screen is EARNED from provenance, not the determination text.
    flipped = [dict(s) for s in _SIGNALS]
    for s in flipped:
        if s["end_user"] == "Sinotech Microelectronics" and s["determination"] == "listed":
            s["publisher"], s["source_uri"], s["signed"] = "ScreenFast DB", "https://screenfast-db.example.com/x", False
        elif s["end_user"] == "Sinotech Microelectronics" and s["determination"] == "clear":
            s["publisher"], s["source_uri"], s["signed"] = "Bureau of Industry and Security", "https://www.bis.doc.gov/x", True
    out_f = run(exports=_EXPORTS, screening_signals=flipped)
    assert out_f["governing"]["Sinotech Microelectronics"]["determination"] == "clear", out_f["governing"]
    assert "EXP-001" not in out_f["blocked_export_ids"]

    # 4. derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(exports=_EXPORTS, screening_signals=_SIGNALS), sort_keys=True) == \
           json.dumps(run(exports=_EXPORTS, screening_signals=_SIGNALS), sort_keys=True)

    print("PASS — export_control_screening: the BIS Entity List (earned authority) governs over a stale vendor "
          "screening DB, so a 'clear' cache result is HELD OUT and the export to the LISTED end-user REQUIRES A "
          "LICENSE (escalated) while a genuinely clean end-user clears; flip the source and the screen flips — "
          "authority is EARNED; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="BIS export-control screening showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(exports=_EXPORTS, screening_signals=_SIGNALS)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
