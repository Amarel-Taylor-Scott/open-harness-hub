#!/usr/bin/env python3
"""hub_engine_runner — the per-hub orchestrator / supervisor surface (run the 22 Open*Hub engines).

Thin wrapper over src.openharnesshub.hub_engine: instantiate ONE shared HubEngine per registry hub, run its lifecycle
cycle (scrape→ingest→digest→verify→serve), and report served counts + the lead-gen/substrate funnel. In production,
inject per-hub scraper + model ports (a real source poller + scripts._llm_client); here it runs over the durable store.
DEVELOPMENT plane (the operator surface); the engines + store are PRODUCT (src/openharnesshub).

  --hub <HubId>   run one hub's cycle      --all   run a cycle for every hub
  --ingest <HubId> [--links u1,u2] [--okf f1,f2] [--text '...'|@file] [--improve] [--llm]  OWNER intake of raw materials
  --discover [q]  autonomous OpenClaw/Hermes sweep   --fresh [q]  Teleon keep_hub_fresh (unbounded→bounded)
  --generate [HubId]  GENERATE channel: emit candidates from our own systems (method catalog / descent brain)
  --capability "<plain text>" [--plan-only] [--rounds N]  plan + run an OPEN-ENDED capability (iterative/scheduled/multi-component)
  --browse <url> [--goal "..."] [--steps N]  run the low-cost-LLM-driven browser (the research descent's deep-detail tier)
  --browsing-stack [--needs "deep_detail,js_render"] [--allow-restricted] [--all-licenses]  registry coverage + compose a governed stack
  --feed [HubId]  print the substrate_feed (what Teleon/Baltor consume)
  --self-test     offline: the runner wires every hub + runs a cycle
CLI: PYTHONPATH=. python3 scripts/hub_engine_runner.py --ingest OpenSkillsHub --okf my_skill.md --improve
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _engines(store=None, *, model=None):
    from src.openharnesshub.component_store import ComponentStore
    from src.openharnesshub.hub_engine import engines_for_all_hubs
    return engines_for_all_hubs(store or ComponentStore(), model=model)


def _model_port(use_llm: bool = False):
    """Real digest/improve model port (the ollama-cloud lane) when --llm is set + configured; else None (the engine
    falls back to its deterministic digest/improve). Resilient: a model error degrades to deterministic, never crashes."""
    if not use_llm:
        return None
    try:
        from scripts._llm_client import resolve_provider, chat
        prov = resolve_provider("ollama")
        if not prov.get("key"):
            print("  (--llm requested but the ollama lane isn't configured — using deterministic digest/improve)")
            return None
        import os
        model = os.environ.get("OH_LLM_MODEL") or prov.get("model") or "qwen2.5:7b"

        def m(prompt: str) -> str:
            try:
                return chat(model, "You enrich/improve governed Open*Hub components. Be concrete and terse.",
                            prompt, prov, max_tokens=400).get("text", "")
            except Exception:  # noqa: BLE001 — degrade to deterministic
                return ""
        return m
    except Exception:  # noqa: BLE001
        return None


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


def ingest_cmd(hub: str, *, links=(), okf_files=(), texts=(), improve=False, tenant="_global", use_llm=False) -> int:
    """OWNER INTAKE: feed raw materials YOU provide (OKF docs / links / pasted text) into one hub's lifecycle
    (digest → optional improve → verify → version). The complement to autonomous --discover/--fresh."""
    from src.openharnesshub.intake import ingest_materials
    eng = _engines(model=_model_port(use_llm))
    if hub not in eng:
        print(f"unknown hub {hub!r} (one of {sorted(eng)[:6]}...)"); return 1
    okf_docs = []
    for f in okf_files:
        try:
            okf_docs.append(Path(f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  (skip okf {f}: {e})")
    txts = []
    for t in texts:
        txts.append(Path(t[1:]).read_text(encoding="utf-8") if t.startswith("@") and Path(t[1:]).exists() else t)
    r = ingest_materials(eng[hub], links=links, okf=okf_docs, texts=txts, improve=improve, tenant=tenant)
    print(json.dumps(r, indent=1))
    print(f"\n{r['ingested']} ingested, {r['verified']} verified, {r['improved']} improved into {hub} "
          f"(tenant={tenant}) — serves_truth=false; only verified versions serve. View: --feed {hub}")
    return 0


def _extra_generators() -> dict:
    """Operator-layer generators that read Teleon internals — INJECTED so OHH never imports Teleon (dependency law).
    The runner is the wiring plane (it may import the product); the open hub layer stays clean."""
    gens: dict = {}
    try:
        from src.teleon.evolution.descent_attempt_store import DescentAttemptStore
        from src.openharnesshub.generators import make_descent_brain_generator
        gens["descent_brain"] = make_descent_brain_generator(lambda: DescentAttemptStore().all())
    except Exception:  # noqa: BLE001
        pass
    return gens


def generate_cmd(hub: str | None, *, tenant="_global", use_llm=False) -> int:
    """GENERATE channel: emit candidates from OUR systems (method catalog / descent brain / ...) -> ingest -> verify.
    The complement to --discover (public) and --ingest (owner). --generate with no hub runs every wired generator."""
    from src.openharnesshub.generators import generate_for
    eng = _engines(model=_model_port(use_llm))
    extra = _extra_generators()
    hubs = [hub] if hub else list(eng)
    total_gen = total_ver = wired = 0
    for h in hubs:
        if h not in eng:
            print(f"  unknown hub {h!r}"); continue
        g = generate_for(h, extra_generators=extra)
        if g["pending"]:
            if hub:  # only chatter about pending when a single hub was asked for
                print(f"  {h:<22} generate PENDING — {g['reason']} (discover/intake still populate it)")
            continue
        wired += 1
        gi = gv = 0
        for cand in g["candidates"]:
            try:
                rec = eng[h].ingest(cand, tenant=tenant)
                gi += 1
                gv += int(eng[h].verify(rec))
            except Exception:  # noqa: BLE001
                continue
        total_gen += gi
        total_ver += gv
        print(f"  {h:<22} generated {gi:>3} via {g['generator']:<22} -> {gv} verified")
    print(f"generate channel: {wired} wired generators, {total_gen} candidates, {total_ver} verified (serves_truth=false)")
    return 0


def browsing_stack_cmd(needs_csv: str = "", *, allow_restricted: bool = False, vendorable_only: bool = True) -> int:
    """Show the web-browsing stack registry coverage + (optionally) compose a governed stack for the needed caps."""
    from src.openharnesshub.browsing_registry import coverage, load_registry, select_stack
    cov = coverage(load_registry())
    b, dc = cov["browsers"], cov["driving_components"]
    print(f"browsers: {b['have']}/{b['target']} (target met={b['met']})")
    print(f"driving components: {dc['have']}/{dc['target']} ({dc['models']} models + {dc['logic']} logic) — "
          f"gap {dc['gap']} to fill via {cov['fill_via']}")
    if needs_csv:
        needs = [n.strip() for n in needs_csv.split(",") if n.strip()]
        print(f"\ncompose stack for {needs} (vendorable_only={vendorable_only}, allow_restricted={allow_restricted}):")
        print(json.dumps(select_stack(needs, vendorable_only=vendorable_only, allow_restricted=allow_restricted), indent=1))
    return 0


def browse_cmd(url: str, *, goal: str = "the page's main content", steps: int = 3) -> int:
    """Run the REAL low-cost-LLM-driven browser (the catalog's browse-tier component) on a URL — the expensive tier
    the research descent escalates to only for deep detail. Renders via chromium, the cheap LLM extracts the goal
    (deterministic fallback if no LLM lane), bounded steps+tokens, prints the receipt. serves_truth=false."""
    from src.teleon.research.llm_browser import LLMBrowserDriver
    r = LLMBrowserDriver(max_steps=steps).browse(url, goal=goal)
    print(json.dumps(r.as_dict(), indent=1))
    print(f"\nfound={r.found} pages={r.pages_visited} steps={r.steps} llm_calls={r.llm_calls} ~tokens={r.approx_tokens} — serves_truth=false")
    if r.note:
        print(f"note: {r.note}")
    return 0


def capability_cmd(intent: str, *, plan_only: bool = False, rounds: int = 5, tenant: str = "_global") -> int:
    """Process an OPEN-ENDED capability ('scrape the internet for more skills for openskillshub.io'): the planner
    recognizes iterative/scheduled, resolves the hub, descends the research catalog, decomposes into steps, executes."""
    from src.openharnesshub.discovery import OpenClaw, default_plugins
    from src.openharnesshub.hub_engine import hub_specs
    from src.teleon.capability_planner import plan as make_plan, execute as run_plan
    specs = hub_specs()
    hubs = [s.hub_id for s in specs]
    kinds = {s.hub_id: s.component_kind for s in specs}
    p = make_plan(intent, hubs=hubs, kinds=kinds, max_rounds=rounds)
    print(f"INTENT: {intent}")
    print(f"  -> hub={p.hub}  cadence={p.cadence}  iterative={p.iterative}  scheduled={p.scheduled}"
          + (f"  every={p.schedule_every} cycles" if p.scheduled else ""))
    print(f"  -> research need='{p.needed_capability}'  descent selects={p.research_descent.get('selected')}"
          f"  escalation={p.research_descent.get('escalation')}")
    print("  -> plan (multi-component):")
    for i, s in enumerate(p.steps, 1):
        print(f"       {i}. {s.name:<15} via {s.binds_to}")
    print(f"  -> stop: {p.stop}")
    if plan_only:
        return 0
    eng, oc, tools = _engines(), OpenClaw(default_plugins()), _tools()
    r = run_plan(p, hub_engines=eng, openclaw=oc, tools=tools, tenant=tenant)
    print(f"\nEXECUTED {r['rounds_run']} round(s) — stopped: {r['stopped_because']}; totals={r['totals']}")
    if r["schedule"]:
        print(f"SCHEDULE: recurring every {r['schedule']['every_cycles']} — honored by {r['schedule']['honored_by']}")
    print("serves_truth=false; candidates served only after the hub verify gate.")
    return 0


def settings(hub: str | None) -> int:
    """View the resolved per-hub SETTINGS PLANE (operational policy merged with the strategy)."""
    from src.openharnesshub.hub_settings import all_settings, load_settings
    items = {hub: load_settings(hub)} if hub else all_settings()
    for h, s in items.items():
        allow = ",".join(s.tool_allowlist) or "all"
        print(f"  {h:<22} enabled={s.enabled} cadence={s.cadence} rate={s.rate_limit_per_cycle} "
              f"auto_verify={s.auto_verify} visibility={s.visibility} tools={allow} freshness_bar={s.freshness_bar}")
    print("edit: scripts/hub_engine_runner.py --set <hub> enabled=false rate_limit_per_cycle=10 ...")
    return 0


def set_setting(hub: str, kvs: list[str]) -> int:
    """Set + validate one or more operational settings for a hub (the operator/UI write path)."""
    from src.openharnesshub.hub_settings import save_settings
    updates = {}
    for kv in kvs:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        if v.lower() in ("true", "false"):
            updates[k] = v.lower() == "true"
        elif v.isdigit():
            updates[k] = int(v)
        elif k == "tool_allowlist":
            updates[k] = [x for x in v.split(",") if x]
        else:
            updates[k] = v
    try:
        s = save_settings(hub, **updates)
        print(f"updated {hub}: enabled={s.enabled} cadence={s.cadence} rate={s.rate_limit_per_cycle} auto_verify={s.auto_verify} visibility={s.visibility}")
        return 0
    except ValueError as e:
        print(f"rejected (validation): {e}")
        return 1


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
        # OWNER INTAKE: OKF + a raw dict -> digest -> improve (lossless new version) -> verify
        from src.openharnesshub.intake import ingest_materials, parse_okf
        okf = "---\nname: A Skill\ntype: skill\n---\n# A Skill\nDoes a thing.\n"
        b = parse_okf(okf)
        ck("parse_okf reads frontmatter + keeps the raw doc (lossless)", b["name"] == "A Skill" and b["raw_okf"] == okf)
        r = ingest_materials(eng["OpenSkillsHub"], okf=[okf], dicts=[{"name": "manual skill", "summary": "x"}], improve=True)
        ck("owner intake: OKF + dict ingested, verified, improved (lossless new versions)",
           r["ingested"] == 2 and r["verified"] >= 1 and r["improved"] == 2 and r["serves_truth"] is False)
        # GENERATE channel: real method primitives from the catalog; honest 'pending' for unwired generators
        from src.openharnesshub.generators import generate_for
        g = generate_for("OpenOptimizationHub")
        ck("generate channel emits real method primitives (method_catalog single source)",
           not g["pending"] and len(g["candidates"]) >= 3 and g["candidates"][0]["serves_truth"] is False)
        gp = generate_for("OpenSkillToTool")
        ck("unwired generator returns honest 'pending' (never fabricates candidates)", gp["pending"] and gp["candidates"] == [])
    print("\nPASS - hub_engine_runner: the per-hub orchestrator/supervisor — runs the ONE shared engine across all 22 "
          "Open*Hubs, reports served + the funnel, exposes substrate_feed. serves_truth=false."
          if not fails else f"FAIL: {fails}")
    return 0 if not fails else 1


def _val(argv, flag, default=""):
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def _csv(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--ingest" in argv:
        hub = _val(argv, "--ingest")
        if not hub or hub.startswith("-"):
            print("usage: --ingest <Hub> [--links u1,u2] [--okf f1,f2] [--text '...'|@file] [--improve] [--tenant T] [--llm]")
            return 1
        return ingest_cmd(hub, links=_csv(_val(argv, "--links")), okf_files=_csv(_val(argv, "--okf")),
                          texts=[_val(argv, "--text")] if _val(argv, "--text") else [],
                          improve="--improve" in argv, tenant=_val(argv, "--tenant", "_global"),
                          use_llm="--llm" in argv)
    if "--all" in argv:
        return run_all()
    if "--hub" in argv:
        i = argv.index("--hub")
        return run_hub(argv[i + 1]) if i + 1 < len(argv) else 1
    if "--feed" in argv:
        i = argv.index("--feed")
        return feed(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None)
    if "--browsing-stack" in argv:
        return browsing_stack_cmd(_val(argv, "--needs", ""), allow_restricted="--allow-restricted" in argv,
                                  vendorable_only="--all-licenses" not in argv)
    if "--browse" in argv:
        url = _val(argv, "--browse")
        if not url or url.startswith("-"):
            print('usage: --browse <url> [--goal "what to extract"] [--steps N]')
            return 1
        return browse_cmd(url, goal=_val(argv, "--goal", "the page's main content"),
                          steps=int(_val(argv, "--steps", "3") or 3))
    if "--capability" in argv:
        intent = _val(argv, "--capability")
        if not intent:
            print('usage: --capability "scrape the internet for more skills for openskillshub.io" [--plan-only] [--rounds N]')
            return 1
        return capability_cmd(intent, plan_only="--plan-only" in argv,
                              rounds=int(_val(argv, "--rounds", "5") or 5), tenant=_val(argv, "--tenant", "_global"))
    if "--generate" in argv:
        i = argv.index("--generate")
        hub = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None
        return generate_cmd(hub, tenant=_val(argv, "--tenant", "_global"), use_llm="--llm" in argv)
    if "--discover" in argv:
        i = argv.index("--discover")
        return discover(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else "2026")
    if "--fresh" in argv:
        i = argv.index("--fresh")
        return fresh(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else "continuously update with public repos/skills/context")
    if "--settings" in argv:
        i = argv.index("--settings")
        return settings(argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None)
    if "--set" in argv:
        i = argv.index("--set")
        return set_setting(argv[i + 1], argv[i + 2:]) if i + 2 < len(argv) else 1
    print("usage: hub_engine_runner.py --all | --hub <H> | --ingest <H> [--links|--okf|--text|--improve|--llm] | "
          "--feed [H] | --discover [q] | --fresh [q] | --settings [H] | --set <H> k=v | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
