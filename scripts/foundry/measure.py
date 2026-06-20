#!/usr/bin/env python3
"""Foundry measure — Stage 5: the lift measurement engine (the linchpin).

The admission bar is a **measured** ``pipeline_score - bare_model_score`` on
held-out task instances — the one piece the codebase never had (lift was only
ever *asserted* by heuristics). This stage computes it for real and attaches it to
each candidate's ``lift`` so the gate (Stage 6) can decide on evidence.

**Honesty first — no fabricated deltas.** Offline (the default), it scores the
*recorded* bare/pipeline answers carried on a gap's ``eval_tasks`` — measuring real
outputs, not inventing them. If no answers are available and no live model is
wired, it leaves ``lift`` unmeasured (``None``) and the gate routes the candidate
to **review** — it never makes up a number.

**Production seam.** Wire a ``BareModel`` and a ``PipelineRunner`` (e.g. Claude
sub-agents / a model route) and the stage will *generate* the bare and pipeline
answers, spending the model-call budget on ``ctx``. A ``Judge`` scores answers; the
default is a deterministic token-F1 checker against a known ``correct_answer`` (use
an LLM-judge where there is no deterministic ground truth).

**Amortized per family.** Measurement runs once per gap (task family) and the delta
is shared by every candidate serving that gap — this is what makes 10k/day
affordable (model calls per *family*, not per *row*).

Run ``python -m scripts.foundry.measure`` for the offline self-test.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Protocol, runtime_checkable

from scripts.eval.reason_codes import durability_class
from scripts.foundry.benchmark_synth import Synthesizer
from scripts.foundry.contracts import BaseStage, Candidate, FoundryContext

_WORD = re.compile(r"[a-z0-9]+")


# --------------------------------------------------------------------------- #
# scoring helpers (deterministic, stdlib)
# --------------------------------------------------------------------------- #
def _norm_tokens(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def token_f1(pred: str, gold: str) -> float:
    """Token-overlap F1 in [0,1] — partial credit for partially-correct answers."""
    p, g = _norm_tokens(pred), _norm_tokens(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    pc, gc = defaultdict(int), defaultdict(int)
    for t in p:
        pc[t] += 1
    for t in g:
        gc[t] += 1
    overlap = sum(min(pc[t], gc[t]) for t in pc.keys() & gc.keys())
    if overlap == 0:
        return 0.0
    precision = overlap / len(p)
    recall = overlap / len(g)
    return round(2 * precision * recall / (precision + recall), 4)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# --------------------------------------------------------------------------- #
# pluggable protocols (offline defaults below; wire model-backed in production)
# --------------------------------------------------------------------------- #
@runtime_checkable
class Judge(Protocol):
    name: str

    def score(self, task: dict, answer: str | None) -> float | None:
        """Return a quality score in [0,1], or None if unscoreable."""
        ...


@runtime_checkable
class BareModel(Protocol):
    def answer(self, task: dict) -> str:
        """The bare LLM's attempt at the task (no pipeline)."""
        ...


@runtime_checkable
class PipelineRunner(Protocol):
    def run(self, task: dict, candidate: Candidate) -> str:
        """Run the pipeline that uses this candidate on the task."""
        ...


class DeterministicChecker:
    """Default Judge: token-F1 against ``task['correct_answer']``.

    Returns None when there is no ground truth to score against (then the family is
    only measurable via a model-backed Judge — never fabricated)."""

    name = "deterministic-f1"

    def score(self, task: dict, answer: str | None) -> float | None:
        gold = task.get("correct_answer")
        if gold is None or answer is None:
            return None
        return token_f1(str(answer), str(gold))


# --------------------------------------------------------------------------- #
# the stage
# --------------------------------------------------------------------------- #
class MeasurementStage(BaseStage):
    """Measure lift per family and attach it to every candidate in that family."""

    name = "measure"

    def __init__(
        self,
        *,
        judge: Judge | None = None,
        bare_model: BareModel | None = None,
        pipeline_runner: PipelineRunner | None = None,
        synthesizer: Synthesizer | None = None,
    ) -> None:
        # Default to the LadderJudge: graded token-F1 against a gold answer when one exists,
        # else the REFERENCE-FREE faithfulness proxy (scores lift from evidence with no gold —
        # closing the offline cap). Lazy import avoids the eval_scorers↔measure cycle. A
        # builtins-only fallback (DeterministicChecker) keeps measure importable in isolation.
        if judge is not None:
            self.judge = judge
        else:
            try:
                from scripts.foundry.eval_scorers import LadderJudge
                self.judge = LadderJudge()
            except Exception:  # noqa: BLE001
                self.judge = DeterministicChecker()
        self.bare_model = bare_model
        self.pipeline_runner = pipeline_runner
        self.synthesizer = synthesizer   # generates held-out eval tasks when a gap has none

    @property
    def offline(self) -> bool:
        return self.bare_model is None and self.pipeline_runner is None

    @staticmethod
    def _family_tasks(members: list[Candidate]) -> list[dict]:
        """Held-out tasks for the family (shared via the gap)."""
        gap = members[0].gap or {}
        tasks = gap.get("eval_tasks") or []
        if tasks:
            return list(tasks)
        # fall back to failure_samples that already carry a correct_answer
        return [s for s in (gap.get("failure_samples") or []) if isinstance(s, dict) and s.get("correct_answer")]

    def _answers(self, task: dict, member: Candidate, ctx: FoundryContext) -> tuple[str | None, str | None]:
        """Recorded answers first; else generate via wired models (budget-gated)."""
        bare = task.get("bare_answer")
        if bare is None and self.bare_model is not None and ctx.spend_model_call():
            bare = self.bare_model.answer(task)
        pipe = task.get("pipeline_answer")
        if pipe is None and self.pipeline_runner is not None and ctx.spend_model_call():
            pipe = self.pipeline_runner.run(task, member)
        return bare, pipe

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        families: dict[str, list[Candidate]] = defaultdict(list)
        for c in batch:
            if c.alive:
                families[(c.gap or {}).get("id", "")].append(c)

        for gap_id, members in families.items():
            tasks = self._family_tasks(members)
            # benchmark-synthesis: if the gap has no held-out tasks, generate them from the
            # component's own SOURCE content (ground truth from the source, not the model).
            if not tasks and self.synthesizer is not None:
                tasks = self.synthesizer.synthesize(members[0])
                for c in members:
                    if tasks:
                        c.gap.setdefault("eval_tasks", tasks)
            if not tasks:
                for c in members:
                    c.mark(self.name, "unmeasured", "no held-out eval tasks for family (and no synthesizer)")
                continue

            bare_scores: list[float] = []
            pipe_scores: list[float] = []
            rep = members[0]   # representative; the component is interchangeable within a family
            for task in tasks:
                bare_ans, pipe_ans = self._answers(task, rep, ctx)
                bs = self.judge.score(task, bare_ans)
                ps = self.judge.score(task, pipe_ans)
                if bs is not None:
                    bare_scores.append(bs)
                if ps is not None:
                    pipe_scores.append(ps)

            if not bare_scores or not pipe_scores:
                for c in members:
                    c.mark(self.name, "unmeasured",
                           "answers unavailable (offline + no recorded bare/pipeline answers)")
                continue

            bare = _mean(bare_scores)
            pipe = _mean(pipe_scores)
            delta = pipe - bare
            for c in members:
                c.lift = {
                    "bare_score": round(bare, 4),
                    "pipeline_score": round(pipe, 4),
                    "delta": round(delta, 4),
                    "n": len(tasks),
                    "judge": self.judge.name,
                    "durability_class": durability_class((c.gap or {}).get("lift_reason")),
                    "measured_offline": self.offline,
                }
                c.mark(self.name, "measured", f"delta {delta:+.3f} (bare {bare:.2f} → pipe {pipe:.2f}, n={len(tasks)})")
        return batch


# --------------------------------------------------------------------------- #
# self-test (offline; no model, no network)
# --------------------------------------------------------------------------- #
def _cand(gap_id: str, eval_tasks: list[dict], *, lift_reason: str = "esoteric_rule") -> Candidate:
    return Candidate(
        target_type="knowledge-pack",
        component_id=f"knowledge-pack/{gap_id}",
        body={"id": f"knowledge-pack/{gap_id}", "type": "knowledge-pack", "name": gap_id},
        gap={"id": gap_id, "lift_reason": lift_reason, "eval_tasks": eval_tasks},
        source={"source_url": "https://x/y", "author": "a", "license": "MIT"},
    )


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # token-F1 sanity
    check("f1 exact match = 1.0", token_f1("article 8 csddd", "article 8 csddd") == 1.0)
    check("f1 disjoint = 0.0", token_f1("apple", "orange") == 0.0)
    check("f1 partial in (0,1)", 0.0 < token_f1("article 8 csddd", "article 8") < 1.0)

    # POSITIVE measured lift: bare answers wrong, pipeline answers correct (recorded)
    tasks_good = [
        {"prompt": "cite the CSDDD due-diligence article",
         "correct_answer": "Article 8 CSDDD", "bare_answer": "Article 12 (wrong)", "pipeline_answer": "Article 8 CSDDD"},
        {"prompt": "cite the civil-liability article",
         "correct_answer": "Article 29 CSDDD", "bare_answer": "Article 5 (wrong)", "pipeline_answer": "Article 29 CSDDD"},
    ]
    a = _cand("gap-csddd", tasks_good)
    b = _cand("gap-csddd", tasks_good)   # SAME family — measured once, shared
    b.component_id = "knowledge-pack/gap-csddd-2"
    ctx = FoundryContext()
    MeasurementStage().run([a, b], ctx)
    check("positive delta measured", a.lift and a.lift["delta"] > 0.5, str(a.lift))
    check("bare < pipeline", a.lift["bare_score"] < a.lift["pipeline_score"])
    check("amortized: both family members share the delta", a.lift["delta"] == b.lift["delta"])
    check("n reflects task count", a.lift["n"] == 2)
    check("durability class carried", a.lift["durability_class"] == "transient")
    check("flagged measured_offline", a.lift["measured_offline"] is True)

    # NO lift: pipeline no better than bare (both wrong) → delta ~0 → gate will cull
    tasks_flat = [{"prompt": "q", "correct_answer": "right", "bare_answer": "wrong", "pipeline_answer": "wrong"}]
    flat = _cand("gap-flat", tasks_flat)
    MeasurementStage().run([flat], FoundryContext())
    check("no-improvement family ⇒ delta ~0", abs(flat.lift["delta"]) < 1e-9, str(flat.lift))

    # UNMEASURABLE offline (no recorded answers, no model) ⇒ lift stays None (honest)
    tasks_norec = [{"prompt": "q", "correct_answer": "right"}]   # no bare/pipeline answers
    norec = _cand("gap-norec", tasks_norec)
    MeasurementStage().run([norec], FoundryContext())
    check("no recorded answers + offline ⇒ lift unmeasured (None)", norec.lift is None)
    check("unmeasured recorded in log", any(s["status"] == "unmeasured" for s in norec.stage_log))

    # no eval tasks at all ⇒ unmeasured
    empty = _cand("gap-empty", [])
    MeasurementStage().run([empty], FoundryContext())
    check("no eval tasks ⇒ unmeasured", empty.lift is None)

    # PRODUCTION SEAM: wired models generate answers when none are recorded; budget spent
    class ScriptedBare:
        def answer(self, task):
            return "totally wrong"

    class ScriptedPipeline:
        def run(self, task, candidate):
            return task["correct_answer"]   # the pipeline grounds it

    tasks_live = [{"prompt": "q1", "correct_answer": "the grounded answer one"},
                  {"prompt": "q2", "correct_answer": "the grounded answer two"}]
    live = _cand("gap-live", tasks_live)
    lctx = FoundryContext()
    MeasurementStage(bare_model=ScriptedBare(), pipeline_runner=ScriptedPipeline()).run([live], lctx)
    check("model-backed measurement yields positive delta", live.lift and live.lift["delta"] > 0.9, str(live.lift))
    check("model calls counted against budget", lctx.model_calls == 4, f"calls={lctx.model_calls}")
    check("not flagged offline when models wired", live.lift["measured_offline"] is False)

    # budget cap: zero budget blocks generation ⇒ unmeasured (no fabrication)
    capped = _cand("gap-capped", [{"prompt": "q", "correct_answer": "x"}])
    cctx = FoundryContext()
    cctx.config.model_call_budget = 0
    MeasurementStage(bare_model=ScriptedBare(), pipeline_runner=ScriptedPipeline()).run([capped], cctx)
    check("budget=0 ⇒ unmeasured (no fabricated delta)", capped.lift is None)

    # benchmark-synthesis: a gap with NO eval_tasks but a component WITH source content
    from scripts.foundry.benchmark_synth import DeterministicSynth
    synth_c = Candidate(target_type="knowledge-pack", component_id="knowledge-pack/synth",
                        body={"name": "X corpus", "_entries": [{"anchor": "A1", "text": "the grounded answer one"},
                                                               {"anchor": "A2", "text": "the grounded answer two"}]},
                        gap={"id": "gap/synth", "lift_reason": "esoteric_rule"},
                        source={"source_url": "u", "author": "a", "license": "MIT"})
    MeasurementStage(synthesizer=DeterministicSynth(), bare_model=ScriptedBare(),
                     pipeline_runner=ScriptedPipeline()).run([synth_c], FoundryContext())
    check("synthesized benchmark ⇒ measurable lift", bool(synth_c.lift) and synth_c.lift["delta"] > 0.5, str(synth_c.lift))
    check("synth attached eval_tasks to the gap", bool(synth_c.gap.get("eval_tasks")))

    print(f"\n{'all measure self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
