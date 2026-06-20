#!/usr/bin/env python3
"""Backs `processor/icd10-code-grounder` (process_kind ``coerce.icd_ground``).

Resolve each candidate diagnosis to an ICD-10-CM code via EXACT lookup
against an injected terminology corpus (code ↔ canonical term + synonyms),
linking every resolved code to the documented evidence span it came from.
Undocumented or unmatched diagnoses are left UNCODED (abstain) — this
eliminates the bare model's habit of fabricating plausible-but-wrong codes.
The grounder never invents a code, never fuzzy-guesses across terms, and
requires a documentation span for every coded diagnosis.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs diagnoses, terminology_corpus → outputs codes, abstained.

CLI / self-test: python3 scripts/processors/clinical/icd10_code_grounder.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

ABSTAIN_NO_MATCH = "no exact terminology match — left uncoded rather than guessed"
ABSTAIN_NO_EVIDENCE = "no documented evidence span — a diagnosis without documentation is never coded"


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split())


def run(*, diagnoses: list[dict[str, Any]],
        terminology_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Ground ``diagnoses`` ([{"term", "evidence_span"?}]) in the corpus.

    Corpus entries: {"code", "term", "synonyms"?: [str], "citation"}.
    """
    if not isinstance(diagnoses, list):
        raise TypeError("diagnoses must be a list of term dicts")
    if not isinstance(terminology_corpus, list):
        raise TypeError("terminology_corpus must be a list")
    index: dict[str, dict[str, Any]] = {}
    for i, e in enumerate(terminology_corpus):
        if not isinstance(e, dict) or not all(k in e for k in ("code", "term", "citation")):
            raise ValueError(f"terminology_corpus[{i}] needs code, term, citation")
        index[_norm(e["term"])] = e
        for syn in e.get("synonyms", []) or []:
            index.setdefault(_norm(syn), e)

    codes: list[dict[str, Any]] = []
    abstained: list[dict[str, Any]] = []
    for i, d in enumerate(diagnoses):
        if not isinstance(d, dict) or "term" not in d:
            raise ValueError(f"diagnoses[{i}] needs term")
        span = d.get("evidence_span")
        if not span:
            abstained.append({"term": d["term"], "reason": ABSTAIN_NO_EVIDENCE})
            continue
        entry = index.get(_norm(d["term"]))
        if entry is None:
            abstained.append({"term": d["term"], "reason": ABSTAIN_NO_MATCH,
                              "evidence_span": span})
            continue
        codes.append({"code": entry["code"], "canonical_term": entry["term"],
                      "as_documented": d["term"], "evidence_span": span,
                      "citation": entry["citation"],
                      "match": "exact_terminology"})
    return {"codes": {"resolved": codes, "disposition": "proposed", "serves_truth": False},
            "abstained": abstained}


def _selftest() -> None:
    # SYNTHETIC demo terminology — proves the mechanism, not a code set.
    corpus = [
        {"code": "DEMO-E11.9", "term": "type 2 diabetes mellitus without complications",
         "synonyms": ["type 2 diabetes", "t2dm"], "citation": "demo-icd:e119@v1"},
        {"code": "DEMO-I10", "term": "essential hypertension",
         "synonyms": ["high blood pressure"], "citation": "demo-icd:i10@v1"},
    ]
    diagnoses = [
        {"term": "Type 2 Diabetes", "evidence_span": "A1c 8.1% on metformin (note line 12)"},
        {"term": "high blood pressure", "evidence_span": "BP 152/94 repeated (vitals 09:14)"},
        {"term": "fibromyalgia", "evidence_span": "patient mentions diffuse pain"},
        {"term": "essential hypertension"},  # no evidence span
    ]
    out = run(diagnoses=diagnoses, terminology_corpus=corpus)
    resolved = {c["as_documented"]: c for c in out["codes"]["resolved"]}
    # Exact + synonym matches resolve WITH the evidence span and citation linked.
    assert resolved["Type 2 Diabetes"]["code"] == "DEMO-E11.9"
    assert "A1c 8.1%" in resolved["Type 2 Diabetes"]["evidence_span"]
    assert resolved["high blood pressure"]["code"] == "DEMO-I10"
    assert resolved["high blood pressure"]["match"] == "exact_terminology"
    # Unmatched terms abstain (no fabricated code), reason recorded.
    reasons = {a["term"]: a["reason"] for a in out["abstained"]}
    assert reasons["fibromyalgia"] == ABSTAIN_NO_MATCH
    # No documentation → never coded, even though the term matches the corpus.
    assert reasons["essential hypertension"] == ABSTAIN_NO_EVIDENCE
    # Every resolved code is accounted; nothing invented (2 coded + 2 abstained = 4 in).
    assert len(out["codes"]["resolved"]) + len(out["abstained"]) == len(diagnoses)
    # Propose-never-dispose pinned; deterministic; on_error=raise.
    assert out["codes"]["disposition"] == "proposed" and out["codes"]["serves_truth"] is False
    assert json.dumps(run(diagnoses=diagnoses, terminology_corpus=corpus), sort_keys=True) == \
           json.dumps(run(diagnoses=diagnoses, terminology_corpus=corpus), sort_keys=True)
    raised = False
    try:
        run(diagnoses=[{"evidence_span": "x"}], terminology_corpus=corpus)
    except ValueError:
        raised = True
    assert raised
    print("PASS — icd10_code_grounder: exact terminology+synonym grounding with evidence "
          "spans + citations, undocumented/unmatched diagnoses ABSTAIN (never a "
          "fabricated code), full accounting, proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
