#!/usr/bin/env python3
"""scripts.check_fleet_execution_projection — PROOF: the live execution-backend decisions are VISIBLE on the
API/UI (closes the CLOUD-DEFER bar "local equivalent … API/UI visible"). READ-ONLY projection only.

Asserts:
  A. supervisor_projection exposes an `execution` section: total + by_backend + by_capability + recent + note,
     and it distinguishes backends (a local-emulator vs local-subprocess mix shows up separately).
  B. /api/fleet/execution works via fleet_section("execution") (the admin route delegates to it).
  C. The projection is READ-ONLY — calling it does not mutate the SupervisorStore (decision count unchanged).
  D. The /fleet page (_repos/baltor/frontend/fleet.html) renders the execution panels and stays PROJECTION-ONLY
     (GET only — no POST/PUT/DELETE, no mutating fetch).

Deterministic + offline: injected `now`, temp DB, no network. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from scripts._repo_paths import resource
from src.baltor.workers import execution_dispatch, supervisor_projection
from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
from src.baltor.workers.supervisor_store import SupervisorStore

_NOW_ISO = "2026-06-06T00:00:00Z"
_NOW = 1_749_168_000
# web/baltor/fleet.html relocated to _repos/baltor/frontend/fleet.html by the _repos/ migration; resolve via
# the universal resource() resolver so the read finds the real file (no compat symlink at the old root).
_FLEET_HTML = resource("web/baltor/fleet.html")


def _seed(db: str) -> None:
    """Record two execution-backend decisions on DIFFERENT backends by driving real dispatch."""
    store = SupervisorStore(db)
    L = DurableFleetLedger(db)
    for i in range(2):
        L.enqueue_task(tenant_id="t", capability_id="verify", idempotency_key=f"v{i}", now=_NOW_ISO)
    for i in range(2):
        L.enqueue_task(tenant_id="t", capability_id="ingest", idempotency_key=f"g{i}", now=_NOW_ISO)
    L.close()
    # verify → default local function emulator; ingest → forced to local_subprocess (a deliberate switch)
    execution_dispatch.dispatch_capability(store, db, capability="verify", bucket="verification_fact_check",
                                           now=_NOW, run=True)
    execution_dispatch.dispatch_capability(store, db, capability="ingest", bucket="ingestion_sync", now=_NOW,
                                           run=True, policy_override={"preferred_backends": ["local_subprocess@v1"]})
    store.close()


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("'execution' is a registered fleet section", "execution" in supervisor_projection._SECTIONS)

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "fleet.db")
        _seed(db)

        # ── A. execution section is present + well-shaped + distinguishes backends ──
        proj = supervisor_projection.fleet_projection(db, now=_NOW)
        ex = proj.get("execution", {})
        check("A: projection has an execution section", isinstance(ex, dict) and "by_backend" in ex, str(list(ex)))
        check("A: total counts both decisions", ex.get("total") == 2, str(ex.get("total")))
        check("A: by_backend distinguishes the two backends",
              ex.get("by_backend", {}).get("local_function_emulator@v1") == 1
              and ex.get("by_backend", {}).get("local_subprocess@v1") == 1, str(ex.get("by_backend")))
        check("A: by_capability shows verify + ingest",
              set(ex.get("by_capability", {})) == {"verify", "ingest"}, str(ex.get("by_capability")))
        check("A: recent rows carry capability + backend (parsed from the key, not prose)",
              all(r.get("capability") in ("verify", "ingest") and "@" in r.get("backend", "") for r in ex.get("recent", []))
              and len(ex.get("recent", [])) == 2, str(ex.get("recent")))
        check("A: note states the choice is switchable + local-first", "switchable" in ex.get("note", "")
              or "reversible" in ex.get("note", ""), ex.get("note", ""))

        # ── B. /api/fleet/execution path (fleet_section) ──
        sec = supervisor_projection.fleet_section("execution", db, now=_NOW)
        check("B: fleet_section('execution') ok + returns the section", sec.get("ok") is True and "execution" in sec,
              str(sec.get("error")))
        check("B: section payload matches the full projection", sec["execution"]["total"] == 2)

        # ── C. projection is READ-ONLY (no mutation) ──
        s = SupervisorStore(db)
        before = len(s.decisions(decision_type="execution_backend"))
        s.close()
        supervisor_projection.fleet_projection(db, now=_NOW)   # call again
        s = SupervisorStore(db)
        after = len(s.decisions(decision_type="execution_backend"))
        s.close()
        check("C: projecting does not mutate the store", before == after == 2, f"{before}->{after}")

    # ── D. the /fleet page renders the panels and stays projection-only ──
    html = _FLEET_HTML.read_text()
    check("D: fleet.html renders the execution-mix panel", 'id="execmix"' in html and 'id="execrecent"' in html)
    check("D: fleet.html reads d.execution", "d.execution" in html or ".execution" in html)
    lowered = html.lower()
    check("D: fleet page is PROJECTION-ONLY (no mutating verbs)",
          not any(v in lowered for v in ("method: 'post'", 'method:"post"', "method: 'put'", "method: 'delete'",
                                         ".post(", ".put(", ".delete(")), "found a mutating call")

    print("\n" + ("PASS — check_fleet_execution_projection: the live execution-backend decisions are visible on "
                  "/api/fleet/execution + the /fleet page (by-backend mix, recent decisions, switchable/local-first "
                  "note), READ-ONLY, projection-only — the CLOUD-DEFER 'API/UI visible' bar is met."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_fleet_execution_projection.py --self-test")
    raise SystemExit(0)
