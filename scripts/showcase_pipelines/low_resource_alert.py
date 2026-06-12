#!/usr/bin/env python3
"""Showcase: low-resource-language DISASTER-ALERT pipeline, composing the edge/i18n family.

Scenario (WeatherSpeak pattern): a government weather bulletin must become a radio
script in a low-resource language (Waray) for broadcast. A bare model mistranslates
life-safety instructions and drifts to a high-resource neighbor. The pipeline grounds
on the governed bulletin, routes through English as a pivot, locks the output language,
and prepares TTS — then ESCALATES to a human who signs off before broadcast (nothing
auto-published; serves_truth=False).

Composition (every step a real `scripts/processors` callable):
  1. faithful_extract_before_model — pull machine-readable fields BEFORE the model
  2. english_pivot_translation      — source → English → target (two recorded hops)
  3. language_lock_respond_in_input_language — lock the output to the target language
  4. tts_preprocess_low_resource    — number/abbrev expansion, breath segments, SSML
  5. escalate_human                 — human signs off before broadcast (governed)

Run:  python3 scripts/showcase_pipelines/low_resource_alert.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.faithful_extract_before_model import run as extract_run
from scripts.processors.english_pivot_translation import run as pivot_run
from scripts.processors.language_lock_respond_in_input_language import run as lock_run
from scripts.processors.tts_preprocess_low_resource import run as tts_run
from scripts.processors.deliver.escalate_human import run as escalate_run

_FIELD_MAP = {
    "signal_level": r"Signal No\.\s*(\d+)",
    "typhoon_name": r"Typhoon:\s*([A-Z]+)",
    "max_winds_kmh": r"Max winds:\s*(\d+)\s*km/h",
}
_TTS_EXPANSION = {"3": "tulo", "km/h": "kilometro kada oras", "155": "usa ka gatos kalim-an ug lima"}


def run(*, bulletin: str, source_language: str, target_language: str,
        translate, broadcast_queue) -> dict[str, Any]:
    """Turn a governed bulletin into a target-language TTS-ready radio script, then
    ESCALATE for human sign-off. ``translate`` and ``broadcast_queue`` are injected
    (no model/transport is faked)."""
    # 1. faithful extraction (deterministic fields the model must not re-read/guess).
    extracted = extract_run(raw_text=bulletin, input_type="weather_bulletin",
                            field_map=_FIELD_MAP,
                            system_prompt_prefix="You write disaster-alert radio scripts.")
    # 2. english-pivot translation of the bulletin body (two recorded hops).
    pivoted = pivot_run(source_text=bulletin, source_language=source_language,
                        target_language=target_language, translate=translate)
    target_text = pivoted["target_language_text"]
    # 3. language lock (output must stay in the target language).
    locked = lock_run(user_text=bulletin, system_prompt="Write the alert.",
                      detector=lambda t: (target_language, 0.99))
    # 4. TTS preprocessing of the translated script.
    tts = tts_run(text=target_text, target_language=target_language, tts_engine="mms",
                  expansion_map=_TTS_EXPANSION, ssml_rate=0.9)
    # 5. escalate for human sign-off BEFORE broadcast (nothing auto-published).
    ticket = escalate_run(result={"script": tts["preprocessed_text"],
                                  "extracted_fields": extracted["extracted_fields"],
                                  "pivot_hops": pivoted["hops"]},
                          reason="policy_review", enqueue=broadcast_queue)["ticket"]
    return {"extracted_fields": extracted["extracted_fields"],
            "unextracted_fields": extracted["unextracted_fields"],
            "pivot_hops": [h["hop"] for h in pivoted["hops"]],
            "language_locked": locked["lock_applied"],
            "tts_segments": tts["segments"],
            "ssml": tts["ssml_output"],
            "awaiting_human_signoff": ticket["queue_ref"],
            "auto_broadcast": False, "serves_truth": False}


_BULLETIN = ("PAGASA WEATHER BULLETIN #14\nTyphoon: AMANG\nSignal No. 3 over Eastern Samar\n"
             "Max winds: 155 km/h near the center. Evacuate coastal sitios now and move to "
             "high ground. Bring water, radios, and documents. Stay calm.")


def _self_test() -> int:
    queue: list[dict] = []
    # Scripted injected translator (tagged hops) + broadcast queue.
    def translate(text, src, tgt):
        return f"[{src}->{tgt}] {text}"
    def enqueue(ticket):
        queue.append(ticket)
        return {"ref": f"bcast-{len(queue):04d}"}

    out = run(bulletin=_BULLETIN, source_language="filipino", target_language="waray",
              translate=translate, broadcast_queue=enqueue)
    # Faithful extraction pulled the structured fields.
    assert out["extracted_fields"]["signal_level"]["value"] == "3"
    assert out["extracted_fields"]["typhoon_name"]["value"] == "AMANG"
    # The pivot went through English (two recorded hops).
    assert out["pivot_hops"] == ["filipino->english", "english->waray"]
    # Output language was locked to the target, TTS produced breath-length segments,
    # and the number expansion fired.
    assert out["language_locked"] is True and len(out["tts_segments"]) >= 1
    assert "tulo" in " ".join(out["tts_segments"])
    # NOTHING auto-broadcasts — a human must sign off first.
    assert out["auto_broadcast"] is False and out["awaiting_human_signoff"]
    assert out["serves_truth"] is False
    assert len(queue) == 1
    # Deterministic.
    q2: list[dict] = []
    again = run(bulletin=_BULLETIN, source_language="filipino", target_language="waray",
                translate=translate, broadcast_queue=lambda t: (q2.append(t), {"ref": f"bcast-{len(q2):04d}"})[1])
    assert again["tts_segments"] == out["tts_segments"] and again["pivot_hops"] == out["pivot_hops"]
    print("PASS — low_resource_alert: faithful-extract → english-pivot (2 hops) → "
          "language-lock → TTS-preprocess → human sign-off; nothing auto-broadcasts, "
          "serves_truth=False, deterministic")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Low-resource disaster-alert showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    out = run(bulletin=_BULLETIN, source_language="filipino", target_language="waray",
              translate=lambda t, s, g: f"[{s}->{g}] {t}", broadcast_queue=lambda t: {"ref": "bcast-0001"})
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
