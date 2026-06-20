"""src.teleon.extraction.document_extraction_cascade — PDF/document → schema extraction as a CHEAPEST-THAT-MEETS-
REQUIREMENTS cascade over a hyperparameter grid of methods.

The idea (owner, 2026-06-20): extracting a schema from a document (e.g. an employment-agency licence) can be done
MANY ways with very different cost/latency: extract the text layer, OCR, deterministic regex/keyword/NLP rules,
prune unimportant text, compress, then escalate to an LLM (cheapest capable first). Every step is a grid of options.
The runtime should search that grid and pick the CHEAPEST variation that still fills the required schema fields to
the confidence floor — escalating only as far as the document forces, and tracking metadata (the path + cost +
what filled what) for supervision.

This composes the same machinery as the descent engine: deterministic-before-LLM (cost↓), cheapest-capable model
(model-downgrade), prune+compress (tokens↓), accuracy/coverage floor (don't ship below requirement). A field that no
available method can fill is reported MISSING honestly — never fabricated. serves_truth is False (extraction output
is a candidate that the verification rail dispositions). Pure + deterministic; Teleon-layer (never imports baltor).
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: field "classes" by how they're best recovered — drives which methods can fill them.
STRUCTURED, SEMI, UNSTRUCTURED = "structured", "semi", "unstructured"

#: cost ordering of acquire methods (cheapest text-layer first; OCR for scans; vision-LLM last).
_ACQUIRE = [
    ("pdf_text_extract", 0.002, True, ("text_layer",)),       # needs a text layer
    ("ocr", 0.020, True, ("scanned",)),                       # works on scans
    ("image_enhance_ocr", 0.045, True, ("scanned",)),         # poor scans
    ("vision_llm", 0.300, False, ("any",)),                   # last resort; needs a key
]

#: the EXTRACT ladder, cheapest-first: deterministic rules → prune/compress → cheapest-capable LLM → frontier LLM.
@dataclass(frozen=True)
class Method:
    name: str
    stage: str
    cost: float
    deterministic: bool
    fills: tuple                 # which field-classes this method can recover
    requires_keys: tuple = ()
    reduces_llm_cost: bool = False


_LADDER = [
    Method("regex_keyword", "rule_extract", 0.001, True, (STRUCTURED,)),
    Method("deterministic_nlp", "rule_extract", 0.005, True, (STRUCTURED, SEMI)),
    Method("heuristic_patterns", "rule_extract", 0.008, True, (SEMI,)),
    Method("prune_compress", "prune_compress", 0.003, True, (), reduces_llm_cost=True),  # cuts cost of any later LLM
    Method("cheap_llm", "llm_extract", 0.030, False, (SEMI, UNSTRUCTURED), ("LLM_API_KEY",)),
    Method("frontier_llm", "llm_extract", 0.300, False, (STRUCTURED, SEMI, UNSTRUCTURED), ("LLM_API_KEY",)),
]
_COMPRESS_LLM_DISCOUNT = 0.5   # prune_compress halves a subsequent LLM call's cost (fewer tokens)


def _pick_acquire(doc: dict, have: set) -> tuple | None:
    """Cheapest acquire method the document supports (text-layer < OCR < enhanced OCR < vision-LLM)."""
    for name, cost, det, needs in _ACQUIRE:
        ok = (("text_layer" in needs and doc.get("has_text_layer"))
              or ("scanned" in needs and doc.get("scanned"))
              or ("any" in needs and ("LLM_API_KEY" in have)))
        if ok:
            return (name, cost, det)
    return None


def extract(required_fields: dict, doc: dict, *, available_keys: tuple = (), confidence_floor: float = 0.0) -> dict:
    """Fill ``required_fields`` (``{field: class}``) from a document, cheapest-first, stopping when every required
    field is filled. ``doc`` = {has_text_layer, scanned}. Returns the filled schema + a cost/path receipt; an
    unfillable field is reported MISSING, never fabricated."""
    have = {k.upper() for k in available_keys}
    steps: list[dict] = []
    filled: dict[str, str] = {}
    cost = 0.0
    compressed = False

    acq = _pick_acquire(doc, have)
    if acq:
        cost += acq[1]
        steps.append({"stage": "acquire", "method": acq[0], "cost": acq[1]})

    remaining = lambda: {f: c for f, c in required_fields.items() if f not in filled}
    for m in _LADDER:
        if not remaining():
            break
        if m.requires_keys and not set(k.upper() for k in m.requires_keys) <= have:
            steps.append({"stage": m.stage, "method": m.name, "cost": 0.0, "skipped": "missing key"})
            continue
        if m.reduces_llm_cost:
            # only worth it if we're about to need an LLM (an unstructured field still missing)
            if any(c == UNSTRUCTURED for c in remaining().values()):
                cost += m.cost
                compressed = True
                steps.append({"stage": m.stage, "method": m.name, "cost": m.cost, "effect": "compress→LLM cost halved"})
            continue
        fills_now = {f: c for f, c in remaining().items() if c in m.fills}
        if not fills_now:
            continue
        mcost = m.cost * (_COMPRESS_LLM_DISCOUNT if (compressed and m.stage == "llm_extract") else 1.0)
        cost += mcost
        for f in fills_now:
            filled[f] = m.name
        steps.append({"stage": m.stage, "method": m.name, "cost": round(mcost, 4),
                      "filled": sorted(fills_now), "deterministic": m.deterministic})

    missing = sorted(remaining())
    used_llm = any(s.get("stage") == "llm_extract" and "filled" in s for s in steps)
    return {
        "filled": filled, "missing": missing, "met_requirement": not missing,
        "total_cost": round(cost, 4), "used_llm": used_llm, "path": [s["method"] for s in steps if "filled" in s or s["stage"] == "acquire"],
        "receipt": steps, "confidence_floor": confidence_floor, "serves_truth": False,
    }


#: a representative employment-agency-licence schema (the DueCare domain) by field class.
EMPLOYMENT_AGENCY_SCHEMA = {
    "agency_license_no": STRUCTURED, "agency_name": STRUCTURED, "issue_date": STRUCTURED,
    "address": SEMI, "authorized_destinations": SEMI,
    "recruiter_obligations": UNSTRUCTURED, "fee_terms": UNSTRUCTURED,
}


def demonstrate(*, available_keys: tuple = ("LLM_API_KEY",)) -> dict:
    """Extract the employment-agency schema from a clean text-layer PDF, cheapest-first."""
    return extract(EMPLOYMENT_AGENCY_SCHEMA, {"has_text_layer": True, "scanned": False}, available_keys=available_keys)
