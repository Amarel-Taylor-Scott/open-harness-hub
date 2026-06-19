#!/usr/bin/env python3
"""check_teleon_freshness_e2e — proof for the freshness/anti-fragility axis END-TO-END on a regulated fact.

The wedge formal-proof systems concede and gateways disclaim: keep the ground truth CURRENT. On a real regulated
fact (Reg E error-resolution deadline, eCFR §1005.11) the capability binds to the authoritative source, serves the
current value, and when the rule CHANGES holds the stale answer OUT — never serves it — until re-synced to the new
value. Asserts: fresh serve carries provenance; a stale answer is NEVER served; re-sync restores service with the
NEW value; the sync cadence matches the fragile-context volatility; never serves truth.

CLI: python3 scripts/check_teleon_freshness_e2e.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import FreshnessSyncedCapability, demonstrate_freshness_e2e
from src.teleon.evolution.freshness_runtime import STATUS_FRESH, STATUS_HELD_OUT_STALE


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    e2e = demonstrate_freshness_e2e()
    steps = dict(e2e["trace"])
    ck("the capability binds to the authoritative source on a volatility-matched cadence (monthly for low-volatility regs)",
       e2e["authoritative_source"] == "ecfr://12/1005.11" and e2e["sync_cadence"] == "monthly")

    # fresh serve carries the current value + provenance.
    fresh = steps["serve_fresh"]
    ck("after the initial sync, the CURRENT value is served (fresh) with provenance (source + version)",
       fresh["status"] == STATUS_FRESH and fresh["served"] == "10 business days"
       and fresh["provenance"]["authoritative_source"] == "ecfr://12/1005.11"
       and fresh["provenance"]["source_version"] == "2025-edition")

    # source change -> held out.
    changed = steps["source_changed"]
    ck("a CDC 'changed' event for the source marks the prior answer STALE + held out (CDC reheal armed)",
       changed["status"] == STATUS_HELD_OUT_STALE and changed["served"] is None and changed["cdc_reheal"] is True)

    # THE KEY GUARANTEE: while stale, the capability serves NOTHING — never the stale "10 business days".
    stale = steps["serve_while_stale"]
    ck("while stale the capability serves NOTHING (never serves the stale regulated fact)",
       stale["status"] == STATUS_HELD_OUT_STALE and stale["served"] is None and stale["value"] is None)

    # re-sync restores service with the NEW current value.
    again = steps["serve_fresh_again"]
    ck("after re-sync, the NEW current value is served (12 business days, 2026 edition)",
       again["status"] == STATUS_FRESH and again["served"] == "12 business days"
       and again["provenance"]["source_version"] == "2026-edition")

    ck("the whole freshness flow never serves truth (evidence/candidate, governed)",
       e2e["serves_truth"] is False and all(s.get("serves_truth") is False for _, s in e2e["trace"]))

    # an event for a DIFFERENT source is ignored (no spurious hold-out).
    cap = FreshnessSyncedCapability("x", authoritative_source="ecfr://12/1005.11", volatility_class="low")
    cap.sync("v1", now="t0", source_version="ed1")
    other = cap.on_source_change({"kind": "changed", "source": "ecfr://99/9999"}, now="t1")
    ck("a change event for a DIFFERENT source does not hold this capability out",
       cap.serve(now="t2")["status"] == STATUS_FRESH and "ignored" in other.get("note", ""))

    # realtime volatility -> continuous cadence (the policy adapts to how fast the facts move).
    rt = FreshnessSyncedCapability("price", authoritative_source="api://quotes", volatility_class="realtime")
    ck("a realtime-volatility capability gets a continuous sync cadence", rt.policy["sync_cadence"] == "continuous")

    # deterministic
    ck("the e2e is deterministic", demonstrate_freshness_e2e()["trace"] == e2e["trace"])

    print("\n" + ("PASS - check_teleon_freshness_e2e: a regulated fact (Reg E deadline / eCFR) binds to its "
                  "authoritative source on a volatility-matched cadence; it serves the current value with "
                  "provenance, and when the rule changes it HOLDS THE STALE ANSWER OUT — never serving it — until "
                  "re-synced to the new value. Keeping the ground truth current is the wedge provers concede + "
                  "gateways disclaim. Deterministic; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
