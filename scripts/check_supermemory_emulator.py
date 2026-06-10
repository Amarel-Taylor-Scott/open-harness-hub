#!/usr/bin/env python3
"""scripts.check_supermemory_emulator — proof: memory.supermemory_emulator@v1 is the working offline impl.

Asserts the deterministic Supermemory emulator satisfies MemoryProviderPort + MemoryProfileProviderPort with
NO credentials and NO network: status()=="emulated" (available offline), write/search/profile round-trip
works, every output is a governed candidate MemoryArtifact (claim_status="candidate" + external_source_handle
+ lineage, never served/canonical), and two runs with the same injected time are byte-identical. Also asserts
the emulator imports NO third-party SDK and makes NO network call (source scan), AND that the credential-less
candidate api/mcp stubs raise UnavailableProvider so the CORRECTNESS INVARIANT (emulator) is what runs offline.

CLI: python3 scripts/check_supermemory_emulator.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.adapters.memory.supermemory_emulator import SupermemoryEmulatorProvider  # noqa: E402
from src.baltor.ports.memory_provider import (  # noqa: E402
    CANDIDATE_CLAIM_STATUS,
    MEMORY_ARTIFACT_REQUIRED_FIELDS,
    MemoryProfileProviderPort,
    MemoryProviderPort,
    UnavailableProvider,
)

_NOW = 1_700_000_000  # injected fixed time
#: forbidden in any memory adapter source — no SDK import, no network primitive.
_FORBIDDEN_SRC = (r"^\s*import supermemory", r"^\s*from supermemory", r"\brequests\.", r"\burllib\.request\b",
                  r"\bhttp\.client\b", r"\bsocket\.", r"\bhttpx\b", r"\baiohttp\b")
_MEMORY_ADAPTER_DIR = _REPO / "src" / "baltor" / "adapters" / "memory"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    p = SupermemoryEmulatorProvider()
    check("emulator satisfies MemoryProviderPort", isinstance(p, MemoryProviderPort))
    check("emulator satisfies MemoryProfileProviderPort", isinstance(p, MemoryProfileProviderPort))

    st = p.status()
    check("status() == emulated (available offline)", st["status"] == "emulated")
    check("emulator needs NO credentials", st["has_credentials"] is True and st["credential_ref"] is None)
    check("emulator names the would-be live credential ref", st["emulates_credential_ref"] == "env://SUPERMEMORY_API_KEY")

    w = p.write({"tenant_id": "acme", "project": "default",
                 "content": "Sanctions list updated for entity OFAC-123.", "now": _NOW})
    check("write returns a MemoryArtifact with all required governance fields",
          all(f in w for f in MEMORY_ARTIFACT_REQUIRED_FIELDS))
    check("written artifact is claim_status=candidate (not served/canonical)",
          w["claim_status"] == CANDIDATE_CLAIM_STATUS and w["served"] is False and w["canonical"] is False)
    check("external_source_handle records supermemory-ish upstream id",
          "sm_" in w["external_source_handle"] and w["lineage"]["upstream_id"].startswith("sm_"))

    found = p.search({"tenant_id": "acme", "project": "default", "query": "sanctions OFAC"})
    check("search recalls the written item (round-trip)",
          bool(found["results"]) and found["results"][0]["content_hash"] == w["content_hash"])
    check("results carry a deterministic relevance_score",
          bool(found["results"]) and isinstance(found["results"][0]["relevance_score"], float))
    check("every search result is claim_status=candidate",
          all(r["claim_status"] == CANDIDATE_CLAIM_STATUS for r in found["results"]))

    prof = p.profile({"tenant_id": "acme", "project": "default", "now": _NOW + 10})
    check("profile returns static + dynamic (supermemory shape)", "static" in prof and "dynamic" in prof)
    check("every profile entry is claim_status=candidate",
          all(e["claim_status"] == CANDIDATE_CLAIM_STATUS for e in prof["static"] + prof["dynamic"]))

    # determinism
    q = SupermemoryEmulatorProvider()
    w2 = q.write({"tenant_id": "acme", "project": "default",
                  "content": "Sanctions list updated for entity OFAC-123.", "now": _NOW})
    check("deterministic: same content + same now => identical artifact across instances", w2 == w)

    # NO SDK / NO network in any memory adapter source
    offenders: list[str] = []
    for f in sorted(_MEMORY_ADAPTER_DIR.glob("*.py")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        for pat in _FORBIDDEN_SRC:
            if re.search(pat, text, re.M):
                offenders.append(f"{f.name}:{pat}")
    check("NO memory adapter imports a supermemory SDK or a network primitive", offenders == [], str(offenders))

    # CORRECTNESS INVARIANT is offline: the candidate api/mcp stubs are unavailable with no creds
    from src.baltor.adapters.memory.supermemory_api import SupermemoryApiProvider
    from src.baltor.adapters.memory.supermemory_mcp import SupermemoryMcpProvider
    api_raised = mcp_raised = False
    try:
        SupermemoryApiProvider().search({"tenant_id": "acme", "project": "default", "query": "x"})
    except UnavailableProvider:
        api_raised = True
    try:
        SupermemoryMcpProvider().recall({"tenant_id": "acme", "project": "default", "query": "x"})
    except UnavailableProvider:
        mcp_raised = True
    check("candidate api stub is UNAVAILABLE with no creds (correctness invariant uses emulator)", api_raised)
    check("candidate mcp stub is UNAVAILABLE with no creds (correctness invariant uses emulator)", mcp_raised)

    print(f"\n{'PASS — check_supermemory_emulator: the deterministic emulator is the working offline contract impl (status=emulated, no creds, no SDK, no network); outputs are candidate MemoryArtifacts; credential-less api/mcp stubs are unavailable so the correctness invariant runs offline.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Proof: the Supermemory emulator is the working offline impl.")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return _self_test()
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
