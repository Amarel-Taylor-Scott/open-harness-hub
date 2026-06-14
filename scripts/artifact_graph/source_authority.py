#!/usr/bin/env python3
"""scripts.artifact_graph.source_authority — EARNED source authority (classify, don't assign).

The load-bearing moat claim is "Baltor establishes which source is authoritative." Made real here: a
source's authority RANK is DERIVED from its publisher/domain (and whether its provenance is verified)
against architecture/source_authority_registry.json — never hand-typed on an artifact. Change the
publisher and the rank changes; a CLAIMED top-tier domain whose provenance is unverified is DOWNGRADED;
an unlisted publisher earns nothing (rank 10), not a neutral default. Reconciliation reads rank from
here, so authority precedence is something a source EARNS by provenance, not a fixture number.

classify(publisher=, source_uri=, signed=) -> {tier, rank, matched_by, domain, signed, label,
downgraded, basis}. Deterministic, offline, no clock. --self-test included.
"""
from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

_REPO = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_REGISTRY = _REPO / "architecture" / "source_authority_registry.json"
_TOP_TIERS = ("source_of_law", "official_agency")  # binding authority → requires VERIFIED provenance
_UNVERIFIED = "unverified"
_DOWNGRADE_TO = "official_guidance"  # a claimed top-tier source without verified provenance lands here
#: tiers that COUNT toward corroboration — an independent AUTHORITATIVE source. Secondary/unverified never do.
_AUTHORITATIVE_TIERS = ("source_of_law", "official_agency", "standards_body", "government_other")


@lru_cache(maxsize=1)
def _registry() -> dict:
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))


def _domain_of(source_uri: str, publisher: str) -> str:
    """Host from a URL; else the publisher string lowercased (so a bare domain also classifies)."""
    s = (source_uri or "").strip()
    if s:
        host = urlsplit(s if "//" in s else "//" + s).netloc.lower()
        if host:
            return host.split("@")[-1].split(":")[0]  # strip any creds/port
    return (publisher or "").strip().lower()


def _best_match(domain: str, publishers: list[dict]) -> dict | None:
    """Longest (most-specific) matching rule wins → sanctionssearch.ofac.treas.gov beats treasury.gov beats .gov."""
    hits = [p for p in publishers if p["match"].lower() in domain]
    return max(hits, key=lambda p: len(p["match"])) if hits else None


def classify(*, publisher: str = "", source_uri: str = "", signed: bool | None = None) -> dict:
    """Resolve a source's authority from its provenance. `signed` (verified at ingest) overrides the
    registry default for that publisher; pass it when ingest actually verified the source's signature."""
    reg = _registry()
    tiers = reg["tiers"]
    domain = _domain_of(source_uri, publisher)
    rule = _best_match(domain, reg["publishers"])
    label = (rule and rule.get("label")) or publisher or domain or "unknown publisher"

    if rule is None:
        rank = tiers[_UNVERIFIED]["rank"]
        return {"tier": _UNVERIFIED, "rank": rank, "matched_by": None, "domain": domain, "signed": False,
                "label": label, "downgraded": False,
                "basis": f"'{domain or publisher or 'unknown'}' is not a listed authoritative publisher → unverified (rank {rank})"}

    is_signed = bool(rule.get("signed", False)) if signed is None else bool(signed)
    tier = rule["tier"]
    downgraded = False
    if tier in _TOP_TIERS and not is_signed:
        tier, downgraded = _DOWNGRADE_TO, True
    rank = tiers[tier]["rank"]
    basis = (f"{label} matched '{rule['match']}' → {tier} (rank {rank}); "
             f"provenance {'verified' if is_signed else 'UNVERIFIED'}"
             + (" — downgraded from a claimed top tier" if downgraded else ""))
    return {"tier": tier, "rank": rank, "matched_by": rule["match"], "domain": domain,
            "signed": is_signed, "label": label, "downgraded": downgraded, "basis": basis}


def classify_payload(payload: dict) -> dict:
    """Classify from an artifact payload's provenance fields: publisher / source_uri / source_signed."""
    return classify(publisher=str(payload.get("publisher", "")),
                    source_uri=str(payload.get("source_uri", "")),
                    signed=payload.get("source_signed"))


def has_provenance(payload: dict) -> bool:
    """True if the payload carries classifiable provenance (so the rank can be EARNED, not assigned)."""
    return bool(payload.get("publisher") or payload.get("source_uri"))


def corroboration(value_claims: list[dict]) -> dict:
    """Multi-source corroboration: does the WINNING value have >=2 INDEPENDENT authoritative sources agreeing?

    ``value_claims`` = [{"value":…, "publisher":…, "source_uri":…, "signed":…}, …]. Independence = distinct
    publisher DOMAINS (two reads of the SAME agency do not corroborate each other). Only authoritative tiers
    count (a vendor blog never corroborates). The winning value is the one with the highest single-source
    authority (ties → more independent authoritative backing); its corroboration is the number of independent
    authoritative domains asserting it. This is the difference between "a source SAYS X" and "independent
    authorities AGREE X" — recorded so a receipt can claim corroboration only when it is earned."""
    enriched = []
    for c in value_claims:
        a = classify(publisher=str(c.get("publisher", "")), source_uri=str(c.get("source_uri", "")), signed=c.get("signed"))
        enriched.append({"value": c.get("value"), "domain": a["domain"], "tier": a["tier"], "rank": a["rank"],
                         "label": a["label"], "authoritative": a["tier"] in _AUTHORITATIVE_TIERS})
    if not enriched:
        return {"value": None, "corroborated": False, "independent_authoritative_sources": 0, "sources": [], "basis": "no claims"}
    by_value: dict = {}
    for e in enriched:
        by_value.setdefault(e["value"], []).append(e)

    def _score(v):
        es = by_value[v]
        return (max(e["rank"] for e in es), len({e["domain"] for e in es if e["authoritative"]}))

    winner = max(sorted(by_value), key=_score)   # sorted() first → deterministic tie-break
    ws = by_value[winner]
    independent_auth = sorted({e["domain"] for e in ws if e["authoritative"]})
    corroborated = len(independent_auth) >= 2
    basis = (f"value {winner!r} asserted by {len(independent_auth)} independent authoritative source(s)"
             + (": " + ", ".join(independent_auth) if independent_auth else "")
             + (" → CORROBORATED" if corroborated else " → single-sourced (not corroborated)"))
    return {"value": winner, "corroborated": corroborated,
            "independent_authoritative_sources": len(independent_auth),
            "sources": [{"label": e["label"], "domain": e["domain"], "tier": e["tier"]} for e in ws if e["authoritative"]],
            "basis": basis}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    law = classify(publisher="eCFR", source_uri="https://www.ecfr.gov/current/title-12/part-1005/section-1005.11")
    ck("eCFR → source_of_law (rank 100), signed", law["tier"] == "source_of_law" and law["rank"] == 100 and law["signed"])
    cfpb = classify(source_uri="https://www.consumerfinance.gov/faq")
    ck("consumerfinance.gov → official_agency (rank 90)", cfpb["tier"] == "official_agency" and cfpb["rank"] == 90)
    vendor = classify(publisher="Acme Compliance LLC", source_uri="https://acme-compliance.com/blog/reg-e")
    ck("a vendor blog earns NO authority (unverified, rank 10)", vendor["tier"] == "unverified" and vendor["rank"] == 10)

    # THE PROOF THAT IT IS EARNED, NOT ASSIGNED: same fact, flip the publisher → the winner flips.
    a_on_law = classify(source_uri="https://ecfr.gov/x")["rank"]
    a_on_blog = classify(source_uri="https://acme-compliance.com/x")["rank"]
    ck("flip-the-publisher changes the rank (authority is EARNED, not a fixture)", a_on_law > a_on_blog, f"{a_on_law} vs {a_on_blog}")

    # claimed != verified: an UNSIGNED claim to a top-tier domain is downgraded, not granted binding authority
    unsigned = classify(source_uri="https://treasury.gov/x", signed=False)
    ck("unsigned claim to a top-tier domain is DOWNGRADED (claimed != verified)",
       unsigned["tier"] == "official_guidance" and unsigned["downgraded"])
    signed = classify(source_uri="https://treasury.gov/x", signed=True)
    ck("the same source WITH verified provenance earns official_agency", signed["tier"] == "official_agency" and signed["rank"] == 90)

    # most-specific match wins
    ofac = classify(source_uri="https://sanctionssearch.ofac.treas.gov/")
    ck("longest/most-specific domain match wins (OFAC SDN, not bare .gov)", ofac["matched_by"] == "sanctionssearch.ofac.treas.gov")

    # every basis is human-readable lineage for the receipt
    ck("classification carries a human-readable basis (receipt lineage)", all("rank" in c["basis"] for c in (law, cfpb, vendor)))

    print(("PASS — " if not fails else "FAIL — ")
          + "source_authority: rank is DERIVED from publisher/domain+provenance (earned, not assigned); "
            "flip-the-publisher flips the winner; unsigned top-tier claims downgraded; unlisted earns rank 10.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
