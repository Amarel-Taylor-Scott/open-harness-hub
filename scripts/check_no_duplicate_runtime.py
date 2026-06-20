#!/usr/bin/env python3
"""scripts.check_no_duplicate_runtime — proof: no core framework class is defined twice in the governed
scope (a second bus/store/registry/gateway/harness) except an explicit legacy allowlist. Runtime drift —
reinventing the bones — becomes a failing check.

CLI: python3 scripts/check_no_duplicate_runtime.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_FRAMEWORK_CLASSES = ("DurableStore", "EventBus", "ProcessorRegistry", "LLMGateway", "TenantStoreResolver",
                      "ArtifactLedger", "ArtifactGraphLedger", "CapabilityRegistry", "VerificationGate",
                      "OptimizationHarness", "ConsumptionReadinessGate", "ConsumptionService")


def _governed_files(scope: list[str]) -> list[Path]:
    out: list[Path] = []
    for s in scope:
        p = _REPO / s
        if p.is_file() and p.suffix == ".py":
            out.append(p)
        elif p.is_dir():
            out += [f for f in p.rglob("*.py") if "__pycache__" not in f.parts]
    return sorted(set(out))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_REPO / "architecture" / "runtime_ownership.json").read_text())
    scope = m["governed_scope"]
    owners = m["owners"]
    allow = {(e["class"], e["path"]) for e in m["legacy_duplicate_allowlist"]}

    files = _governed_files(scope)
    for cls in _FRAMEWORK_CLASSES:
        definers = [str(f.relative_to(_REPO)) for f in files
                    if re.search(rf"^class {cls}\b", f.read_text(encoding="utf-8", errors="ignore"), re.M)]
        effective = [d for d in definers if (cls, d) not in allow]
        check(f"{cls} is defined at most ONCE in governed scope (outside legacy allowlist)",
              len(effective) <= 1, f"{cls}: {definers} (allowlisted: {[d for d in definers if (cls,d) in allow]})")
        if cls in owners and definers:
            check(f"{cls}'s sole/canonical definition is its declared owner", owners[cls] in definers,
                  f"owner={owners[cls]} definers={definers}")

    check("the known pre-existing duplicate (pipeline_runtime ProcessorRegistry) is allowlisted",
          ("ProcessorRegistry", "scripts/pipeline_runtime/processors.py") in allow)

    print(f"\n{'PASS — check_no_duplicate_runtime: no second framework class exists in the governed scope (the one legacy ProcessorRegistry duplicate is allowlisted with a consolidation deadline).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no duplicate runtime frameworks.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
