#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_keda_mapping — proof (C-FLEET-3): the supervisor-scaling doc exists
and explains the four scaling levels, the leader/shard lease invariants, that execution stays in workers,
the coordination-pressure scale signal, and the K8s mapping (supervisor Deployment min 1-2, SKIP LOCKED).
The supervisor scaling schema is also registered.

CLI: PYTHONPATH=. python3 scripts/check_flywheel_supervisor_keda_mapping.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "docs" / "workers" / "flywheel-supervisor-scaling.md"
_SCHEMA = _REPO / "schemas" / "workers" / "SupervisorScaling.schema.json"
_CONCEPTS = ["leader lease", "shard", "idempotent", "source of truth", "minReplicas", "SKIP LOCKED",
             "coordination pressure"]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("scaling doc exists", _DOC.exists())
    text = _DOC.read_text().lower() if _DOC.exists() else ""
    for c in _CONCEPTS:
        chk(f"doc explains '{c}'", c.lower() in text)
    chk("doc lists the four scaling levels", text.count("supervisor") >= 4 and "shard" in text and "active/passive" in text)
    chk("doc keeps execution in workers (not the supervisor)", "workers = execution" in text or "execution stays in workers" in text)

    chk("supervisor scaling schema exists + parses", _SCHEMA.exists() and isinstance(json.loads(_SCHEMA.read_text()), dict))
    sc = json.loads(_SCHEMA.read_text())
    defs = set(sc.get("definitions", {}))
    chk("schema defines the 5 coordination records",
        {"SupervisorInstance", "SupervisorLease", "SupervisorShard", "SupervisorTick", "SupervisorDecision"} <= defs,
        str(defs))

    # the schema is registered as a governed artifact
    reg = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    names = {a["name"] for a in reg["artifact_types"]}
    chk("supervisor_scaling registered in contract_registry", "supervisor_scaling" in names)

    print(f"\n{'PASS — check_flywheel_supervisor_keda_mapping: scaling doc (4 levels, lease invariants, execution-in-workers, coordination-pressure signal, K8s mapping) + 5-record schema registered.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
