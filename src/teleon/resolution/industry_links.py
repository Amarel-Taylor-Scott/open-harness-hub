"""industry_links — the per-INDUSTRY linking-rules surface (the OpenLinkingHub substrate). For each industry it declares
which entity-resolution RULESET applies to each entity ROLE (provider->person, practice->organization, location->address)
and the cross-entity LINKAGE rules (a person affiliated_with an organization when they agree on the declared fields). It
composes the shared entity_resolver — the same engine + rulesets, parameterized per industry. serves_truth=false (links
are proposed candidates; a review tier + governance dispose).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.resolution import entity_resolver as ER

_RULES = Path(__file__).resolve().parents[3] / "architecture" / "industry_linking_rules.json"


@lru_cache(maxsize=1)
def _rules() -> dict:
    return json.loads(_RULES.read_text())


def industries() -> list:
    return sorted(_rules()["industries"])


def industry(name: str) -> dict | None:
    if name in _rules().get("excluded", []):
        return None
    return _rules()["industries"].get(name)


def ruleset_for(industry_name: str, role: str) -> str | None:
    """Which entity-resolution ruleset applies to an entity role in this industry (e.g. healthcare/provider -> person)."""
    return (industry(industry_name) or {}).get("entities", {}).get(role)


def resolve_role(industry_name: str, role: str, records: list) -> dict:
    """Dedup the records for an entity role using THAT industry+role's ruleset (composes entity_resolver)."""
    rs = ruleset_for(industry_name, role)
    if rs is None:
        return {"error": f"no ruleset for {industry_name}/{role}", "serves_truth": False}
    return ER.resolve_entities(records, rs)


def _agreement(link_on: list, fr: dict, to: dict) -> float:
    """Mean field agreement (token_set on normalized values) over the link fields. Each entry is 'field' (same on both)
    or 'from_field:to_field'. Name-ish fields use the company-name normalizer; address fields the address normalizer."""
    scores = []
    for entry in link_on:
        ff, tf = entry.split(":", 1) if ":" in entry else (entry, entry)
        va, vb = fr.get(ff), to.get(tf)
        if va is None or vb is None:
            continue
        nrm = ER._NORMALIZERS["address"] if "address" in ff else ER._NORMALIZERS["company_name"]
        scores.append(ER.token_set(nrm(va), nrm(vb)))
    return sum(scores) / len(scores) if scores else 0.0


def _rid(r: dict):
    return r.get("id", r.get("provider_id"))


def link(industry_name: str, records_by_role: dict) -> dict:
    """Apply the industry's cross-entity LINKAGE rules. records_by_role: {role: [records]}. Returns the proposed links:
    [{from_role, from_id, to_role, to_id, type, score}] where a from-record agrees with a to-record on the link fields."""
    ind = industry(industry_name)
    if ind is None:
        return {"error": f"unknown or excluded industry {industry_name!r}", "serves_truth": False}
    links = []
    for rule in ind.get("links", []):
        for fr in records_by_role.get(rule["from"], []):
            for to in records_by_role.get(rule["to"], []):
                score = _agreement(rule["link_on"], fr, to)
                if score >= rule.get("threshold", 0.8):
                    links.append({"from_role": rule["from"], "from_id": _rid(fr), "to_role": rule["to"],
                                  "to_id": _rid(to), "type": rule["type"], "score": round(score, 3)})
    return {"industry": industry_name, "links": links, "serves_truth": False}
