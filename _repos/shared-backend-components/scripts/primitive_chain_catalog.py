#!/usr/bin/env python3
"""scripts.primitive_chain_catalog — ideated BASIC operation primitives across families (string, text,
vector, numeric, temporal, collection, categorical, graph, hash/crypto, geospatial) AND the canonical
CHAINS that link them (owner ask 2026-07-07: "how they are commonly linked together with other primitives,
into chains for data cleansing, data modeling, data representation, user management, data matching").

Two row kinds, both deterministic data:
  * OPERATION candidates — ~130 basic ops with typed edges (shared vocabulary; same-family ops chain);
  * CHAIN candidates — named pipelines expressed in the PLANNED-LANE DIALECT (a -> b(setting=v) -> c),
    each with purpose, family, and the settings knobs a caller (or an LLM's short plan) would tune. Chains
    reference pack impl names where they are ALREADY EXECUTABLE (reuse-first) and ideated op names
    otherwise (to_build = the minting queue).

candidate=true, serves_truth=false; generation is not promotion.

    python3 scripts/primitive_chain_catalog.py --self-test
    python3 scripts/primitive_chain_catalog.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_chain_catalog requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-chain"

#: family -> (input_edge, output_edge, ops). Op names are snake_case; pack-implemented names appear verbatim.
OPERATION_FAMILIES: dict[str, dict[str, Any]] = {
    "string": {"edges": ("RawStringValue", "NormalizedStringValue"), "ops": (
        "reverse_string", "pad_left", "pad_right", "truncate_with_ellipsis", "slugify", "camel_to_snake",
        "snake_to_camel", "remove_html_tags", "escape_sql_literal", "escape_regex_metachars",
        "normalize_line_endings", "dedent_text", "wrap_text_width", "extract_between_delimiters",
        "mask_middle_chars", "repeat_collapse_chars", "swap_case", "strip_bom", "normalize_quotes_pairs",
        "titlecase_with_exceptions")},
    "text": {"edges": ("TextDocumentValue", "TextAnalysisResult"), "ops": (
        "sentence_split", "paragraph_split", "stopword_filter", "porter_stem", "simple_lemmatize",
        "keyword_extract_tf", "acronym_expand", "abbreviation_detect", "readability_score_flesch",
        "language_guess_ngram", "quote_extract", "bullet_list_extract", "heading_detect",
        "boilerplate_strip", "sentence_case_repair", "profanity_flag", "spelling_variant_fold",
        "word_frequency_profile", "cooccurrence_pairs", "text_diff_tokens")},
    "vector": {"edges": ("EmbeddingVector", "VectorOperationResult"), "ops": (
        "l2_normalize", "cosine_similarity_pair", "dot_product_pair", "euclidean_distance_pair",
        "manhattan_distance_pair", "vector_mean_pool", "vector_max_pool", "vector_concat",
        "vector_pad_or_trim", "scalar_quantize_int8", "binary_quantize_sign", "top_k_by_similarity",
        "similarity_matrix_block", "centroid_of_cluster", "outlier_by_distance", "pca_project_2d",
        "random_projection_fixed_seed", "simhash_from_vector", "vector_delta", "weighted_vector_blend")},
    "numeric": {"edges": ("NumericFieldValue", "NormalizedNumericValue"), "ops": (
        "parse_locale_decimal", "unit_convert_length", "unit_convert_mass", "currency_minor_units",
        "round_half_even", "clamp_range", "zscore_scale", "minmax_scale", "log_transform_safe",
        "winsorize_percentile", "bucket_fixed_width", "bucket_quantile", "percent_change",
        "moving_average_window", "cumulative_sum", "safe_divide", "ratio_with_floor",
        "significant_figures_round", "detect_numeric_outlier_iqr", "benford_first_digit_profile")},
    "temporal": {"edges": ("TemporalFieldValue", "NormalizedTemporalValue"), "ops": (
        "parse_iso8601", "parse_us_date", "parse_eu_date", "epoch_to_utc", "utc_offset_apply",
        "truncate_to_day", "truncate_to_month", "week_of_year_iso", "business_days_between",
        "age_from_birthdate", "recency_bucket", "date_range_overlap", "duration_humanize",
        "timezone_guess_from_offset", "detect_future_date", "detect_impossible_date",
        "fiscal_period_assign", "cron_next_occurrence", "sessionize_by_gap", "interval_merge")},
    "collection": {"edges": ("RecordCollection", "CollectionOperationResult"), "ops": (
        "stable_sort_by_key", "group_by_key", "first_per_key", "last_per_key", "count_per_key",
        "top_n_per_key", "flatten_nested_lists", "zip_by_index", "set_union_keys", "set_intersect_keys",
        "set_difference_keys", "jaccard_of_sets", "chunk_into_batches", "round_robin_partition",
        "stable_shuffle_seeded", "sliding_window_records", "dedupe_preserve_order", "pivot_key_value",
        "unpivot_columns", "coalesce_first_nonnull")},
    "categorical": {"edges": ("CategoricalFieldValue", "EncodedCategoryValue"), "ops": (
        "one_hot_encode", "ordinal_encode_ordered", "frequency_encode", "rare_category_collapse",
        "unknown_category_bucket", "category_alias_fold", "hierarchy_rollup", "hash_encode_fixed_buckets",
        "target_mean_encode_fold_safe", "category_drift_compare")},
    "graph": {"edges": ("GraphEdgeList", "GraphAnalysisResult"), "ops": (
        "build_adjacency", "connected_components", "degree_count", "bfs_reachable_set",
        "shortest_path_unweighted", "triangle_count_node", "pagerank_iterations_fixed",
        "bipartite_project", "edge_dedupe", "self_loop_strip")},
    "hash_crypto": {"edges": ("SensitiveFieldValue", "ProtectedFieldValue"), "ops": (
        "sha256_hex", "blake2b_keyed_mac", "salted_hash_field", "hmac_compare_constant_time",
        "checksum_crc32", "uuid5_namespaced", "token_split_reversible", "format_preserving_mask",
        "k_anonymity_bucket_check", "pepper_rotate_rehash")},
    "geospatial": {"edges": ("GeoPointValue", "GeoOperationResult"), "ops": (
        "haversine_distance_km", "geohash_encode", "geohash_neighbors", "bounding_box_contains",
        "point_in_radius", "centroid_of_points", "lat_lon_validate", "coordinate_precision_round",
        "country_bbox_guess", "distance_bucket")},
    # the universal dirty-data spec's TYPE-INFERENCE family: guess before parsing, route to the right parser
    "type_inference": {"edges": ("DirtyObservedValue", "TypeCandidateList"), "ops": (
        "looks_like_null", "looks_like_boolean", "looks_like_integer", "looks_like_decimal",
        "looks_like_percent", "looks_like_currency", "looks_like_quantity", "looks_like_range",
        "looks_like_date", "looks_like_datetime", "looks_like_email", "looks_like_phone",
        "looks_like_url", "looks_like_uuid", "looks_like_json", "looks_like_html",
        "looks_like_address", "looks_like_person_name", "looks_like_company_name",
        "looks_like_contact_block", "select_type_candidate", "route_to_specialized_parser")},
    # markup/format types (owner ask: latex, bbcode, markdown, wiki, rst, csv-in-field, xml, yaml)
    "format_markup": {"edges": ("MarkupTextValue", "NormalizedDocumentValue"), "ops": (
        "detect_markdown", "markdown_to_plain_text", "markdown_extract_headings", "markdown_extract_links",
        "markdown_extract_code_blocks", "detect_latex", "latex_to_plain_text", "latex_extract_formulas",
        "latex_normalize_math_symbols", "detect_bbcode", "bbcode_to_plain_text", "bbcode_to_markdown",
        "detect_rst", "rst_to_plain_text", "detect_wiki_markup", "wiki_markup_to_plain_text",
        "detect_xml_fragment", "xml_to_canonical_text", "detect_yaml_fragment", "detect_csv_in_field",
        "escape_markup_for_display", "strip_all_markup_for_match")},
    # lexicon/nomenclature (owner ask: synonym detection, word frequency, nomenclature standardization)
    "lexicon": {"edges": ("TokenValue", "LexiconResult"), "ops": (
        "corpus_word_frequency", "document_frequency", "idf_weight", "rare_token_flag",
        "synonym_lookup", "synonym_ring_fold", "abbreviation_synonym_fold", "domain_nomenclature_map",
        "controlled_vocabulary_snap", "taxonomy_rollup", "hypernym_generalize", "stopword_profile",
        "collocation_detect", "term_variant_cluster", "spelling_variant_fold", "brand_generic_fold",
        "acronym_expansion_ring", "unit_nomenclature_fold", "job_title_nomenclature_fold",
        "industry_term_fold")},
    # dirty numerics from the universal spec: formula-like strings, locale decimals, accounting negatives
    "dirty_numeric": {"edges": ("DirtyNumericString", "TypedCanonicalNumber"), "ops": (
        "parse_accounting_negative", "parse_percent_string", "parse_basis_points", "parse_fraction_string",
        "parse_mixed_fraction", "parse_ordinal_string", "parse_word_number", "parse_magnitude_suffix",
        "parse_dimension_expression", "parse_quantity_times_price", "parse_pack_size", "parse_ratio_string",
        "detect_approximate_marker", "evaluate_safe_arithmetic", "reject_unsafe_expression")},
}

#: the universal spec's PACKAGE MAP — wrap-don't-rebuild candidates (each = one wrap primitive; reuse-first:
#: we NEVER reimplement what these do well; our packs cover the keyless deterministic core)
PACKAGE_WRAP_MAP: tuple[tuple[str, str, str], ...] = (
    ("ftfy", "mojibake repair", "fix_mojibake"), ("regex", "unicode-property regex", "regex_unicode_ops"),
    ("unidecode", "ascii transliteration", "transliterate_ascii"),
    ("python-slugify", "unicode slugs", "slugify"), ("inflection", "case/plural conversions", "case_convert"),
    ("phonenumbers", "international phone parse/E.164", "parse_phone_international"),
    ("email-validator", "email syntax+deliverability", "validate_email_full"),
    ("usaddress", "probabilistic US address parse", "parse_us_address_probabilistic"),
    ("libpostal", "international address parse", "parse_address_international"),
    ("probablepeople", "person/company string parse", "parse_party_probabilistic"),
    ("cleanco", "company suffix processing", "clean_company_suffix"),
    ("dateparser", "human-readable dates", "parse_human_date"),
    ("python-dateutil", "forgiving datetime parse", "parse_datetime_flexible"),
    ("babel", "locale numbers/currency", "parse_locale_number"),
    ("price-parser", "messy price extraction", "parse_price_string"),
    ("word2number", "number words to digits", "parse_word_number"),
    ("pint", "unit conversion", "convert_units"), ("quantulum3", "quantity extraction", "extract_quantities"),
    ("rapidfuzz", "fast fuzzy metrics", "fuzzy_similarity"),
    ("jellyfish", "phonetic + edit distances", "phonetic_keys_multi"),
    ("textdistance", "30+ similarity algorithms", "similarity_zoo"),
    ("recordlinkage", "linkage primitives", "record_linkage_pipeline"),
    ("dedupe", "ml dedupe", "ml_dedupe"), ("splink", "probabilistic linkage at scale", "probabilistic_linkage"),
    ("skrub", "dirty categorical features", "dirty_category_encode"),
    ("pandera", "dataframe schema validation", "validate_dataframe_schema"),
    ("pyjanitor", "dataframe cleaning api", "clean_dataframe"),
)

#: the CHAINS — plan-dialect pipelines linking ops (pack impl names verbatim where already executable)
CHAIN_CATALOG: tuple[tuple[str, str, str], ...] = (
    # (chain name, purpose family, plan)
    ("clean_freeform_text_field", "data_cleansing",
     "trim_collapse_whitespace -> unicode_normalize_nfc -> normalize_apostrophes -> remove_html_tags -> "
     "repeat_collapse_chars -> normalize_line_endings"),
    ("standardize_person_record", "data_cleansing",
     "trim_collapse_whitespace -> unicode_normalize_nfc -> standardize_party_name -> "
     "standardize_person_name -> generate_match_keys"),
    ("standardize_company_record", "data_cleansing",
     "trim_collapse_whitespace -> standardize_party_name -> standardize_company_name -> "
     "generate_match_keys"),
    ("standardize_us_address_record", "data_cleansing",
     "trim_collapse_whitespace -> standardize_us_address -> geohash_encode(precision=7)"),
    ("dummy_data_screen", "data_cleansing",
     "name_dummy_signals -> phone_dummy_signals -> email_dummy_signals -> rate_dummy_likelihood -> "
     "if(is_likely_dummy)?route_to_review:pass_through"),
    ("null_and_placeholder_sweep", "data_cleansing",
     "detect_placeholder_name -> coalesce_first_nonnull -> unknown_category_bucket"),
    ("numeric_field_hardening", "data_cleansing",
     "parse_locale_decimal -> clamp_range -> detect_numeric_outlier_iqr -> winsorize_percentile(p=1)"),
    ("temporal_field_hardening", "data_cleansing",
     "parse_iso8601 -> detect_impossible_date -> detect_future_date -> truncate_to_day"),
    ("dedupe_blocking_pipeline", "data_matching",
     "tokenize_alnum -> token_sorted_key -> soundex_key -> blocking_key(parts=2) -> group_by_key"),
    ("person_match_pipeline", "data_matching",
     "standardize_person_name -> generate_match_keys -> blocking_key -> jaccard_of_sets -> "
     "if(above_threshold)?create_match_candidate:skip"),
    ("company_match_pipeline", "data_matching",
     "standardize_company_name -> token_sorted_key -> blocking_key -> cosine_similarity_pair -> "
     "if(above_threshold)?create_match_candidate:route_to_review"),
    ("near_duplicate_text_screen", "data_matching",
     "boilerplate_strip -> ngram_key(n=3) -> simhash_from_vector -> group_by_key -> top_n_per_key(n=5)"),
    ("embedding_retrieval_chain", "data_representation",
     "sentence_split -> stopword_filter -> l2_normalize -> top_k_by_similarity(k=10) -> "
     "weighted_vector_blend"),
    ("document_chunk_index_chain", "data_representation",
     "boilerplate_strip -> paragraph_split -> chunk_into_batches(size=400) -> l2_normalize -> "
     "geohash_encode"),
    ("feature_vector_assembly", "data_modeling",
     "one_hot_encode -> frequency_encode -> zscore_scale -> vector_concat -> vector_pad_or_trim(dim=128)"),
    ("target_leak_safe_encoding", "data_modeling",
     "rare_category_collapse(min_count=20) -> target_mean_encode_fold_safe(folds=5) -> minmax_scale"),
    ("time_series_feature_chain", "data_modeling",
     "parse_iso8601 -> sessionize_by_gap(minutes=30) -> moving_average_window(w=7) -> percent_change"),
    ("cohort_rollup_chain", "data_modeling",
     "truncate_to_month -> group_by_key -> count_per_key -> pivot_key_value"),
    ("user_signup_hardening", "user_management",
     "trim_collapse_whitespace -> email_dummy_signals -> rate_dummy_likelihood -> salted_hash_field -> "
     "if(is_likely_dummy)?route_to_review:create_account"),
    ("user_identity_merge_screen", "user_management",
     "standardize_person_name -> generate_match_keys -> hmac_compare_constant_time -> "
     "if(strong_signal)?create_match_candidate:route_to_review"),
    ("session_activity_rollup", "user_management",
     "sessionize_by_gap(minutes=30) -> count_per_key -> recency_bucket -> category_drift_compare"),
    ("pii_protection_chain", "user_management",
     "mask_middle_chars -> salted_hash_field -> k_anonymity_bucket_check(k=5) -> "
     "if(bucket_too_small)?suppress_output:pass_through"),
    ("fraud_ring_screen", "data_matching",
     "phone_dummy_signals -> build_adjacency -> connected_components -> degree_count -> "
     "top_n_per_key(n=20)"),
    ("catalog_search_document_chain", "data_representation",
     "slugify -> keyword_extract_tf -> word_frequency_profile -> l2_normalize"),
    ("geospatial_dedupe_chain", "data_matching",
     "lat_lon_validate -> coordinate_precision_round(places=4) -> geohash_encode(precision=7) -> "
     "group_by_key -> haversine_distance_km"),
    ("audit_trail_chain", "data_modeling",
     "sha256_hex -> uuid5_namespaced -> interval_merge -> stable_sort_by_key"),
)


def mint_operation_rows() -> list[dict[str, Any]]:
    rows = []
    for family, spec in sorted(OPERATION_FAMILIES.items()):
        ie, oe = spec["edges"]
        for op in spec["ops"]:
            words = op.replace("_", " ")
            title = f"{words} ({family} operation)"
            rows.append({"primitive_id": canonical_id(CARD_PREFIX, family, op), "kind": "primitive",
                         "record_type": "basic_operation_primitive_candidate", "title": title[:160],
                         "operation_family": family, "impl_name": op,
                         "blackbox": f"Basic {family} operation: {words}. Input: a {ie}. Output: a {oe}.",
                         "input_edge": ie, "output_edge": oe,
                         "tags": f"family:{family} op:{op}", **BOUNDARY})
    return rows


def mint_package_wrap_rows() -> list[dict[str, Any]]:
    """The universal spec's package map as WRAP candidates (integrate, never rebuild)."""
    rows = []
    for pkg, purpose, impl in PACKAGE_WRAP_MAP:
        rows.append({"primitive_id": canonical_id(CARD_PREFIX, "wrap", pkg), "kind": "primitive",
                     "record_type": "package_wrap_primitive_candidate",
                     "title": f"Wrap {pkg}: {purpose}", "impl_name": impl, "wrapped_package": pkg,
                     "blackbox": f"Wrap-don't-rebuild candidate: expose {pkg} ({purpose}) behind the "
                                 f"deterministic primitive seam `{impl}`. Input: DirtyObservedValue. "
                                 f"Output: TypedCanonicalValue.",
                     "input_edge": "DirtyObservedValue", "output_edge": "TypedCanonicalValue",
                     "tags": f"wrap:{pkg}", **BOUNDARY})
    return rows


def mint_chain_rows(known_ops: set[str]) -> list[dict[str, Any]]:
    rows = []
    for name, purpose, plan in CHAIN_CATALOG:
        steps = re.findall(r"[a-z_]+", plan.split("?")[0])
        rows.append({"primitive_id": canonical_id(CARD_PREFIX, "chain", name), "kind": "primitive_group",
                     "record_type": "operation_chain_candidate", "title": f"Chain: {name.replace('_', ' ')}",
                     "chain_name": name, "purpose_family": purpose, "plan": f"PLAN: {plan}",
                     "plan_steps": [s for s in steps if s in known_ops or s in ("if", "loop")],
                     "blackbox": f"Canonical {purpose.replace('_', ' ')} chain '{name}': {plan}. Steps with "
                                 f"parentheses carry SETTINGS in the plan dialect; deterministic builders "
                                 f"wire it. Input: RawStringValue/RecordCollection. Output: chain result.",
                     "input_edge": "RawDataInput", "output_edge": "ChainResult",
                     "tags": f"chain:{name} purpose:{purpose}", **BOUNDARY})
    return rows


def _pack_impl_names() -> set[str]:
    names: set[str] = set()
    for mod_name in ("scripts.string_standardization_primitives", "scripts.party_name_primitives",
                     "scripts.dummy_data_detection_primitives", "scripts.ui_design_primitives"):
        try:
            mod = __import__(mod_name, fromlist=["all_cards"])
            names |= {str(c.get("impl_name")) for c in mod.all_cards()}
        except Exception:  # noqa: BLE001
            continue
    return names


def run_catalog() -> dict[str, Any]:
    op_rows = mint_operation_rows()
    wrap_rows = mint_package_wrap_rows()
    known = {r["impl_name"] for r in op_rows} | _pack_impl_names() | {r["impl_name"] for r in wrap_rows}
    chain_rows = mint_chain_rows(known)
    out_dir = resource("data") / "dev-intel" / "primitive_chain_catalog"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = op_rows + wrap_rows + chain_rows
    (out_dir / "operation_and_chain_candidates.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    executable = sum(1 for r in chain_rows
                     for s in r["plan_steps"] if s in _pack_impl_names())
    rec = {"record_type": "primitive_chain_catalog_receipt", "operation_candidates": len(op_rows),
           "package_wraps": len(wrap_rows),
           "families": len(OPERATION_FAMILIES), "chains": len(chain_rows),
           "chain_steps_already_executable": executable,
           "staged_path": str(out_dir / "operation_and_chain_candidates.jsonl"), **BOUNDARY}
    (out_dir / "primitive_chain_catalog_receipt.json").write_text(json.dumps(rec, indent=2, sort_keys=True))
    return rec


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    ops = mint_operation_rows()
    checks.append(("mints 235+ basic operations across ALL declared families with typed edges (incl. "
                   "type-inference, dirty-numeric, format-markup latex/bbcode/markdown, and lexicon "
                   "synonym/frequency/nomenclature families)",
                   len(ops) >= 235
                   and {r["operation_family"] for r in ops} == set(OPERATION_FAMILIES)
                   and all(r["input_edge"] and r["output_edge"] for r in ops)
                   and any(r["impl_name"] == "latex_extract_formulas" for r in ops)
                   and any(r["impl_name"] == "synonym_ring_fold" for r in ops)))
    wraps = mint_package_wrap_rows()
    checks.append(("universal-spec package map minted as WRAP candidates (integrate, never rebuild)",
                   len(wraps) == len(PACKAGE_WRAP_MAP) >= 25
                   and any(r["wrapped_package"] == "phonenumbers" for r in wraps)))
    checks.append(("same-family ops share edges (chainability)",
                   len({r["input_edge"] for r in ops if r["operation_family"] == "string"}) == 1))
    known = {r["impl_name"] for r in ops} | _pack_impl_names()
    chains = mint_chain_rows(known)
    checks.append(("26 canonical chains across cleansing/matching/modeling/representation/user-management",
                   len(chains) == len(CHAIN_CATALOG)
                   and {r["purpose_family"] for r in chains} >= {"data_cleansing", "data_matching",
                                                                 "data_modeling", "data_representation",
                                                                 "user_management"}))
    checks.append(("chains are in the PLAN DIALECT with inline settings",
                   all(r["plan"].startswith("PLAN: ") for r in chains)
                   and any("(" in r["plan"] for r in chains)))
    checks.append(("REUSE-FIRST: chains reference already-executable pack primitives",
                   sum(1 for r in chains if set(r["plan_steps"]) & _pack_impl_names()) >= 8))
    checks.append(("unique ids + deterministic",
                   len({r["primitive_id"] for r in ops + chains}) == len(ops) + len(chains)
                   and json.dumps(mint_operation_rows(), sort_keys=True)
                   == json.dumps(mint_operation_rows(), sort_keys=True)))
    checks.append(("boundary", all(r.get("serves_truth") is False for r in ops + chains)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_chain_catalog: {len(ops)} basic operations x {len(OPERATION_FAMILIES)} "
          f"families + {len(chains)} canonical chains in the plan dialect (settings inline; pack "
          f"primitives reused). serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        print(json.dumps(run_catalog(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
