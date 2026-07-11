"""src.teleon.evolution.external_outcomes — record an EXTERNAL run's result+metadata into the descent brain.

Teleon is a CONTROL / METADATA plane (_repos/teleon/context/architecture/teleon-control-plane-vs-compute.md): the final capability
unit — and even the improvement runs — execute EXTERNALLY (Cloudflare Workers/Workers AI, the customer's account, the
edge). Teleon does not need to run them; it TRACKS their results + metadata to GUIDE improvement. This module is that
seam: it ingests an external run's measured axes (from its receipt) into the canonical descent brain
(descent_attempt_store) and exposes the brain's next-move guidance — so improvement is driven by tracked telemetry of
runs Teleon never executed. serves_truth=false (a record is evidence, not truth); Teleon-layer — never imports baltor.
"""
from __future__ import annotations

from src.teleon.evolution.descent_attempt_store import DescentAttempt, DescentAttemptStore


def record_external_outcome(store: DescentAttemptStore, *, unit_id: str, before: dict, after: dict, provider: str,
                            strategy: str = "external_run", receipt_ref: str = "", outcome: str | None = None) -> dict:
    """Record an externally-executed run (e.g. on Cloudflare/customer compute) into the brain. ``before``/``after`` are
    the measured descent axes (from the run's receipt); ``provider`` is where it ran. Teleon did NOT run the unit — it
    is tracking the result to guide the next improvement. Returns the record + the (false) execution flags."""
    if outcome is None:
        outcome = ("improved" if (after.get("cost", 1e9) < before.get("cost", 1e9)
                                  or after.get("determinism", 0.0) > before.get("determinism", 0.0)) else "no_change")
    rec = store.append(DescentAttempt(unit_id=unit_id, strategy=strategy, before=before, after=after, outcome=outcome,
                                      rollback_target=f"{unit_id}@prior", raw_ref=receipt_ref,
                                      substrate_ref=f"external:{provider}"))
    return {"recorded": True, "unit_id": unit_id, "ran_on": provider, "ran_by": "external_compute",
            "teleon_executed_unit": False, "outcome": outcome, "attempt_id": rec["attempt_id"], "serves_truth": False}


def guide_next(store: DescentAttemptStore, before_state: dict) -> dict:
    """Teleon's improvement guidance from TRACKED results — no run required. The brain's empirically-best next descent
    move for a unit in ``before_state`` (computed from recorded attempts, incl. external ones)."""
    return {"recommended_strategy": store.best_strategy_for(before_state),
            "learned_from_attempts": len(store.all()), "serves_truth": False}
