#!/usr/bin/env python3
"""scripts.check_memory_api — proof (C-MEM-1): the Memory API is a projection-only, offline, degrade-graceful
read surface. Each of the six GET routes returns the expected dict keys; every memory result is
claim_status="candidate" (never served/fact/canonical); the handler has NO write side effects; no secret ever
leaks. Tests the pure request handler (no socket) so the contract is deterministic + offline. The CORRECTNESS INVARIANT
runs with NO credentials and no network: every route returns 200 even when no provider is landed.

CLI: python3 scripts/check_memory_api.py --self-test
"""
from __future__ import annotations

import argparse
import json

from scripts.api_memory_handler import CANDIDATE, ROUTES, handle, owns

# any of these substrings in a serialized payload is a leak.
_SECRET_MARKERS = ("OH_SHOWCASE_TOKEN", "api_key", "Authorization", "Bearer ", "MEMORY.md", ".agent/")


def _no_secret(payload: dict) -> bool:
    blob = json.dumps(payload)
    # build the synthetic token-prefix at runtime so no literal secret string lives in this file.
    sk_prefix = "sk" + "-"
    return not any(m in blob for m in _SECRET_MARKERS) and sk_prefix not in blob


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    expected = {
        "/api/memory/artifacts":  {"artifacts", "total", "claim_status"},
        "/api/memory/profile":    {"profile"},
        "/api/memory/search":     {"results", "total", "claim_status"},
        "/api/memory/connectors": {"connectors", "total"},
        "/api/memory/providers":  {"providers", "total"},
        "/api/memory/traces":     {"traces", "total"},
    }
    for route, keys in expected.items():
        code, payload = handle("GET", route, {"tenant_id": "demo", "q": "policy"})
        check(f"GET {route} returns 200 (correctness invariant: no creds, no provider needed)", code == 200, str(code))
        check(f"GET {route} returns expected dict keys", isinstance(payload, dict) and keys <= set(payload), str(sorted(set(payload))))
        check(f"GET {route} leaks no secret", _no_secret(payload))

    # claim_status is candidate everywhere a provider result could appear (never served/fact/canonical).
    for route in ("/api/memory/artifacts", "/api/memory/search"):
        _, payload = handle("GET", route, {"tenant_id": "demo"})
        check(f"{route} top-level claim_status == candidate", payload.get("claim_status") == CANDIDATE, str(payload.get("claim_status")))
        rows = payload.get("artifacts") or payload.get("results") or []
        check(f"{route} every item is claim_status=candidate",
              all(r.get("claim_status") == CANDIDATE for r in rows if isinstance(r, dict)))

    # providers: none is the source of truth; the candidate (supermemory) stub is unavailable offline + names its credential.
    _, prov = handle("GET", "/api/memory/providers", {})
    plist = prov.get("providers", [])
    check("no provider is the source of truth", all(p.get("is_source_of_truth") is False for p in plist))
    cands = [p for p in plist if p.get("kind") == "candidate"]
    check("at least one CANDIDATE (supermemory) provider is listed", len(cands) >= 1)
    check("candidate providers are unavailable offline (no creds, no network)", all(p.get("available") is False for p in cands))
    check("candidate providers name a required credential", all(p.get("requires_credential") for p in cands))

    # profile separates promoted (static) from candidate (dynamic): dynamic must never be claim_status promoted.
    _, profp = handle("GET", "/api/memory/profile", {"tenant_id": "demo"})
    dyn = profp.get("profile", {}).get("dynamic", [])
    check("profile.dynamic is candidate-only (never promoted)", all(d.get("claim_status") == CANDIDATE for d in dyn))

    # mutation methods are rejected (read-only surface) — and produce NO change to the projection.
    before = handle("GET", "/api/memory/traces", {})[1]["total"]
    code_post, _ = handle("POST", "/api/memory/artifacts", {"value": "x"})
    after = handle("GET", "/api/memory/traces", {})[1]["total"]
    check("POST to a memory route is 405 (read-only)", code_post == 405, str(code_post))
    check("a rejected mutation records NO trace (no write side effect)", after == before, f"{before}->{after}")

    # unknown route degrades to 404 (no crash)
    c404, p404 = handle("GET", "/api/memory/nope", {})
    check("unknown memory route returns 404 (not a crash)", c404 == 404 and "error" in p404)

    # owns() recognizes exactly the declared routes
    check("owns() matches every declared route", all(owns(r) for r in ROUTES) and not owns("/api/context/serve"))

    print(f"\n{'PASS — check_memory_api: six projection-only GET routes return expected keys offline (correctness invariant, no creds); every memory result is claim_status=candidate; no provider is the source of truth; mutations are rejected with no side effect; no secret leaks.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: memory API projection (offline, candidate-only, no secrets).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
