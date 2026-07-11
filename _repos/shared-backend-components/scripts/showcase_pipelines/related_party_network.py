#!/usr/bin/env python3
"""Showcase: RELATED-PARTY / shell-network discovery — hidden links via shared identifiers + M&A.

The use case the owner asked for: find NETWORKS OF RELATIONSHIPS between businesses (e.g. staffing /
employment agencies) that present as independent but are really one operation — discovered by
clustering over SHARED IDENTIFIERS (registered address, phone, officer, bank account) and corporate
events (mergers & acquisitions). The classic shell-network / collusion / labor-trafficking-front /
sanctions-evasion-by-related-party pattern.

Structural gap (durability: AGGREGATION + entity-resolution): a frontier model takes each entity at
face value — different names, different-looking rows — and says "they appear independent." It cannot
normalize identifiers, traverse the shared-identifier graph, or compute connected components, and it
can't tell a DISCLOSED M&A group (legitimate) from an UNDISCLOSED shared-address-and-phone-and-officer
cluster (a shell network). That is deterministic graph arithmetic over a governed registry, not recall.

Composition (real `_repos/shared-backend-components/scripts/processors` callables + deterministic identifier-graph clustering):
  1. _normalize_identifiers   — canonicalize address/phone/officer (the entity-resolution prep)
  2. _link_graph + _components— build the shared-identifier + M&A graph, then UNION-FIND the
                                connected components (related-party clusters) — the domain step
  3. fuzzy_trigram_retrieve   — soft-link near-duplicate NAMES too ("Acme Staffing" ~ "ACME Staffing LLC")
  4. graphrag_retrieve        — present the relationship subgraph around a queried entity
  5. _risk_score             — shell-network heuristic: many "independent" entities sharing a single
                                address+phone+officer with NO disclosed M&A → HIGH; a disclosed M&A group → NORMAL
  6. source_precedence_select — a signed registry filing governs over a scraped M&A news article
  7. escalate_human + deliver_report — escalate the high-risk clusters with the link evidence

Run:  python3 _repos/shared-backend-components/scripts/showcase_pipelines/related_party_network.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

#: A cluster sharing at least this many DISTINCT identifier TYPES (address/phone/officer/account),
#: with no disclosed M&A explaining the link, is treated as a likely shell network → escalate.
SHELL_SHARED_TYPE_THRESHOLD = 2
#: Identifier kinds that link entities. M&A is a DISCLOSED relationship (legitimate); the others are
#: undisclosed shared attributes (suspicious when they pile up).
_UNDISCLOSED_KINDS = ("address", "phone", "officer", "account")


def _norm(kind: str, value: str) -> str:
    """Canonicalize an identifier so '(555) 123-4567' and '555-123-4567' collide (entity resolution)."""
    v = str(value).strip().lower()
    if kind == "phone":
        return re.sub(r"\D", "", v)                         # digits only
    if kind == "address":
        v = re.sub(r"[.,#]", " ", v)
        v = (v.replace("suite", "ste").replace("street", "st").replace("avenue", "ave")
             .replace("road", "rd").replace("floor", "fl"))
        return re.sub(r"\s+", " ", v).strip()
    if kind == "officer":                                   # strip honorific punctuation: "J. Doe" == "J Doe"
        return re.sub(r"\s+", " ", re.sub(r"[.,]", " ", v)).strip()
    return re.sub(r"\s+", " ", v).strip()                   # account: collapse whitespace


def _link_graph(entities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Edges between entities that share a normalized identifier; each edge carries the evidence."""
    by_key: dict[tuple[str, str], list[str]] = {}
    for e in entities:
        for kind in _UNDISCLOSED_KINDS:
            for raw in e.get(kind + "s", []) if kind + "s" in e else ([e[kind]] if kind in e else []):
                by_key.setdefault((kind, _norm(kind, raw)), []).append(e["id"])
    edges: dict[str, list[dict[str, Any]]] = {e["id"]: [] for e in entities}
    for (kind, value), ids in by_key.items():
        uniq = sorted(set(ids))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                edges[uniq[i]].append({"to": uniq[j], "kind": kind, "shared": value})
                edges[uniq[j]].append({"to": uniq[i], "kind": kind, "shared": value})
    return edges


def _components(entities: list[dict[str, Any]], edges: dict[str, list[dict]],
                ma_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union-Find over shared-identifier edges AND disclosed M&A edges → related-party clusters."""
    parent = {e["id"]: e["id"] for e in entities}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for src, es in edges.items():
        for e in es:
            union(src, e["to"])
    for m in ma_events:                                     # an acquisition links acquirer + target
        if m["acquirer"] in parent and m["target"] in parent:
            union(m["acquirer"], m["target"])

    groups: dict[str, list[str]] = {}
    for eid in parent:
        groups.setdefault(find(eid), []).append(eid)

    clusters = []
    for members in groups.values():
        members = sorted(members)
        shared_kinds = sorted({e["kind"] for m in members for e in edges[m]})
        disclosed = [m for m in ma_events if m["acquirer"] in members and m["target"] in members]
        clusters.append({"members": members, "shared_kinds": shared_kinds,
                         "disclosed_ma": [f"{m['acquirer']}→{m['target']}" for m in disclosed]})
    return sorted(clusters, key=lambda c: (-len(c["members"]), c["members"][0]))


def _risk_score(cluster: dict[str, Any]) -> dict[str, Any]:
    """Shell-network heuristic: many entities linked by ≥N undisclosed shared identifier types, with
    NO disclosed M&A explaining the link → HIGH. A disclosed-M&A group, or a singleton → low."""
    n = len(cluster["members"])
    shared = len(cluster["shared_kinds"])
    if n < 2:
        return {"level": "none", "reason": "standalone entity (no shared identifiers)"}
    if cluster["disclosed_ma"] and shared < SHELL_SHARED_TYPE_THRESHOLD:
        return {"level": "normal", "reason": f"linked by disclosed M&A ({', '.join(cluster['disclosed_ma'])})"}
    if shared >= SHELL_SHARED_TYPE_THRESHOLD:
        return {"level": "high",
                "reason": f"{n} entities present as independent but share {shared} identifier types "
                          f"({', '.join(cluster['shared_kinds'])}) with no disclosed M&A — likely one operation"}
    return {"level": "review", "reason": f"{n} entities share {shared} identifier type — confirm"}


def run(*, entities: list[dict[str, Any]], ma_events: list[dict[str, Any]],
        sources: list[dict[str, Any]], focus: str | None = None) -> dict[str, Any]:
    """Discover related-party clusters across ``entities`` and flag likely shell networks."""
    trace: list[dict[str, Any]] = []

    # 1+2. normalize identifiers → shared-identifier graph → connected components.
    edges = _link_graph(entities)
    clusters = _components(entities, edges, ma_events)
    trace.append({"step": "identifier_graph_components", "clusters": len(clusters),
                  "sizes": [len(c["members"]) for c in clusters]})

    # 3. soft-link near-duplicate NAMES (catches "Acme Staffing" vs "ACME Staffing LLC").
    names = [{"id": e["id"], "text": e["name"]} for e in entities]
    name_links = []
    for e in entities:
        cands = fuzzy_run(query=e["name"], corpus=[n for n in names if n["id"] != e["id"]])["candidates"]
        for c in cands:
            if c.get("trigram_similarity", 0) >= 0.6:
                name_links.append({"a": e["id"], "b": c["id"], "similarity": round(c["trigram_similarity"], 3)})
    trace.append({"step": "fuzzy_name_softlink", "near_duplicate_name_pairs": len(name_links) // 2})

    # 4. graph view around the focus entity (or the largest cluster's first member).
    focus_id = focus or clusters[0]["members"][0]
    graph_nodes = {e["id"]: {} for e in entities}
    graph_edges = [{"source": s, "relation": ed["kind"], "target": ed["to"]} for s, es in edges.items() for ed in es]
    sub = graph_run(query=f"who is connected to {focus_id}",
                    graph={"nodes": graph_nodes, "edges": graph_edges}, max_hops=3)["subgraph"]
    trace.append({"step": "graphrag_retrieve", "focus": focus_id, "reached": sorted(sub["nodes"])})

    # 5. risk-score each multi-entity cluster.
    scored = [{**c, "risk": _risk_score(c)} for c in clusters]
    high = [c for c in scored if c["risk"]["level"] == "high"]
    trace.append({"step": "risk_score", "high_risk_clusters": len(high),
                  "levels": sorted({c["risk"]["level"] for c in scored})})

    # 6. which source governs (a signed registry filing beats scraped M&A news).
    prec = precedence_run(candidates=sources)
    governing = prec["selected"][0]["id"] if prec["selected"] else None
    trace.append({"step": "source_precedence_select", "governing": governing})

    # 7. escalate the high-risk networks + report.
    queue: list[dict] = []
    tickets = []
    name_of = {e["id"]: e["name"] for e in entities}
    for c in high:
        t = escalate_run(result={"members": [name_of[m] for m in c["members"]], "reason": c["risk"]["reason"],
                                 "shared_identifiers": c["shared_kinds"], "governing_source": governing},
                         reason="gate_fired",
                         enqueue=lambda t: (queue.append(t), {"ref": f"rel-{len(queue):04d}"})[1])["ticket"]
        tickets.append(t["queue_ref"])
    result = {"title": "Related-party network discovery",
              "answer": (f"{len(high)} likely shell network(s) flagged" if high
                         else "no undisclosed related-party networks found"),
              "details": {"clusters": len(clusters),
                          "high_risk": [{"members": [name_of[m] for m in c["members"]],
                                         "shared": c["shared_kinds"]} for c in high]},
              "citations": [governing] if governing else []}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"clusters": [{"members": [name_of[m] for m in c["members"]],
                          "shared_kinds": c["shared_kinds"], "disclosed_ma": c["disclosed_ma"],
                          "risk": c["risk"]["level"], "why": c["risk"]["reason"]} for c in scored],
            "high_risk_count": len(high), "escalated": tickets, "near_duplicate_name_pairs": name_links,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC registry (public-shape data only; proves the mechanism, not real businesses).
# Cluster A — three "independent" staffing agencies sharing ONE address + phone + officer (shell network).
# Cluster B — a DISCLOSED M&A group (legitimate). Solo Staffing — standalone.
_ENTITIES = [
    {"id": "e1", "name": "Apex Staffing LLC", "address": "100 Oak Ave, Suite 5", "phone": "(555) 000-1111",
     "officer": "J. Doe"},
    {"id": "e2", "name": "Summit Labor Partners", "address": "100 Oak Avenue Ste 5", "phone": "555-000-1111",
     "officer": "J Doe"},
    {"id": "e3", "name": "Premier Workforce Inc", "address": "100 oak ave  ste 5", "phone": "5550001111",
     "officer": "j doe"},
    {"id": "e4", "name": "BigCo Staffing", "address": "1 Corporate Plaza", "phone": "(555) 222-3333",
     "officer": "A. Smith"},
    {"id": "e5", "name": "Regional Temps", "address": "42 Market St", "phone": "(555) 444-5555",
     "officer": "B. Jones"},
    {"id": "e6", "name": "Solo Staffing", "address": "9 Lone Rd", "phone": "(555) 777-8888", "officer": "C. Lee"},
]
_MA_EVENTS = [  # disclosed mergers & acquisitions (the legitimate corporate-group link)
    {"acquirer": "e4", "target": "e5", "date": "2025-03-01", "source": "registry-filing@2025"},
]
_SOURCES = [
    {"id": "corp-registry@2026-06-12", "text": "state corporate registry filings (signed, current)",
     "source_kind": "source_of_law", "signed": True, "valid_through": 2_000_000.0, "as_of": 1_000_000.0},
    {"id": "ma-news-scrape@old", "text": "scraped M&A news articles", "source_kind": "secondary_report",
     "signed": False, "valid_through": 500_000.0, "as_of": 1_000_000.0},
]


def _self_test() -> int:
    out = run(entities=_ENTITIES, ma_events=_MA_EVENTS, sources=_SOURCES)
    by_members = {tuple(sorted(c["members"])): c for c in out["clusters"]}
    # The three shell agencies collapse into ONE high-risk cluster (normalized address/phone/officer all collide).
    shell = next(c for c in out["clusters"] if "Apex Staffing LLC" in c["members"])
    assert sorted(shell["members"]) == ["Apex Staffing LLC", "Premier Workforce Inc", "Summit Labor Partners"], shell
    assert shell["risk"] == "high", shell
    assert set(shell["shared_kinds"]) >= {"address", "phone", "officer"}, shell["shared_kinds"]
    assert out["high_risk_count"] == 1 and out["escalated"], out
    # The disclosed-M&A pair is ONE cluster but NORMAL (legitimately related, not a shell).
    ma = next(c for c in out["clusters"] if "BigCo Staffing" in c["members"])
    assert sorted(ma["members"]) == ["BigCo Staffing", "Regional Temps"] and ma["risk"] == "normal", ma
    assert ma["disclosed_ma"], ma
    # The standalone agency is its own singleton, no risk (the heuristic doesn't over-flag).
    solo = next(c for c in out["clusters"] if "Solo Staffing" in c["members"])
    assert solo["members"] == ["Solo Staffing"] and solo["risk"] == "none", solo
    # The signed registry governs over scraped news.
    gov = next(t for t in out["trace"] if t["step"] == "source_precedence_select")["governing"]
    assert gov == "corp-registry@2026-06-12", gov
    assert "shell network" in out["report_markdown"] or "flagged" in out["report_markdown"]
    # Identifier normalization is doing the work: with RAW (un-normalized) ids the shells wouldn't merge.
    assert _norm("phone", "(555) 000-1111") == _norm("phone", "5550001111") == "5550001111"
    assert _norm("address", "100 Oak Ave, Suite 5") == _norm("address", "100 oak avenue ste 5")
    # Derived honesty + determinism.
    assert out["serves_truth"] is False
    assert json.dumps(run(entities=_ENTITIES, ma_events=_MA_EVENTS, sources=_SOURCES), sort_keys=True) == \
           json.dumps(run(entities=_ENTITIES, ma_events=_MA_EVENTS, sources=_SOURCES), sort_keys=True)
    print("PASS — related_party_network: normalize identifiers → shared-identifier graph → union-find "
          "components; 3 'independent' agencies sharing one address+phone+officer collapse into ONE "
          "HIGH-risk shell network (escalated), a DISCLOSED M&A pair stays NORMAL, a standalone stays "
          "singleton; signed registry governs; the hidden network a bare model can't see; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Related-party / shell-network discovery showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(entities=_ENTITIES, ma_events=_MA_EVENTS, sources=_SOURCES)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
