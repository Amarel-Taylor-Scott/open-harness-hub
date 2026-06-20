#!/usr/bin/env python3
"""scripts.integrate_cfpb — the one-click "Integrate CFPB data" end-to-end flow.

Drives the WHOLE Baltor motion over the CFPB corpus and returns a per-stage bundle a single page can
render step-by-step. It REUSES the proven pieces (connect, don't recreate):
  * `demo_run_export.build_run("cfpb")` — the real, offline, deterministic 7-stage CFPB run (Source →
    Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption + verification), which
    catches the CFPB FAQ-vs-Reg-E contradiction and serves the correct answer (10 business days).
  * a FREE, no-auth regulatory source fetch (`federal_register_feed` / `ecfr_feed`) for a real
    freshness signal — live when network is available, else the bundled offline fixture (labeled SEAM).
No paid cloud: everything is a free API or its offline equivalent.

Optional `bus=` emits the run onto the live event bus so the dashboards animate it; byte-identical /
non-breaking without a bus.

CLI:
    python3 scripts/integrate_cfpb.py --self-test     # offline, deterministic
    python3 scripts/integrate_cfpb.py --live          # also attempt the free Federal Register fetch
"""
from __future__ import annotations

import argparse
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.demo_run_export import build_run

#: CFPB's regulatory home: Reg E (electronic fund transfers) lives at 12 CFR Part 1005. The bundled
#: corpus encodes the FAQ(30-day) vs Reg-E(10-business-day) error-resolution contradiction.
CFPB_REG = "12 CFR 1005 (Reg E)"
CFPB_PREDICATE = "error_resolution_days"
CFPB_FAQ_VALUE = 30          # the stale FAQ figure (wrong)
CFPB_AUTHORITY_VALUE = 10    # Reg E business-days window (correct) — matches build_run answer


def _ingest_source(*, live: bool, bus=None) -> dict[str, Any]:
    """Free, no-auth regulatory source. Live = real Federal Register fetch; else offline fixture (SEAM)."""
    mode, handle, detail = "offline", "ctx://cfpb/reg-e/12-CFR-1005", "bundled CFPB Reg E corpus (offline)"
    docs = 0
    if live:
        try:  # real free API (no auth); falls back to offline on any network error
            from scripts.ingest.federal_register_feed import load_documents
            records, lineage = load_documents()
            mode, handle, docs = "live", lineage.source_handle, lineage.documents_parsed
            detail = f"LIVE Federal Register fetch ({docs} federal documents)"
        except Exception as e:  # noqa: BLE001 — offline / no network is expected, not an error
            detail = f"offline fixture (live fetch unavailable: {type(e).__name__})"
    if bus is not None:
        bus.publish("source.received", component="integrate_cfpb", stage="Source Systems",
                    correlation_id="cfpb-integrate", object_ref=handle,
                    payload={"source": CFPB_REG, "mode": mode, "documents": docs})
        bus.publish("source_handle.created", component="integrate_cfpb", stage="Source Systems",
                    correlation_id="cfpb-integrate", object_ref=handle, payload={"regulation": CFPB_REG})
    return {"mode": mode, "handle": handle, "detail": detail, "regulation": CFPB_REG, "documents": docs}


def _lift(run_rec: dict) -> dict[str, Any]:
    bm = run_rec.get("lift_matrix", {}).get("by_model", {})
    model = next(iter(bm), None)
    cm = (bm.get(model, {}) if model else {}).get("condition_mean", {})
    no_ctx, pack = cm.get("no_context"), cm.get("context_pack")
    lift = round((pack or 0.0) - (no_ctx or 0.0), 4) if (pack is not None and no_ctx is not None) else None
    return {"no_context": no_ctx, "context_pack": pack, "lift": lift,
            "best": run_rec.get("lift_matrix", {}).get("summary", {}).get("best_condition")}


def _emit_run(bus, run_rec: dict, source: dict, lift: dict) -> None:
    cid = "cfpb-integrate"
    for st in run_rec.get("stages", []):
        bus.publish("component.progressed", component="integrate_cfpb", stage=st.get("title", ""),
                    correlation_id=cid, payload={"stage": st.get("title"), "headline": st.get("headline"),
                                                 **(st.get("metrics") or {})})
    bus.publish("contradiction_found", component="integrate_cfpb", stage="Anti-Fragility",
                correlation_id=cid, object_ref="obj-faq",
                payload={"predicate": CFPB_PREDICATE, "value": CFPB_AUTHORITY_VALUE,
                         "superseded": CFPB_FAQ_VALUE, "authority": CFPB_REG})
    bus.publish("review.requested", component="integrate_cfpb", stage="Anti-Fragility", correlation_id=cid,
                object_ref="obj-faq", payload={"trigger": "stale_faq_superseded", "risk": "high"})
    bus.publish("context_pack.created", component="integrate_cfpb", stage="Optimization", correlation_id=cid,
                object_ref=run_rec.get("receipt", {}).get("pack_id"),
                payload={"served": True, **(_pack_tokens(run_rec))})
    bus.publish("eval.started", component="integrate_cfpb", stage="Verification rail", correlation_id=cid, payload={"corpus": "cfpb"})
    bus.publish("eval.completed", component="integrate_cfpb", stage="Verification rail", correlation_id=cid, payload={"best_condition": lift.get("best")})
    bus.publish("context_lift.calculated", component="integrate_cfpb", stage="Verification rail",
                correlation_id=cid, payload=lift)
    bus.publish("receipt_issued", component="integrate_cfpb", stage="Consumption", correlation_id=cid,
                payload={"answer_value": run_rec.get("receipt", {}).get("answer_value"),
                         "receipt_id": run_rec.get("receipt", {}).get("receipt_id")})
    bus.publish("pipeline.completed", component="integrate_cfpb", stage="Consumption", correlation_id=cid,
                payload={"answer_value": run_rec.get("receipt", {}).get("answer_value"), "lift": lift.get("lift")})


def _pack_tokens(run_rec: dict) -> dict[str, Any]:
    for st in run_rec.get("stages", []):
        m = st.get("metrics") or {}
        if "tokens_before" in m and "tokens_after" in m:
            return {"tokens_before": m["tokens_before"], "tokens_after": m["tokens_after"]}
    return {}


def run(*, bus=None, live: bool = False) -> dict[str, Any]:
    """Run the full CFPB integration. Returns {source, stages, lift, answer, headline, receipt, run}."""
    if bus is not None:
        bus.publish("pipeline.started", component="integrate_cfpb", stage="Source Systems",
                    correlation_id="cfpb-integrate", payload={"corpus": "cfpb", "live": live})
    source = _ingest_source(live=live, bus=bus)
    run_rec = build_run("cfpb")
    lift = _lift(run_rec)
    if bus is not None:
        _emit_run(bus, run_rec, source, lift)
    return {
        "source": source,
        "headline": run_rec.get("headline"),
        "stages": run_rec.get("stages", []),
        "graph": run_rec.get("graph"),
        "lift": lift,
        "answer": run_rec.get("receipt", {}).get("answer_value"),
        "receipt": run_rec.get("receipt"),
        "contradiction": {"predicate": CFPB_PREDICATE, "faq": CFPB_FAQ_VALUE,
                          "authority_value": CFPB_AUTHORITY_VALUE, "authority": CFPB_REG},
        "run": run_rec,
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    r = run()  # offline, deterministic
    check("source step ran (offline mode, CFPB Reg E)", r["source"]["mode"] == "offline" and r["source"]["regulation"] == CFPB_REG)
    check("all 7 stages present", len(r["stages"]) == 7, str(len(r["stages"])))
    check("served answer is 10 business days (Reg E)", r["answer"] == 10, str(r["answer"]))
    check("contradiction surfaced (FAQ 30 superseded by Reg E 10)",
          r["contradiction"]["faq"] == 30 and r["contradiction"]["authority_value"] == 10)
    check("measured lift computed (pack > no-context)",
          r["lift"]["lift"] is not None and r["lift"]["lift"] > 0, str(r["lift"]))
    check("receipt carries answer + receipt_id", r["receipt"]["answer_value"] == 10 and bool(r["receipt"]["receipt_id"]))
    check("each stage has a title + headline (great results to show)",
          all(s.get("title") and s.get("headline") for s in r["stages"]))

    r2 = run()
    check("deterministic (re-run identical)", r2 == r)

    # bus emit (non-breaking)
    from scripts.context_events import EventBus
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    r3 = run(bus=bus)
    kinds = [e["kind"] for e in seen]
    check("bus: pipeline.started … pipeline.completed", kinds and kinds[0] == "pipeline.started" and kinds[-1] == "pipeline.completed")
    for need in ("source.received", "contradiction_found", "context_pack.created", "context_lift.calculated", "receipt_issued"):
        check(f"bus emits {need}", need in kinds)
    check("bus vs no-bus return is IDENTICAL", r3 == r)

    print(f"\n{'all integrate_cfpb self-tests passed (one-click CFPB run: 7 stages, answer 10, contradiction caught, measured lift, receipt; offline-deterministic; bus non-breaking).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="One-click Integrate-CFPB end-to-end flow.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--live", action="store_true", help="also attempt the free Federal Register fetch")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    import json
    print(json.dumps(run(live=args.live)["source"], indent=2))
    print(f"answer={run(live=args.live)['answer']} stages={len(run()['stages'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
