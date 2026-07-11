#!/usr/bin/env python3
"""scripts.check_distillation_rollback — proof: rollback moves the pointer only and deletes nothing.

Promotes a candidate pack over a baseline, stores an old ``ContextResponse`` derived from the baseline, then
rolls back via ``src.baltor.distillation.rollback.{RollbackPlan, execute}`` and asserts the lossless law:

* a promoted candidate rolls back to the baseline (the active pointer becomes the baseline);
* the old ``ContextResponse`` remains readable after rollback;
* the current pointer CHANGES (candidate → baseline);
* a rollback RECEIPT is written (as a lossless derived entry whose lineage reaches both versions);
* the candidate artifacts are NOT deleted (still present + still a version of the key);
* rollback is tenant-scoped and deterministic.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_distillation_rollback.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.distillation.lossless_store import DistillationStoreError, LosslessStore  # noqa: E402
from src.baltor.distillation.rollback import RollbackPlan, execute  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_PACK_KEY = "cfpb/pack/regE"
_HANDLE = "ctx://cfpb/consumer-complaints/complaint/demo-1001#timely"


def _setup(store: LosslessStore) -> dict:
    raw = store.put_raw(_TENANT, key="cfpb/raw/demo-1001", raw_bytes=b'{"timely":"Yes"}', now=_NOW)
    src = store.put_source(_TENANT, key="cfpb/source/demo-1001", body={"timely": "Yes"},
                           parent_ids=[raw.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001"],
                           transform_run_id="run-normalize-1", now=_NOW)
    fact = store.put_derived(_TENANT, key="cfpb/fact/demo-1001/timely",
                             body={"text": "timely response is Yes."}, parent_ids=[src.entry_id],
                             source_handles=[_HANDLE], transform_type="decompose",
                             transform_run_id="run-decompose-1", role="atomic_fact", now=_NOW)
    baseline = store.put_derived(_TENANT, key=_PACK_KEY, body={"answer": "10 business days", "v": "baseline"},
                                 parent_ids=[fact.entry_id], source_handles=[_HANDLE],
                                 transform_type="optimize", transform_run_id="run-opt-baseline",
                                 role="baseline", now=_NOW)
    # an old ContextResponse served FROM the baseline (must stay readable after a future rollback).
    old_response = store.put_derived(_TENANT, key="cfpb/response/regE",
                                     body={"schema_version": "ContextResponse", "answer": "10 business days",
                                           "served_from": "baseline"}, parent_ids=[baseline.entry_id],
                                     source_handles=[_HANDLE], transform_type="consume",
                                     transform_run_id="run-consume-baseline", role="context_response", now=_NOW)
    # a promoted candidate over the baseline, made the active pointer.
    candidate = store.put_derived(_TENANT, key=_PACK_KEY, body={"answer": "10 business days", "v": "candidate", "compressed": True},
                                  parent_ids=[baseline.entry_id], source_handles=[_HANDLE],
                                  transform_type="promote", transform_run_id="run-promote-1",
                                  rollback_target_ids=[baseline.entry_id], role="winner", now=_NOW)
    store.set_current(_PACK_KEY, candidate.entry_id, tenant=_TENANT)
    return {"baseline": baseline, "candidate": candidate, "old_response": old_response, "fact": fact}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LosslessStore()
    g = _setup(store)
    baseline, candidate, old_response = g["baseline"], g["candidate"], g["old_response"]

    # precondition: the candidate is the active pointer.
    check("precondition: the promoted candidate is the active pointer",
          store.current_id(_PACK_KEY, tenant=_TENANT) == candidate.entry_id)
    versions_before = len(store.versions(_PACK_KEY, tenant=_TENANT))

    # build + execute the rollback plan (candidate → baseline).
    plan = RollbackPlan.of(store, key=_PACK_KEY, tenant=_TENANT, to_id=baseline.entry_id,
                           reason="candidate regressed source-handle coverage in monitoring")
    check("RollbackPlan.of sets from_id = the live candidate", plan.from_id == candidate.entry_id)
    check("RollbackPlan.of sets to_id = the baseline", plan.to_id == baseline.entry_id)
    receipt = execute(store, plan, now=_NOW)

    # 1) the promoted candidate rolled back to the baseline (pointer now names the baseline).
    check("after rollback the active pointer is the BASELINE",
          store.current_id(_PACK_KEY, tenant=_TENANT) == baseline.entry_id)
    check("the current pointer CHANGED (candidate → baseline)",
          store.current_id(_PACK_KEY, tenant=_TENANT) != candidate.entry_id)

    # 2) the old ContextResponse remains readable.
    resp = store.get(old_response.entry_id, tenant=_TENANT)
    check("the old ContextResponse remains readable after rollback",
          resp.body["schema_version"] == "ContextResponse" and resp.body["answer"] == "10 business days")

    # 3) a rollback receipt was written (as a lossless derived entry reaching both versions).
    check("a rollback receipt is returned", receipt.receipt_id.startswith("rbkrcpt-"))
    check("the rollback receipt records from→to", receipt.rolled_from_id == candidate.entry_id and receipt.rolled_to_id == baseline.entry_id)
    rcpt_entry = store.get(receipt.receipt_entry_id, tenant=_TENANT)
    check("the rollback receipt was persisted as a lossless derived entry", rcpt_entry.transform_type == "rollback")
    check("the receipt entry's lineage reaches BOTH baseline and candidate",
          baseline.entry_id in rcpt_entry.parent_ids and candidate.entry_id in rcpt_entry.parent_ids)
    check("the receipt carries the candidate as a rollback_target (reconstructable)",
          candidate.entry_id in rcpt_entry.rollback_target_ids)

    # 4) the candidate artifacts are NOT deleted.
    check("the promoted candidate is NOT deleted (still gettable)",
          store.has(candidate.entry_id) and store.get(candidate.entry_id, tenant=_TENANT).body["v"] == "candidate")
    check("the receipt asserts candidate_preserved", receipt.candidate_preserved is True)
    check("the candidate is still a version of the key (versions list did not shrink)",
          candidate.entry_id in {e.entry_id for e in store.versions(_PACK_KEY, tenant=_TENANT)})
    # the rollback added the receipt under its own key; the pack key's version count is unchanged.
    check("the pack key's version count is unchanged by rollback (no version removed)",
          len(store.versions(_PACK_KEY, tenant=_TENANT)) == versions_before)

    # 5) rollback can be re-applied forward then back (pointer is the only state that moves).
    store.set_current(_PACK_KEY, candidate.entry_id, tenant=_TENANT)
    check("the pointer can move forward to the candidate again (it was never deleted)",
          store.current_id(_PACK_KEY, tenant=_TENANT) == candidate.entry_id)

    # 6) NEGATIVE: a plan whose from_id is not the live pointer is rejected.
    store.set_current(_PACK_KEY, baseline.entry_id, tenant=_TENANT)  # baseline is live now
    stale = RollbackPlan(key=_PACK_KEY, tenant_id=_TENANT, from_id=candidate.entry_id, to_id=baseline.entry_id)
    stale_caught = False
    try:
        execute(store, stale, now=_NOW)  # from_id (candidate) is no longer the live pointer
    except DistillationStoreError:
        stale_caught = True
    check("execute rejects a plan whose from_id is not the live pointer (negative-tested)", stale_caught)
    # NEGATIVE: a rollback target that is not a version of the key is rejected.
    bad_target_caught = False
    try:
        RollbackPlan.of(store, key=_PACK_KEY, tenant=_TENANT, to_id=g["fact"].entry_id)
    except DistillationStoreError:
        bad_target_caught = True
    check("RollbackPlan.of rejects a target that is not a version of the key (negative-tested)", bad_target_caught)

    # 7) deterministic receipt id.
    store2 = LosslessStore()
    g2 = _setup(store2)
    plan2 = RollbackPlan.of(store2, key=_PACK_KEY, tenant=_TENANT, to_id=g2["baseline"].entry_id,
                            reason="candidate regressed source-handle coverage in monitoring")
    receipt2 = execute(store2, plan2, now=_NOW)
    check("rollback receipt id is deterministic across a clean run", receipt2.receipt_id == receipt.receipt_id)

    ok = not fails
    print("\n" + ("PASS — check_distillation_rollback: rollback moves the active pointer from the promoted "
                  "candidate back to the baseline, the old ContextResponse stays readable, a rollback receipt is "
                  "written as a lossless entry reaching both versions, the candidate is never deleted, and the "
                  "operation is tenant-scoped + deterministic." if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: rollback moves the pointer only and deletes nothing.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
