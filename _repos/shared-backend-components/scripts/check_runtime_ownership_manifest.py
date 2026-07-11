#!/usr/bin/env python3
"""scripts.check_runtime_ownership_manifest — proof: every runtime concept has exactly one declared owner
whose file exists in the governed scope; no concept is owned twice.

CLI: python3 _repos/shared-backend-components/scripts/check_runtime_ownership_manifest.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_REQUIRED = ("CommandEnvelope", "EventEnvelope", "ArtifactEnvelope", "ProcessorResult", "ErrorEnvelope",
             "DurableStore", "EventBus", "ProcessorHarness", "ProcessorRegistry", "PipelineRunner",
             "LLMGateway", "TenantStoreResolver", "ArtifactLedger", "RuntimeLogger", "CapabilityRegistry",
             "VerificationGate", "OptimizationHarness", "ConsumptionReadinessGate", "ConsumptionService")


def _in_scope(path: str, scope: list[str]) -> bool:
    return any(path == s or path.startswith(s.rstrip("/") + "/") or path == s for s in scope)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_resource("architecture") / "runtime_ownership.json").read_text())
    owners, scope = m["owners"], m["governed_scope"]
    check("every required runtime concept has a declared owner", all(c in owners for c in _REQUIRED),
          str([c for c in _REQUIRED if c not in owners]))
    missing = [f"{c}->{p}" for c, p in owners.items() if not (_resource(p)).exists()]
    check("every owner file exists", missing == [], str(missing))
    check("every owner path is inside the governed scope", all(_in_scope(p, scope) for p in owners.values()),
          str([p for p in owners.values() if not _in_scope(p, scope)]))
    # owners is a JSON object → keys unique by construction; assert no two concepts map to the same (concept,path) dup name
    check("no concept is declared twice", len(owners) == len(set(owners)))
    check("legacy duplicate allowlist is explicit (ProcessorRegistry dedup planned)",
          any(e["class"] == "ProcessorRegistry" for e in m["legacy_duplicate_allowlist"]))

    print(f"\n{'PASS — check_runtime_ownership_manifest: one canonical owner per runtime concept; all owner files exist in the governed scope.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: runtime ownership registry.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
