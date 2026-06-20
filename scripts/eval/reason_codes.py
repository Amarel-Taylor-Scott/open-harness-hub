#!/usr/bin/env python3
"""Canonical taxonomy for classifying capability gaps and *why a lift survives*.

Single source of truth behind docs/concepts/capability-valleys.md and read by
scripts.eval.durable_gap_harness and scripts.factory.candidate_promotion_scorer.
Do not re-define these lists elsewhere — import from here (no magic values).

Names match the External Research Brief (2026-05-28) two-axis gate so the schema
field `lift_reason` and this module never drift.

The only question that decides whether a gap is worth building a component for:

    WILL THIS LIFT SURVIVE THE NEXT MODEL?

  - TRANSIENT lift: closes when labs throw scale, data, or a tool at it. The very
    expert demonstrations you collect to *find* it are the data that *erases* it
    a model generation later. Revenue today, depreciating — never a defensibility
    claim. Keep its benchmark traces governed/private (don't feed the flywheel).
  - STRUCTURAL lift: does not close with more model/data/tools — the advantage is
    not text-prediction at all (a body, a login, a license, accountability, a
    deterministic verifier) or the source is volatile/un-ingestible. The moat.
  - MIXED: part of the lift is structural, part will erode — watch its decay.

Three orthogonal axes (full write-up in the doc):
  MECHANISM            — why the task is hard for a model
  RETRIEVABILITY_TIER  — how reachable the ground truth is (clean API → human)
  LIFT_REASON          — why it lifts, which maps to a DURABILITY_CLASS
"""
from __future__ import annotations

# --- Durability + decay enums (the two-axis gate) --------------------------
DURABILITY_CLASSES: tuple[str, ...] = ("transient", "structural", "mixed")
# decay_signal is set by re-benchmarking a component against each new base model.
DECAY_SIGNALS: tuple[str, ...] = ("none", "watch", "decaying")

# --- Axis 1: why the task is hard (the failure mechanism) ------------------
MECHANISMS: dict[str, str] = {
    "anti_fluency": "Domain punishes fluent paraphrase, rewards a rigid approved-word grammar (ASD-STE100, ICAO phraseology).",
    "sub_token": "Task lives below the token boundary — exact character/byte counting, fixed-width alignment, raw digit ops.",
    "rigid_grammar": "Long-range structural constraints to satisfy exactly (SMILES valence/ring closure, Verilog timing, proof tactics, patent antecedent basis).",
    "sparse_data": "Little in-domain text; the model reverts to a common neighbor (low-resource languages, COBOL/JCL, Global South statutes).",
    "coded_vocabulary": "Output is a code where fluency gives zero signal and a plausible-but-wrong code is worse than abstaining (ICD-10, METAR, G-code).",
    "adversarial_concealment": "The target actively mutates to stay out-of-distribution (laundering typologies, trafficking code words, scam rebrands).",
    "channel_inaccessibility": "The authoritative source lives in a channel a pipeline cannot ingest (login-walled post, WhatsApp forward, scanned image, oral/radio, deleted/edited).",
}

# --- Axis 2: how reachable the ground truth is (retrievability spectrum) ----
RETRIEVABILITY_TIERS: list[dict[str, object]] = [
    {"tier": 1, "key": "clean_api", "label": "Clean public API",
     "example": "NYC Open Data / Socrata SoQL, Open311 GeoReport v2", "tooling_solves": True},
    {"tier": 2, "key": "structured_no_api", "label": "Structured data, no clean API",
     "example": "scrape/ETL into your own index", "tooling_solves": True},
    {"tier": 3, "key": "unstructured_addressable", "label": "Unstructured but addressable",
     "example": "PDFs/reports on a stable URL → OCR + RAG (lossy)", "tooling_solves": True},
    {"tier": 4, "key": "unaddressable_ephemeral", "label": "Un-addressable / ephemeral / login-walled",
     "example": "deleted Facebook post in Pidgin, WhatsApp-forwarded circular", "tooling_solves": False},
    {"tier": 5, "key": "human_only", "label": "Human-only (apex tool call)",
     "example": "go inspect the site, call the regulator, sign as a licensed pro", "tooling_solves": False},
]
TIER_BY_KEY: dict[str, dict[str, object]] = {t["key"]: t for t in RETRIEVABILITY_TIERS}
MAX_TIER: int = max(int(t["tier"]) for t in RETRIEVABILITY_TIERS)

# --- Axis 3: why it lifts → durability class (the analytic core) ------------
# The 8 brief codes verbatim + complementary codes; each maps to a class.
LIFT_REASONS: dict[str, dict[str, str]] = {
    # ---- transient: discount, the data flywheel closes these ----
    "long_tail_fact": {"durability_class": "transient",
        "note": "A fact a bigger model may simply absorb."},
    "esoteric_rule": {"durability_class": "transient",
        "note": "Closes if the rule enters training corpora (transient-leaning)."},
    "missing_tool": {"durability_class": "transient",
        "note": "Model wasn't given a tool/source it needed — closes by wiring it (tiers 1-3)."},
    "stale_parametric": {"durability_class": "transient",
        "note": "Model snapshot was stale — closes with retrieval over a live source."},
    "weak_reasoning_at_scale": {"durability_class": "transient",
        "note": "A reasoning/format slip scratchpads or larger models paper over."},
    # ---- structural: build, the lift does not come from the text ----
    "volatile_fact": {"durability_class": "structural",
        "note": "Structural-by-recency: true today, wrong next quarter; never 'known', only retrieved + versioned."},
    "no_addressable_source": {"durability_class": "structural",
        "note": "Source is un-crawlable: closed platform, oral, ephemeral (tier 4) — no endpoint to point a tool at."},
    "embodiment_required": {"durability_class": "structural",
        "note": "Needs a body/sensor/site visit — inspect, photograph, count, swab."},
    "closed_channel_access": {"durability_class": "structural",
        "note": "Needs a login, relationship, or credential to reach the source (tier 4)."},
    "accountability_or_license": {"durability_class": "structural",
        "note": "Needs an accountable/licensed human or a chain of custody. A model cannot hold a license or be sued."},
    "deterministic_guarantee": {"durability_class": "structural",
        "note": "Needs a rule/verifier a sampler can't promise."},
    "tacit_local_knowledge": {"durability_class": "structural",
        "note": "The informal price, who really decides, what the rule means in practice — never written down."},
    # ---- mixed: part structural, part erodes — watch decay ----
    "realtime_high_stakes_judgment": {"durability_class": "mixed",
        "note": "Judgment improves with models, but the high-stakes accountability stays human."},
}
STRUCTURAL_LIFT_REASONS: frozenset[str] = frozenset(
    c for c, v in LIFT_REASONS.items() if v["durability_class"] == "structural")
TRANSIENT_LIFT_REASONS: frozenset[str] = frozenset(
    c for c, v in LIFT_REASONS.items() if v["durability_class"] == "transient")

# Scoring band for the durability factor (0..5; high = defensible/durable lift).
_BASE_BY_CLASS = {"structural": 4.0, "mixed": 3.0, "transient": 1.0}
_UNKNOWN_BASE = 2.0       # unclassified: neutral-low until tagged
_TIER_STEP = 0.25         # each step DOWN the retrievability spectrum adds durability
_ADVERSARIAL_BONUS = 1.0  # non-stationary target → permanent gap
_CHANNEL_BONUS = 0.75     # source lives in an un-ingestible channel


def durability_class(lift_reason: str | None) -> str:
    """'transient' | 'structural' | 'mixed' | 'unknown'."""
    return LIFT_REASONS.get(lift_reason or "", {}).get("durability_class", "unknown")


def is_structural(lift_reason: str | None) -> bool:
    """True if more model/data/tools will NOT close this lift (the moat)."""
    return lift_reason in STRUCTURAL_LIFT_REASONS


def _clamp(value: float, low: float = 0.0, high: float = 5.0) -> float:
    return max(low, min(high, value))


def gap_durability_score(
    *,
    reason_codes: list[str] | None = None,
    retrievability_tier: int | str | None = None,
    adversarial: bool = False,
    mechanisms: list[str] | None = None,
) -> float:
    """Single source for the durability/defensibility factor (0..5, high = build).

    A lift is defensible to the extent it will NOT close on its own: structural
    lift reasons, low retrievability (no endpoint to tool), an adversarial/non-
    stationary target, or an un-ingestible channel all raise it.
    """
    codes = [c for c in (reason_codes or []) if c in LIFT_REASONS]
    classes = {durability_class(c) for c in codes}
    if "structural" in classes:
        base = _BASE_BY_CLASS["structural"]
    elif "mixed" in classes:
        base = _BASE_BY_CLASS["mixed"]
    elif "transient" in classes:
        base = _BASE_BY_CLASS["transient"]
    else:
        base = _UNKNOWN_BASE

    tier = 0
    if isinstance(retrievability_tier, str):
        tier = int(TIER_BY_KEY.get(retrievability_tier, {}).get("tier", 0))
    elif isinstance(retrievability_tier, (int, float)):
        tier = int(retrievability_tier)
    base += _TIER_STEP * max(0, tier - 1)

    if adversarial:
        base += _ADVERSARIAL_BONUS
    if "channel_inaccessibility" in (mechanisms or []):
        base += _CHANNEL_BONUS
    return round(_clamp(base), 3)


def _self_test() -> int:
    assert is_structural("embodiment_required") and not is_structural("missing_tool")
    assert durability_class("no_addressable_source") == "structural"
    assert durability_class("long_tail_fact") == "transient"
    assert durability_class("realtime_high_stakes_judgment") == "mixed"
    assert durability_class(None) == "unknown"
    # a deleted FB-post regulation in Pidgin = maximal structural gap
    hi = gap_durability_score(reason_codes=["no_addressable_source", "closed_channel_access"],
                              retrievability_tier="unaddressable_ephemeral", adversarial=True,
                              mechanisms=["channel_inaccessibility", "sparse_data"])
    lo = gap_durability_score(reason_codes=["long_tail_fact"], retrievability_tier=1)
    assert hi == 5.0, hi
    assert lo < 2.0, lo
    # every brief code present
    for code in ("long_tail_fact", "esoteric_rule", "volatile_fact", "no_addressable_source",
                 "embodiment_required", "closed_channel_access", "accountability_or_license",
                 "deterministic_guarantee"):
        assert code in LIFT_REASONS, code
    print(f"reason_codes OK · {len(LIFT_REASONS)} lift reasons "
          f"({len(STRUCTURAL_LIFT_REASONS)} structural / {len(TRANSIENT_LIFT_REASONS)} transient / "
          f"{sum(1 for v in LIFT_REASONS.values() if v['durability_class']=='mixed')} mixed) · "
          f"{len(MECHANISMS)} mechanisms · {len(RETRIEVABILITY_TIERS)} tiers · "
          f"durable_max={hi} transient_min={lo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
