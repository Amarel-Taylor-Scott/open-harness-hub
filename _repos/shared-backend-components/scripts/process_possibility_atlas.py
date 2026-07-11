#!/usr/bin/env python3
"""scripts.process_possibility_atlas — the reusable STEP x LAYER x POSSIBILITY atlas across every process family
(candidate-only), and a raw-count generator that explodes every possibility into a primitive candidate.

Owner directive (2026-07-09): give examples of all steps, each possibility per step, per layer, for document
ingestion, document processing, AI tasks, ML training, evaluation, and serving — as a reusable process atlas
(layers, step alternatives, routing choices, verification choices, examples). Combined with the raw-count law
(owner 2026-07-08: "raw count is very important, scale it, then test against billions/trillions of prompts and
figure out what works best — stop artificially limiting yourself"): every possibility here is a first-class
primitive CANDIDATE. We scale count; empirical testing at scale decides what works; usefulness routes
non-destructively.

The reusable "possibility schema" (owner §9), applied to every step:
    {step_id, goal, possible_methods:[{method,best_for,cost,quality,failure_modes}], routing_features,
     verifiers, fallbacks}

This module encodes the MASTER 10-layer model, six process DOMAINS with their ordered steps and the possibility
zoo per step, one fully-worked RICH method example (layout_detection with cost/quality/failure_modes), and a
`build_candidate_cards()` that explodes every (domain, step, possibility) into a candidate primitive. Everything
candidate=true / serves_truth=false. Extend by adding a row (a step, a possibility, a domain) — never a rewrite.

    python3 scripts/process_possibility_atlas.py --self-test
    python3 scripts/process_possibility_atlas.py --emit
    python3 scripts/process_possibility_atlas.py --stats
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"process_possibility_atlas requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ATLAS_ID_PREFIX = "prim-atlas"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
SPEC_FILENAME = "process_possibility_atlas.json"
CARDS_FILENAME = "process_possibility_atlas_candidate_cards.jsonl"
PACKAGED_AT = "2026-07-08T00:00:00Z"

# ── the master model: every process moves through these universal layers, each a zoo of implementations ──────
MASTER_LAYERS: list[str] = [
    "input", "metadata_context", "classification", "route_selection", "transformation", "verification",
    "promotion_or_rejection", "serving", "telemetry", "drift_feedback",
]
IMPLEMENTATION_KINDS: list[str] = [
    "manual", "deterministic_code", "rules_engine", "schema_validator", "ocr_vlm", "embedding_search",
    "llm_extraction", "browser_automation", "api_call", "workflow_engine", "human_review", "benchmark_harness",
    "compiled_primitive",
]

# ── the possibility schema (owner §9) — the shape every step is stored in ────────────────────────────────────
POSSIBILITY_SCHEMA_FIELDS: list[str] = [
    "step_id", "goal", "possible_methods", "routing_features", "verifiers", "fallbacks",
]

# ── DOMAINS -> ordered steps -> possibility zoo. Compact: possibilities are the zoo members (each -> a candidate
#    primitive). routing_features/verifiers/fallbacks filled where the owner named them. Extend by adding a row. ─
DOMAIN_STEPS: dict[str, list[dict[str, Any]]] = {
    "document_ingestion": [
        {"step": "source_discovery", "possibilities": [
            "official_standard_search", "government_api_discovery", "sitemap_crawl", "rss_feed_discovery",
            "github_repo_scan", "kaggle_notebook_discovery", "public_dataset_catalog", "vendor_docs_crawl",
            "customer_upload", "email_attachment_intake", "browser_download", "cloud_bucket_scan",
            "api_changelog_watcher", "support_ticket_attachment_miner", "sop_binder_miner"],
         "routing_features": ["domain", "expected_primitive_yield"], "verifiers": ["source_reachable"],
         "fallbacks": ["queue_for_review"]},
        {"step": "source_trust_acquisition_policy", "possibilities": [
            "allow_public_fetch", "allow_api_only", "allow_browser_fetch", "allow_customer_file_only",
            "allow_metadata_only", "quarantine_source", "skip_license_unclear", "skip_robots_terms_block",
            "require_human_approval"],
         "routing_features": ["authority_tier", "license", "sensitivity"], "verifiers": ["policy_allows_use"],
         "fallbacks": ["quarantine_source"]},
        {"step": "acquisition", "possibilities": [
            "http_get", "curl_wget", "python_requests_httpx", "browser_download", "playwright_selenium_cdp",
            "rest_api", "graphql_api", "openapi_client", "sftp", "s3_gcs_azure_blob", "github_raw", "kaggle_api",
            "data_gov_api", "email_attachment", "manual_upload", "webhook"],
         "routing_features": ["api_available", "js_required", "login_required", "private_data"],
         "verifiers": ["content_hash_matches"], "fallbacks": ["browser_automation", "require_authorized_session"]},
        {"step": "raw_preservation", "possibilities": [
            "store_raw_pdf", "store_raw_html", "store_raw_json", "store_raw_csv", "store_raw_notebook",
            "store_raw_screenshot", "store_browser_har", "store_dom_snapshot", "store_accessibility_tree",
            "store_cloud_object_metadata", "store_hash_only_if_unretained"],
         "routing_features": ["retainable", "content_type"], "verifiers": ["raw_hash_recorded"], "fallbacks": []},
        {"step": "metadata_classification", "possibilities": [
            "classify_by_filename", "classify_by_url_path", "classify_by_domain", "classify_by_mime_type",
            "classify_by_pdf_metadata", "classify_by_page_count", "classify_by_language",
            "classify_by_source_authority", "classify_by_file_size", "classify_by_title",
            "classify_by_first_page_sample", "classify_by_metadata_embedding", "classify_by_bounded_llm"],
         "routing_features": ["filename", "url", "headers", "pdf_metadata"],
         "verifiers": ["classification_confidence"], "fallbacks": ["deeper_sample"]},
        {"step": "triage", "possibilities": [
            "digital_pdf_text_first", "scanned_pdf_ocr", "hybrid_text_plus_ocr", "table_heavy_pipeline",
            "form_extraction_pipeline", "contract_extraction_pipeline", "policy_extraction_pipeline",
            "standards_extraction_pipeline", "code_heavy_pipeline", "image_heavy_pipeline", "skip_or_quarantine"],
         "routing_features": ["embedded_text_ratio", "image_density", "table_density", "scan_quality",
                              "source_trust", "expected_value"],
         "verifiers": ["route_covers_pages"], "fallbacks": ["hybrid_text_plus_ocr"]},
        {"step": "forensics", "possibilities": [
            "detect_embedded_text", "detect_scanned_pages", "detect_encryption", "detect_page_rotation",
            "detect_page_size", "detect_fonts", "detect_images", "detect_form_fields", "detect_annotations",
            "detect_bookmarks", "detect_attachments", "detect_digital_signatures", "detect_cheap_tables",
            "detect_multi_column"],
         "routing_features": ["page_count"], "verifiers": [], "fallbacks": []},
        {"step": "page_rendering", "possibilities": [
            "render_all_pages", "render_selected_pages", "render_first_page_for_classification", "render_72_dpi",
            "render_100_dpi", "render_150_dpi", "render_200_dpi", "adaptive_dpi", "rgb_render", "grayscale_render",
            "tile_render", "thumbnail_render", "rotation_corrected_render"],
         "routing_features": ["small_font_density", "table_density", "text_size"],
         "verifiers": ["page_image_hash"], "fallbacks": ["higher_dpi_render"]},
        {"step": "page_visual_classification", "possibilities": [
            "text_heavy", "table_heavy", "form", "diagram", "figure", "scanned", "handwritten", "multi_column",
            "code_heavy", "formula_heavy", "low_quality_scan", "blank", "cover_page", "toc", "appendix"],
         "routing_features": ["layout_complexity"], "verifiers": [], "fallbacks": []},
        {"step": "layout_detection", "possibilities": [
            "no_layout_detection", "rule_based_layout", "pp_doclayout_v3", "detectron_layout",
            "commercial_document_ai", "vlm_full_page_layout", "ocr_first_then_reconstruct",
            "hybrid_textbox_image_fusion"],
         "routing_features": ["page_class", "table_density", "scan_quality", "source_trust", "cost_budget"],
         "verifiers": ["region_coverage_score", "reading_order_score", "table_fidelity_score"],
         "fallbacks": ["full_page_ocr", "higher_dpi_render", "human_review"]},
        {"step": "region_routing", "possibilities": [
            "heading_ocr", "paragraph_ocr", "table_ocr", "formula_ocr", "code_block_ocr", "figure_caption_ocr",
            "form_key_value_ocr", "skip_header_footer", "low_confidence_review"],
         "routing_features": ["layout_label", "confidence"], "verifiers": ["cell_structure_verifier"],
         "fallbacks": ["low_confidence_review"]},
        {"step": "region_crop_normalization", "possibilities": [
            "crop_exact_bbox", "crop_with_padding", "deskew_crop", "contrast_normalize", "binarize_crop",
            "resize_crop", "split_large_table_crop", "merge_adjacent_paragraph_crops", "encode_png_jpeg_webp",
            "hash_crop"],
         "routing_features": [], "verifiers": ["crop_hash_recorded"], "fallbacks": []},
        {"step": "ocr_recognition", "possibilities": [
            "tesseract", "paddleocr", "glm_ocr", "mistral_ocr", "azure_document_intelligence", "google_document_ai",
            "full_page_vlm_ocr", "region_level_vlm_ocr", "table_only_ocr", "formula_specific_ocr", "handwriting_ocr",
            "multi_model_voting", "ocr_with_human_review", "ocr_fallback_commercial"],
         "routing_features": ["region_type", "quality_budget"], "verifiers": ["ocr_confidence_estimate"],
         "fallbacks": ["ocr_fallback_commercial", "human_review"]},
        {"step": "ocr_postprocessing", "possibilities": [
            "preserve_raw_ocr", "normalize_whitespace", "repair_hyphenated_line_breaks", "remove_repeated_headers",
            "remove_repeated_footers", "normalize_bullets", "normalize_numbered_lists", "normalize_table_markdown",
            "normalize_math_symbols", "normalize_unicode", "detect_gibberish", "detect_repeated_text",
            "detect_missing_text"],
         "routing_features": [], "verifiers": ["raw_and_normalized_preserved"], "fallbacks": []},
        {"step": "reconstruction", "possibilities": [
            "plain_text", "markdown", "html", "json_layout", "alto_xml", "page_region_graph", "table_objects",
            "semantic_chunks", "knowledge_graph_nodes", "source_span_graph"],
         "routing_features": [], "verifiers": ["source_spans_preserved"], "fallbacks": []},
    ],
    "document_processing": [
        {"step": "structure_classification", "possibilities": [
            "invoice", "receipt", "contract", "policy_manual", "sop", "api_reference", "standard", "research_paper",
            "kaggle_notebook", "payer_policy", "insurance_form", "government_form", "technical_manual",
            "spreadsheet_export", "email_thread", "chat_transcript", "support_ticket_batch"],
         "routing_features": ["detected_objects"], "verifiers": [], "fallbacks": []},
        {"step": "semantic_classification", "possibilities": [
            "industry_classifier", "standard_classifier", "datatype_classifier", "persona_classifier",
            "process_stage_classifier", "operation_classifier", "risk_classifier", "side_effect_classifier",
            "compliance_classifier", "architecture_classifier", "source_authority_classifier",
            "primitive_yield_classifier"],
         "routing_features": ["content"], "verifiers": ["human_review_if_high_risk"], "fallbacks": ["human_review"]},
        {"step": "structural_extraction", "possibilities": [
            "extract_tables", "extract_key_value_pairs", "extract_form_fields", "extract_code_blocks",
            "extract_api_endpoints", "extract_request_schemas", "extract_response_schemas", "extract_error_codes",
            "extract_enum_values", "extract_examples", "extract_rules", "extract_decision_tables",
            "extract_workflow_steps", "extract_dates_versions", "extract_definitions", "extract_citations",
            "extract_parties", "extract_obligations", "extract_line_items"],
         "routing_features": ["object_type"], "verifiers": ["source_span_present"], "fallbacks": ["human_review"]},
        {"step": "chunking_indexing", "possibilities": [
            "fixed_token_chunking", "paragraph_chunking", "section_chunking", "heading_aware_chunking",
            "table_aware_chunking", "page_aware_chunking", "source_span_preserving_chunking", "semantic_chunking",
            "embedding_segmentation", "sliding_window", "hierarchical_chunking", "parent_child_chunks",
            "index_bm25", "index_dense", "index_hybrid"],
         "routing_features": ["chunk_type"], "verifiers": ["source_span_refs_preserved"], "fallbacks": []},
        {"step": "primitive_candidate_generation", "possibilities": [
            "parser", "validator", "normalizer", "mapper", "lookup", "schema", "api_wrapper", "browser_primitive",
            "ruleset", "workflow", "benchmark", "verifier", "anti_primitive", "human_review_form", "fallback_policy"],
         "routing_features": ["extracted_object_type"], "verifiers": ["candidate_boundary_gate"],
         "fallbacks": ["human_review"]},
        {"step": "anti_primitive_generation", "possibilities": [
            "anti_primitive_from_warning", "anti_primitive_from_exception", "anti_primitive_from_forbidden_action",
            "anti_primitive_from_common_error", "anti_primitive_from_leakage_pattern",
            "anti_primitive_from_security_warning"],
         "routing_features": ["warning_type"], "verifiers": [], "fallbacks": []},
    ],
    "ai_agent": [
        {"step": "request_intake", "possibilities": [
            "llm_intent_parser", "deterministic_form_intake", "workflow_template_selection", "classification_model",
            "keyword_rule_classifier", "conversation_memory_lookup", "session_context_resolver",
            "user_profile_resolver", "policy_context_resolver", "human_clarification"],
         "routing_features": ["ambiguity"], "verifiers": ["intent_schema_valid"], "fallbacks": ["human_clarification"]},
        {"step": "retrieval", "possibilities": [
            "exact_name_lookup", "keyword_bm25_search", "dense_embedding_search", "hybrid_search",
            "typed_edge_search", "schema_compatible_search", "source_domain_facet_search",
            "benchmark_score_filtered_search", "permission_filtered_search", "risk_filtered_search", "lsh_blocking",
            "reranking", "mcp_primitive_search"],
         "routing_features": ["query_class"], "verifiers": ["typed_edges_align"], "fallbacks": ["llm_planner"]},
        {"step": "route_planning_composition", "possibilities": [
            "exact_typed_edge_composer", "schema_cast_composer", "unit_conversion_composer", "field_mapping_composer",
            "llm_planner", "learned_route_planner", "cached_compiled_route", "human_designed_workflow",
            "workflow_template", "constraint_solver", "dag_compiler", "temporal_airflow_dagster_workflow"],
         "routing_features": ["edge_alignment"], "verifiers": ["schema_valid", "provenance_present"],
         "fallbacks": ["llm_planner"]},
        {"step": "tool_selection", "possibilities": [
            "pure_function", "local_deterministic_code", "database_query", "api_call", "browser_read_only",
            "browser_side_effect", "llm_extraction", "human_review", "workflow_engine", "batch_job", "streaming_job"],
         "routing_features": ["side_effects", "risk", "quality_sufficiency"],
         "verifiers": ["least_privilege"], "fallbacks": ["human_review"]},
        {"step": "execution", "possibilities": [
            "local_python", "typescript", "sql", "dbt", "duckdb", "spark", "container_job", "serverless_function",
            "workflow_engine", "browser_automation", "api_client", "mcp_tool", "cli_wrapper", "human_task",
            "llm_call_for_gap_only"],
         "routing_features": ["runtime"], "verifiers": ["output_hash_recorded"], "fallbacks": ["fallback_to_llm"]},
        {"step": "verification", "possibilities": [
            "json_schema_validation", "pydantic_validation", "sql_constraint_check", "unit_test", "golden_fixture",
            "negative_fixture", "deterministic_replay", "output_range_check", "source_span_check", "citation_check",
            "policy_check", "human_review", "llm_judge_secondary_only"],
         "routing_features": ["risk"], "verifiers": ["deterministic_replay"], "fallbacks": ["human_review"]},
        {"step": "fallback", "possibilities": [
            "retry_same_primitive", "switch_provider", "raise_dpi", "rerun_ocr", "use_commercial_api",
            "ask_one_human_question", "route_to_review", "call_llm_for_glue", "generate_candidate_primitive",
            "open_gap_record", "quarantine_output"],
         "routing_features": ["failure_class"], "verifiers": [], "fallbacks": ["open_gap_record"]},
    ],
    "ml_training": [
        {"step": "problem_framing", "possibilities": [
            "binary_classification", "multiclass_classification", "multilabel_classification", "regression",
            "ranking", "recommendation", "forecasting", "anomaly_detection", "clustering", "segmentation",
            "object_detection", "text_generation", "retrieval", "rag_evaluation", "survival_analysis",
            "causal_uplift", "reinforcement_learning"],
         "routing_features": ["target_type"], "verifiers": ["metric_defined"], "fallbacks": []},
        {"step": "data_acquisition", "possibilities": [
            "sql_extract", "csv_parquet_files", "warehouse_table", "data_lake", "api_sync", "cdc_stream",
            "event_logs", "kaggle_openml", "s3_gcs_azure", "feature_store", "document_corpus", "vector_store",
            "media_folders", "human_labels", "synthetic_data"],
         "routing_features": ["source"], "verifiers": ["dataset_hash", "data_contract_valid"], "fallbacks": []},
        {"step": "data_profiling", "possibilities": [
            "schema_profile", "missingness_report", "duplicate_report", "target_distribution",
            "feature_distributions", "train_test_drift", "outlier_report", "correlation_matrix",
            "mutual_information", "class_imbalance", "label_noise", "group_leakage", "time_leakage", "pii_scan"],
         "routing_features": [], "verifiers": ["no_leakage_detected"], "fallbacks": ["human_review"]},
        {"step": "cleaning_standardization", "possibilities": [
            "fill_mean_median_mode", "group_median_imputation", "knn_imputation", "drop_high_missingness",
            "clip_winsorize_outliers", "normalize_strings", "parse_dates", "parse_money", "normalize_units",
            "dedupe_rows", "resolve_entities", "remove_bad_labels", "redact_pii"],
         "routing_features": ["dtype"], "verifiers": ["schema_still_valid"], "fallbacks": []},
        {"step": "feature_engineering", "possibilities": [
            "numeric_ratios", "interactions", "polynomial_features", "bins", "log_transforms", "date_features",
            "cyclical_time_features", "lag_features", "rolling_windows", "group_aggregates", "target_encoding",
            "one_hot_encoding", "frequency_encoding", "text_tfidf", "text_embeddings", "image_embeddings",
            "geospatial_distance", "weather_census_enrichment", "graph_features", "model_derived_features"],
         "routing_features": ["dtype", "task_type"], "verifiers": ["no_target_leakage"],
         "fallbacks": ["drop_feature"]},
        {"step": "split_cv", "possibilities": [
            "random_split", "stratified_split", "group_split", "time_split", "rolling_origin_split",
            "purged_timeseries_split", "nested_cv", "kfold", "stratified_kfold", "group_kfold",
            "stratified_group_kfold", "leave_one_group_out", "holdout_benchmark_set"],
         "routing_features": ["has_groups", "is_temporal"], "verifiers": ["no_leakage_across_folds"],
         "fallbacks": []},
        {"step": "model_selection", "possibilities": [
            "dummy_baseline", "logistic_linear_regression", "ridge_lasso_elasticnet", "random_forest",
            "extra_trees", "xgboost", "lightgbm", "catboost", "tabpfn", "tabfm", "gandalf", "mlp", "cnn",
            "transformer", "arima_sarimax", "prophet_style", "nbeats_nhits", "matrix_factorization",
            "two_tower_recommender", "anomaly_detector", "autoencoder", "llm_classifier", "rag_pipeline"],
         "routing_features": ["task_type", "data_size", "latency_budget"], "verifiers": ["beats_baseline"],
         "fallbacks": ["dummy_baseline"]},
        {"step": "training", "possibilities": [
            "single_train_valid", "cross_validation_training", "distributed_training", "gpu_training", "tpu_training",
            "mixed_precision", "early_stopping", "checkpointing", "gradient_accumulation", "hyperparameter_search",
            "population_based_training", "automl", "seed_ensemble", "fold_ensemble"],
         "routing_features": ["compute_budget"], "verifiers": ["training_run_logged"], "fallbacks": []},
        {"step": "evaluation", "possibilities": [
            "holdout_score", "cv_mean_std", "oof_score", "slice_metrics", "confusion_matrix", "roc_auc", "pr_auc",
            "log_loss", "rmse_mae_rmsle", "map_ndcg_mrr", "dice_iou", "forecast_backtest", "calibration_curve",
            "fairness_slices", "robustness_tests", "latency_test", "cost_test", "drift_simulation"],
         "routing_features": ["task_type"], "verifiers": ["eval_report_attached"], "fallbacks": []},
        {"step": "model_registry", "possibilities": [
            "store_model_artifact", "store_preprocessing_artifact", "store_feature_set_version",
            "store_dataset_snapshot", "store_training_code_hash", "store_hyperparameters", "store_metrics",
            "store_model_card", "store_approval_state", "store_deployment_alias"],
         "routing_features": [], "verifiers": ["model_card_present"], "fallbacks": []},
    ],
    "evaluation": [
        {"step": "benchmark_task_definition", "possibilities": [
            "unit_test", "golden_fixture", "hidden_fixture", "randomized_seeded_fixture", "mutation_test",
            "sandbox_task", "kaggle_hidden_labels", "agent_task", "browser_task", "api_task",
            "document_extraction_task", "route_composition_task", "security_task"],
         "routing_features": ["task_family"], "verifiers": ["deterministic_verifier_command"],
         "fallbacks": ["human_review"]},
        {"step": "evaluation_modes", "possibilities": [
            "no_primitives_baseline", "curated_primitives", "generated_primitives", "compiled_artifact",
            "runtime_llm", "hybrid_with_fallback", "human_baseline", "commercial_api_baseline",
            "old_production_primitive", "new_candidate_primitive"],
         "routing_features": [], "verifiers": ["hidden_tests", "leakage_audit", "pinned_dependencies"],
         "fallbacks": []},
        {"step": "metrics", "possibilities": [
            "pass_rate", "exact_correctness", "partial_correctness", "deterministic_reproducibility", "token_usage",
            "runtime_cost", "compile_time_cost", "break_even_transaction_count", "latency_p50_p95_p99",
            "human_review_rate", "fallback_rate", "verifier_coverage", "security_failures", "regression_count",
            "benchmark_lift", "candidate_count", "useful_candidate_rate", "executor_certified_per_million_tokens"],
         "routing_features": ["domain"], "verifiers": [], "fallbacks": []},
    ],
    "serving": [
        {"step": "request_intake", "possibilities": [
            "rest_api", "graphql", "batch_file", "stream_event", "webhook", "browser_action", "mcp_tool_call",
            "cli", "ui_form", "scheduled_job", "human_review_queue"],
         "routing_features": ["channel"], "verifiers": ["request_schema_valid", "authn", "authz"],
         "fallbacks": ["reject"]},
        {"step": "route_selection", "possibilities": [
            "exact_compiled_route", "cached_route", "typed_edge_composition", "schema_cast_composition",
            "primitive_search_plus_llm_planner", "workflow_template", "manual_route", "fallback_route"],
         "routing_features": ["edge_alignment"], "verifiers": ["route_valid"], "fallbacks": ["fallback_route"]},
        {"step": "runtime_execution", "possibilities": [
            "pure_deterministic_code", "rules_engine", "sql_query", "feature_store_lookup", "model_inference",
            "llm_call", "api_call", "browser_workflow", "workflow_engine", "human_approval", "batch_queue",
            "stream_processor"],
         "routing_features": ["primitive_kind"], "verifiers": ["output_hash"], "fallbacks": ["human_approval"]},
        {"step": "output_validation", "possibilities": [
            "json_schema", "pydantic", "business_rule_check", "range_check", "enum_check", "source_span_check",
            "citation_check", "policy_check", "toxicity_safety_check", "pii_leakage_check", "contract_check",
            "human_review"],
         "routing_features": ["risk"], "verifiers": ["validation_passed"], "fallbacks": ["human_review"]},
        {"step": "monitoring", "possibilities": [
            "logs", "metrics", "traces", "token_ledger", "latency", "cost", "error_rate", "fallback_rate",
            "human_override_rate", "quality_score", "data_drift", "model_drift", "schema_drift", "source_drift",
            "route_composition_success", "primitive_regression"],
         "routing_features": [], "verifiers": [], "fallbacks": ["trigger_retraining", "trigger_reingestion"]},
    ],
}

# ── one fully-worked RICH method example (owner §9), proving the cost/quality/failure_modes shape ────────────
RICH_METHOD_EXAMPLE: dict[str, Any] = {
    "step_id": "document_ingestion.layout_detection",
    "goal": "Detect page regions and reading order.",
    "possible_methods": [
        {"method": "rule_based_layout", "best_for": ["simple digital PDFs"], "cost": "low", "quality": "medium",
         "failure_modes": ["multi_column", "complex_tables"]},
        {"method": "pp_doclayout_v3", "best_for": ["complex layouts", "tables", "mixed regions"], "cost": "medium",
         "quality": "high", "failure_modes": ["unusual_scans", "handwriting"]},
        {"method": "commercial_document_ai", "best_for": ["managed SLA", "forms"], "cost": "high",
         "quality": "high", "failure_modes": ["cost", "vendor_lock_in"]},
    ],
    "routing_features": ["page_class", "table_density", "scan_quality", "source_trust", "cost_budget"],
    "verifiers": ["region_coverage_score", "reading_order_score", "table_fidelity_score"],
    "fallbacks": ["full_page_ocr", "higher_dpi_render", "human_review"],
}

# ── the universal pattern across all workflows (owner §10) ───────────────────────────────────────────────────
UNIVERSAL_PATTERN: list[str] = [
    "classify_cheaply", "route_intelligently", "preserve_raw_evidence", "transform_into_typed_objects",
    "generate_candidates", "verify_deterministically", "promote_only_with_proof", "serve_through_typed_routes",
    "monitor_everything", "feed_failures_into_new_gaps",
]


def total_possibilities() -> int:
    return sum(len(s["possibilities"]) for steps in DOMAIN_STEPS.values() for s in steps)


def build_candidate_cards() -> list[dict[str, Any]]:
    """Explode every (domain, step, possibility) into a candidate primitive — scaling raw count (owner law)."""
    cards: list[dict[str, Any]] = []
    for domain, steps in DOMAIN_STEPS.items():
        for step in steps:
            step_id = f"{domain}.{step['step']}"
            for method in step["possibilities"]:
                cid = canonical_id(ATLAS_ID_PREFIX, domain, step["step"], method)
                cards.append({
                    "record_type": "process_possibility_primitive_candidate",
                    "kind": "process_step_method",
                    "card_id": cid, "primitive_id": cid,
                    "title": f"{step_id} :: {method}",
                    "blackbox": f"Method '{method}' for step '{step['step']}' in the {domain} process. One option "
                                f"in the step's zoo; routes by {step.get('routing_features') or 'context'}.",
                    "domain": domain, "step": step["step"], "method": method,
                    "blocking_keys": sorted({domain, step["step"], method, "process_atlas"}),
                    "domains": [domain, "process_atlas", step["step"]],
                    "candidate": True, "serves_truth": False,
                    "routing_features": step.get("routing_features", []),
                    "verifiers": step.get("verifiers", []),
                    "fallbacks": step.get("fallbacks", []),
                    "composition_hints": {"candidate_only": True, "serves_truth": False,
                                          "consumes_edge": f"{step['step']}Input",
                                          "produces_edge": f"{step['step']}Output"},
                    "packaged_at": PACKAGED_AT,
                })
    return cards


def build_spec() -> dict[str, Any]:
    spec_id = canonical_id(ATLAS_ID_PREFIX, "spec", str(len(DOMAIN_STEPS)), str(total_possibilities()))
    return {
        "record_type": "process_possibility_atlas",
        "spec_id": spec_id,
        "title": "Step x layer x possibility atlas — every possibility is a primitive candidate (scale raw count)",
        "master_layers": MASTER_LAYERS,
        "implementation_kinds": IMPLEMENTATION_KINDS,
        "possibility_schema_fields": POSSIBILITY_SCHEMA_FIELDS,
        "domains": {d: {"steps": [s["step"] for s in steps], "n_steps": len(steps),
                        "n_possibilities": sum(len(s["possibilities"]) for s in steps)}
                    for d, steps in DOMAIN_STEPS.items()},
        "n_domains": len(DOMAIN_STEPS),
        "n_steps_total": sum(len(v) for v in DOMAIN_STEPS.values()),
        "n_possibilities_total": total_possibilities(),
        "rich_method_example": RICH_METHOD_EXAMPLE,
        "universal_pattern": UNIVERSAL_PATTERN,
        "raw_count_law": "every possibility is a first-class candidate; scale count, test at scale against "
                         "billions/trillions of prompts, route usefulness non-destructively.",
        "how_to_extend": "add a possibility to a step, a step to a domain, or a new domain — one row each.",
        "packaged_at": PACKAGED_AT,
        **BOUNDARY,
    }


def emit() -> dict[str, Any]:
    spec = build_spec()
    cards = build_candidate_cards()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / SPEC_FILENAME).write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    with (out_dir / CARDS_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"spec_path": str(out_dir / SPEC_FILENAME), "cards_path": str(out_dir / CARDS_FILENAME),
            "n_domains": spec["n_domains"], "n_steps": spec["n_steps_total"],
            "n_candidate_primitives": len(cards)}


def self_test() -> bool:
    """Mutation-gated: a step with <2 possibilities (not a zoo), a missing schema field, or a lost boundary bit
    goes RED. Raw count is a GOAL — the test asserts the atlas GENERATES many candidates, never caps them."""
    # (1) six process domains present.
    for d in ("document_ingestion", "document_processing", "ai_agent", "ml_training", "evaluation", "serving"):
        assert d in DOMAIN_STEPS, f"missing domain {d}"

    # (2) every step is a ZOO (>=2 possibilities) and carries the possibility-schema shape.
    for domain, steps in DOMAIN_STEPS.items():
        for s in steps:
            assert len(s["possibilities"]) >= 2, f"{domain}.{s['step']} is not a zoo (<2 options)"
            for key in ("routing_features", "verifiers", "fallbacks"):
                assert key in s, f"{domain}.{s['step']} missing schema field {key}"

    # (3) the rich example carries the full method shape (cost/quality/failure_modes).
    for m in RICH_METHOD_EXAMPLE["possible_methods"]:
        for f in ("method", "best_for", "cost", "quality", "failure_modes"):
            assert f in m, f"rich method missing {f}"

    # (4) raw count: the atlas explodes into MANY candidates (a scaling goal, never capped).
    cards = build_candidate_cards()
    n = total_possibilities()
    assert len(cards) == n and n >= 150, f"expected >=150 candidate primitives, got {n}"
    ids = [c["card_id"] for c in cards]
    assert len(set(ids)) == len(ids), "duplicate candidate ids"
    for c in cards:
        assert c["candidate"] is True and c["serves_truth"] is False

    # (5) master model + universal pattern present; spec candidate-only + deterministic.
    assert len(MASTER_LAYERS) == 10 and len(UNIVERSAL_PATTERN) == 10
    spec = build_spec()
    assert spec["candidate"] is True and spec["serves_truth"] is False
    assert build_spec()["spec_id"] == spec["spec_id"]

    print(f"OK process_possibility_atlas self-test: {len(DOMAIN_STEPS)} domains, {spec['n_steps_total']} steps, "
          f"{n} possibilities -> {len(cards)} candidate primitives (raw count SCALES; not capped), serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Step x layer x possibility atlas -> candidate primitives.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.stats:
        spec = build_spec()
        print(json.dumps({"domains": spec["domains"], "n_steps": spec["n_steps_total"],
                          "n_possibilities": spec["n_possibilities_total"]}, indent=2))
        return
    if args.show:
        print(json.dumps(build_spec(), indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
