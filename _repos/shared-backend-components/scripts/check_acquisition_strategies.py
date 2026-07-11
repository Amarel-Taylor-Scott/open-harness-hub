"""check_acquisition_strategies — proof for _repos/shared-backend-components/architecture/acquisition_strategies.json (backs registry #82).

The AGENCY layer: ACTIONS an agent takes to generate/acquire missing information. Enforces the catalog is
well-formed AND GOVERNED — the load-bearing safety rail: any HIGH-invasiveness (side-effecting) strategy must
be boundary-APPROVED, and the estimate strategy must flag itself as non-truth. Cost/invasiveness in legend;
ids unique; >=8 strategies; serves_truth=false. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_DOC = _resource("architecture") / "acquisition_strategies.json"
_REQ = ("id", "action", "yields", "cost_tier", "invasiveness", "governance", "when")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    strategies = doc.get("strategies", [])
    costs = set(doc.get("cost_legend", {}))
    invs = set(doc.get("invasiveness_legend", {}))
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck(">=8 strategies", len(strategies) >= 8, str(len(strategies)))
    ck("cost + invasiveness legends defined", len(costs) >= 3 and len(invs) >= 3)

    ids: set[str] = set()
    for s in strategies:
        sid = s.get("id", "?")
        for f in _REQ:
            ck(f"{sid}: has '{f}'", bool(s.get(f)))
        ck(f"{sid}: unique id", sid not in ids, "duplicate")
        ids.add(sid)
        ck(f"{sid}: cost_tier in legend", s.get("cost_tier") in costs, str(s.get("cost_tier")))
        ck(f"{sid}: invasiveness in legend", s.get("invasiveness") in invs, str(s.get("invasiveness")))
        # GOVERNANCE RAIL: a side-effecting (high-invasiveness) action must be boundary-approved.
        if s.get("invasiveness") == "high":
            ck(f"{sid}: high-invasiveness is boundary-APPROVED", "approv" in str(s.get("governance", "")).lower(),
               str(s.get("governance")))

    # the estimate strategy must flag itself as non-truth (never assert an estimate as fact)
    est = next((s for s in strategies if s.get("id") == "synthesize_estimate"), None)
    ck("synthesize_estimate flags non-truth", est is not None and "estimate" in str(est.get("governance", "")).lower())

    if fails:
        print(f"\nFAIL - check_acquisition_strategies: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_acquisition_strategies: {len(strategies)} governed acquisition strategies "
          f"(invasive actions boundary-approved, estimates flagged); {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
