#!/usr/bin/env python3
"""scripts.check_eval_promotion_io — PROOF: the spine's eval/promotion layer is RATIFIED to the existing
parallel-path engine, plus the one missing gate — HumanApprovalReceipt for boundary expansion — is enforced.

Asserts:
  A. SPINE MAP: every eval/promotion contract resolves to a real schema file (no dangling).
  B. ENGINE PRESENT (ratify by reference): _repos/baltor/backend/src/baltor/experiments/{parallel_paths,path_comparator,path_promotion,
     path_rollback}.py exist and the parallel-path promotion-gate proof is registered in the flywheel.
  C. REVERSIBLE BY CONTRACT: PathPromotionDecision REQUIRES rollback_target (a promotion is always reversible).
  D. NEW CONTRACT: HumanApprovalReceipt registered; mint produces all required fields.
  E. BOUNDARY GATE: a boundary-expanding promotion WITHOUT an approved receipt is blocked; WITH an approved
     receipt it passes; a PENDING receipt is blocked; a non-boundary-expanding promotion needs no approval.
  F. SUBJECT MATCH: an approval for a different subject_ref is rejected.
  G. DETERMINISM + minting validates boundary_kind/approver_role.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.experiments import boundary_approval as BA

_NOW = "2026-06-07T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    spine = json.loads((_resource("architecture") / "shared_io_spine.json").read_text())
    layer = next(L for L in spine["layers"] if L["layer"] == "evaluation_promotion_io")
    dangling = [c["schema"] for c in layer["contracts"] if c["status"] in ("exists", "new") and not (_resource(c["schema"])).exists()]
    check("A: eval/promotion spine contracts all resolve", not dangling, "; ".join(dangling))

    eng = _resource("src/baltor/experiments")
    check("B: parallel-path engine modules present",
          all((eng / f"{m}.py").exists() for m in ("parallel_paths", "path_comparator", "path_promotion", "path_rollback")))
    fly = (_resource("scripts/flywheel_proof_modules.py")).read_text()
    check("B: parallel-path promotion-gate proof registered in flywheel", "check_parallel_path_promotion_gate" in fly)

    ppd = json.loads((_resource("schemas") / "experiments" / "PathPromotionDecision.schema.json").read_text())
    check("C: PathPromotionDecision requires rollback_target (always reversible)", "rollback_target" in ppd["required"])

    contracts = json.dumps(json.loads((_resource("architecture") / "contract_registry.json").read_text()))
    check("D: HumanApprovalReceipt registered", "governance/HumanApprovalReceipt.schema.json" in contracts)
    req_fields = json.loads((_resource("schemas") / "governance" / "HumanApprovalReceipt.schema.json").read_text())["required"]
    receipt = BA.mint_human_approval_receipt(subject_ref="decision-1", boundary_kind="tool_added",
                                             approver_role="owner", status="approved", now=_NOW)
    check("D: minted receipt carries all required fields", all(k in receipt for k in req_fields), str([k for k in req_fields if k not in receipt]))

    ok_no, why_no = BA.gate_boundary_expansion(boundary_expanding=True, approval=None, subject_ref="decision-1")
    ok_yes, _ = BA.gate_boundary_expansion(boundary_expanding=True, approval=receipt, subject_ref="decision-1")
    pending = BA.mint_human_approval_receipt(subject_ref="decision-1", boundary_kind="tool_added", approver_role="owner", status="pending", now=_NOW)
    ok_pend, why_pend = BA.gate_boundary_expansion(boundary_expanding=True, approval=pending, subject_ref="decision-1")
    ok_non, _ = BA.gate_boundary_expansion(boundary_expanding=False, approval=None)
    check("E: boundary expansion gate (no approval blocked; approved ok; pending blocked; non-boundary ok)",
          (not ok_no) and "boundary_expansion_requires_human_approval" in why_no and ok_yes
          and (not ok_pend) and ok_non)

    ok_sub, why_sub = BA.gate_boundary_expansion(boundary_expanding=True, approval=receipt, subject_ref="OTHER")
    check("F: approval for a different subject is rejected", (not ok_sub) and "approval_subject_mismatch" in why_sub)

    check("G: deterministic + validates inputs",
          BA.mint_human_approval_receipt(subject_ref="decision-1", boundary_kind="tool_added", approver_role="owner", status="approved", now=_NOW) == receipt)
    bad = False
    try:
        BA.mint_human_approval_receipt(subject_ref="x", boundary_kind="not_a_kind", approver_role="owner", status="approved", now=_NOW)
    except ValueError:
        bad = True
    check("G: minting rejects an unknown boundary_kind", bad)

    print("\n" + ("PASS — check_eval_promotion_io: the eval/promotion spine layer is ratified to the existing "
                  "parallel-path engine (promotion always reversible by contract; engine proofs registered), and "
                  "boundary expansion now requires an approved HumanApprovalReceipt (non-boundary promotions don't); "
                  "deterministic." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_eval_promotion_io.py --self-test")
    raise SystemExit(0)
