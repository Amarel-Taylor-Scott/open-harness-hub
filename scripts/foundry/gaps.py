#!/usr/bin/env python3
"""Foundry gaps — Stage 0: confirm a capability gap is REAL (measure, don't assert).

A gap is admitted only if (a) the bare model **demonstrably fails** the task family
— from recorded failure samples, or from a live ``Prober`` run + ``Judge`` score —
AND (b) the gap's **model-independent** signal clears a floor (so the model can't
draw its own map: corpus-density gap, query-miss demand, volatility — not the
model's own confidence). This is the screen the rest of the pipeline trusts; weak
or model-flattering gaps are dropped here, before any source/build/measure cost.

Offline default reads recorded ``failure_samples`` + ``model_independent_score`` on
each gap. Production wires a ``Prober`` (bare model) + a ``Judge`` (`measure.Judge`)
to confirm failure live, budget-gated via ``ctx``. Model-independent weighting can
be deepened with `scripts.acquisition.gap_screen` (its weights already favor
model-independent signals).

Input candidates carry a ``gap`` dict; this stage confirms or drops them. Run
``python -m scripts.foundry.gaps`` for the offline self-test.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from scripts.foundry.contracts import BaseStage, Candidate, FoundryContext

DEFAULT_MIN_MODEL_INDEPENDENT = 0.30   # below this ⇒ too model-dependent / weak to build for
DEFAULT_FAIL_THRESHOLD = 0.50          # bare-model mean score below this ⇒ model fails ⇒ gap real


@runtime_checkable
class Prober(Protocol):
    def probe(self, task: dict) -> str:
        """The bare model's attempt at a task (used to confirm failure live)."""
        ...


class GapDiscoveryStage(BaseStage):
    """Confirm gaps; drop unconfirmed/weak ones. Sets the ``areas_probed`` checkpoint."""

    name = "gaps"

    def __init__(
        self,
        *,
        min_model_independent: float = DEFAULT_MIN_MODEL_INDEPENDENT,
        prober: Prober | None = None,
        judge=None,  # measure.Judge — scores the bare answer vs ground truth
        fail_threshold: float = DEFAULT_FAIL_THRESHOLD,
    ) -> None:
        self.min_mi = min_model_independent
        self.prober = prober
        self.judge = judge
        self.fail_threshold = fail_threshold

    def _probe_confirms(self, gap: dict, ctx: FoundryContext) -> bool | None:
        """Live confirmation: returns True if the bare model fails, None if no probe."""
        if not (self.prober and self.judge):
            return None
        scores: list[float] = []
        for task in gap.get("eval_tasks") or []:
            if not ctx.spend_model_call():
                break
            s = self.judge.score(task, self.prober.probe(task))
            if s is not None:
                scores.append(s)
        if not scores:
            return None
        return (sum(scores) / len(scores)) < self.fail_threshold

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        ctx.ledger.checkpoint("areas_probed", len([c for c in batch if c.alive]))
        for c in batch:
            if not c.alive:
                continue
            g = c.gap or {}
            probed = self._probe_confirms(g, ctx)
            confirmed_failure = bool(g.get("failure_samples")) if probed is None else probed
            mi = float(g.get("model_independent_score") or 0.0)
            if not confirmed_failure:
                c.drop(self.name, "unconfirmed: bare-model failure not demonstrated")
            elif mi < self.min_mi:
                c.drop(self.name, f"weak gap: model-independent {mi:.2f} < floor {self.min_mi:.2f}")
            else:
                # record HOW it was confirmed (recorded/human > model-independent > llm_probe,
                # the weakest — "the LLM doesn't know what it doesn't know"). Drives human-approval.
                g["confirmation_source"] = ("recorded" if g.get("failure_samples")
                                            else "llm_probe" if probed else "model_independent")
                c.mark(self.name, "confirmed", g.get("id", ""))
        return batch


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    strong = Candidate(gap={"id": "g1", "model_independent_score": 0.8,
                            "failure_samples": [{"task": "x", "correct": False}]})
    weak = Candidate(gap={"id": "g2", "model_independent_score": 0.1,
                          "failure_samples": [{"task": "x", "correct": False}]})
    no_evidence = Candidate(gap={"id": "g3", "model_independent_score": 0.9})
    ctx = FoundryContext()
    GapDiscoveryStage().run([strong, weak, no_evidence], ctx)
    check("strong gap confirmed", strong.alive)
    check("recorded-evidence gap ⇒ confirmation_source=recorded", strong.gap.get("confirmation_source") == "recorded")
    check("weak (model-dependent) gap dropped", not weak.alive and "weak gap" in weak.reasons[-1])
    check("no failure evidence dropped", not no_evidence.alive and "unconfirmed" in no_evidence.reasons[-1])
    check("areas_probed checkpoint set", ctx.ledger.checkpoints.get("areas_probed") == 3)

    # live probe confirmation: bare model fails ⇒ confirmed even without recorded samples
    class FailingProber:
        def probe(self, task):
            return "wrong"

    from scripts.foundry.measure import DeterministicChecker
    live = Candidate(gap={"id": "g4", "model_independent_score": 0.6,
                          "eval_tasks": [{"prompt": "q", "correct_answer": "the right answer"}]})
    lctx = FoundryContext()
    GapDiscoveryStage(prober=FailingProber(), judge=DeterministicChecker()).run([live], lctx)
    check("live probe: bare fails ⇒ gap confirmed", live.alive, str(live.reasons))
    check("probe spent model budget", lctx.model_calls >= 1)
    check("probe-confirmed gap ⇒ confirmation_source=llm_probe (weakest)",
          live.gap.get("confirmation_source") == "llm_probe", str(live.gap))

    # live probe: bare model SUCCEEDS ⇒ no gap (dropped)
    class PassingProber:
        def probe(self, task):
            return task["correct_answer"]

    solved = Candidate(gap={"id": "g5", "model_independent_score": 0.6,
                            "eval_tasks": [{"prompt": "q", "correct_answer": "the right answer"}]})
    GapDiscoveryStage(prober=PassingProber(), judge=DeterministicChecker()).run([solved], FoundryContext())
    check("live probe: bare succeeds ⇒ no gap (dropped)", not solved.alive)

    print(f"\n{'all gaps self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
