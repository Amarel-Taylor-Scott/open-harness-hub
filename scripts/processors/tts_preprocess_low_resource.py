#!/usr/bin/env python3
"""Backs `processor/tts-preprocess-low-resource` (process_kind ``format_convert.tts_preprocess``).

Prepare model-generated text for open-source TTS engines (MMS / Coqui /
eSpeak-NG) serving LOW-RESOURCE languages — the WeatherSpeak pattern:
disaster alerts read over radio in Waray/Ilocano/Kapampangan. Deterministic
transforms, every one logged: expand numbers/abbreviations via an INJECTED
expansion map (the language community owns its expansions — never hardcoded
here), strip TTS-hostile symbols, split into breath-length segments, apply
an injected phonetic map, and optionally wrap segments in minimal SSML.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs text, target_language, tts_engine, expansion_map, ssml_rate,
phonetic_map → preprocessed_text, segments, ssml_output,
transformations_applied.

CLI / self-test: python3 scripts/processors/tts_preprocess_low_resource.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

SUPPORTED_ENGINES = ("mms", "coqui", "espeak-ng")

#: Breath-length segment ceiling (chars) — long sentences make low-resource
#: TTS models drift; radio scripts read in short phrases.
MAX_SEGMENT_CHARS = 120

#: Symbols TTS engines mispronounce or choke on; replaced with spoken forms
#: only when the injected expansion map provides one, otherwise dropped.
TTS_HOSTILE_RE = re.compile(r"[#*_`~^|<>{}\[\]]")

#: Default SSML prosody rate (1.0 = neutral; alerts read slightly slow).
DEFAULT_SSML_RATE = 0.9

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_NUMBER_RE = re.compile(r"\b\d+\b")
_WORD_RE = re.compile(r"\b[\w']+\b")


def run(*, text: str, target_language: str, tts_engine: str = "mms",
        expansion_map: dict[str, str] | None = None, ssml_rate: float | None = None,
        phonetic_map: dict[str, str] | None = None) -> dict[str, Any]:
    """Transform ``text`` into TTS-ready segments for ``target_language``."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty str")
    if not isinstance(target_language, str) or not target_language:
        raise ValueError("target_language must be a non-empty language code/name")
    if tts_engine not in SUPPORTED_ENGINES:
        raise ValueError(f"tts_engine must be one of {SUPPORTED_ENGINES}, got {tts_engine!r}")
    expansion_map = expansion_map or {}
    phonetic_map = phonetic_map or {}
    applied: list[dict[str, Any]] = []
    out = text

    # 1. Expansions (numbers + abbreviations) via the injected map; numbers
    #    WITHOUT an expansion are kept verbatim and REPORTED — a number read
    #    wrong in an alert is dangerous, so the gap is surfaced, not guessed.
    unexpanded_numbers: list[str] = []
    def expand_token(m: re.Match) -> str:
        token = m.group(0)
        if token in expansion_map:
            applied.append({"transform": "expand", "from": token, "to": expansion_map[token]})
            return expansion_map[token]
        if _NUMBER_RE.fullmatch(token):
            unexpanded_numbers.append(token)
        return token
    out = _WORD_RE.sub(expand_token, out)

    # 2. Strip TTS-hostile symbols (logged once if anything changed).
    stripped = TTS_HOSTILE_RE.sub("", out)
    if stripped != out:
        applied.append({"transform": "strip_tts_hostile_symbols"})
        out = stripped

    # 3. Phonetic respelling via the injected map.
    for src in sorted(phonetic_map, key=len, reverse=True):
        if src in out:
            out = out.replace(src, phonetic_map[src])
            applied.append({"transform": "phonetic", "from": src, "to": phonetic_map[src]})

    # 4. Breath-length segmentation: sentences first, comma-split when over cap.
    segments: list[str] = []
    for sent in (s.strip() for s in _SENTENCE_SPLIT_RE.split(out) if s.strip()):
        if len(sent) <= MAX_SEGMENT_CHARS:
            segments.append(sent)
            continue
        piece = ""
        for clause in sent.split(","):
            clause = clause.strip()
            if piece and len(piece) + len(clause) + 2 > MAX_SEGMENT_CHARS:
                segments.append(piece + ",")
                piece = clause
            else:
                piece = f"{piece}, {clause}" if piece else clause
        if piece:
            segments.append(piece)
    applied.append({"transform": "segment", "count": len(segments),
                    "max_segment_chars": MAX_SEGMENT_CHARS})

    # 5. Optional minimal SSML (rate + per-segment <s> tags).
    ssml_output = None
    if ssml_rate is not None:
        if not 0.5 <= float(ssml_rate) <= 1.5:
            raise ValueError(f"ssml_rate must be 0.5..1.5, got {ssml_rate!r}")
        body = "".join(f"<s>{seg}</s>" for seg in segments)
        ssml_output = (f'<speak><prosody rate="{ssml_rate}">{body}</prosody></speak>')
        applied.append({"transform": "ssml", "rate": float(ssml_rate)})

    return {"preprocessed_text": " ".join(segments),
            "segments": segments,
            "ssml_output": ssml_output,
            "transformations_applied": applied,
            "unexpanded_numbers": sorted(set(unexpanded_numbers)),
            "target_language": target_language, "tts_engine": tts_engine}


def _selftest() -> None:
    expansion = {"3": "tulo", "km/h": "kilometro kada oras", "PAGASA": "PAG-ASA weather bureau",
                 "155": "usa ka gatos kalim-an ug lima}"[:-1]}
    text = ("PAGASA alert: Signal 3 *active*. Winds reach 155 km/h, "
            "evacuate coastal sitios now, move to high ground, bring water, "
            "radios, and documents. Stay calm.")
    out = run(text=text, target_language="waray", tts_engine="mms",
              expansion_map=expansion, ssml_rate=0.9,
              phonetic_map={"sitios": "sit-yos"})
    # Expansions applied and logged; the injected map owns the language.
    assert "tulo" in out["preprocessed_text"] and "PAG-ASA weather bureau" in out["preprocessed_text"]
    assert any(t.get("from") == "155" for t in out["transformations_applied"])
    # Hostile symbols stripped; phonetic respelling applied.
    assert "*" not in out["preprocessed_text"] and "sit-yos" in out["preprocessed_text"]
    # Breath-length segmentation: every segment under the cap (+1 for the comma).
    assert all(len(s) <= MAX_SEGMENT_CHARS + 1 for s in out["segments"])
    assert len(out["segments"]) >= 3
    # SSML wraps every segment at the requested rate.
    assert out["ssml_output"].startswith('<speak><prosody rate="0.9">')
    assert out["ssml_output"].count("<s>") == len(out["segments"])
    # Numbers without an expansion are surfaced, never guessed.
    no_map = run(text="Signal 4 expected.", target_language="waray", tts_engine="espeak-ng")
    assert no_map["unexpanded_numbers"] == ["4"] and no_map["ssml_output"] is None
    # Deterministic; on_error=raise.
    assert json.dumps(run(text=text, target_language="waray", expansion_map=expansion), sort_keys=True) == \
           json.dumps(run(text=text, target_language="waray", expansion_map=expansion), sort_keys=True)
    for bad in (lambda: run(text=" ", target_language="waray"),
                lambda: run(text="x", target_language="waray", tts_engine="festival"),
                lambda: run(text="x", target_language="waray", ssml_rate=3.0)):
        raised = False
        try:
            bad()
        except ValueError:
            raised = True
        assert raised
    print("PASS — tts_preprocess_low_resource: injected expansion/phonetic maps (language "
          "community owns the language), hostile-symbol strip, breath-length segments, "
          "minimal SSML, unexpanded numbers surfaced (never guessed), deterministic verified")


if __name__ == "__main__":
    _selftest()
