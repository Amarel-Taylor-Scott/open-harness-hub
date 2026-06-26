"""src/teleon/experiments/path_rollback — build the plan that UNDOES a path promotion (pointer move only).

A promotion is always reversible because every :func:`path_promotion.decide` result carries a
``rollback_target`` = the prior baseline's path_id. This module turns that guarantee into an executable
``PathRollbackPlan``: move the active-path pointer for a ``capability_slot`` from the currently-promoted
candidate (``from_path_id``) back to the prior baseline (``rollback_target_path_id``) — and ONLY the pointer.

LOSSLESS DISTILLATION CLAUSE: rollback NEVER deletes. ``deletes_paths`` and ``deletes_prior_runs`` are pinned
``False`` — the losing AND winning path definitions and every prior :class:`ParallelPathRun` stay readable
after a rollback. Promotion is a pointer move; rollback is the inverse pointer move; nothing is destroyed.

Pure + deterministic: ``now`` is injected; the plan id is a content hash via :mod:`ids`. No wall-clock / RNG.
"""
from __future__ import annotations

from typing import Any

from scripts.runtime import schema_validator as _sv

from .ids import canonical_id

SCHEMA_VERSION = "PathRollbackPlan"


def build_rollback_plan(
    decision: dict[str, Any],
    *,
    now: str,
    reason: str = "rollback to baseline (pointer move; nothing deleted)",
    validate: bool = True,
) -> dict[str, Any]:
    """Build a ``PathRollbackPlan`` that reverts a promotion described by ``decision``.

    ``decision`` is a :func:`path_promotion.decide` result. The pointer moves AWAY from the decision's
    ``promoted_path_id`` (the candidate that was promoted) and BACK to its ``rollback_target`` (the prior
    baseline — ``decide`` always sets this). ``deletes_paths`` / ``deletes_prior_runs`` are structurally
    ``False`` (a rollback is a pointer move, never a delete). ``now`` is injected.

    A keep_baseline decision never promoted anything, so ``from_path_id`` falls back to the candidate that was
    judged — the plan still reverts the pointer to the baseline and deletes nothing.
    """
    rollback_target = decision["rollback_target"]
    from_path_id = decision.get("promoted_path_id") or decision["candidate_path_id"]
    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": canonical_id(
            "prp", decision["decision_id"], from_path_id, rollback_target
        ),
        "capability_slot": decision["capability_slot"],
        "from_path_id": from_path_id,
        # the prior baseline the pointer reverts to == the promotion's rollback_target (always the baseline).
        "rollback_target_path_id": rollback_target,
        "promotion_decision_id": decision["decision_id"],
        # rollback is a POINTER MOVE — never a delete (lossless distillation: keep the losers and the winner).
        "deletes_paths": False,
        "deletes_prior_runs": False,
        "reason": reason,
        "planned_at": now,
    }
    if validate:
        errs = _sv.validate_ref(plan, f"experiments/{SCHEMA_VERSION}")
        if errs:
            raise ValueError(f"PathRollbackPlan failed contract validation: {errs[:5]}")
    return plan
