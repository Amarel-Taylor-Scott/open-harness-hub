#!/usr/bin/env python3
"""Measured-lift → promotion bridge — the gate that makes a *measured* capability
lift the thing that decides whether a component may promote.

THE GAP THIS CLOSES (docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md):
the repo has TWO promotion notions that never touch —
  (a) the Teleon runtime gate (`_repos/shared-backend-components/scripts/teleon_local_runtime.py`): train+holdout
      pass-rate >= 0.90 → promoted. A real gate, but pass-rate ON ITS OWN SUITE,
      with NO lift axis and NO durability axis — a capability can clear it while
      adding nothing a bare model couldn't do, or while its advantage is one model
      generation from evaporating.
  (b) `_repos/shared-backend-components/scripts/eval/measured_lift_headtohead.py`: the REAL two-axis discipline
      (paired / held-out / SEPARATE judge — it *raises* on self-grading) and the
      one that pairs the lift with a `durability_class`. But it writes promotion
      NOWHERE — it produces the number and stops.
The capability-gap framework (_repos/shared-backend-components/docs/concepts/capability-valleys.md,
`_repos/shared-backend-components/scripts/eval/reason_codes.py`, `_repos/shared-backend-components/scripts/eval/durable_gap_harness.py`) says the
admission rule is: a component must LIFT (`pipeline_score − bare_model_score > 0`)
AND that lift must be STRUCTURALLY durable (it will not close when the next base
model ships). This module is the deterministic function that *applies* that rule
to a measured-lift result, so "measured lift" becomes an enforceable promotion
gate other surfaces can call — the missing wire between (b) and a promote/cull.

It is **step 3 of the backbone program** in the deep-dive ("tie
measured_lift_headtohead … into promotion as the Stage-2 confirm") and the **P2**
item "measured-lift promotion for registry components".

WHAT THIS IS (honest scope):
  * a PURE, deterministic decision function: `promotion_decision(lift_result,
    gate_evidence, *, policy) -> a verdict dict`. No IO, no clock, no model, no
    network. Same inputs → byte-identical output.
  * the verdict is one of **promote | candidate | reject** and carries the FULL
    reasoning (lossless — never a bare verdict): the normalized lift it read, the
    durability class, every reason that moved the decision, and the policy used.
  * it REQUIRES a positive *measured* lift AND a non-transient `durability_class`
    (from the canonical `reason_codes` taxonomy — imported, NEVER re-defined here)
    to say **promote**; it maps a borderline / transient / unknown-durability /
    review-blocked case to **candidate**; it **rejects** a no-lift / negative-lift
    / unmeasured / self-graded result. Self-grading can never promote: if the
    result is not evaluator-independent the bridge refuses it outright.

WHAT THIS IS NOT:
  * it does NOT run the head-to-head — `measured_lift_headtohead.run_headtohead`
    does that (and is what *should* feed this). This consumes its OUTPUT.
  * it does NOT itself decide model-level judge independence, CIs, or n-floors for
    *publication* — those are the head-to-head's `publish_blockers`/`seams`, which
    this bridge READS and treats as review-forcing, never silently clears.
  * it does NOT edit `teleon_local_runtime.py` or `registry_local_service.py`.
    Those wire-in points are documented (see WIRE-IN below + the §doc) so the
    owner/next wave connects them; this pass ships the callable they call.

No-Magic-Values: the durability vocabulary and its classifier come from
`scripts.eval.reason_codes` (the single taxonomy source — CLAUDE.md: "never
redefine these enums elsewhere"). The only literals THIS module owns are its own
decision thresholds, each a named constant with a unit/rationale below; every
verdict echoes the `policy` it used so a reader never has to guess them.

Public API:
    from scripts.eval.promotion_bridge import promotion_decision, PromotionPolicy
    verdict = promotion_decision(lift_result, gate_evidence)
    # -> {"decision": "promote"|"candidate"|"reject", "basis", "lift",
    #     "durability_class", "reasons": [...], "requires_review": bool, ...}

CLI / self-test (deterministic; proves every path, no model, no network):
    python -m scripts.eval.promotion_bridge --self-test
    python -m scripts.eval.promotion_bridge --explain <lift_result.json> [--evidence <gate.json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any

# Make the repo root importable when run *directly* (defensive; the package also
# has _repos/shared-backend-components/scripts/eval/__init__.py so `-m` works without this). Stdlib only; no-op
# under -m. Mirrors the pattern in measured_lift_headtohead.py.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os as _os

    _REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Canonical durability taxonomy — SINGLE SOURCE, never re-defined here (CLAUDE.md /
# reason_codes.py header). We CLASSIFY durability via these; we do not re-enumerate
# the classes or the lift-reason → class mapping anywhere in this module.
from scripts.eval.reason_codes import (
    DURABILITY_CLASSES,   # ("transient", "structural", "mixed")
    LIFT_REASONS,         # canonical lift_reason → {durability_class, note}
    durability_class,     # lift_reason -> "transient"|"structural"|"mixed"|"unknown"
)

# ── Decision vocabulary (this module's own — single source) ──────────────────
#
# Deliberately DISTINCT from the other two promotion vocabularies so a reader is
# never confused about which gate spoke:
#   * teleon_local_runtime.py: promoted | candidate | rolled-back  (pass-rate gate)
#   * candidate_promotion_scorer.py: promote_candidate | review_before_promotion |
#     hold | reject  (heuristic readiness score)
# This bridge — the MEASURED-LIFT gate — answers exactly the three the task names:
PROMOTE = "promote"     # positive measured lift + non-transient durability + clean evidence
CANDIDATE = "candidate"  # real-but-not-yet-promotable: borderline lift, transient/unknown
#                          durability, or a review-forcing gate blocker
REJECT = "reject"        # no/negative measured lift, unmeasured, or self-graded (never trustable)
DECISIONS: tuple[str, ...] = (PROMOTE, CANDIDATE, REJECT)

# The durability classes that CLEAR the durability axis for a promote. Derived
# from the canonical taxonomy (NOT a re-listing): everything that is not the
# single transient class. "unknown" is intentionally NOT here — an unclassified
# lift cannot be asserted durable, so it can reach `candidate` but never `promote`.
# Built from DURABILITY_CLASSES so a taxonomy change flows through automatically.
TRANSIENT_CLASS = "transient"            # the one class the data flywheel closes
UNKNOWN_CLASS = "unknown"                # not in DURABILITY_CLASSES — untagged lift
assert TRANSIENT_CLASS in DURABILITY_CLASSES  # guard: taxonomy still names it
NON_TRANSIENT_DURABILITY_CLASSES: frozenset[str] = frozenset(
    c for c in DURABILITY_CLASSES if c != TRANSIENT_CLASS
)  # == {"structural", "mixed"} today, but computed, never hand-typed

# ── Thresholds (this module's ONLY owned literals; each named + rationale) ────
#
# A lift must be STRICTLY positive to be a lift at all (capability-valleys.md:
# `pipeline_score − bare_model_score > 0`). We use a tiny epsilon as the floor so
# floating-point noise around a true 0 (an identical-to-bare pipeline) is never
# mistaken for a positive lift — token-F1 deltas are rounded to 6 d.p. upstream,
# so anything at/below this is indistinguishable from "no lift".
DEFAULT_MIN_PROMOTE_LIFT = 1e-6          # unit: evaluator-score delta (B−A), [−1, 1]
# Paired-denominator floor: the head-to-head's `n` is the number of items scored
# on BOTH arms. One item is enough to be non-empty offline (mirrors the harness's
# MIN_DEV_ITEMS), but a single paired item is too thin to assert a durable promote
# — below this it can reach `candidate` but is review-forced for a promote. This is
# a DEVELOPMENT floor; the publication n-floor is the harness's own seam (carried
# through as a blocker), never silently satisfied here.
DEFAULT_MIN_PROMOTE_N = 2                 # unit: paired held-out items
# An unmeasured result (no real delta) is NEVER a promote and NEVER a silent pass.
# This is a posture constant, not a number — kept here so the rule is one place.
TREAT_UNMEASURED_AS = REJECT             # honest: no number ⇒ no lift claim


@dataclass(frozen=True)
class PromotionPolicy:
    """The thresholds the bridge applies — frozen, echoed in every verdict.

    Defaults are the module constants above; a caller may tighten them (e.g. a
    higher `min_promote_n` for an outward-facing surface) but the verdict always
    records which policy decided, so a downstream reader never guesses the bar.
    A non-positive `min_promote_lift` is rejected at construction — the gate's
    whole point is that a lift must be measured AND positive.
    """

    min_promote_lift: float = DEFAULT_MIN_PROMOTE_LIFT
    min_promote_n: int = DEFAULT_MIN_PROMOTE_N
    #: durability classes that satisfy the durability axis for a promote.
    promote_durability_classes: frozenset[str] = NON_TRANSIENT_DURABILITY_CLASSES

    def __post_init__(self) -> None:
        if not self.min_promote_lift > 0:
            raise ValueError(
                f"min_promote_lift must be > 0 (a lift must be positive to gate a "
                f"promote); got {self.min_promote_lift!r}"
            )
        if self.min_promote_n < 1:
            raise ValueError(f"min_promote_n must be >= 1; got {self.min_promote_n!r}")
        unknown = set(self.promote_durability_classes) - set(DURABILITY_CLASSES)
        if unknown:
            raise ValueError(
                f"promote_durability_classes must be a subset of the canonical "
                f"reason_codes.DURABILITY_CLASSES {DURABILITY_CLASSES}; "
                f"got unexpected {sorted(unknown)}"
            )
        if TRANSIENT_CLASS in self.promote_durability_classes:
            # A transient lift closes with the next model — it is, by the taxonomy's
            # definition, never a durable promote. Refuse a policy that says otherwise
            # rather than silently let a transient gain promote.
            raise ValueError(
                f"{TRANSIENT_CLASS!r} durability can never satisfy a promote "
                "(it closes with the next model; capability-valleys.md). Remove it "
                "from promote_durability_classes."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "min_promote_lift": self.min_promote_lift,
            "min_promote_n": self.min_promote_n,
            "promote_durability_classes": sorted(self.promote_durability_classes),
        }


DEFAULT_POLICY = PromotionPolicy()


# ── Normalizing the measured-lift input (accepts BOTH real result shapes) ─────
#
# The bridge is callable by any surface, so it accepts either:
#   (1) the rich `measured_lift_headtohead.run_headtohead` output — keys:
#       lift, durability_class, n, measurement_kind, evaluator_independent,
#       publish_blockers, (head_to_head, by_family, fidelity, seams …); OR
#   (2) the leaner `scripts.foundry.measure` candidate-`lift` dict — keys:
#       delta, durability_class, n, judge, measured_offline.
# It reduces either to one canonical record so the decision logic has ONE shape.

@dataclass
class NormalizedLift:
    """The canonical lift facts the decision reads, distilled from either shape."""

    lift: float | None                 # the measured delta (B−A). None ⇒ unmeasured
    durability_class: str              # "transient"|"structural"|"mixed"|"unknown"
    n: int                             # paired held-out items scored on both arms
    measured: bool                     # a real delta exists (not None / "unmeasured")
    evaluator_independent: bool        # the judge was not an answer arm (object-level)
    lift_reason: str | None            # the reason behind the durability, if carried
    source_blockers: list[str]         # publish_blockers carried up from the harness
    raw_keys: list[str]                # which input keys we saw (lineage/debug)


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):  # bool is an int subclass — exclude
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _coerce_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return default


def normalize_lift_result(result: dict[str, Any]) -> NormalizedLift:
    """Reduce a head-to-head result OR a measure.py candidate-lift dict to one record.

    Robust to either shape and to missing optional keys. Raises ``TypeError`` only
    if ``result`` is not a mapping — a malformed-but-mapping result degrades to
    ``measured=False`` (→ reject) rather than throwing, because an unmeasurable
    result is an HONEST outcome the gate must handle, not an error.
    """
    if not isinstance(result, dict):
        raise TypeError(f"lift result must be a dict, got {type(result).__name__}")

    # the delta: head-to-head uses "lift"; measure.py uses "delta". Either may be None.
    lift = _coerce_float(result.get("lift"))
    if lift is None:
        lift = _coerce_float(result.get("delta"))

    # measured? prefer the explicit head-to-head flag; else infer from a real delta.
    kind = result.get("measurement_kind")
    if kind == "measured":
        measured = True
    elif kind == "unmeasured":
        measured = False
    else:  # measure.py shape (no measurement_kind) — measured iff a real delta exists
        measured = lift is not None

    # durability: prefer the carried class; else derive from a carried lift_reason
    # via the canonical classifier (NEVER re-mapping the table here).
    klass = result.get("durability_class")
    lift_reason = result.get("lift_reason")
    if klass is None and lift_reason is not None:
        klass = durability_class(str(lift_reason))
    if klass is None:
        klass = UNKNOWN_CLASS
    klass = str(klass)
    # guard: a carried class must be a taxonomy value (or our explicit "unknown").
    if klass not in (*DURABILITY_CLASSES, UNKNOWN_CLASS):
        klass = UNKNOWN_CLASS

    # evaluator independence: the head-to-head sets this True only after enforcing
    # the separate-evaluator guard. A result that does NOT carry it is treated as
    # NOT independent — fail closed: an unproven separation can never promote.
    evaluator_independent = result.get("evaluator_independent") is True

    blockers = result.get("publish_blockers")
    source_blockers = [str(b) for b in blockers] if isinstance(blockers, list) else []

    return NormalizedLift(
        lift=lift,
        durability_class=klass,
        n=_coerce_int(result.get("n"), 0),
        measured=measured,
        evaluator_independent=evaluator_independent,
        lift_reason=str(lift_reason) if lift_reason is not None else None,
        source_blockers=source_blockers,
        raw_keys=sorted(result.keys()),
    )


# ── gate_evidence: the promotion-boundary blockers (CLAUDE.md "Promotion Boundary")
#
# Beyond the measured lift, CLAUDE.md forbids a candidate becoming tenant-visible
# while it has open review tickets, placeholder embeddings, unresolved source/
# signature questions, or volatile public facts without CDC/revocation. The bridge
# does not RE-DERIVE these (that is the registry/runtime's job) — it ACCEPTS them
# as `gate_evidence` and treats any present blocker as review-forcing: it caps the
# decision at `candidate` and sets requires_review=True. This is the single place
# the names of these blockers live for the bridge, each with the boundary it maps.
HARD_GATE_BLOCKERS: dict[str, str] = {
    # key in gate_evidence (truthy ⇒ blocked) : why it blocks a promote
    "open_review_tickets": "has open review tickets (promotion boundary)",
    "high_risk_review_required": "high-risk review is required before publication",
    "placeholder_embeddings": "embeddings are placeholders, not real vectors",
    "unresolved_source": "source/provenance question is unresolved",
    "unresolved_signature": "signed-publisher/signature question is unresolved",
    "volatile_without_cdc": "volatile public facts without CDC/revocation handling",
}


def _evidence_blockers(gate_evidence: dict[str, Any] | None) -> list[str]:
    """Human-readable reasons for every HARD_GATE_BLOCKER present (truthy) in evidence.

    Two accepted spellings, both honored:
      * a truthy boolean under the blocker key (``{"open_review_tickets": True}``);
      * a non-empty list/count under it (``{"open_review_tickets": ["t1", "t2"]}``)
        — any non-empty container or non-zero number counts as present.
    Also honors an explicit ``{"blockers": [...]}`` free-list of extra reason strings.
    """
    if not gate_evidence:
        return []
    reasons: list[str] = []
    for key, why in HARD_GATE_BLOCKERS.items():
        val = gate_evidence.get(key)
        present = bool(val) if not isinstance(val, (int, float)) or isinstance(val, bool) else val != 0
        if present:
            # enrich the reason with a count when a container/number was given
            if isinstance(val, (list, tuple, set, dict)):
                reasons.append(f"{why} [{len(val)}]")
            else:
                reasons.append(why)
    extra = gate_evidence.get("blockers")
    if isinstance(extra, list):
        reasons.extend(f"evidence blocker: {b}" for b in extra)
    return reasons


# ── The decision (deterministic, pure) ───────────────────────────────────────


def promotion_decision(
    measured_lift_result: dict[str, Any],
    gate_evidence: dict[str, Any] | None = None,
    *,
    policy: PromotionPolicy = DEFAULT_POLICY,
) -> dict[str, Any]:
    """Decide whether a measured-lift result permits a component to promote.

    Args:
      measured_lift_result: the OUTPUT of
        ``scripts.eval.measured_lift_headtohead.run_headtohead`` (preferred) OR a
        ``scripts.foundry.measure`` candidate-``lift`` dict. Either shape is
        normalized (see ``normalize_lift_result``).
      gate_evidence: optional promotion-boundary signals (CLAUDE.md "Promotion
        Boundary") — open review tickets, placeholder embeddings, unresolved
        source/signature, volatile-without-CDC (see ``HARD_GATE_BLOCKERS``). Any
        present blocker is review-forcing: it caps the verdict at ``candidate``.
      policy: the thresholds to apply (``DEFAULT_POLICY`` unless overridden); the
        verdict echoes them.

    Returns a verdict dict (lossless — carries the full reasoning):
      ``decision``           — ``promote`` | ``candidate`` | ``reject``.
      ``basis``              — one short machine token naming the deciding rule
                               (e.g. ``positive_lift_durable``, ``no_lift``,
                               ``self_graded``, ``transient_durability``,
                               ``review_blocked``, ``unmeasured``, ``thin_n``).
      ``lift``               — the normalized measured delta (B−A), or ``None``.
      ``durability_class``   — ``transient``|``structural``|``mixed``|``unknown``.
      ``lift_is_positive``   — ``lift is not None and lift > policy.min_promote_lift``.
      ``durability_ok``      — class is in ``policy.promote_durability_classes``.
      ``n``                  — paired held-out items scored.
      ``evaluator_independent`` — object-level judge separation (from the result).
      ``requires_review``    — a human/curator must look before any promotion.
      ``reasons``            — ordered, human-readable reasoning chain (every factor
                               that moved the decision — never a bare verdict).
      ``gate_blockers``      — the promotion-boundary blockers found in evidence.
      ``source_publish_blockers`` — the head-to-head ``publish_blockers`` carried up
                               (e.g. no CI, model-level judge independence unverified).
      ``policy``             — the thresholds used (so a reader never guesses them).
      ``normalized``         — the full normalized lift record (lineage).

    Determinism: pure function of (result, evidence, policy). No IO, clock, RNG.
    """
    norm = normalize_lift_result(measured_lift_result)
    reasons: list[str] = []

    lift_is_positive = norm.lift is not None and norm.lift > policy.min_promote_lift
    durability_ok = norm.durability_class in policy.promote_durability_classes
    evidence_blockers = _evidence_blockers(gate_evidence)
    n_sufficient = norm.n >= policy.min_promote_n

    # describe what the durability class means (lossless: carry the taxonomy note)
    durability_note = LIFT_REASONS.get(norm.lift_reason or "", {}).get("note") if norm.lift_reason else None

    # ── Decision ladder. Each branch sets decision + a basis token + reasons, and
    #    every rule's *reason* is recorded even when it isn't the deciding one, so
    #    the verdict is a full audit, not a yes/no. ──
    requires_review = False

    # (0) Self-grading can NEVER promote — and cannot even be a trusted candidate.
    #     The head-to-head raises if you self-grade, so a well-formed result is
    #     always independent; but a hand-assembled / legacy result might not carry
    #     the flag. Fail closed: no proof of separation ⇒ the number is untrustable.
    if not norm.evaluator_independent:
        reasons.append(
            "evaluator independence NOT established (evaluator_independent != True) — "
            "a self-graded or unproven number cannot gate a promotion "
            "(measured-lift-head-to-head.md §5). Re-run via run_headtohead with a "
            "SEPARATE evaluator."
        )
        return _verdict(REJECT, "self_graded", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=True)

    # (1) No measurement at all ⇒ no lift claim ⇒ reject (honest, never a silent pass).
    if not norm.measured or norm.lift is None:
        reasons.append(
            "no measured lift (measurement_kind='unmeasured' or no delta) — there is "
            "no number to gate on; routed to review, never promoted "
            f"(policy treats unmeasured as {TREAT_UNMEASURED_AS})."
        )
        # carry the upstream blockers so a reader sees WHY it was unmeasurable
        if norm.source_blockers:
            reasons.append("upstream publish_blockers: " + ", ".join(norm.source_blockers))
        return _verdict(TREAT_UNMEASURED_AS, "unmeasured", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=True)

    # record the measured delta either way
    reasons.append(
        f"measured lift (B−A) = {norm.lift:+.6f} over n={norm.n} paired held-out "
        f"item(s); durability_class={norm.durability_class}"
        + (f" ({durability_note})" if durability_note else "")
    )

    # (2) No positive lift ⇒ reject. A zero/negative delta means the pipeline did
    #     not let the model do anything it couldn't do alone (capability-valleys.md).
    if not lift_is_positive:
        reasons.append(
            f"lift {norm.lift:+.6f} is not above the positive floor "
            f"{policy.min_promote_lift:g} — the component adds no measured capability "
            "over the bare model; rejected (the admission rule is a POSITIVE lift)."
        )
        return _verdict(REJECT, "no_lift", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=False)

    # From here the lift is positive. Whether it PROMOTES turns on durability + n +
    # evidence; anything short of all three is a real CANDIDATE (kept, not rejected).
    reasons.append(f"lift is positive (> {policy.min_promote_lift:g}) — the capability axis is cleared.")

    # (3) Durability axis: a transient lift closes with the next model ⇒ candidate,
    #     not promote (the data flywheel that found it is the data that erases it).
    if norm.durability_class == TRANSIENT_CLASS:
        reasons.append(
            "durability_class is 'transient' — the lift will close when the next "
            "base model ships (the demos that find it are the training data that "
            "erase it); real lift TODAY, but not a durable promote — held as candidate."
        )
        return _verdict(CANDIDATE, "transient_durability", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=requires_review)

    # (4) Unknown durability: positive lift but no lift_reason to assert it is
    #     structural ⇒ candidate + review (a human must assign a lift_reason; this
    #     mirrors durable_gap_harness's 'review' decision for untagged gaps).
    if not durability_ok:  # i.e. UNKNOWN_CLASS (transient handled above)
        reasons.append(
            "durability is not classified (no lift_reason in the canonical "
            "reason_codes taxonomy) — a positive lift cannot be asserted DURABLE "
            "without a reason; held as candidate pending a lift_reason assignment."
        )
        return _verdict(CANDIDATE, "durability_unclassified", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=True)

    # the durability axis is genuinely cleared (structural or mixed)
    reasons.append(
        f"durability_class '{norm.durability_class}' is non-transient — the lift is "
        "structural (will not close with more model/data/tools); durability axis cleared."
    )
    if norm.durability_class == "mixed":
        reasons.append(
            "durability is 'mixed' — part of the lift may erode; promote but the "
            "registry should re-benchmark for decay (decay_signal watch)."
        )

    # (5) Promotion-boundary evidence: any open blocker forces review and caps at
    #     candidate (CLAUDE.md Promotion Boundary). Lossless: list every blocker.
    if evidence_blockers:
        reasons.append("promotion-boundary blockers present — capped at candidate, review required: "
                       + "; ".join(evidence_blockers))
        return _verdict(CANDIDATE, "review_blocked", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=True)

    # (6) Thin paired n: positive + durable + clean, but too few paired items to
    #     assert a promote ⇒ candidate + review (gather more held-out items). The
    #     publication n-floor is the harness's own seam — carried, not satisfied here.
    if not n_sufficient:
        reasons.append(
            f"paired n={norm.n} is below the promote floor (min_promote_n="
            f"{policy.min_promote_n}) — the lift is real and durable but measured on "
            "too few held-out items to promote; held as candidate pending more items."
        )
        return _verdict(CANDIDATE, "thin_n", norm, policy, reasons,
                        lift_is_positive, durability_ok, evidence_blockers,
                        requires_review=True)

    # (7) PROMOTE: positive measured lift + non-transient durability + sufficient n +
    #     no promotion-boundary blocker + evaluator-independent. The full bar.
    reasons.append(
        "ALL promote conditions met: positive measured lift, non-transient "
        "durability, sufficient paired n, no promotion-boundary blocker, "
        "evaluator-independent judge → PROMOTE."
    )
    # Even a promote carries any UNCLEARED publication seams (e.g. no CI) as an
    # advisory — promotable into the registry, not necessarily publishable as a
    # headline number. Lossless: never drop the seam.
    if norm.source_blockers:
        reasons.append(
            "advisory — these head-to-head publish_blockers remain for a PUBLISHED "
            "headline number (not a promotion blocker): " + ", ".join(norm.source_blockers)
        )
    return _verdict(PROMOTE, "positive_lift_durable", norm, policy, reasons,
                    lift_is_positive, durability_ok, evidence_blockers,
                    requires_review=requires_review)


def _verdict(
    decision: str,
    basis: str,
    norm: NormalizedLift,
    policy: PromotionPolicy,
    reasons: list[str],
    lift_is_positive: bool,
    durability_ok: bool,
    evidence_blockers: list[str],
    *,
    requires_review: bool,
) -> dict[str, Any]:
    """Assemble the full lossless verdict dict (single place the shape is defined)."""
    assert decision in DECISIONS, f"internal: bad decision {decision!r}"
    # a non-promote that turned on a problem always requires review unless it's a
    # clean no_lift/no-lift reject (which is a definitive, reviewable-by-record cull).
    requires_review = requires_review or (decision == CANDIDATE)
    return {
        "decision": decision,
        "basis": basis,
        "lift": norm.lift,
        "durability_class": norm.durability_class,
        "lift_reason": norm.lift_reason,
        "lift_is_positive": lift_is_positive,
        "durability_ok": durability_ok,
        "n": norm.n,
        "evaluator_independent": norm.evaluator_independent,
        "requires_review": requires_review,
        "reasons": list(reasons),
        "gate_blockers": list(evidence_blockers),
        "source_publish_blockers": list(norm.source_blockers),
        "policy": policy.as_dict(),
        "normalized": {
            "lift": norm.lift,
            "durability_class": norm.durability_class,
            "n": norm.n,
            "measured": norm.measured,
            "evaluator_independent": norm.evaluator_independent,
            "lift_reason": norm.lift_reason,
            "input_keys_seen": norm.raw_keys,
        },
    }


# ── WIRE-IN (documented one-liners; NOT applied this pass) ────────────────────
#
# These are the EXACT single call sites the owner/next wave connects. They are
# stated here (and in _repos/shared-backend-components/context/status/p2-measured-lift-promotion.md) so the bridge can
# be adopted without re-deriving where it plugs in. This module does not import or
# edit either file — adopting is a one-line change in each, behind a flag.
#
# (A) Teleon runtime gate — _repos/shared-backend-components/scripts/teleon_local_runtime.py, in
#     Runtime._run_to_completion, right AFTER the existing pass-rate decision
#     (the line: `decision = ("promoted" if train_rate >= PROMOTE_AT ...)`).
#     The runtime gate proves a capability DOES ITS JOB on a held-out suite; this
#     bridge adds the orthogonal "does it LIFT a bare model, durably?" axis. One
#     line, given a measured-lift result for the capability's gap:
#
#         from scripts.eval.promotion_bridge import promotion_decision
#         lift_gate = promotion_decision(measured_lift_result, gate_evidence={
#             "high_risk_review_required": run["holdout_contaminated"]})
#         # promote only if BOTH gates agree:
#         if decision == "promoted" and lift_gate["decision"] != "promote":
#             decision = "candidate"   # passed its suite but no durable measured lift
#         run["lift_gate"] = lift_gate # attach the lossless reasoning to the receipt
#
#     (`measured_lift_result` comes from run_headtohead over the capability's
#     held-out eval items; the runtime today has no lift suite — that wiring is the
#     larger task. The bridge is ready the moment a result exists.)
#
# (B) Registry submit/review path — _repos/shared-backend-components/scripts/registry_local_service.py, in
#     RegistryStore.decide, right BEFORE recording an "approve" (the promotion to
#     the public-active catalog). Today a reviewer's approve is the only
#     candidate→active path and consults NO lift evidence. One line gates it on a
#     measured lift carried on the submission entry (entry["measured_lift"]):
#
#         from scripts.eval.promotion_bridge import promotion_decision
#         lift_gate = promotion_decision(
#             (sub.get("entry") or {}).get("measured_lift") or {"measurement_kind": "unmeasured"},
#             gate_evidence={"open_review_tickets": False})
#         if decision == "approve" and lift_gate["decision"] != "promote":
#             # block the approve (or downgrade to a 'candidate' shelf) + surface reasons
#             raise ValueError("measured-lift gate: " + "; ".join(lift_gate["reasons"]))
#
#     This makes "discovery ≠ trust" enforced by a MEASURED number, not only by a
#     reviewer's judgement. Behind a registry flag so the demo's reviewer flow is
#     unchanged until the owner enables it.


# ── CLI: --self-test (deterministic proof of every path) + --explain ──────────


def _approx(a: float | None, b: float, tol: float = 1e-9) -> bool:
    return a is not None and abs(a - b) <= tol


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── (1) END-TO-END from the REAL harness: run_headtohead → promotion_decision.
    # This is the load-bearing proof: the bridge consumes the actual output of the
    # head-to-head fixture (structural durability, positive lift) → must PROMOTE.
    from scripts.eval.measured_lift_headtohead import (
        AbstainAwareEvaluator,
        RecordedAnswerScorer,
        _FIXTURE,
        run_headtohead,
    )

    bare = RecordedAnswerScorer("bare_answer")
    pipe = RecordedAnswerScorer("pipeline_answer")
    judge = AbstainAwareEvaluator()
    real = run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=pipe, evaluator=judge)
    v_real = promotion_decision(real)
    ck("real head-to-head result (positive lift, structural) → promote",
       v_real["decision"] == PROMOTE and v_real["basis"] == "positive_lift_durable",
       f"{v_real['decision']}/{v_real['basis']}")
    ck("real result: the measured lift is carried through losslessly",
       _approx(v_real["lift"], real["lift"]) and v_real["durability_class"] == "structural")
    ck("real result: head-to-head publish_blockers carried as advisory (lossless)",
       set(real["publish_blockers"]).issubset(set(v_real["source_publish_blockers"]))
       and len(v_real["source_publish_blockers"]) > 0)
    ck("real result: reasoning chain is non-empty (never a bare verdict)",
       len(v_real["reasons"]) >= 3)

    # ── (2) PROMOTE path on a hand-built minimal result (structural + positive). ──
    promote_in = {"lift": 0.42, "durability_class": "structural", "n": 4,
                  "measurement_kind": "measured", "evaluator_independent": True,
                  "lift_reason": "no_addressable_source"}
    v = promotion_decision(promote_in)
    ck("promote: positive lift + structural + n>=floor + independent → promote",
       v["decision"] == PROMOTE and v["lift_is_positive"] and v["durability_ok"])
    ck("promote: requires_review is False on a clean promote", v["requires_review"] is False)
    ck("promote: 'mixed' durability also promotes (non-transient) + notes decay",
       promotion_decision({**promote_in, "durability_class": "mixed",
                           "lift_reason": "realtime_high_stakes_judgment"})["decision"] == PROMOTE)

    # ── (3) CANDIDATE: transient durability blocks promote (positive lift kept). ──
    transient_in = {"lift": 0.9, "durability_class": "transient", "n": 8,
                    "measurement_kind": "measured", "evaluator_independent": True,
                    "lift_reason": "long_tail_fact"}
    v = promotion_decision(transient_in)
    ck("transient durability blocks promote → candidate (real lift, no moat)",
       v["decision"] == CANDIDATE and v["basis"] == "transient_durability")
    ck("transient: durability_ok is False, lift_is_positive is True",
       v["durability_ok"] is False and v["lift_is_positive"] is True)
    ck("transient: candidate requires review", v["requires_review"] is True)

    # ── (3b) CANDIDATE: positive + structural but UNKNOWN class (no lift_reason). ──
    v = promotion_decision({"lift": 0.3, "n": 4, "measurement_kind": "measured",
                            "evaluator_independent": True})  # no durability_class/reason
    ck("unknown durability (positive lift, no reason) → candidate + review",
       v["decision"] == CANDIDATE and v["basis"] == "durability_unclassified"
       and v["durability_class"] == UNKNOWN_CLASS and v["requires_review"])

    # ── (3c) CANDIDATE: positive + durable + clean but THIN n. ──
    v = promotion_decision({"lift": 0.5, "durability_class": "structural", "n": 1,
                            "measurement_kind": "measured", "evaluator_independent": True,
                            "lift_reason": "embodiment_required"})
    ck("durable positive lift but n below promote floor → candidate (thin_n) + review",
       v["decision"] == CANDIDATE and v["basis"] == "thin_n" and v["requires_review"])

    # ── (4) REJECT: no lift (zero delta) — an identical-to-bare pipeline. ──
    v = promotion_decision({"lift": 0.0, "durability_class": "structural", "n": 4,
                            "measurement_kind": "measured", "evaluator_independent": True,
                            "lift_reason": "no_addressable_source"})
    ck("zero lift → reject (no measured capability over the bare model)",
       v["decision"] == REJECT and v["basis"] == "no_lift")
    ck("reject(no_lift): even with structural durability, no lift cannot promote",
       v["durability_ok"] is True and v["lift_is_positive"] is False)
    # negative lift (pipeline worse than bare) also rejects
    ck("negative lift → reject",
       promotion_decision({"lift": -0.2, "durability_class": "structural", "n": 4,
                           "measurement_kind": "measured", "evaluator_independent": True,
                           "lift_reason": "no_addressable_source"})["decision"] == REJECT)

    # ── (5) REJECT: self-grading is foreclosed (evaluator_independent not True). ──
    v = promotion_decision({"lift": 0.9, "durability_class": "structural", "n": 9,
                            "measurement_kind": "measured", "evaluator_independent": False,
                            "lift_reason": "no_addressable_source"})
    ck("self-graded result (evaluator_independent=False) → reject (untrustable number)",
       v["decision"] == REJECT and v["basis"] == "self_graded" and v["requires_review"])
    # a result that simply OMITS the flag is also treated as not independent (fail closed)
    ck("missing evaluator_independent flag → treated as self-graded (fail closed) → reject",
       promotion_decision({"lift": 0.9, "durability_class": "structural", "n": 9,
                           "measurement_kind": "measured",
                           "lift_reason": "no_addressable_source"})["basis"] == "self_graded")

    # ── (6) REJECT: unmeasured (no number) is never a silent pass. ──
    v = promotion_decision({"durability_class": "structural", "n": 0,
                            "measurement_kind": "unmeasured", "evaluator_independent": True,
                            "publish_blockers": ["unmeasured", "no_confidence_interval"]})
    ck("unmeasured result → reject (no number to gate on) + review + blockers carried",
       v["decision"] == REJECT and v["basis"] == "unmeasured" and v["requires_review"]
       and "no_confidence_interval" in v["source_publish_blockers"])

    # ── (7) CANDIDATE: promotion-boundary blockers cap a would-be promote. ──
    v = promotion_decision(promote_in, gate_evidence={"open_review_tickets": ["t1", "t2"]})
    ck("a clean promote with an OPEN REVIEW TICKET is capped at candidate + review",
       v["decision"] == CANDIDATE and v["basis"] == "review_blocked"
       and v["requires_review"] and any("review tickets" in b for b in v["gate_blockers"]))
    ck("placeholder embeddings also cap at candidate (promotion boundary)",
       promotion_decision(promote_in, gate_evidence={"placeholder_embeddings": True}
                          )["decision"] == CANDIDATE)
    ck("evidence 'blockers' free-list is honored",
       any("custom-block" in b for b in promotion_decision(
           promote_in, gate_evidence={"blockers": ["custom-block"]})["gate_blockers"]))

    # ── (8) measure.py shape is accepted (delta/n, no measurement_kind). ──
    # Build a real measure.py-shaped lift dict via the actual engine to prove
    # cross-surface compatibility (not a hand-faked shape).
    from scripts.foundry.measure import MeasurementStage, _cand  # type: ignore
    from scripts.foundry.contracts import FoundryContext

    tasks_good = [
        {"prompt": "q1", "correct_answer": "Article 8 CSDDD",
         "bare_answer": "Article 12 (wrong)", "pipeline_answer": "Article 8 CSDDD"},
        {"prompt": "q2", "correct_answer": "Article 29 CSDDD",
         "bare_answer": "Article 5 (wrong)", "pipeline_answer": "Article 29 CSDDD"},
    ]
    cand = _cand("gap-csddd", tasks_good, lift_reason="no_addressable_source")  # structural
    MeasurementStage().run([cand], FoundryContext())
    # measure.py lift dict has no evaluator_independent; the deterministic checker
    # is separate from the (recorded) answers, but the dict doesn't assert it — so
    # by fail-closed policy this normalizes to NOT independent → self_graded reject.
    # That is CORRECT: a surface that wants the measure.py delta to PROMOTE must
    # route it through run_headtohead (separate evaluator enforced) or assert
    # independence explicitly. Prove the shape is parsed and the lift carried:
    nshape = normalize_lift_result(cand.lift)
    ck("measure.py lift dict shape: delta parsed as lift, durability carried",
       _approx(nshape.lift, cand.lift["delta"]) and nshape.durability_class == "structural"
       and nshape.measured is True)
    ck("measure.py dict without independence flag → fail-closed self_graded reject",
       promotion_decision(cand.lift)["basis"] == "self_graded")
    ck("...but asserting independence on the same delta promotes (positive+structural)",
       promotion_decision({**cand.lift, "evaluator_independent": True})["decision"] == PROMOTE)

    # ── (9) thresholds come from CONSTANTS, not hand-typed; policy is echoed. ──
    ck("policy echoed in verdict equals the module defaults",
       v_real["policy"]["min_promote_lift"] == DEFAULT_MIN_PROMOTE_LIFT
       and v_real["policy"]["min_promote_n"] == DEFAULT_MIN_PROMOTE_N)
    ck("promote_durability_classes is COMPUTED from the taxonomy (== non-transient)",
       set(DEFAULT_POLICY.promote_durability_classes) == set(DURABILITY_CLASSES) - {TRANSIENT_CLASS})
    # a custom (tighter) policy changes the bar AND is reflected in the verdict
    strict = PromotionPolicy(min_promote_n=5)
    v_strict = promotion_decision(promote_in, policy=strict)  # n=4 < 5 now
    ck("tighter policy (min_promote_n=5) downgrades the n=4 promote to candidate(thin_n)",
       v_strict["decision"] == CANDIDATE and v_strict["basis"] == "thin_n"
       and v_strict["policy"]["min_promote_n"] == 5)
    # a policy that tries to allow transient durability is refused at construction
    refused = False
    try:
        PromotionPolicy(promote_durability_classes=frozenset({"structural", "transient"}))
    except ValueError:
        refused = True
    ck("a policy allowing 'transient' to promote is refused (transient never durable)", refused)
    refused2 = False
    try:
        PromotionPolicy(min_promote_lift=0.0)  # a lift must be positive to gate
    except ValueError:
        refused2 = True
    ck("a policy with non-positive min_promote_lift is refused", refused2)

    # ── (10) the reason_codes taxonomy is NOT re-defined here (single source). ──
    # Prove the bridge's promote-class set is derived from the canonical enum and
    # that we never shadowed durability_class / DURABILITY_CLASSES with a local copy.
    import scripts.eval.promotion_bridge as mod
    redefimed = [name for name in ("DURABILITY_CLASSES", "LIFT_REASONS", "durability_class")
                 if name in vars(mod) and name in vars(__import__("scripts.eval.reason_codes",
                                                                   fromlist=[name]))
                 and vars(mod)[name] is not getattr(__import__("scripts.eval.reason_codes",
                                                               fromlist=[name]), name)]
    ck("reason_codes taxonomy is IMPORTED, never re-defined (same objects)", not redefimed,
       f"shadowed: {redefimed}")

    # ── (11) DETERMINISM: same inputs → byte-identical verdict (no clock/RNG/IO). ──
    a = promotion_decision(promote_in, gate_evidence={"open_review_tickets": False})
    b = promotion_decision(promote_in, gate_evidence={"open_review_tickets": False})
    ck("deterministic: identical inputs → identical verdict (incl. reasons)",
       json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True))

    # ── (12) every decision value is one of the three named, and is JSON-serializable.
    for case in (v_real, promote_in and promotion_decision(promote_in), v, v_strict):
        ck("decision is one of promote|candidate|reject and the verdict serializes",
           isinstance(case, dict) and case["decision"] in DECISIONS
           and json.loads(json.dumps(case))["decision"] in DECISIONS)

    print("\n" + ("PASS — promotion_bridge: measured lift gates promotion. "
                  f"REAL run_headtohead fixture → {v_real['decision']} "
                  f"(lift {v_real['lift']:+.3f}, durability {v_real['durability_class']}); "
                  "transient durability blocks promote→candidate; no/negative/zero lift→reject; "
                  "self-graded (or independence-unproven)→reject; unmeasured→reject; "
                  "promotion-boundary blocker (open review ticket / placeholder embeddings)"
                  "→candidate+review; thin n→candidate; thresholds from named constants + the "
                  "promote-durability set COMPUTED from reason_codes (taxonomy never re-defined); "
                  "deterministic re-run identical."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _explain(result_path: str, evidence_path: str | None) -> int:
    """Read a JSON lift result (+ optional evidence) and print the decision."""
    with open(result_path, encoding="utf-8") as fh:
        result = json.load(fh)
    evidence = None
    if evidence_path:
        with open(evidence_path, encoding="utf-8") as fh:
            evidence = json.load(fh)
    verdict = promotion_decision(result, gate_evidence=evidence)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    # exit non-zero on reject so the CLI is usable as a gate in a shell pipeline
    return 0 if verdict["decision"] in (PROMOTE, CANDIDATE) else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Measured-lift → promotion gate: turn a head-to-head lift result "
                    "into a promote/candidate/reject decision (lift + durability).")
    p.add_argument("--self-test", action="store_true",
                   help="Run the deterministic self-test (every path).")
    p.add_argument("--explain", metavar="LIFT_RESULT_JSON",
                   help="Path to a JSON lift result (run_headtohead output or a "
                        "measure.py lift dict); prints the promotion decision.")
    p.add_argument("--evidence", metavar="GATE_EVIDENCE_JSON",
                   help="Optional path to a JSON gate_evidence object "
                        "(open_review_tickets, placeholder_embeddings, …).")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.explain:
        return _explain(args.explain, args.evidence)
    p.error("one of --self-test or --explain is required")
    return 2  # unreachable (argparse error exits), kept for type-checkers


if __name__ == "__main__":
    raise SystemExit(_main())
