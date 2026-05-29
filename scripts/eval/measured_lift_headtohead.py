#!/usr/bin/env python3
"""Measured-lift head-to-head — the runnable harness for OHH's #1 differentiator.

This is the **paired, separately-judged, held-out** protocol that produces the one
number `docs/strategy/measured-lift-head-to-head.md` specifies and the Contextual
verdict demands ("do this for real or not at all"): on a shared domain task over a
governed corpus, does the OHH pipeline lift a bare model's accuracy by a *measured*
margin, judged by a *separate* evaluator, and is that lift *structural* (it will
not close when the next base model ships)?

It is the M4 milestone of `docs/codex/north-star.md` — "the credibility + the
differentiator (currently THIN): a paired pipeline-vs-bare-model protocol scored
by a separate evaluator, runnable on a fixture now and on a live model route when
available."

WHAT IS REAL HERE vs WHAT IS A SEAM (honesty first — change-verification-contract):
  REAL (runs offline, deterministically, in this network-blocked environment):
    * the paired protocol: per-item and aggregate `pipeline_score − bare_score`
      (the admission-gate lift, B−A) and `pipeline_score − contextual_score`
      (the head-to-head, B−C — the number Contextual's demos never publish);
    * a SEPARATE evaluator object, structurally distinct from any scorer it grades
      (`run_headtohead` *raises* if you pass the same object as a scorer AND the
      evaluator — self-grading cannot happen by construction, the §5 trap);
    * the durability axis: a `durability_class` from the canonical taxonomy
      (`scripts.eval.reason_codes` — imported, never re-defined here), so the lift
      ships paired with "will the next model erase it" (§7);
    * deterministic offline stub scorers so the harness runs end-to-end with NO
      model — they return *recorded* answers / fixed deterministic behaviours, they
      never invent a quality number.
  SEAM (NOT faked — explicitly unwired here, wired the moment a route exists):
    * the live model route for the answer arms and a *different-family* judge route
      (`scripts/foundry/model_route.py`; today it shares one route across
      bare/pipeline/judge — the doc's gap-1, which must be fixed before publishing);
    * bootstrap/Wilson confidence intervals + `MIN_EVAL_TASKS` + judge↔human
      calibration + the publish-or-don't CI gate (doc §6/§8) — this harness emits
      the per-item paired scores the interval is computed from and records the
      `publish_blockers`, but does not compute a CI or clear the gate offline;
    * wrapping Contextual's LMUnit (arXiv:2412.13091) as a selectable judge behind
      `processor/eval/llm-judge` (doc §5) — arm C / the judge are pluggable here.
  HONEST RULE (restated): there are **no invented lift numbers**. The fixture's
  numbers are real token-F1 scores of fixed stub answers; a real head-to-head
  number requires the live route + the §8 gate, which is the seam.

No-Magic-Values: the token scorer and the `Judge.score(task, answer)` protocol are
IMPORTED from `scripts.foundry.measure` (the lift engine) — one definition of
"token score", reused — and the durability taxonomy is imported from
`scripts.eval.reason_codes`. This module adds the *head-to-head comparison design*
(three arms, separate-evaluator enforcement, per-family breakout) on top of those.

Public API:
    from scripts.eval.measured_lift_headtohead import run_headtohead
    out = run_headtohead(items, bare_model_scorer=..., pipeline_scorer=...,
                         evaluator=..., contextual_scorer=...)
    # -> {"lift", "bare_mean", "pipeline_mean", "per_item",
    #     "durability_class", "n", "evaluator", ... (auditable detail)}

CLI / self-test (proves the protocol on a bundled fixture, no model, no network):
    python3 scripts/eval/measured_lift_headtohead.py
    python3 -m scripts.eval.measured_lift_headtohead
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable

# Make the repo root importable when run *directly* (the repo has no top-level
# scripts/__init__.py; it is a namespace package run via -m from the root). This
# orchestrator must COMPOSE scripts.* (it imports the lift engine's scorer + the
# durability taxonomy), so it cannot be self-contained. Stdlib only; no-op under -m.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Canonical durability taxonomy — single source, never re-defined (CLAUDE.md /
# reason_codes.py header). We classify the lift's durability, we don't re-enumerate.
from scripts.eval.reason_codes import DURABILITY_CLASSES, durability_class

# The token scorer AND the Judge protocol shape — IMPORTED from the lift engine so
# "token score" / "what an evaluator is" has ONE definition (no-magic-values). The
# evaluator below is exactly measure.py's `Judge`: `.name` + `.score(task, answer)`.
from scripts.foundry.measure import Judge, token_f1

# ── The three arms (the comparison design — doc §2) ──────────────────────────
#
# Single source of truth for the arm vocabulary used by the per-item record, the
# aggregates, and the head-to-head deltas. Defined ONCE so a rename can't drift.
ARM_BARE = "bare"               # A — frontier base model, closed-book (the floor)
ARM_PIPELINE = "pipeline"       # B — the OHH governed pipeline (the product)
ARM_CONTEXTUAL = "contextual"   # C — Contextual-style clean-RAG over public docs

#: All arms in report order. Bare and pipeline are required; contextual is optional
#: (the head-to-head slot — present only when a `contextual_scorer` is supplied).
ARMS: tuple[str, ...] = (ARM_BARE, ARM_PIPELINE, ARM_CONTEXTUAL)

#: The minimum dev n. This is a DEVELOPMENT floor only — it lets the harness run on
#: a tiny fixture. It is deliberately NOT the publication minimum: the publish gate
#: (doc §6/§8, `MIN_EVAL_TASKS`) is a SEAM, recorded in `publish_blockers`, not
#: enforced here. Mirrors measure.py's n=2 offline self-test floor.
MIN_DEV_ITEMS = 1

#: Honest record of what stays a SEAM after this harness runs — carried in the
#: result so a consumer sees the gap, not buried in prose. These are the doc §6/§8
#: publication preconditions this OFFLINE harness intentionally does not satisfy.
PUBLISH_SEAMS: tuple[str, ...] = (
    "live model route — scripts/foundry/model_route.py wires the answer arms; today "
    "it shares ONE route across bare/pipeline/judge (doc gap-1). A publishable "
    "number needs a SEPARATE judge route (different model family).",
    "judge independence at the MODEL level — this harness enforces OBJECT separation "
    "(evaluator is not a scorer); judge_model_family != answer_model_family (doc §5) "
    "is checkable only once real routes exist.",
    "bootstrap/Wilson confidence interval + MIN_EVAL_TASKS + promote-on-lower-bound "
    "(doc §6) — per-item paired scores are emitted here so a CI is reproducible, but "
    "the CI and the n-floor are not computed/enforced offline.",
    "open-book contamination guard — answer_in_grounding items must be split out of "
    "the headline (doc §4); items carry the flag here, the gate is a seam.",
    "judge↔human calibration (Cohen's kappa) published next to the number (doc §5).",
    "LMUnit (Contextual, arXiv:2412.13091) as a selectable judge behind "
    "processor/eval/llm-judge (doc §5) — the evaluator is pluggable for exactly this.",
)

#: Declared runtime-routing signals (change-verification-contract: declare them).
#: Deterministic GIVEN deterministic scorers + evaluator (the fixture uses such);
#: a live model route makes the answer arms non-deterministic — that is the seam,
#: and `deterministic` then describes only this orchestrator's own logic.
RUNTIME: dict[str, Any] = {
    "process_kind": "eval.measured_lift_headtohead",
    "deterministic": True,      # this module adds no clock/RNG/IO; det. iff scorers are
    "idempotent": True,         # pure function of (items, scorers, evaluator)
    "side_effects": "none",     # reads nothing, writes nothing
    "on_error": "raise",        # bad wiring (self-grading, no scorers) raises, never silent
}


# ── Pluggable scorer protocol ────────────────────────────────────────────────
#
# A "scorer" produces an arm's ANSWER for an item; the SEPARATE evaluator then
# grades that answer. This split is the whole anti-self-grading point: the thing
# that answers is never the thing that scores. A scorer is any callable
# (item: dict) -> answer-string, so a live model route, a recorded-answer reader,
# or a fixture stub all satisfy it without a base class.
Scorer = Callable[[dict[str, Any]], "str | None"]


@runtime_checkable
class Evaluator(Protocol):
    """The SEPARATE judge — same shape as measure.py's `Judge` (imported).

    `score(item, answer) -> float in [0,1] | None`. It must be a DIFFERENT object
    from every arm's scorer (enforced in `run_headtohead`) — and, in production, a
    different model family (the seam). It grades; it does not answer.
    """

    name: str

    def score(self, item: dict[str, Any], answer: "str | None") -> "float | None":
        ...


# ── Offline deterministic stub scorers / evaluator (the fixture runs with NO model)
#
# These exist so the harness PROVES the protocol logic without a model. They are
# honest: they return fixed/recorded answers, never a fabricated quality number.


class RecordedAnswerScorer:
    """A scorer that returns an arm's answer RECORDED on the item (no model call).

    This is the offline path measure.py uses: score the *recorded* bare/pipeline
    answers carried on a held-out item, measuring real outputs rather than inventing
    them. `field` selects which recorded answer (e.g. ``"bare_answer"``).
    """

    def __init__(self, field: str, *, name: str | None = None) -> None:
        self.field = field
        self.name = name or f"recorded:{field}"

    def __call__(self, item: dict[str, Any]) -> str | None:
        value = item.get(self.field)
        return None if value is None else str(value)


class AbstainAwareEvaluator:
    """Separate deterministic evaluator (a `Judge`): token-F1, abstain-aware.

    Reuses the IMPORTED ``token_f1`` (one definition of "token score") against
    ``item['correct_answer']`` — EXCEPT for the negative-space family (doc §3,
    family 3) where the correct response is to *abstain and route to an authority*.
    There, "did the arm abstain?" is a DETERMINISTIC, self-grading-proof check (doc
    §5): an arm that abstains scores 1.0, an arm that confidently answers scores
    0.0. This is exactly where ``grounding != lift`` becomes a number — arm C
    answers-by-default and is wrong; arm B abstains and is right.

    Honest scope: this is a deterministic CHECKER, the offline stand-in for the
    LLM-judge / LMUnit seam. It is *separate* from the scorers by construction.
    """

    name = "abstain-aware-f1"

    #: Substrings that mark an abstain-and-route response (deterministic detector).
    _ABSTAIN_MARKERS: tuple[str, ...] = (
        "unanswerable", "abstain", "route to", "cannot be determined",
        "not available in the", "refer to", "no addressable source",
    )

    def _is_abstain(self, text: str) -> bool:
        low = text.lower()
        return any(m in low for m in self._ABSTAIN_MARKERS)

    def score(self, item: dict[str, Any], answer: str | None) -> float | None:
        if answer is None:
            return None
        # Negative-space / abstain-correct family: grade the DECISION, not the words.
        if item.get("item_family") == "abstain_correct" or bool(item.get("abstain_correct")):
            return 1.0 if self._is_abstain(answer) else 0.0
        gold = item.get("correct_answer")
        if gold is None:
            return None
        return token_f1(str(answer), str(gold))


# ── Aggregation helpers (deterministic, stdlib) ──────────────────────────────


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 6) if xs else None


def _is_separate(a: object, b: object) -> bool:
    """True iff ``a`` and ``b`` are distinct objects (identity, not equality).

    The anti-self-grading guard: the evaluator must not BE any arm's scorer. We use
    identity so two independent stubs that merely *look* alike are still allowed —
    what is forbidden is literally reusing the answering object to also grade.
    """
    return a is not b


# ── Public entrypoint ─────────────────────────────────────────────────────────


def run_headtohead(
    items: list[dict[str, Any]],
    *,
    bare_model_scorer: Scorer,
    pipeline_scorer: Scorer,
    evaluator: Evaluator,
    contextual_scorer: Scorer | None = None,
    lift_reason: str | None = None,
) -> dict[str, Any]:
    """Run the paired, separately-judged head-to-head over held-out ``items``.

    Args:
      items: held-out eval items, each a dict shaped like the ``eval_tasks`` row
        ``measure.py`` consumes (doc §3):
        ``{"prompt", "correct_answer", "item_family"?, "lift_reason"?,
           "answer_in_grounding"?, ...}`` plus any recorded answers a stub reads.
      bare_model_scorer:  arm A — produces the bare model's answer for an item.
      pipeline_scorer:    arm B — produces the OHH governed pipeline's answer.
      evaluator:          the SEPARATE judge (an ``Evaluator``/``Judge``). MUST be a
        different object from every scorer — passing a scorer as the evaluator
        raises ``ValueError`` (self-grading is impossible by construction, doc §5).
      contextual_scorer:  arm C (optional) — a Contextual-style clean-RAG answer.
        When supplied, the result carries the ``pipeline − contextual`` head-to-head
        delta (B−C), the number a Contextual demo does not publish.
      lift_reason: optional family-level ``lift_reason`` (``reason_codes.LIFT_REASONS``)
        used for the aggregate ``durability_class`` when items don't carry their own.

    Returns a dict whose **headline keys are exactly the seven the M4 task names**
    plus auditable detail:

      ``lift``            — aggregate ``pipeline_mean − bare_mean`` (B−A; the
                            admission-gate lift). ``None`` if either arm is unscored.
      ``bare_mean``       — mean evaluator score of arm A over scored items.
      ``pipeline_mean``   — mean evaluator score of arm B.
      ``per_item``        — per-item paired record (each arm's answer + score + the
                            per-item lift) — the rows a bootstrap CI is computed
                            from (doc §6); persisted so the interval is reproducible.
      ``durability_class``— ``transient`` | ``structural`` | ``mixed`` | ``unknown``
                            for the lift (doc §7), from the canonical taxonomy.
      ``n``               — number of items SCORED on both required arms (the paired
                            denominator), not merely supplied.
      ``evaluator``       — the evaluator's ``name`` (so the report shows WHO judged;
                            distinct from the arms — the separateness is enforced).
      ``head_to_head``    — ``{ "B-A", "B-C", "C-A" }`` deltas (doc §6); ``B-C``/``C-A``
                            are ``None`` when no ``contextual_scorer`` was supplied.
      ``arm_means``       — mean score per present arm.
      ``by_family``       — B−A / B−C broken out per ``item_family`` (doc §6: shows
                            WHERE the lift comes from — negative-space, not controls).
      ``fidelity``        — the extraction-fidelity caveat (doc §4): the fraction of
                            scored items whose answer was verbatim in the grounding
                            (``answer_in_grounding``) — these test copying, not lift,
                            and must be split from a headline. (Lift != fidelity.)
      ``evaluator_independent`` — ``True`` (object-level: evaluator is not a scorer).
        Model-level independence is the seam (see ``publish_blockers``).
      ``measurement_kind``— ``"measured"`` once both arms scored ``n>=MIN_DEV_ITEMS``
                            items, else ``"unmeasured"`` (mirrors measure.py; never a
                            fabricated number).
      ``publish_blockers``— the doc §8 qualifiers this OFFLINE run does NOT clear
                            (CI, model-level judge independence, calibration, …) — so
                            the result is honestly un-publishable until the seam lands.
      ``runtime``         — the declared routing signals (``RUNTIME``).
      ``seams``           — ``PUBLISH_SEAMS`` (what stays unwired, stated plainly).

    Raises:
      ValueError: if ``items`` is empty, or the ``evaluator`` is the SAME object as
        any scorer (the self-grading guard — doc §5), or two distinct answer arms
        share one scorer object (would silently make a delta trivially 0).
      TypeError:  if a scorer is not callable or the evaluator has no ``score``.

    Deterministic GIVEN deterministic scorers + evaluator (the fixture's are);
    pure; no side effects.
    """
    if not items:
        raise ValueError("run_headtohead needs at least one held-out item")

    # --- wiring validation (fail loud — on_error: raise) ---
    scorers: dict[str, Scorer] = {ARM_BARE: bare_model_scorer, ARM_PIPELINE: pipeline_scorer}
    if contextual_scorer is not None:
        scorers[ARM_CONTEXTUAL] = contextual_scorer

    # The anti-self-grading guard FIRST (doc §5): the evaluator may not BE any scorer,
    # and the two REQUIRED answer arms may not share one scorer object (that would make
    # B−A a trivial, meaningless 0). Identity check — structural, not heuristic. This
    # runs BEFORE the type checks on purpose: an object handed in as both a scorer and
    # the evaluator is a self-grading error regardless of whether it happens to be
    # callable, and that is the more specific, more important diagnosis to surface.
    for arm, scorer in scorers.items():
        if not _is_separate(evaluator, scorer):
            raise ValueError(
                f"evaluator is the SAME object as the {arm} scorer — self-grading is "
                "forbidden (measured-lift-head-to-head.md §5). Pass a separate evaluator."
            )
    if not _is_separate(bare_model_scorer, pipeline_scorer):
        raise ValueError(
            "bare and pipeline scorers are the SAME object — the lift would be a "
            "trivial 0. The arms must be distinct (measured-lift-head-to-head.md §2)."
        )

    # Then the shape checks: each scorer answers (callable), the evaluator grades.
    for arm, scorer in scorers.items():
        if not callable(scorer):
            raise TypeError(f"{arm} scorer must be callable, got {type(scorer).__name__}")
    if not hasattr(evaluator, "score") or not callable(getattr(evaluator, "score")):
        raise TypeError("evaluator must have a callable .score(item, answer) method")

    # --- run every arm on every item, grade with the SEPARATE evaluator ---
    per_item: list[dict[str, Any]] = []
    arm_scores: dict[str, list[float]] = {arm: [] for arm in scorers}
    answer_in_grounding_scored = 0

    for idx, item in enumerate(items):
        prompt = item.get("prompt", item.get("task", ""))
        family = item.get("item_family") or ("abstain_correct" if item.get("abstain_correct") else None)

        answers: dict[str, str | None] = {}
        scores: dict[str, float | None] = {}
        for arm, scorer in scorers.items():
            ans = scorer(item)
            answers[arm] = ans
            sc = evaluator.score(item, ans)
            scores[arm] = sc
            if sc is not None:
                arm_scores[arm].append(sc)

        bare_s = scores[ARM_BARE]
        pipe_s = scores[ARM_PIPELINE]
        comp_s = scores.get(ARM_CONTEXTUAL)
        # Item is "scored" (counts toward n / the headline) iff BOTH required arms
        # produced a number — the paired denominator (doc §6).
        scored = bare_s is not None and pipe_s is not None
        if scored and bool(item.get("answer_in_grounding")):
            answer_in_grounding_scored += 1

        per_item.append({
            "i": idx,
            "prompt": prompt,
            "item_family": family,
            "lift_reason": item.get("lift_reason", lift_reason),
            "answer_in_grounding": bool(item.get("answer_in_grounding")),
            "scored": scored,
            "answers": answers,
            "scores": scores,
            # per-item paired lift (B−A); the row a bootstrap CI is built from (doc §6)
            "lift": (round(pipe_s - bare_s, 6) if scored else None),
            "head_to_head_BC": (round(pipe_s - comp_s, 6) if (pipe_s is not None and comp_s is not None) else None),
        })

    # --- aggregates (paired by item; means over scored items) ---
    arm_means: dict[str, float | None] = {arm: _mean(s) for arm, s in arm_scores.items()}
    bare_mean = arm_means[ARM_BARE]
    pipeline_mean = arm_means[ARM_PIPELINE]
    contextual_mean = arm_means.get(ARM_CONTEXTUAL)

    n_scored = sum(1 for r in per_item if r["scored"])
    measured = (bare_mean is not None and pipeline_mean is not None and n_scored >= MIN_DEV_ITEMS)

    lift = round(pipeline_mean - bare_mean, 6) if (bare_mean is not None and pipeline_mean is not None) else None
    bc = (round(pipeline_mean - contextual_mean, 6)
          if (pipeline_mean is not None and contextual_mean is not None) else None)
    ca = (round(contextual_mean - bare_mean, 6)
          if (contextual_mean is not None and bare_mean is not None) else None)

    # --- per-family breakout (doc §6: WHERE the lift comes from) ---
    by_family: dict[str, dict[str, Any]] = {}
    for r in per_item:
        if not r["scored"]:
            continue
        fam = r["item_family"] or "unspecified"
        slot = by_family.setdefault(fam, {"n": 0, "_ba": [], "_bc": []})
        slot["n"] += 1
        slot["_ba"].append(r["lift"])
        if r["head_to_head_BC"] is not None:
            slot["_bc"].append(r["head_to_head_BC"])
    for fam, slot in by_family.items():
        slot["lift_BA"] = _mean(slot.pop("_ba"))
        bc_vals = slot.pop("_bc")
        slot["lift_BC"] = _mean(bc_vals) if bc_vals else None

    # --- durability: aggregate over item lift_reasons, else the family-level one ---
    reasons = {r["lift_reason"] for r in per_item if r["scored"] and r["lift_reason"]}
    if not reasons and lift_reason:
        reasons = {lift_reason}
    classes = {durability_class(r) for r in reasons}
    if "structural" in classes:
        agg_class = "structural"
    elif "mixed" in classes:
        agg_class = "mixed"
    elif classes == {"transient"}:
        agg_class = "transient"
    elif "transient" in classes:        # mixed bag of transient + unknown
        agg_class = "mixed"
    else:
        agg_class = "unknown"
    assert agg_class in (*DURABILITY_CLASSES, "unknown")   # taxonomy is the single source

    # --- the doc §8 publish qualifiers this OFFLINE run does NOT clear (honest) ---
    publish_blockers: list[str] = [
        "no_confidence_interval",            # doc §6: bootstrap/Wilson CI not computed offline
        "model_level_judge_independence_unverified",  # doc §5: needs real, different-family routes
        "no_judge_human_calibration",        # doc §5: kappa not measured offline
        "below_publication_min_n",           # doc §6: MIN_EVAL_TASKS is a seam, not MIN_DEV_ITEMS
    ]
    if answer_in_grounding_scored:
        publish_blockers.append("answer_in_grounding_items_in_headline")  # doc §4
    if not measured:
        publish_blockers.append("unmeasured")

    return {
        # ── the seven headline keys the M4 task names ──
        "lift": lift,
        "bare_mean": bare_mean,
        "pipeline_mean": pipeline_mean,
        "per_item": per_item,
        "durability_class": agg_class,
        "n": n_scored,
        "evaluator": getattr(evaluator, "name", evaluator.__class__.__name__),
        # ── head-to-head + auditable detail ──
        "head_to_head": {"B-A": lift, "B-C": bc, "C-A": ca},
        "arm_means": arm_means,
        "by_family": by_family,
        "fidelity": {
            # doc §4: lift != fidelity. Fraction of scored items whose answer was
            # verbatim in the grounding (tests copying, must be split from a headline).
            "answer_in_grounding_scored": answer_in_grounding_scored,
            "answer_in_grounding_fraction": (
                round(answer_in_grounding_scored / n_scored, 6) if n_scored else None),
            "note": "extraction-fidelity, NOT lift — exclude these from a headline (doc §4)",
        },
        "evaluator_independent": True,   # object-level (enforced above); model-level = seam
        "measurement_kind": "measured" if measured else "unmeasured",
        "publish_blockers": publish_blockers,
        "runtime": dict(RUNTIME),
        "seams": list(PUBLISH_SEAMS),
    }


# ── Self-test (proves the protocol on a bundled fixture; no model, no network) ──

# A held-out fixture spanning the doc §3 item families. Each item carries a
# `correct_answer` (the gold) and the three arms' RECORDED answers — so deterministic
# stubs can replay them with NO model. The answers are authored to encode a HONEST
# reality, not a flattering one:
#   * the pipeline genuinely helps on the long-tail/volatile/abstain families;
#   * on the addressable CONTROL item, the bare model already gets it right and the
#     pipeline adds nothing (lift 0 there) — honesty ballast (doc §3, family 4);
#   * arm C (clean-RAG) wins/ties on the control but CONFIDENTLY HALLUCINATES on the
#     negative-space item where it should abstain (doc §3, family 3 — grounding!=lift).
_FIXTURE: list[dict[str, Any]] = [
    # family 1 — answerable-from-corpus long-tail clause (bare gets it wrong)
    {"prompt": "Under the PH Fire Code IRR, what is the minimum required width of an exit corridor for an occupant load over 50?",
     "correct_answer": "1.12 meters (44 inches)", "item_family": "answerable_corpus",
     "lift_reason": "esoteric_rule", "answer_in_grounding": False,
     "bare_answer": "about 0.9 meters", "pipeline_answer": "1.12 meters (44 inches)",
     "contextual_answer": "1.0 meters"},
    # family 2 — volatile / freshness (bare's snapshot is stale; corpus is CDC-fresh)
    {"prompt": "What is the CURRENT renumbered IRR clause for the recruitment-fee ban after the 2026 amendment?",
     "correct_answer": "Section 5.3.2 (renumbered from 5.2.1)", "item_family": "volatile",
     "lift_reason": "volatile_fact", "answer_in_grounding": False,
     "bare_answer": "Section 5.2.1", "pipeline_answer": "Section 5.3.2 (renumbered from 5.2.1)",
     "contextual_answer": "Section 5.2.1"},
    # family 3 — negative-space / abstain-correct (arm C hallucinates; arm B abstains)
    {"prompt": "What was the as-built floor count of the unpermitted annex at site 12-B?",
     "correct_answer": "unanswerable from the available sources; route to the local building official (embodiment-required, counter-only permit record)",
     "item_family": "abstain_correct", "lift_reason": "no_addressable_source",
     "answer_in_grounding": False,
     "bare_answer": "It has 4 floors.",
     "pipeline_answer": "Unanswerable from the available sources; route to the local building official for an on-site verification.",
     "contextual_answer": "The annex has 3 floors."},   # confident + wrong (grounding != lift)
    # family 4 — addressable CONTROL (bare already correct; pipeline adds NO lift here)
    {"prompt": "What does the acronym BFP stand for in PH building safety?",
     "correct_answer": "Bureau of Fire Protection", "item_family": "control",
     "lift_reason": "long_tail_fact", "answer_in_grounding": True,   # gold is in the grounding span
     "bare_answer": "Bureau of Fire Protection", "pipeline_answer": "Bureau of Fire Protection",
     "contextual_answer": "Bureau of Fire Protection"},
]


def _approx(a: float | None, b: float, tol: float = 1e-9) -> bool:
    return a is not None and abs(a - b) <= tol


def _selftest() -> None:
    # Distinct, separate objects: three answer scorers + ONE separate evaluator.
    bare = RecordedAnswerScorer("bare_answer")
    pipe = RecordedAnswerScorer("pipeline_answer")
    ctx = RecordedAnswerScorer("contextual_answer")
    judge = AbstainAwareEvaluator()

    out = run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=pipe,
                         evaluator=judge, contextual_scorer=ctx)

    # ── (1) Headline contract: the seven named keys are present and well-typed. ──
    for key in ("lift", "bare_mean", "pipeline_mean", "per_item",
                "durability_class", "n", "evaluator"):
        assert key in out, f"missing headline key: {key!r}"
    assert out["n"] == len(_FIXTURE), f"all fixture items should score, got n={out['n']}"
    assert len(out["per_item"]) == len(_FIXTURE)

    # ── (2) A pipeline that GENUINELY helps shows clearly positive lift (no fake). ──
    # The pipeline is right on 3/4 families and ties the bare on the control; the
    # bare is wrong on 3/4. So B-A must be strongly positive — a REAL token-F1 delta.
    assert out["lift"] is not None and out["lift"] > 0.3, \
        f"a genuinely-helpful pipeline must show clear positive lift, got {out['lift']}"
    assert out["pipeline_mean"] > out["bare_mean"], "pipeline_mean must exceed bare_mean"
    assert _approx(out["lift"], out["pipeline_mean"] - out["bare_mean"]), \
        "headline lift must equal pipeline_mean - bare_mean (paired aggregate)"
    assert out["measurement_kind"] == "measured"

    # ── (3) The control item shows NO lift (honesty ballast — not every item lifts). ──
    control = next(r for r in out["per_item"] if r["item_family"] == "control")
    assert _approx(control["lift"], 0.0), \
        f"the addressable control must show ~0 lift (bare already correct), got {control['lift']}"
    # ...and the negative-space item is where the pipeline separates from BOTH others.
    neg = next(r for r in out["per_item"] if r["item_family"] == "abstain_correct")
    assert _approx(neg["scores"][ARM_PIPELINE], 1.0), "pipeline should abstain-correct here"
    assert _approx(neg["scores"][ARM_BARE], 0.0), "bare should confidently (wrongly) answer"
    assert _approx(neg["scores"][ARM_CONTEXTUAL], 0.0), \
        "arm C (clean-RAG) should confidently hallucinate here — grounding != lift"
    assert _approx(neg["head_to_head_BC"], 1.0), "B-C must be maximal on the negative-space item"

    # ── (4) An IDENTICAL-TO-BARE pipeline shows ~0 lift (no fabricated positive). ──
    # Same fixture, but the 'pipeline' arm reads the *bare* answers. The harness must
    # report ~0 lift — proving it measures a real delta, not an assumed win.
    pipe_eq_bare = RecordedAnswerScorer("bare_answer", name="pipeline-identical-to-bare")
    out_eq = run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=pipe_eq_bare,
                            evaluator=judge)
    assert _approx(out_eq["lift"], 0.0), \
        f"an identical-to-bare pipeline MUST show ~0 lift (no fake positive), got {out_eq['lift']}"
    assert all(_approx(r["lift"], 0.0) for r in out_eq["per_item"]), \
        "every per-item lift must be ~0 when the pipeline equals the bare model"

    # ── (5) The evaluator is SEPARATE from the scored pipeline (not self-graded). ──
    # (a) reported evaluator name is the judge's, distinct from the arms;
    assert out["evaluator"] == judge.name == "abstain-aware-f1"
    assert out["evaluator_independent"] is True
    # (b) passing the SAME object as a scorer AND the evaluator must RAISE — the
    #     self-grading trap (doc §5) is foreclosed by construction, not by hope.
    raised = False
    try:
        run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=judge,  # judge grades itself
                       evaluator=judge)
    except ValueError as e:
        raised = "self-grading" in str(e).lower()
    assert raised, "reusing the evaluator as a scorer MUST raise (no self-grading)"
    # (c) two identical answer arms (same object) must also raise (trivial-0 guard).
    raised2 = False
    try:
        run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=bare, evaluator=judge)
    except ValueError:
        raised2 = True
    assert raised2, "reusing one scorer for both required arms MUST raise"

    # ── (6) Durability class comes from the canonical taxonomy and is structural. ──
    # The fixture's reasons include no_addressable_source/volatile_fact (structural)
    # → the aggregate must be structural (the moat axis Contextual lacks, doc §7).
    assert out["durability_class"] == "structural", \
        f"fixture has structural lift_reasons → structural, got {out['durability_class']}"
    assert durability_class("no_addressable_source") == "structural"   # taxonomy unchanged

    # ── (7) Head-to-head (B-C) is reported and positive; per-family breakout present. ──
    assert out["head_to_head"]["B-A"] == out["lift"]
    assert out["head_to_head"]["B-C"] is not None and out["head_to_head"]["B-C"] > 0.0, \
        "B-C (vs Contextual-style clean-RAG) should be positive on this negative-space fixture"
    assert set(out["by_family"]) == {"answerable_corpus", "volatile", "abstain_correct", "control"}
    assert _approx(out["by_family"]["control"]["lift_BA"], 0.0), "control family shows no B-A lift"
    assert out["by_family"]["abstain_correct"]["lift_BA"] > 0.0

    # ── (8) lift != fidelity (doc §4): the control's gold was in the grounding → it is
    #        counted as extraction-fidelity, and flagged as a publish blocker. ──
    assert out["fidelity"]["answer_in_grounding_scored"] == 1, \
        "the control item (answer_in_grounding) must be counted toward fidelity, not lift"
    assert "answer_in_grounding_items_in_headline" in out["publish_blockers"]

    # ── (9) HONEST publish posture: the offline run is NOT publishable (seam blockers). ──
    for blocker in ("no_confidence_interval", "model_level_judge_independence_unverified",
                    "no_judge_human_calibration", "below_publication_min_n"):
        assert blocker in out["publish_blockers"], f"missing honest publish blocker: {blocker}"
    assert out["seams"] == list(PUBLISH_SEAMS) and out["seams"], "seams must be carried, not hidden"

    # ── (10) Determinism: a re-run is byte-identical (no clock/RNG/IO in this module). ──
    out2 = run_headtohead(_FIXTURE, bare_model_scorer=bare, pipeline_scorer=pipe,
                          evaluator=judge, contextual_scorer=ctx)
    assert out2 == out, "harness is not deterministic on deterministic scorers (re-run differed)"

    # ── (11) Empty items raises (on_error: raise — no silent empty result). ──
    raised3 = False
    try:
        run_headtohead([], bare_model_scorer=bare, pipeline_scorer=pipe, evaluator=judge)
    except ValueError:
        raised3 = True
    assert raised3, "empty items must raise"

    # ── (12) unmeasured path is honest: an arm that never scores → no fabricated lift. ──
    none_scorer = RecordedAnswerScorer("missing_field", name="always-none")   # field absent → None
    out_un = run_headtohead(_FIXTURE, bare_model_scorer=none_scorer, pipeline_scorer=pipe,
                            evaluator=judge)
    assert out_un["lift"] is None and out_un["measurement_kind"] == "unmeasured", \
        "an unscored arm must yield unmeasured + lift=None, never a fabricated number"
    assert out_un["n"] == 0, "no item is paired-scored when an arm always returns None"

    print(
        "PASS — measured_lift_headtohead: "
        f"genuine pipeline lift B-A={out['lift']:+.3f} (bare {out['bare_mean']:.3f} → "
        f"pipeline {out['pipeline_mean']:.3f}, n={out['n']}, judge='{out['evaluator']}'); "
        f"head-to-head B-C={out['head_to_head']['B-C']:+.3f} vs clean-RAG; "
        f"durability={out['durability_class']}; "
        f"identical-to-bare pipeline lift={out_eq['lift']:+.3f} (no fake positive); "
        "self-grading RAISES (separate evaluator enforced); control shows 0 lift; "
        "deterministic re-run identical. "
        "(REAL: protocol + offline stub scores; SEAM: live route + CI + model-level "
        "judge independence + §8 publish gate — un-publishable offline, blockers recorded)"
    )


if __name__ == "__main__":
    _selftest()
