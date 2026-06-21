#!/usr/bin/env python3
"""hub_engine_runner — the per-hub orchestrator / supervisor surface (run the 22 Open*Hub engines).

Thin wrapper over src.openharnesshub.hub_engine: instantiate ONE shared HubEngine per registry hub, run its lifecycle
cycle (scrape→ingest→digest→verify→serve), and report served counts + the lead-gen/substrate funnel. In production,
inject per-hub scraper + model ports (a real source poller + scripts._llm_client); here it runs over the durable store.
DEVELOPMENT plane (the operator surface); the engines + store are PRODUCT (src/openharnesshub).

  --hub <HubId>   run one hub's cycle      --all   run a cycle for every hub
  --feed [HubId]  print the substrate_feed (what Teleon/Baltor consume)
  --self-test     offline: the runner wires every hub + runs a cycle
CLI: PYTHONPATH=. python3 scripts/hub_engine_runner.py --all
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _engines(store=None):
    from src.openharnesshub.component_store import ComponentStore
    from src.openharnesshub.hub_engine import engines_for_all_hubs
    return engines_for_all_hubs(store or ComponentStore())


def run_all() -> int:
    eng = _engines()
    for hub, e in eng.items():
        s = e.run_cycle()
        print(f"  {hub:<22} served {s['served']:>3}  (+{s['ingested']} ingested, {s['verified']} verified this cycle)")
    print(f"ran {len(eng)} hub engines (inject per-hub scraper/model ports to ingest live candidates)")
    return 0


def run_hub(hub_id: str) -> int:
    eng = _engines()
    if hub_id not in eng:
        print(f"unknown hub {hub_id!r} (one of {sorted(eng)[:6]}...)"); return 1
    print(json.dumps(eng[hub_id].run_cycle(), indent=1))
    return 0


def feed(hub_id: str | None) -> int:
    eng = _engines()
    hubs = [hub_id] if hub_id else list(eng)
    for h in hubs:
        if h in eng:
            f = eng[h].substrate_feed()
            print(f"  {h:<22} served {len(f['served'])}  funnel {f['funnel']['signals']} signals  -> consumed_by {f['consumed_by'] or '(internal)'}")
    return 0


def _hn_search(q: str) -> list:
    """REAL web search via the key-free HN Algolia API (the 'search' tier)."""
    import json
    import urllib.parse
    import urllib.request
    try:
        url = "https://hn.algolia.com/api/v1/search?tags=story&query=" + urllib.parse.quote(q)
        with urllib.request.urlopen(url, timeout=8) as r:  # noqa: S310 — fixed trusted host
            hits = json.loads(r.read()).get("hits", [])
        return [{"name": h.get("title") or h.get("story_title"), "url": h.get("url"), "source": "hn-algolia"}
                for h in hits[:5] if (h.get("title") or h.get("story_title"))]
    except Exception:  # noqa: BLE001
        return []


def _js_scrape(q: str) -> list:
    """REAL JS-compatible scrape (the 'scrape' tier) — shells to e2e/scrape_url.mjs (chromium). q is a URL."""
    import json
    import subprocess
    if not q.startswith("http"):
        return []
    try:
        r = subprocess.run(["node", str(REPO / "e2e" / "scrape_url.mjs"), q], cwd=str(REPO),
                           capture_output=True, text=True, timeout=40)
        data = json.loads((r.stdout or "{}").strip().splitlines()[-1])
        return [{"name": l["text"], "url": l["href"], "source": "js-scrape"} for l in data.get("links", [])[:10]]
    except Exception:  # noqa: BLE001
        return []


def _tools(real: bool = True):
    """The TOOL REPOSITORY for OpenClaw — REAL, multi-tier (unbounded→bounded): api (github/HN-search) > search
    (HN Algolia) > scrape (chromium JS render). All already-generated/installed tools; deterministic stubs offline."""
    from src.openharnesshub.discovery import Tool, stub_tools
    if real:
        try:
            from scripts.research_radar import research
            def _gh(q: str) -> list:
                try:
                    return research(q, "github", n=5) or []
                except Exception:  # noqa: BLE001
                    return []
            tools = [Tool("research_radar_github", "api", 2, _gh),
                     Tool("hn_algolia_search", "search", 3, _hn_search),
                     Tool("chromium_js_scrape", "scrape", 5, _js_scrape)]
            return tools or stub_tools()
        except Exception:  # noqa: BLE001
            pass
    return stub_tools()


def hub_query(hub: str) -> str:
    """Build a discovery query for a hub from architecture/hub_population_strategy.json (the per-hub sources)."""
    try:
        import json
        strat = json.loads((REPO / "architecture" / "hub_population_strategy.json").read_text()).get("hubs", {})
        src = strat.get(hub, {}).get("sources", {})
        terms = list(src.get("github_topics", [])) + list(src.get("hackernews", []))
        return " ".join(terms[:4]) or hub
    except Exception:  # noqa: BLE001
        return hub


def discover(query: str) -> int:
    """Stateless OpenClaw/Hermes discovery sweep across every hub (continuous append). Stub tools here; inject
    web-search / JS-scraping / research_radar-backed tools for live discovery."""
    from src.openharnesshub.discovery import OpenClaw, Hermes, default_plugins
    eng, oc, h = _engines(), OpenClaw(default_plugins()), Hermes()
    for r in h.sweep(query, openclaw=oc, hub_engines=eng, tools=_tools()):
        print(f"  {r['hub']:<22} discovered {r['discovered']} -> ingested {r['ingested']}")
    print("(stub tools — inject web-search / scraping / research_radar tools for live discovery)")
    return 0


def fresh(query: str) -> int:
    """Run Teleon's 'keep this hub fresh' capability per hub: plain text -> unbounded discovery -> descend to bounded."""
    from src.openharnesshub.discovery import OpenClaw, default_plugins
    from src.teleon.hub_freshness import keep_hub_fresh
    eng, oc, tools = _engines(), OpenClaw(default_plugins()), _tools()
    for hub in sorted({p.target_hub for p in oc.plugins}):
        intent = f"{query} :: {hub_query(hub)}"   # the plain-text capability + the hub's strategy sources
        r = keep_hub_fresh(hub, intent, hub_engines=eng, openclaw=oc, tools=tools)
        print(f"  {r['hub']:<22} discovered {r['discovered']} ingested {r['ingested']} | descended -> {r['bounded_tool']} ({r['pct_saved']}% cheaper)")
    return 0


def _self_test() -> int:
    import tempfile
    from src.openharnesshub.component_store import ComponentStore
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    with tempfile.TemporaryDirectory() as d:
        eng = _engines(ComponentStore(Path(d) / "c.jsonl"))
        ck("runner wires all 22 hub engines", len(eng) == 22)
        s = eng["OpenToolsHub"].run_cycle(raw_candidates=[{"name": "a governed tool"}])
        ck("runner runs a hub cycle (ingest+verify+serve)", s["ingested"] == 1 and s["served"] == 1)
        ck("runner exposes the substrate feed (Teleon/Baltor consume it)", "funnel" in eng["OpenToolsHub"].substrate_feed())
    print("\nPASS - hub_engine_runner: the per-hub orchestrator/supervisor — runs the ONE shared engine across all 22 "
          "Open*Hubs, reports served + the funnel, exposes substrate_feed. serves_truth=false."
          if not fails else f"FAIL: {fails}")
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--all" in argv:
        return run_all()
    if "--hub" in argv:
        i = argv.index("--hub")
        return run_hub(argv[i + 1]) if i + 1 < len(argv) else 1
    if "--feed" in argv:
        i = argv.index("--feed")
        return feed(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None)
    if "--discover" in argv:
        i = argv.index("--discover")
        return discover(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else "2026")
    if "--fresh" in argv:
        i = argv.index("--fresh")
        return fresh(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else "continuously update with public repos/skills/context")
    print("usage: hub_engine_runner.py --all | --hub <HubId> | --feed [HubId] | --discover [q] | --fresh [q] | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
