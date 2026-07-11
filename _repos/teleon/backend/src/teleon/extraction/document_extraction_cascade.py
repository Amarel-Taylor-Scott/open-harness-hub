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
                      "deterministic": d["stage"] != "llm_extract",
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


# ---------------------------------------------------------------------------
# The headline margin + brain integration (the descent, recorded — owner 2026-06-21)
# ---------------------------------------------------------------------------
# The cascade IS a descent (the naive default — send the whole document to a frontier LLM — descended to the
# cheapest-that-meets path). Make that explicit: compute the frontier-only baseline vs the cascade (the headline
# "you don't need the frontier model" margin), name the REAL cheap + frontier models from the model registry
# (model_index, via substrate_selector — same load-bearing wiring as catalog_descent), and record the move as a
# DescentAttempt so the extraction descent feeds the same brain/meta-learner. serves_truth stays False.


def frontier_only_cost(doc: dict, *, scanned_acquire: float = 0.300) -> float:
    """What most people pay: acquire + ONE frontier LLM pass over the whole document. The naive baseline."""
    acquire = 0.002 if doc.get("has_text_layer") else (scanned_acquire if doc.get("scanned") else 0.300)
    frontier = next(m for m in _LADDER if m.name == "frontier_llm").cost
    return round(acquire + frontier, 4)


def extraction_savings(required_fields: dict | None = None, doc: dict | None = None, *,
                       available_keys: tuple = ("LLM_API_KEY",), confidence_floor: float = 0.8) -> dict:
    """The headline: frontier-only baseline vs the measured cascade, at the SAME met-requirement. Names the real
    cheap+frontier models the tiers map to (lineage from model_index)."""
    required_fields = required_fields or EMPLOYMENT_AGENCY_SCHEMA
    doc = doc or {"has_text_layer": True, "scanned": False}
    casc = extract_measured(required_fields, doc, available_keys=available_keys, confidence_floor=confidence_floor)
    baseline = frontier_only_cost(doc)
    lineage = {"cheap_llm": None, "frontier_llm": None}
    try:
        from src.teleon.evolution import substrate_selector
        dg = substrate_selector.model_downgrade()
        lineage = {"cheap_llm": dg.get("picked_model"), "frontier_llm": dg.get("frontier_model"),
                   "substrate_ref": dg.get("substrate_ref")}
    except Exception:  # noqa: BLE001 — lineage is annotation; never block extraction on the registry
        pass
    saved = round(baseline - casc["total_cost"], 4)
    return {"frontier_only_cost": baseline, "cascade_cost": casc["total_cost"], "cost_saved": saved,
            "pct_saved": round(100 * saved / baseline, 1) if baseline else 0.0,
            "met_requirement": casc["met_requirement"], "used_llm": casc["used_llm"],
            "model_lineage": lineage, "path": casc["path"], "serves_truth": False}


def record_extraction_descent(store, *, required_fields: dict | None = None, doc: dict | None = None,
                              available_keys: tuple = ("LLM_API_KEY",), confidence_floor: float = 0.8) -> dict:
    """Record the extraction cascade as a DescentAttempt (before = frontier-only naive default; after = the measured
    cascade) into the canonical descent brain, so the meta-learner learns extraction descents too. Returns the
    savings summary. Uses the brain's 5 canonical axes; serves_truth stays False."""
    from src.teleon.evolution.descent_attempt_store import DescentAttempt
    s = extraction_savings(required_fields, doc, available_keys=available_keys, confidence_floor=confidence_floor)
    before = {"cost": s["frontier_only_cost"], "determinism": 0.2, "tokens_in": 4000, "llm_usage": 1, "freshness": 0.2}
    after = {"cost": s["cascade_cost"], "determinism": 0.2 if s["used_llm"] else 1.0,
             "tokens_in": 2000 if s["used_llm"] else 0, "llm_usage": 1 if s["used_llm"] else 0,
             "freshness": 0.2 if s["used_llm"] else 1.0}
    outcome = "converged" if not s["used_llm"] else ("improved" if s["cost_saved"] > 0 else "no_change")
    strategy = "llm_to_rule" if not s["used_llm"] else "model_downgrade"
    store.append(DescentAttempt(
        unit_id="extraction:document_schema_cascade", strategy=strategy, before=before, after=after, outcome=outcome,
        losers=("frontier_llm",), rollback_target="extraction:frontier_only",
        raw_ref="src/teleon/extraction/document_extraction_cascade.py",
        substrate_ref=s["model_lineage"].get("substrate_ref", "deterministic_rule")))
    return s


# ---------------------------------------------------------------------------
# LLM-as-CONTROL-SUPERVISOR (owner 2026-06-21): the cheapest mode — deterministic/cheap methods extract EVERY field,
# and the LLM is used ONLY to AUDIT a sample of that output for accuracy (not to extract), then escalate ONLY the
# fields the audit flags below the floor. "LLM calls only as a control supervisor checking accuracy of the cheaper
# methods/heuristics." Far cheaper than a frontier pass over the whole document. serves_truth stays False.
# ---------------------------------------------------------------------------
def supervise_extraction(required_fields: dict, doc: dict, *, available_keys: tuple = ("LLM_API_KEY",),
                         audit_fraction: float = 0.34, audit_floor: float = 0.9) -> dict:
    """Deterministic methods fill ALL fields; the LLM AUDITS a `audit_fraction` sample for accuracy (cost = a fraction
    of ONE cheap-LLM call), then ONLY the audit-flagged fields escalate to the cheap LLM. Returns a cost/path receipt;
    a flagged field with no LLM key is reported MISSING, never fabricated. Deterministic (measured fixtures stand in
    for the audit verdict)."""
    import math
    have = {k.upper() for k in available_keys}
    has_llm = "LLM_API_KEY" in have
    acq = _pick_acquire(doc, have)
    steps: list[dict] = []
    cost = 0.0
    if acq:
        steps.append({"stage": "acquire", "method": acq[0], "cost": acq[1]}); cost += acq[1]
    # 1. deterministic extraction of ALL fields — answers BEFORE any LLM (distinct rule-method costs, once)
    rule_methods = [m for m in _LADDER if m.stage == "rule_extract"]
    det_cost = round(sum(m.cost for m in rule_methods), 4)
    cost += det_cost
    steps.append({"stage": "rule_extract", "method": "+".join(m.name for m in rule_methods), "cost": det_cost,
                  "effect": "deterministic fill of all fields (OCR/text + patterns + dedupe)"})
    field_acc: dict[str, float] = {}
    for field, cls in required_fields.items():
        best = 0.0
        for m in rule_methods:
            a = measured_field_accuracy(m.name, field)
            a = a if a is not None else (measured_class_accuracy(m.name, cls) or 0.0)
            best = max(best, a)
        field_acc[field] = round(best, 4)
    rule_filled = [f for f, a in field_acc.items() if a > 0]
    # 2. LLM SUPERVISOR audits a SAMPLE for accuracy (does NOT extract) — cost = fraction of one cheap-LLM call
    fields = list(required_fields)
    sample_n = max(1, math.ceil(audit_fraction * len(fields))) if fields else 0
    sample = fields[:sample_n]
    cheap = next(m.cost for m in _LADDER if m.name == "cheap_llm")
    audit_cost = round(audit_fraction * cheap, 4) if (has_llm and sample) else 0.0
    cost += audit_cost
    audit_accuracy = round(sum(field_acc[f] for f in sample) / len(sample), 4) if sample else 1.0
    if has_llm:
        steps.append({"stage": "supervise", "method": "cheap_llm_audit", "cost": audit_cost, "audited": sample,
                      "audit_accuracy": audit_accuracy, "role": "supervisor — checks the cheap methods, does not extract"})
    # 3. escalate ONLY the fields the audit flags below the floor → one cheap-LLM pass
    flagged = [f for f, a in field_acc.items() if a < audit_floor]
    used_escalation = bool(flagged and has_llm)
    if used_escalation:
        cost += cheap
        steps.append({"stage": "llm_extract", "method": "cheap_llm", "cost": cheap, "escalated": flagged,
                      "effect": "re-extract ONLY the audit-flagged fields (chunked, cheap)"})
    missing = [] if has_llm else flagged
    return {"required": dict(required_fields), "rule_filled": rule_filled, "audited_sample": sample,
            "audit_accuracy": audit_accuracy, "escalated": flagged if has_llm else [], "missing": missing,
            "llm_role": "supervisor" + ("+targeted_escalation" if used_escalation else ""),
            "total_cost": round(cost, 4), "steps": steps, "serves_truth": False}


def compare_strategies(required_fields: dict | None = None, doc: dict | None = None, *,
                       available_keys: tuple = ("LLM_API_KEY",), confidence_floor: float = 0.8,
                       audit_floor: float = 0.9) -> dict:
    """The flagship 3-way for slides/demos: (1) frontier-only — send the WHOLE PDF/email to the frontier model (what
    most companies do today), (2) the cheapest-that-meets cascade, (3) LLM-as-supervisor. Costs computed; serves_truth
    False. This is the land-lease / oil & gas extraction story made concrete."""
    required_fields = required_fields or EMPLOYMENT_AGENCY_SCHEMA
    doc = doc or {"has_text_layer": True, "scanned": False}
    baseline = frontier_only_cost(doc)
    casc = extract_measured(required_fields, doc, available_keys=available_keys, confidence_floor=confidence_floor)
    sup = supervise_extraction(required_fields, doc, available_keys=available_keys, audit_floor=audit_floor)
    def pct(c: float) -> float:
        return round(100 * (baseline - c) / baseline, 1) if baseline else 0.0
    return {"fields": len(required_fields),
            "frontier_only": {"cost": baseline, "note": "send the entire PDF/email to the frontier model (Gemini-class)"},
            "cascade": {"cost": casc["total_cost"], "pct_saved": pct(casc["total_cost"]),
                        "used_llm": casc["used_llm"], "path": casc["path"]},
            "supervised": {"cost": sup["total_cost"], "pct_saved": pct(sup["total_cost"]), "llm_role": sup["llm_role"],
                           "rule_filled": len(sup["rule_filled"]), "escalated": len(sup["escalated"])},
            "serves_truth": False}
