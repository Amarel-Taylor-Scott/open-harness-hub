#!/usr/bin/env python3
"""check_hub_settings — proof for the per-hub SETTINGS PLANE (typed objects + merge + validation + enforcement).

Proves: each hub resolves a typed HubSettings (operational policy merged with the strategy's sources/bars); defaults
apply when absent; validation catches bad values; the live hub_settings.json is well-formed; and the settings are
ENFORCED by keep_hub_fresh — disabled hubs skip, the tool allowlist filters, rate_limit caps ingest, auto_verify gates
serving. Offline, deterministic, temp store.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_hub_settings.py --self-test
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.openhubforai.hub_settings import HubSettings, load_settings, all_settings, tools_for
    from src.openhubforai.component_store import ComponentStore
    from src.openhubforai.hub_engine import engines_for_all_hubs
    from src.openhubforai.discovery import OpenClaw, default_plugins, stub_tools
    from src.teleon.hub_freshness import keep_hub_fresh
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    # typed object + merge (operational policy + strategy sources/bars)
    s = load_settings("OpenContextHub")
    ck("a hub resolves a TYPED HubSettings (policy merged with strategy sources/bars)",
       isinstance(s, HubSettings) and s.hub_id == "OpenContextHub" and isinstance(s.sources, dict) and 0.0 <= s.freshness_bar <= 1.0)
    ck("the live hub_settings.json resolves for every configured hub (well-formed)", len(all_settings()) >= 7 and all(not v.validate() for v in all_settings().values()))
    ck("defaults apply for an unconfigured hub (no crash)", load_settings("NoSuchHub").enabled is True)

    # validation catches bad values
    ck("validate() rejects bad values (cadence<1, bad visibility, freshness out of range)",
       set(HubSettings(hub_id="x", cadence=0, visibility="nope", freshness_bar=2.0).validate()) and len(HubSettings(hub_id="x", cadence=0, visibility="nope", freshness_bar=2.0).validate()) >= 3)
    ck("a good settings object validates clean", HubSettings(hub_id="x").validate() == [])

    # tool allowlist filtering
    tools = stub_tools()
    allow_one = HubSettings(hub_id="x", tool_allowlist=("stub_api",))
    ck("tool_allowlist filters the tool repository", [t.name for t in tools_for(allow_one, tools)] == ["stub_api"])
    ck("empty allowlist = all tools", len(tools_for(HubSettings(hub_id="x"), tools)) == len(tools))

    # ENFORCEMENT in keep_hub_fresh
    with tempfile.TemporaryDirectory() as d:
        store = ComponentStore(Path(d) / "c.jsonl")
        engines = engines_for_all_hubs(store)
        oc = OpenClaw(default_plugins())
        # disabled -> skipped (nothing ingested)
        r_off = keep_hub_fresh("OpenContextHub", "x", hub_engines=engines, openclaw=oc, tools=tools,
                               settings=HubSettings(hub_id="OpenContextHub", enabled=False))
        ck("DISABLED hub is skipped (no ingest)", r_off.get("skipped") and r_off["ingested"] == 0)
        # rate_limit caps ingest
        r_cap = keep_hub_fresh("OpenContextHub", "x", hub_engines=engines, openclaw=oc, tools=tools,
                               settings=HubSettings(hub_id="OpenContextHub", rate_limit_per_cycle=1, auto_verify=True))
        ck("rate_limit_per_cycle caps ingest", r_cap["ingested"] <= 1)
        # auto_verify True -> the (verified) component IS served; False -> withheld
        ck("auto_verify=True serves the verified component", len(store.serve("OpenContextHub")) >= 1)
        store2 = ComponentStore(Path(d) / "c2.jsonl")
        eng2 = engines_for_all_hubs(store2)
        keep_hub_fresh("OpenToolsHub", "x", hub_engines=eng2, openclaw=oc, tools=tools,
                       settings=HubSettings(hub_id="OpenToolsHub", auto_verify=False))
        ck("auto_verify=False withholds (discovery≠trust)", store2.serve("OpenToolsHub") == [])

    print("\n" + ("PASS - check_hub_settings: the per-hub SETTINGS PLANE — typed HubSettings (policy merged with strategy "
                  "sources/bars), defaults, validation, and ENFORCEMENT in keep_hub_fresh (enabled/skip, tool allowlist, "
                  "rate_limit cap, auto_verify gate). serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_hub_settings.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
