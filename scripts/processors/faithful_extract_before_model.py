#!/usr/bin/env python3
"""Backs `processor/faithful-extract-before-model` (process_kind ``extract.structured_fields``).

Pre-LLM faithful extraction: pull every machine-readable field out of a
structured input (weather bulletin, advisory, form, tabular text) with
DETERMINISTIC parsers BEFORE the model sees anything, and inject the result
as a fenced ``extracted_facts`` block the prompt builds on. The model then
narrates facts it was handed instead of re-reading (and mis-reading) the
source. Fields the parsers cannot extract are listed in
``unextracted_fields`` — the model is told what it does NOT have, which is
how hallucinated values get squeezed out.

The field map is INJECTED ({"field": regex-with-one-capture-group}) — the
caller's domain owns its shapes; this processor owns the discipline.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs raw_text, input_type, field_map, system_prompt_prefix →
extracted_fields, unextracted_fields, prompt_block, extraction_coverage.

CLI / self-test: python3 scripts/processors/faithful_extract_before_model.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The fenced block label the prompt layer greps for.
FACTS_FENCE = "extracted_facts"

#: Instruction emitted with the block — the contract that makes extraction
#: useful: facts are authoritative, missing means missing.
BLOCK_CONTRACT = ("Use ONLY the values in the extracted_facts block for these fields. "
                  "Fields listed as NOT EXTRACTED are unknown — say so, never invent them.")

COVERAGE_DECIMALS = 4


def run(*, raw_text: str, input_type: str, field_map: dict[str, str],
        system_prompt_prefix: str = "") -> dict[str, Any]:
    """Extract ``field_map`` fields from ``raw_text``; build the prompt block."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty str")
    if not isinstance(input_type, str) or not input_type:
        raise ValueError("input_type must be a non-empty label (e.g. weather_bulletin)")
    if not isinstance(field_map, dict) or not field_map:
        raise ValueError("field_map must be a non-empty dict of field -> regex")
    extracted: dict[str, dict[str, Any]] = {}
    unextracted: list[str] = []
    for field in sorted(field_map):
        pattern = field_map[field]
        try:
            rx = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as exc:
            raise ValueError(f"field_map[{field!r}] is not a valid regex: {exc}") from exc
        if rx.groups != 1:
            raise ValueError(f"field_map[{field!r}] must have exactly ONE capture group "
                             f"(has {rx.groups}) — the group IS the value")
        m = rx.search(raw_text)
        if m and m.group(1).strip():
            extracted[field] = {"value": m.group(1).strip(),
                                "span": [m.start(1), m.end(1)],
                                "quote": m.group(0).strip()}
        else:
            unextracted.append(field)
    coverage = round(len(extracted) / len(field_map), COVERAGE_DECIMALS)

    lines = [f"```{FACTS_FENCE}", f"input_type: {input_type}"]
    lines += [f"{f}: {extracted[f]['value']}" for f in sorted(extracted)]
    if unextracted:
        lines += [f"NOT EXTRACTED: {', '.join(unextracted)}"]
    lines += ["```", BLOCK_CONTRACT]
    prompt_block = ((system_prompt_prefix.rstrip() + "\n\n") if system_prompt_prefix else "") \
        + "\n".join(lines)
    return {"extracted_fields": extracted,
            "unextracted_fields": unextracted,
            "prompt_block": prompt_block,
            "extraction_coverage": coverage}


def _selftest() -> None:
    bulletin = ("PAGASA WEATHER BULLETIN #14\n"
                "Typhoon: AMANG\n"
                "Signal No. 3 over Eastern Samar\n"
                "Max winds: 155 km/h near the center\n"
                "Movement: WNW at 20 km/h\n")
    field_map = {
        "typhoon_name": r"Typhoon:\s*([A-Z]+)",
        "signal_level": r"Signal No\.\s*(\d+)",
        "max_winds_kmh": r"Max winds:\s*(\d+)\s*km/h",
        "rainfall_mm": r"Rainfall:\s*(\d+)\s*mm",       # not present in this bulletin
    }
    out = run(raw_text=bulletin, input_type="weather_bulletin", field_map=field_map,
              system_prompt_prefix="You write radio alerts.")
    # Extraction with value + exact span + verbatim quote lineage.
    assert out["extracted_fields"]["typhoon_name"]["value"] == "AMANG"
    assert out["extracted_fields"]["signal_level"]["value"] == "3"
    span = out["extracted_fields"]["max_winds_kmh"]["span"]
    assert bulletin[span[0]:span[1]] == "155"
    assert "Max winds: 155 km/h" in out["extracted_fields"]["max_winds_kmh"]["quote"]
    # The absent field is DECLARED missing — in the list AND in the block.
    assert out["unextracted_fields"] == ["rainfall_mm"]
    assert "NOT EXTRACTED: rainfall_mm" in out["prompt_block"]
    assert out["extraction_coverage"] == 0.75
    # The block carries the fence, the facts, the contract, and the prefix.
    assert out["prompt_block"].startswith("You write radio alerts.")
    assert f"```{FACTS_FENCE}" in out["prompt_block"] and BLOCK_CONTRACT in out["prompt_block"]
    assert "typhoon_name: AMANG" in out["prompt_block"]
    # Deterministic; on_error=raise: zero/two capture groups, bad regex, empty inputs.
    assert json.dumps(run(raw_text=bulletin, input_type="t", field_map=field_map), sort_keys=True) == \
           json.dumps(run(raw_text=bulletin, input_type="t", field_map=field_map), sort_keys=True)
    for bad_map in ({"f": r"no group"}, {"f": r"(two)(groups)"}, {"f": r"(unclosed"}):
        raised = False
        try:
            run(raw_text=bulletin, input_type="t", field_map=bad_map)
        except ValueError:
            raised = True
        assert raised
    raised = False
    try:
        run(raw_text="  ", input_type="t", field_map={"f": "(x)"})
    except ValueError:
        raised = True
    assert raised
    print("PASS — faithful_extract_before_model: one-capture-group field maps, span+quote "
          "lineage per value, missing fields DECLARED in the block (anti-hallucination "
          "contract), coverage reported, deterministic verified")


if __name__ == "__main__":
    _selftest()
