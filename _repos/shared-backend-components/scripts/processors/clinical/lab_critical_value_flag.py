#!/usr/bin/env python3
"""Backs `processor/lab-critical-value-flag` (process_kind ``gate.lab_critical_value``).

The panic-value safety net: compare lab results against an injected governed
reference table (normal range + critical thresholds per analyte, with
citations) and ESCALATE critical values immediately. Deterministic, no model
call. An analyte the table does not cover is an honest ``uncovered`` row —
never assumed normal; a unit mismatch is an ERROR, never a silent conversion.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs labs, reference_ranges → outputs critical, escalate.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/clinical/lab_critical_value_flag.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Result classifications (single definition; dashboards read these).
CLASS_CRITICAL = "critical"
CLASS_ABNORMAL = "abnormal"
CLASS_NORMAL = "normal"
CLASS_UNCOVERED = "uncovered"


def _norm(name: str) -> str:
    return " ".join(str(name).lower().split())


def run(*, labs: list[dict[str, Any]], reference_ranges: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify every lab against the injected reference table.

    labs: [{"analyte", "value", "unit"}]; reference_ranges entries:
    {"analyte", "unit", "normal_low", "normal_high", "critical_low"?,
    "critical_high"?, "citation"}.
    """
    if not isinstance(labs, list):
        raise TypeError("labs must be a list of analyte/value/unit dicts")
    if not isinstance(reference_ranges, list):
        raise TypeError("reference_ranges must be a list")
    table: dict[str, dict[str, Any]] = {}
    for i, r in enumerate(reference_ranges):
        if not isinstance(r, dict) or not all(k in r for k in ("analyte", "unit", "normal_low", "normal_high", "citation")):
            raise ValueError(f"reference_ranges[{i}] needs analyte, unit, normal_low, normal_high, citation")
        table[_norm(r["analyte"])] = r

    rows: list[dict[str, Any]] = []
    criticals: list[dict[str, Any]] = []
    for i, lab in enumerate(labs):
        if not isinstance(lab, dict) or not all(k in lab for k in ("analyte", "value", "unit")):
            raise ValueError(f"labs[{i}] needs analyte, value, unit")
        name = _norm(lab["analyte"])
        ref = table.get(name)
        if ref is None:
            rows.append({"analyte": lab["analyte"], "value": lab["value"], "unit": lab["unit"],
                         "classification": CLASS_UNCOVERED,
                         "note": "no governed reference range — NOT assumed normal"})
            continue
        if _norm(lab["unit"]) != _norm(ref["unit"]):
            raise ValueError(f"unit mismatch for {lab['analyte']!r}: result in {lab['unit']!r}, "
                             f"reference in {ref['unit']!r} — refusing to compare across units")
        value = float(lab["value"])
        crit_low = ref.get("critical_low")
        crit_high = ref.get("critical_high")
        if (crit_low is not None and value <= float(crit_low)) or \
           (crit_high is not None and value >= float(crit_high)):
            cls = CLASS_CRITICAL
        elif value < float(ref["normal_low"]) or value > float(ref["normal_high"]):
            cls = CLASS_ABNORMAL
        else:
            cls = CLASS_NORMAL
        row = {"analyte": lab["analyte"], "value": value, "unit": lab["unit"],
               "classification": cls, "citation": ref["citation"]}
        rows.append(row)
        if cls == CLASS_CRITICAL:
            criticals.append(row)
    return {"critical": {"results": rows, "critical_hits": criticals,
                         "disposition": "proposed", "serves_truth": False},
            "escalate": {"required": bool(criticals),
                         "action": "notify clinician immediately (panic-value protocol)"
                                   if criticals else None,
                         "analytes": [c["analyte"] for c in criticals]}}


def _selftest() -> None:
    # SYNTHETIC demo reference table — proves the mechanism, not clinical data.
    refs = [
        {"analyte": "potassium", "unit": "mmol/L", "normal_low": 3.5, "normal_high": 5.0,
         "critical_low": 2.5, "critical_high": 6.5, "citation": "demo-ranges:k@v1"},
        {"analyte": "glucose", "unit": "mg/dL", "normal_low": 70, "normal_high": 140,
         "critical_low": 40, "critical_high": 500, "citation": "demo-ranges:glu@v1"},
    ]
    labs = [
        {"analyte": "Potassium", "value": 6.8, "unit": "mmol/L"},   # critical high
        {"analyte": "Glucose", "value": 150, "unit": "mg/dL"},      # abnormal, not critical
        {"analyte": "tsh", "value": 2.0, "unit": "mIU/L"},          # uncovered analyte
    ]
    out = run(labs=labs, reference_ranges=refs)
    rows = {r["analyte"]: r for r in out["critical"]["results"]}
    # The panic value fires and escalates immediately with its citation.
    assert rows["Potassium"]["classification"] == CLASS_CRITICAL
    assert rows["Potassium"]["citation"] == "demo-ranges:k@v1"
    assert out["escalate"]["required"] is True and out["escalate"]["analytes"] == ["Potassium"]
    # Abnormal-but-not-critical stays a flag, not an escalation.
    assert rows["Glucose"]["classification"] == CLASS_ABNORMAL
    # Uncovered analytes are honest unknowns, never assumed normal.
    assert rows["tsh"]["classification"] == CLASS_UNCOVERED
    # Boundary semantics: >= critical_high is critical (6.5 itself fires).
    edge = run(labs=[{"analyte": "potassium", "value": 6.5, "unit": "mmol/L"}],
               reference_ranges=refs)
    assert edge["escalate"]["required"] is True
    # All-normal panel → no escalation; propose-never-dispose pinned.
    calm = run(labs=[{"analyte": "potassium", "value": 4.0, "unit": "mmol/L"}],
               reference_ranges=refs)
    assert calm["escalate"]["required"] is False
    assert calm["critical"]["disposition"] == "proposed" and calm["critical"]["serves_truth"] is False
    # Unit mismatch is an ERROR — never silently converted.
    raised = False
    try:
        run(labs=[{"analyte": "glucose", "value": 8.3, "unit": "mmol/L"}], reference_ranges=refs)
    except ValueError as e:
        raised = "unit mismatch" in str(e)
    assert raised
    # Deterministic; on_error=raise for malformed rows.
    assert json.dumps(run(labs=labs, reference_ranges=refs), sort_keys=True) == \
           json.dumps(run(labs=labs, reference_ranges=refs), sort_keys=True)
    raised = False
    try:
        run(labs=[{"analyte": "x"}], reference_ranges=refs)
    except ValueError:
        raised = True
    assert raised
    print("PASS — lab_critical_value_flag: governed-range classification with citations, "
          "panic values escalate immediately (boundary-inclusive), uncovered analytes "
          "honest, unit mismatches refuse, proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
