#!/usr/bin/env python3
"""Backs `processor/language-lock-respond-in-input-language` (process_kind ``format_convert.language_patch``).

Pre-pass: detect the user's input language and inject a language-lock
instruction into the system prompt BEFORE the model call — preventing the
classic mid-response drift into English. The detector is INJECTED (fastText/
lingua in production); without one, a deterministic stopword-profile
detector covers the bundled language profiles and HONESTLY reports itself
(``detector`` field). Below the confidence threshold the lock is NOT applied
and the fallback language is named — an uncertain lock is worse than none.

Contract: deterministic (built-in detector); side_effects=none; on_error=raise.
Inputs user_text, system_prompt, detection_confidence_threshold,
fallback_language → detected_language, detection_confidence,
patched_system_prompt, lock_applied.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/language_lock_respond_in_input_language.py
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Built-in stopword profiles (deterministic detector lane). Small by design —
#: production injects a real LID model; these cover the demo languages.
LANGUAGE_PROFILES: dict[str, frozenset[str]] = {
    "english": frozenset({"the", "and", "is", "of", "to", "in", "for", "with", "that", "this"}),
    "tagalog": frozenset({"ang", "ng", "sa", "mga", "ay", "na", "po", "ito", "para", "ko"}),
    "spanish": frozenset({"el", "la", "de", "que", "y", "en", "los", "del", "se", "por"}),
    "german": frozenset({"der", "die", "und", "das", "ist", "nicht", "mit", "ein", "für", "auf"}),
}

#: Default minimum confidence before the lock applies.
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_FALLBACK_LANGUAGE = "english"

#: The lock instruction template (single definition; tests read it).
LOCK_TEMPLATE = ("Respond ONLY in {language}. Do not switch to any other language "
                 "mid-response, even for technical terms when a {language} term exists.")

DETECTOR_BUILTIN = "stopword-profile (deterministic, bundled profiles only)"
DETECTOR_INJECTED = "injected-lid-model"

_TOKEN_RE = re.compile(r"[a-zà-ÿäöüß'-]+")
CONFIDENCE_DECIMALS = 4


def _builtin_detect(text: str) -> tuple[str, float]:
    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return "", 0.0
    scores = {lang: sum(1 for t in tokens if t in prof) / len(tokens)
              for lang, prof in LANGUAGE_PROFILES.items()}
    best = max(sorted(scores), key=lambda l: scores[l])
    total = sum(scores.values())
    confidence = (scores[best] / total) if total > 0 else 0.0
    return best, round(confidence, CONFIDENCE_DECIMALS)


def run(*, user_text: str, system_prompt: str,
        detection_confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        fallback_language: str = DEFAULT_FALLBACK_LANGUAGE,
        detector: Callable[[str], tuple[str, float]] | None = None) -> dict[str, Any]:
    """Detect the input language and patch the system prompt with the lock."""
    if not isinstance(user_text, str) or not user_text.strip():
        raise ValueError("user_text must be a non-empty str")
    if not isinstance(system_prompt, str):
        raise TypeError("system_prompt must be str")
    if not 0.0 <= float(detection_confidence_threshold) <= 1.0:
        raise ValueError("detection_confidence_threshold must be in [0, 1]")
    detect = detector if detector is not None else _builtin_detect
    language, confidence = detect(user_text)
    lock_applied = bool(language) and confidence >= float(detection_confidence_threshold)
    target = language if lock_applied else fallback_language
    if lock_applied:
        patched = system_prompt.rstrip() + "\n\n" + LOCK_TEMPLATE.format(language=target)
    else:
        patched = system_prompt  # uncertain → unpatched, fallback NAMED in the envelope
    return {"detected_language": language or None,
            "detection_confidence": round(float(confidence), CONFIDENCE_DECIMALS),
            "patched_system_prompt": patched,
            "lock_applied": lock_applied,
            "fallback_language": None if lock_applied else fallback_language,
            "detector": DETECTOR_INJECTED if detector is not None else DETECTOR_BUILTIN}


def _selftest() -> None:
    sysp = "You are a disaster-alert assistant."
    # Tagalog input → tagalog lock injected, builtin detector honestly labeled.
    tl = run(user_text="Ano po ang gagawin namin sa mga baha sa amin?", system_prompt=sysp)
    assert tl["detected_language"] == "tagalog" and tl["lock_applied"] is True
    assert LOCK_TEMPLATE.format(language="tagalog") in tl["patched_system_prompt"]
    assert tl["patched_system_prompt"].startswith(sysp)
    assert tl["detector"] == DETECTOR_BUILTIN
    # English input locks to english.
    en = run(user_text="What is the evacuation route for the coastal area?", system_prompt=sysp)
    assert en["detected_language"] == "english" and en["lock_applied"] is True
    # Ambiguous text under the threshold → NO lock, fallback named, prompt untouched.
    amb = run(user_text="zzz qqq 12345 xkcd", system_prompt=sysp)
    assert amb["lock_applied"] is False and amb["patched_system_prompt"] == sysp
    assert amb["fallback_language"] == DEFAULT_FALLBACK_LANGUAGE
    # Injected detector wins authority and flips the label.
    inj = run(user_text="anything", system_prompt=sysp,
              detector=lambda t: ("waray", 0.99))
    assert inj["detected_language"] == "waray" and inj["lock_applied"] is True
    assert inj["detector"] == DETECTOR_INJECTED
    assert "Respond ONLY in waray." in inj["patched_system_prompt"]
    # Threshold respected against the injected confidence.
    weak = run(user_text="anything", system_prompt=sysp,
               detector=lambda t: ("waray", 0.3), detection_confidence_threshold=0.5)
    assert weak["lock_applied"] is False
    # Deterministic; on_error=raise.
    assert json.dumps(run(user_text="Ano po ito?", system_prompt=sysp), sort_keys=True) == \
           json.dumps(run(user_text="Ano po ito?", system_prompt=sysp), sort_keys=True)
    for bad in (lambda: run(user_text=" ", system_prompt=sysp),
                lambda: run(user_text="x", system_prompt=sysp, detection_confidence_threshold=2.0)):
        raised = False
        try:
            bad()
        except ValueError:
            raised = True
        assert raised
    print("PASS — language_lock_respond_in_input_language: stopword-profile builtin "
          "(honestly labeled) or injected LID, lock injected only above threshold "
          "(uncertain → unpatched + named fallback), deterministic verified")


if __name__ == "__main__":
    _selftest()
