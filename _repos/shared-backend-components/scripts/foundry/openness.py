#!/usr/bin/env python3
"""Foundry openness — classify a promoted component OPEN vs COMMERCIAL.

Operationalizes the open-core boundary (`_repos/_shared/strategy/open-core-model.md`) so the
open/closed split is a *property of the pipeline*, not a manual sort. Two axes:

  1. **Execution** — does it need a runtime/host/credentials? `code-executing`
     components (custom tools, harnesses, adapters, pipelines) and **verified RAG
     databases** (OHH-built retrieval) are **commercial**. (Freshness/dynamic is a
     *delivery* axis — billed via `access.py`, not an openness axis.)
  2. **Verification provenance** — *who* vouched for the content? Knowledge/rules
     **published or verified by an external public authority** (a government agency,
     standards body) under a public license are **open** (the funnel — "some free
     knowledge components, especially those published or verified by others");
     content OHH itself curated/verified is **commercial** (the verification is the
     value).

Format itself — component **definitions, schemas, the export capability** — is always
open; that lives in the public repo + engine, not gated here. This classifier only
decides where a *promoted component's content/execution* sits.

stdlib-only. Run ``python -m scripts.foundry.openness`` for the offline self-test.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from scripts.foundry.contracts import Candidate

TIER_OPEN = "open"
TIER_COMMERCIAL = "commercial"

# type → which axis governs it
CODE_EXECUTING_TYPES = {"tool", "harness", "adapter", "pipeline"}    # need runtime/host
CONTENT_TYPES = {"knowledge-pack", "dataset", "rule-pack", "logic-pack"}  # provenance axis
LOGIC_TYPES = {"processor", "pattern", "persona", "rubric", "benchmark"}  # format/logic/eval

# public-license terms that signal openly-redistributable public content
OPEN_PUBLIC_LICENSE_TERMS = ("public-domain", "public domain", "cc0", "cc-by")
# rule-pack families that require retrieval/network at runtime → commercial
RUNTIME_RULE_FAMILIES = {"rag", "online_search"}
# explicit public-authority domains (govs are caught by the 'gov'/'mil' label test)
PUBLIC_AUTHORITY_DOMAINS = {
    "europa.eu", "un.org", "who.int", "oecd.org", "iso.org", "ietf.org", "w3.org",
    "worldbank.org", "imf.org", "wto.org", "ilo.org", "imo.org",
}
PUBLIC_AUTHORITY_AUTHOR_HINTS = (
    "government", "ministry", "agency", "commission", "authority", "united nations",
    "european union", "european commission", "nist", "iso/iec", "world health",
    "oecd", "standards body", "regulator",
)

# Public-good domains that are FREE TIER regardless of execution/provenance (a mission
# carve-out — e.g. anti-human-trafficking). Deliberately tight, and deliberately EXCLUDES
# the generic ESG / forced-labor / modern-slavery wedge (that stays the paid vertical).
# Extend via config, not by fuzzy guessing.
PUBLIC_GOOD_DOMAINS = {
    "anti_human_trafficking", "human_trafficking", "anti_trafficking", "trafficking",
    "child_safety", "online_child_safety", "csae", "csam", "gbv",
    "humanitarian", "humanitarian_response", "disaster_response", "famine_response",
    "refugee", "refugee_response", "public_health_emergency",
}
# Verified-publisher classes whose components are free tier when published through an
# OpenHubForAI account (a government entity / public authority / standards body).
FREE_PUBLISHER_CLASSES = {"government", "public_authority", "standards_body"}


def _host(url: str) -> str:
    try:
        return (urlsplit(url or "").netloc or "").lower().lstrip("www.")
    except ValueError:
        return ""


def is_public_license(license_str: str) -> bool:
    lic = (license_str or "").lower()
    return any(term in lic for term in OPEN_PUBLIC_LICENSE_TERMS)


def is_public_authority(source: dict) -> bool:
    """Heuristic: a government / standards body / public authority published it."""
    host = _host(source.get("source_url", ""))
    labels = set(host.split("."))
    if {"gov", "mil", "gob", "gouv"} & labels:               # bsp.gov.ph, nist.gov, gov.uk, gob.mx
        return True
    if any(host == d or host.endswith("." + d) for d in PUBLIC_AUTHORITY_DOMAINS):
        return True
    author = (source.get("author") or "").lower()
    if any(h in author for h in PUBLIC_AUTHORITY_AUTHOR_HINTS):
        return True
    return source.get("publisher_class") == "public_authority" or bool(source.get("externally_verified"))


def externally_verified_public(source: dict) -> bool:
    return is_public_license(source.get("license", "")) and is_public_authority(source)


def _is_rag_database(body: dict) -> bool:
    """A verified RAG database = OHH-built vector retrieval (the moat), not a passthrough."""
    if "rag_vector" in (body.get("retrieval") or []):
        return True
    if ((body.get("indexing") or {}).get("dense") or {}).get("enabled"):
        return True
    return body.get("family") in RUNTIME_RULE_FAMILIES


def _norm(value: Any) -> str:
    return str(value or "").lower().replace("-", "_").strip()


def is_public_good(candidate: Candidate) -> bool:
    """Mission/public-good component (anti-trafficking, child-safety, humanitarian) —
    free tier regardless of execution or provenance. Reads explicit `public_good: true`,
    a curated domain set, or public-good language on the gap."""
    body = candidate.body or {}
    if body.get("public_good") is True:
        return True
    tags: set[str] = set()
    for facet in ("industry", "capability", "tags"):
        tags.update(_norm(v) for v in (body.get(facet) or []))
    tags.update(_norm(v) for v in ((candidate.gap or {}).get("industry") or []))
    if tags & PUBLIC_GOOD_DOMAINS:
        return True
    blob = (" ".join(tags) + " " + _norm((candidate.gap or {}).get("summary"))).replace("_", " ")
    return any(k in blob for k in ("human trafficking", "anti trafficking", "child safety",
                                   "humanitarian", "disaster response", "refugee"))


def verified_public_publisher(source: dict) -> bool:
    """A government / public authority publishing through a VERIFIED OHH account → free."""
    return bool(source.get("publisher_verified")) and _norm(source.get("publisher_class")) in FREE_PUBLISHER_CLASSES


def classify(candidate: Candidate) -> dict[str, Any]:
    """Return {tier, basis, reason, axes}. ``tier == 'open'`` means **free tier**."""
    t = candidate.target_type
    body = candidate.body or {}
    source = candidate.source or {}
    axes = {"execution": "static", "provenance": "n_a"}

    # precedence 0 — public-good mission carve-out → FREE (overrides the paywall, incl. RAG)
    if is_public_good(candidate):
        return {"tier": TIER_OPEN, "basis": "public_good", "axes": axes,
                "reason": "public-good domain (e.g. anti-human-trafficking) — free tier"}

    # precedence 1 — published via a verified government / public-authority OHH account → FREE
    if verified_public_publisher(source):
        axes["provenance"] = "public"
        return {"tier": TIER_OPEN, "basis": "verified_public_publisher", "axes": axes,
                "reason": f"published via a verified {_norm(source.get('publisher_class'))} "
                          f"publisher account — free tier"}

    # axis 1 — execution / runtime (custom tools + runtime-heavy functions)
    if t in CODE_EXECUTING_TYPES:
        axes["execution"] = "runtime"
        return {"tier": TIER_COMMERCIAL, "basis": "code_executing", "axes": axes,
                "reason": f"code-executing ({t}): custom tool / needs runtime, credentials, sandbox"}

    # content types — RAG databases & dynamic corpora are the commercial moat
    if t in CONTENT_TYPES:
        if _is_rag_database(body):
            axes["execution"] = "retrieval"
            return {"tier": TIER_COMMERCIAL, "basis": "rag_database", "axes": axes,
                    "reason": "verified RAG database — OHH-built retrieval + verification is the value"}
        # NOTE: freshness/dynamic is a DELIVERY axis (billed via access.py — export ships a
        # snapshot, freshness is a subscription), NOT an openness axis. A gov-published
        # dynamic corpus stays OPEN here; its live feed is metered in access.
        # axis 2 — who verified it?
        if externally_verified_public(source):
            axes["provenance"] = "public"
            return {"tier": TIER_OPEN, "basis": "external_public_knowledge", "axes": axes,
                    "reason": f"externally published/verified public knowledge "
                              f"({_host(source.get('source_url', '')) or 'public authority'}, "
                              f"{source.get('license', '')})"}
        axes["provenance"] = "first_party"
        return {"tier": TIER_COMMERCIAL, "basis": "first_party", "axes": axes,
                "reason": f"first-party-verified {t} — OHH curation/verification is the value"}

    # logic / format / eval scaffolding — open (it's framework, not gated content)
    if t in LOGIC_TYPES:
        return {"tier": TIER_OPEN, "basis": "scaffolding", "axes": axes,
                "reason": f"format/logic/eval scaffolding ({t})"}

    return {"tier": TIER_COMMERCIAL, "basis": "default", "axes": axes, "reason": "default: governed content"}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    gov = {"source_url": "https://bsp.gov.ph/circular-1230", "author": "BSP", "license": "CC0-1.0"}
    eu = {"source_url": "https://eur-lex.europa.eu/csddd", "author": "European Union", "license": "CC-BY-4.0"}
    private = {"source_url": "https://acme.example/internal", "author": "Acme Corp", "license": "CC-BY-4.0"}

    def cand(t, body=None, source=None):
        return Candidate(target_type=t, body=body or {}, source=source or {})

    # externally-published public knowledge (gov, public license, non-RAG) → OPEN
    r = classify(cand("knowledge-pack", {"retrieval": ["keyword", "exact_id"]}, gov))
    check("gov-published non-RAG knowledge ⇒ open", r["tier"] == TIER_OPEN, str(r))
    check("provenance axis = public", r["axes"]["provenance"] == "public")

    # EU regulation-derived grep rules (public, non-RAG) → OPEN
    r = classify(cand("rule-pack", {"family": "grep"}, eu))
    check("EU-public grep IfStatement ⇒ open", r["tier"] == TIER_OPEN, str(r))

    # OHH verified RAG database (rag_vector) from a public source → COMMERCIAL (the moat)
    r = classify(cand("knowledge-pack", {"retrieval": ["rag_vector"]}, eu))
    check("verified RAG database ⇒ commercial (even from public source)", r["tier"] == TIER_COMMERCIAL, str(r))
    check("execution axis = retrieval", r["axes"]["execution"] == "retrieval")

    # dense-indexed corpus → commercial
    r = classify(cand("knowledge-pack", {"indexing": {"dense": {"enabled": True}}}, gov))
    check("dense-indexed corpus ⇒ commercial", r["tier"] == TIER_COMMERCIAL)

    # first-party (non-authority) knowledge → commercial
    r = classify(cand("knowledge-pack", {"retrieval": ["keyword"]}, private))
    check("first-party-verified knowledge ⇒ commercial", r["tier"] == TIER_COMMERCIAL, str(r))
    check("provenance axis = first_party", r["axes"]["provenance"] == "first_party")

    # dynamic is a DELIVERY axis (access.py), NOT openness: gov-published dynamic stays OPEN
    # (free content; freshness billed separately); first-party dynamic is commercial.
    r = classify(cand("knowledge-pack", {"retrieval": ["keyword"], "freshness": "volatile"}, gov))
    check("gov-published dynamic ⇒ still open (freshness billed via access)", r["tier"] == TIER_OPEN, str(r))
    r = classify(cand("knowledge-pack", {"retrieval": ["keyword"], "freshness": "volatile"}, private))
    check("first-party dynamic ⇒ commercial", r["tier"] == TIER_COMMERCIAL and r["basis"] == "first_party", str(r))

    # custom tool / runtime-heavy function → commercial
    r = classify(cand("tool", {"side_effects": "external_call"}, gov))
    check("custom tool ⇒ commercial", r["tier"] == TIER_COMMERCIAL)
    check("execution axis = runtime", r["axes"]["execution"] == "runtime")
    check("harness/adapter/pipeline ⇒ commercial",
          all(classify(cand(t))["tier"] == TIER_COMMERCIAL for t in ("harness", "adapter", "pipeline")))

    # logic / format / eval scaffolding → open
    for t in ("processor", "pattern", "persona", "rubric", "benchmark"):
        check(f"{t} (scaffolding) ⇒ open", classify(cand(t))["tier"] == TIER_OPEN)

    # PUBLIC-GOOD carve-out → free, even for a RAG database (overrides the paywall)
    r = classify(cand("knowledge-pack", {"retrieval": ["rag_vector"], "industry": ["anti_human_trafficking"]}, private))
    check("anti-trafficking RAG ⇒ open (public-good free tier)",
          r["tier"] == TIER_OPEN and r["basis"] == "public_good", str(r))
    r = classify(Candidate(target_type="tool", body={"side_effects": "external_call"},
                           gap={"summary": "triage suspected human trafficking reports"}))
    check("public-good tool ⇒ open (overrides runtime)", r["tier"] == TIER_OPEN and r["basis"] == "public_good", str(r))

    # VERIFIED GOV PUBLISHER ACCOUNT → free (published via an OHH gov account)
    r = classify(cand("knowledge-pack", {"retrieval": ["keyword"]},
                      {"source_url": "https://data.example/x", "author": "X", "license": "CC-BY-4.0",
                       "publisher_verified": True, "publisher_class": "government"}))
    check("verified gov publisher account ⇒ open free tier",
          r["tier"] == TIER_OPEN and r["basis"] == "verified_public_publisher", str(r))

    # WEDGE PROTECTED: generic ESG/CSDDD RAG is NOT auto public-good → stays commercial
    r = classify(cand("knowledge-pack", {"retrieval": ["rag_vector"], "industry": ["esg", "supply_chain"]}, eu))
    check("ESG/CSDDD RAG not auto-free ⇒ commercial (wedge protected)",
          r["tier"] == TIER_COMMERCIAL and r["basis"] == "rag_database", str(r))
    check("classify always returns a basis", "basis" in classify(cand("processor")))

    # authority detection across gov TLD shapes
    check("nist.gov is authority", is_public_authority({"source_url": "https://nist.gov/x"}))
    check("gov.uk is authority", is_public_authority({"source_url": "https://www.gov.uk/x"}))
    check("bsp.gov.ph is authority", is_public_authority({"source_url": "https://bsp.gov.ph/x"}))
    check("europa.eu is authority", is_public_authority({"source_url": "https://eur-lex.europa.eu/x"}))
    check("random .com is NOT authority", not is_public_authority({"source_url": "https://acme.com/x"}))
    check("public license requires public terms", is_public_license("CC0-1.0") and not is_public_license("All Rights Reserved"))

    print(f"\n{'all openness self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
