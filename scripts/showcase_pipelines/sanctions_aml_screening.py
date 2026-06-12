#!/usr/bin/env python3
"""Showcase: SANCTIONS / AML ownership screening — the OFAC 50% Rule (a non-CFPB example).

Scenario where a bare model fails STRUCTURALLY (durability: aggregation): an entity is NOT on
the SDN list itself, but is majority-owned (aggregate ≥ 50%) by listed persons through an
ownership chain. A frontier model can't traverse an ownership graph or know today's delta-list
additions; the 50% Rule is arithmetic over a governed graph, not recall.

Composition (real `scripts/processors` callables):
  1. fuzzy_trigram_retrieve     — name match against the list: a near-exact hit is a DIRECT
                                  match (unlisted ≠ clear is the whole point), lower hits are variants
  2. graphrag_retrieve          — traverse the OWNERSHIP graph from the entity to listed owners
  3. _fifty_percent_rule        — deterministic aggregation of listed ownership along the paths
                                  (the governed domain step the model can't do)
  4. source_precedence_select   — which list snapshot governs (signed/current wins)
  5. escalate_human + deliver_report — block + route to review with the ownership evidence

Run:  python3 scripts/showcase_pipelines/sanctions_aml_screening.py [--self-test]
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

from scripts.processors.retrieval.fuzzy_trigram_retrieve import run as fuzzy_run
from scripts.processors.retrieval.graphrag_retrieve import run as graph_run
from scripts.processors.retrieval.source_precedence_select import run as precedence_run
from scripts.processors.deliver.escalate_human import run as escalate_run
from scripts.processors.deliver.deliver_report import run as report_run

#: OFAC's blocking threshold — aggregate listed ownership at or above this blocks the entity.
FIFTY_PERCENT_RULE = 0.50
#: A fuzzy name match at/above this trigram similarity is treated as a DIRECT list hit
#: (an exact name = ~1.0); below it the candidate is only a variant to review.
DIRECT_HIT_SIMILARITY = 0.95


def _fifty_percent_rule(entity: str, graph: dict[str, Any], listed: set[str]) -> dict[str, Any]:
    """Aggregate the ownership of ``entity`` held (directly + indirectly) by LISTED parties.

    Deterministic graph arithmetic the bare model can't do: each ``owns`` edge carries a ``pct``;
    indirect ownership multiplies along the chain; total listed ownership is the sum over all
    paths from listed roots to the entity. >= FIFTY_PERCENT_RULE → blocked."""
    # owners_of[x] = [(owner, pct)]
    owners_of: dict[str, list[tuple[str, float]]] = {}
    for e in graph.get("edges", []):
        if e.get("relation") == "owns":
            owners_of.setdefault(str(e["target"]), []).append((str(e["source"]), float(e.get("pct", 0.0))))

    # listed ownership of `entity` = Σ over owners: pct * (1 if owner listed else listed-share-of-owner)
    seen: set[str] = set()

    def listed_share(node: str) -> float:
        if node in seen:  # cycle guard
            return 0.0
        seen.add(node)
        total = 0.0
        for owner, pct in owners_of.get(node, []):
            if owner in listed:
                total += pct
            else:
                total += pct * listed_share(owner)
        seen.discard(node)
        return total

    share = round(listed_share(entity), 6)
    return {"entity": entity, "aggregate_listed_ownership": share,
            "blocked": share >= FIFTY_PERCENT_RULE, "threshold": FIFTY_PERCENT_RULE}


def run(*, entity: str, sdn_list: list[dict[str, Any]], ownership_graph: dict[str, Any],
        list_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Screen ``entity`` against the SDN list + the 50% ownership rule."""
    trace: list[dict[str, Any]] = []

    # 1+2. fuzzy name match: a near-exact hit is a DIRECT list match; lower-similarity hits are
    # variants to review. (exact-id-lookup is for structured ids like CVE/statute, not names.)
    fuzzy = fuzzy_run(query=entity, corpus=sdn_list)["candidates"]
    top_sim = fuzzy[0]["trigram_similarity"] if fuzzy else 0.0
    direct_hit = bool(fuzzy) and (top_sim >= DIRECT_HIT_SIMILARITY
                                  or any(t["distance"] == 0 for t in fuzzy[0]["typo_matches"]))
    direct = {"found": direct_hit, "matched": fuzzy[0]["id"] if direct_hit else None}
    trace.append({"step": "fuzzy_trigram_retrieve", "direct_hit": direct_hit,
                  "name_variants": [c["id"] for c in fuzzy[:3]]})

    # 3. ownership-graph traversal from the entity.
    sub = graph_run(query=f"who owns {entity}", graph=ownership_graph, max_hops=3)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "reached": sorted(sub["nodes"]), "seeds": sub["seeds"]})

    # 4. the 50% rule — deterministic aggregation over the ownership subgraph.
    listed = {str(d["id"]) for d in sdn_list} | {str(d.get("name", "")) for d in sdn_list}
    listed |= {n for n in ownership_graph.get("nodes", {}) if ownership_graph["nodes"][n].get("sdn_listed")}
    rule = _fifty_percent_rule(entity, ownership_graph, listed)
    trace.append({"step": "fifty_percent_rule", **rule})

    # 5. which list snapshot governs.
    prec = precedence_run(candidates=list_sources)
    trace.append({"step": "source_precedence_select", "governing": prec["selected"][0]["id"] if prec["selected"] else None})

    blocked = bool(direct["found"]) or rule["blocked"]
    queue: list[dict] = []
    ticket = None
    if blocked:
        reason = "direct SDN match" if direct["found"] else \
            f"aggregate listed ownership {rule['aggregate_listed_ownership']:.0%} >= {int(FIFTY_PERCENT_RULE*100)}% rule"
        ticket = escalate_run(result={"entity": entity, "reason": reason, "ownership": rule,
                                      "governing_source": prec["selected"][0]["id"] if prec["selected"] else None},
                              reason="gate_fired", enqueue=lambda t: (queue.append(t), {"ref": f"sar-{len(queue):04d}"})[1])["ticket"]
    result = {"title": f"Sanctions screening — {entity}",
              "answer": "BLOCKED" if blocked else "no listed match (direct or via 50% rule)",
              "details": {"direct_hit": direct["found"],
                          "aggregate_listed_ownership": rule["aggregate_listed_ownership"],
                          "fifty_percent_blocked": rule["blocked"]},
              "citations": [prec["selected"][0]["id"]] if prec["selected"] else []}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"entity": entity, "blocked": blocked,
            "aggregate_listed_ownership": rule["aggregate_listed_ownership"],
            "escalated": ticket is not None, "ticket": ticket["queue_ref"] if ticket else None,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC data (public-metadata shapes only; proves the mechanism, not a real list).
_SDN = [
    {"id": "Volkov, Dmitri", "name": "Volkov, Dmitri", "text": "Dmitri Volkov — listed individual (SDN)"},
    {"id": "Northstar Holdings", "name": "Northstar Holdings", "text": "Northstar Holdings — blocked entity"},
]
_LIST_SOURCES = [
    {"id": "ofac-sdn@2026-06-12", "text": "OFAC SDN list, current delta", "source_kind": "source_of_law",
     "signed": True, "valid_through": 2_000_000.0, "as_of": 1_000_000.0},
    {"id": "thirdparty-mirror@old", "text": "third-party SDN mirror", "source_kind": "secondary_report",
     "signed": False, "valid_through": 500_000.0, "as_of": 1_000_000.0},
]
# Acme Trading is NOT on the list, but Volkov (listed) owns 30% directly + 60% of MidCo which owns 40%
# of Acme → 0.30 + 0.60*0.40 = 0.54 ≥ 50% → blocked by the rule.
_OWNERSHIP = {
    "nodes": {"Acme Trading": {}, "MidCo": {}, "Volkov, Dmitri": {"sdn_listed": True}, "CleanCo": {}},
    "edges": [
        {"source": "Volkov, Dmitri", "relation": "owns", "target": "Acme Trading", "pct": 0.30},
        {"source": "MidCo", "relation": "owns", "target": "Acme Trading", "pct": 0.40},
        {"source": "Volkov, Dmitri", "relation": "owns", "target": "MidCo", "pct": 0.60},
        {"source": "CleanCo", "relation": "owns", "target": "MidCo", "pct": 0.40},
    ],
}


def _self_test() -> int:
    # The unlisted-but-majority-owned entity is BLOCKED by the 50% rule (0.30 + 0.60*0.40 = 0.54).
    out = run(entity="Acme Trading", sdn_list=_SDN, ownership_graph=_OWNERSHIP, list_sources=_LIST_SOURCES)
    assert out["blocked"] is True, out
    assert abs(out["aggregate_listed_ownership"] - 0.54) < 1e-6, out["aggregate_listed_ownership"]
    assert out["escalated"] is True and out["ticket"]
    assert "BLOCKED" in out["report_markdown"]
    # A directly-listed entity is blocked too.
    direct = run(entity="Northstar Holdings", sdn_list=_SDN, ownership_graph=_OWNERSHIP, list_sources=_LIST_SOURCES)
    assert direct["blocked"] is True
    # An entity with only MINORITY listed ownership is NOT blocked (the rule is real, not a blanket flag).
    clean_graph = {"nodes": {"Beta Corp": {}, "Volkov, Dmitri": {"sdn_listed": True}},
                   "edges": [{"source": "Volkov, Dmitri", "relation": "owns", "target": "Beta Corp", "pct": 0.20}]}
    clean = run(entity="Beta Corp", sdn_list=_SDN, ownership_graph=clean_graph, list_sources=_LIST_SOURCES)
    assert clean["blocked"] is False and clean["aggregate_listed_ownership"] == 0.20
    assert clean["escalated"] is False
    # The current signed list snapshot governs (not the old mirror).
    prec_step = next(t for t in out["trace"] if t["step"] == "source_precedence_select")
    assert prec_step["governing"] == "ofac-sdn@2026-06-12"
    # Derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(entity="Acme Trading", sdn_list=_SDN, ownership_graph=_OWNERSHIP, list_sources=_LIST_SOURCES),
                      sort_keys=True) == json.dumps(run(entity="Acme Trading", sdn_list=_SDN,
                      ownership_graph=_OWNERSHIP, list_sources=_LIST_SOURCES), sort_keys=True)
    print("PASS — sanctions_aml_screening: fuzzy name-match + ownership-graph traversal + the 50% Rule "
          "(0.30 + 0.60×0.40 = 54% ≥ 50% → BLOCKED) — catches an UNLISTED entity the bare model clears; "
          "minority ownership not blocked; current signed list governs; escalates; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sanctions/AML 50%-rule screening showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(entity="Acme Trading", sdn_list=_SDN, ownership_graph=_OWNERSHIP, list_sources=_LIST_SOURCES)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
