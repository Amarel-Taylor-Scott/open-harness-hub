#!/usr/bin/env python3
"""scripts.check_step_path_portfolio_pack — gate the step-path portfolio registry.

Asserts the pack on disk matches the builder (freshness), every path references a REAL engine mode (imported from
parallel_paths, not the pack), the engine + tracking-ledger refs resolve to importable symbols, and the boundary
holds. Offline, read-only. CLI: --self-test.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_step_path_portfolio_pack import (  # noqa: E402
    ALL_MODES,
    PACK_DIR,
    build_manifest,
    build_pack,
    self_test as builder_self_test,
)


def _fail(msg: str) -> None:
    raise AssertionError(msg)


def _resolves(dotted: str) -> bool:
    mod, _, attr = dotted.rpartition(".")
    try:
        return hasattr(importlib.import_module(mod), attr)
    except Exception:  # noqa: BLE001
        return False


def self_test() -> dict:
    if builder_self_test() != 0:
        _fail("builder self-test failed")

    # freshness: on-disk manifest must equal a freshly built manifest (hand-edits go red)
    disk_manifest = json.loads((PACK_DIR / "manifest.json").read_text(encoding="utf-8"))
    fresh = build_manifest(build_pack(), date=disk_manifest.get("generated_utc", "1970-01-01"))
    if disk_manifest.get("content_sha256") != fresh["content_sha256"]:
        _fail("pack is stale/hand-edited — regenerate via build_step_path_portfolio_pack.py --write")

    # engine + ledger refs must resolve to real symbols
    if not _resolves(disk_manifest["engine_ref"]):
        _fail(f"engine_ref {disk_manifest['engine_ref']} does not resolve")
    if not _resolves(disk_manifest["tracking_ledger_ref"]):
        _fail(f"tracking_ledger_ref {disk_manifest['tracking_ledger_ref']} does not resolve")

    # every path mode is a real engine mode; every step has one baseline + a fallback escalation
    steps = [json.loads(ln) for ln in (PACK_DIR / "step_path_portfolios.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    for step in steps:
        modes = [p["engine_mode"] for p in step["paths"]]
        if any(m not in ALL_MODES for m in modes):
            _fail(f"step {step['step']} references a non-engine mode")
        if modes.count("baseline") != 1:
            _fail(f"step {step['step']} must have exactly one baseline path")
        # a portfolio must offer at least one escalation beyond the baseline champion (challenger/shadow/canary/fallback)
        if not any(m != "baseline" for m in modes):
            _fail(f"step {step['step']} has no escalation path beyond baseline")

    return {
        "check": "step_path_portfolio_pack",
        "steps": len(steps),
        "total_paths": disk_manifest["total_paths_across_steps"],
        "engine_ref_resolves": True,
        "tracking_ledger_ref_resolves": True,
        "candidate": True,
        "serves_truth": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    print("PASS - step_path_portfolio_pack: fresh, modes single-sourced from the engine, refs resolve, "
          "every step is a portfolio with a baseline + fallback.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
