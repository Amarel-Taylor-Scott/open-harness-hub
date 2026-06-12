#!/usr/bin/env python3
"""scripts.foundry.eval_scorers — Judge implementations for the foundry `measure` stage.

`measure.py` measures lift by scoring a bare-model answer vs a pipeline answer with a
`Judge` (`score(task, answer) -> float | None`). Its default `DeterministicChecker` is
token-F1 against `task['correct_answer']` — and returns `None` (honest "unmeasured")
whenever there is no gold answer. That is the offline cap.

This module lifts the cap with a ladder of scorers, deterministic-first (the repo's law:
prefer a deterministic gate; an LLM judge is a candidate signal, never the gate):

  Deterministic (no model, no gold needed for the faithfulness/precision proxies):
    ExactMatchJudge            — normalized exact match vs gold.
    TokenF1Judge               — token-F1 vs gold (the existing default, re-exposed).
    FaithfulnessProxyJudge     — REFERENCE-FREE: decompose the answer into claims and
                                 score the fraction grounded in task evidence. The
                                 deterministic shadow of Ragas Faithfulness — gives a
                                 lift signal with NO gold answer, the key offline-cap fix.
    ContextPrecisionProxyJudge — REFERENCE-FREE: fraction of retrieved context that is
                                 relevant (Average-Precision@k, the Ragas shape).

  Model-backed seams (candidate signals only — wrapped so they can NEVER game the gate):
    NJudgeMajority             — calls an INJECTED llm_judge N times; returns the median
                                 only if the judges agree within a variance floor,
                                 otherwise `None` (honest "unmeasured"). No injected
                                 judge → raises (a score is never fabricated).
    RagasJudge / DeepEvalJudge — honest seams: raise NotImplementedError when the
                                 (candidate, never auto-installed) package is absent,
                                 documenting how to wire them behind the model route.

Design: each Judge is a `measure.Judge` (a `.name` + `.score`); deterministic ones are
pure stdlib and self-tested offline; model-backed ones honor the no-fabrication law.

CLI / self-test:
    python3 scripts/foundry/eval_scorers.py
    python3 -m scripts.foundry.eval_scorers --self-test
"""
from __future__ import annotations

import argparse
import math
import re
import statistics
import sys
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.measure import token_f1

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: A claim is "supported" by an evidence item when they share at least this many
#: salient (non-stopword) terms — the deterministic faithfulness threshold.
FAITHFULNESS_SUPPORT_OVERLAP = 2

#: A retrieved-context item counts as relevant to the query/gold at this overlap.
CONTEXT_RELEVANCE_OVERLAP = 2

#: NJudgeMajority: if the judges' sample stdev exceeds this, they disagree too much
#: to trust — return None (unmeasured) rather than a fabricated median.
DEFAULT_JUDGE_VARIANCE_FLOOR = 0.2

STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what",
    "when", "where", "which", "who", "why", "will", "with", "must", "shall",
})
_TOKEN_RE = re.compile(r"[a-z0-9%$.]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|;\s+")
SCORE_DECIMALS = 6


def _salient(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(str(text).lower()) if t not in STOPWORDS}


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split())


def _evidence_items(task: dict) -> list[str]:
    """The grounding the answer must be faithful to: task['evidence'] or
    ['context'] or ['retrieved_context'] — whichever the eval task carries."""
    for key in ("evidence", "context", "retrieved_context"):
        v = task.get(key)
        if isinstance(v, list) and v:
            return [str(x) for x in v]
        if isinstance(v, str) and v.strip():
            return [v]
    return []


class ExactMatchJudge:
    """Deterministic: 1.0 iff the normalized answer equals the gold, else 0.0."""

    name = "deterministic-exact-match"

    def score(self, task: dict, answer: str | None) -> float | None:
        gold = task.get("correct_answer")
        if gold is None or answer is None:
            return None
        return 1.0 if _norm(answer) == _norm(gold) else 0.0


class TokenF1Judge:
    """Deterministic: token-F1 vs gold (the existing default, named for the ladder)."""

    name = "deterministic-token-f1"

    def score(self, task: dict, answer: str | None) -> float | None:
        gold = task.get("correct_answer")
        if gold is None or answer is None:
            return None
        return token_f1(str(answer), str(gold))


class FaithfulnessProxyJudge:
    """REFERENCE-FREE deterministic faithfulness: fraction of the answer's claims that
    are grounded in the task evidence. The offline-cap fix — a lift signal with no gold.

    Decompose the answer into claim sentences; a claim is supported when it shares
    >= FAITHFULNESS_SUPPORT_OVERLAP salient terms with ANY evidence item. Score =
    supported / total. None when there are no claims or no evidence (honest unmeasured).
    """

    name = "deterministic-faithfulness-proxy"

    def score(self, task: dict, answer: str | None) -> float | None:
        if answer is None:
            return None
        evidence = _evidence_items(task)
        if not evidence:
            return None
        ev_sets = [_salient(e) for e in evidence]
        claims = [c.strip() for c in _SENTENCE_SPLIT_RE.split(str(answer)) if c.strip()]
        claims = [c for c in claims if _salient(c)]
        if not claims:
            return None
        supported = sum(
            1 for c in claims
            if any(len(_salient(c) & ev) >= FAITHFULNESS_SUPPORT_OVERLAP for ev in ev_sets))
        return round(supported / len(claims), SCORE_DECIMALS)


class ContextPrecisionProxyJudge:
    """REFERENCE-FREE deterministic context precision (Average-Precision@k, the Ragas
    shape): of the retrieved context, how much near the top is relevant to the query.

    A context item is relevant when it shares >= CONTEXT_RELEVANCE_OVERLAP salient terms
    with the query (or gold). AP@k = Σ(Precision@k · rel_k) / total_relevant.
    """

    name = "deterministic-context-precision-proxy"

    def score(self, task: dict, answer: str | None) -> float | None:
        ctx = task.get("retrieved_context")
        ref = task.get("correct_answer") or task.get("query") or task.get("question")
        if not isinstance(ctx, list) or not ctx or ref is None:
            return None
        ref_terms = _salient(ref)
        rels = [1 if len(_salient(c) & ref_terms) >= CONTEXT_RELEVANCE_OVERLAP else 0 for c in ctx]
        total_rel = sum(rels)
        if total_rel == 0:
            return 0.0
        running, ap = 0, 0.0
        for k, rel in enumerate(rels, start=1):
            if rel:
                running += 1
                ap += running / k
        return round(ap / total_rel, SCORE_DECIMALS)


class NJudgeMajority:
    """Model-backed Judge wrapped so it can never game the gate: call an INJECTED
    ``llm_judge(task, answer, seed) -> float`` ``n`` times; return the median ONLY if
    the judges agree within ``variance_floor`` (sample stdev), else None (unmeasured).
    Without an injected judge it RAISES — a score is never fabricated.
    """

    name = "llm-njudge-majority"

    def __init__(self, llm_judge: Callable[[dict, str | None, int], float] | None = None,
                 *, n: int = 3, variance_floor: float = DEFAULT_JUDGE_VARIANCE_FLOOR) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        self.llm_judge = llm_judge
        self.n = n
        self.variance_floor = variance_floor

    def score(self, task: dict, answer: str | None) -> float | None:
        if answer is None:
            return None
        if self.llm_judge is None:
            raise RuntimeError(
                "NJudgeMajority needs an injected llm_judge(task, answer, seed) -> float "
                "(wire it to scripts.foundry.model_route behind src/teleon/inference); "
                "an LLM score is never fabricated offline")
        scores = [max(0.0, min(1.0, float(self.llm_judge(task, answer, seed))))
                  for seed in range(self.n)]
        if self.n >= 2 and statistics.pstdev(scores) > self.variance_floor:
            return None  # judges disagree too much → honest unmeasured, not a guess
        return round(statistics.median(scores), SCORE_DECIMALS)


def _raise_seam(pkg: str, klass: str) -> None:
    raise NotImplementedError(
        f"{klass} needs the '{pkg}' package (a CANDIDATE — never auto-installed). "
        f"Install it in a dependency-permitted environment, then back the LLM-judge "
        f"calls with scripts.foundry.model_route via src/teleon/inference so model "
        f"selection, cost caps, and receipts stay governed. The metric is a candidate "
        f"SCORER behind a deterministic gate, never a second source of truth.")


class RagasJudge:
    """Honest seam for Ragas metrics (Faithfulness / Context-Precision-WithoutReference).
    Raises until the package is present and the model route is wired."""

    name = "ragas-scorer"

    def __init__(self, metric: str = "faithfulness") -> None:
        self.metric = metric

    def score(self, task: dict, answer: str | None) -> float | None:
        try:
            import ragas  # noqa: F401
        except Exception:  # noqa: BLE001
            _raise_seam("ragas", "RagasJudge")
        # pragma: no cover — only reachable in a deps-permitted env
        raise NotImplementedError("wire RagasJudge to ragas.metrics behind the model route")


class DeepEvalJudge:
    """Honest seam for DeepEval metrics (G-Eval / Answer-Relevancy). Raises until wired."""

    name = "deepeval-scorer"

    def __init__(self, metric: str = "answer_relevancy") -> None:
        self.metric = metric

    def score(self, task: dict, answer: str | None) -> float | None:
        try:
            import deepeval  # noqa: F401
        except Exception:  # noqa: BLE001
            _raise_seam("deepeval", "DeepEvalJudge")
        raise NotImplementedError("wire DeepEvalJudge to deepeval.metrics behind the model route")


#: The deterministic ladder, best-effort first — a caller can try each and take the
#: first non-None score (gold-based when gold exists, else reference-free proxies).
DETERMINISTIC_JUDGES: tuple[type, ...] = (
    ExactMatchJudge, TokenF1Judge, FaithfulnessProxyJudge, ContextPrecisionProxyJudge)


class LadderJudge:
    """Drop-in `measure.Judge` that tries judges in order and returns the FIRST non-None
    score — so a task with a gold answer is scored against it (token-F1), and a task with
    only evidence still gets a reference-free faithfulness signal instead of `None`. This
    is the offline-cap fix as one object: `MeasurementStage(judge=LadderJudge())`.

    The default ladder is deterministic-only (no model). Pass `tail=[NJudgeMajority(...)]`
    to append a model-backed judge as the last resort — still bounded by its own
    no-fabrication rules.
    """

    name = "deterministic-ladder"

    def __init__(self, judges: list[Any] | None = None, *, tail: list[Any] | None = None) -> None:
        base = judges if judges is not None else [J() for J in DETERMINISTIC_JUDGES]
        self.judges = list(base) + list(tail or [])

    def score(self, task: dict, answer: str | None) -> float | None:
        for judge in self.judges:
            s = judge.score(task, answer)
            if s is not None:
                return s
        return None  # nothing could score it — honest unmeasured


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ExactMatch + TokenF1 vs gold.
    em = ExactMatchJudge()
    check("exact-match hit", em.score({"correct_answer": "10 business days"}, "10 Business Days") == 1.0)
    check("exact-match miss", em.score({"correct_answer": "10 business days"}, "30 days") == 0.0)
    check("exact-match no gold -> None", em.score({}, "x") is None)
    f1 = TokenF1Judge()
    check("token-f1 partial in (0,1)", 0.0 < f1.score({"correct_answer": "a b c d"}, "a b c") < 1.0)

    # FaithfulnessProxy — the offline-cap fix: a grounded answer scores high WITHOUT gold.
    fp = FaithfulnessProxyJudge()
    grounded = {"evidence": ["Regulation E requires provisional credit within ten business days."]}
    s_good = fp.score(grounded, "Provisional credit is required within ten business days.")
    s_bad = fp.score(grounded, "The cap is thirty days for credit cards in California.")
    check("faithfulness grounded answer high", s_good == 1.0, str(s_good))
    check("faithfulness ungrounded answer low", s_bad == 0.0, str(s_bad))
    check("faithfulness mixed in (0,1)",
          0.0 < fp.score(grounded,
                         "Provisional credit within ten business days. Also unicorns exist nearby.") < 1.0)
    check("faithfulness no evidence -> None", fp.score({}, "anything") is None)
    # It gives a lift SIGNAL where the gold-based judge returns None.
    check("faithfulness fills the offline cap", f1.score(grounded, "x") is None and s_good is not None)

    # ContextPrecision — relevant context near the top scores higher (AP@k).
    cp = ContextPrecisionProxyJudge()
    top = {"correct_answer": "provisional credit ten business days",
           "retrieved_context": ["provisional credit ten business days rule",
                                  "unrelated gardening note", "another unrelated note"]}
    bot = {"correct_answer": "provisional credit ten business days",
           "retrieved_context": ["unrelated gardening note", "another unrelated note",
                                  "provisional credit ten business days rule"]}
    check("context-precision rewards top placement", cp.score(top, None) > cp.score(bot, None),
          f"{cp.score(top, None)} vs {cp.score(bot, None)}")
    check("context-precision no relevant -> 0.0",
          cp.score({"correct_answer": "zzz qqq", "retrieved_context": ["abc", "def"]}, None) == 0.0)

    # NJudgeMajority — agreement returns median, disagreement returns None, no judge raises.
    agree = NJudgeMajority(lambda t, a, s: 0.8, n=3)
    check("njudge agreement -> median", agree.score({}, "x") == 0.8)
    disagree = NJudgeMajority(lambda t, a, s: [0.1, 0.9, 0.5][s], n=3, variance_floor=0.1)
    check("njudge disagreement -> None (unmeasured)", disagree.score({}, "x") is None)
    raised = False
    try:
        NJudgeMajority(None).score({}, "x")
    except RuntimeError:
        raised = True
    check("njudge no model -> raises (never fabricated)", raised)

    # The package seams raise honestly (packages absent in this env).
    for J in (RagasJudge, DeepEvalJudge):
        raised = False
        try:
            J().score({"evidence": ["x"]}, "y")
        except NotImplementedError:
            raised = True
        check(f"{J.__name__} honest seam raises", raised)

    # Every deterministic judge satisfies the measure.Judge shape (name + score).
    check("ladder judges have name+score",
          all(hasattr(J(), "name") and callable(getattr(J(), "score")) for J in DETERMINISTIC_JUDGES))

    # LadderJudge: gold present -> token-F1; only evidence -> faithfulness proxy; the
    # drop-in offline-cap fix. And it plugs into the real MeasurementStage.
    ladder = LadderJudge()
    check("ladder uses gold when present",
          ladder.score({"correct_answer": "ten business days"}, "ten business days") == 1.0)
    check("ladder falls back to faithfulness without gold",
          ladder.score({"evidence": ["credit within ten business days"]},
                       "credit within ten business days") == 1.0)
    check("ladder honest None when nothing scores", ladder.score({}, "x") is None)
    from scripts.foundry.measure import MeasurementStage
    stage = MeasurementStage(judge=ladder)
    check("LadderJudge drops into MeasurementStage", stage.judge.name == "deterministic-ladder")

    ok = not fails
    print("\n" + ("PASS — eval_scorers: deterministic ladder (exact/f1/faithfulness-proxy/"
                  "context-precision) scores offline incl. REFERENCE-FREE faithfulness that "
                  "fills the gold-less cap; LLM N-judge returns None on disagreement and raises "
                  "without a model; Ragas/DeepEval honest seams."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Foundry measure-stage Judge scorers.")
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
