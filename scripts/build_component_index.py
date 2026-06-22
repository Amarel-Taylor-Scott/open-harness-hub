#!/usr/bin/env python3
"""build_component_index — label EVERY component (tools/ml-models/microsteps/planes/rungs/external-APIs) for search.

Walks all the registries and emits one search-index row per component {id, kind, text, keywords, vector} to the operational
component_search_index stream (data/dev-intel/component_search_index.jsonl), so the synthesizer can search + COMPOSE
components by meaning (src/teleon/synthesis/component_search.py). serves_truth=false. Dev-plane script.

  python3 scripts/build_component_index.py            # rebuild the index
  python3 scripts/build_component_index.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.teleon.synthesis.component_search import INDEX_PATH, index_entry

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def collect() -> list[dict]:
    rows, seen = [], set()
    def add(id, kind, text, keywords):
        key = f"{kind}:{id}"
        if id and key not in seen:
            seen.add(key); rows.append(index_entry(key, kind, text, keywords))
    for t in _load("tool_registry.json")["tools"]:
        add(t["id"], "tool", f"{t['name']} {t.get('plane','')}", [t.get("plane"), "tool"])
    for m in _load("ml_model_registry.json")["models"]:
        add(m["id"], "ml_model", f"{m['family']} {m.get('when_to_use','')}", [m.get("ml_task"), m.get("plane"), "ml_model"])
    for d in _load("rung_microsteps.json")["decompositions"]:
        for s in d["microsteps"]:
            add(f"{d['capability']}.{d['rung']}.{s['id']}", "microstep", s["does"], [s.get("primitive"), s.get("plane_hint"), "microstep"])
    for p in _load("tool_planes.json")["planes"]:
        add(p["plane"], "plane", f"{p['name']} {p.get('registry','')}", [p["plane"], "plane"])
    for l in _load("capability_ladders.json")["ladders"]:
        for r in l["rungs"]:
            add(f"{l['capability']}.{r['tier']}", "rung", f"{r['tier']} {r['method']}", [l["capability"], (r.get("planes") or [None])[0], "rung"])
    for a in _load("external_api_registry.json")["apis"]:
        add(a["id"], "external_api", a["name"], [a.get("plane"), a.get("marketplace"), "external_api"])
    return rows


def build() -> int:
    rows = collect()
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return len(rows)


def _self_test() -> int:
    rows = collect()
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    kinds = {r["kind"] for r in rows}
    ck("indexes ALL component kinds (tool/ml_model/microstep/plane/rung/external_api)",
       kinds == {"tool", "ml_model", "microstep", "plane", "rung", "external_api"})
    ck("substantial index (>=400 components)", len(rows) >= 400)
    ck("every row has text + keywords + a 256-d vector", all(r["text"] and r["keywords"] and len(r["vector"]) == 256 for r in rows))
    ck("ids unique", len({r["id"] for r in rows}) == len(rows))
    ck("serves_truth=false", all(r["serves_truth"] is False for r in rows))
    print("\n" + (f"PASS - build_component_index: {len(rows)} components labelled (text+keywords+vector) for search."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print(f"indexed {build()} components -> {INDEX_PATH.relative_to(REPO)}")
