"""check_lookup_portals — proof for architecture/lookup_portals.json (backs registry #72 lookup_portals).

A META, POINTER-ONLY catalog: each portal says WHERE to look up an authoritative FACT (a license / property /
tax-address / weather / sanctions record) and how to access it — NEVER a copy of the data. Enforces:
  - every portal carries id / domain / name / returns / access / cost_tier / jurisdiction / plane / authority / ref;
  - access in {free,key,paid}; cost_tier in {free,freemium,paid}; ids unique;
  - it is a POINTER catalog: every portal has a short string `ref` (an endpoint pointer) and NO bulk data array
    (no field is a list of records) — so it can't quietly become a data dump;
  - cross-domain coverage (>=10 portals across >=6 domains); serves_truth=false.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "lookup_portals.json"
_REQ = ("id", "domain", "name", "returns", "access", "cost_tier", "jurisdiction", "plane", "authority", "ref")
_ACCESS = {"free", "key", "paid"}
_COST = {"free", "freemium", "paid"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="print every failure; exit nonzero on any failure")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    portals = doc.get("portals", [])
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck(">=10 portals", len(portals) >= 10, str(len(portals)))

    ids: set[str] = set()
    domains: set[str] = set()
    for p in portals:
        pid = p.get("id", "?")
        for f in _REQ:
            ck(f"{pid}: has '{f}'", bool(p.get(f)))
        ck(f"{pid}: unique id", pid not in ids, "duplicate")
        ids.add(pid)
        domains.add(p.get("domain", ""))
        ck(f"{pid}: access in {_ACCESS}", p.get("access") in _ACCESS, str(p.get("access")))
        ck(f"{pid}: cost_tier in {_COST}", p.get("cost_tier") in _COST, str(p.get("cost_tier")))
        # pointer-only: ref is a short string endpoint pointer, and NO field is a bulk list of records.
        ck(f"{pid}: ref is a short pointer string", isinstance(p.get("ref"), str) and len(p.get("ref", "")) < 120)
        ck(f"{pid}: stores no bulk data (pointer-only)", not any(isinstance(v, list) and len(v) > 3 for v in p.values()))

    ck(">=6 domains covered", len(domains) >= 6, str(sorted(domains)))

    if fails:
        print(f"\nFAIL - check_lookup_portals: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_lookup_portals: {len(portals)} pointer-only lookup portals across {len(domains)} domains "
          f"({sorted(domains)}); access/cost enums valid; no data dump; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
