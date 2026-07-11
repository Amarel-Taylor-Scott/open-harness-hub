#!/usr/bin/env python3
"""Backs `processor/on-device-ocr-prepass` (process_kind ``format_convert.pdf_to_text``).

Run on-device OCR against an image BEFORE the model call, and inject the
extracted text as a fenced ``ocr_text`` block so the model narrates what the
OCR engine read instead of imagining what the photo says. The engine is
INJECTED (``ocr(image_bytes, language_hint) -> {"text", "confidence",
"boxes"?}`` — ML Kit / TFLite / Tesseract adapters in production). Without
an engine the call RAISES — OCR text is never faked. Low-confidence reads
are passed through but FLAGGED in the block, so the prompt itself warns the
model.

Contract: side_effects=none (pure transform around the injected engine);
on_error=raise. Inputs image_bytes, language_hint, engine → ocr_text,
bounding_boxes, confidence, engine_used, prompt_block.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/on_device_ocr_prepass.py
"""
from __future__ import annotations

import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Below this confidence the block carries an explicit low-confidence warning.
LOW_CONFIDENCE_THRESHOLD = 0.75

OCR_FENCE = "ocr_text"
LOW_CONFIDENCE_WARNING = ("WARNING: low OCR confidence — treat values as uncertain and "
                          "say so rather than asserting them.")
BLOCK_CONTRACT = ("Use ONLY the text in the ocr_text block as the document's content. "
                  "If a needed value is not in the block, it was not legible — say so.")

CONFIDENCE_DECIMALS = 4


def run(*, image_bytes: bytes, language_hint: str | None = None,
        engine: Callable[[bytes, str | None], dict[str, Any]] | None = None,
        engine_name: str = "injected-ocr-engine") -> dict[str, Any]:
    """OCR ``image_bytes`` via the injected engine; build the prompt block."""
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        raise ValueError("image_bytes must be non-empty bytes")
    if language_hint is not None and not isinstance(language_hint, str):
        raise TypeError("language_hint must be a str or None")
    if engine is None:
        raise RuntimeError("on_device_ocr_prepass requires an injected OCR engine "
                           "(engine=(image_bytes, language_hint) -> {'text', 'confidence'}); "
                           "OCR text is never faked")
    result = engine(bytes(image_bytes), language_hint)
    if not isinstance(result, dict) or "text" not in result or "confidence" not in result:
        raise ValueError("OCR engine returned no text/confidence — malformed engine result")
    text = str(result["text"])
    confidence = round(float(result["confidence"]), CONFIDENCE_DECIMALS)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"engine confidence must be in [0, 1], got {confidence}")
    boxes = result.get("boxes") or []
    low = confidence < LOW_CONFIDENCE_THRESHOLD

    lines = [f"```{OCR_FENCE}"]
    if language_hint:
        lines.append(f"language_hint: {language_hint}")
    lines.append(f"confidence: {confidence}")
    if low:
        lines.append(LOW_CONFIDENCE_WARNING)
    lines += [text.rstrip(), "```", BLOCK_CONTRACT]
    return {"ocr_text": text,
            "bounding_boxes": boxes,
            "confidence": confidence,
            "engine_used": engine_name,
            "low_confidence": low,
            "prompt_block": "\n".join(lines)}


def _selftest() -> None:
    def good_engine(img: bytes, hint: str | None) -> dict[str, Any]:
        assert img == b"fake-image" and hint == "fil"
        return {"text": "BAYAD: PHP 1,500.00\nPetsa: 2026-06-10",
                "confidence": 0.93,
                "boxes": [{"text": "BAYAD: PHP 1,500.00", "x": 10, "y": 12, "w": 220, "h": 24}]}

    out = run(image_bytes=b"fake-image", language_hint="fil",
              engine=good_engine, engine_name="mlkit-v2")
    # The engine's text flows into a fenced block with the use-only contract.
    assert out["ocr_text"].startswith("BAYAD") and out["engine_used"] == "mlkit-v2"
    assert f"```{OCR_FENCE}" in out["prompt_block"] and BLOCK_CONTRACT in out["prompt_block"]
    assert "PHP 1,500.00" in out["prompt_block"] and "language_hint: fil" in out["prompt_block"]
    assert out["low_confidence"] is False and LOW_CONFIDENCE_WARNING not in out["prompt_block"]
    assert out["bounding_boxes"][0]["w"] == 220
    # Low confidence flows through but the block WARNS the model.
    blurry = run(image_bytes=b"x", engine=lambda i, h: {"text": "barely legible", "confidence": 0.4})
    assert blurry["low_confidence"] is True and LOW_CONFIDENCE_WARNING in blurry["prompt_block"]
    # Refusals: no engine, malformed engine result, bad confidence, empty image.
    for bad in (lambda: run(image_bytes=b"x"),
                lambda: run(image_bytes=b"x", engine=lambda i, h: {"text": "t"}),
                lambda: run(image_bytes=b"x", engine=lambda i, h: {"text": "t", "confidence": 1.4}),
                lambda: run(image_bytes=b"", engine=lambda i, h: {"text": "t", "confidence": 0.9})):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    # Deterministic given the same scripted engine.
    assert json.dumps(run(image_bytes=b"fake-image", language_hint="fil", engine=good_engine),
                      sort_keys=True) == \
           json.dumps(run(image_bytes=b"fake-image", language_hint="fil", engine=good_engine),
                      sort_keys=True)
    print("PASS — on_device_ocr_prepass: injected engine (text never faked), fenced "
          "ocr_text block with use-only contract, low-confidence warning in-prompt, "
          "bounding boxes passed through, honest refusals verified")


if __name__ == "__main__":
    _selftest()
