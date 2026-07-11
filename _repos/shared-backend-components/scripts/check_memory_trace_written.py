#!/usr/bin/env python3
"""scripts.check_memory_trace_written — proof (C-MEM-1): every Memory-API provider call records a MemoryTrace.
A trace is the audit record that a recall happened; it carries the provider id, op, tenant scope, result
count, and claim_status=candidate (a trace records a CANDIDATE recall, never a served fact). Deterministic
(injected time, hashlib ids, no RNG); offline; resets the in-process trace projection so the count is exact.

CLI: python3 _repos/shared-backend-components/scripts/check_memory_trace_written.py --self-test
"""
from __future__ import annotations

import argparse

import scripts.api_memory_handler as mem
from scripts.api_memory_handler import CANDIDATE, handle

#: every MemoryTrace must carry these keys.
_TRACE_KEYS = {"schema_version", "trace_id", "seq", "provider_id", "op", "tenant_id",
               "result_count", "claim_status", "recorded_at"}
#: routes whose handling makes a provider call (each MUST leave a trace). connectors/providers read static
#: catalogs / module presence and intentionally do not emit a per-call trace.
_CALLING_ROUTES = ("/api/memory/artifacts", "/api/memory/profile", "/api/memory/search")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # deterministic: clear the in-process trace projection so counts are exact (no durable store touched).
    mem._TRACES.clear()
    check("trace projection starts empty", len(mem._TRACES) == 0)

    # each provider-calling route records exactly one new trace per call.
    for i, route in enumerate(_CALLING_ROUTES, start=1):
        handle("GET", route, {"tenant_id": "demo", "q": "policy"})
        check(f"{route} leaves a MemoryTrace (cumulative count == {i})", len(mem._TRACES) == i, str(len(mem._TRACES)))

    # every trace is well-formed: required keys, candidate status, injected time, deterministic id.
    for t in mem._TRACES:
        check(f"trace {t.get('trace_id')} has all required keys", _TRACE_KEYS <= set(t), str(sorted(set(t))))
        check(f"trace {t.get('trace_id')} is claim_status=candidate (records a candidate recall)",
              t.get("claim_status") == CANDIDATE)
        check(f"trace {t.get('trace_id')} uses injected deterministic time", t.get("recorded_at") == mem._NOW)
        check(f"trace {t.get('trace_id')} id is hashlib-derived (mtr- + 16 hex)",
              isinstance(t.get("trace_id"), str) and t["trace_id"].startswith("mtr-") and len(t["trace_id"]) == 20)

    # determinism: identical call sequence yields identical trace ids (no RNG, injected time).
    ids_a = [t["trace_id"] for t in mem._TRACES]
    mem._TRACES.clear()
    for route in _CALLING_ROUTES:
        handle("GET", route, {"tenant_id": "demo", "q": "policy"})
    ids_b = [t["trace_id"] for t in mem._TRACES]
    check("trace ids are deterministic across identical runs", ids_a == ids_b, f"{ids_a} != {ids_b}")

    # the /api/memory/traces route projects exactly the recorded traces and is tenant-scoped.
    _, payload = handle("GET", "/api/memory/traces", {"tenant_id": "demo"})
    check("/api/memory/traces projects the recorded traces", payload.get("total") == len(mem._TRACES), str(payload.get("total")))
    _, other = handle("GET", "/api/memory/traces", {"tenant_id": "other-tenant"})
    check("traces are tenant-scoped (no cross-tenant leakage)", other.get("total") == 0, str(other.get("total")))

    print(f"\n{'PASS — check_memory_trace_written: every provider-calling Memory-API route records a well-formed MemoryTrace (required keys, claim_status=candidate, injected time, deterministic hashlib id); traces are tenant-scoped and deterministic across runs.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: every memory provider call records a MemoryTrace.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
