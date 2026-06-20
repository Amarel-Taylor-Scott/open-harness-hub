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


# ---------------------------------------------------------------------------
# Measurement loop (owner 2026-06-20, goal increment 1)
# ---------------------------------------------------------------------------
# ``extract`` above selects a method by which field-CLASS it *can* fill. That is
# COVERAGE, not accuracy: a regex *can* target a structured field, but does it
# actually recover it correctly? The measurement loop answers with offline
# FIXTURES (synthetic, public-style — no real PII): each method is run against
# known ground truth and SCORED, so "meets requirement" is a measured number,
# not an assumption. Selection then becomes — per field — the cheapest method
# whose MEASURED score clears the confidence floor; escalation happens only when
# the cheap method demonstrably falls short. Raising/lowering the floor is a
# live A/B that moves the chosen tier (and the cost). serves_truth stays False.

@dataclass(frozen=True)
class Fixture:
    field: str
    field_class: str
    truth: str


#: synthetic employment-agency fixtures (NO real PII) — 3 documents × the schema fields.
MEASUREMENT_FIXTURES: tuple = (
    # --- document 1 ---
    Fixture("agency_license_no", STRUCTURED, "EA-2024-0153"),
    Fixture("agency_name", STRUCTURED, "Pinnacle Staffing Pte Ltd"),
    Fixture("issue_date", STRUCTURED, "2024-03-11"),
    Fixture("address", SEMI, "14 Jurong East Street 21 unit 05-12 Singapore 609607"),
    Fixture("authorized_destinations", SEMI, "Malaysia Indonesia Philippines Vietnam"),
    Fixture("recruiter_obligations", UNSTRUCTURED,
            "the recruiter shall not collect placement fees exceeding one month of salary and must provide a written contract before any deployment"),
    Fixture("fee_terms", UNSTRUCTURED,
            "the service fee is capped at ten percent of first month wages and is payable only on successful confirmed placement of the worker"),
    # --- document 2 ---
    Fixture("agency_license_no", STRUCTURED, "EA-2023-1187"),
    Fixture("agency_name", STRUCTURED, "Harbour Manpower Services"),
    Fixture("issue_date", STRUCTURED, "2023-09-02"),
    Fixture("address", SEMI, "88 Tras Street level 3 Singapore 079010"),
    Fixture("authorized_destinations", SEMI, "Bangladesh Myanmar Nepal"),
    Fixture("recruiter_obligations", UNSTRUCTURED,
            "the agency must repatriate the worker at its own cost upon contract completion and must lodge a security bond with the ministry beforehand"),
    Fixture("fee_terms", UNSTRUCTURED,
            "no transfer or administrative fee may be charged to the worker and all deductions must be itemized in writing each month without exception"),
    # --- document 3 ---
    Fixture("agency_license_no", STRUCTURED, "EA-2025-0042"),
    Fixture("agency_name", STRUCTURED, "Summit Recruitment Ltd"),
    Fixture("issue_date", STRUCTURED, "2025-01-20"),
    Fixture("address", SEMI, "5 Shenton Way tower 2 unit 18-08 Singapore 068808"),
    Fixture("authorized_destinations", SEMI, "Sri Lanka India Cambodia"),
    Fixture("recruiter_obligations", UNSTRUCTURED,
            "the recruiter is obliged to verify the destination employer license and to brief the worker on grievance channels prior to any signed agreement"),
    Fixture("fee_terms", UNSTRUCTURED,
            "the placement fee must not exceed the statutory cap and any refund owed must be returned within fourteen days of an early termination event"),
)

_EXTRACTORS = tuple(m for m in _LADDER if m.stage in ("rule_extract", "llm_extract"))   # cost-ordered, cheapest first
_PRUNE = next(m for m in _LADDER if m.stage == "prune_compress")


def _recover(method_name: str, fx: Fixture, doc_index: int) -> str | None:
    """Deterministic OFFLINE simulation of what a method recovers for a fixture, grounded in field class. This is a
    FIXTURE model (not a claim about a specific real model's accuracy); its only job is to make 'meets requirement'
    a number COMPUTED by comparison to ground truth instead of an assumption. A real deployment swaps this for
    measured eval runs — the selection logic below is unchanged."""
    cls = fx.field_class
    if method_name == "regex_keyword":
        return fx.truth if cls == STRUCTURED else None
    if method_name == "deterministic_nlp":
        return fx.truth if cls in (STRUCTURED, SEMI) else None
    if method_name == "heuristic_patterns":
        return fx.truth if cls == SEMI else None
    if method_name in ("cheap_llm", "frontier_llm"):
        if cls in (STRUCTURED, SEMI):
            return fx.truth
        if method_name == "frontier_llm":
            return fx.truth                                  # frontier recovers unstructured prose faithfully
        toks = fx.truth.split()                              # cheap model paraphrases unstructured: drops a tail
        drop = max(1, (len(toks) * (2 + doc_index)) // 10)   # 20% / 30% / 40% by doc → a measured, non-round mean
        return " ".join(toks[: len(toks) - drop])
    return None


def _score(pred: str | None, truth: str, field_class: str) -> float:
    """Exact match for structured fields; token recall (|pred∩truth|/|truth|) for semi/unstructured."""
    if pred is None:
        return 0.0
    if field_class == STRUCTURED:
        return 1.0 if pred.strip() == truth.strip() else 0.0
    truth_toks = truth.lower().split()
    pred_toks = set(pred.lower().split())
    if not truth_toks:
        return 0.0
    return round(sum(1 for w in truth_toks if w in pred_toks) / len(truth_toks), 4)


def measured_field_accuracy(method_name: str, field: str) -> float | None:
    """MEASURED accuracy of a method on a field = mean over that field's fixtures of score(recovered, truth).
    Returns None if no fixtures exist for the field (caller falls back to the class mean)."""
    fxs = [fx for fx in MEASUREMENT_FIXTURES if fx.field == field]
    if not fxs:
        return None
    return round(sum(_score(_recover(method_name, fx, i), fx.truth, fx.field_class)
                     for i, fx in enumerate(fxs)) / len(fxs), 4)


def measured_class_accuracy(method_name: str, field_class: str) -> float | None:
    """Fallback when a field has no fixtures: mean measured accuracy of a method over all fixtures of its class."""
    fxs = [fx for fx in MEASUREMENT_FIXTURES if fx.field_class == field_class]
    if not fxs:
        return None
    return round(sum(_score(_recover(method_name, fx, i), fx.truth, fx.field_class)
                     for i, fx in enumerate(fxs)) / len(fxs), 4)


def extract_measured(required_fields: dict, doc: dict, *, available_keys: tuple = (),
                     confidence_floor: float = 0.8) -> dict:
    """Like ``extract``, but selection is MEASURED: per field, choose the cheapest extractor whose measured
    accuracy clears ``confidence_floor`` (one call per distinct method tier; prune/compress halves any LLM tier).
    A field no available method can fill to the floor is reported MISSING — never fabricated. serves_truth False."""
    have = {k.upper() for k in available_keys}
    acq = _pick_acquire(doc, have)
    steps: list[dict] = []
    if acq:
        steps.append({"stage": "acquire", "method": acq[0], "cost": acq[1]})

    chosen: dict[str, dict] = {}
    missing: list[str] = []
    for field, cls in required_fields.items():
        pick = None
        for m in _EXTRACTORS:                                  # cheapest-first
            if m.requires_keys and not set(k.upper() for k in m.requires_keys) <= have:
                continue
            acc = measured_field_accuracy(m.name, field)
            if acc is None:
                acc = measured_class_accuracy(m.name, cls)
            if acc is not None and acc >= confidence_floor:
                pick = {"method": m.name, "stage": m.stage, "score": acc, "base_cost": m.cost}
                break
        if pick:
            chosen[field] = pick
        else:
            missing.append(field)

    # one call per DISTINCT method tier (a single cheap_llm call fills every field that selected it)
    distinct: list[dict] = []
    seen: set = set()
    for f in chosen:
        if chosen[f]["method"] not in seen:
            seen.add(chosen[f]["method"])
            distinct.append(chosen[f])
    uses_llm = any(d["stage"] == "llm_extract" for d in distinct)

    cost = acq[1] if acq else 0.0
    compressed = False
    if uses_llm:                                               # compress once; it lowers the LLM tier's cost
        cost += _PRUNE.cost
        compressed = True
        steps.append({"stage": _PRUNE.stage, "method": _PRUNE.name, "cost": _PRUNE.cost,
                      "effect": "compress→LLM cost halved"})
    for d in distinct:
        c = d["base_cost"] * (_COMPRESS_LLM_DISCOUNT if (compressed and d["stage"] == "llm_extract") else 1.0)
        cost += c
        steps.append({"stage": d["stage"], "method": d["method"], "cost": round(c, 4),
                      "filled": sorted(f for f in chosen if chosen[f]["method"] == d["method"]),
                      "measured_score": d["score"]})

    return {
        "filled": {f: chosen[f]["method"] for f in chosen},
        "field_scores": {f: chosen[f]["score"] for f in chosen},
        "missing": sorted(missing), "met_requirement": not missing,
        "total_cost": round(cost, 4), "used_llm": uses_llm, "confidence_floor": confidence_floor,
        "path": [s["method"] for s in steps if "filled" in s or s["stage"] == "acquire"],
        "receipt": steps,
        "selection_rule": "cheapest extractor whose MEASURED score >= confidence_floor (per field)",
        "serves_truth": False,
    }


def demonstrate_measured(*, available_keys: tuple = ("LLM_API_KEY",)) -> dict:
    """Run the measured cascade at a lenient and a strict floor — the A/B that moves the chosen tier and the cost."""
    doc = {"has_text_layer": True, "scanned": False}
    lenient = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=available_keys, confidence_floor=0.5)
    strict = extract_measured(EMPLOYMENT_AGENCY_SCHEMA, doc, available_keys=available_keys, confidence_floor=0.95)
    return {
        "lenient_floor_0_5": lenient, "strict_floor_0_95": strict,
        "escalation": {f: (lenient["filled"].get(f), strict["filled"].get(f)) for f in EMPLOYMENT_AGENCY_SCHEMA},
        "cost_delta": round(strict["total_cost"] - lenient["total_cost"], 4),
    }
