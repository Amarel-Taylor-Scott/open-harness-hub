#!/usr/bin/env python3
"""scripts.artifact_graph.reconciliation — DETERMINISTIC conflict reconciliation + receipts.

Precedence (highest first): exact regulation/source-of-law > FAQ/summary; newer source_version > older
(same authority); structured-field fact > narrative allegation; human-signed > LLM suggestion; if
unresolved → HOLD OUT from the promoted context pack. Every reconciliation emits a receipt
(decision, winning_artifact_id, held_out_artifact_ids, reason, evidence handles, human_review_required).
The human-signed override is a documented hook — no human UI yet.

CLI: imported by scripts/check_cfpb_reconciliation.py and the orchestrator.
"""
from __future__ import annotations

from typing import Sequence

from scripts.artifact_graph.artifact_ledger import EPOCH, Reconciliation, chash


def _rank(art) -> int:
    return int(art.payload_json.get("source_rank", 50)) if art else 0


def _rid(conflict_id: str) -> str:
    return "recon-" + chash({"c": conflict_id}).split(":")[1][:16]


def reconcile(conflicts: Sequence, by_id: dict, *, tenant_id: str, now: str = EPOCH) -> dict:
    """Returns {reconciliations: [Reconciliation], status: {conflict_id: new_status}, held_out_ids: [...],
    winners: {conflict_id: winning_artifact_id}}."""
    recons: list[Reconciliation] = []
    status: dict[str, str] = {}
    held_out: set[str] = set()
    winners: dict[str, str] = {}

    for c in sorted(conflicts, key=lambda x: x.conflict_id):
        a, b = by_id.get(c.artifact_a_id), by_id.get(c.artifact_b_id)
        decision, winning, loser, resolver, human = "unresolved_hold_out", None, None, "deterministic", False
        rationale = "unresolved → held out from the promoted pack"

        if c.conflict_type == "promoted_depends_on_unverified":
            # a promotable artifact leaning on an unverified allegation → needs human; hold the allegation out
            decision, winning, loser, human = "needs_human", c.artifact_a_id, c.artifact_b_id, True
            rationale = "promotable artifact depends on an unverified allegation; routed to human review"
        elif a and b:
            ra, rb = _rank(a), _rank(b)
            if ra != rb:  # source-of-law / authority precedence
                hi, lo = (a, b) if ra > rb else (b, a)
                decision, winning, loser = "resolved_by_authority", hi.artifact_id, lo.artifact_id
                rationale = (f"{hi.payload_json.get('authority', hi.source_id)} (rank {max(ra, rb)}) outranks "
                             f"{lo.payload_json.get('authority', lo.source_id)} (rank {min(ra, rb)})")
            elif a.source_version != b.source_version:  # freshness (same authority)
                hi, lo = (a, b) if a.source_version >= b.source_version else (b, a)
                decision, winning, loser = "resolved_by_freshness", hi.artifact_id, lo.artifact_id
                rationale = f"newer source_version {hi.source_version} beats {lo.source_version}"
            elif a.artifact_type != b.artifact_type and "atomic_fact" in (a.artifact_type, b.artifact_type):
                fact = a if a.artifact_type == "atomic_fact" else b
                other = b if fact is a else a
                decision, winning, loser = "resolved_by_scope", fact.artifact_id, other.artifact_id
                rationale = "structured-field fact beats narrative allegation for a factual field"
            else:
                human = True  # genuinely ambiguous → hold out + flag

        if loser:
            held_out.add(loser)
        if winning:
            winners[c.conflict_id] = winning
        receipt = {"reconciliation_id": _rid(c.conflict_id), "decision": decision, "winning_artifact_id": winning,
                   "held_out_artifact_ids": [loser] if loser else [], "reason": rationale,
                   "evidence": (a.source_handles_json if a else []) + (b.source_handles_json if b else []),
                   "human_review_required": human}
        recons.append(Reconciliation(reconciliation_id=_rid(c.conflict_id), tenant_id=tenant_id,
                                      conflict_ids_json=[c.conflict_id], decision=decision, winning_artifact_id=winning,
                                      rationale=rationale, resolver_type=resolver, receipt_json=receipt, created_at=now))
        status[c.conflict_id] = "needs_human" if (human or decision == "unresolved_hold_out") else "reconciled"

    return {"reconciliations": recons, "status": status, "held_out_ids": sorted(held_out), "winners": winners}
