#!/usr/bin/env python3
"""Showcase: FDA drug-labeling claim review — promotional overclaims vs the approved label (off-label risk).

A pharma promotional piece makes efficacy/safety/indication claims. Each claim is only substantiable if it
matches the FDA-APPROVED label (the authoritative source); a claim that contradicts the label, or asserts an
indication the label does not carry, is a potential off-label / misbranding violation (FDCA 502) and must be
HELD OUT of anything an agent serves. Which source governs is the whole game — and it is EARNED: the FDA
label (fda.gov, official agency) outranks a marketing brochure (an unlisted vendor domain).

Structural gap (durability: source-authority + freshness): a frontier model can't tell an FDA-approved label
from a glossy brochure, doesn't know post-cutoff label revisions, and will happily repeat a promotional
overclaim as fact. Substantiation is a governed comparison against the authoritative label, not recall.

Composition (the REAL source-authority classifier + real processors + deterministic claim matching; the ONE
simulated seam would be a model call — there is none):
  1. source_authority.classify  — EARN each claim-source's authority (FDA label governs over a brochure)
  2. _review_claims             — per topic, the highest-authority claim substantiates; promo conflicts/extras held out
  3. graphrag_retrieve          — present the label-vs-promotion claim graph
  4. escalate_human + deliver_report — flag every off-label / contradicted promotional claim with its proof

Run:  python3 _repos/shared-backend-components/scripts/showcase_pipelines/fda_labeling_claim_review.py [--self-test]
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


def _review_claims(claims: list[dict[str, Any]]) -> tuple[dict[str, dict], list[dict]]:
    """Group claims by topic; the GOVERNING (substantiating) claim is the one whose source has the highest
    EARNED authority (ties → most recent). A promotional claim that conflicts with the governing FDA-label
    claim, OR asserts a topic the label does not cover, is HELD OUT as a potential off-label overclaim."""
    by_topic: dict[str, list[dict]] = {}
    for c in claims:
        a = classify(publisher=c.get("publisher", ""), source_uri=c.get("source_uri", ""), signed=c.get("signed"))
        by_topic.setdefault(c["topic"], []).append({**c, "_rank": a["rank"], "_basis": a["basis"], "_tier": a["tier"]})
    governing: dict[str, dict] = {}
    held_out: list[dict] = []
    label_topics = {c["topic"] for cl in by_topic.values() for c in cl if c["_tier"] in ("source_of_law", "official_agency")}
    for topic, cs in by_topic.items():
        cs.sort(key=lambda c: (c["_rank"], c.get("date", ""), c["claim"]), reverse=True)
        win = cs[0]
        governing[topic] = {"claim": win["claim"], "authority_basis": win["_basis"], "tier": win["_tier"]}
        for c in cs[1:]:
            if c["claim"] != win["claim"]:
                held_out.append({"topic": topic, "claim": c["claim"], "kind": "contradicts_approved_label",
                                 "reason_held_out": f"lower authority — {c['_basis']}"})
    # a claim on a topic the AUTHORITATIVE label never covers = an off-label indication overclaim
    for topic, cs in by_topic.items():
        if topic not in label_topics:
            for c in cs:
                held_out.append({"topic": topic, "claim": c["claim"], "kind": "off_label_unsupported_topic",
                                 "reason_held_out": f"no FDA-approved label claim for this topic — {c['_basis']}"})
    return governing, held_out


def run(*, label_claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Review a drug's claim set: substantiate against the FDA-approved label, hold out promotional overclaims."""
    trace: list[dict[str, Any]] = []
    governing, held_out = _review_claims(label_claims)
    trace.append({"step": "source_authority.classify + review_claims",
                  "governing": {t: {"tier": g["tier"]} for t, g in governing.items()}, "held_out": held_out})

    nodes = {f"{c['topic']}::{c['claim'][:24]}": {} for c in label_claims}
    edges = [{"source": f"{c['topic']}::{c['claim'][:24]}", "relation": "claims", "target": c["topic"]} for c in label_claims]
    sub = graph_run(query="substantiate label claims vs promotion",
                    graph={"nodes": nodes, "edges": edges}, max_hops=3)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"])})

    queue: list[dict] = []
    tickets = []
    for h in sorted(held_out, key=lambda x: (x["topic"], x["claim"])):
        t = escalate_run(result={"topic": h["topic"], "promotional_claim": h["claim"], "violation_kind": h["kind"],
                                 "rule": "FDCA 502 misbranding / off-label promotion", "reason": h["reason_held_out"]},
                         reason="gate_fired",
                         enqueue=lambda x: (queue.append(x), {"ref": f"fda-{len(queue):04d}"})[1])["ticket"]
        tickets.append(t["queue_ref"])

    n = len(held_out)
    result = {"title": "FDA drug-labeling claim review",
              "answer": (f"{n} promotional claim(s) HELD OUT (off-label / contradicts the FDA-approved label): "
                         + "; ".join(sorted({h['claim'] for h in held_out})) if held_out
                         else "all promotional claims substantiated by the FDA-approved label"),
              "details": {"substantiated": {t: g["claim"] for t, g in governing.items()},
                          "held_out_overclaims": [f"[{h['kind']}] {h['claim']} ({h['reason_held_out']})" for h in held_out]},
              "citations": sorted({g["authority_basis"] for g in governing.values()})}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"governing": governing, "held_out": held_out, "escalated": bool(tickets), "tickets": tickets,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC label/promo claim set (public-shape). The FDA-approved label (fda.gov) is authoritative; a
# marketing brochure (unlisted vendor domain) overclaims efficacy and asserts an off-label indication.
_CLAIMS = [
    {"topic": "indication", "claim": "indicated for hypertension in adults", "date": "2025-03",
     "publisher": "FDA approved labeling (DailyMed)", "source_uri": "https://www.fda.gov/drugs/cardizem-x/label.pdf", "signed": True},
    {"topic": "efficacy_bp", "claim": "lowers systolic BP by ~12 mmHg vs placebo", "date": "2025-03",
     "publisher": "FDA approved labeling", "source_uri": "https://www.fda.gov/drugs/cardizem-x/label.pdf", "signed": True},
    {"topic": "efficacy_bp", "claim": "lowers systolic BP by 25 mmHg — best in class", "date": "2025-05",
     "publisher": "BrandRx Marketing", "source_uri": "https://brandrx-promo.example.com/cardizem-x", "signed": False},
    {"topic": "cardiac_risk", "claim": "reduces heart-attack risk by 40%", "date": "2025-05",
     "publisher": "BrandRx Marketing", "source_uri": "https://brandrx-promo.example.com/cardizem-x", "signed": False},
]


def _self_test() -> int:
    out = run(label_claims=_CLAIMS)
    held = {h["claim"]: h for h in out["held_out"]}

    # 1. EARNED authority: the FDA label substantiates efficacy; the marketing overclaim is HELD OUT.
    assert out["governing"]["efficacy_bp"]["claim"] == "lowers systolic BP by ~12 mmHg vs placebo", out["governing"]
    assert "official_agency" in out["governing"]["efficacy_bp"]["tier"]
    assert "lowers systolic BP by 25 mmHg — best in class" in held, list(held)
    assert held["lowers systolic BP by 25 mmHg — best in class"]["kind"] == "contradicts_approved_label"

    # 2. OFF-LABEL: a claim on a topic the FDA label never covers (cardiac risk) is flagged off-label.
    assert "reduces heart-attack risk by 40%" in held
    assert held["reduces heart-attack risk by 40%"]["kind"] == "off_label_unsupported_topic"
    assert out["escalated"] is True and out["tickets"]
    assert "HELD OUT" in out["report_markdown"]

    # 3. FLIP THE SOURCE: if the brochure were the FDA label and vice versa, the substantiated efficacy FLIPS —
    #    proving the decision is EARNED from provenance, not the wording.
    flipped = [dict(c) for c in _CLAIMS]
    for c in flipped:
        if c["topic"] == "efficacy_bp" and "25 mmHg" in c["claim"]:
            c["publisher"], c["source_uri"], c["signed"] = "FDA approved labeling", "https://www.fda.gov/x.pdf", True
        elif c["topic"] == "efficacy_bp" and "12 mmHg" in c["claim"]:
            c["publisher"], c["source_uri"], c["signed"] = "BrandRx Marketing", "https://brandrx-promo.example.com/x", False
    out_f = run(label_claims=flipped)
    assert out_f["governing"]["efficacy_bp"]["claim"] == "lowers systolic BP by 25 mmHg — best in class", out_f["governing"]

    # 4. derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(label_claims=_CLAIMS), sort_keys=True) == json.dumps(run(label_claims=_CLAIMS), sort_keys=True)

    print("PASS — fda_labeling_claim_review: the FDA-approved label (earned authority) substantiates the efficacy "
          "claim; a marketing brochure's 25-mmHg overclaim (contradicts the label) and a 40%-heart-attack-risk "
          "claim (off-label, no approved topic) are HELD OUT and escalated as FDCA-502 risk; flip the source and "
          "the substantiated claim flips — authority is EARNED; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FDA drug-labeling claim review showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(label_claims=_CLAIMS)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
