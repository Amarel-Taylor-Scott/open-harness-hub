#!/usr/bin/env python3
"""Foundry benchmark_synth — Stage 5's missing input: held-out eval tasks per gap.

Measurement needs a benchmark: `(prompt, correct_answer)` pairs whose ground truth
lives in the **source**, so we can test whether grounding (the component) lifts the
bare model. Real research-queue gaps carry *signals*, not tasks — so this synthesizes
the tasks from the constructed component's own content.

**Honesty:** ground truth comes from the SOURCE content the component carries
(`_entries` / `rules`), never the model's parametric knowledge. The synthesizer only
turns source facts into questions; whether the component actually *lifts* is then
decided by measurement (a fact the model already knows → delta ≈ 0 → not promoted; a
fresh/esoteric fact → delta > 0 → promoted). The synth doesn't bias the verdict.

  - ``DeterministicSynth`` — offline, templated Q&A from the entries/rules (no model).
  - ``RouteSynth`` — uses a model route to write more natural held-out questions whose
    answers must come from the provided facts (falls back to deterministic on any
    parse failure).

stdlib-only; the route is duck-typed (anything with ``.complete``), so no import of
`model_route` (no cycle). Run ``python -m scripts.foundry.benchmark_synth`` for the test.
"""
from __future__ import annotations

import json
import re
from typing import Any, Protocol, runtime_checkable

from scripts.foundry.contracts import Candidate

_DEFAULT_MAX_TASKS = 6


@runtime_checkable
class Synthesizer(Protocol):
    def synthesize(self, candidate: Candidate, *, max_tasks: int = _DEFAULT_MAX_TASKS) -> list[dict]:
        ...


def _source_facts(candidate: Candidate) -> list[Any]:
    body = candidate.body or {}
    return list(body.get("_entries") or []) + list(body.get("rules") or [])


def _entry_qa(name: str, entry: Any) -> dict | None:
    """One (prompt, correct_answer) from a source entry/rule; answer comes from the source."""
    if not isinstance(entry, dict):
        text = str(entry).strip()
        return {"prompt": f"According to {name}, state this fact.", "correct_answer": text} if text else None
    anchor = entry.get("anchor") or entry.get("code") or entry.get("id") or entry.get("term") or entry.get("condition")
    answer = (entry.get("text") or entry.get("fact") or entry.get("definition") or entry.get("value")
              or entry.get("rule") or entry.get("action"))
    if anchor and answer:
        return {"prompt": f"In {name}, what does '{anchor}' specify?", "correct_answer": str(answer)}
    if answer:
        return {"prompt": f"According to {name}, state the relevant rule or fact.", "correct_answer": str(answer)}
    return None


class DeterministicSynth:
    """Offline: templated Q&A straight from the source content. No model."""

    name = "deterministic-synth"

    def synthesize(self, candidate: Candidate, *, max_tasks: int = _DEFAULT_MAX_TASKS) -> list[dict]:
        name = (candidate.body or {}).get("name") or "the source"
        tasks: list[dict] = []
        for entry in _source_facts(candidate):
            qa = _entry_qa(name, entry)
            if qa:
                tasks.append(qa)
            if len(tasks) >= max_tasks:
                break
        return tasks


class RouteSynth:
    """Model-backed: write held-out questions whose answers must come from the facts.

    Ground truth is still the source; the model only reformats facts into Q&A. Falls
    back to ``DeterministicSynth`` if the model returns unparseable output."""

    name = "route-synth"

    def __init__(self, route: Any) -> None:
        self.route = route
        self._fallback = DeterministicSynth()

    def synthesize(self, candidate: Candidate, *, max_tasks: int = _DEFAULT_MAX_TASKS) -> list[dict]:
        facts = _source_facts(candidate)
        if not facts:
            return []
        name = (candidate.body or {}).get("name") or "the source"
        facts_text = "\n".join(json.dumps(f, ensure_ascii=False) if isinstance(f, dict) else str(f)
                               for f in facts[: max_tasks * 2])
        system = ("You write held-out test questions. The answer to each question MUST be contained in "
                  "the provided facts — never use outside knowledge. Reply with ONLY a JSON array of "
                  '{"prompt": "...", "correct_answer": "..."} objects.')
        prompt = f"SOURCE: {name}\nFACTS:\n{facts_text}\n\nWrite up to {max_tasks} questions as JSON."
        try:
            out = self.route.complete(prompt, system)
            arr = out[out.index("["): out.rindex("]") + 1]
            data = json.loads(arr)
            tasks = [{"prompt": str(d["prompt"]), "correct_answer": str(d["correct_answer"])}
                     for d in data if isinstance(d, dict) and d.get("prompt") and d.get("correct_answer")]
            return tasks[:max_tasks] or self._fallback.synthesize(candidate, max_tasks=max_tasks)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return self._fallback.synthesize(candidate, max_tasks=max_tasks)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    c = Candidate(target_type="knowledge-pack",
                  body={"name": "CSDDD article corpus",
                        "_entries": [{"anchor": "Article 8", "text": "the due-diligence obligation"},
                                     {"anchor": "Article 29", "text": "civil liability"}],
                        "rules": [{"condition": "supplier lacks a due-diligence statement", "action": "cite Article 8"}]})

    # deterministic synth: ground truth comes from the source content
    tasks = DeterministicSynth().synthesize(c)
    check("synthesizes tasks from entries + rules", len(tasks) == 3, str(len(tasks)))
    check("each task has prompt + correct_answer", all(t.get("prompt") and t.get("correct_answer") for t in tasks))
    check("answer is the source's text (not invented)",
          any(t["correct_answer"] == "the due-diligence obligation" for t in tasks), str(tasks))
    check("respects max_tasks", len(DeterministicSynth().synthesize(c, max_tasks=1)) == 1)
    check("no facts ⇒ no tasks", DeterministicSynth().synthesize(Candidate(target_type="tool", body={})) == [])

    # route synth: parses a model's JSON; falls back on garbage
    class GoodRoute:
        def complete(self, prompt, system=None):
            return 'Sure: [{"prompt":"Q1?","correct_answer":"A1"},{"prompt":"Q2?","correct_answer":"A2"}]'

    class BadRoute:
        def complete(self, prompt, system=None):
            return "I cannot comply."

    rs = RouteSynth(GoodRoute()).synthesize(c)
    check("route synth parses model JSON", len(rs) == 2 and rs[0]["prompt"] == "Q1?", str(rs))
    fb = RouteSynth(BadRoute()).synthesize(c)
    check("route synth falls back on unparseable output", len(fb) == 3, str(len(fb)))

    print(f"\n{'all benchmark_synth self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
