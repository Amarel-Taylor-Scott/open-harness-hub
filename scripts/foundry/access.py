#!/usr/bin/env python3
"""Foundry access — how a component is DELIVERED and BILLED (the recurring-revenue layer).

`openness.py` answers *is it free or commercial*. This answers *how do you get it, and
what's metered* — the mechanisms that survive an export (the live demo measured a **+1.0
lift from a fresh fact** the bare model got wrong, which is exactly what an export
loses). Four delivery modes, computed from execution-class + dynamic-corpus + the
openness tier:

  - **frozen_export** — fully bundled; free; works offline forever (a static snapshot).
  - **live_subscription** — the export ships a *dated snapshot*; staying current
    (re-scrape + CDC + revocation, with full date + provenance) is a subscription. This
    is the "updated knowledge facts from verified sources" value — freshness, not shape.
  - **credentialed_data** — the flow + schema export, but querying the **verified data**
    (RAG databases / curated corpora) needs a billed credential to the hosted corpus.
  - **hosted_endpoint** — runs on our servers (managed processing / proxy to a model
    API); metered per call; or self-host with your own keys.

Billable events accumulate across these (``refresh`` for any dynamic corpus — the
freshness feed is a service even for *free* gov facts; ``data_query`` only when the data
itself is gated; ``hosted_call`` for code-executing). stdlib-only.

Run ``python -m scripts.foundry.access`` for the offline self-test.
"""
from __future__ import annotations

from typing import Any

from scripts.foundry.contracts import Candidate
from scripts.foundry.openness import (
    CODE_EXECUTING_TYPES,
    CONTENT_TYPES,
    TIER_COMMERCIAL,
    classify as classify_openness,
)

DELIVERY_FROZEN = "frozen_export"
DELIVERY_LIVE = "live_subscription"
DELIVERY_CREDENTIALED = "credentialed_data"
DELIVERY_HOSTED = "hosted_endpoint"

# billable event keys (metering ledger uses these)
EVENT_REFRESH = "refresh"          # keep a dynamic corpus current (re-scrape + CDC)
EVENT_DATA_QUERY = "data_query"    # read gated verified data from the hosted corpus
EVENT_HOSTED_CALL = "hosted_call"  # run a code-executing component on our servers

_EXPORT_NOTE = {
    DELIVERY_FROZEN: "Fully bundled in the export — free, works offline forever (a static snapshot).",
    DELIVERY_LIVE: "Export ships a DATED snapshot; staying current (re-scrape + CDC + revocation, with "
                   "full date + provenance) is a subscription — the value is freshness, not the shape.",
    DELIVERY_CREDENTIALED: "The flow + schema export, but querying the verified data needs a billed "
                           "credential to the hosted corpus (metered per query).",
    DELIVERY_HOSTED: "Runs on our servers (managed processing / API proxy), metered per call — or "
                     "self-host with your own keys (adds the credential to your workflow).",
}


def classify_access(candidate: Candidate) -> dict[str, Any]:
    """Return {delivery, billable_events, openness, export, why} for a promoted component."""
    t = candidate.target_type
    body = candidate.body or {}
    tier = classify_openness(candidate)["tier"]

    is_code = t in CODE_EXECUTING_TYPES
    is_content = t in CONTENT_TYPES
    is_dynamic = body.get("freshness") == "volatile"
    data_gated = is_content and tier == TIER_COMMERCIAL

    billable: list[str] = []
    if is_code:
        billable.append(EVENT_HOSTED_CALL)
    if is_dynamic:
        billable.append(EVENT_REFRESH)        # freshness feed is a service even for FREE gov facts
    if data_gated:
        billable.append(EVENT_DATA_QUERY)     # the verified data itself is the moat

    if is_code:
        delivery, why = DELIVERY_HOSTED, "code-executing — runs server-side or self-hosted with creds"
    elif is_dynamic:
        delivery, why = DELIVERY_LIVE, "dynamic corpus — the export goes stale; freshness is the recurring value"
    elif data_gated:
        delivery, why = DELIVERY_CREDENTIALED, "verified data is gated — the flow exports, the data is metered"
    else:
        delivery, why = DELIVERY_FROZEN, "static + open — fully exportable, nothing to meter"

    return {"delivery": delivery, "billable_events": billable, "openness": tier,
            "export": _EXPORT_NOTE[delivery], "why": why}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    gov = {"source_url": "https://bsp.gov.ph/x", "author": "BSP", "license": "CC0-1.0"}
    eu = {"source_url": "https://eur-lex.europa.eu/x", "author": "EU", "license": "CC-BY-4.0"}
    private = {"source_url": "https://acme.com/x", "author": "Acme", "license": "CC-BY-4.0"}

    def c(t, body=None, source=None):
        return Candidate(target_type=t, body=body or {}, source=source or {})

    # open static scaffolding → frozen, nothing metered
    r = classify_access(c("processor"))
    check("static scaffolding ⇒ frozen_export, no billing", r["delivery"] == DELIVERY_FROZEN and not r["billable_events"], str(r))

    # FREE gov fact, but DYNAMIC ⇒ live_subscription (snapshot free, freshness metered)
    r = classify_access(c("knowledge-pack", {"retrieval": ["keyword"], "freshness": "volatile"}, gov))
    check("free dynamic gov corpus ⇒ live_subscription", r["delivery"] == DELIVERY_LIVE, str(r))
    check("free dynamic ⇒ refresh metered, NOT data_query", r["billable_events"] == [EVENT_REFRESH], str(r))
    check("free dynamic stays open tier", r["openness"] == "open")

    # commercial static RAG ⇒ credentialed_data (data metered)
    r = classify_access(c("knowledge-pack", {"retrieval": ["rag_vector"]}, eu))
    check("commercial RAG ⇒ credentialed_data", r["delivery"] == DELIVERY_CREDENTIALED, str(r))
    check("commercial RAG ⇒ data_query metered", r["billable_events"] == [EVENT_DATA_QUERY], str(r))

    # commercial DYNAMIC RAG ⇒ live_subscription + both refresh & data_query
    r = classify_access(c("knowledge-pack", {"retrieval": ["rag_vector"], "freshness": "volatile"}, private))
    check("commercial dynamic RAG ⇒ live_subscription", r["delivery"] == DELIVERY_LIVE, str(r))
    check("commercial dynamic ⇒ refresh + data_query", set(r["billable_events"]) == {EVENT_REFRESH, EVENT_DATA_QUERY}, str(r))

    # code-executing tool ⇒ hosted_endpoint, hosted_call metered
    r = classify_access(c("tool", {"side_effects": "external_call"}, private))
    check("custom tool ⇒ hosted_endpoint", r["delivery"] == DELIVERY_HOSTED and r["billable_events"] == [EVENT_HOSTED_CALL], str(r))

    # public-good corpus (free) static ⇒ frozen + exportable (mission carve-out wins openness, free to export)
    r = classify_access(c("knowledge-pack", {"retrieval": ["keyword"], "industry": ["anti_human_trafficking"]}, private))
    check("public-good static ⇒ frozen_export (free)", r["delivery"] == DELIVERY_FROZEN and r["openness"] == "open", str(r))

    # every delivery mode has an export note
    check("every delivery has an export note", all(d in _EXPORT_NOTE for d in
          (DELIVERY_FROZEN, DELIVERY_LIVE, DELIVERY_CREDENTIALED, DELIVERY_HOSTED)))

    print(f"\n{'all access self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
