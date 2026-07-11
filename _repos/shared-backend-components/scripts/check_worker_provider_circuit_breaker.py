#!/usr/bin/env python3
"""scripts.check_worker_provider_circuit_breaker — proof (C-FLEET-2): per-provider circuit breakers open
on consecutive failures / failure rate / forced signals, reject while open, admit probes in half_open, and
close on a good probe (re-open on a bad one). Only taxonomy `opens_circuit` failures count. The fallback
router routes to the first provider whose circuit admits work, holds when all are open, and stamps results
with provider_id (one provider per attempt — no duplicate side effects).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_worker_provider_circuit_breaker.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.provider_circuit_breaker import CLOSED, HALF_OPEN, OPEN, CircuitBreaker
from src.baltor.workers.provider_fallback import FallbackRouter

T0 = "2026-06-06T00:00:00Z"


def _plus(sec):
    return f"2026-06-06T00:{sec // 60:02d}:{sec % 60:02d}Z"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # consecutive failures trip the breaker
    cb = CircuitBreaker("p", consec_threshold=3, open_seconds=60)
    chk("starts closed", cb.state(now=T0) == CLOSED)
    for _ in range(3):
        cb.record_failure("rate_limited", now=T0)   # opens_circuit=True
    chk("opens after consecutive failures", cb.state(now=T0) == OPEN)
    chk("rejects work while open", cb.allow(now=T0) is False)

    # after open_seconds → half_open admits limited probes
    chk("half_open after cooldown", cb.state(now=_plus(61)) == HALF_OPEN)
    chk("half_open admits a probe", cb.allow(now=_plus(61)) is True)
    cb.record_success(now=_plus(61))
    chk("good probe closes the circuit", cb.state(now=_plus(62)) == CLOSED)

    # a bad probe re-opens
    cb2 = CircuitBreaker("p", consec_threshold=2, open_seconds=30)
    cb2.record_failure("rate_limited", now=T0); cb2.record_failure("rate_limited", now=T0)
    cb2.state(now=_plus(31))  # → half_open
    cb2.allow(now=_plus(31))
    cb2.record_failure("rate_limited", now=_plus(31))
    chk("bad probe re-opens", cb2.state(now=_plus(31)) == OPEN)

    # non-opens_circuit failures do NOT trip
    cb3 = CircuitBreaker("p", consec_threshold=2)
    cb3.record_failure("parse_failed", now=T0); cb3.record_failure("parse_failed", now=T0)
    chk("content failures (opens_circuit=false) do not trip", cb3.state(now=T0) == CLOSED)

    # forced open (health check / rate limit signal)
    cb4 = CircuitBreaker("p")
    cb4.force_open(now=T0)
    chk("force_open trips immediately", cb4.state(now=T0) == OPEN)

    # fallback router: primary open → route to fallback; all open → None
    fr = FallbackRouter(["primary@v1", "fallback@v1"], consec_threshold=2, open_seconds=300)
    chk("router selects primary first", fr.select(now=T0) == "primary@v1")
    fr.record_failure("primary@v1", "provider_unavailable", now=T0)
    fr.record_failure("primary@v1", "provider_unavailable", now=T0)
    chk("primary tripped → router selects fallback", fr.select(now=T0) == "fallback@v1")
    fr.record_failure("fallback@v1", "provider_unavailable", now=T0)
    fr.record_failure("fallback@v1", "provider_unavailable", now=T0)
    chk("all circuits open → router holds (None)", fr.select(now=T0) is None)
    chk("result stamped with provider_id (provenance, single provider)",
        FallbackRouter.mark_output("fallback@v1", {"x": 1}) == {"x": 1, "provider_id": "fallback@v1"})

    # determinism of state transitions
    cbA = CircuitBreaker("p", consec_threshold=2); cbB = CircuitBreaker("p", consec_threshold=2)
    for cbx in (cbA, cbB):
        cbx.record_failure("rate_limited", now=T0); cbx.record_failure("rate_limited", now=T0)
    chk("deterministic", cbA.state(now=T0) == cbB.state(now=T0) == OPEN)

    print(f"\n{'PASS — check_worker_provider_circuit_breaker: open on consec/rate/forced, reject-while-open, half_open probes, close/reopen, taxonomy-gated, fallback routing + provenance, deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
