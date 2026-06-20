"""src/teleon/experiments/path_promotion — the ONLY object that may authorize promoting a candidate.

``decide(report, criteria, *, candidate_path_id, now, cost_acceptable=..., ...) -> PathPromotionDecision``
turns one candidate's verdict from a :func:`path_comparator.compare` report into a
``PathPromotionDecision.v1``. A candidate is promoted ONLY when ALL gates pass:

    same_input AND same_output_contract AND output_equivalent AND source_handles_preserved
    AND held_out_not_leaked AND safety_ok AND cost_acceptable

``same_input`` is the input-attestation gate: the candidate must provably have run on the IDENTICAL input
the baseline did (its recorded input_snapshot_hash == the run's). A different-input comparison can NEVER be
promoted, even if the output happens to match. If ANY gate is false the decision is 'keep_baseline' and
``promoted_path_id`` is null. ``rollback_target`` is ALWAYS the baseline's path_id (so a promotion is
reversible) — there is no code path that produces a 'promote' without it. ``cost_acceptable`` is decided
from ``criteria`` (a max cost_delta ceiling) OR an explicit ``cost_acceptable`` override (justified) — the
cost number itself comes from the pricebook via :mod:`path_costing`, never hardcoded.

Nothing else in the engine may promote a path: :func:`parallel_paths.run_parallel` never serves a
candidate, and a candidate becomes the served baseline only by a caller acting on a 'promote' decision
from here — AND only after :func:`is_promote_authorized` re-derives the gates from the decision's own
fields (so a decision that merely *validates* against the schema, but whose gates do not actually all hold,
can never authorize a serve). Pure + deterministic: ``now`` is injected; no wall-clock / RNG / network.

Canonical TELEON home (experiments layer); imports its ids leaf from Teleon — never Baltor. Baltor re-exports
this via a shim at src/baltor/experiments/path_promotion.py.
"""
from __future__ import annotations

from typing import Any

from scripts.runtime import schema_validator as _sv

from .ids import canonical_id

SCHEMA_VERSION = "PathPromotionDecision.v1"
DECISION_PROMOTE = "promote"
DECISION_KEEP = "keep_baseline"

#: the gates that ALL must be true to promote (mirrors PathPromotionDecision.v1 required gates).
#: same_input is FIRST: a candidate that did not provably run on the baseline's input is never promotable.
GATES = (
    "same_input",
    "same_output_contract",
    "output_equivalent",
    "source_handles_preserved",
    "held_out_not_leaked",
    "safety_ok",
    "cost_acceptable",
)


def _find_verdict(report: dict[str, Any], candidate_path_id: str) -> dict[str, Any]:
    for v in report.get("candidate_verdicts", []):
        if v["candidate_path_id"] == candidate_path_id:
            return v
    raise KeyError(f"candidate_path_id {candidate_path_id!r} has no verdict in report {report.get('report_id')!r}")


def _cost_acceptable(verdict: dict[str, Any], criteria: dict[str, Any], override: bool | None) -> bool:
    """Decide the cost gate.

    Explicit ``override`` (a justified human/policy decision) wins. Otherwise the candidate's cost_delta
    must be at or below ``criteria['max_cost_delta']`` (a candidate that is the same price or cheaper
    passes by default when no ceiling is given).
    """
    if override is not None:
        return bool(override)
    ceiling = criteria.get("max_cost_delta")
    cost_delta = float(verdict.get("cost_delta", 0.0))
    if ceiling is None:
        # no explicit ceiling: a candidate that is not MORE expensive than the baseline is acceptable.
        return cost_delta <= 0.0
    return cost_delta <= float(ceiling)


def decide(
    report: dict[str, Any],
    criteria: dict[str, Any],
    *,
    candidate_path_id: str,
    now: str,
    cost_acceptable: bool | None = None,
    validate: bool = True,
) -> dict[str, Any]:
    """Authorize (or refuse) promoting ``candidate_path_id`` to baseline; return a ``PathPromotionDecision.v1``.

    Promote ONLY if every gate is true. ``rollback_target`` is ALWAYS set to the report's baseline_path_id.
    The five comparator gates are mirrored from the verdict (auditable warrant); the sixth, cost_acceptable,
    is decided from ``criteria`` / the ``cost_acceptable`` override. ``now`` is injected.
    """
    verdict = _find_verdict(report, candidate_path_id)
    baseline_path_id = report["baseline_path_id"]

    same_input = bool(verdict["same_input"])
    same_output_contract = bool(verdict["same_output_contract"])
    output_equivalent = bool(verdict["output_equivalent"])
    source_handles_preserved = bool(verdict["source_handles_preserved"])
    held_out_not_leaked = bool(verdict["held_out_not_leaked"])
    safety_ok = bool(verdict["safety_ok"])
    cost_ok = _cost_acceptable(verdict, criteria, cost_acceptable)

    gate_values = {
        "same_input": same_input,
        "same_output_contract": same_output_contract,
        "output_equivalent": output_equivalent,
        "source_handles_preserved": source_handles_preserved,
        "held_out_not_leaked": held_out_not_leaked,
        "safety_ok": safety_ok,
        "cost_acceptable": cost_ok,
    }
    promote = all(gate_values[g] for g in GATES)

    if promote:
        decision = DECISION_PROMOTE
        promoted_path_id: Any = candidate_path_id
        reason = "all gates green; candidate promoted to baseline (rollback_target = prior baseline)"
    else:
        decision = DECISION_KEEP
        promoted_path_id = None  # MUST be null when keeping the baseline.
        failed = [g for g in GATES if not gate_values[g]]
        reason = f"keep_baseline: failing gate(s) {failed}"

    decision_obj: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": canonical_id(
            "ppd", report["report_id"], candidate_path_id, baseline_path_id, decision
        ),
        "report_id": report["report_id"],
        "run_id": report["run_id"],
        "capability_slot": report["capability_slot"],
        "candidate_path_id": candidate_path_id,
        "baseline_path_id": baseline_path_id,
        "decision": decision,
        "promoted_path_id": promoted_path_id,
        **gate_values,
        # ALWAYS the baseline — a promotion is always reversible. There is no branch that omits this.
        "rollback_target": baseline_path_id,
        "reason": reason,
        "decided_at": now,
    }
    if validate:
        errs = _sv.validate_ref(decision_obj, f"experiments/{SCHEMA_VERSION}")
        if errs:
            raise ValueError(f"PathPromotionDecision failed contract validation: {errs[:5]}")
    return decision_obj


def is_promote_authorized(decision: dict[str, Any]) -> bool:
    """Re-derive whether ``decision`` actually authorizes PROMOTING a candidate — from its OWN fields, not
    its label. Returns True ONLY for a legitimate promote; a keep_baseline (which promotes nothing) is False.

    A decision authorizes a promotion iff ALL of:
      - decision == 'promote', AND
      - EVERY gate boolean in :data:`GATES` is exactly True, AND
      - promoted_path_id == candidate_path_id (it names the candidate it judged), AND
      - rollback_target is present (a promotion is always reversible).

    This is the barrier that closes the "schema-valid forgery" hole: a hand-built dict can pass the
    PathPromotionDecision.v1 contract while claiming decision=='promote' with FALSE gates (or a mismatched
    promoted_path_id). Any code that would SERVE a candidate must gate on this function — never on
    ``decision.get('decision') == 'promote'`` alone. The schema's own if/then constraint enforces the same
    consistency at the contract layer; this is the defence-in-depth runtime check.
    """
    if not isinstance(decision, dict):
        return False
    if decision.get("decision") != DECISION_PROMOTE:
        return False
    if not all(decision.get(g) is True for g in GATES):
        return False
    if decision.get("promoted_path_id") != decision.get("candidate_path_id"):
        return False
    if not decision.get("rollback_target"):
        return False
    return True


def authorized_promoted_path_id(decision: dict[str, Any]) -> str | None:
    """The path_id a serve layer may switch the baseline to — ONLY when :func:`is_promote_authorized`.

    Returns the promoted candidate's path_id for an authorized 'promote', else None. This is the single
    function any serve-authorization logic should call: it never trusts ``decision['decision']`` alone, so a
    forged-but-schema-valid 'promote' (all gates false) yields None — the baseline stays served.
    """
    return decision.get("promoted_path_id") if is_promote_authorized(decision) else None
