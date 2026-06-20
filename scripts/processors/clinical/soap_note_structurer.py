#!/usr/bin/env python3
"""Backs `processor/soap-note-structurer` (process_kind ``format_convert.soap_note``).

Structure a dictated/free-text encounter into Subjective / Objective /
Assessment / Plan sections, each item linked to its SOURCE SPAN in the
original text (char offsets — the lossless law at the formatting layer:
restructuring never replaces the raw encounter). Classification is
deterministic: section-header cues first, then sentence-pattern rules, then
the RUNNING header (after a dictated "Plan:" the following unmatched
sentences belong to Plan — that is the dictation's own declared structure,
marked ``classified_by: running_header``, not a guess). Sentences matching
nothing before any header land in ``unclassified`` — returned, never
dropped, never guessed into a section. Coded diagnoses are DEFERRED to the
ICD grounder; this structurer never invents codes.

Contract: deterministic; side_effects=none; on_error=raise.
Input encounter → output soap.

CLI / self-test: python3 scripts/processors/clinical/soap_note_structurer.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

SECTIONS = ("subjective", "objective", "assessment", "plan")

#: Explicit header cues (a dictation often says them) — highest precedence.
HEADER_CUES = {
    "subjective": re.compile(r"^(?:s|subj|subjective)\s*[:\-]", re.I),
    "objective": re.compile(r"^(?:o|obj|objective|exam|vitals)\s*[:\-]", re.I),
    "assessment": re.compile(r"^(?:a|assessment|impression)\s*[:\-]", re.I),
    "plan": re.compile(r"^(?:p|plan)\s*[:\-]", re.I),
}

#: Sentence-pattern rules, tried in order (first match wins).
PATTERN_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("subjective", re.compile(r"\b(?:patient (?:reports|states|complains|denies)|c/o|"
                              r"reports|states that|since (?:yesterday|this morning|last))\b", re.I)),
    ("objective", re.compile(r"\b(?:bp|blood pressure|hr|heart rate|temp(?:erature)?|spo2|rr|"
                             r"respiratory rate|\d+\s*/\s*\d+\s*mmhg|on exam|auscultation|"
                             r"labs?\b|a1c|examination shows)\b", re.I)),
    ("plan", re.compile(r"\b(?:start|begin|prescribe|order|schedule|follow[- ]?up|refer|"
                        r"increase|decrease|discontinue|recheck|return if)\b", re.I)),
    ("assessment", re.compile(r"\b(?:consistent with|likely|impression|suggests|"
                              r"differential|assessment|probable|uncontrolled)\b", re.I)),
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def run(*, encounter: str) -> dict[str, Any]:
    """Structure ``encounter`` into SOAP with char-span lineage per item."""
    if not isinstance(encounter, str):
        raise TypeError(f"encounter must be str, got {type(encounter).__name__}")
    sections: dict[str, list[dict[str, Any]]] = {s: [] for s in SECTIONS}
    unclassified: list[dict[str, Any]] = []
    cursor = 0
    current_header: str | None = None
    for raw in _SENTENCE_SPLIT_RE.split(encounter):
        sent = raw.strip()
        if not sent:
            continue
        start = encounter.find(sent, cursor)
        if start < 0:
            start = encounter.find(sent)
        cursor = start + len(sent) if start >= 0 else cursor
        item = {"text": sent, "char_start": start, "char_end": start + len(sent)}
        # Header cue switches the running section and classifies its own line.
        header_hit = next((s for s, pat in HEADER_CUES.items() if pat.match(sent)), None)
        if header_hit is not None:
            current_header = header_hit
            body = re.split(r"[:\-]", sent, maxsplit=1)[1].strip()
            if body:
                sections[header_hit].append({**item, "classified_by": "header_cue"})
            continue
        rule_hit = next((s for s, pat in PATTERN_RULES if pat.search(sent)), None)
        if rule_hit is not None:
            sections[rule_hit].append({**item, "classified_by": "pattern_rule"})
        elif current_header is not None:
            sections[current_header].append({**item, "classified_by": "running_header"})
        else:
            unclassified.append({**item, "reason": "no header cue or pattern matched — not guessed"})
    total = sum(len(v) for v in sections.values()) + len(unclassified)
    return {"soap": {**{s: sections[s] for s in SECTIONS},
                     "unclassified": unclassified,
                     "items_total": total,
                     "coding_note": "diagnosis codes deferred to processor/icd10-code-grounder — never invented here",
                     "raw_preserved": True, "disposition": "proposed", "serves_truth": False}}


def _selftest() -> None:
    encounter = ("The weather was nice on the drive in. "
                 "Patient reports worsening thirst and fatigue since last month. "
                 "BP 152/94 mmHg, A1c 8.1%. "
                 "Findings consistent with uncontrolled type 2 diabetes. "
                 "Start metformin 500 mg daily and schedule follow-up in 6 weeks. "
                 "Plan: recheck A1c at the visit.")
    out = run(encounter=encounter)["soap"]
    # Each sentence lands in its section with exact char-span lineage.
    assert any("worsening thirst" in i["text"] for i in out["subjective"])
    assert any("152/94" in i["text"] for i in out["objective"])
    assert any("consistent with" in i["text"] for i in out["assessment"])
    assert any(i["text"].startswith("Start metformin") for i in out["plan"])
    for sec in ("subjective", "objective", "assessment", "plan"):
        for item in out[sec]:
            assert encounter[item["char_start"]:item["char_end"]] == item["text"]
    # The explicit "Plan:" header classifies via the cue.
    assert any(i["classified_by"] == "header_cue" and "recheck A1c" in i["text"]
               for i in out["plan"])
    # Off-topic prose is UNCLASSIFIED with a reason — never guessed into a section.
    assert any("weather" in u["text"] for u in out["unclassified"])
    # Lossless accounting: every sentence is somewhere.
    assert out["items_total"] == 6 and out["raw_preserved"] is True
    # Codes are deferred, never minted here.
    assert "icd10-code-grounder" in out["coding_note"]
    assert re.search(r"\b[A-Z]\d{2}\.\d", json.dumps(out)) is None  # no ICD-shaped strings invented
    # Propose-never-dispose pinned; deterministic; on_error=raise.
    assert out["disposition"] == "proposed" and out["serves_truth"] is False
    assert json.dumps(run(encounter=encounter), sort_keys=True) == \
           json.dumps(run(encounter=encounter), sort_keys=True)
    raised = False
    try:
        run(encounter=42)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
    print("PASS — soap_note_structurer: S/O/A/P via header cues + pattern rules with "
          "exact char-span lineage, unclassified kept with reasons (never guessed), "
          "codes deferred to the grounder, lossless accounting verified")


if __name__ == "__main__":
    _selftest()
