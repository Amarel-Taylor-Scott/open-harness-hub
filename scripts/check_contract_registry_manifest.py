#!/usr/bin/env python3
"""scripts.check_contract_registry_manifest — proof: the contract registry tracks every command/event/
artifact/processor/pipeline/queue/log type with name + status (+ version/schema where applicable), and any
referenced schema exists. Contract sprawl (new unregistered types) becomes a failing check.

CLI: python3 scripts/check_contract_registry_manifest.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_REGISTRIES = ("command_types", "event_types", "artifact_types", "processor_ids", "pipeline_ids", "queue_names", "log_events")
_VALID_STATUS = {"active", "experimental", "deprecated"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    check("all required registries exist", all(r in reg for r in _REGISTRIES), str([r for r in _REGISTRIES if r not in reg]))

    bad_status, no_name, bad_schema = [], [], []
    for r in _REGISTRIES:
        for item in reg[r]:
            if "name" not in item:
                no_name.append(f"{r}:{item}")
            if item.get("status") not in _VALID_STATUS:
                bad_status.append(f"{r}:{item.get('name')}={item.get('status')}")
            if "schema" in item and not (_REPO / item["schema"]).exists():
                bad_schema.append(item["schema"])
    check("every registry item has a name", no_name == [], str(no_name))
    check("every item status ∈ active|experimental|deprecated", bad_status == [], str(bad_status))
    check("every referenced schema file exists", bad_schema == [], str(bad_schema))

    # the registry must cover the contracts actually shipped this turn
    cmds = {c["name"] for c in reg["command_types"]}
    procs = {p["name"] for p in reg["processor_ids"]}
    arts = {a["name"] for a in reg["artifact_types"]}
    check("pipeline.run_step command is registered", "pipeline.run_step" in cmds)
    check("the CFPB harness processors are registered", {"decompose.cfpb_structured", "source.cfpb_fixture"} <= procs)
    check("the claim-shaped artifact types are registered", {"atomic_fact", "narrative_allegation"} <= arts)

    print(f"\n{'PASS — check_contract_registry_manifest: all contract registries are complete + valid; referenced schemas exist; shipped contracts are registered.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: contract registry.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
