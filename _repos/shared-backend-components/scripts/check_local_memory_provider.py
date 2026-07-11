#!/usr/bin/env python3
"""scripts.check_local_memory_provider — proof: memory.baltor_local@v1 is a WORKING local memory provider.

Asserts a write→search→profile round-trip on the in-process content-addressed store: a written item is
recallable; its artifacts are content-addressed (same content → same id/hash, idempotent re-write); the
provider satisfies MemoryProviderPort + MemoryProfileProviderPort; status() reports available offline; and
every output is a governed candidate MemoryArtifact (claim_status="candidate", not served/canonical). Two
runs with the same injected time produce byte-identical artifacts (deterministic).

CLI: python3 _repos/shared-backend-components/scripts/check_local_memory_provider.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider  # noqa: E402
from src.baltor.ports.memory_provider import (  # noqa: E402
    CANDIDATE_CLAIM_STATUS,
    MEMORY_ARTIFACT_REQUIRED_FIELDS,
    MemoryProfileProviderPort,
    MemoryProviderPort,
)

_NOW = 1_700_000_000  # injected fixed time — no wall-clock


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    p = BaltorLocalMemoryProvider()
    check("satisfies MemoryProviderPort", isinstance(p, MemoryProviderPort))
    check("satisfies MemoryProfileProviderPort", isinstance(p, MemoryProfileProviderPort))

    st = p.status()
    check("status() == available offline", st["status"] == "available")
    check("status() needs no external credential", st["credential_ref"] is None and st["has_credentials"] is True)

    # write → search round-trip
    w = p.write({"tenant_id": "acme", "project": "default",
                 "content": "The Reg E dispute window is 10 days.", "now": _NOW})
    check("write returns a MemoryArtifact with all required governance fields",
          all(f in w for f in MEMORY_ARTIFACT_REQUIRED_FIELDS),
          str([f for f in MEMORY_ARTIFACT_REQUIRED_FIELDS if f not in w]))
    check("written artifact is claim_status=candidate (not served/canonical)",
          w["claim_status"] == CANDIDATE_CLAIM_STATUS and w["served"] is False and w["canonical"] is False)
    check("written artifact carries external_source_handle + lineage",
          bool(w["external_source_handle"]) and bool(w["lineage"]) and "provider_id" in w["lineage"])

    found = p.search({"tenant_id": "acme", "project": "default", "query": "Reg E dispute"})
    check("search recalls the written item", bool(found["results"]))
    check("recalled item matches by content_hash (round-trip)",
          bool(found["results"]) and found["results"][0]["content_hash"] == w["content_hash"])
    check("every search result is claim_status=candidate",
          all(r["claim_status"] == CANDIDATE_CLAIM_STATUS for r in found["results"]))

    # content-addressed + idempotent: re-writing identical content yields the SAME id, no duplicate
    w2 = p.write({"tenant_id": "acme", "project": "default",
                  "content": "The Reg E dispute window is 10 days.", "now": _NOW})
    check("re-write of identical content is content-addressed (same id)", w2["artifact_id"] == w["artifact_id"])
    again = p.search({"tenant_id": "acme", "project": "default", "query": "Reg E"})
    check("idempotent: identical content not duplicated", len(again["results"]) == 1)

    # profile static + dynamic
    p.write({"tenant_id": "acme", "project": "default", "content": "Vendor invoice 4471 is under review.",
             "now": _NOW + 5})
    prof = p.profile({"tenant_id": "acme", "project": "default", "now": _NOW + 10})
    check("profile returns static + dynamic lists", "static" in prof and "dynamic" in prof)
    check("profile dynamic is most-recent-first",
          bool(prof["dynamic"]) and prof["dynamic"][0]["content"] == "Vendor invoice 4471 is under review.")
    check("every profile entry is claim_status=candidate",
          all(e["claim_status"] == CANDIDATE_CLAIM_STATUS for e in prof["static"] + prof["dynamic"]))

    # determinism: a fresh provider + same injected time => identical artifact
    q = BaltorLocalMemoryProvider()
    w_again = q.write({"tenant_id": "acme", "project": "default",
                       "content": "The Reg E dispute window is 10 days.", "now": _NOW})
    check("deterministic: same content + same now => identical artifact across instances", w_again == w)

    print(f"\n{'PASS — check_local_memory_provider: memory.baltor_local@v1 writes/searches/profiles offline; outputs are content-addressed, idempotent, deterministic candidate MemoryArtifacts (never served/canonical).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Proof: the local memory provider write/search/profile round-trip.")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return _self_test()
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
