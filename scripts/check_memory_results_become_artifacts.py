#!/usr/bin/env python3
"""scripts.check_memory_results_become_artifacts — proof (THE GOVERNANCE LINE): every memory-provider output
is a governed candidate MemoryArtifact, NEVER a served/canonical fact.

Across ALL providers (local + emulator working; api + mcp candidates), asserts that every write/search/profile
(and every MCP memory/recall/context) output is a MemoryArtifact carrying claim_status="candidate" + a
populated external_source_handle + lineage — and is explicitly NOT marked served/canonical/verified/promoted.
remembered != verified · retrieved != served · profiled != canonical · candidate memory != promoted fact.

The candidate api/mcp stubs (no creds) MUST raise UnavailableProvider naming env://SUPERMEMORY_API_KEY rather
than ever returning a non-candidate result — the only way they could "serve" is by failing closed.

CLI: python3 scripts/check_memory_results_become_artifacts.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider  # noqa: E402
from src.baltor.adapters.memory.supermemory_api import SupermemoryApiProvider  # noqa: E402
from src.baltor.adapters.memory.supermemory_emulator import SupermemoryEmulatorProvider  # noqa: E402
from src.baltor.adapters.memory.supermemory_mcp import SupermemoryMcpProvider  # noqa: E402
from src.baltor.ports.memory_provider import (  # noqa: E402
    CANDIDATE_CLAIM_STATUS,
    FORBIDDEN_CLAIM_STATUSES,
    MEMORY_ARTIFACT_REQUIRED_FIELDS,
    MEMORY_ARTIFACT_TYPE,
    UnavailableProvider,
)

_NOW = 1_700_000_000


def _is_governed_candidate(art: dict) -> tuple[bool, str]:
    """A memory output is governed iff: it's a memory_artifact, claim_status=candidate, has all required
    governance fields, carries external_source_handle + lineage, and is NOT served/canonical/verified."""
    if not isinstance(art, dict):
        return False, "not a dict"
    if art.get("artifact_type") != MEMORY_ARTIFACT_TYPE:
        return False, f"artifact_type={art.get('artifact_type')!r}"
    if art.get("claim_status") != CANDIDATE_CLAIM_STATUS:
        return False, f"claim_status={art.get('claim_status')!r}"
    if art.get("claim_status") in FORBIDDEN_CLAIM_STATUSES:
        return False, "claim_status is forbidden (served/canonical/...)"
    missing = [f for f in MEMORY_ARTIFACT_REQUIRED_FIELDS if not art.get(f) and f != "claim_status"]
    if missing:
        return False, f"missing/empty governance fields {missing}"
    if art.get("served") is not False or art.get("canonical") is not False:
        return False, "marked served/canonical"
    if not isinstance(art.get("lineage"), dict) or not art["lineage"].get("external_source_handle"):
        return False, "lineage missing external_source_handle"
    return True, ""


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── working providers: every output is a governed candidate artifact ──
    for label, prov in (("local", BaltorLocalMemoryProvider()), ("emulator", SupermemoryEmulatorProvider())):
        w = prov.write({"tenant_id": "acme", "project": "default", "content": "Wire limit is $50k/day.",
                        "now": _NOW})
        ok, why = _is_governed_candidate(w)
        check(f"{label}.write output is a governed candidate MemoryArtifact", ok, why)

        s = prov.search({"tenant_id": "acme", "project": "default", "query": "wire limit"})
        all_ok = all(_is_governed_candidate(r)[0] for r in s["results"])
        check(f"{label}.search outputs are ALL governed candidate MemoryArtifacts", all_ok and bool(s["results"]))

        pr = prov.profile({"tenant_id": "acme", "project": "default", "now": _NOW + 1})
        prof_ok = all(_is_governed_candidate(e)[0] for e in pr["static"] + pr["dynamic"])
        check(f"{label}.profile entries are ALL governed candidate MemoryArtifacts", prof_ok)

        # explicit NEGATIVE: no output is marked served/canonical/verified/promoted/fact
        for out in [w] + s["results"] + pr["static"] + pr["dynamic"]:
            if out.get("claim_status") in FORBIDDEN_CLAIM_STATUSES:
                check(f"{label}: NO output carries a forbidden (served/canonical) claim_status", False,
                      out.get("claim_status"))
                break
        else:
            check(f"{label}: NO output carries a forbidden (served/canonical) claim_status", True)

    # ── candidate stubs: fail CLOSED (UnavailableProvider), never return a non-candidate result ──
    api = SupermemoryApiProvider()
    for op_name, op in (("write", lambda: api.write({"tenant_id": "t", "project": "p", "content": "x", "now": _NOW})),
                        ("search", lambda: api.search({"tenant_id": "t", "project": "p", "query": "x"})),
                        ("profile", lambda: api.profile({"tenant_id": "t", "project": "p", "now": _NOW}))):
        raised = False
        named = ""
        try:
            op()
        except UnavailableProvider as e:
            raised, named = True, e.credential_ref
        check(f"api.{op_name} fails CLOSED with UnavailableProvider (never serves)", raised)
        check(f"api.{op_name} UnavailableProvider names env://SUPERMEMORY_API_KEY", named == "env://SUPERMEMORY_API_KEY")

    mcp = SupermemoryMcpProvider()
    for tool, op in (("memory", lambda: mcp.memory({})), ("recall", lambda: mcp.recall({})),
                     ("context", lambda: mcp.context({}))):
        raised = False
        named = ""
        try:
            op()
        except UnavailableProvider as e:
            raised, named = True, e.credential_ref
        check(f"mcp.{tool} fails CLOSED with UnavailableProvider (never serves)", raised)
        check(f"mcp.{tool} UnavailableProvider names env://SUPERMEMORY_API_KEY", named == "env://SUPERMEMORY_API_KEY")

    # negative-control: a hand-forged "served fact" is correctly REJECTED by the governance predicate
    forged = {"artifact_type": MEMORY_ARTIFACT_TYPE, "claim_status": "served", "tenant_id": "t", "project": "p",
              "external_source_handle": "mem://x", "lineage": {"external_source_handle": "mem://x"},
              "content_hash": "abc", "served": True, "canonical": True, "artifact_id": "x"}
    rejected, _ = _is_governed_candidate(forged)
    check("negative control: a forged served/canonical result is REJECTED by the governance predicate", not rejected)

    print(f"\n{'PASS — check_memory_results_become_artifacts: every provider output is a governed candidate MemoryArtifact (claim_status=candidate + external_source_handle + lineage, NOT served/canonical); candidate stubs fail closed naming their env:// credential; a forged served result is rejected.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Proof: memory results become candidate artifacts, never served facts.")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return _self_test()
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
