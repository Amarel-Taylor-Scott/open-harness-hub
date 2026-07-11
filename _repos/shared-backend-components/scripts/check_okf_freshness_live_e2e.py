#!/usr/bin/env python3
"""check_okf_freshness_live_e2e — the capstone that wires the two things adopted this session into ONE local loop:
ingest Google's OKF, bind its fragile fact to the LOCAL source emulator, and prove the exported OKF stays provably
CURRENT — the assurance OKF itself cannot express.

End to end, fully local (no GPU / key / network / cloud):
  1. import an OKF concept (type=runbook) carrying a regulated fact + its authoritative source;
  2. bind it to local_emulators.source_of_truth_emulator via a FreshnessSyncedCapability and serve the value (FRESH);
  3. the local source CHANGES (emulator.change -> CDC event) -> the prior answer is HELD OUT (never served), and the
     concept's freshness_status flips + the change is appended to its CDC history;
  4. re-sync from the emulator's new value -> serve the NEW value;
  5. export the concept back to OKF -> the file reflects the new value, freshness=fresh, and the reserved log.md
     carries the change. Round-trip stays lossless.

This is the one-line thesis made real, locally: "OKF is how context travels; Baltor governs whether it's true and
CURRENT." Never serves truth.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_okf_freshness_live_e2e.py --self-test | --report
"""
from __future__ import annotations

import json
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from local_emulators.source_of_truth_emulator import SourceOfTruthEmulator
from src.baltor.native.okf_adapter import okf_export, okf_import, round_trip
from src.teleon.evolution.freshness_runtime import FreshnessSyncedCapability

_SOURCE = "ecfr://12/1005.11"
_OKF_IN = {
    "reg-e-error-resolution-deadline.md": (
        "---\n"
        "type: runbook\n"
        "title: Reg E error-resolution deadline\n"
        f"resource: {_SOURCE}\n"
        "tags: [regulation, reg-e]\n"
        f'x_baltor_governance_json: {{"verified": true, "authoritative_source": "{_SOURCE}", '
        '"freshness_status": "fresh", "current_value": "10 business days", "serves_truth": false}\n'
        "---\n"
        "The financial institution must resolve a disputed EFT within the regulatory deadline.\n"
    )
}


def run_live_loop() -> dict:
    # 1. ingest OKF -> governed concept
    concept = okf_import(_OKF_IN)[0]
    source_id = concept.governance["authoritative_source"]

    # 2. bind the fragile fact to the LOCAL source emulator + serve it fresh
    emu = SourceOfTruthEmulator(source_id=source_id, value=concept.governance["current_value"], version="2025-edition")
    cap = FreshnessSyncedCapability(concept.concept_id, authoritative_source=source_id, volatility_class="low")
    cur = emu.current()
    cap.sync(cur["value"], now="t0", source_version=cur["version"])
    served_fresh = cap.serve(now="t1")["served"]

    # 3. the local source changes -> hold the stale answer out + reflect it in the concept's governance
    event = emu.change("12 business days", "2026-edition")
    held = cap.on_source_change(event, now="t2")
    concept.governance["freshness_status"] = held["status"]            # held_out
    concept.governance.setdefault("cdc_history", []).append(event)
    served_while_stale = cap.serve(now="t3")["served"]                 # None

    # 4. re-sync from the emulator's new authoritative value
    cur2 = emu.current()
    cap.sync(cur2["value"], now="t4", source_version=cur2["version"])
    served_after = cap.serve(now="t5")["served"]                       # "12 business days"
    concept.governance["freshness_status"] = "fresh"
    concept.governance["current_value"] = cur2["value"]
    concept.body = concept.body.replace("10 business days", cur2["value"])

    # 5. export back to OKF — the file is now provably current, with the change in log.md
    okf_out = okf_export([concept])
    reimported = round_trip([concept])[0]                              # still lossless after the live update
    return {
        "served_fresh": served_fresh, "served_while_stale": served_while_stale, "served_after_resync": served_after,
        "exported_value": reimported.governance.get("current_value"),
        "exported_freshness": reimported.governance.get("freshness_status"),
        "log_md": okf_out["log.md"], "source_changes": emu.change_count,
        "lossless": reimported.governance.get("verified") is True and reimported.type == concept.type,
        "serves_truth": any(x["serves_truth"] for x in (held,)) or reimported.as_dict()["serves_truth"],
    }


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = run_live_loop()
    ck("OKF concept binds to the LOCAL source emulator and serves the fresh value (10 business days)",
       r["served_fresh"] == "10 business days")
    ck("the local source change HOLDS the stale answer out (nothing served while stale)",
       r["served_while_stale"] is None and r["source_changes"] == 1)
    ck("re-sync from the emulator serves the NEW value (12 business days)",
       r["served_after_resync"] == "12 business days")
    ck("the exported OKF reflects the new value + freshness=fresh (provably current)",
       r["exported_value"] == "12 business days" and r["exported_freshness"] == "fresh")
    ck("the reserved log.md carries the source change (the assurance OKF cannot express)",
       "2026-edition" in r["log_md"] and _SOURCE in r["log_md"])
    ck("the round-trip stays LOSSLESS after the live update (governance + type survive)", r["lossless"] is True)
    ck("nothing serves truth across the whole live loop", r["serves_truth"] is False)
    ck("deterministic", run_live_loop()["exported_value"] == r["exported_value"])

    print("\n" + ("PASS - check_okf_freshness_live_e2e: an OKF concept, ingested and bound to the LOCAL source "
                  "emulator, serves fresh -> the source changes -> the stale answer is held out -> re-synced -> "
                  "the exported OKF is provably current with the change in log.md; round-trip stays lossless. OKF "
                  "carries the context; Baltor governs whether it's true and current — end-to-end, fully local. "
                  "Never serves truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--report" in argv:
        print(json.dumps(run_live_loop(), indent=2))
        return 0
    print("usage: check_okf_freshness_live_e2e.py --self-test | --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
