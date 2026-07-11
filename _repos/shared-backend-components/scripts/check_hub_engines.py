#!/usr/bin/env python3
"""check_hub_engines — proof for the per-hub engines + the versioned multi-tenant component store + the funnel.

Proves: ONE shared HubEngine covers all 22 Open*Hubs (config-driven from the registry); the full lifecycle
(ingest→digest→verify→serve); user-owned VERSIONED components (tenant-isolated + lossless + tenant overrides global);
governance (unverified withheld; serves_truth=false); and the product wedge — opt-in contribute (sharing) + a governed
lead-gen / substrate funnel (signals + substrate_feed) that feeds Teleon/Baltor. Offline, deterministic, temp store.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_hub_engines.py --self-test
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.openhubforai.component_store import ComponentStore, GLOBAL_TENANT
    from src.openhubforai.hub_engine import HubEngine, hub_specs, engines_for_all_hubs
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    specs = hub_specs()
    ck("ONE engine per hub, single-sourced from the registry (22)", len(specs) == 22, str(len(specs)))
    ck("each hub spec carries its component kind (what it stores/serves)", all(s.component_kind for s in specs))

    with tempfile.TemporaryDirectory() as d:
        store = ComponentStore(Path(d) / "components.jsonl")
        engines = engines_for_all_hubs(store)
        ck("the shared engine instantiates for ALL 22 hubs (not 22 copies)", len(engines) == 22)
        eng = engines["OpenContextHub"]

        # ── lifecycle ──
        summ = eng.run_cycle(raw_candidates=[{"name": "OFAC SDN pack"}, "eCFR Reg E pack"])
        ck("lifecycle ingests + verifies + serves (run_cycle)", summ["ingested"] == 2 and summ["verified"] == 2 and summ["served"] == 2)
        ck("everything is governed (serves_truth=false)", summ["serves_truth"] is False)

        # ── governance: unverified is withheld ──
        rec = store.put_version("OpenContextHub", GLOBAL_TENANT, "draft-pack", {"component_id": "draft-pack", "name": "Draft"})
        ck("an UNVERIFIED component is NOT served (governed)", "draft-pack" not in {r["component_id"] for r in store.serve("OpenContextHub")})
        ck("...and a version record is serves_truth=false", rec["serves_truth"] is False)

        # ── user-owned versioned components (tenant isolation + override + lossless) ──
        eng.run_cycle(tenant="userA", raw_candidates=[{"name": "OFAC SDN pack", "note": "userA's tuned variant"}])
        ga = {r["component_id"]: r for r in store.serve("OpenContextHub", "userA")}
        ck("a user serves their OWN version overriding global (by component_id)",
           ga["ofac-sdn-pack"]["tenant"] == "userA" and ga["ofac-sdn-pack"]["body"].get("note") == "userA's tuned variant")
        ck("the GLOBAL version is untouched by the tenant (isolation)",
           {r["component_id"]: r for r in store.serve("OpenContextHub")}["ofac-sdn-pack"]["tenant"] == GLOBAL_TENANT)
        # lossless: a new version of the same component preserves the old
        store.put_version("OpenContextHub", "userA", "ofac-sdn-pack", {"component_id": "ofac-sdn-pack", "name": "OFAC SDN pack", "v": 2})
        ck("versioning is LOSSLESS (old version preserved)", len(store.versions("OpenContextHub", "userA", "ofac-sdn-pack")) == 2)

        # ── sharing + the lead-gen / substrate funnel (the product wedge) ──
        g = eng.contribute("ofac-sdn-pack", from_tenant="userA")
        ck("opt-in CONTRIBUTE promotes a verified tenant component to global (sharing surface)",
           g is not None and any(r["component_id"] == "ofac-sdn-pack" and r["body"].get("contributed") for r in store.serve("OpenContextHub")))
        eng.download("ofac-sdn-pack", tenant="userA")
        funnel = store.funnel_summary("OpenContextHub")
        ck("usage SIGNALS are captured (the lead-gen / info-collection funnel)",
           funnel["signals"] >= 3 and {"store", "download", "contribute"} <= set(funnel["by_action"]))
        feed = eng.substrate_feed()
        ck("substrate_feed exposes served components + the AGGREGATE funnel for Teleon/Baltor to consume",
           feed["served"] and "funnel" in feed and feed["serves_truth"] is False)
        ck("the funnel is aggregate-only (no raw tenant rows leak globally)", set(funnel) >= {"by_action", "tenants"} and "tenant" not in funnel)

    print("\n" + ("PASS - check_hub_engines: ONE shared HubEngine covers all 22 Open*Hubs (config-driven) — full lifecycle "
                  "(ingest→digest→verify→serve), USER-OWNED versioned components (tenant-isolated, lossless, override "
                  "global), governed (unverified withheld; serves_truth=false), + opt-in CONTRIBUTE sharing and a "
                  "governed lead-gen/substrate FUNNEL (signals + substrate_feed) that feeds Teleon/Baltor."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_hub_engines.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
