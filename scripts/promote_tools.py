#!/usr/bin/env python3
"""promote_tools — the PROMOTION BOUNDARY: lift vetted staged rows into the auto-promoted tier the descent can read.

staged (candidate) -> promoted requires ALL of: permissive license (vendorable), a real source URL, a classified plane
that the core covers (NOT a dedicated-registry plane: ocr/browser/llm have their own registries), a popularity floor
(a quality signal), and dedupe-clean vs the core + the promoted tier. Promoted rows go to architecture/tool_registry_
promoted.json marked {promoted, vetted:false} — they're core-READABLE but NOT the hand-curated, human-vetted core
(determinism unknown for a scraped repo, so we don't fabricate the flag). A human vetting pass moves promoted -> the core.
Lossless: staging is untouched. serves_truth=false; discovery≠trust.

  python3 scripts/promote_tools.py --run            # promote everything in staging that passes the gate
  python3 scripts/promote_tools.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.openharnesshub.licenses import classify_license

REPO = Path(__file__).resolve().parents[1]
STAGING = REPO / "data" / "dev-intel" / "tool_registry_staging.jsonl"
PROMOTED = REPO / "architecture" / "tool_registry_promoted.json"
DEDICATED = {"ocr", "browser", "llm"}            # have their own registries — not promoted into the core's scope
MIN_POPULARITY = 100                             # GitHub-stars quality floor (a vetting signal)


def _core_ids() -> set[str]:
    reg = json.loads((REPO / "architecture" / "tool_registry.json").read_text())["tools"]
    norm = lambda n: n.split("/")[-1].strip().lower().replace("-", "_").replace(".", "_")
    return {t["id"] for t in reg} | {norm(t["name"]) for t in reg}


def _core_planes() -> set[str]:
    planes = {p["plane"] for p in json.loads((REPO / "architecture" / "tool_planes.json").read_text())["planes"]}
    return planes - DEDICATED


def _promoted() -> list[dict]:
    return json.loads(PROMOTED.read_text())["tools"] if PROMOTED.exists() else []


def passes_gate(row: dict, *, core_ids: set, core_planes: set, min_pop: int = MIN_POPULARITY) -> bool:
    """The promotion boundary, applied to one staged row."""
    cls, vend = classify_license(row.get("license"))
    return bool(
        vend and cls == "permissive"                         # permissive -> vendorable
        and row.get("url")                                   # real source
        and row.get("plane") in core_planes                  # a core-covered, non-dedicated plane
        and (row.get("popularity") or 0) >= min_pop          # quality floor
        and row.get("bare") not in core_ids                  # dedupe vs core
    )


def promote(min_pop: int = MIN_POPULARITY) -> dict:
    if not STAGING.exists():
        return {"promoted": 0, "total_promoted": 0, "considered": 0}
    staged = [json.loads(l) for l in STAGING.read_text().splitlines() if l.strip()]
    core_ids, core_planes = _core_ids(), _core_planes()
    have = {t["id"] for t in _promoted()}
    promoted = _promoted()
    added = 0
    for r in staged:
        if r["id"] in have or r["bare"] in {p["id"] for p in promoted}:
            continue
        if passes_gate(r, core_ids=core_ids, core_planes=core_planes, min_pop=min_pop):
            promoted.append({"id": r["bare"], "plane": r["plane"], "name": r["name"], "license": r["license"],
                             "repo": r["url"], "popularity": r.get("popularity"), "promoted": True, "vetted": False,
                             "source": "staged_harvest"})
            have.add(r["bare"]); added += 1
    PROMOTED.write_text(json.dumps({"version": "0.1.0", "updated": "2026-06-22",
        "principle": "Auto-PROMOTED tier: staged rows that passed the boundary (permissive + real URL + core plane + "
                     "popularity + dedupe). Core-readable but vetted=false (determinism unknown for a scraped repo). A "
                     "human vetting pass moves these into the hand-curated tool_registry.json. serves_truth=false.",
        "serves_truth": False, "tools": promoted}, indent=2) + "\n")
    return {"promoted": added, "total_promoted": len(promoted), "considered": len(staged)}


def _self_test() -> int:
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    core_ids, core_planes = {"faiss"}, {"reranker", "data_extraction", "classical_ml"}
    g = lambda r: passes_gate(r, core_ids=core_ids, core_planes=core_planes, min_pop=100)
    ck("permissive + popular + core-plane + url + new -> PROMOTE", g({"bare": "x", "license": "MIT", "url": "u", "plane": "reranker", "popularity": 500}))
    ck("copyleft -> blocked", not g({"bare": "y", "license": "GPL-3.0", "url": "u", "plane": "reranker", "popularity": 500}))
    ck("low popularity -> blocked", not g({"bare": "z", "license": "MIT", "url": "u", "plane": "reranker", "popularity": 3}))
    ck("dedicated plane (ocr) -> blocked (has its own registry)", not g({"bare": "w", "license": "MIT", "url": "u", "plane": "ocr", "popularity": 999}))
    ck("no url -> blocked", not g({"bare": "v", "license": "MIT", "url": "", "plane": "reranker", "popularity": 999}))
    ck("dup of core -> blocked", not g({"bare": "faiss", "license": "MIT", "url": "u", "plane": "vector_store", "popularity": 999}))
    print("\n" + ("PASS - promote_tools: boundary gate (permissive+url+core-plane+popularity+dedupe); promoted tier vetted=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print(json.dumps(promote(), indent=2))
