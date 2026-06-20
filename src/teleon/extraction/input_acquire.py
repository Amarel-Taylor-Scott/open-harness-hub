"""src.teleon.extraction.input_acquire — generalize the document cascade's ACQUIRE stage across input types.

The cheapest-that-meets extraction cascade (document_extraction_cascade) works on normalized text/structure. This
turns ANY input type — PDF, Office doc, plain text, email + attachments, web page, RSS feed, social post, image,
audio note — into that normalized form via a cheapest-first acquire ladder (deterministic where possible, model
only when the input forces it), then feeds the SAME extraction cascade. Web/social acquire uses LEGITIMATE paths
only (HTML→clean-text of fetched/owner-provided content; social via the governed legitimate-feed intake — never
ToS-violating scraping). serves_truth False; live network acquire is owner-gated. Teleon-layer; never imports baltor.
"""
from __future__ import annotations

from src.teleon.extraction.document_extraction_cascade import extract

#: per input type, the acquire ladder cheapest-first: (method, cost, deterministic, requires_keys, needs).
ACQUIRE_LADDER: dict[str, list[tuple]] = {
    "pdf": [("text_layer_extract", 0.002, True, (), ("text_layer",)), ("ocr", 0.020, True, (), ("scanned",)),
            ("vision_llm", 0.300, False, ("LLM_API_KEY",), ("any",))],
    "office_doc": [("office_parse", 0.002, True, (), ("any",))],       # docx/xlsx/pptx native parse
    "text": [("passthrough", 0.0, True, (), ("any",))],
    "email": [("mime_parse", 0.002, True, (), ("any",))],              # headers+body; attachments recurse by type
    "web_page": [("html_to_clean_text", 0.003, True, (), ("html",)), ("readability", 0.004, True, (), ("html",)),
                 ("vision_llm", 0.300, False, ("LLM_API_KEY",), ("js_heavy",))],
    "rss_feed": [("feed_parse", 0.002, True, (), ("any",))],           # per-item structured
    "social_post": [("legitimate_feed_intake", 0.005, True, (), ("legitimate_api",))],  # governed; refuses scraping
    "image": [("ocr", 0.020, True, (), ("any",)), ("vision_llm", 0.300, False, ("LLM_API_KEY",), ("any",))],
    "audio_note": [("asr", 0.030, False, ("LLM_API_KEY",), ("any",))],
}


def supported_input_types() -> list[str]:
    return sorted(ACQUIRE_LADDER)


def _supports(needs: tuple, source: dict, have: set) -> bool:
    if "any" in needs:
        return True
    return any((n == "text_layer" and source.get("has_text_layer")) or (n == "scanned" and source.get("scanned"))
               or (n == "html" and source.get("is_html", True)) or (n == "js_heavy" and source.get("js_heavy"))
               or (n == "legitimate_api" and source.get("has_legitimate_api")) for n in needs)


def acquire(input_type: str, source: dict | None = None, *, available_keys: tuple = ()) -> dict:
    """Pick the cheapest acquire method this input supports → normalized text/structure for the extraction cascade.
    Deterministic methods are preferred (they sort first by cost); a model method needs its key."""
    source = source or {}
    have = {k.upper() for k in available_keys}
    ladder = ACQUIRE_LADDER.get(input_type)
    if not ladder:
        return {"input_type": input_type, "acquired": False, "reason": "unsupported input type", "serves_truth": False}
    for method, cost, det, keys, needs in ladder:
        if keys and not set(k.upper() for k in keys) <= have:
            continue
        if _supports(needs, source, have):
            return {"input_type": input_type, "method": method, "cost": cost, "deterministic": det,
                    "acquired": True, "serves_truth": False}
    return {"input_type": input_type, "acquired": False,
            "reason": "no available acquire method supports this source (provide a key or a legitimate path)",
            "serves_truth": False}


def extract_from(input_type: str, source: dict, required_fields: dict, *, available_keys: tuple = ()) -> dict:
    """Acquire the input (any type) → run the cheapest-that-meets extraction cascade on it. One combined receipt."""
    acq = acquire(input_type, source, available_keys=available_keys)
    if not acq["acquired"]:
        return {"input_type": input_type, "acquired": False, "reason": acq.get("reason"),
                "met_requirement": False, "total_cost": 0.0, "serves_truth": False}
    ex = extract(required_fields, source, available_keys=available_keys)
    return {
        "input_type": input_type, "acquire": acq, "extract": ex,
        "total_cost": round(acq["cost"] + ex["total_cost"], 4),
        "met_requirement": ex["met_requirement"], "missing": ex["missing"],
        "deterministic_only": acq["deterministic"] and not ex["used_llm"],
        "path": [acq["method"]] + ex["path"], "serves_truth": False,
    }
