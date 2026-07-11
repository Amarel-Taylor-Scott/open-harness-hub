#!/usr/bin/env python3
"""scripts.check_event_integration — proof that a real engine emits real events onto the bus.

The first "is it actually CONNECTED?" test: run `context_graph.interrogate` over the demo graph WITH
an EventBus and assert it emits the expected ordered lifecycle sequence (started → contradiction_found
→ finished), all sharing one correlation id — AND that passing no bus is non-breaking (identical
return, zero events). Fully offline + deterministic.

CLI:
    python3 _repos/shared-backend-components/scripts/check_event_integration.py --self-test
"""
from __future__ import annotations

import argparse

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.context_compress import compress
from scripts.context_events import EventBus
from scripts.context_graph import ContextGraph, interrogate, load_seed
from scripts.context_swarm import swarm_object
from scripts.foundry.scrapers import CannedFetcher
from scripts.ingest.sanctions_feed_live import (
    LIVE_SANCTIONS_SOURCES, POSITIONAL_CSV_SOURCE, _FIXTURE_SDN_CSV, fetch_live_records,
)
from scripts.ingest.ecfr_feed import ECFR_TITLES_URL as _ECFR_URL, _FIXTURE as _ECFR_FIXTURE, load_titles
from scripts.ingest.federal_register_feed import FR_DOCS_URL as _FR_URL, _FIXTURE as _FR_FIXTURE, load_documents
from scripts.context_diff import diff_text
from scripts.context_memory_block import build_memory_block
from scripts.pipeline.verified_context_flow import (
    DEMO_INTERNAL_CLAIMS, DEMO_SOURCE_RECORDS, run as run_verified_context_flow,
)
from scripts.source_expansion import expand_source_handle

_Q = "What is the retry ceiling / how many retries are allowed?"


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    g = ContextGraph(load_seed())
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    run = interrogate(g, _Q, bus=bus)

    kinds = [e["kind"] for e in seen]
    check("interrogation emitted events onto the bus", len(seen) >= 3, str(len(seen)))
    check("first event is component.started", kinds[0] == "component.started", kinds[0] if kinds else "none")
    check("last event is component.finished", kinds[-1] == "component.finished", kinds[-1] if kinds else "none")
    check("a contradiction_found event fired (the 5-vs-3 conflict)", "contradiction_found" in kinds)
    cf = next((e for e in seen if e["kind"] == "contradiction_found"), None)
    check("contradiction_found carries predicate=max_retries, value=5",
          cf and cf["payload"].get("predicate") == "max_retries" and cf["payload"].get("value") == 5)
    cids = {e["correlation_id"] for e in seen}
    check("all events share ONE correlation id", len(cids) == 1, str(cids))
    check("finished payload carries the answer_value 5", seen[-1]["payload"].get("answer_value") == 5)

    # NON-BREAKING: without a bus → zero events + identical return value
    bus2 = EventBus()
    none_seen: list[dict] = []
    bus2.subscribe(none_seen.append)
    run_nobus = interrogate(ContextGraph(load_seed()), _Q)  # no bus
    check("no bus → engine still answers 5", run_nobus["answer_value"] == 5)
    check("bus vs no-bus return value is IDENTICAL (events are side-effects only)", run == run_nobus)

    # ── context_swarm emits per-agent events natively ──
    sbus = EventBus()
    sseen: list[dict] = []
    sbus.subscribe(sseen.append)
    g2 = ContextGraph(load_seed())
    sw = swarm_object(g2, "obj-runbook", bus=sbus)
    skinds = [e["kind"] for e in sseen]
    check("swarm emitted events onto the bus", len(sseen) >= 5, str(len(sseen)))
    check("swarm first event is swarm.started", skinds[0] == "swarm.started" if skinds else False)
    check("swarm emitted >=3 swarm.agent.completed (one per bounded agent)",
          skinds.count("swarm.agent.completed") >= 3, str(skinds.count("swarm.agent.completed")))
    check("swarm last event is swarm.consensus.created", skinds[-1] == "swarm.consensus.created" if skinds else False)
    check("swarm.agent.completed carries agent + max_severity",
          all(("agent" in e["payload"] and "max_severity" in e["payload"]) for e in sseen if e["kind"] == "swarm.agent.completed"))
    check("swarm.consensus.created reports the high risk + proposed fix",
          any(e["payload"].get("risk_level") == "high" and e["payload"].get("proposed_fix") == "3→5" for e in sseen if e["kind"] == "swarm.consensus.created"))
    # non-breaking: no-bus swarm returns identical
    sw_nobus = swarm_object(ContextGraph(load_seed()), "obj-runbook")
    check("swarm bus vs no-bus return is IDENTICAL (events are side-effects)", sw == sw_nobus)
    check("swarm did not mutate canonical state", sw["canonical_mutated"] is False)

    # ── context_compress emits per-ladder-step events natively ──
    _items = [{"ref": "a", "text": "ADR-014: at most 5 retries with full-jitter backoff. Authoritative.", "source_handle": "ctx://acme-billing/decisions/ADR-014-billing-retry-policy.md#decision"},
              {"ref": "b", "text": "The payment-submit client retries up to 3 times.", "source_handle": "ctx://acme-billing/docs/billing-runbook.md#retry-policy"},
              {"ref": "c", "text": "billing-service is owned by billing-team.", "source_handle": "ctx://acme-billing/org/OWNERS.md#billing-team"}]
    cbus = EventBus()
    cseen: list[dict] = []
    cbus.subscribe(cseen.append)
    comp = compress(_items, query="retry ceiling retries", max_tokens=256, bus=cbus)
    ckinds = [e["kind"] for e in cseen]
    check("compress first event is component.started", ckinds and ckinds[0] == "component.started")
    check("compress emitted >=3 component.progressed (ladder steps)", ckinds.count("component.progressed") >= 3, str(ckinds.count("component.progressed")))
    check("compress last event is context_pack.created", ckinds and ckinds[-1] == "context_pack.created")
    pk = next((e for e in cseen if e["kind"] == "context_pack.created"), None)
    check("context_pack.created reports token reduction (after <= before)",
          pk and pk["payload"]["tokens_after"] <= pk["payload"]["tokens_before"])
    comp_nobus = compress(_items, query="retry ceiling retries", max_tokens=256)
    check("compress bus vs no-bus return is IDENTICAL", comp == comp_nobus)

    # ── source_expansion emits allowed / denied events natively ──
    _adr = "ctx://acme-billing/decisions/ADR-014-billing-retry-policy.md#decision"
    ebus = EventBus()
    eseen: list[dict] = []
    ebus.subscribe(eseen.append)
    allow = expand_source_handle(_adr, classification="internal", bus=ebus)
    deny = expand_source_handle(_adr, classification="regulated", bus=ebus)  # restricted → denied
    ekinds = [e["kind"] for e in eseen]
    check("allowed expansion emits source_handle.expanded", "source_handle.expanded" in ekinds)
    check("denied expansion emits a component.progressed with denied_reason + NO raw",
          any(e["kind"] == "component.progressed" and e["payload"].get("denied_reason") for e in eseen)
          and deny.get("raw_excerpt") is None)
    check("expansion bus vs no-bus return is IDENTICAL", allow == expand_source_handle(_adr, classification="internal"))

    # ── ingest connector (sanctions_feed_live) emits Source Systems events (offline CannedFetcher) ──
    fetcher = CannedFetcher({LIVE_SANCTIONS_SOURCES[POSITIONAL_CSV_SOURCE]["url"]: _FIXTURE_SDN_CSV})
    ibus = EventBus()
    iseen: list[dict] = []
    ibus.subscribe(iseen.append)
    recs, lin = fetch_live_records(POSITIONAL_CSV_SOURCE, fetcher=fetcher, bus=ibus)
    ikinds = [e["kind"] for e in iseen]
    check("connector emits source.received", "source.received" in ikinds)
    check("connector emits source_handle.created (ctx://ofac/sdn)",
          any(e["kind"] == "source_handle.created" and e["object_ref"] == lin.source_handle for e in iseen))
    recs2, lin2 = fetch_live_records(POSITIONAL_CSV_SOURCE, fetcher=fetcher)  # no bus
    check("connector bus vs no-bus result is IDENTICAL", recs == recs2 and lin == lin2)

    # ── ecfr_feed connector emits Source Systems events (offline CannedFetcher) ──
    efetcher = CannedFetcher({_ECFR_URL: _ECFR_FIXTURE})
    ebus2 = EventBus()
    e2seen: list[dict] = []
    ebus2.subscribe(e2seen.append)
    erecs, elin = load_titles(fetcher=efetcher, bus=ebus2)
    e2kinds = [e["kind"] for e in e2seen]
    check("ecfr_feed emits source.received + source_handle.created",
          "source.received" in e2kinds and "source_handle.created" in e2kinds)
    erecs2, elin2 = load_titles(fetcher=efetcher)  # no bus
    check("ecfr_feed bus vs no-bus result is IDENTICAL", erecs == erecs2 and elin == elin2)

    # ── federal_register_feed connector emits Source Systems events (offline CannedFetcher) ──
    frfetcher = CannedFetcher({_FR_URL: _FR_FIXTURE})
    fbus = EventBus()
    fseen: list[dict] = []
    fbus.subscribe(fseen.append)
    frecs, flin = load_documents(fetcher=frfetcher, bus=fbus)
    fkinds = [e["kind"] for e in fseen]
    check("federal_register_feed emits source.received + source_handle.created",
          "source.received" in fkinds and "source_handle.created" in fkinds)
    frecs2, flin2 = load_documents(fetcher=frfetcher)  # no bus
    check("federal_register_feed bus vs no-bus result is IDENTICAL", frecs == frecs2 and flin == flin2)

    # ── verified_context_flow (the end-to-end ingest→assure→serve flow) emits Source + Verification-rail + Consumption events ──
    vbus = EventBus()
    vseen: list[dict] = []
    vbus.subscribe(vseen.append)
    vbundle = run_verified_context_flow(DEMO_SOURCE_RECORDS, DEMO_INTERNAL_CLAIMS, bus=vbus)
    vkinds = [e["kind"] for e in vseen]
    check("verified_context_flow emits source.received", "source.received" in vkinds)
    check("verified_context_flow emits verification.started + verification.completed",
          "verification.started" in vkinds and "verification.completed" in vkinds)
    check("verified_context_flow emits context_pack.created (the served corpus)", "context_pack.created" in vkinds)
    check("verification.completed reports served + held_out counts",
          any(e["kind"] == "verification.completed" and "served" in e["payload"] and "held_out" in e["payload"]
              for e in vseen))
    check("verified_context_flow event order: source.received < verification.started < verification.completed < context_pack.created",
          all(k in vkinds for k in ("source.received", "verification.started", "verification.completed", "context_pack.created"))
          and vkinds.index("source.received") < vkinds.index("verification.started")
          < vkinds.index("verification.completed") < vkinds.index("context_pack.created"))
    vcids = {e["correlation_id"] for e in vseen}
    check("verified_context_flow events share ONE correlation id", len(vcids) == 1, str(vcids))
    vbundle_nobus = run_verified_context_flow(DEMO_SOURCE_RECORDS, DEMO_INTERNAL_CLAIMS)  # no bus
    check("verified_context_flow bus vs no-bus return is IDENTICAL (events are side-effects only)",
          vbundle == vbundle_nobus)

    # ── context_memory_block (anti-drift reconciliation) emits Reconciliation + Consumption events ──
    _decs = [{"decision_id": "d1", "key": "max_retries", "value": 3},
             {"decision_id": "d3", "key": "max_retries", "value": 5, "supersedes": "d1"}]
    mbus = EventBus()
    mseen: list[dict] = []
    mbus.subscribe(mseen.append)
    mb = build_memory_block(_decs, bus=mbus)
    mkinds = [e["kind"] for e in mseen]
    check("context_memory_block emits component.started…finished",
          bool(mkinds) and mkinds[0] == "component.started" and mkinds[-1] == "component.finished")
    check("context_memory_block emits a supersedes relationship.created (d3→d1)",
          any(e["kind"] == "relationship.created" and e["object_ref"] == "d3"
              and e["payload"].get("object") == "d1" for e in mseen))
    check("context_memory_block emits context_pack.created (the pinned block)", "context_pack.created" in mkinds)
    check("context_memory_block pins the latest decision (max_retries=5)", mb["pinned"]["max_retries"] == 5)
    check("context_memory_block bus vs no-bus return is IDENTICAL", mb == build_memory_block(_decs))

    # ── context_diff (rewrite change-report) emits Verification-rail + Consumption events ──
    dbus = EventBus()
    dseen: list[dict] = []
    dbus.subscribe(dseen.append)
    drep = diff_text("Block all 5 transactions on 2026-05-28 for Northwind.",
                     "Block the transactions for Northwind and add 9 checks.", protect=["Northwind"], bus=dbus)
    dkinds = [e["kind"] for e in dseen]
    check("context_diff emits component.started…finished",
          bool(dkinds) and dkinds[0] == "component.started" and dkinds[-1] == "component.finished")
    check("context_diff emits a risk as component.progressed (number dropped)",
          any(e["kind"] == "component.progressed" and e["payload"].get("risk_flag") for e in dseen))
    check("context_diff emits context_pack.created (the change-report)", "context_pack.created" in dkinds)
    check("context_diff flags the dropped figure (5) as high risk",
          any(f["flag"] == "number_dropped_or_changed" and f["severity"] == "high" for f in drep["risk_flags"]))
    check("context_diff bus vs no-bus return is IDENTICAL",
          drep == diff_text("Block all 5 transactions on 2026-05-28 for Northwind.",
                            "Block the transactions for Northwind and add 9 checks.", protect=["Northwind"]))

    print(f"\n{'PASS — check_event_integration: context_graph + context_swarm + context_compress emit real ordered events onto the bus (graph: started→contradiction→finished; swarm: started→agent.completed×N→consensus; compress: started→progressed×N→pack.created), all byte-identical/non-breaking without a bus. + source_expansion emits allowed/denied + sanctions_feed_live, ecfr_feed & federal_register_feed emit Source Systems events + verified_context_flow emits source.received→verification.started→verification.completed→context_pack.created + context_memory_block emits started→relationship.created(supersedes)→context_pack.created→finished + context_diff emits started→progressed(risk)→context_pack.created→finished. Ten modules CONNECTED.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prove a real engine emits real events onto the bus.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
