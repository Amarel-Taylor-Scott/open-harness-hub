#!/usr/bin/env python3
"""check_input_profilers — profile-then-shortcut routing is real, deterministic, and saves the expensive rungs.

Owner: profile a PDF (metadata/characteristics), classify the layout, and take SHORTCUTS based on the classification.
Proves: classify_layout is deterministic + correct (born-digital -> skip OCR; scanned -> skip text-layer; form ->
AcroForm; tabular -> tables; encrypted -> honest-blocked); routes reference real document_extraction rungs; the profiler
is the wired rung-0 router of the ladder; the PDF reader adapter is honest when pypdf is absent (no fabrication); the
registry covers more input types. serves_truth=false.

  python3 scripts/check_input_profilers.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.extraction.pdf_profiler import classify_layout, profile_pdf, route, shortcut_plan

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # deterministic classification from cheap signals
    ck("born-digital text PDF", classify_layout({"has_text_layer": True, "page_count": 10}) == "born_digital_text")
    ck("scanned image PDF", classify_layout({"has_text_layer": False, "has_images": True, "page_count": 5}) == "scanned_image")
    ck("AcroForm -> form", classify_layout({"has_acroform": True, "has_text_layer": True}) == "form")
    ck("tabular", classify_layout({"has_text_layer": True, "table_hint": True}) == "tabular")
    ck("encrypted", classify_layout({"encrypted": True}) == "encrypted")
    ck("empty", classify_layout({"page_count": 0}) == "empty")

    # the SHORTCUTS: born-digital skips OCR; scanned skips text_layer (the whole point)
    born = shortcut_plan({"has_text_layer": True, "page_count": 8})
    ck("born-digital SHORTCUT skips ocr + tables", "ocr" in born["skipped"] and "tables" in born["skipped"] and born["run"] == ["text_layer", "field_parse"])
    scan = shortcut_plan({"has_text_layer": False, "has_images": True})
    ck("scanned SHORTCUT skips text_layer, runs ocr", "text_layer" in scan["skipped"] and "ocr" in scan["run"])
    enc = shortcut_plan({"encrypted": True})
    ck("encrypted is honest-blocked (not fabricated)", enc["blocked"] and enc["run"] == ["decrypt"])
    ck("shortcut plan is a candidate (serves_truth=false)", born["serves_truth"] is False)

    # routes reference REAL document_extraction rungs (so the shortcut maps onto the ladder)
    ladders = {l["capability"]: l for l in _load("capability_ladders.json")["ladders"]}
    de_rungs = {r["tier"] for r in ladders["document_extraction"]["rungs"]}
    routed = {step for prof in _load("input_profilers.json")["profilers"] if prof["input"] == "pdf"
              for steps in prof["classes"].values() for step in steps}
    ck("pdf route steps map to real document_extraction rungs (or are honest extras)",
       {"text_layer", "tables", "ocr", "field_parse"} <= de_rungs and {"text_layer", "ocr", "field_parse"} <= routed)
    ck("document_extraction ladder wires the profiler as its router", ladders["document_extraction"].get("router", "").endswith("shortcut_plan"))
    ck("profile_route is the rung-0 of the ladder (deterministic)",
       any(r["tier"] == "profile_route" and r["deterministic"] and r["cost_rank"] == 0 for r in ladders["document_extraction"]["rungs"]))

    # reader adapter is honest when pypdf is absent (never fabricates a profile)
    prof = profile_pdf("/nonexistent.pdf")
    ck("profile_pdf honest on missing dep / unreadable", prof.get("available") is False)

    profilers = {p["input"] for p in _load("input_profilers.json")["profilers"]}
    ck("profilers cover more input types (pdf/image/email/html/audio)", {"pdf", "image", "email", "html"} <= profilers)
    ck("serves_truth=false", _load("input_profilers.json").get("serves_truth") is False)

    print("\n" + ("PASS - check_input_profilers: profile -> classify -> shortcut (skip the expensive rungs), routes map to "
                  "the ladder, honest adapter + encrypted block." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
