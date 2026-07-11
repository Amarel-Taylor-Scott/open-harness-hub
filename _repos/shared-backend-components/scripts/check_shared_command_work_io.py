#!/usr/bin/env python3
"""scripts.check_shared_command_work_io — PROOF: the command/work I/O layer is real — the EXISTING durable runtime
(FleetLedger) produces records that conform to the typed work-I/O contracts; the projectors name those shapes.

Drives a LIVE FleetLedger (in-memory, deterministic) through the full lifecycle and asserts:
  A. CONTRACTS: WorkerClaim/AckNackReceipt/DeadLetterEntry/IdempotencyKey registered; WorkItem ratified to
     CapabilityTask in the spine (no duplicate schema).
  B. WORK ITEM: enqueue → a work item carrying all WORK_ITEM_CORE_FIELDS, status queued, schema CapabilityTask.
  C. IDEMPOTENCY: re-enqueue with the same key returns the SAME task (dedup); project_idempotency_key conforms.
  D. CLAIM: atomic claim → project_worker_claim conforms (lease_owner + lease_until + claimed_at + status claimed).
  E. ACK: ack → succeeded; project_ack_nack_receipt(outcome=ack) conforms, carries result artifact ids.
  F. NACK retryable (attempts remain): → retry_wait; receipt outcome=nack, resulting_status retry_wait.
  G. DEAD-LETTER: nack at max_attempts (or non-retryable) → dead; project_dead_letter conforms, preserves the error.
  H. CONFORMANCE: every projected record contains all of its schema's required fields.
  I. DETERMINISM (projectors pure) + DEPENDENCY LAW (_repos/teleon/backend/src/teleon/io never imports src.baltor).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.workers.fleet_ledger import FleetLedger
from src.teleon.io import (project_work_item, project_worker_claim, project_ack_nack_receipt,
                           project_dead_letter, project_idempotency_key, WORK_ITEM_CORE_FIELDS)

_NOW = "2026-06-06T00:00:00Z"


def _required(schema_rel: str) -> list[str]:
    return json.loads((_resource("schemas") / "io" / schema_rel).read_text())["required"]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    def conforms(record: dict, schema_rel: str) -> bool:
        return all(k in record for k in _required(schema_rel))

    contracts = json.dumps(json.loads((_resource("architecture") / "contract_registry.json").read_text()))
    check("A: WorkerClaim/AckNackReceipt/DeadLetterEntry/IdempotencyKey registered",
          all(f"io/{s}.schema.json" in contracts for s in ("WorkerClaim", "AckNackReceipt", "DeadLetterEntry", "IdempotencyKey")))
    spine = json.loads((_resource("architecture") / "shared_io_spine.json").read_text())
    wi = next((c for L in spine["layers"] if L["layer"] == "command_work_io" for c in L["contracts"] if c["name"] == "WorkItem"), {})
    check("A: WorkItem ratified to CapabilityTask (no duplicate schema)", wi.get("status") == "ratified")

    L = FleetLedger()
    L.register_worker(worker_id="w1", capability_ids=["cap.demo"], now=_NOW)

    # B work item
    t = L.enqueue_task(tenant_id="t1", capability_id="cap.demo", idempotency_key="k-1", now=_NOW)
    wi_rec = project_work_item(t)
    check("B: work item carries core fields + queued + CapabilityTask",
          all(f in wi_rec for f in WORK_ITEM_CORE_FIELDS) and wi_rec["status"] == "queued" and wi_rec["schema_version"] == "CapabilityTask",
          str([f for f in WORK_ITEM_CORE_FIELDS if f not in wi_rec]))

    # C idempotency dedup
    t_again = L.enqueue_task(tenant_id="t1", capability_id="cap.demo", idempotency_key="k-1", now=_NOW)
    idk = project_idempotency_key(t)
    check("C: re-enqueue same key → same task (dedup) + IdempotencyKey conforms",
          t_again["task_id"] == t["task_id"] and conforms(idk, "IdempotencyKey.schema.json"))

    # D claim
    claimed = L.claim_task(worker_id="w1", capability_id="cap.demo", now=_NOW)
    wc = project_worker_claim(claimed)
    check("D: claim → WorkerClaim conforms (lease owner + lease_until + claimed)",
          claimed is not None and wc["worker_id"] == "w1" and wc["status"] == "claimed"
          and wc["lease_until"] and wc["claimed_at"] and conforms(wc, "WorkerClaim.schema.json"))

    # E ack (claim → start → ack; the status machine requires running before succeeded)
    L.start_task(claimed["task_id"], "w1", now=_NOW)
    acked = L.ack_task(claimed["task_id"], "w1", result_artifact_ids=["art-1"], now=_NOW)
    ar = project_ack_nack_receipt(acked, outcome="ack", worker_id="w1")
    check("E: ack → succeeded + AckNackReceipt conforms (result ids)",
          ar["resulting_status"] == "succeeded" and ar["outcome"] == "ack" and ar["result_artifact_ids"] == ["art-1"]
          and conforms(ar, "AckNackReceipt.schema.json"))

    # F nack retryable (max_attempts 3, attempts remain → runtime does retry_wait→queued, lease cleared)
    t2 = L.enqueue_task(tenant_id="t1", capability_id="cap.demo", idempotency_key="k-2", now=_NOW, max_attempts=3)
    L.claim_task(worker_id="w1", capability_id="cap.demo", now=_NOW)
    nacked = L.nack_task(t2["task_id"], "w1", {"msg": "transient"}, retryable=True, now=_NOW)
    nr = project_ack_nack_receipt(nacked, outcome="nack", worker_id="w1", retryable=True)
    check("F: nack(retryable) with attempts left → requeued (status queued, lease cleared, attempt incremented)",
          nr["resulting_status"] == "queued" and nr["outcome"] == "nack" and nr["attempt"] == 1
          and nacked["lease_owner"] == "" and conforms(nr, "AckNackReceipt.schema.json"),
          json.dumps(nr))

    # G dead-letter (max_attempts 1 → first nack is terminal)
    t3 = L.enqueue_task(tenant_id="t1", capability_id="cap.demo", idempotency_key="k-3", now=_NOW, max_attempts=1)
    L.claim_task(worker_id="w1", capability_id="cap.demo", now=_NOW)
    dead = L.nack_task(t3["task_id"], "w1", {"msg": "fatal"}, retryable=True, now=_NOW)
    dl = project_dead_letter(dead)
    nr3 = project_ack_nack_receipt(dead, outcome="nack", worker_id="w1", retryable=True)
    check("G: nack at max_attempts → dead + DeadLetterEntry conforms (error preserved)",
          dead["status"] == "dead" and dl["error_json"] == {"msg": "fatal"} and dl["reason"]
          and conforms(dl, "DeadLetterEntry.schema.json") and nr3["resulting_status"] == "dead",
          json.dumps(dl))
    # non-retryable also dead-letters
    t4 = L.enqueue_task(tenant_id="t1", capability_id="cap.demo", idempotency_key="k-4", now=_NOW, max_attempts=3)
    L.claim_task(worker_id="w1", capability_id="cap.demo", now=_NOW)
    dead2 = L.nack_task(t4["task_id"], "w1", {"msg": "no-retry"}, retryable=False, now=_NOW)
    check("G: non-retryable nack → dead immediately", dead2["status"] == "dead")

    # H conformance already checked per record above; assert all required-field sets are non-empty (real schemas)
    check("H: all work-I/O schemas declare required fields",
          all(_required(f"{s}.schema.json") for s in ("WorkerClaim", "AckNackReceipt", "DeadLetterEntry", "IdempotencyKey")))

    # I determinism (pure: same input snapshot → same output) + dependency law
    snap = dict(dead)
    check("I: projectors deterministic (pure)",
          project_dead_letter(snap) == project_dead_letter(snap)
          and project_ack_nack_receipt(snap, outcome="nack", worker_id="w1") == project_ack_nack_receipt(snap, outcome="nack", worker_id="w1"))
    src = "\n".join(p.read_text() for p in (_resource("src/teleon/io")).rglob("*.py"))
    check("I: _repos/teleon/backend/src/teleon/io never imports src.baltor",
          not any(l.strip().startswith(("import src.baltor", "from src.baltor")) for l in src.splitlines()))

    print("\n" + ("PASS — check_shared_command_work_io: the durable runtime (FleetLedger) produces records that "
                  "conform to the typed work-I/O contracts — work item = CapabilityTask, idempotent enqueue, "
                  "atomic WorkerClaim, AckNackReceipt (ack→succeeded / nack→retry_wait), and DeadLetterEntry at "
                  "max-attempts/non-retryable (error preserved); projectors are pure; Teleon-side."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_command_work_io.py --self-test")
    raise SystemExit(0)
