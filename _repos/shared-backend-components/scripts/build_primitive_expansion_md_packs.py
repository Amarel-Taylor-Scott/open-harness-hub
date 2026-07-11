#!/usr/bin/env python3
"""Deterministic Markdown primitive expansion pack generator.

Owner-specified methodology (2026-07-01 session): dimension-driven
deterministic generation — curated dimension lists, modular prime-multiplier
cross-products with uniqueness, compact edge templates, proof/effects/
source-ref-family fields, strict candidate flags, validation, index, and a
computed manifest. No hand-written rows; no random generation.

Packs are CANDIDATE ATLASES, not truth registries. Rows exist to create search
recipes, source-adapter backlogs, primitive-demand hypotheses, route-planning
dimensions, benchmark adapter records, proof obligations, telemetry fields,
and strategy-tournament candidates. Every row keeps candidate=true /
serves_truth=false; promotion requires source refs, license/policy review,
contract validation, side-effect declaration, tests/receipts, privacy review,
and runtime profile — enforced elsewhere, never here.

Outputs (single source = this builder; never hand-edit):
    generated_primitive_packs/<pack>.md          one Markdown table per pack
    generated_primitive_packs/primitive_generated_pack_index.md
    generated_primitive_packs/manifest.json      computed counts + sha256
Use --check to re-validate written packs against the manifest (drift goes red).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

OUT_DIR_NAME = "generated_primitive_packs"
BASE_PROOFS = (
    "source_ref_resolution",
    "license_policy_review",
    "input_contract_validation",
    "output_contract_validation",
    "side_effect_declaration",
)
SOURCE_REF_STATUS = "required_before_promotion"

# ── shared dimension libraries (curated, reused across packs) ──
INDUSTRIES = [
    "healthcare", "financial_services", "insurance", "retail_ecommerce", "manufacturing", "logistics",
    "real_estate", "legal_compliance", "government", "education", "energy_utilities", "telecom",
    "media_entertainment", "agriculture_food", "construction", "transportation", "hospitality",
    "nonprofit", "cybersecurity", "saas_devtools",
]
ROLES = [
    "data_engineer", "backend_engineer", "frontend_engineer", "ml_engineer", "sre", "security_engineer",
    "gis_analyst", "compliance_analyst", "procurement_analyst", "product_manager", "support_engineer",
    "research_analyst",
]
BUSINESS_OBJECTS = [
    "customer", "order", "invoice", "payment", "product", "claim", "ticket", "contract", "shipment",
    "patient_directory_entry", "provider", "job_posting", "grant", "permit", "facility", "dataset",
]
SCHEMA_STANDARDS = [
    "schema_org", "json_schema", "openapi", "asyncapi", "fhir", "xbrl", "gs1", "gtfs", "geojson",
    "dcat", "csvw", "custom_canonical",
]
DATA_SHAPES = [
    "json_nested_object", "csv_wide_table", "csv_long_table", "event_stream", "document_pdf",
    "html_page", "parquet_columnar", "sql_table", "graph_edges", "embedding_vectors",
]
TRANSFORMS = [
    "extract", "validate", "normalize", "dedupe", "reconcile", "classify", "score", "sync",
    "enrich", "redact", "summarize_with_receipt", "route",
]
RUNTIME_SHAPES = [
    "local_python", "api_endpoint", "queue_worker", "cloud_function", "kubernetes_job",
    "workflow_step", "cli_command", "mcp_tool", "browser_worker", "cron_job",
]
PROOF_ROTATION = [
    "schema_validation", "fixture_test", "contract_test", "source_span_receipt", "idempotency_test",
    "row_count_check", "dry_run_receipt", "golden_output_test",
]
SOURCE_SURFACES = [
    "openapi_specs", "asyncapi_specs", "mcp_registry", "pypi_packages", "npm_packages", "github_repos",
    "github_actions", "terraform_registry", "helm_charts", "kubernetes_crds", "n8n_templates",
    "zapier_integrations", "make_templates", "pipedream_components", "kaggle_competitions",
    "huggingface_hub", "sec_edgar", "government_data_portals", "cloud_marketplaces", "app_stores",
    "engineering_blogs", "runbooks", "standards_bodies", "benchmark_suites",
]
SEARCH_LENSES = [
    "api_examples", "schema_definitions", "error_messages", "workflow_templates", "test_fixtures",
    "rate_limit_docs", "auth_scopes", "changelog_deprecations", "dataset_catalogs", "integration_guides",
]
GENERATION_PATHS = [
    "source_adapter_extract", "marketplace_listing_extract", "benchmark_task_demand_extract",
    "trace_to_workflow_mine", "workflow_template_mine", "repo_symbol_surface_extract",
    "schema_to_primitive_emit", "human_curated_seed", "model_draft_candidate", "negative_memory_to_gap",
]
SEARCH_PATHS = [
    "exact_edge_search", "type_compatible_edge_search", "schema_contract_search", "bm25_search",
    "embedding_similarity_search", "hybrid_search", "graph_route_search", "benchmark_task_search",
    "negative_memory_search", "runtime_shape_search", "proof_requirement_search",
]
ROUTE_PLANNERS = [
    "exact_route_lookup", "template_slot_fill", "deterministic_graph_search", "contract_diff_remix",
    "llm_plan_delta", "tree_or_graph_of_routes", "mcts_route_search", "evolutionary_route_search",
    "trace_replay_compile", "human_review_route",
]
COMPILE_TARGETS = [
    "planlock_json", "python_callable", "typescript_function", "fastapi_endpoint", "mcp_tool_wrapper",
    "cli_command", "queue_consumer", "airflow_task", "dbt_model", "sql_view",
    "browser_automation_script", "kubernetes_job",
]
RANKING_METRICS = [
    "proof_strength", "contract_fit", "source_authority", "runtime_llm_tokens",
    "source_escalation_depth", "route_reuse_count", "effect_risk", "negative_memory_risk",
]
GUARDRAIL_FAMILIES = [
    "prompt_injection_detect", "jailbreak_phrase_gate", "pii_redact", "secret_detect",
    "tenant_boundary_gate", "rag_source_allowlist", "citation_required_gate", "groundedness_threshold",
    "tool_schema_validate", "tool_allowlist_gate", "action_amount_limit", "human_approval_gate",
    "idempotency_required_gate", "data_export_gate", "disclaimer_required", "output_schema_gate",
    "decision_receipt_emit", "policy_version_pin",
]
CLOUD_RUNTIMES = [
    "aws_lambda", "google_cloud_run", "azure_functions", "kubernetes_sidecar", "knative_service",
    "envoy_ext_authz", "api_gateway_middleware", "mcp_prehook", "queue_worker", "fastapi_middleware",
    "ci_cd_gate", "browser_agent_proxy",
]
DEPLOYMENT_SHAPES = [
    "sidecar", "gateway", "middleware_library", "serverless_function", "standalone_service",
    "admission_controller", "prehook", "batch_scanner", "stream_processor", "sdk_wrapper",
]
POLICY_BACKENDS = [
    "open_policy_agent_rego", "cedar_policy", "deterministic_rule_pack", "provider_managed_guardrail",
    "json_schema_validator", "allowlist_table", "threshold_policy", "dual_control_policy",
]
INPUT_SURFACES = [
    "user_prompt", "retrieved_context_bundle", "proposed_tool_call", "model_draft_output",
    "uploaded_document", "webhook_payload", "agent_shell_command", "sql_query_text",
    "outbound_email_draft", "browser_action_plan",
]
DECISION_ACTIONS = [
    "allow", "block", "redact", "rewrite_with_receipt", "route_to_review", "require_approval",
    "require_citation", "log_only",
]
MARKETPLACES = [
    "aws_marketplace", "google_cloud_marketplace", "microsoft_marketplace", "aws_serverless_repo",
    "terraform_registry", "pulumi_registry", "cdk_construct_hub", "artifact_hub", "operatorhub",
    "docker_hub", "github_actions_marketplace", "mcp_registry", "postman_api_network", "apis_guru",
    "mulesoft_exchange", "n8n_library", "zapier_directory", "pipedream_registry",
    "huggingface_hub", "snowflake_marketplace",
]
LISTING_TYPES = [
    "saas_api_product", "container_image", "iac_module", "workflow_template", "agent_tool",
    "model_endpoint", "dataset_product", "operator_controller", "action_step", "sdk_package",
]
CAPABILITY_FAMILIES = [
    "record_import", "entity_enrichment", "notification_routing", "document_extraction",
    "payment_reconciliation", "inventory_sync", "lead_scoring", "compliance_screening",
    "report_generation", "media_transcode", "search_indexing", "identity_resolution",
    "monitoring_alerting", "deployment_automation",
]
PACKAGE_REGISTRIES = [
    "pypi", "npm", "crates_io", "maven_central", "go_modules", "rubygems", "nuget", "packagist",
    "conda_forge", "homebrew",
]
PACKAGE_DOMAINS = [
    "http_clients", "data_validation", "dataframe_processing", "orm_database", "auth_security",
    "file_parsing", "image_processing", "geospatial", "nlp_text", "queue_messaging", "caching",
    "serialization", "cli_frameworks", "testing_tools", "observability", "workflow_orchestration",
]
SURFACE_TYPES = [
    "public_functions", "cli_entrypoints", "class_methods", "config_schemas", "test_fixtures",
    "usage_examples", "type_stubs", "error_taxonomies", "plugin_hooks", "migration_scripts",
]
EXTRACTION_OBJECTIVES = [
    "edge_contract_cards", "error_model_cards", "auth_requirement_cards", "pagination_pattern_cards",
    "rate_limit_cards", "fixture_seed_cards", "composition_affinity_edges", "deprecation_watch_cards",
    "capability_summary_cards", "proof_obligation_cards",
]
SPEC_FAMILIES = ["openapi", "asyncapi", "graphql", "grpc"]
OPERATION_KINDS = [
    "list_collection", "get_by_id", "create_resource", "update_resource", "delete_resource",
    "search_query", "batch_operation", "subscribe_events", "stream_results", "webhook_callback",
]
AUTH_SCHEMES = [
    "api_key_header", "oauth2_client_credentials", "oauth2_authorization_code", "bearer_jwt",
    "basic_auth", "mtls", "signed_request", "no_auth_public",
]
PAGINATION_MODELS = ["cursor", "offset_limit", "page_number", "link_header", "token_continuation", "none"]
ERROR_MODELS = [
    "problem_json", "envelope_code_message", "http_status_only", "graphql_errors_array",
    "grpc_status_codes", "custom_error_taxonomy",
]
DS_TASK_FAMILIES = [
    "tabular_classification", "tabular_regression", "time_series_forecast", "nlp_classification",
    "computer_vision", "recommendation", "anomaly_detection", "clustering", "ranking",
    "uplift_modeling", "survival_analysis", "graph_learning", "optimization", "simulation",
]
DS_METHOD_STEPS = [
    "dataset_profile", "target_leakage_scan", "split_policy_bind", "baseline_model_fit",
    "feature_engineering_pass", "cross_validation_run", "hyperparameter_search", "metric_parse",
    "error_analysis", "calibration_check", "submission_format_validate", "experiment_receipt_emit",
    "ensemble_blend", "model_card_emit", "repro_package_build", "drift_monitor_bind",
]
DS_METRICS = [
    "auc_roc", "f1_macro", "rmse", "mae", "mape", "log_loss", "ndcg_at_k", "recall_at_k",
    "precision_at_k", "r2", "silhouette", "profit_curve",
]
SITE_CATEGORIES = [
    "government_portal", "company_directory", "product_catalog", "job_board", "news_archive",
    "documentation_site", "support_center", "regulatory_register", "court_records", "tender_portal",
    "real_estate_listings", "event_calendar", "provider_directory", "statistics_dashboard",
    "open_data_portal", "standards_library",
]
EXTRACTION_TARGETS = [
    "structured_entity_records", "table_rows", "document_downloads", "contact_details",
    "price_and_availability", "schedule_and_hours", "schema_org_jsonld", "pagination_full_sweep",
    "change_detection_diff", "citation_spans", "form_submission_receipt", "media_assets",
]
NAVIGATION_PATTERNS = [
    "static_html_get", "paginated_listing_walk", "search_form_submit", "infinite_scroll_capture",
    "login_gated_session", "sitemap_seeded_crawl", "api_behind_page_discovery", "headless_render_wait",
    "download_queue_drain", "robots_respectful_throttle",
]
FRAGILITY_GUARDS = [
    "selector_drift_detector", "layout_change_alarm", "rate_limit_backoff", "captcha_stop_gate",
    "terms_of_service_gate", "snapshot_hash_receipt", "retry_idempotency_key", "source_freshness_stamp",
    "attribution_receipt", "pii_boundary_filter",
]
CORPUS_TYPES = [
    "product_docs", "api_references", "policy_manuals", "contract_repository", "support_tickets",
    "research_papers", "regulatory_filings", "code_repositories", "meeting_transcripts",
    "knowledge_base_articles", "catalog_records", "mixed_multilingual",
]
CHUNKERS = [
    "fixed_token_window", "semantic_boundary", "heading_hierarchy", "sentence_group", "code_symbol_aware",
    "table_preserving", "layout_block", "recursive_split",
]
RETRIEVERS = [
    "bm25", "dense_biencoder", "hybrid_rrf", "hyde_expansion", "colbert_late_interaction",
    "splade_sparse_expansion", "graph_neighborhood", "metadata_filtered_dense", "multi_query_fusion",
    "parent_document", "time_weighted", "source_authority_boosted",
]
RERANKERS = [
    "cross_encoder", "llm_judge_bounded", "mmr_diversity", "freshness_boost", "authority_boost",
    "negative_memory_suppression", "citation_coverage_rank", "none_passthrough",
]
GROUNDING_GATES = [
    "citation_required", "source_span_verify", "no_source_no_answer", "conflicting_source_escalate",
    "freshness_threshold", "confidence_abstain", "human_review_route", "answer_schema_validate",
]
RAG_EVALS = [
    "retrieval_recall_at_k", "context_precision", "answer_faithfulness", "citation_accuracy",
    "abstention_correctness", "latency_budget", "token_budget", "regression_replay",
]
IAC_FAMILIES = [
    "terraform_module", "pulumi_component", "cloudformation_stack", "cdk_construct", "helm_chart",
    "kustomize_overlay", "ansible_playbook", "github_actions_workflow", "argo_workflow", "crossplane_composition",
]
RESOURCE_FAMILIES = [
    "vpc_networking", "object_storage", "managed_database", "queue_topic", "serverless_function",
    "container_service", "kubernetes_cluster", "iam_policy", "secret_store", "cdn_distribution",
    "monitoring_alarm", "dns_zone", "load_balancer", "scheduler_job",
]
ENVIRONMENTS = ["dev", "staging", "production", "multi_region", "single_tenant", "multi_tenant"]
SAFETY_GATES = [
    "plan_diff_review", "policy_as_code_check", "cost_estimate_gate", "drift_detection",
    "secret_boundary_scan", "least_privilege_review", "rollback_plan_required", "canary_deploy_gate",
    "change_window_gate", "dual_approval",
]
SIGNAL_FAMILIES = [
    "latency_p99", "error_rate", "saturation_cpu_memory", "queue_depth", "cost_anomaly",
    "log_error_burst", "trace_span_outlier", "synthetic_probe_fail", "security_alert", "data_quality_breach",
    "cache_hit_drop", "deploy_regression",
]
DETECTORS = [
    "static_threshold", "dynamic_baseline", "seasonal_decompose", "outlier_zscore", "burn_rate_slo",
    "changepoint_detect", "correlation_cluster", "topology_aware_rollup", "budget_burn_alert",
    "ml_anomaly_score",
]
TRIAGE_STEPS = [
    "blast_radius_map", "recent_change_diff", "dependency_health_walk", "log_slice_extract",
    "trace_exemplar_pull", "runbook_match", "owner_page_route", "mitigation_action_gate",
    "postmortem_seed_emit", "status_page_update",
]
RUNBOOK_ARTIFACTS = [
    "diagnostic_checklist", "mitigation_plan", "rollback_recipe", "escalation_packet",
    "incident_timeline", "customer_comms_draft", "postmortem_template", "slo_impact_report",
]
ESCALATIONS = ["auto_remediate", "oncall_page", "team_channel_alert", "manager_escalate", "vendor_ticket", "log_only"]
COMPANY_SURFACES = [
    "homepage", "product_pages", "developer_docs", "investor_relations", "sec_filings", "careers_pages",
    "support_docs", "app_marketplace_listing", "structured_data_jsonld", "rss_changelog",
    "github_organization", "press_releases", "pricing_pages", "partner_directory",
]
ENTITY_TYPES = [
    "organization", "product", "offer", "job_posting", "executive_person", "subsidiary",
    "financial_metric", "risk_factor", "customer_segment", "partner", "api_capability",
    "office_location", "patent_reference", "regulatory_event", "press_event", "support_workflow",
]
OUTPUT_ARTIFACTS = [
    "canonical_entity_record", "metric_panel", "citation_digest", "coverage_map", "change_watch_feed",
    "candidate_bundle", "risk_digest", "comparison_table", "graph_edges_export", "review_packet",
]
COMPARISON_ARMS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
SCORECARD_METRICS = [
    "task_success", "tokens_to_plan", "tokens_to_pass", "runtime_llm_tokens", "source_context_tokens",
    "depth_to_solution", "compile_success", "proof_success", "route_reuse", "negative_memory_created",
    "cost_per_success", "wall_clock_latency",
]
PRIMITIVE_DEMANDS = [
    "tool_schema_validate", "tool_select", "argument_bind", "abstain_when_no_safe_tool",
    "state_transition_plan", "document_field_extract", "line_item_group", "repo_patch_plan",
    "terminal_command_plan", "dataset_profile", "metric_parse", "citation_span_verify",
    "receipt_emit", "negative_memory_write",
]
# Seed benchmarks from the owner's Kaggle benchmark-hub paste (2026-07-01). The
# hub lists 1,030+ benchmarks; these named rows are SEEDS — the full hub is a
# pending source-adapter harvest (see research queue), never a completed claim.
KAGGLE_BENCHMARKS = [
    "enterprise_operations_bench", "chess_suite", "itbench", "facts_benchmark_suite",
    "heads_up_poker", "parsebench_doc_ocr", "chess_fen_pgn", "wwtp_engineering_benchmark",
    "lewis_carroll_sorites_logic", "game_arena", "eclektic_cross_lingual", "icml_2025_experts",
    "kaggle_task_tuesday", "learningbench", "scicode", "global_mmlu_lite",
    "kaggle_hub_unnamed_family_seed_a", "kaggle_hub_unnamed_family_seed_b",
    "kaggle_hub_unnamed_family_seed_c", "kaggle_hub_unnamed_family_seed_d",
]
BENCHMARK_TASK_TYPES = [
    "function_tool_routing", "document_extraction", "repo_repair", "terminal_workflow",
    "api_state_transition", "data_science_pipeline", "game_strategic_reasoning",
    "probabilistic_imperfect_information", "multilingual_qa", "factual_grounding",
    "domain_engineering_reasoning", "multi_step_logic_deduction",
]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def md_escape(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").replace("\r", " ").replace("\t", " ")


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "::".join(str(part) for part in parts)
    return f"{prefix}:{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def pick(values: list[str], index: int, multiplier: int) -> str:
    return values[(index * multiplier) % len(values)]


def cc(value: str) -> str:
    return "".join(word.capitalize() for word in re.findall(r"[a-zA-Z0-9]+", value))


def proofs_for(pack_extras: list[str], index: int) -> str:
    rotating = pick(PROOF_ROTATION, index, 17)
    ordered: list[str] = list(BASE_PROOFS) + pack_extras + [rotating, "candidate_boundary_gate"]
    seen: set[str] = set()
    unique = [item for item in ordered if not (item in seen or seen.add(item))]
    return "; ".join(unique)


LENS_QUERY_TEMPLATES: dict[str, str] = {
    "api_examples": "{industry} {object} API examples {surface} request response schema",
    "schema_definitions": "{industry} {object} schema definition {surface} required fields",
    "error_messages": "{surface} {object} error message taxonomy retry {industry}",
    "workflow_templates": "{industry} {object} workflow template {surface} steps receipts",
    "test_fixtures": "{object} test fixtures {surface} sample data {industry}",
    "rate_limit_docs": "{surface} rate limits quotas {object} api {industry}",
    "auth_scopes": "{surface} auth scopes permissions {object} api {industry}",
    "changelog_deprecations": "{surface} changelog deprecation {object} api version {industry}",
    "dataset_catalogs": "{industry} {object} dataset catalog download schema {surface}",
    "integration_guides": "{industry} {object} integration guide {surface} setup mapping",
}


# ── pack spec engine ──
PackBuilder = Callable[[dict[str, str], int, str], dict[str, Any]]


def _coprime_multiplier(length: int) -> int:
    # Scramble each mixed-radix digit with a multiplier coprime to the axis
    # length: a bijection per axis, so full Cartesian coverage survives while
    # adjacent rows stop looking repetitive.
    for prime in (7, 11, 13, 17, 19, 23, 29, 31, 3, 5, 1):
        if length % prime != 0 or prime == 1:
            return prime
    return 1


def generate_rows(pack_id: str, dims: list[tuple[str, list[str], int]], target: int, build: PackBuilder) -> list[dict[str, Any]]:
    # Mixed-radix (odometer) enumeration over the dimension axes: combo(i) is
    # unique for i < capacity, so row counts are honest — no lockstep aliasing.
    lengths = [len(values) for _, values, _ in dims]
    capacity = 1
    for length in lengths:
        capacity *= length
    scramblers = [_coprime_multiplier(length) for length in lengths]
    rows: list[dict[str, Any]] = []
    for i in range(min(target, capacity)):
        combo: dict[str, str] = {}
        quotient = i
        for axis, (name, values, _) in enumerate(dims):
            digit = quotient % lengths[axis]
            quotient //= lengths[axis]
            combo[name] = values[(digit * scramblers[axis]) % lengths[axis]]
        record_id = stable_id(pack_id, "::".join(combo[name] for name, _, _ in dims))
        row = build(combo, len(rows) + 1, record_id)
        row["candidate"] = "true"
        row["serves_truth"] = "false"
        rows.append(row)
    return rows


def _variant_common(pack_id: str, combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
    return {"row_id": row_id, "record_id": record_id, "pack_id": pack_id}


def build_pack_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def spec(pack_id: str, title: str, purpose: str, target: int, columns: list[str],
             dims: list[tuple[str, list[str], int]], build: PackBuilder) -> None:
        specs.append({
            "pack_id": pack_id,
            "filename": f"primitive_{pack_id}_pack.md",
            "title": title,
            "purpose": purpose,
            "target_rows": target,
            "columns": columns + ["candidate", "serves_truth"],
            "dims": dims,
            "build": build,
        })

    # 1 ── search query recipes
    def build_query(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        template = LENS_QUERY_TEMPLATES[combo["search_lens"]]
        query = template.format(industry=combo["industry"].replace("_", " "),
                                object=combo["business_object"].replace("_", " "),
                                surface=combo["source_surface"].replace("_", " "))
        return {
            **_variant_common("search_query_recipes", combo, row_id, record_id),
            **combo,
            "search_query": query,
            "what_to_extract": pick(EXTRACTION_OBJECTIVES, row_id, 7),
            "expected_input_edge": f"{cc(combo['source_surface'])}Target+{cc(combo['search_lens'])}Policy",
            "expected_output_edge": f"{cc(combo['business_object'])}SourceCandidateSet+SourceEvidenceReceipt",
            "source_ref_policy": SOURCE_REF_STATUS,
            "proof_requirements": proofs_for(["source_span_receipt"], row_id),
        }

    spec("search_query_recipes", "Search Query Recipe Pack",
         "Source-discovery search prompts for source scouts and crawler queues: role x industry x object x surface x lens.",
         10000,
         ["row_id", "record_id", "pack_id", "industry", "role", "business_object", "source_surface",
          "search_lens", "search_query", "what_to_extract", "expected_input_edge", "expected_output_edge",
          "source_ref_policy", "proof_requirements"],
         [("industry", INDUSTRIES, 1), ("role", ROLES, 3), ("business_object", BUSINESS_OBJECTS, 5),
          ("source_surface", SOURCE_SURFACES, 7), ("search_lens", SEARCH_LENSES, 11)],
         build_query)

    # 2 ── public company surface/entity tensor
    def build_company(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("public_company_surface_entity_tensor", combo, row_id, record_id),
            **combo,
            "title": f"{combo['industry']} {combo['entity_type']} from {combo['company_surface']} ({combo['transform']})",
            "input_edge": f"Company{cc(combo['company_surface'])}+{cc(combo['entity_type'])}ExtractionPolicy",
            "output_edge": f"{cc(combo['output_artifact'])}+SourceSpanReceipt",
            "known_implementation_families": "Playwright/Scrapy; Pydantic/JSON Schema; Pandas/DuckDB; OpenTelemetry",
            "source_ref_families": "SEC_EDGAR; Schema.org; official_docs; GitHub_repo; government_data_portal",
            "effects": "network_read; artifact_write",
            "proof_requirements": proofs_for(["source_span_receipt", "privacy_boundary_review"], row_id),
        }

    spec("public_company_surface_entity_tensor", "Public Company Surface / Entity Tensor",
         "Company-surface interrogation variants: which entities to extract from which public company surfaces, per industry, schema, shape, and transform.",
         6000,
         ["row_id", "record_id", "pack_id", "company_surface", "industry", "entity_type", "schema_standard",
          "data_shape", "transform", "output_artifact", "title", "input_edge", "output_edge",
          "known_implementation_families", "source_ref_families", "effects", "proof_requirements"],
         [("company_surface", COMPANY_SURFACES, 1), ("industry", INDUSTRIES, 3), ("entity_type", ENTITY_TYPES, 5),
          ("schema_standard", SCHEMA_STANDARDS, 7), ("data_shape", DATA_SHAPES, 11),
          ("transform", TRANSFORMS, 13), ("output_artifact", OUTPUT_ARTIFACTS, 17)],
         build_company)

    # 3 ── cloud guardrail runtime
    def build_guardrail(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("cloud_guardrail_runtime", combo, row_id, record_id),
            **combo,
            "title": f"{combo['guardrail_family']} as {combo['deployment_shape']} on {combo['cloud_runtime']}",
            "input_edge": f"{cc(combo['input_surface'])}+{cc(combo['guardrail_family'])}Policy",
            "output_edge": "GuardrailDecision+DecisionReceipt",
            "known_implementation_families": "OPA/Cedar; provider guardrail adapters; FastAPI/Express middleware; OpenTelemetry",
            "source_ref_families": "official_docs; cloud_provider_docs; policy_engine_docs",
            "effects": "audit_log_write; decision_gate",
            "proof_requirements": proofs_for(
                ["positive_fixture", "negative_fixture", "false_positive_fixture", "decision_receipt_schema", "policy_version_pin"],
                row_id),
        }

    spec("cloud_guardrail_runtime", "Cloud Guardrail Runtime Pack",
         "Deterministic guardrail primitives x cloud runtimes x deployment shapes x policy backends x decision actions.",
         5000,
         ["row_id", "record_id", "pack_id", "guardrail_family", "cloud_runtime", "deployment_shape",
          "policy_backend", "input_surface", "decision_action", "title", "input_edge", "output_edge",
          "known_implementation_families", "source_ref_families", "effects", "proof_requirements"],
         [("guardrail_family", GUARDRAIL_FAMILIES, 1), ("cloud_runtime", CLOUD_RUNTIMES, 3),
          ("deployment_shape", DEPLOYMENT_SHAPES, 5), ("policy_backend", POLICY_BACKENDS, 7),
          ("input_surface", INPUT_SURFACES, 11), ("decision_action", DECISION_ACTIONS, 13)],
         build_guardrail)

    # 4 ── marketplace-to-primitive adapter
    def build_marketplace(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("marketplace_to_primitive_adapter", combo, row_id, record_id),
            **combo,
            "title": f"{combo['marketplace']} {combo['listing_type']} -> {combo['capability_family']} cards",
            "input_edge": f"{cc(combo['marketplace'])}Listing+ExtractionPolicy",
            "output_edge": f"{cc(combo['capability_family'])}PrimitiveCandidateSet+LicenseReviewReceipt",
            "known_implementation_families": "registry API clients; OpenAPI parsers; listing scrapers; JSON Schema validators",
            "source_ref_families": "cloud_marketplace_listing; official_docs; package_metadata; MCP_registry",
            "effects": "network_read; artifact_write",
            "proof_requirements": proofs_for(["listing_source_ref", "deployment_smoke_test_optional"], row_id),
        }

    spec("marketplace_to_primitive_adapter", "Marketplace-To-Primitive Adapter Pack",
         "Convert marketplace/registry listings into typed primitive candidate cards with license and deployment review obligations.",
         5000,
         ["row_id", "record_id", "pack_id", "marketplace", "listing_type", "capability_family", "runtime_shape",
          "deployment_target", "title", "input_edge", "output_edge", "known_implementation_families",
          "source_ref_families", "effects", "proof_requirements"],
         [("marketplace", MARKETPLACES, 1), ("listing_type", LISTING_TYPES, 3),
          ("capability_family", CAPABILITY_FAMILIES, 5), ("runtime_shape", RUNTIME_SHAPES, 7),
          ("deployment_target", CLOUD_RUNTIMES, 11)],
         build_marketplace)

    # 5 ── package API surface mining
    def build_package(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("package_api_surface_mining", combo, row_id, record_id),
            **combo,
            "title": f"{combo['registry']} {combo['package_domain']} {combo['surface_type']} -> {combo['extraction_objective']}",
            "input_edge": f"{cc(combo['registry'])}PackageRef+{cc(combo['surface_type'])}MiningPolicy",
            "output_edge": f"{cc(combo['extraction_objective'])}+ApiSurfaceReceipt",
            "known_implementation_families": "registry metadata APIs; AST parsers; type-stub readers; docstring miners",
            "source_ref_families": "PyPI_metadata; npm_metadata; GitHub_repo; official_docs",
            "effects": "network_read; artifact_write",
            "proof_requirements": proofs_for(["signature_fixture_test", "license_gate"], row_id),
        }

    spec("package_api_surface_mining", "Package API Surface Mining Pack",
         "Mine package registries for reusable capability contracts: surfaces x domains x extraction objectives (no code copying — contracts only).",
         5000,
         ["row_id", "record_id", "pack_id", "registry", "package_domain", "surface_type",
          "extraction_objective", "title", "input_edge", "output_edge", "known_implementation_families",
          "source_ref_families", "effects", "proof_requirements"],
         [("registry", PACKAGE_REGISTRIES, 1), ("package_domain", PACKAGE_DOMAINS, 3),
          ("surface_type", SURFACE_TYPES, 5), ("extraction_objective", EXTRACTION_OBJECTIVES, 7)],
         build_package)

    # 6 ── API contract primitives
    def build_api(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("api_contract_primitives", combo, row_id, record_id),
            **combo,
            "title": f"{combo['spec_family']} {combo['operation_kind']} wrapper for {combo['business_object']}",
            "input_edge": f"{cc(combo['spec_family'])}Operation[{cc(combo['business_object'])}{cc(combo['operation_kind'])}]+AuthPolicy",
            "output_edge": f"Typed{cc(combo['business_object'])}Response+ApiCallReceipt",
            "known_implementation_families": "OpenAPI/AsyncAPI parsers; GraphQL clients; gRPC stubs; contract-test harnesses",
            "source_ref_families": "OpenAPI_spec; AsyncAPI_spec; official_api_reference",
            "effects": "network_read; network_write_optional",
            "proof_requirements": proofs_for(
                ["openapi_contract_test", "auth_scope_review", "request_response_fixture", "rate_limit_policy_check", "idempotency_test"],
                row_id),
        }

    spec("api_contract_primitives", "OpenAPI / AsyncAPI / GraphQL / gRPC Contract Primitive Pack",
         "Endpoint/operation primitive variants across spec families, operation kinds, auth schemes, pagination, error models, and wrapper targets.",
         6000,
         ["row_id", "record_id", "pack_id", "spec_family", "operation_kind", "business_object", "auth_scheme",
          "pagination_model", "error_model", "wrapper_target", "title", "input_edge", "output_edge",
          "known_implementation_families", "source_ref_families", "effects", "proof_requirements"],
         [("spec_family", SPEC_FAMILIES, 1), ("operation_kind", OPERATION_KINDS, 3),
          ("business_object", BUSINESS_OBJECTS, 5), ("auth_scheme", AUTH_SCHEMES, 7),
          ("pagination_model", PAGINATION_MODELS, 11), ("error_model", ERROR_MODELS, 13),
          ("wrapper_target", COMPILE_TARGETS, 17)],
         build_api)

    # 7 ── data science methodology
    def build_ds(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("data_science_methodology", combo, row_id, record_id),
            **combo,
            "title": f"{combo['task_family']} {combo['method_step']} ({combo['metric']})",
            "input_edge": f"{cc(combo['dataset_shape'])}Dataset+{cc(combo['method_step'])}Policy",
            "output_edge": f"{cc(combo['method_step'])}Artifact+ExperimentReceipt",
            "known_implementation_families": "Pandas/Polars; scikit-learn family; XGBoost/LightGBM family; MLflow/W&B; Optuna/Ray Tune",
            "source_ref_families": "Kaggle_competition; OpenML_task; official_docs; benchmark_fixture",
            "effects": "cpu_compute; artifact_write",
            "proof_requirements": proofs_for(
                ["metric_parser_test", "leakage_scan", "cross_validation_receipt", "submission_format_check", "experiment_repro_receipt"],
                row_id),
        }

    spec("data_science_methodology", "Kaggle / OpenML Data Science Methodology Pack",
         "Method-step primitives for competition-grade data science: task family x dataset shape x method step x metric x runtime.",
         5000,
         ["row_id", "record_id", "pack_id", "task_family", "dataset_shape", "method_step", "metric",
          "runtime_shape", "title", "input_edge", "output_edge", "known_implementation_families",
          "source_ref_families", "effects", "proof_requirements"],
         [("task_family", DS_TASK_FAMILIES, 1), ("dataset_shape", DATA_SHAPES, 3),
          ("method_step", DS_METHOD_STEPS, 5), ("metric", DS_METRICS, 7), ("runtime_shape", RUNTIME_SHAPES, 11)],
         build_ds)

    # 8 ── browser/web extraction
    def build_browser(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("browser_web_extraction", combo, row_id, record_id),
            **combo,
            "title": f"{combo['site_category']} {combo['extraction_target']} via {combo['navigation_pattern']}",
            "input_edge": f"{cc(combo['site_category'])}Target+{cc(combo['extraction_target'])}Schema+BrowsePolicy",
            "output_edge": f"{cc(combo['extraction_target'])}Batch+SourceSnapshotReceipt",
            "known_implementation_families": "Playwright/Selenium; Scrapy/requests; readability parsers; diff monitors",
            "source_ref_families": "government_data_portal; official_docs; robots_and_terms; runtime_trace",
            "effects": "network_read; artifact_write",
            "proof_requirements": proofs_for(
                ["selector_fixture", "snapshot_hash_receipt", "terms_of_service_gate", "attribution_receipt"],
                row_id),
        }

    spec("browser_web_extraction", "Browser / Web Extraction Pack",
         "Policy-gated web extraction routes: site categories x targets x navigation patterns x fragility guards.",
         5000,
         ["row_id", "record_id", "pack_id", "site_category", "extraction_target", "navigation_pattern",
          "fragility_guard", "runtime_shape", "title", "input_edge", "output_edge",
          "known_implementation_families", "source_ref_families", "effects", "proof_requirements"],
         [("site_category", SITE_CATEGORIES, 1), ("extraction_target", EXTRACTION_TARGETS, 3),
          ("navigation_pattern", NAVIGATION_PATTERNS, 5), ("fragility_guard", FRAGILITY_GUARDS, 7),
          ("runtime_shape", RUNTIME_SHAPES, 11)],
         build_browser)

    # 9 ── RAG retrieval grounding
    def build_rag(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("rag_retrieval_grounding", combo, row_id, record_id),
            **combo,
            "title": f"{combo['corpus_type']} {combo['retriever']} + {combo['reranker']} + {combo['grounding_gate']}",
            "input_edge": f"UserQuestion+{cc(combo['corpus_type'])}CorpusRef+RetrievalPolicy",
            "output_edge": "GroundedAnswerDraft+CitationReceipt",
            "known_implementation_families": "BM25 engines; dense embedders; late-interaction rankers; span verifiers",
            "source_ref_families": "official_docs; benchmark_fixture; runtime_trace",
            "effects": "cpu_compute; index_read",
            "proof_requirements": proofs_for(
                ["retrieval_recall_fixture", "citation_accuracy_check", "abstention_fixture", "regression_replay"],
                row_id),
        }

    spec("rag_retrieval_grounding", "RAG Retrieval / Grounding Pack",
         "Retrieval-route variants: corpus x chunker x retriever x reranker x grounding gate x eval — no single retriever assumed best.",
         5000,
         ["row_id", "record_id", "pack_id", "corpus_type", "chunker", "retriever", "reranker",
          "grounding_gate", "rag_eval", "title", "input_edge", "output_edge",
          "known_implementation_families", "source_ref_families", "effects", "proof_requirements"],
         [("corpus_type", CORPUS_TYPES, 1), ("chunker", CHUNKERS, 3), ("retriever", RETRIEVERS, 5),
          ("reranker", RERANKERS, 7), ("grounding_gate", GROUNDING_GATES, 11), ("rag_eval", RAG_EVALS, 13)],
         build_rag)

    # 10 ── devops/IaC/cloud deploy
    def build_devops(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("devops_iac_cloud_deploy", combo, row_id, record_id),
            **combo,
            "title": f"{combo['iac_family']} {combo['resource_family']} deploy ({combo['environment']})",
            "input_edge": f"{cc(combo['resource_family'])}Config+{cc(combo['environment'])}Policy",
            "output_edge": f"{cc(combo['iac_family'])}PlanOrApplyReceipt+ResourceRefs",
            "known_implementation_families": "Terraform/Pulumi/CDK; Helm/Kustomize; GitHub Actions/Argo; policy-as-code engines",
            "source_ref_families": "Terraform_Registry; Kubernetes_docs; cloud_provider_docs; official_docs",
            "effects": "cloud_resource_create_optional; state_write; audit_log_write",
            "proof_requirements": proofs_for(
                ["dry_run_plan", "policy_check", "secret_boundary_check", "healthcheck", "rollback_plan"],
                row_id),
        }

    spec("devops_iac_cloud_deploy", "DevOps / IaC / Cloud Deployment Pack",
         "Deployment-route primitives: IaC family x resource family x environment x safety gate x runtime.",
         5000,
         ["row_id", "record_id", "pack_id", "iac_family", "resource_family", "environment", "safety_gate",
          "runtime_shape", "title", "input_edge", "output_edge", "known_implementation_families",
          "source_ref_families", "effects", "proof_requirements"],
         [("iac_family", IAC_FAMILIES, 1), ("resource_family", RESOURCE_FAMILIES, 3),
          ("environment", ENVIRONMENTS, 5), ("safety_gate", SAFETY_GATES, 7), ("runtime_shape", RUNTIME_SHAPES, 11)],
         build_devops)

    # 11 ── observability / incident response
    def build_obs(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("observability_incident_response", combo, row_id, record_id),
            **combo,
            "title": f"{combo['signal_family']} -> {combo['detector']} -> {combo['triage_step']}",
            "input_edge": f"{cc(combo['signal_family'])}Stream+{cc(combo['detector'])}Policy",
            "output_edge": f"{cc(combo['runbook_artifact'])}+IncidentReceipt",
            "known_implementation_families": "OpenTelemetry; Prometheus-family; log pipelines; paging/routing systems",
            "source_ref_families": "official_docs; runbooks; runtime_trace",
            "effects": "telemetry_read; alert_emit_optional; artifact_write",
            "proof_requirements": proofs_for(
                ["synthetic_signal_fixture", "false_positive_budget_check", "escalation_route_test", "receipt_schema_test"],
                row_id),
        }

    spec("observability_incident_response", "Observability / Incident Response Pack",
         "Detection-to-runbook primitives: signal x detector x triage step x runbook artifact x escalation.",
         5000,
         ["row_id", "record_id", "pack_id", "signal_family", "detector", "triage_step", "runbook_artifact",
          "escalation", "title", "input_edge", "output_edge", "known_implementation_families",
          "source_ref_families", "effects", "proof_requirements"],
         [("signal_family", SIGNAL_FAMILIES, 1), ("detector", DETECTORS, 3), ("triage_step", TRIAGE_STEPS, 5),
          ("runbook_artifact", RUNBOOK_ARTIFACTS, 7), ("escalation", ESCALATIONS, 11)],
         build_obs)

    # 12 ── search method strategy arms
    def build_strategy(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("search_method_strategy_arms", combo, row_id, record_id),
            **combo,
            "title": f"{combo['generation_path']} + {combo['search_path']} + {combo['planner']} -> {combo['compile_target']}",
            "input_edge": "TaskIntent+CandidateBundle+StrategyPolicy",
            "output_edge": "PlanLock+RouteCompileReceipt",
            "when_it_should_win": f"tasks where {combo['search_path']} finds a near-match and {combo['planner']} closes the gap",
            "known_failure": f"{combo['search_path']} misses and {combo['planner']} overfits to a wrong candidate",
            "proof_requirements": proofs_for(["paired_comparison_receipt", "held_out_replay"], row_id),
        }

    spec("search_method_strategy_arms", "Search-Method Strategy Arm Pack",
         "Comparable strategy arms: generation path x search path x planner x compile target x proof path x ranking metric.",
         3000,
         ["row_id", "record_id", "pack_id", "generation_path", "search_path", "planner", "compile_target",
          "proof_path", "ranking_metric", "title", "input_edge", "output_edge", "when_it_should_win",
          "known_failure", "proof_requirements"],
         [("generation_path", GENERATION_PATHS, 1), ("search_path", SEARCH_PATHS, 3),
          ("planner", ROUTE_PLANNERS, 5), ("compile_target", COMPILE_TARGETS, 7),
          ("proof_path", PROOF_ROTATION, 11), ("ranking_metric", RANKING_METRICS, 13)],
         build_strategy)

    # 13 ── Kaggle benchmark adapters (seeds of the 1,030+ hub)
    def build_kaggle(combo: dict[str, str], row_id: int, record_id: str) -> dict[str, Any]:
        return {
            **_variant_common("kaggle_benchmark_adapters", combo, row_id, record_id),
            **combo,
            "title": f"{combo['benchmark']} -> {combo['primitive_demand']} ({combo['comparison_arm']})",
            "input_edge": f"{cc(combo['benchmark'])}Task+AdapterPolicy",
            "output_edge": "PrimitiveDemandSet+BenchmarkScorecard",
            "harvest_status": "seed_only_full_hub_harvest_pending",
            "source_ref_families": "Kaggle_benchmark_hub_listing; benchmark_fixture; official_docs",
            "proof_requirements": proofs_for(
                ["adapter_fixture_test", "scorecard_schema_test", "no_external_number_promotion_gate"],
                row_id),
        }

    spec("kaggle_benchmark_adapters", "Kaggle Benchmark Adapter Pack",
         "Benchmark-to-primitive-demand adapter seeds for the Kaggle benchmark hub (1,030+ benchmarks; named rows here are SEEDS from the owner's paste — the full hub harvest is a pending source adapter, tracked in the research queue).",
         4000,
         ["row_id", "record_id", "pack_id", "benchmark", "benchmark_task_type", "comparison_arm",
          "scorecard_metric", "primitive_demand", "title", "input_edge", "output_edge", "harvest_status",
          "source_ref_families", "proof_requirements"],
         [("benchmark", KAGGLE_BENCHMARKS, 1), ("benchmark_task_type", BENCHMARK_TASK_TYPES, 3),
          ("comparison_arm", COMPARISON_ARMS, 5), ("scorecard_metric", SCORECARD_METRICS, 7),
          ("primitive_demand", PRIMITIVE_DEMANDS, 11)],
         build_kaggle)

    return specs


# ── writers ──
def write_md_pack(out_dir: Path, spec: dict[str, Any], rows: list[dict[str, Any]]) -> Path:
    path = out_dir / spec["filename"]
    columns = spec["columns"]
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# {spec['title']}\n\n")
        handle.write(spec["purpose"].strip() + "\n\n")
        handle.write(
            "Status: generated candidate rows only (dimension-driven deterministic generation; no hand-written rows; "
            "no random values). Keep `candidate=true` and `serves_truth=false` until source refs, contracts, side "
            "effects, tests, and promotion evidence exist. Regenerate via "
            "`python3 scripts/build_primitive_expansion_md_packs.py --write` — never hand-edit.\n\n"
        )
        handle.write("| " + " | ".join(columns) + " |\n")
        handle.write("| " + " | ".join(["---"] * len(columns)) + " |\n")
        for row in rows:
            handle.write("| " + " | ".join(md_escape(row.get(column, "")) for column in columns) + " |\n")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_bundle(out_dir: Path, *, row_scale: float) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = build_pack_specs()
    entries: list[dict[str, Any]] = []
    paths: list[Path] = []
    for spec in specs:
        target = max(50, int(spec["target_rows"] * row_scale))
        rows = generate_rows(spec["pack_id"], spec["dims"], target, spec["build"])
        path = write_md_pack(out_dir, spec, rows)
        paths.append(path)
        entries.append({
            "pack_id": spec["pack_id"],
            "filename": spec["filename"],
            "title": spec["title"],
            "purpose": spec["purpose"],
            "row_count": len(rows),
            "target_rows": target,
            "columns": spec["columns"],
            "dimension_axes": [name for name, _, _ in spec["dims"]],
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    index_path = out_dir / "primitive_generated_pack_index.md"
    with index_path.open("w", encoding="utf-8") as handle:
        handle.write("# Generated Primitive Pack Index\n\n")
        handle.write("All rows candidate=true / serves_truth=false. Regenerate via the builder; never hand-edit.\n\n")
        handle.write("| file | title | rows | axes |\n| --- | --- | ---: | --- |\n")
        for entry in entries:
            handle.write(
                f"| {entry['filename']} | {md_escape(entry['title'])} | {entry['row_count']} "
                f"| {md_escape('; '.join(entry['dimension_axes']))} |\n"
            )
    manifest = {
        "record_type": "primitive_expansion_md_pack_manifest",
        "created_at": _now(),
        "builder": "scripts/build_primitive_expansion_md_packs.py",
        "row_scale": row_scale,
        "pack_count": len(entries),
        "total_rows": sum(entry["row_count"] for entry in entries),
        "packs": entries,
        "index_file": index_path.name,
        "candidate": True,
        "serves_truth": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


# ── validation (owner section-13 rules) ──
def check_md_pack(path: Path, entry: dict[str, Any]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [line for line in lines if line.startswith("|")]
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    assert header == entry["columns"], f"{path.name}: header drift"
    rows = table_lines[2:]
    assert len(rows) == entry["row_count"], f"{path.name}: expected {entry['row_count']} rows, got {len(rows)}"
    idx = {name: header.index(name) for name in header}
    seen_ids: set[str] = set()
    for line in rows:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == len(header), f"{path.name}: bad cell count: {line[:120]}"
        record_id = cells[idx["record_id"]]
        assert record_id and record_id not in seen_ids, f"{path.name}: duplicate/empty record_id {record_id}"
        seen_ids.add(record_id)
        assert cells[idx["candidate"]] == "true", f"{path.name}: candidate flag broken"
        assert cells[idx["serves_truth"]] == "false", f"{path.name}: serves_truth flag broken"
        for column in ("input_edge", "output_edge", "proof_requirements"):
            if column in idx:
                assert cells[idx[column]], f"{path.name}: empty {column}"
    assert _sha256(path) == entry["sha256"], f"{path.name}: sha256 drift — regenerate via the builder, never hand-edit"


def check_bundle(out_dir: Path) -> dict[str, Any]:
    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists(), f"missing {manifest_path}; run --write first"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("candidate") is True and manifest.get("serves_truth") is False
    for entry in manifest["packs"]:
        check_md_pack(out_dir / entry["filename"], entry)
    assert (out_dir / manifest["index_file"]).exists(), "missing pack index"
    return manifest


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / OUT_DIR_NAME
        manifest = write_bundle(out_dir, row_scale=0.01)
        assert manifest["pack_count"] == 13, f"expected 13 packs, got {manifest['pack_count']}"
        assert manifest["total_rows"] >= 13 * 50
        checked = check_bundle(out_dir)
        assert checked["total_rows"] == manifest["total_rows"]
        kaggle = next(entry for entry in manifest["packs"] if entry["pack_id"] == "kaggle_benchmark_adapters")
        assert "harvest_status" in kaggle["columns"], "kaggle pack must carry harvest_status seed marker"
    real_dir = _resource(OUT_DIR_NAME)
    if (real_dir / "manifest.json").exists():
        check_bundle(real_dir)
        note = " + real bundle validated"
    else:
        note = ""
    print(f"OK: primitive expansion md packs self-test passed (13 packs, uniqueness, flags, sha freshness{note}).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Generate all packs + index + manifest.")
    parser.add_argument("--check", action="store_true", help="Validate written packs against the manifest.")
    parser.add_argument("--row-scale", type=float, default=1.0, help="Scale factor over per-pack default row targets.")
    parser.add_argument("--out-dir", default=str(_resource(OUT_DIR_NAME)))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    out_dir = Path(args.out_dir)
    if args.write:
        manifest = write_bundle(out_dir, row_scale=args.row_scale)
        print(json.dumps({key: manifest[key] for key in ("pack_count", "total_rows", "created_at")}, indent=2))
        for entry in manifest["packs"]:
            print(f"  {entry['filename']}: {entry['row_count']} rows")
        return
    if args.check:
        manifest = check_bundle(out_dir)
        print(f"OK: {manifest['pack_count']} packs, {manifest['total_rows']} rows validated against manifest.")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
