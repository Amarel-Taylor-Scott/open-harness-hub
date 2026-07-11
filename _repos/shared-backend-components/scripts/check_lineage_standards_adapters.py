#!/usr/bin/env python3
"""scripts.check_lineage_standards_adapters — proof (C-OBS-1): Baltor renders lineage/claims into the
four adopted interchange standards and each rendering is conformant, deterministic, and carries Baltor
governance facets so the receipt is PORTABLE:

  * W3C PROV-JSON       — prefix + entity/activity/agent + used/wasGeneratedBy/wasAttributedTo/wasDerivedFrom
  * OpenLineage RunEvent — eventType/eventTime/producer/run/job/inputs/outputs + baltor_governance facet
  * W3C Web Annotation   — @context/type/body/target+selector (FragmentSelector for ctx:// handles)
  * RFC 6902 JSON Patch  — add/remove/replace ops with RFC6901 pointer escaping

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_lineage_standards_adapters.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.observability.projections.lineage import BaltorLocalLineage, LineageEvent, LineageProvider
from src.baltor.observability.projections.standards import (
    OPENLINEAGE_SCHEMA_URL,
    WEB_ANNOTATION_CONTEXT,
    canonical_hash,
    to_json_patch,
    to_openlineage_run_event,
    to_prov_json,
    to_web_annotation,
)

T0 = "2026-06-06T00:00:00Z"
GOV = {"authority": "deterministic_reconciliation", "claim_status": "verified_current",
       "receipt_id": "rcpt-abc", "held_out": False, "verified_current": True}


def _event() -> LineageEvent:
    return LineageEvent(event_id="ev-1", activity="reconciliation.resolve", occurred_at=T0,
                        inputs=("ctx://acme/adr-014", "ctx://acme/runbook"), outputs=("pack-bill-782",),
                        agent="baltor.deterministic_reconciliation", governance=GOV)


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ev = _event()

    # ── PROV-JSON ──
    prov = to_prov_json(ev)
    chk("PROV: declares prefix (baltor + prov)", "prefix" in prov and "baltor" in prov["prefix"] and "prov" in prov["prefix"])
    chk("PROV: has all core relations", all(k in prov for k in ("entity", "activity", "agent", "used", "wasGeneratedBy", "wasAttributedTo", "wasDerivedFrom")))
    chk("PROV: one used per input", len(prov["used"]) == 2, str(len(prov["used"])))
    chk("PROV: one wasGeneratedBy per output", len(prov["wasGeneratedBy"]) == 1)
    chk("PROV: derivation links each output to each input", len(prov["wasDerivedFrom"]) == 2)
    out_entity = next(e for e in prov["entity"].values() if e.get("baltor:authority"))
    chk("PROV: governance facets on output entity", out_entity.get("baltor:authority") == GOV["authority"] and out_entity.get("baltor:receipt_id") == "rcpt-abc")

    # ── OpenLineage ──
    ol = to_openlineage_run_event(ev)
    chk("OL: required RunEvent fields", all(k in ol for k in ("eventType", "eventTime", "producer", "schemaURL", "run", "job", "inputs", "outputs")))
    chk("OL: eventType default COMPLETE", ol["eventType"] == "COMPLETE")
    chk("OL: schemaURL points at OpenLineage spec", ol["schemaURL"] == OPENLINEAGE_SCHEMA_URL)
    chk("OL: runId is UUID-shaped", len(ol["run"]["runId"]) == 36 and ol["run"]["runId"].count("-") == 4)
    chk("OL: run + output carry baltor_governance facet", ol["run"]["facets"]["baltor_governance"]["authority"] == GOV["authority"] and ol["outputs"][0]["facets"]["baltor_governance"]["receipt_id"] == "rcpt-abc")
    chk("OL: governance facet declares _producer + _schemaURL", "_producer" in ol["run"]["facets"]["baltor_governance"] and "_schemaURL" in ol["run"]["facets"]["baltor_governance"])
    chk("OL: START variant supported", to_openlineage_run_event(ev, event_type="START")["eventType"] == "START")

    # ── Web Annotation ──
    ann = to_web_annotation(annotation_id="anno-1", claim_body="max_retries = 5", source_iri="ctx://acme/adr-014",
                            fragment="page=3&block=7", created=T0, governance={"claim_status": "allegation"},
                            quote="max_retries: 5")
    chk("WA: @context is W3C anno", ann["@context"] == WEB_ANNOTATION_CONTEXT)
    chk("WA: type Annotation", ann["type"] == "Annotation")
    chk("WA: FragmentSelector carries the ctx:// fragment", ann["target"]["selector"][0]["type"] == "FragmentSelector" and ann["target"]["selector"][0]["value"] == "page=3&block=7")
    chk("WA: TextQuoteSelector when quote given", any(s["type"] == "TextQuoteSelector" and s["exact"] == "max_retries: 5" for s in ann["target"]["selector"]))
    chk("WA: governance rides on the body", ann["body"]["baltor:governance"]["claim_status"] == "allegation")

    # ── JSON Patch (RFC 6902) ──
    patch = to_json_patch(before={"max_retries": 3, "removed": 1, "kept": "x"},
                          after={"max_retries": 5, "added": 9, "kept": "x"},
                          governance=GOV, from_version="v1", to_version="v2")
    ops = patch["patch"]
    chk("JP: replace for changed key", {"op": "replace", "path": "/max_retries", "value": 5} in ops)
    chk("JP: remove for dropped key", {"op": "remove", "path": "/removed"} in ops)
    chk("JP: add for new key", {"op": "add", "path": "/added", "value": 9} in ops)
    chk("JP: unchanged key produces no op", all("/kept" != o["path"] for o in ops))
    chk("JP: carries from/to version + governance", patch["from_version"] == "v1" and patch["governance"]["authority"] == GOV["authority"])
    # RFC6901 escaping
    esc = to_json_patch(before={}, after={"a/b~c": 1}, governance={})["patch"]
    chk("JP: RFC6901 pointer escaping (~1, ~0)", esc[0]["path"] == "/a~1b~0c", esc[0]["path"])

    # ── Determinism ──
    chk("PROV deterministic", canonical_hash(to_prov_json(ev)) == canonical_hash(to_prov_json(_event())))
    chk("OL deterministic", canonical_hash(to_openlineage_run_event(ev)) == canonical_hash(to_openlineage_run_event(_event())))

    # ── Provider seam wiring ──
    prov_adapter = BaltorLocalLineage()
    chk("lineage stub satisfies the port", isinstance(prov_adapter, LineageProvider))
    chk("wired adapter id is the local stub", prov_adapter.adapter_id == "lineage.baltor_local@v1")
    facet = prov_adapter.emit(ev)
    chk("emit() returns both renderings + content hash", set(facet.renderings) == {"prov", "openlineage"} and len(facet.content_hash) == 64)

    print(f"\n{'PASS — check_lineage_standards_adapters: PROV-JSON / OpenLineage / Web Annotation / JSON Patch all conformant, deterministic, and governance-bearing; the lineage stub renders them in-process (OpenLineage stays candidate-only).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: lineage standards adapters.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
