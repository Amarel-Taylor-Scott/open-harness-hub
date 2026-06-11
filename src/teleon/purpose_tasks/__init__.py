"""src.teleon.purpose_tasks — PurposeTask: purpose/capability-provisioned, self-adapting execution units.

A PurposeTask is declared by INTENT (purpose · capability_slot · input/output contract · success_criteria ·
promotion_criteria · resources), NOT by hand-wired code. The controller binds an implementation FROM a
capability registry by numeric priority (provision-by-capability), runs a cheap deterministic hot path, and —
when it drifts below success_criteria — self-adapts by running a candidate implementation SIDE-BY-SIDE against
the current one via the governed Parallel-Path Engine, promoting only on a passing PathPromotionDecision and
keeping the prior implementation as a fallback. Agents PROPOSE; the gate DISPOSES. See
docs/architecture/purpose-task-self-adapting-execution.md.

This package is the minimal PoC of that motion, composed entirely from the built substrate
(src/teleon/experiments/*) — no second runtime, ledger, or registry.
"""
from .purpose_task import (
    adapt,
    eval_suite_for,
    evaluate_health,
    provision,
    run_current,
    PurposeTaskSpec,
    EVAL_SUITE_FIELD,
)
from . import eval_suite

__all__ = ["provision", "run_current", "evaluate_health", "adapt",
           "PurposeTaskSpec", "eval_suite_for", "EVAL_SUITE_FIELD", "eval_suite"]
