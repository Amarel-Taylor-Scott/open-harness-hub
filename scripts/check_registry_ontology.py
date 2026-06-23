"""check_registry_ontology — grounding proof for architecture/registry_ontology.json.

The registry ontology is the registry-of-registries: it indexes the load-bearing knowledge registries and claims
a REAL backing module/file for each. The load-bearing invariant is that those claims are TRUE — a 'live'/'partial'
registry must name backing paths that actually exist on disk, so the map can never drift into describing modules we
don't have (the anti-hallucination rail for an architecture map).

Enforces:
  - every live/partial registry names >=1 backing path, and EVERY backing path exists on disk;
  - a 'gap' registry names NO backing (stay honest: a gap is a gap);
  - status in {live,partial,gap}; stage in the declared set; ids unique; maps_to_hub (when set) is a real hub in
    hub_profiles.json; partial/gap entries carry a gap_to_close note;
  - the universal interface declares its verbs and the universal object its fields; serves_truth=false.

Counts are computed, never hand-typed. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ONT = _REPO / "architecture" / "registry_ontology.json"
_PROFILES = _REPO / "architecture" / "hub_profiles.json"

_STATUS = {"live", "partial", "gap"}
_STAGES = {"pre_llm", "model", "post_llm", "runtime", "cross_cutting"}
_REQ_FIELDS = ("n", "id", "holds", "status", "stage", "maps_to_hub", "backing")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="print every assertion; exit nonzero on any failure")
    args = ap.parse_args()

    doc = json.loads(_ONT.read_text())
    hubs = set(json.loads(_PROFILES.read_text()).get("profiles", {}))

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
    ck("universal_interface declares verbs", len(doc.get("universal_interface", {}).get("verbs", {})) >= 8)
    ck("universal_object declares fields", len(doc.get("universal_object", {}).get("fields", [])) >= 8)

    regs = doc.get("registries", [])
    ck(">=30 registries indexed", len(regs) >= 30, str(len(regs)))

    ids: set[str] = set()
    for r in regs:
        rid = r.get("id", "?")
        for f in _REQ_FIELDS:
            ck(f"{rid}: has '{f}'", f in r)
        ck(f"{rid}: unique id", rid not in ids, "duplicate")
        ids.add(rid)
        ck(f"{rid}: status in {_STATUS}", r.get("status") in _STATUS, str(r.get("status")))
        ck(f"{rid}: stage in stages", r.get("stage") in _STAGES, str(r.get("stage")))

        hub = r.get("maps_to_hub")
        ck(f"{rid}: maps_to_hub is a real hub or null", hub is None or hub in hubs, str(hub))

        backing = r.get("backing", [])
        ck(f"{rid}: backing is a list", isinstance(backing, list))
        status = r.get("status")
        if status in {"live", "partial"}:
            ck(f"{rid}: live/partial names >=1 backing path", len(backing) >= 1)
            for p in backing:
                ck(f"{rid}: backing path exists '{p}'", (_REPO / p).exists())
        elif status == "gap":
            ck(f"{rid}: gap names NO backing (stay honest)", len(backing) == 0, str(backing))
        if status in {"partial", "gap"}:
            ck(f"{rid}: partial/gap carries gap_to_close", bool(r.get("gap_to_close")))

    # computed coverage — never hand-typed
    n_live = sum(1 for r in regs if r.get("status") == "live")
    n_partial = sum(1 for r in regs if r.get("status") == "partial")
    n_gap = sum(1 for r in regs if r.get("status") == "gap")

    if fails:
        print(f"\nFAIL - check_registry_ontology: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_ontology: {len(regs)} registries indexed, every backing path grounded on disk "
          f"({n_live} live + {n_partial} partial + {n_gap} gap); {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
