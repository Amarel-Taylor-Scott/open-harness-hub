#!/usr/bin/env python3
"""scaffold_hub — stand up a NEW Open*Hub in one command: reuse the design + wire the content path, then Teleon fills it.

Writes the (config-driven) entries a new hub needs and emits a design-reusing site stub:
  1. _repos/shared-backend-components/architecture/portfolio_connection_map.json   (the roster -> the shared HubEngine auto-covers it)
  2. _repos/shared-backend-components/architecture/hub_population_strategy.json     (sources + bars -> an OpenClaw plugin is auto-derived)
  3. _repos/shared-backend-components/architecture/hub_settings.json                (the operational settings object)
  4. dist/sites/<slug>/index.html                  (a branded site stub — reuses the design language)
After scaffolding, the existing engine + OpenClaw/Hermes + Teleon's keep_hub_fresh POPULATE it (the hubs flywheel
picks it up on its cadence). Idempotent; serves_truth=false; --dry-run shows the plan.

  scaffold_hub.py "OpenEvalHub" --kind evals --provides "eval result records" --sources github:llm-eval,hackernews:"llm eval"
  scaffold_hub.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CONN = _resource("architecture") / "portfolio_connection_map.json"
STRAT = _resource("architecture") / "hub_population_strategy.json"
SETTINGS = _resource("architecture") / "hub_settings.json"
SITE_DIR = _resource("dist") / "sites"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "hub"


def _parse_sources(spec: str) -> dict:
    """'github:llm-eval,github:agent-eval,hackernews:llm eval' -> {github_topics:[...], hackernews:[...], seed_urls:[...]}."""
    out: dict[str, list] = {}
    key = {"github": "github_topics", "hackernews": "hackernews", "hn": "hackernews", "url": "seed_urls"}
    for part in [p for p in spec.split(",") if p.strip()]:
        k, _, v = part.partition(":")
        out.setdefault(key.get(k.strip().lower(), "seed_urls"), []).append(v.strip() or k.strip())
    return out


def _site_stub(name: str, one_liner: str, kind: str, *, mode: str = "discover", sources: dict | None = None) -> str:
    """The new-hub site stub uses the SAME standardized template as build_hub_sites (single source of the hub UI), so
    a scaffolded hub looks identical to the live 22 from day one (then keep_hub_fresh fills in browse/served)."""
    try:
        from src.openhubforai.hub_site import render_hub_page
        return render_hub_page(name, content_kind=kind, one_liner=one_liner, contribution_mode=mode,
                               sources=sources or {}, tier="new")
    except Exception:  # noqa: BLE001 — fall back to a minimal branded card if the renderer can't import
        return (f"<!doctype html><meta charset=utf-8><title>{name} — Open*Hub</title>"
                f"<body style='font-family:Hanken Grotesk,system-ui;max-width:780px;margin:48px auto;padding:0 24px'>"
                f"<h1>{name}</h1><p>{one_liner}</p><p>stores: {kind} · powered by Teleon · serves_truth=false</p>")


def scaffold(name: str, *, kind: str, provides: str, sources: dict, tier: str = "private_bench",
             consumed_by: str = "teleon", conn: Path = CONN, strat: Path = STRAT, settings: Path = SETTINGS,
             site_dir: Path = SITE_DIR, dry_run: bool = False) -> dict:
    slug = _slug(name)
    changes = []

    def _load(p):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _write(p, data):
        if not dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    # 1. roster (the shared HubEngine auto-covers any hub in the roster)
    c = _load(conn)
    hubs = c.setdefault("hubs", [])
    if not any(h.get("name") == name for h in hubs):
        hubs.append({"name": name, "tier": tier, "provides": provides, "consumed_by": consumed_by})
        changes.append(f"roster += {name} ({tier})")
        _write(conn, c)
    # 2. strategy (sources + bars -> an OpenClaw plugin is auto-derived from this)
    s = _load(strat)
    sh = s.setdefault("hubs", {})
    if name not in sh:
        sh[name] = {"content_kind": kind, "contribution_mode": "discover", "generator": "", "tool_tier": "search",
                    "sources": sources or {"github_topics": [slug]},  # never stranded: default a discover source
                    "freshness_bar": 0.5, "verify_bar": f"a verified {kind[:-1] if kind.endswith('s') else kind}"}
        changes.append(f"strategy += {name} (kind={kind}, mode=discover, sources={list(sources) or [slug]})")
        _write(strat, s)
    # 3. settings (the operational settings object; defaults)
    g = _load(settings)
    gh = g.setdefault("hubs", {})
    if name not in gh:
        gh[name] = {"enabled": True, "cadence": 7, "rate_limit_per_cycle": 25, "tool_allowlist": [],
                    "auto_verify": True, "visibility": "tenant_first"}
        changes.append(f"settings += {name} (defaults)")
        _write(settings, g)
    # 4. design-reusing site stub
    site = site_dir / slug / "index.html"
    if not dry_run:
        site.parent.mkdir(parents=True, exist_ok=True)
        site.write_text(_site_stub(name, f"{provides.capitalize()} — governed, continuously updated from public sources.",
                                   kind, mode="discover", sources=sources), encoding="utf-8")
    try:
        _rel = site.relative_to(REPO)
    except ValueError:
        _rel = site
    changes.append(f"site stub -> {_rel}")
    return {"hub": name, "slug": slug, "dry_run": dry_run, "changes": changes, "serves_truth": False,
            "next": "the hubs flywheel + keep_hub_fresh will populate it (or run: hub_engine_runner.py --hub " + name + ")"}


def _self_test() -> int:
    import shutil
    import tempfile
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': '+d) if d and not ok else ''}")
        if not ok: fails.append(n)
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        for src, dst in [(CONN, td / "conn.json"), (STRAT, td / "strat.json"), (SETTINGS, td / "settings.json")]:
            shutil.copy(src, dst)
        before = len(json.loads((td / "conn.json").read_text())["hubs"])
        r = scaffold("OpenEvalHub", kind="evals", provides="eval result records",
                     sources=_parse_sources("github:llm-eval,hackernews:llm eval"),
                     conn=td / "conn.json", strat=td / "strat.json", settings=td / "settings.json", site_dir=td / "sites")
        conn = json.loads((td / "conn.json").read_text())
        strat = json.loads((td / "strat.json").read_text())
        settings = json.loads((td / "settings.json").read_text())
        ck("roster gains the hub (the shared HubEngine auto-covers it)", len(conn["hubs"]) == before + 1 and any(h["name"] == "OpenEvalHub" for h in conn["hubs"]))
        ck("strategy gains sources/bars (an OpenClaw plugin is auto-derived from this)", "OpenEvalHub" in strat["hubs"] and strat["hubs"]["OpenEvalHub"]["sources"])
        ck("settings gains a typed settings object (defaults)", "OpenEvalHub" in settings["hubs"] and settings["hubs"]["OpenEvalHub"]["enabled"] is True)
        ck("a design-reusing site stub is emitted", (td / "sites" / "openevalhub" / "index.html").exists())
        ck("source spec parses (github/hackernews -> typed sources)", strat["hubs"]["OpenEvalHub"]["sources"].get("github_topics") == ["llm-eval"])
        # idempotent: re-run adds nothing
        before2 = len(conn["hubs"])
        scaffold("OpenEvalHub", kind="evals", provides="x", sources={}, conn=td / "conn.json", strat=td / "strat.json", settings=td / "settings.json", site_dir=td / "sites")
        ck("idempotent (re-scaffold doesn't duplicate)", len(json.loads((td / "conn.json").read_text())["hubs"]) == before2)
        # dry-run writes nothing
        dr = scaffold("OpenDryHub", kind="x", provides="x", sources={}, conn=td / "conn.json", strat=td / "strat.json", settings=td / "settings.json", site_dir=td / "sites", dry_run=True)
        ck("--dry-run plans without writing", dr["dry_run"] and not any(h["name"] == "OpenDryHub" for h in json.loads((td / "conn.json").read_text())["hubs"]))
    print("\n" + ("PASS - scaffold_hub: one command stands up a new Open*Hub — roster (engine auto-covers) + strategy "
                  "(plugin auto-derived) + settings object + a design-reusing site stub; then Teleon's keep_hub_fresh "
                  "populates it. Idempotent, dry-run-able, serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if not argv or argv[0].startswith("-"):
        print('usage: scaffold_hub.py "OpenEvalHub" --kind evals --provides "..." --sources github:topic,hn:query [--tier private_bench] [--dry-run]')
        return 0
    name = argv[0]
    def opt(flag, default=""):
        return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default
    r = scaffold(name, kind=opt("--kind", "components"), provides=opt("--provides", name + " components"),
                 sources=_parse_sources(opt("--sources", "")), tier=opt("--tier", "private_bench"),
                 consumed_by=opt("--consumed-by", "teleon"), dry_run="--dry-run" in argv)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
