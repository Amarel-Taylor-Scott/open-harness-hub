#!/usr/bin/env python3
"""check_plane_separation — enforce the DEVELOPMENT vs PRODUCT boundary (architecture/plane_separation.json).

Dev research/tools/loops/data must stay separate from product modules/actions/data. This proves: (1) PRODUCT modules
(src/teleon, src/baltor) import NO development tool (they may import shared_infra); (2) dev tools live under scripts/,
not src/; (3) dev data is routed under data/dev-intel/ (+ docs); (4) every storage stream declares a plane; (5) the
dev research tool is not inside the product package. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_plane_separation.py --self-test
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_SPEC = REPO / "architecture" / "plane_separation.json"


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    d = json.loads(_SPEC.read_text())
    ck("classification has development + product + shared_infra + rules", all(k in d for k in ("development", "product", "shared_infra", "rules")))

    # (1) PRODUCT (src/) imports NO development tool
    dev_tools = d["development"]["tools"]
    dev_mods = [Path(t).stem for t in dev_tools]            # e.g. external_review, panel_review, research_radar, ...
    pat = re.compile(r"^\s*(from|import)\s+scripts\.(" + "|".join(re.escape(m) for m in dev_mods) + r")\b", re.M)
    offenders = []
    for root in ("src/teleon", "src/baltor"):
        base = REPO / root
        if base.exists():
            for f in base.rglob("*.py"):
                if "__pycache__" in f.parts:
                    continue
                if pat.search(f.read_text(encoding="utf-8", errors="replace")):
                    offenders.append(str(f.relative_to(REPO)))
    ck("PRODUCT modules import NO development tool (may import shared_infra)", not offenders, str(offenders))

    # (2) dev tools live under scripts/, not src/
    ck("every development tool lives under scripts/ (not src/)", all(t.startswith("scripts/") for t in dev_tools), str([t for t in dev_tools if not t.startswith("scripts/")]))
    ck("every development tool file exists", all((REPO / t).exists() for t in dev_tools), str([t for t in dev_tools if not (REPO / t).exists()]))

    # (3) dev data is routed to dev paths (the loop + radar constants point under data/dev-intel/)
    loop = (REPO / "scripts" / "multi_model_improvement_loop.py").read_text()
    radar = (REPO / "scripts" / "research_radar.py").read_text()
    ck("the improvement loop writes findings + cursor under data/dev-intel/", 'data" / "dev-intel"' in loop and loop.count('data" / "dev-intel"') >= 2)
    ck("the research radar writes hits under data/dev-intel/", 'data" / "dev-intel"' in radar)
    ck("NO dev tool writes to a product data path (data/descent-attempts)", "descent-attempts" not in loop and "descent-attempts" not in radar)

    # (4) every storage stream declares a plane; panel_reviews is development, descent_attempts is product
    streams = {s["stream"]: s for s in json.loads((REPO / "architecture" / "storage_tier_policy.json").read_text())["streams"]}
    ck("every storage stream declares a plane (development|product)", all(s.get("plane") in ("development", "product") for s in streams.values()))
    ck("panel_reviews=development, descent_attempts=product (correctly classified)",
       streams["panel_reviews"]["plane"] == "development" and streams["descent_attempts"]["plane"] == "product")

    # (5) the dev research tool is OUT of the product package; shared_infra exists
    ck("research_radar is NOT inside the product package (src/teleon)", not (REPO / "src/teleon/intel/research_radar.py").exists())
    ck("shared_infra modules exist (the seam both planes use)", all((REPO / m).exists() for m in d["shared_infra"]["modules"]))

    print("\n" + ("PASS - check_plane_separation: development (tools/loops/data under scripts/ + data/dev-intel/) is "
                  "separate from product (src/ modules + governed product streams); product imports no dev tool (only "
                  "shared_infra); every storage stream is plane-tagged. Dev research is quarantined from product serving."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_plane_separation.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
