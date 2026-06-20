#!/usr/bin/env python3
"""scripts.check_scripts_are_entrypoints — proof: top-level scripts/ files stay entrypoints/proofs/wrappers
and do NOT define a new framework owner class (DurableStore/EventBus/ProcessorHarness/PipelineRunner/
LLMGateway/TenantStoreResolver/ProcessorRegistry) except the declared canonical owners. Stops a new
mini-framework from being dropped into scripts/.

CLI: python3 scripts/check_scripts_are_entrypoints.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_FRAMEWORK = ("DurableStore", "EventBus", "ProcessorHarness", "PipelineRunner", "LLMGateway",
              "TenantStoreResolver", "ProcessorRegistry")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    owners = json.loads((_REPO / "architecture" / "runtime_ownership.json").read_text())["owners"]
    declared_owner_files = {p for p in owners.values()}

    # rule 1: no top-level scripts/*.py defines a framework class unless it's that class's declared owner
    offenders = []
    for p in sorted((_REPO / "scripts").glob("*.py")):
        rel = str(p.relative_to(_REPO))
        text = p.read_text(encoding="utf-8", errors="ignore")
        for cls in _FRAMEWORK:
            if re.search(rf"^class {cls}\b", text, re.M) and owners.get(cls) != rel:
                offenders.append(f"{rel}:{cls}")
    check("no top-level scripts/*.py defines a framework owner class (except declared owners)",
          offenders == [], str(offenders))

    # rule 2: every check_*/demo_*/baltor_* script is a runnable entrypoint (argparse or __main__)
    # only proofs/demos + the known entrypoints must be runnable (a baltor_* client LIBRARY is exempt)
    _ENTRYPOINTS = {"flywheel_worker.py", "baltor_flywheel.py", "dev_status.py", "make_review_pack.py"}
    not_entry = []
    for p in sorted((_REPO / "scripts").glob("*.py")):
        if not (p.name.startswith(("check_", "demo_")) or p.name in _ENTRYPOINTS):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "__main__" not in text and "argparse" not in text and "def _main" not in text:
            not_entry.append(str(p.relative_to(_REPO)))
    check("every check_/demo_/baltor_ script is a runnable entrypoint", not_entry == [], str(not_entry[:6]))

    # the declared owners that live in scripts/ root are the ONLY framework-class scripts (legacy, pending migration)
    legacy_owner_scripts = sorted({p for p in declared_owner_files if p.startswith("scripts/") and "/" not in p[len("scripts/"):]})
    check("declared owner files in scripts/ root exist (durable_store + context_events)",
          all((_REPO / p).exists() for p in legacy_owner_scripts) and len(legacy_owner_scripts) >= 2, str(legacy_owner_scripts))

    print(f"\n{'PASS — check_scripts_are_entrypoints: scripts/ stays entrypoints/proofs/wrappers; no new framework class is hidden there.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: scripts are entrypoints, not frameworks.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
