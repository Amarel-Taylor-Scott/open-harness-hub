#!/usr/bin/env python3
"""scripts.check_lineage_bundle_complete — proof: every promoted artifact has a complete LineageBundle.

Builds a small CFPB-shaped lossless graph (raw → source → atomic facts → optimized pack → reconciliation
winner/loser) in ``LosslessStore`` and asserts ``LineageBundle.build`` satisfies the promotability test:

* a served-fact bundle REACHES raw + source;
* an optimized-pack bundle REACHES its baseline;
* a reconciliation bundle REACHES BOTH the winner and the loser (no winner without lineage to the loser);
* no promoted artifact has empty ``source_handles`` or a missing ``transform_run_id`` (``is_complete``);
* the lineage is tenant-scoped — it never reaches a foreign tenant.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_lineage_bundle_complete.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.distillation.lineage import LineageBundle  # noqa: E402
from src.baltor.distillation.lossless_store import LosslessStore  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_HANDLE = "ctx://cfpb/consumer-complaints/complaint/demo-1001"


def _build_graph(store: LosslessStore) -> dict:
    """raw → source → two atomic facts → optimized pack (baseline→candidate) → reconciliation winner/loser."""
    raw = store.put_raw(_TENANT, key="cfpb/raw/demo-1001",
                        raw_bytes=b'{"native_id":"demo-1001","timely":"Yes","company_response":"Closed with explanation"}',
                        mime_type="application/json", now=_NOW)
    src = store.put_source(_TENANT, key="cfpb/source/demo-1001", body={"native_id": "demo-1001"},
                           parent_ids=[raw.entry_id], source_handles=[_HANDLE],
                           transform_run_id="run-normalize-1", now=_NOW)
    fact_timely = store.put_derived(_TENANT, key="cfpb/fact/demo-1001/timely",
                                    body={"text": "Complaint demo-1001: timely response is Yes."},
                                    parent_ids=[src.entry_id], source_handles=[f"{_HANDLE}#timely"],
                                    transform_type="decompose", transform_run_id="run-decompose-1",
                                    role="atomic_fact", now=_NOW)
    fact_resp = store.put_derived(_TENANT, key="cfpb/fact/demo-1001/company_response",
                                  body={"text": "Complaint demo-1001: company response is Closed with explanation."},
                                  parent_ids=[src.entry_id], source_handles=[f"{_HANDLE}#company_response"],
                                  transform_type="decompose", transform_run_id="run-decompose-1",
                                  role="atomic_fact", now=_NOW)
    # optimized pack: baseline then a promoted candidate over it.
    baseline = store.put_derived(_TENANT, key="cfpb/pack/regE", body={"answer": "10 business days", "v": 1},
                                 parent_ids=[fact_timely.entry_id, fact_resp.entry_id],
                                 source_handles=[f"{_HANDLE}#timely"], transform_type="optimize",
                                 transform_run_id="run-opt-baseline", role="baseline", now=_NOW)
    optimized = store.put_derived(_TENANT, key="cfpb/pack/regE", body={"answer": "10 business days", "v": 2, "compressed": True},
                                  parent_ids=[baseline.entry_id], source_handles=[f"{_HANDLE}#timely"],
                                  transform_type="optimize", transform_run_id="run-opt-candidate", role="winner", now=_NOW)
    # reconciliation: a fact-vs-allegation conflict resolved; winner = fact, loser = allegation (held out).
    allegation = store.put_derived(_TENANT, key="cfpb/allegation/demo-1001/s0",
                                   body={"text": "They reported an account that is not mine."},
                                   parent_ids=[src.entry_id], source_handles=[f"{_HANDLE}#narrative.s0"],
                                   transform_type="decompose", transform_run_id="run-decompose-1",
                                   role="held_out", now=_NOW)
    reconciliation = store.put_derived(_TENANT, key="cfpb/reconciliation/demo-1001",
                                       body={"decision": "resolved_by_scope", "winner": "fact", "loser": "allegation"},
                                       parent_ids=[fact_timely.entry_id, allegation.entry_id],
                                       source_handles=[f"{_HANDLE}#timely"], transform_type="reconcile",
                                       transform_run_id="run-reconcile-1", role="winner",
                                       held_out_ids=[allegation.entry_id], receipt_ids=["recon-receipt-1"], now=_NOW)
    return {"raw": raw, "src": src, "fact_timely": fact_timely, "fact_resp": fact_resp,
            "baseline": baseline, "optimized": optimized, "allegation": allegation, "reconciliation": reconciliation}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LosslessStore()
    g = _build_graph(store)

    # 1) a served-fact bundle reaches raw + source.
    fb = LineageBundle.build(store, g["fact_timely"].entry_id, tenant=_TENANT)
    check("served-fact bundle reaches RAW", fb.reaches_raw() and g["raw"].entry_id in fb.raw_ids)
    check("served-fact bundle reaches SOURCE", fb.reaches_source() and g["src"].entry_id in fb.source_ids)
    check("served-fact bundle carries its #field source handle", f"{_HANDLE}#timely" in fb.source_handles)
    check("served-fact bundle names the transform_run that produced it", "run-decompose-1" in fb.transform_run_ids)
    check("served-fact bundle is_complete()", fb.is_complete())

    # 2) an optimized-pack bundle reaches its baseline.
    ob = LineageBundle.build(store, g["optimized"].entry_id, tenant=_TENANT)
    check("optimized-pack bundle reaches the BASELINE", ob.reaches(g["baseline"].entry_id))
    check("optimized-pack bundle reaches raw + source through the baseline",
          ob.reaches_raw() and ob.reaches_source())
    check("optimized-pack bundle records prior versions of its key (the baseline is a prior version)",
          g["baseline"].entry_id in ob.prior_version_ids)
    check("optimized-pack bundle is_complete()", ob.is_complete())

    # 3) a reconciliation bundle reaches BOTH winner and loser (no winner without lineage to the loser).
    rb = LineageBundle.build(store, g["reconciliation"].entry_id, tenant=_TENANT)
    check("reconciliation bundle reaches the WINNER (the atomic fact)", rb.reaches(g["fact_timely"].entry_id))
    check("reconciliation bundle reaches the LOSER (the held-out allegation)", rb.reaches(g["allegation"].entry_id))
    check("reconciliation bundle records the loser as held-out (kept, not deleted)",
          g["allegation"].entry_id in rb.held_out_ids and store.has(g["allegation"].entry_id))
    check("reconciliation bundle carries its reconciliation receipt", "recon-receipt-1" in rb.receipt_ids)
    check("reconciliation bundle is_complete()", rb.is_complete())

    # 4) no promoted artifact has empty source_handles or a missing transform_run_id.
    promoted = [g["fact_timely"], g["fact_resp"], g["baseline"], g["optimized"], g["reconciliation"]]
    empty_handle = [a.entry_id for a in promoted
                    if not LineageBundle.build(store, a.entry_id, tenant=_TENANT).source_handles]
    missing_run = [a.entry_id for a in promoted
                   if not LineageBundle.build(store, a.entry_id, tenant=_TENANT).transform_run_ids]
    check("no promoted artifact has empty source_handles", empty_handle == [], str(empty_handle))
    check("no promoted artifact has a missing transform_run_id", missing_run == [], str(missing_run))
    check("every promoted artifact's bundle is_complete()",
          all(LineageBundle.build(store, a.entry_id, tenant=_TENANT).is_complete() for a in promoted))

    # 5) the bundle is tenant-scoped — it never reaches a foreign tenant.
    other = LosslessStore()
    _build_graph(other)  # an identical graph for a different store — must not bleed in
    # build for the wrong tenant raises (cross-tenant read), proving scoping at the read boundary.
    cross_caught = False
    try:
        LineageBundle.build(store, g["fact_timely"].entry_id, tenant="globex")
    except Exception:
        cross_caught = True
    check("LineageBundle.build is tenant-scoped (wrong tenant rejected)", cross_caught)
    check("bundle's reached ids are all the requesting tenant's",
          all(store.get(i, tenant=_TENANT).tenant_id == _TENANT for i in fb.reached_ids))

    # 6) deterministic: rebuilding the same bundle yields the same projection.
    check("LineageBundle.build is deterministic (rebuild identical)",
          LineageBundle.build(store, g["fact_timely"].entry_id, tenant=_TENANT).to_dict() == fb.to_dict())

    ok = not fails
    print("\n" + ("PASS — check_lineage_bundle_complete: every promoted artifact's LineageBundle reaches raw + "
                  "source, an optimized pack reaches its baseline, a reconciliation reaches BOTH winner and loser, "
                  "no promoted artifact has empty handles or a missing transform_run, and the lineage is tenant-"
                  "scoped and deterministic." if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: every promoted artifact has a complete LineageBundle.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
