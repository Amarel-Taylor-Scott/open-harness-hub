#!/usr/bin/env python3
"""scripts.check_shared_io_resource_redteam — ADVERSARIAL PROOF of the Shared I/O + Resource Spine.

Standalone redteam: every attempt to smuggle a secret, skip a guard, or emit an ungoverned I/O artifact must FAIL
CLOSED. It attacks the REAL entry points (src/teleon/resources/resource_ref + src/teleon/io/{event_io,work_io,
inference_io}) — complementing check_shared_io_resource_spine (which proves the spine works on the happy path).

Attacks (each must be blocked / redacted / rejected):
  RESOURCE LAYER (resource_ref):
    A. raw secret smuggled into a DataResourceSpec -> validate_resource_spec rejects (raw_secret_in_resource_spec).
    B. a SecretRef carrying a raw value (or wrong scheme) -> make_secret_ref raises.
    C. a KeyRef with the wrong scheme -> make_key_ref raises.
    D. a temporary resource with no TTL -> rejected (temporary_resource_requires_ttl).
    E. a persistent resource with no owner/retention -> rejected (persistent_resource_requires_{owner,retention}).
    F. a cloud (non-local) provider with no local_equivalent -> rejected (cloud_resource_requires_local_equivalent).
    G. a secret_ref FIELD using the wrong scheme -> rejected (secret_ref_must_use_secret_scheme).
  EVENT LAYER (event_io):
    H. a raw secret in an event payload -> the projected CloudEvents data is REDACTED (secret never leaves).
    I. a projected event with no correlation_id -> raises (tracing guarantee).
    J. a projected event with a kind not in the single-source kind set -> raises.
  WORK LAYER (work_io):
    K. a WorkerClaim projection for a task with NO lease -> raises (no claim/ack without a lease).
    L. a retryable nack -> the AckNackReceipt requeues (resulting_status) + records the explicit worker + retryable
       (fallback/failure is never silent).
  INFERENCE LAYER (inference_io):
    M. a raw prompt handed to make_inference_request -> only its HASH is stored; the raw text never appears.
  CROSS-CUTTING:
    N. no raw-secret pattern appears in ANY artifact the spine produced in this run.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.resources import resource_ref as R
from src.teleon.io import event_io as E
from src.teleon.io import work_io as W
from src.teleon.io import inference_io as I
from scripts.context_events import EVENT_KINDS

_RAW = "sk-" + "a1b2c3d4" * 6          # trips the key-prefix guard
_DSN = "postgres://user:pass@host:5432/db"  # trips the DSN guard
_LEAK = re.compile(r"sk-[A-Za-z0-9_\-]{16,}|gsk_[A-Za-z0-9_\-]{16,}|(?:postgres|mysql|mongodb|redis)://[^ \"']+:[^ \"']+@")
_NOW = "2026-06-05T00:00:00Z"


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except Exception:
        return True


def _self_test() -> int:
    fails: list[str] = []
    produced: list = []  # every artifact we build, for the final no-leak scan

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ── RESOURCE LAYER ──
    leaky = R.make_data_resource_spec(logical_name="facts", kind_code=R.KIND["relational_table"],
                                      ownership_code=R.MANAGED_PERSISTENT, owner="team", retention_class="standard")
    leaky["note"] = _RAW  # smuggle a raw key into a free field (a REJECTED attacker input — not a spine output)
    okA, whyA = R.validate_resource_spec(leaky)
    check("A: raw secret smuggled into a resource spec is rejected", not okA and "raw_secret_in_resource_spec" in whyA, str(whyA))

    check("B: SecretRef carrying a raw value / wrong scheme raises",
          _raises(lambda: R.make_secret_ref(_RAW)) and _raises(lambda: R.make_secret_ref("secret://" + _RAW)))
    check("C: KeyRef with the wrong scheme raises", _raises(lambda: R.make_key_ref("not-a-key-ref")))

    notttl = R.make_data_resource_spec(logical_name="scratch", kind_code=R.KIND["relational_table"],
                                       ownership_code=R.MANAGED_EPHEMERAL)
    okD, whyD = R.validate_resource_spec(notttl)
    check("D: temporary resource with no TTL is rejected", not okD and "temporary_resource_requires_ttl" in whyD, str(whyD))

    noowner = R.make_data_resource_spec(logical_name="p", kind_code=R.KIND["relational_table"],
                                        ownership_code=R.MANAGED_PERSISTENT)
    okE, whyE = R.validate_resource_spec(noowner)
    check("E: persistent resource with no owner/retention is rejected",
          not okE and "persistent_resource_requires_owner" in whyE and "persistent_resource_requires_retention" in whyE, str(whyE))

    cloud = R.make_data_resource_spec(logical_name="b", kind_code=R.KIND["object_bucket"],
                                      ownership_code=R.MANAGED_PERSISTENT, owner="team", retention_class="standard",
                                      provider="aws_s3")
    okF, whyF = R.validate_resource_spec(cloud)
    check("F: cloud provider with no local_equivalent is rejected",
          not okF and "cloud_resource_requires_local_equivalent" in whyF, str(whyF))

    badscheme = R.make_data_resource_spec(logical_name="q", kind_code=R.KIND["relational_table"],
                                          ownership_code=R.MANAGED_PERSISTENT, owner="team", retention_class="standard",
                                          secret_ref="raw-not-a-ref")
    okG, whyG = R.validate_resource_spec(badscheme)
    check("G: a secret_ref field with the wrong scheme is rejected",
          not okG and any("secret_ref_must_use" in r for r in whyG), str(whyG))

    # a clean persistent spec with a proper secret_ref still passes (control)
    clean = R.make_data_resource_spec(logical_name="ok", kind_code=R.KIND["relational_table"],
                                      ownership_code=R.MANAGED_PERSISTENT, owner="team", retention_class="standard",
                                      secret_ref="secret://provider/db")
    okClean, _ = R.validate_resource_spec(clean)
    produced.append(clean)
    check("A-G control: a clean spec with a secret_ref (not a value) passes", okClean)

    # ── EVENT LAYER ──
    kind = "receipt_issued" if "receipt_issued" in EVENT_KINDS else sorted(EVENT_KINDS)[0]
    ev = {"seq": 1, "kind": kind, "correlation_id": "c1", "payload": {"api_key": _RAW, "dsn": _DSN, "ok": "fine"}}
    env = E.project_event_envelope(ev, source="redteam", now=_NOW, valid_kinds=EVENT_KINDS)
    produced.append(env)
    check("H: a raw secret in an event payload is REDACTED in the projection",
          _RAW not in json.dumps(env) and _DSN not in json.dumps(env) and "[REDACTED]" in json.dumps(env["data"]))
    check("I: a projected event with no correlation_id raises",
          _raises(lambda: E.project_event_envelope({"seq": 2, "kind": kind, "payload": {}}, source="x", now=_NOW)))
    check("J: a projected event with an unknown kind raises",
          _raises(lambda: E.project_event_envelope({"seq": 3, "kind": "totally.bogus.kind", "correlation_id": "c"},
                                                   source="x", now=_NOW, valid_kinds=EVENT_KINDS)))

    # ── WORK LAYER ──
    unleased = {"task_id": "t1", "status": "queued"}  # no lease_owner
    check("K: a WorkerClaim projection for an unleased task raises (no claim without a lease)",
          _raises(lambda: W.project_worker_claim(unleased)))
    requeued = {"task_id": "t2", "status": "queued", "attempt": 1}  # a retryable nack requeued it (lease cleared)
    rcpt = W.project_ack_nack_receipt(requeued, outcome="nack", worker_id="w-1", retryable=True)
    produced.append(rcpt)
    check("L: a retryable nack requeues + records the explicit worker + retryable (not silent)",
          rcpt.get("resulting_status") == "queued" and rcpt.get("worker_id") == "w-1" and rcpt.get("retryable") is True, json.dumps(rcpt))

    # ── INFERENCE LAYER ──
    req = I.make_inference_request(object_id="obj", requested_model_class="tier:400/300",
                                   input_text="SECRET PROMPT containing " + _RAW, now=_NOW, preference_id="p")
    produced.append(req)
    check("M: make_inference_request stores only the input HASH, never the raw prompt",
          req.get("input_hash", "").startswith("sha256:") and _RAW not in json.dumps(req) and "SECRET PROMPT" not in json.dumps(req))

    # ── CROSS-CUTTING ──
    leaks = [i for i, a in enumerate(produced) if _LEAK.search(json.dumps(a))]
    check("N: no raw-secret pattern in ANY artifact the spine produced", not leaks, f"artifacts with a leak: {leaks}")

    print("\n" + ("PASS — check_shared_io_resource_redteam: every attack on the Shared I/O + Resource Spine fails "
                  "closed — raw secrets/DSNs are rejected or redacted, temporary/persistent/cloud guards hold, events "
                  "require a correlation_id + known kind, work needs a lease (nack is never silent), inference stores "
                  "only the input hash, and no artifact leaks a secret." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_io_resource_redteam.py --self-test")
    raise SystemExit(0)
