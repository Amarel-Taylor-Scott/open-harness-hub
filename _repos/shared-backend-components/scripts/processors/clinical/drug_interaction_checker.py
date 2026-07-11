#!/usr/bin/env python3
"""Backs `processor/drug-interaction-checker` (process_kind ``verify.drug_interaction``).

Deterministic lookup of EVERY medication pair in a list against an injected
governed interaction corpus — severity-tiered hits with the corpus citation
and a prescriber-flag action. Never a model guess about safety: a pair the
corpus does not cover is reported as ``uncovered`` (honest unknown), not
assumed safe.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs med_list, interaction_corpus → outputs interactions, severity.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/clinical/drug_interaction_checker.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Severity tiers, worst-first; the envelope's top-level severity is the worst
#: hit. Unknown corpus severities raise (a typo must not soften a warning).
SEVERITY_ORDER = ("contraindicated", "major", "moderate", "minor")
NO_HIT_SEVERITY = "none"

#: Action per severity tier (single definition; the UI reads it).
SEVERITY_ACTION = {
    "contraindicated": "block_order_and_escalate",
    "major": "flag_prescriber_before_dispense",
    "moderate": "flag_prescriber",
    "minor": "note_in_chart",
}


def _norm(name: str) -> str:
    return " ".join(str(name).lower().split())


def run(*, med_list: list[str], interaction_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Check every pair in ``med_list`` against the injected corpus.

    Corpus entries: {"drug_a", "drug_b", "severity", "mechanism"?, "citation"}.
    """
    if not isinstance(med_list, list) or not all(isinstance(m, str) and m.strip() for m in med_list):
        raise TypeError("med_list must be a list of non-empty drug-name strings")
    if not isinstance(interaction_corpus, list):
        raise TypeError("interaction_corpus must be a list of entries")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for i, e in enumerate(interaction_corpus):
        if not isinstance(e, dict) or not all(k in e for k in ("drug_a", "drug_b", "severity", "citation")):
            raise ValueError(f"interaction_corpus[{i}] needs drug_a, drug_b, severity, citation")
        if e["severity"] not in SEVERITY_ORDER:
            raise ValueError(f"interaction_corpus[{i}] severity {e['severity']!r} "
                             f"not in {SEVERITY_ORDER}")
        key = tuple(sorted((_norm(e["drug_a"]), _norm(e["drug_b"]))))
        index[key] = e

    meds = sorted({_norm(m) for m in med_list})
    hits: list[dict[str, Any]] = []
    uncovered: list[list[str]] = []
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            pair = (meds[i], meds[j])
            entry = index.get(pair)
            if entry is None:
                uncovered.append(list(pair))
                continue
            hits.append({"pair": list(pair), "severity": entry["severity"],
                         "mechanism": entry.get("mechanism"),
                         "citation": entry["citation"],
                         "action": SEVERITY_ACTION[entry["severity"]]})
    hits.sort(key=lambda h: (SEVERITY_ORDER.index(h["severity"]), h["pair"]))
    worst = hits[0]["severity"] if hits else NO_HIT_SEVERITY
    return {"interactions": {"hits": hits,
                             "uncovered_pairs": uncovered,
                             "pairs_checked": len(meds) * (len(meds) - 1) // 2,
                             "disposition": "proposed", "serves_truth": False},
            "severity": worst}


def _selftest() -> None:
    # SYNTHETIC demo corpus — proves the mechanism, not clinical reference data.
    corpus = [
        {"drug_a": "warfarin", "drug_b": "fluconazole", "severity": "major",
         "mechanism": "CYP2C9 inhibition raises INR", "citation": "demo-corpus:wf-flu@v1"},
        {"drug_a": "simvastatin", "drug_b": "clarithromycin", "severity": "contraindicated",
         "mechanism": "CYP3A4 inhibition", "citation": "demo-corpus:sim-cla@v1"},
        {"drug_a": "aspirin", "drug_b": "ibuprofen", "severity": "moderate",
         "citation": "demo-corpus:asa-ibu@v1"},
    ]
    out = run(med_list=["Warfarin", "Fluconazole", "Simvastatin", "Clarithromycin"],
              interaction_corpus=corpus)
    ix = out["interactions"]
    # Every pair checked; hits carry citation + tiered action; worst severity tops.
    assert ix["pairs_checked"] == 6 and out["severity"] == "contraindicated"
    assert ix["hits"][0]["pair"] == ["clarithromycin", "simvastatin"]
    assert ix["hits"][0]["action"] == "block_order_and_escalate"
    wf = next(h for h in ix["hits"] if "warfarin" in h["pair"])
    assert wf["citation"] == "demo-corpus:wf-flu@v1" and wf["severity"] == "major"
    # Uncovered pairs are HONEST unknowns, not assumed safe.
    assert ["fluconazole", "simvastatin"] in ix["uncovered_pairs"]
    # Propose-never-dispose pinned.
    assert ix["disposition"] == "proposed" and ix["serves_truth"] is False
    # Case/whitespace-insensitive matching; duplicates collapse.
    dup = run(med_list=["WARFARIN ", "warfarin", "Fluconazole"], interaction_corpus=corpus)
    assert dup["interactions"]["pairs_checked"] == 1 and dup["severity"] == "major"
    # No meds / single med → honest empty.
    assert run(med_list=["aspirin"], interaction_corpus=corpus)["severity"] == NO_HIT_SEVERITY
    # Deterministic; corpus untouched; on_error=raise (bad severity in corpus).
    snap = json.dumps(corpus, sort_keys=True)
    assert json.dumps(run(med_list=["aspirin", "ibuprofen"], interaction_corpus=corpus), sort_keys=True) == \
           json.dumps(run(med_list=["aspirin", "ibuprofen"], interaction_corpus=corpus), sort_keys=True)
    assert json.dumps(corpus, sort_keys=True) == snap
    raised = False
    try:
        run(med_list=["a", "b"], interaction_corpus=[{"drug_a": "a", "drug_b": "b",
                                                      "severity": "scary", "citation": "x"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — drug_interaction_checker: exhaustive pairwise lookup against the "
          "injected governed corpus, severity-tiered actions with citations, "
          "uncovered pairs honestly unknown, proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
