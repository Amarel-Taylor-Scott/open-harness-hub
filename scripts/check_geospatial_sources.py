"""check_geospatial_sources — proof for architecture/geospatial_sources.json (backs registry #77).

POINTER-ONLY catalog of public geospatial data sources (OSM/Census/NaturalEarth/GeoNames/WorldPop class).
Enforces required fields incl. LICENSE; access/cost enums; pointer-only (short ref, no bulk data); coverage
(>=10 sources across >=5 domains); serves_truth=false. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "geospatial_sources.json"
_REQ = ("id", "domain", "name", "returns", "access", "cost_tier", "jurisdiction", "license", "ref")
_ACCESS = {"free", "key", "paid"}
_COST = {"free", "freemium", "paid"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    sources = doc.get("sources", [])
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
    ck(">=10 sources", len(sources) >= 10, str(len(sources)))

    ids: set[str] = set()
    domains: set[str] = set()
    for s in sources:
        sid = s.get("id", "?")
        for f in _REQ:
            ck(f"{sid}: has '{f}'", bool(s.get(f)))
        ck(f"{sid}: unique id", sid not in ids, "duplicate")
        ids.add(sid)
        domains.add(s.get("domain", ""))
        ck(f"{sid}: access in {_ACCESS}", s.get("access") in _ACCESS, str(s.get("access")))
        ck(f"{sid}: cost_tier in {_COST}", s.get("cost_tier") in _COST, str(s.get("cost_tier")))
        ck(f"{sid}: ref is a short pointer string", isinstance(s.get("ref"), str) and len(s.get("ref", "")) < 80)
        ck(f"{sid}: stores no bulk data (pointer-only)", not any(isinstance(v, list) and len(v) > 3 for v in s.values()))

    ck(">=5 domains", len(domains) >= 5, str(sorted(domains)))

    if fails:
        print(f"\nFAIL - check_geospatial_sources: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_geospatial_sources: {len(sources)} pointer-only geospatial sources across {len(domains)} "
          f"domains ({sorted(domains)}); licensed; no data dump; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
