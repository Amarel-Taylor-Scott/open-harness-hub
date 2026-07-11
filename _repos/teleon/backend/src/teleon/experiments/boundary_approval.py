"""src.teleon.experiments.boundary_approval — the human-approval gate for BOUNDARY EXPANSION.

The parallel-path engine's automated gates (path_comparator/path_promotion) decide apples-to-apples
correctness, safety, and cost. This module adds the capstone's extra gate: when a promotion WIDENS what a
capability is allowed to do (a new capability/tool/runtime-class/data-class/autonomy/external provider), a human
must approve it via a HumanApprovalReceipt before the promotion may proceed. A non-boundary-expanding promotion
needs no such approval. Additive + pure + deterministic (now injected); does not edit the proven promotion path.
"""
from __future__ import annotations

import hashlib

BOUNDARY_KINDS = ("capability_added", "tool_added", "runtime_class_added", "data_class_widened",
                  "autonomy_increased", "external_provider_added")
_APPROVER_ROLES = ("owner", "exec", "policy", "security", "legal", "steward")


def mint_human_approval_receipt(*, subject_ref: str, boundary_kind: str, approver_role: str, status: str,
                                now: str, requested_by: str = "", justification: str = "") -> dict:
    if boundary_kind not in BOUNDARY_KINDS:
        raise ValueError(f"unknown boundary_kind {boundary_kind!r}")
    if approver_role not in _APPROVER_ROLES:
        raise ValueError(f"unknown approver_role {approver_role!r}")
    aid = "appr_" + hashlib.blake2b(f"{subject_ref}|{boundary_kind}|{approver_role}|{now}".encode(), digest_size=10).hexdigest()
    return {"schema_version": "HumanApprovalReceipt", "approval_id": aid, "subject_ref": subject_ref,
            "boundary_kind": boundary_kind, "approver_role": approver_role, "status": status,
            "requested_by": requested_by, "justification": justification, "created_at": now}


def gate_boundary_expansion(*, boundary_expanding: bool, approval: dict | None = None,
                            subject_ref: str = "") -> tuple[bool, list[str]]:
    """Return (ok, reasons). A non-boundary-expanding promotion is always ok. A boundary-expanding one is ok ONLY
    with an approved HumanApprovalReceipt whose subject matches (if subject_ref is given)."""
    if not boundary_expanding:
        return True, []
    reasons: list[str] = []
    if not approval:
        reasons.append("boundary_expansion_requires_human_approval")
    else:
        if approval.get("status") != "approved":
            reasons.append(f"approval_not_approved:{approval.get('status')}")
        if approval.get("approver_role") not in _APPROVER_ROLES:
            reasons.append("approval_missing_valid_role")
        if subject_ref and approval.get("subject_ref") != subject_ref:
            reasons.append("approval_subject_mismatch")
    return (not reasons), reasons


__all__ = ["mint_human_approval_receipt", "gate_boundary_expansion", "BOUNDARY_KINDS"]
