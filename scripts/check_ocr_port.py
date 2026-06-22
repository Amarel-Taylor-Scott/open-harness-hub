#!/usr/bin/env python3
"""check_ocr_port — OCR/document-parse is an agnostic, registry-populated port that scales to future engines.

Proves: the port enumerates from architecture/ocr_provider_registry.json; 'auto' picks the CHEAPEST reachable engine
(text-layer before local OCR before cloud before vision-LLM); a cloud engine is excluded without its key; an absent
engine reports UNAVAILABLE (never fabricates text); and the DROP-IN TEST — a future OCR engine registers in one line and
an unchanged caller uses it. serves_truth=false.

  python3 scripts/check_ocr_port.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.teleon.extraction.ocr_port import (available_ocr, select_ocr, descent_order, register_ocr_adapter,
                                                CallableOCR, UnavailableOCR)
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    av = available_ocr()
    ck(f"port POPULATED FROM the registry ({len(av['providers'])} engines: text-layer/local/cloud/vision-llm)",
       len(av["providers"]) >= 6 and "tesseract" in av["providers"] and "pdf_text_layer" in av["providers"])
    ck("the PDF text layer is reachable with no deps (the cheapest acquire)", "pdf_text_layer" in av["reachable"])
    order = descent_order()
    ck("descent order is cheapest-first (text layer leads)", order and order[0] == "pdf_text_layer")
    ck("'auto' selects the cheapest reachable engine (the text layer, no key/binary needed)",
       select_ocr("auto").name == "pdf_text_layer")
    ck("a cloud engine is EXCLUDED without its key (honest)", not select_ocr("aws_textract").available())
    ck("an unknown engine → UnavailableOCR (never fabricates)", isinstance(select_ocr("nope-9000"), UnavailableOCR))
    ck("an unavailable engine extract() returns '' (no fabricated text)", select_ocr("aws_textract").extract("x.pdf") == "")

    # DROP-IN TEST: a future OCR engine registers in one line; an unchanged caller uses it
    register_ocr_adapter("future_ocr_2027", lambda: CallableOCR(lambda src: "TEXT-BY-FUTURE-OCR", name="future_ocr_2027"))
    fut = select_ocr("future_ocr_2027")
    ck("a FUTURE OCR engine drops in via one-line registration + an unchanged caller uses it",
       fut.available() and fut.extract("scan.png") == "TEXT-BY-FUTURE-OCR" and "future_ocr_2027" in available_ocr()["adapters"])

    print("\n" + ("PASS - check_ocr_port: OCR/document-parse behind an agnostic port populated from the registry; 'auto' "
                  "picks the cheapest reachable engine; cloud key-gated; absent engines honest (no fabrication); a future "
                  "engine drops in with zero caller change. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
