#!/usr/bin/env python3
"""primitive_attribute_plan — the UNCAPPED, computed attribute/descriptor/embedding/hash plan per primitive.

Owner (2026-07-10): "Each primitive will need to have at a minimum 500+ attributes and descriptors … numerous ways
to describe the input and output … at least 5+ different embedding models and stored embeddings … tags, labels,
triggers, blocking keys, LSH hashes, wide and slim LSH hashes … the system should generate all of these columns …
throughout testing we will find the most appropriate efficient and effective paths. Why did you only support 60?
Shouldn't we support more, and allow flexibility for more?"

Answer, made executable: the earlier 61-column multi-index was a PILOT SLICE, not a ceiling. This module defines the
FULL LOGICAL column space as data-driven catalogs — description facets × linguistic styles × audiences, embedding
model slots, hash/LSH profiles, lexical/NLP matcher families (keyword counts, edit distance, word frequency,
fuzzy/phonetic, vowel/consonant/letter metrics — each with a trainable weight slot), and per-field projections —
and COMPUTES every count from those catalogs (no typed totals, no cap). Supporting more = adding a row; the
self-test PROVES a one-row addition grows the plan with no other change, and enforces the owner's ≥500 floor as a
ratchet.

Logical ≠ physical: everything below is logically declared for EVERY primitive; what gets physically materialized
is decided by the adaptive-vectorization WATERFALL (scripts/adaptive_vectorization.py) — L0 cards carry the cheap
universal slice, and usage promotes cards up the ladder until the full plan is materialized for the cards that earn
it. That is how "generate all of these columns" and "100M+ primitives" coexist without materializing
~10^11 vectors nobody has queried. All projections here are PLANS (candidate=true, serves_truth=false), never
measured savings claims.

    PYTHONPATH=. python3 scripts/primitive_attribute_plan.py --self-test
    PYTHONPATH=. python3 scripts/primitive_attribute_plan.py --plan                  # per-primitive logical plan
    PYTHONPATH=. python3 scripts/primitive_attribute_plan.py --corpus 100000000      # corpus-scale projection
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── DESCRIPTION SPACE (facets × styles × audiences) — every row is one way of describing; extend = add a row ────
DESCRIPTION_FACETS: list[str] = [
    # problem side
    "problem_context", "problem_goal", "problem_trigger", "problem_symptom",
    # primitive as a whole
    "purpose", "usage", "algorithm", "behavior", "whole_primitive_canonical",
    # inputs — combined and separated (the owner's "sometimes combined, sometimes separated")
    "inputs_combined", "input_each_port", "input_types", "input_semantics", "input_constraints",
    "input_examples", "input_invalid_examples",
    # outputs — combined and separated
    "outputs_combined", "output_each_port", "output_types", "output_semantics", "output_guarantees",
    "output_examples",
    # relations & contracts
    "input_output_transformation", "preconditions_postconditions", "errors", "side_effects",
    "security_privacy", "compatibility", "composition", "alternatives", "limitations",
    # chunked views (whole-or-in-chunks)
    "retrievable_chunk",
]
LINGUISTIC_STYLES: list[str] = ["canonical", "user_intent", "imperative_request", "question", "diagnostic",
                                "scenario", "terse_tags", "contrastive", "type_explanation"]
AUDIENCES: list[str] = ["developer", "operator", "planner_llm", "reviewer"]

# ── EMBEDDING MODEL SLOTS — computed from the live embedder zoo when importable (the zoo is the single source;
#    adding a model there grows this plan automatically), with a floor list so the plan stands alone offline. ────
_FALLBACK_EMBEDDING_MODEL_SLOTS: list[str] = [
    "model2vec_potion_8m", "fastembed_bge_small", "fastembed_minilm_l6", "ollama_nomic",
    "ollama_embeddinggemma", "fastembed_jina_code", "lsa_local_trained", "proxy_crc32",
]


def embedding_model_slots() -> list[str]:
    try:
        from scripts.embedder_zoo import EMBEDDER_BACKENDS  # noqa: PLC0415
        live = sorted(EMBEDDER_BACKENDS)
        return live if len(live) >= len(_FALLBACK_EMBEDDING_MODEL_SLOTS) else sorted(
            set(live) | set(_FALLBACK_EMBEDDING_MODEL_SLOTS))
    except Exception:  # noqa: BLE001  the zoo may be mid-edit in another session; the plan must stand alone
        return list(_FALLBACK_EMBEDDING_MODEL_SLOTS)


# ── HASH / LSH PROFILES (wide AND slim, per the owner) — one row per profile ─────────────────────────────────────
HASH_LSH_PROFILES: list[dict[str, Any]] = [
    {"name": "sha256_exact", "kind": "exact"},
    {"name": "blake2b_exact", "kind": "exact"},
    {"name": "simhash_64", "kind": "simhash", "bits": 64},
    {"name": "simhash_128", "kind": "simhash", "bits": 128},
    {"name": "simhash_256", "kind": "simhash", "bits": 256},
    {"name": "minhash_64_banded", "kind": "minhash", "permutations": 64},
    {"name": "minhash_128_banded", "kind": "minhash", "permutations": 128},
    {"name": "minhash_256_banded", "kind": "minhash", "permutations": 256},
    {"name": "angular_lsh_64", "kind": "angular", "bits": 64},
    {"name": "angular_lsh_128", "kind": "angular", "bits": 128},
    {"name": "angular_lsh_256", "kind": "angular", "bits": 256},
    {"name": "angular_lsh_512", "kind": "angular", "bits": 512},
    {"name": "cross_polytope_slim", "kind": "cross_polytope", "width": "slim"},
    {"name": "cross_polytope_wide", "kind": "cross_polytope", "width": "wide"},
    {"name": "p_stable_slim", "kind": "p_stable", "width": "slim"},
    {"name": "p_stable_wide", "kind": "p_stable", "width": "wide"},
    {"name": "winner_take_all_slim", "kind": "winner_take_all", "width": "slim"},
    {"name": "winner_take_all_wide", "kind": "winner_take_all", "width": "wide"},
]

# ── LEXICAL / NLP MATCHER FAMILIES — deterministic signals with TRAINABLE weight slots (the owner's "multiple
#    deterministic, semantic fuzzy match, keyword, edit distance, word frequency … language/vowel/consonant/letter
#    metrics … trained, with custom weights, multiple paths"). One row per family; every row is a rankable lane. ──
LEXICAL_SIGNAL_FAMILIES: list[dict[str, Any]] = [
    {"name": "exact_keyword", "trainable_weight": True},
    {"name": "keyword_count", "trainable_weight": True},
    {"name": "word_frequency_tf", "trainable_weight": True},
    {"name": "tf_idf", "trainable_weight": True},
    {"name": "bm25", "trainable_weight": True},
    {"name": "char_ngram_overlap", "trainable_weight": True},
    {"name": "word_ngram_overlap", "trainable_weight": True},
    {"name": "edit_distance_levenshtein", "trainable_weight": True},
    {"name": "edit_distance_damerau", "trainable_weight": True},
    {"name": "fuzzy_token_set_ratio", "trainable_weight": True},
    {"name": "phonetic_soundex", "trainable_weight": True},
    {"name": "phonetic_metaphone", "trainable_weight": True},
    {"name": "vowel_consonant_ratio", "trainable_weight": True},
    {"name": "letter_frequency_profile", "trainable_weight": True},
    {"name": "word_length_profile", "trainable_weight": True},
    {"name": "stopword_density", "trainable_weight": True},
    {"name": "subword_overlap", "trainable_weight": True},
    {"name": "acronym_expansion_match", "trainable_weight": True},
]

# ── CORE ATTRIBUTE FAMILIES (the semantic-ABI side) — canonical scalar/structured columns per primitive ──────────
CORE_ATTRIBUTE_FAMILIES: dict[str, int] = {
    "identity_and_epoch": 6,             # id, version metadata, epoch, lineage refs
    "ports_inputs_outputs_errors": 12,   # typed ports incl. edge names
    "semantic_types_refinements": 10,    # nominal/structural types, units, ranges, encodings
    "contracts_pre_post_invariants": 8,
    "effects_and_scopes": 8,             # least-privilege effect declarations
    "purity_determinism_totality": 6,
    "retry_atomicity_concurrency": 8,
    "resources_latency_cost": 8,
    "runtime_framework_compat": 10,
    "security_privacy_legal": 8,
    "provenance_evidence_trust": 10,
    "usage_telemetry_rollups": 8,        # searched/downloaded/implemented counters + success rates
}
#: per-field projections every attribute/description carries (state, confidence, labels, tags, triggers, blocking
#: keys, sparse terms, embedding refs, hashes, freshness, trust, conflict, evidence refs, privacy, tier, …).
PER_FIELD_PROJECTIONS: list[str] = [
    "normalized_value", "value_state", "confidence", "labels", "tags", "triggers", "blocking_keys",
    "sparse_terms", "embedding_refs", "exact_hash", "simhash", "minhash", "angular_lsh", "slim_code", "wide_code",
    "freshness", "trust_tier", "conflict_flag", "evidence_refs", "privacy_class", "materialization_tier",
    "extractor_id",
]

#: The owner's floor: every primitive's LOGICAL plan must clear this many attributes+descriptors. A ratchet — the
#: self-test fails if catalog edits ever drop the computed plan below it.
MINIMUM_ATTRIBUTES_AND_DESCRIPTORS_PER_PRIMITIVE = 500
#: The prior pilot slice this module supersedes as a ceiling (kept for the receipt: 61 columns was a START).
PILOT_MULTI_INDEX_COLUMNS = 61


def plan_per_primitive(catalogs: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """The COMPUTED logical plan for one primitive. Every count derives from the catalogs — nothing typed."""
    c = catalogs or {}
    facets = c.get("facets", DESCRIPTION_FACETS)
    styles = c.get("styles", LINGUISTIC_STYLES)
    audiences = c.get("audiences", AUDIENCES)
    models = c.get("models", embedding_model_slots())
    hashes = c.get("hashes", HASH_LSH_PROFILES)
    lexical = c.get("lexical", LEXICAL_SIGNAL_FAMILIES)
    families = c.get("families", CORE_ATTRIBUTE_FAMILIES)
    projections = c.get("projections", PER_FIELD_PROJECTIONS)

    core_attributes = sum(families.values())
    description_views = len(facets) * len(styles) * len(audiences)
    embeddable_surfaces = description_views  # every description view is an embeddable surface
    embedding_vector_slots = embeddable_surfaces * len(models)
    hash_record_slots = embeddable_surfaces * len(hashes)
    lexical_signal_slots = embeddable_surfaces * len(lexical)
    attribute_projection_slots = core_attributes * len(projections)
    attributes_and_descriptors = core_attributes + description_views

    return {
        "schema_version": "primitive-attribute-plan/v1",
        "catalog_sizes": {"facets": len(facets), "styles": len(styles), "audiences": len(audiences),
                          "embedding_model_slots": len(models), "hash_lsh_profiles": len(hashes),
                          "lexical_signal_families": len(lexical), "core_attribute_families": len(families),
                          "per_field_projections": len(projections)},
        "core_attributes": core_attributes,
        "description_views": description_views,
        "attributes_and_descriptors": attributes_and_descriptors,
        "embedding_vector_slots": embedding_vector_slots,
        "hash_record_slots": hash_record_slots,
        "lexical_signal_slots": lexical_signal_slots,
        "attribute_projection_slots": attribute_projection_slots,
        "total_logical_slots": (attributes_and_descriptors + embedding_vector_slots + hash_record_slots
                                + lexical_signal_slots + attribute_projection_slots),
        "floor": MINIMUM_ATTRIBUTES_AND_DESCRIPTORS_PER_PRIMITIVE,
        "floor_cleared": attributes_and_descriptors >= MINIMUM_ATTRIBUTES_AND_DESCRIPTORS_PER_PRIMITIVE,
        "supersedes_pilot_columns": PILOT_MULTI_INDEX_COLUMNS,
        "materialization": "logical for ALL primitives; physical materialization is usage-earned via "
                           "scripts/adaptive_vectorization.py (L0 universal slice -> full plan at the top level)",
        "candidate": True,
        "serves_truth": False,
    }


def corpus_projection(n_primitives: int) -> dict[str, Any]:
    """Corpus-scale LOGICAL projection (a plan, not a measurement — never quote as achieved savings)."""
    per = plan_per_primitive()
    try:
        from scripts.adaptive_vectorization import LEVELS, MAX_LEVEL  # noqa: PLC0415
        l0_vectors, max_vectors = LEVELS[0]["vectors"], LEVELS[MAX_LEVEL]["vectors"]
    except Exception:  # noqa: BLE001
        l0_vectors, max_vectors = 1, 300
    return {
        "n_primitives": n_primitives,
        "logical_description_views": n_primitives * per["description_views"],
        "logical_embedding_vector_slots": n_primitives * per["embedding_vector_slots"],
        "logical_hash_record_slots": n_primitives * per["hash_record_slots"],
        "logical_total_slots": n_primitives * per["total_logical_slots"],
        "materialized_floor_vectors_all_l0": n_primitives * l0_vectors,
        "materialized_ceiling_vectors_all_max": n_primitives * max_vectors,
        "note": "logical = declared and generatable for every primitive; materialized = what the usage-earned "
                "waterfall actually builds, between the L0 floor and the max ceiling. PLAN ONLY (projection, "
                "not a measured claim). candidate=true",
        "candidate": True,
        "serves_truth": False,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    per = plan_per_primitive()

    # (1) the owner's floor is a RATCHET: >=500 attributes+descriptors per primitive, computed not typed.
    checks.append((f"floor ratchet: {per['attributes_and_descriptors']} attributes+descriptors >= "
                   f"{MINIMUM_ATTRIBUTES_AND_DESCRIPTORS_PER_PRIMITIVE}",
                   per["floor_cleared"], json.dumps(per["catalog_sizes"])))

    # (2) the pilot 61-column slice is SUPERSEDED, not the ceiling: the computed plan is far wider.
    checks.append((f"pilot {PILOT_MULTI_INDEX_COLUMNS} columns superseded: core attributes alone = "
                   f"{per['core_attributes']}",
                   per["core_attributes"] > PILOT_MULTI_INDEX_COLUMNS, ""))

    # (3) >=5 embedding model slots (the owner's minimum) and every catalog non-trivial.
    sizes = per["catalog_sizes"]
    checks.append((f"embedding model slots {sizes['embedding_model_slots']} >= 5; hashes "
                   f"{sizes['hash_lsh_profiles']} incl. wide+slim; lexical families {sizes['lexical_signal_families']}",
                   sizes["embedding_model_slots"] >= 5 and sizes["hash_lsh_profiles"] >= 18
                   and sizes["lexical_signal_families"] >= 18
                   and any("wide" in h["name"] for h in HASH_LSH_PROFILES)
                   and any("slim" in h["name"] for h in HASH_LSH_PROFILES), ""))

    # (4) UNCAPPED extensibility: adding ONE row to any catalog grows the computed plan — no other change.
    grown = plan_per_primitive({"facets": DESCRIPTION_FACETS + ["new_facet_row"],
                                "models": embedding_model_slots() + ["new_model_row"]})
    checks.append(("adding a facet row + a model row grows the computed plan (flexibility proven, no cap)",
                   grown["description_views"] > per["description_views"]
                   and grown["embedding_vector_slots"]
                   > (per["embedding_vector_slots"] // per["catalog_sizes"]["embedding_model_slots"])
                   * grown["catalog_sizes"]["embedding_model_slots"] - grown["catalog_sizes"]["embedding_model_slots"]
                   and grown["total_logical_slots"] > per["total_logical_slots"], ""))

    # (5) every lexical family carries a trainable weight slot (custom weights, trainable paths).
    checks.append(("every lexical/NLP matcher family declares a trainable weight slot",
                   all(f.get("trainable_weight") for f in LEXICAL_SIGNAL_FAMILIES), ""))

    # (6) corpus projection at 100M stays LABELLED as a plan and binds to the waterfall floor/ceiling.
    projection = corpus_projection(100_000_000)
    checks.append(("100M projection labelled candidate/plan; waterfall floor < ceiling",
                   projection["serves_truth"] is False
                   and projection["materialized_floor_vectors_all_l0"]
                   < projection["materialized_ceiling_vectors_all_max"], ""))

    # (7) determinism: the plan is a pure function of the catalogs.
    checks.append(("plan deterministic", plan_per_primitive() == plan_per_primitive(), ""))

    ok = all(passed for _name, passed, _detail in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_attribute_plan: uncapped COMPUTED column space "
          f"({per['attributes_and_descriptors']} attributes+descriptors, {per['embedding_vector_slots']} embedding "
          f"slots, {per['total_logical_slots']} logical slots per primitive; floor "
          f">={MINIMUM_ATTRIBUTES_AND_DESCRIPTORS_PER_PRIMITIVE} ratcheted; extend = add a row). Materialization "
          f"is usage-earned via the adaptive-vectorization waterfall. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Uncapped computed attribute/descriptor plan per primitive.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--plan", action="store_true", help="the per-primitive logical plan (computed)")
    parser.add_argument("--corpus", type=int, help="corpus-scale logical projection at N primitives")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.plan:
        print(json.dumps(plan_per_primitive(), indent=2, sort_keys=True))
        return 0
    if args.corpus:
        print(json.dumps(corpus_projection(args.corpus), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
