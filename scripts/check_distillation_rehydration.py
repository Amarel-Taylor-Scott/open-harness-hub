#!/usr/bin/env python3
"""scripts.check_distillation_rehydration — proof: every derived artifact rehydrates to its source.

Builds a CFPB-shaped lossless graph and asserts ``src.baltor.distillation.rehydration.rehydrate``:

* an atomic fact rehydrates to its SOURCE field record and its RAW record;
* an optimized pack rehydrates to its BASELINE (reachable through ``parents``/``bundle``);
* a held-out FAQ-30 rehydrates to the SOURCE it was held out of PLUS the reconciliation receipt;
* ``rehydrate_payload`` returns the EXACT raw bytes;
* rehydration NEVER crosses a tenant boundary (negative-tested).

CLI: PYTHONPATH=. python3 scripts/check_distillation_rehydration.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.distillation.lossless_store import LosslessStore  # noqa: E402
from src.baltor.distillation.rehydration import RehydrationError, rehydrate, rehydrate_payload  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_OTHER = "globex"
_HANDLE = "ctx://cfpb/consumer-complaints/complaint/demo-1001"
_RAW = b'{"native_id":"demo-1001","timely":"Yes","faq30":"FAQ #30 superseded by Reg E 1005.11"}'


def _build(store: LosslessStore, tenant: str) -> dict:
    raw = store.put_raw(tenant, key="cfpb/raw/demo-1001", raw_bytes=_RAW, mime_type="application/json", now=_NOW)
    src = store.put_source(tenant, key="cfpb/source/demo-1001",
                           body={"native_id": "demo-1001", "fields": {"timely": "Yes", "faq30": "FAQ #30 …"}},
                           parent_ids=[raw.entry_id], source_handles=[_HANDLE],
                           transform_run_id="run-normalize-1", now=_NOW)
    fact = store.put_derived(tenant, key="cfpb/fact/demo-1001/timely",
                             body={"text": "Complaint demo-1001: timely response is Yes.", "field": "timely"},
                             parent_ids=[src.entry_id], source_handles=[f"{_HANDLE}#timely"],
                             transform_type="decompose", transform_run_id="run-decompose-1",
                             role="atomic_fact", now=_NOW)
    baseline = store.put_derived(tenant, key="cfpb/pack/regE", body={"answer": "10 business days", "v": 1},
                                 parent_ids=[fact.entry_id], source_handles=[f"{_HANDLE}#timely"],
                                 transform_type="optimize", transform_run_id="run-opt-baseline",
                                 role="baseline", now=_NOW)
    optimized = store.put_derived(tenant, key="cfpb/pack/regE", body={"answer": "10 business days", "v": 2, "compressed": True},
                                  parent_ids=[baseline.entry_id], source_handles=[f"{_HANDLE}#timely"],
                                  transform_type="optimize", transform_run_id="run-opt-candidate",
                                  role="winner", now=_NOW)
    # FAQ-30 held out by a reconciliation (superseded by the regulation) — kept + rehydratable.
    faq30 = store.put_derived(tenant, key="cfpb/faq/30",
                              body={"text": "FAQ #30: old guidance.", "field": "faq30"},
                              parent_ids=[src.entry_id], source_handles=[f"{_HANDLE}#faq30"],
                              transform_type="decompose", transform_run_id="run-decompose-1",
                              role="held_out", receipt_ids=["recon-faq30-receipt"], now=_NOW)
    return {"raw": raw, "src": src, "fact": fact, "baseline": baseline, "optimized": optimized, "faq30": faq30}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LosslessStore()
    g = _build(store, _TENANT)

    # 1) atomic fact → source field → raw record.
    rh = rehydrate(store, g["fact"].entry_id, _TENANT)
    check("atomic fact rehydrates to its SOURCE record",
          any(s["entry_id"] == g["src"].entry_id for s in rh["source"]))
    check("atomic fact rehydrates to its RAW record",
          any(r["entry_id"] == g["raw"].entry_id for r in rh["raw"]))
    check("rehydrated source carries the #field handle", _HANDLE in rh["bundle"]["source_handles"] or
          any(_HANDLE in s["source_handles"] for s in rh["source"]))

    # 2) optimized pack rehydrates to its baseline (reachable in the bundle).
    rho = rehydrate(store, g["optimized"].entry_id, _TENANT)
    check("optimized pack rehydrates to its BASELINE (parents)",
          any(p["entry_id"] == g["baseline"].entry_id for p in rho["parents"]))
    check("optimized pack's bundle reaches the baseline", g["baseline"].entry_id in rho["bundle"]["reached_ids"])
    check("optimized pack rehydrates all the way to raw + source",
          bool(rho["raw"]) and bool(rho["source"]))

    # 3) held-out FAQ-30 → source + reconciliation receipt.
    rf = rehydrate(store, g["faq30"].entry_id, _TENANT)
    check("held-out FAQ-30 is still rehydratable (omitted ≠ deleted)", rf["artifact"]["entry_id"] == g["faq30"].entry_id)
    check("FAQ-30 rehydrates to the SOURCE it was held out of",
          any(s["entry_id"] == g["src"].entry_id for s in rf["source"]))
    check("FAQ-30 rehydrates with its reconciliation receipt", "recon-faq30-receipt" in rf["receipts"])

    # 4) exact raw bytes via payload rehydration.
    check("rehydrate_payload returns the EXACT raw bytes for a fact",
          rehydrate_payload(store, g["fact"].entry_id, _TENANT) == _RAW)
    check("rehydrate_payload returns the EXACT raw bytes for the optimized pack",
          rehydrate_payload(store, g["optimized"].entry_id, _TENANT) == _RAW)

    # 5) NEGATIVE: rehydration never crosses a tenant boundary.
    other = LosslessStore()
    go = _build(other, _OTHER)
    # asking the SAME store with a foreign tenant must fail (cross-tenant read).
    cross1 = False
    try:
        rehydrate(store, g["fact"].entry_id, _OTHER)
    except RehydrationError:
        cross1 = True
    check("rehydrate() rejects a foreign tenant for an artifact id (negative-tested)", cross1)
    cross2 = False
    try:
        rehydrate_payload(store, g["fact"].entry_id, _OTHER)
    except RehydrationError:
        cross2 = True
    check("rehydrate_payload() rejects a foreign tenant (negative-tested)", cross2)
    empty_tenant = False
    try:
        rehydrate(store, g["fact"].entry_id, "")
    except RehydrationError:
        empty_tenant = True
    check("rehydrate() refuses an empty tenant (no anonymous rehydration)", empty_tenant)
    # the other tenant's identical graph rehydrates fine on its own — isolation, not breakage.
    check("the other tenant rehydrates its OWN identical graph", rehydrate(other, go["fact"].entry_id, _OTHER)["raw"])

    # 6) deterministic projection.
    check("rehydrate() is deterministic (rebuild identical)",
          rehydrate(store, g["fact"].entry_id, _TENANT) == rh)

    ok = not fails
    print("\n" + ("PASS — check_distillation_rehydration: an atomic fact rehydrates to its source field + raw "
                  "record, an optimized pack rehydrates to its baseline, a held-out FAQ-30 rehydrates to its source "
                  "+ reconciliation receipt, payload rehydration returns exact bytes, and rehydration never crosses "
                  "a tenant boundary." if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: every derived artifact rehydrates to its source (tenant-scoped).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
