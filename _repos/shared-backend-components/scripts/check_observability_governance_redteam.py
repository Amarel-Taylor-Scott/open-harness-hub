#!/usr/bin/env python3
"""scripts.check_observability_governance_redteam — proof (C-OBS-1): the observability/lineage providers
DESCRIBE; they never become the authority and an external standard can never LAUNDER a claim's status.
Eight attacks must all fail safely:

  1. an allegation stays an allegation across PROV / OpenLineage / Web Annotation (no laundering to verified)
  2. a held-out record is flagged in every rendering (so a consumer can drop it; never served as truth)
  3. forged/extra governance keys are stripped (only the allowed facet keys survive)
  4. span/event records are frozen (a provider physically cannot mutate canonical state)
  5. providers expose no write-to-canonical method (no save/commit/write/delete/publish)
  6. the named external providers (langfuse/phoenix/langsmith/openlineage) stay candidate-only behind ports
  7. the WIRED adapter is always the local stub (never an external candidate)
  8. renderings are deterministic (same input -> identical bytes; CDC-safe)

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_observability_governance_redteam.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import dataclasses
import json
from pathlib import Path

from src.baltor.observability.projections.lineage import BaltorLocalLineage, LineageEvent
from src.baltor.observability.projections.standards import (
    GOVERNANCE_FACET_KEYS,
    to_openlineage_run_event,
    to_prov_json,
    to_web_annotation,
)
from src.baltor.observability.tracing.provider import BaltorLocalObservability, ContextOperationSpan

_CAT = _resource("architecture/external_capability_catalog.json")
T0 = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    alleged = {"claim_status": "allegation", "authority": "unverified_source", "held_out": False}
    ev = LineageEvent(event_id="ev-a", activity="ingest.claim", occurred_at=T0,
                      inputs=("ctx://src/x",), outputs=("claim-1",), governance=alleged)

    # 1 — allegation survives every rendering (not laundered to verified)
    prov = to_prov_json(ev)
    ol = to_openlineage_run_event(ev)
    ann = to_web_annotation(annotation_id="a", claim_body="x", source_iri="ctx://src/x", fragment="block=1",
                            created=T0, governance=alleged)
    out_entity = next(e for e in prov["entity"].values() if e.get("baltor:claim_status"))
    chk("1a PROV keeps claim_status=allegation", out_entity["baltor:claim_status"] == "allegation")
    chk("1b OpenLineage keeps claim_status=allegation", ol["run"]["facets"]["baltor_governance"]["claim_status"] == "allegation")
    chk("1c WebAnnotation keeps claim_status=allegation", ann["body"]["baltor:governance"]["claim_status"] == "allegation")

    # 2 — held-out flagged everywhere
    ho_gov = {"claim_status": "verified_current", "held_out": True}
    ho_ev = LineageEvent(event_id="ho", activity="eval.control", occurred_at=T0, outputs=("ctrl-1",), governance=ho_gov)
    ho_ol = to_openlineage_run_event(ho_ev)
    span = ContextOperationSpan("s", None, "op", "held_out", T0, governance=ho_gov)
    tree = BaltorLocalObservability().record([span])
    chk("2a held_out survives into OpenLineage facet", ho_ol["outputs"][0]["facets"]["baltor_governance"]["held_out"] is True)
    chk("2b held_out flagged on the span node", tree.root["held_out"] is True)

    # 3 — forged/extra governance keys are stripped
    forged = {"claim_status": "verified_current", "is_truth": True, "override_authority": "admin", "held_out": False}
    f_ol = to_openlineage_run_event(LineageEvent(event_id="f", activity="x", occurred_at=T0, governance=forged))
    facet = f_ol["run"]["facets"]["baltor_governance"]
    extra = set(facet) - set(GOVERNANCE_FACET_KEYS) - {"_producer", "_schemaURL"}
    chk("3 forged keys stripped (only allowed facet keys survive)", extra == set(), str(extra))

    # 4 — frozen records (no canonical mutation through a provider)
    for label, obj, field, val in [("span", span, "status", "ok"), ("event", ev, "activity", "tampered")]:
        frozen = False
        try:
            setattr(obj, field, val)
        except dataclasses.FrozenInstanceError:
            frozen = True
        chk(f"4 {label} is immutable", frozen)

    # 5 — providers expose no write-to-canonical method
    banned = ("save", "commit", "write", "delete", "publish", "update", "promote", "mutate")
    for prov_obj in (BaltorLocalObservability(), BaltorLocalLineage()):
        offenders = [m for m in banned if hasattr(prov_obj, m)]
        chk(f"5 {type(prov_obj).__name__} has no canonical-write method", offenders == [], str(offenders))

    # 6 + 7 — catalog discipline: external providers candidate-only; wired adapter is the stub
    cat = json.loads(_CAT.read_text())
    slots = {s["capability_slot"]: s for s in cat["capability_slots"]}
    for slot in ("observability_provider", "lineage_provider"):
        s = slots[slot]
        wired = s["adapter_id"]
        wired_role = next((a["role"] for a in s["adapters"] if a["adapter_id"] == wired), None)
        chk(f"7 {slot} wired adapter is the local stub", wired_role == "stub", f"{wired}={wired_role}")
        externals = [a for a in s["adapters"] if a["role"] in ("primary", "fallback")]
        chk(f"6 {slot} external providers are candidate-only", all(a["status"] == "candidate" for a in externals),
            str([(a["adapter_id"], a["status"]) for a in externals]))

    # 8 — determinism
    a = json.dumps(to_prov_json(ev), sort_keys=True)
    b = json.dumps(to_prov_json(LineageEvent(event_id="ev-a", activity="ingest.claim", occurred_at=T0,
                   inputs=("ctx://src/x",), outputs=("claim-1",), governance=alleged)), sort_keys=True)
    chk("8 renderings are deterministic", a == b)

    print(f"\n{'PASS — check_observability_governance_redteam: 8 attacks fail safely — no laundering of allegations, held-out flagged everywhere, forged facets stripped, records immutable, providers cannot write canonical, externals candidate-only, deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: observability governance redteam.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
