#!/usr/bin/env python3
"""Backs `processor/clinical-abstention-gate` (process_kind ``gate.evidence_sufficiency``).

The cite-or-abstain contract for clinical answers: BLOCK an answer when the
documented/retrieved evidence is insufficient to support it, routing to
"insufficient evidence — clinician review" instead of guessing. Deterministic
sufficiency rules over the answer's claims vs the evidence items: every
claim must be covered by at least one evidence item (salient-term support),
every cited evidence id must exist, and opinion-grade evidence alone never
suffices.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs answer, evidence → outputs sufficient, reason.

CLI / self-test: python3 scripts/processors/clinical/clinical_abstention_gate.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: A claim needs at least this many salient terms shared with one evidence
#: item to count as supported (2 = topical contact + a content word, not a
#: single stray token).
CLAIM_SUPPORT_OVERLAP = 2

#: Evidence kinds that can support a clinical claim on their own. Opinion and
#: model interpretation alone never suffice (LLM output is never truth).
SUFFICIENT_KINDS = frozenset({"documented_finding", "lab_result", "governed_corpus", "source_of_law"})
SOFT_KINDS = frozenset({"opinion", "model_interpretation"})

#: The abstention routing string (single definition; the UI reads it).
ABSTAIN_ROUTE = "insufficient evidence — clinician review"

STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
                       "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
                       "with", "patient", "should", "may"})
_TOKEN_RE = re.compile(r"[a-z0-9.%-]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _salient(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def run(*, answer: dict[str, Any] | str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """Gate ``answer`` ({"text", "cited_evidence_ids"?} or plain text) on ``evidence``.

    Evidence items: {"id", "kind", "text"}.
    """
    if isinstance(answer, str):
        answer_obj: dict[str, Any] = {"text": answer, "cited_evidence_ids": []}
    elif isinstance(answer, dict) and "text" in answer:
        answer_obj = {"text": str(answer["text"]),
                      "cited_evidence_ids": list(answer.get("cited_evidence_ids", []))}
    else:
        raise TypeError("answer must be text or a dict with text")
    if not isinstance(evidence, list):
        raise TypeError("evidence must be a list of id/kind/text dicts")
    by_id: dict[str, dict[str, Any]] = {}
    for i, e in enumerate(evidence):
        if not isinstance(e, dict) or not all(k in e for k in ("id", "kind", "text")):
            raise ValueError(f"evidence[{i}] needs id, kind, text")
        if e["kind"] not in SUFFICIENT_KINDS | SOFT_KINDS:
            raise ValueError(f"evidence[{i}] kind {e['kind']!r} unknown; "
                             f"known: {sorted(SUFFICIENT_KINDS | SOFT_KINDS)}")
        by_id[str(e["id"])] = e

    failures: list[str] = []
    # 1. Every cited id must exist (a fabricated citation is an instant block).
    missing = [cid for cid in answer_obj["cited_evidence_ids"] if str(cid) not in by_id]
    if missing:
        failures.append(f"cited evidence ids do not exist: {missing}")
    # 2. Every claim sentence must be supported by at least one HARD item.
    hard = [e for e in evidence if e["kind"] in SUFFICIENT_KINDS]
    unsupported: list[str] = []
    soft_only: list[str] = []
    for sent in (s.strip() for s in _SENTENCE_SPLIT_RE.split(answer_obj["text"]) if s.strip()):
        terms = _salient(sent)
        if not terms:
            continue
        if any(len(terms & _salient(e["text"])) >= CLAIM_SUPPORT_OVERLAP for e in hard):
            continue
        if any(len(terms & _salient(e["text"])) >= CLAIM_SUPPORT_OVERLAP
               for e in evidence if e["kind"] in SOFT_KINDS):
            soft_only.append(sent)
        else:
            unsupported.append(sent)
    if unsupported:
        failures.append(f"claims with no supporting evidence: {unsupported}")
    if soft_only:
        failures.append(f"claims supported ONLY by opinion/model interpretation: {soft_only}")
    # 3. No evidence at all → block regardless of how confident the text sounds.
    if not evidence:
        failures.append("no evidence provided")

    sufficient = not failures
    return {"sufficient": sufficient,
            "reason": {"decision": "pass" if sufficient else "abstain",
                       "route": None if sufficient else ABSTAIN_ROUTE,
                       "failures": failures,
                       "hard_evidence_count": len(hard),
                       "disposition": "proposed", "serves_truth": False}}


def _selftest() -> None:
    evidence = [
        {"id": "lab1", "kind": "lab_result", "text": "potassium 6.8 mmol/L measured at 09:14"},
        {"id": "doc1", "kind": "documented_finding", "text": "patient reports muscle weakness today"},
        {"id": "op1", "kind": "opinion", "text": "the night shift suspects dietary causes"},
    ]
    # A grounded answer passes.
    ok = run(answer={"text": "Potassium is critically elevated at 6.8 mmol/L. Muscle weakness is documented.",
                     "cited_evidence_ids": ["lab1", "doc1"]}, evidence=evidence)
    assert ok["sufficient"] is True and ok["reason"]["decision"] == "pass"
    # An unsupported claim blocks and routes to clinician review.
    guess = run(answer="The patient is in renal failure and needs dialysis tonight.",
                evidence=evidence)
    assert guess["sufficient"] is False and guess["reason"]["route"] == ABSTAIN_ROUTE
    assert any("no supporting evidence" in f for f in guess["reason"]["failures"])
    # Opinion-only support is named explicitly — soft evidence never suffices.
    soft = run(answer="Dietary causes explain the potassium.", evidence=[evidence[2]])
    assert soft["sufficient"] is False
    assert any("ONLY by opinion" in f for f in soft["reason"]["failures"])
    # A fabricated citation is an instant block even when the text is plausible.
    fab = run(answer={"text": "Potassium 6.8 mmol/L is critical.",
                      "cited_evidence_ids": ["lab1", "made-up-9"]}, evidence=evidence)
    assert fab["sufficient"] is False and any("do not exist" in f for f in fab["reason"]["failures"])
    # No evidence at all → abstain, regardless of confident phrasing.
    empty = run(answer="Definitely fine, no action needed.", evidence=[])
    assert empty["sufficient"] is False
    # Propose-never-dispose pinned; deterministic; on_error=raise.
    assert guess["reason"]["disposition"] == "proposed" and guess["reason"]["serves_truth"] is False
    assert json.dumps(run(answer="Potassium 6.8 mmol/L.", evidence=evidence), sort_keys=True) == \
           json.dumps(run(answer="Potassium 6.8 mmol/L.", evidence=evidence), sort_keys=True)
    raised = False
    try:
        run(answer="x", evidence=[{"id": "e", "kind": "vibes", "text": "t"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — clinical_abstention_gate: per-claim hard-evidence support, opinion/model "
          "support named and insufficient, fabricated citations block, empty evidence "
          f"abstains to '{ABSTAIN_ROUTE}', proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
