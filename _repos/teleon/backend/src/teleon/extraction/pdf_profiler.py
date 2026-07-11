"""src.teleon.extraction.pdf_profiler — profile a PDF cheaply, classify its layout, SHORTCUT to the right extraction path.

Owner's optimization: before running the document-extraction cascade, do a cheap DETERMINISTIC profile (PDF metadata +
characteristics: text layer? scanned images? AcroForm? tables? encrypted?), CLASSIFY the layout, and shortcut to only the
rungs that apply — skipping the expensive ones (e.g. a born-digital text PDF needs no OCR). This is the cheapest rung-0 of
the document_extraction ladder: it REDUCES the ladder before any model runs. classify_layout()/route() are pure
(testable on a signal dict); profile_pdf() is the reader adapter (honest 'pypdf unavailable' rather than fabricating).
serves_truth=false; Teleon layer.
"""
from __future__ import annotations

#: layout class -> the document_extraction ladder rungs to run (in order); everything else is SKIPPED (the shortcut).
_ROUTES = {
    "born_digital_text": ["text_layer", "field_parse"],            # skip ocr + tables (no scan, no grid)
    "scanned_image": ["ocr", "field_parse"],                       # skip text_layer (there is none)
    "form": ["text_layer", "field_parse"],                         # AcroForm fields are text
    "tabular": ["text_layer", "tables", "field_parse"],            # has a real text layer + grids
    "mixed": ["text_layer", "tables", "ocr", "field_parse"],       # unsure -> the fuller cascade
    "encrypted": ["decrypt"],                                      # needs a password/credential first (honest-blocked)
    "empty": [],                                                   # nothing to extract
}
_ALL_RUNGS = ["text_layer", "tables", "ocr", "field_parse"]        # the deterministic rungs a profile can skip


def classify_layout(profile: dict) -> str:
    """Deterministic layout class from cheap signals (most-decisive-first). profile keys: encrypted, page_count,
    has_acroform, has_text_layer, has_images, table_hint, text_density."""
    if profile.get("encrypted"):
        return "encrypted"
    if profile.get("page_count", 1) == 0:
        return "empty"
    if profile.get("has_acroform"):
        return "form"
    text = profile.get("has_text_layer") or (profile.get("text_density", 0) or 0) > 0.05
    if not text and profile.get("has_images"):
        return "scanned_image"
    if text and profile.get("table_hint"):
        return "tabular"
    if text:
        return "born_digital_text"
    return "mixed"


def route(layout: str) -> list[str]:
    """The extraction rungs to run for a layout class (the rest of the ladder is shortcut away)."""
    return list(_ROUTES.get(layout, _ROUTES["mixed"]))


def shortcut_plan(profile: dict) -> dict:
    """Profile -> layout -> the shortcut plan: which rungs to run, which are SKIPPED, and an honest blocker if any.
    A CANDIDATE prediction (serves_truth=false) — the cascade still verifies; a wrong guess just escalates to 'mixed'."""
    layout = classify_layout(profile)
    run = route(layout)
    skipped = [r for r in _ALL_RUNGS if r not in run]
    blocked = None
    if layout == "encrypted":
        blocked = "encrypted: needs a password/credential before extraction (honest-blocked, not fabricated)"
    if layout == "empty":
        blocked = "no extractable content detected"
    return {"layout": layout, "run": run, "skipped": skipped, "blocked": blocked, "serves_truth": False}


def profile_pdf(path) -> dict:
    """Reader ADAPTER: cheap deterministic signals via pypdf. Honest: if pypdf is absent/unreadable, returns
    {available: False, reason} so the caller passes a signal dict or falls back to the full cascade — never fabricates."""
    try:
        from pypdf import PdfReader  # BYO/optional dep
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": f"pypdf unavailable: {type(e).__name__}"}
    try:
        r = PdfReader(str(path))
        if r.is_encrypted:
            return {"available": True, "encrypted": True, "page_count": len(r.pages)}
        pages = r.pages
        sample = " ".join((p.extract_text() or "") for p in pages[:3])
        density = min(1.0, len(sample) / 3000.0)
        return {"available": True, "encrypted": False, "page_count": len(pages),
                "has_acroform": bool(getattr(r, "get_fields", lambda: None)()),
                "has_text_layer": density > 0.05, "text_density": round(density, 3),
                "has_images": any("/Image" in str(p.get("/Resources", {})) for p in pages[:3]),
                "table_hint": ("  " in sample and "\n" in sample), "producer": (r.metadata or {}).get("/Producer", "")}
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": f"unreadable: {type(e).__name__}"}
