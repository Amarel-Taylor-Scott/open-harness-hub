#!/usr/bin/env python3
"""Backs `processor/english-pivot-translation` (process_kind ``format_convert.translate_pivot``).

Two-step translation through English as the pivot: source language →
English → low-resource target (Waray, Ilocano, Kapampangan…), because
direct X→low-resource pairs are where small models fail hardest while
X→English and English→target are each far better resourced. The translator
is the INJECTED model adapter (``translate(text, source_language,
target_language) -> str``); this processor owns the pivot DISCIPLINE: both
hops recorded (the pivot text is lineage, not waste), English passthrough
skips the dead hop, optional TTS mode hands the result to the TTS
preprocessor. Without an adapter it RAISES — translations are never faked.

Contract: side_effects=none (around the injected adapter); on_error=raise.
Inputs source_text, source_language, target_language, tts_mode →
english_pivot_text, target_language_text, tts_ready_text.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/english_pivot_translation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

PIVOT_LANGUAGE = "english"


def run(*, source_text: str, source_language: str, target_language: str,
        tts_mode: bool = False,
        translate: Callable[[str, str, str], str] | None = None,
        tts_expansion_map: dict[str, str] | None = None) -> dict[str, Any]:
    """Translate via the English pivot using the injected adapter."""
    if not isinstance(source_text, str) or not source_text.strip():
        raise ValueError("source_text must be a non-empty str")
    for nm, v in (("source_language", source_language), ("target_language", target_language)):
        if not isinstance(v, str) or not v:
            raise ValueError(f"{nm} must be a non-empty language name/code")
    if translate is None:
        raise RuntimeError("english_pivot_translation requires an injected adapter "
                           "(translate=(text, source, target) -> str); translations are "
                           "never faked")
    src = source_language.lower()
    tgt = target_language.lower()
    hops: list[dict[str, str]] = []

    if src == PIVOT_LANGUAGE:
        english = source_text                      # dead hop skipped, honestly recorded
        hops.append({"hop": f"{src}->{PIVOT_LANGUAGE}", "method": "passthrough (already English)"})
    else:
        english = str(translate(source_text, src, PIVOT_LANGUAGE)).strip()
        if not english:
            raise ValueError("adapter returned an empty English pivot — refusing to continue")
        hops.append({"hop": f"{src}->{PIVOT_LANGUAGE}", "method": "adapter"})

    if tgt == PIVOT_LANGUAGE:
        target_text = english
        hops.append({"hop": f"{PIVOT_LANGUAGE}->{tgt}", "method": "passthrough (target is English)"})
    else:
        target_text = str(translate(english, PIVOT_LANGUAGE, tgt)).strip()
        if not target_text:
            raise ValueError("adapter returned an empty target translation — refusing to fake one")
        hops.append({"hop": f"{PIVOT_LANGUAGE}->{tgt}", "method": "adapter"})

    tts_ready = None
    if tts_mode:
        from scripts.processors.tts_preprocess_low_resource import run as tts_run  # single source
        tts_ready = tts_run(text=target_text, target_language=target_language,
                            expansion_map=tts_expansion_map or {})["preprocessed_text"]
    return {"english_pivot_text": english,
            "target_language_text": target_text,
            "tts_ready_text": tts_ready,
            "hops": hops,
            "pivot_language": PIVOT_LANGUAGE,
            "translation_is_model_output": True,   # candidate prose, never a verified fact
            "serves_truth": False}


def _selftest() -> None:
    # Scripted adapter: deterministic tagged hops so both stages are checkable.
    def adapter(text: str, source: str, target: str) -> str:
        return f"[{source}->{target}] {text}"

    out = run(source_text="Magbabaha sa baybayon bukas.", source_language="filipino",
              target_language="waray", translate=adapter)
    # Both hops happened, in order, through the pivot — with full lineage.
    assert out["english_pivot_text"] == "[filipino->english] Magbabaha sa baybayon bukas."
    assert out["target_language_text"].startswith("[english->waray] [filipino->english]")
    assert [h["hop"] for h in out["hops"]] == ["filipino->english", "english->waray"]
    # English source skips the dead hop (passthrough recorded, not silent).
    en = run(source_text="Coastal flooding expected tomorrow.", source_language="English",
             target_language="waray", translate=adapter)
    assert en["english_pivot_text"] == "Coastal flooding expected tomorrow."
    assert en["hops"][0]["method"].startswith("passthrough")
    # TTS mode hands off to the single-source TTS preprocessor.
    tts = run(source_text="Signal 3 expected.", source_language="english",
              target_language="waray", tts_mode=True, translate=adapter,
              tts_expansion_map={"3": "tulo"})
    assert tts["tts_ready_text"] is not None and "tulo" in tts["tts_ready_text"]
    # Model output is candidate prose, never truth.
    assert out["translation_is_model_output"] is True and out["serves_truth"] is False
    # Refusals: no adapter, empty hop output, bad args.
    for bad in (lambda: run(source_text="x", source_language="a", target_language="b"),
                lambda: run(source_text="x", source_language="a", target_language="b",
                            translate=lambda t, s, g: "  "),
                lambda: run(source_text=" ", source_language="a", target_language="b",
                            translate=adapter)):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    # Deterministic given the same scripted adapter.
    assert json.dumps(run(source_text="x", source_language="a", target_language="b",
                          translate=adapter), sort_keys=True) == \
           json.dumps(run(source_text="x", source_language="a", target_language="b",
                          translate=adapter), sort_keys=True)
    print("PASS — english_pivot_translation: two recorded hops through the English pivot, "
          "passthrough skips dead hops honestly, TTS handoff via the single-source "
          "preprocessor, translations never faked, serves_truth pinned False verified")


if __name__ == "__main__":
    _selftest()
