#!/usr/bin/env python3
"""check_capability_taxonomy — the capability HIERARCHY + the TOOL-PLANE index are well-formed and honestly wired.

Proves: capabilities form a domain → capability → sub-capability tree; every MAPPED leaf's task_id is a real
tunable-task (runnable today); CANDIDATE leaves are honest (no fake task_id); every tool_plane a leaf names is declared
in tool_planes.json; every WIRED plane's port_module file exists, gaps/partials have none; and the tree spans well beyond
the runnable set (real unbounded AI uses queued for grids). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_capability_taxonomy.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
TAX = _resource("architecture") / "capability_taxonomy.json"
PLANES = _resource("architecture") / "tool_planes.json"
CATALOG = _resource("architecture") / "tunable_task_catalog.json"


def _leaves(tax: dict) -> list:
    return [leaf for d in tax["domains"] for c in d["capabilities"] for leaf in c["sub"]]


def _self_test() -> int:
    tax = json.loads(TAX.read_text(encoding="utf-8"))
    planes = json.loads(PLANES.read_text(encoding="utf-8"))
    task_ids = {t["task_id"] for t in json.loads(CATALOG.read_text(encoding="utf-8"))["tasks"]}
    plane_ids = {p["plane"] for p in planes["planes"]}
    leaves = _leaves(tax)
    mapped = [L for L in leaves if L.get("status") == "mapped"]
    cand = [L for L in leaves if L.get("status") == "candidate"]
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"hierarchy is a tree ({len(tax['domains'])} domains, {sum(len(d['capabilities']) for d in tax['domains'])} "
       f"capabilities, {len(leaves)} sub-capabilities)", len(tax["domains"]) >= 4 and len(leaves) >= 30)
    bad_map = [L["id"] for L in mapped if L.get("task_id") not in task_ids]
    ck("every MAPPED leaf points at a real tunable-task (runnable today)", not bad_map, str(bad_map))
    bad_cand = [L["id"] for L in cand if L.get("task_id")]
    ck("every CANDIDATE leaf is honest (no fake task_id)", not bad_cand, str(bad_cand))
    ck(f"all {len(task_ids)} runnable tasks are placed in the tree (no orphan capability)",
       {L.get("task_id") for L in mapped} >= task_ids, str(task_ids - {L.get("task_id") for L in mapped}))
    bad_plane = sorted({pl for L in leaves for pl in L.get("tool_planes", []) if pl not in plane_ids})
    ck("every tool_plane a leaf names is DECLARED in tool_planes.json", not bad_plane, str(bad_plane))
    ck(f"the tree spans BEYOND runnable ({len(mapped)} mapped + {len(cand)} candidate uses to build grids for)", len(cand) >= 10)

    # tool planes honest: wired → port exists; non-wired → no port_module
    pmiss = [p["plane"] for p in planes["planes"] if p["status"] == "wired"
             and not (p.get("port_module") and (_resource(p["port_module"])).exists())]
    ck("every WIRED tool-plane's port_module file exists (ocr/llm/browser real)", not pmiss, str(pmiss))
    pbad = [p["plane"] for p in planes["planes"] if p["status"] in ("gap", "partial") and p.get("port_module")]
    ck("gap/partial planes are honest (no claimed port)", not pbad, str(pbad))
    wired = [p["plane"] for p in planes["planes"] if p["status"] == "wired"]
    ck("the OCR insight is generalized: many planes declared, supervisor-selectable, scaling to hundreds",
       len(planes["planes"]) >= 12 and {"ocr", "llm", "browser"} <= set(wired)
       and all(p.get("supervisor_selectable") for p in planes["planes"]))
    ck("serves_truth=false", tax.get("serves_truth") is False and planes.get("serves_truth") is False)

    print("\n" + (f"PASS - check_capability_taxonomy: {len(leaves)} sub-capabilities in a {len(tax['domains'])}-domain tree "
                  f"({len(mapped)} runnable + {len(cand)} candidate uses); each draws on declared TOOL PLANES "
                  f"({len(wired)} wired, rest queued); the OCR-style agnostic wrapper generalized across {len(planes['planes'])} "
                  "planes. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
