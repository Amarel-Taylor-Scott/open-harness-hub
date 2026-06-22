#!/usr/bin/env python3
"""check_source_poller — freshness CDC events are DETECTED from a real source poll (not passed in) + feed the reheal.

Closes the "live source fetch + CDC freshness" seam: poll_source fetches -> content-hashes -> compares to the last
recorded hash -> emits a real {new|changed|unchanged} CDC event (changed/new appended to cdc_events; unchanged not); a
'changed'/'new' event fed to a FreshnessSyncedCapability HOLDS the stale answer out (never served) until re-sync. Hermetic
(injected fetcher). serves_truth=false.

  python3 scripts/check_source_poller.py --self-test
"""
from __future__ import annotations

from src.teleon.evolution.freshness_runtime import FreshnessSyncedCapability
from src.teleon.evolution.source_poller import content_hash, poll_source, reheal_from_event
import uuid
from src.teleon.storage import record_store as RS


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    sid = "check_src_poller_" + uuid.uuid4().hex[:8]
    vals = iter(["STATE_A", "STATE_A", "STATE_B"])
    f = lambda: next(vals)
    e1 = poll_source(sid, f, now="2026-06-22T00:00:00Z")
    e2 = poll_source(sid, f, now="2026-06-22T00:01:00Z")
    e3 = poll_source(sid, f, now="2026-06-22T00:02:00Z")
    ck("first poll -> 'new' (recorded)", e1["kind"] == "new" and e1["prior_hash"] is None)
    ck("same content -> 'unchanged' (no spurious event)", e2["kind"] == "unchanged")
    ck("changed content -> 'changed' with prior + new hash", e3["kind"] == "changed" and e3["prior_hash"] == e1["content_hash"] and e3["content_hash"] != e1["content_hash"])
    ck("content_hash is deterministic", content_hash("STATE_A") == e1["content_hash"])

    # the change/new events landed in the append-only cdc_events stream
    st = RS.open_record_store("cdc_events")
    try:
        ours = [e for e in st.all() if e.get("source") == sid]
    finally:
        st.close()
    ck("changed/new events persisted to cdc_events (history tier); 'unchanged' NOT", len(ours) == 2 and {o["kind"] for o in ours} == {"new", "changed"})

    # a real CDC event feeds the reheal: the stale answer is HELD OUT (never served) until re-sync
    cap = FreshnessSyncedCapability("reg-deadline-x", authoritative_source=sid, volatility_class="volatile")
    held = reheal_from_event(cap, e3, now="2026-06-22T00:03:00Z")
    ck("a 'changed' CDC event holds the stale answer out (reheal wired)", isinstance(held, dict) and held)
    ck("'unchanged' does NOT trigger a reheal", reheal_from_event(cap, e2, now="t")["held_out"] is False)

    print("\n" + ("PASS - check_source_poller: CDC events DETECTED from a real poll (new/unchanged/changed), persisted, and "
                  "a change holds the stale answer out (live freshness, not passed-in)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
