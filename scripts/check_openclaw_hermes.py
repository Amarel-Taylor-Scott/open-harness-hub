#!/usr/bin/env python3
"""check_openclaw_hermes — proof for the stateless OpenClaw (finder) + Hermes (router) discovery engines.

Proves: OpenClaw is stateless + plugin-based (a finder per hub/content kind); it descends unbounded→bounded when
picking a tool from the injected TOOL REPOSITORY; Hermes routes discovery into the right hub's engine (continuous
append); discovered items are GOVERNED candidates (serves_truth=false; not served until the hub verifies them); and a
sweep keeps every hub fresh. Offline (stub tools), deterministic, temp store.

CLI: PYTHONPATH=. python3 scripts/check_openclaw_hermes.py --self-test
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.openhubforai.component_store import ComponentStore
    from src.openhubforai.hub_engine import engines_for_all_hubs
    from src.openhubforai.discovery import OpenClaw, Hermes, default_plugins, stub_tools
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    import json
    strat = json.loads((REPO / "architecture" / "hub_population_strategy.json").read_text(encoding="utf-8"))["hubs"]
    oc = OpenClaw(default_plugins())
    tools = stub_tools()
    ck("OpenClaw is plugin-based: ONE finder per hub, auto-derived from the strategy (single source — covers all hubs)",
       {p.target_hub for p in oc.plugins} == set(strat) and len(oc.plugins) == len(strat))
    ck("plugin content kinds match the strategy (e.g. tools/skills/context/harnesses/compression)",
       {p.content_kind for p in oc.plugins} >= {"tools", "skills", "context", "harnesses", "compression"})

    # unbounded -> bounded tool DESCENT (OpenToolsHub declares tool_tier=api in the strategy)
    repo_plugin = next(p for p in oc.plugins if p.target_hub == "OpenToolsHub")
    picked = oc.pick_tool(repo_plugin, tools)
    ck("picks the MOST BOUNDED available tool (api over search/scrape) — the descent", picked.tier == "api", picked.tier)

    # discover is pure/stateless (same inputs -> same output; no state mutation)
    d1 = oc.discover("OpenToolsHub", "agent tools", tools=tools)
    d2 = oc.discover("OpenToolsHub", "agent tools", tools=tools)
    ck("OpenClaw.discover is STATELESS (identical inputs -> identical output)", d1 == d2 and len(d1) >= 2)
    ck("discovered items are tagged + governed (hub/kind/tool, serves_truth=false)",
       all(c["hub"] == "OpenToolsHub" and c["via_tool"] and c["serves_truth"] is False for c in d1))

    with tempfile.TemporaryDirectory() as tmp:
        store = ComponentStore(Path(tmp) / "c.jsonl")
        engines = engines_for_all_hubs(store)
        hermes = Hermes()
        r = hermes.handle("OpenToolsHub", "agent tools", openclaw=oc, hub_engines=engines, tools=tools)
        ck("Hermes routes discovery -> the hub engine ingest (continuous append)", r["discovered"] >= 2 and r["ingested"] == r["discovered"])
        # governance: discovered candidates are NOT served until the hub verifies them (discovery != trust)
        ck("discovered candidates are NOT served until verified (discovery≠trust)", store.serve("OpenToolsHub") == [])
        # but they ARE stored as versions (the hub can now verify + serve them)
        ids = {r["component_id"] for r in store._log.all(lambda x: x.get("kind") == "version" and x.get("hub") == "OpenToolsHub")}
        ck("...the candidates ARE appended as versions (ready for the hub's verify gate)", len(ids) >= 2)
        # re-route the same query -> idempotent (content-hash dedupe), no duplicate versions (stateless + lossless)
        before = store.stats()["versions"]
        hermes.handle("OpenToolsHub", "agent tools", openclaw=oc, hub_engines=engines, tools=tools)
        ck("re-discovery is idempotent (content-hash dedupe; no duplicate versions)", store.stats()["versions"] == before)
        # sweep keeps EVERY hub-with-a-plugin fresh
        sweep = hermes.sweep("fresh-2026", openclaw=oc, hub_engines=engines, tools=tools)
        ck("sweep routes across every hub that has a plugin", len(sweep) == len({p.target_hub for p in oc.plugins}) and all(s["ingested"] > 0 for s in sweep))

    print("\n" + ("PASS - check_openclaw_hermes: stateless OpenClaw (plugin finder, unbounded→bounded tool descent) + "
                  "Hermes (router) continuously discover + append to every Open*Hub via the injected tool repository; "
                  "items are governed candidates (serves_truth=false, served only after the hub verifies). Stateless + "
                  "idempotent + lossless."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_openclaw_hermes.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
