#!/usr/bin/env python3
"""check_hub_freshness — proof for the Teleon "keep this hub fresh" capability (plain-text → unbounded → bounded).

Proves: a plain-text intent drives OpenClaw/Hermes across the WHOLE tool repository (unbounded), digests the union into
the hub (continuous append), then DESCENDS to the cheapest BOUNDED tool that still meets the freshness bar — and records
the descent into the ONE descent brain. Governed (serves_truth=false). Offline, deterministic, temp store + temp brain.

CLI: PYTHONPATH=. python3 scripts/check_hub_freshness.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.openhubforai.component_store import ComponentStore
    from src.openhubforai.hub_engine import engines_for_all_hubs
    from src.openhubforai.discovery import OpenClaw, default_plugins, stub_tools
    from src.openhubforai.hub_settings import HubSettings
    from src.teleon.evolution.descent_attempt_store import DescentAttemptStore
    from src.teleon.hub_freshness import keep_hub_fresh
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    with tempfile.TemporaryDirectory() as d:
        store = ComponentStore(Path(d) / "c.jsonl")
        engines = engines_for_all_hubs(store)
        oc = OpenClaw(default_plugins())
        tools = stub_tools()
        brain = DescentAttemptStore(os.path.join(d, "brain.jsonl"))
        hub = "OpenContextHub"

        # auto_verify=False here so we can assert the discovery≠trust governance (candidates withheld until verified)
        r = keep_hub_fresh(hub, "continuously update with public repos, skills, context", hub_engines=engines,
                           openclaw=oc, tools=tools, brain=brain, freshness_floor=0.5,
                           settings=HubSettings(hub_id=hub, auto_verify=False, freshness_bar=0.5))

        ck("plain-text intent ran discovery + digested into the hub (continuous append)", r["ingested"] >= 1, str(r))
        ck("DESCENDED unbounded all-tools -> a cheaper BOUNDED tool (pct_saved > 0)", r["pct_saved"] > 0, f"{r['pct_saved']}%")
        ck("the bounded path is the CHEAPEST tool meeting the freshness bar (the api tier)", r["bounded_tool"] == "stub_api", str(r["bounded_tool"]))
        ck("bounded cost < unbounded cost (efficiency win)", r["bounded_cost"] < r["unbounded_cost"], f"{r['bounded_cost']} vs {r['unbounded_cost']}")
        ck("governed (serves_truth=false; discovered = candidates)", r["serves_truth"] is False)

        recs = [x for x in brain.all() if x.get("unit_id") == f"hub_freshness:{hub}"]
        ck("the descent is recorded into the ONE brain (the meta-learner learns the cheapest discovery path)", bool(recs))
        ck("...with after.cost < before.cost (a real descent)", recs and recs[-1]["after"]["cost"] < recs[-1]["before"]["cost"])

        # the digested candidates are appended but NOT served until verified (discovery≠trust)
        ck("discovered candidates are appended, served only after the hub verifies them", store.serve(hub) == [] and store.stats()["versions"] >= 1)

    print("\n" + ("PASS - check_hub_freshness: Teleon's 'keep this hub fresh' capability — plain text -> unbounded "
                  "OpenClaw/Hermes discovery across the whole tool repo -> digest into the hub -> DESCEND to the cheapest "
                  "bounded tool meeting the freshness bar -> recorded in the brain. Governed; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_hub_freshness.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
