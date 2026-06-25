#!/usr/bin/env python3
"""scripts.check_surface_and_dev_contract — enforce the surface + development contract.

Guards the exact failure modes from the 2026-06-25 incident (docs/codex/surface-and-development-contract.md):
  1. Every brand pillar's BUILT-OUT canonical surface + its must_exist files are present + non-empty — catches a
     destroyed/regressed/emptied design surface (the thing the owner feared).
  2. Reports scripts/*.py that define a self_test but are NOT registered in flywheel_proof_modules (orphaned seams).
serves_truth=false. (run_proofs runs --self-test; --check is the enforcement invocation for CI / pre-demo.)

  --self-test   offline logic test
  --check       run the contract assertions (exit nonzero if a built-out surface is missing/empty)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
SPEC = REPO / "architecture" / "surface_capability_spec.json"


def _spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def surface_violations(spec: dict | None = None) -> list[str]:
    spec = spec or _spec()
    out: list[str] = []
    for p in spec.get("pillars", []):
        cs = REPO / p["canonical_surface"]
        if not cs.exists():
            out.append(f"{p['id']}: canonical surface MISSING: {p['canonical_surface']}")
        for m in p.get("must_exist", []):
            f = REPO / m
            if not f.exists():
                out.append(f"{p['id']}: missing built-out file: {m}")
            elif f.is_file() and f.stat().st_size == 0:
                out.append(f"{p['id']}: EMPTY (regressed?): {m}")
    return out


def unregistered_seams() -> list[str]:
    from scripts.flywheel_proof_modules import PROOF_MODULES
    registered = {m[0] for m in PROOF_MODULES}
    out: list[str] = []
    for f in sorted((REPO / "scripts").glob("*.py")):
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "def self_test" in t and f"scripts/{f.name}" not in registered:
            out.append(f"scripts/{f.name}")
    return out


def check() -> int:
    sv = surface_violations()
    us = unregistered_seams()
    for v in us:                                            # informational (don't fail the gate on pre-existing scripts)
        print(f"  [warn · unregistered seam] {v} — add to flywheel_proof_modules per the contract")
    if sv:
        print("SURFACE CONTRACT VIOLATION (a built-out surface is missing/empty — design at risk):")
        for v in sv:
            print(f"  [surface] {v}")
        return 1
    print(f"surface + dev contract OK ({len(_spec()['pillars'])} pillars' built-out surfaces present"
          + (f"; {len(us)} unregistered seam(s) warned" if us else "; all seams registered") + ")")
    return 0


def self_test() -> int:
    spec = _spec()
    assert len(spec["pillars"]) == 5, "exactly 5 brand pillars"
    assert {p["id"] for p in spec["pillars"]} == {"ai-done-right", "teleon", "aidevobserver", "baltor", "open-star-hubs"}
    assert all(p.get("canonical_surface") and p.get("capabilities") for p in spec["pillars"]), "each pillar has a surface + capabilities"
    assert isinstance(surface_violations(spec), list) and isinstance(unregistered_seams(), list)
    # synthetic: a pillar pointing at a missing file is flagged
    fake = {"pillars": [{"id": "x", "canonical_surface": "nope/x", "must_exist": ["nope/x/missing.html"], "capabilities": ["c"]}]}
    assert any("missing" in v for v in surface_violations(fake)), "detects a missing built-out file"
    print("check_surface_and_dev_contract self-test: OK (5 pillars, surface + seam-registration checks, missing-file detection)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    print("usage: check_surface_and_dev_contract.py --self-test | --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
