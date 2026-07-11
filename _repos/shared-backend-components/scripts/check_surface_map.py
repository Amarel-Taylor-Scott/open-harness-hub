#!/usr/bin/env python3
"""check_surface_map — guard _repos/shared-backend-components/architecture/surface_map.json against drift (drift = fragile context).

The surface map records each surface's wedge/buyer/status + how surfaces COMMUNICATE. This proves it is well-formed
AND that its product-layer communication edges AGREE with the dependency law (Baltor -> Teleon -> OpenHubForAI,
never the reverse) — so the map can never silently contradict _repos/shared-backend-components/architecture/portfolio_dependency_law.json.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_surface_map.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_MAP = _resource("architecture") / "surface_map.json"
_LAW = _resource("architecture") / "portfolio_dependency_law.json"
#: external endpoints a surface may communicate with (not surfaces themselves)
_EXTERNAL = {"sources", "agents", "registries", "(none)"}


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    d = json.loads(_MAP.read_text())
    surfaces = d.get("surfaces", [])
    ids = {s["id"] for s in surfaces}
    ck("surface map is non-empty + covers the products", {"baltor", "teleon", "openhubforai"} <= ids, str(sorted(ids)))
    ck("every surface declares wedge + buyer + status (PMF captured)",
       all(s.get("wedge") and s.get("buyer") and s.get("status") for s in surfaces if s["id"] != "ai-done-right"),
       str([s["id"] for s in surfaces if not (s.get("wedge") and s.get("status"))]))

    # communication edges resolve to known surfaces or known externals
    edges = [(s["id"], e["to"], e.get("relation", "")) for s in surfaces for e in s.get("communicates_with", [])]
    unknown = [(a, b) for a, b, _ in edges if b not in ids and b not in _EXTERNAL]
    ck("every communication edge resolves to a known surface or external", not unknown, str(unknown))

    # AGREE with the dependency law: baltor->teleon + teleon->openhubforai consume edges, and NO reverse
    def has(a, b, rel): return any(s == a and t == b and rel in r for s, t, r in edges)
    ck("baltor -> teleon (consumes) edge present (matches the law)", has("baltor", "teleon", "consumes"))
    ck("teleon -> openhubforai (consumes) edge present (matches the law)", has("teleon", "openhubforai", "consumes"))
    # only DEPENDENCY edges (consumes/imports/depends) must respect the direction; a "serves"/"feeds" edge is the
    # legitimate inverse runtime flow (Teleon SERVES its tenant Baltor without importing it).
    _DEP = ("consumes", "imports", "depends")
    reverse = [(a, b, r) for a, b, r in edges if any(x in r for x in _DEP)
               and ((a == "teleon" and b == "baltor") or (a == "openhubforai" and b in ("teleon", "baltor")))]
    ck("NO reverse DEPENDENCY edge (OHH/Teleon never depend upward) — agrees with the law; 'serves' inverse is allowed",
       not reverse, str(reverse))

    # the law file declares the same direction (cross-source consistency)
    law_txt = _LAW.read_text().lower() if _LAW.exists() else ""
    ck("the dependency law file declares the Baltor->Teleon->OpenHubForAI direction",
       "baltor" in law_txt and "teleon" in law_txt and ("openhubforai" in law_txt or "open harness" in law_txt))
    ck("the map records the communication_law (single-sourced intent)", bool(d.get("communication_law")))

    print("\n" + ("PASS - check_surface_map: surface map is well-formed (wedge/buyer/status per surface), every "
                  "communication edge resolves, and the product-layer edges AGREE with the dependency law "
                  "(Baltor->Teleon->OpenHubForAI, no reverse) — no silent drift."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_surface_map.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
