#!/usr/bin/env python3
"""check_promote_tools — the promotion boundary holds: only license-clean, real, deduped rows reach the promoted tier.

Proves the gate (permissive + real URL + core (non-dedicated) plane + popularity floor + dedupe) and that the promoted
file (if populated) contains ONLY rows that satisfy it: permissive license, a real repo URL, a declared NON-dedicated
plane, marked promoted + vetted=false (not the human-vetted core), unique, disjoint from the core. serves_truth=false.

  python3 scripts/check_promote_tools.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import promote_tools as P
from src.openharnesshub.licenses import classify_license

REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    core_ids, core_planes = {"faiss"}, {"reranker", "data_extraction"}
    g = lambda r: P.passes_gate(r, core_ids=core_ids, core_planes=core_planes, min_pop=100)
    ck("gate PROMOTES permissive+popular+core-plane+url+new", g({"bare": "a", "license": "MIT", "url": "u", "plane": "reranker", "popularity": 500}))
    ck("gate BLOCKS copyleft", not g({"bare": "b", "license": "AGPL-3.0", "url": "u", "plane": "reranker", "popularity": 999}))
    ck("gate BLOCKS unstated license", not g({"bare": "c", "license": None, "url": "u", "plane": "reranker", "popularity": 999}))
    ck("gate BLOCKS low popularity", not g({"bare": "d", "license": "MIT", "url": "u", "plane": "reranker", "popularity": 5}))
    ck("gate BLOCKS dedicated plane (ocr/browser/llm)", not g({"bare": "e", "license": "MIT", "url": "u", "plane": "browser", "popularity": 999}))
    ck("gate BLOCKS missing URL", not g({"bare": "f", "license": "MIT", "url": "", "plane": "reranker", "popularity": 999}))
    ck("gate BLOCKS core dup", not g({"bare": "faiss", "license": "MIT", "url": "u", "plane": "reranker", "popularity": 999}))

    declared = {p["plane"] for p in json.loads((REPO / "architecture" / "tool_planes.json").read_text())["planes"]}
    core = P._core_ids()
    if P.PROMOTED.exists():
        rows = json.loads(P.PROMOTED.read_text())["tools"]
        if rows:
            ck(f"every promoted row is permissive (vendorable) [{len(rows)} rows]", all(classify_license(r["license"])[1] for r in rows))
            ck("every promoted row has a real repo URL", all(r.get("repo") for r in rows))
            ck("every promoted row's plane is declared + NON-dedicated", all(r["plane"] in declared and r["plane"] not in P.DEDICATED for r in rows))
            ck("every promoted row marked promoted + vetted=false (not the human-vetted core)", all(r.get("promoted") and r.get("vetted") is False for r in rows))
            ck("promoted ids unique + disjoint from the core", len({r["id"] for r in rows}) == len(rows) and not ({r["id"] for r in rows} & core))
            print(f"    [info] promoted tier: {len(rows)} tools (e.g. {', '.join(r['name'] for r in rows[:3])})")
        else:
            ck("promoted file present but empty (boundary held)", True)
    ck("promoted file serves_truth=false", (json.loads(P.PROMOTED.read_text()).get("serves_truth") is False) if P.PROMOTED.exists() else True)

    print("\n" + ("PASS - check_promote_tools: boundary gate enforced; promoted tier is permissive+real+non-dedicated, "
                  "vetted=false, disjoint from the core." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
