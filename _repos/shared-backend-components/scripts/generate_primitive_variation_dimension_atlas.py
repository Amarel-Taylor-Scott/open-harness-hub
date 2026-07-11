#!/usr/bin/env python3
"""Generate the primitive variation dimension atlas seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-variation-dimension-atlas")
SOURCE_STATUS = "curated_dimension_seed_needs_source_ref_resolution"

COMMON_ROW = {
    "candidate": True,
    "serves_truth": False,
    "source_refs": [],
    "source_evidence_status": SOURCE_STATUS,
}


def dim(slug: str, title: str, axis: str, values: list[str]) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "variation_axis": axis,
        "values_seed": values,
    }


FAMILIES: list[dict[str, Any]] = [
    {
        "family_id": "fam:primitive_identity_granularity",
        "title": "Primitive identity and granularity",
        "dimension_kind": "primitive_identity",
        "dimensions": [
            dim("atomic_primitive", "Atomic primitive", "granularity", ["single_edge", "pure_transform", "side_effecting_action"]),
            dim("primitive_group", "Primitive group", "granularity", ["visible_edge", "hidden_member_edges", "group_contract"]),
            dim("route_plan", "Route plan", "assembly_level", ["single_step", "multi_step", "fallback_route"]),
            dim("route_portfolio", "Route portfolio", "assembly_level", ["cheap", "balanced", "quality"]),
            dim("resolved_primitive", "Resolved specialized primitive", "materialized_view", ["on_demand", "hot_combination", "promoted"]),
            dim("candidate_status", "Candidate status", "trust_boundary", ["candidate", "needs_evidence", "denied"]),
            dim("promotion_status", "Promotion status", "trust_boundary", ["review_ready", "promoted", "deprecated"]),
            dim("context_level", "Context disclosure level", "llm_context", ["index_card", "edge_card", "contract_card", "source_slice"]),
            dim("hidden_edge_policy", "Hidden edge policy", "llm_context", ["hide_until_gap", "show_for_repair", "show_for_proof"]),
            dim("materialization_policy", "Materialization policy", "storage_policy", ["never", "hot_on_first_use", "proof_backed_only"]),
        ],
    },
    {
        "family_id": "fam:core_computer_logic",
        "title": "Core computer logic",
        "dimension_kind": "core_logic",
        "dimensions": [
            dim("boolean_logic", "Boolean logic", "operation", ["and", "or", "not", "xor"]),
            dim("predicate", "Predicate", "operation", ["field_predicate", "row_predicate", "compound_predicate"]),
            dim("comparison", "Comparison", "operation", ["equals", "range", "fuzzy", "ordering"]),
            dim("arithmetic", "Arithmetic", "operation", ["sum", "difference", "ratio", "rounding_policy"]),
            dim("map", "Map", "operation", ["element_map", "field_projection", "record_transform"]),
            dim("filter", "Filter", "operation", ["predicate_filter", "window_filter", "policy_filter"]),
            dim("reduce", "Reduce", "operation", ["aggregate", "fold", "rollup"]),
            dim("join", "Join", "operation", ["inner", "left", "anti", "asof"]),
            dim("sort_rank", "Sort and rank", "operation", ["ascending", "descending", "score_rank", "tie_break"]),
            dim("dedupe", "Dedupe", "operation", ["exact_key", "fuzzy_match", "survivorship_policy"]),
        ],
    },
    {
        "family_id": "fam:algorithms_data_structures",
        "title": "Algorithms and data structures",
        "dimension_kind": "algorithm_data_structure",
        "dimensions": [
            dim("two_pointers", "Two pointers", "algorithm_pattern", ["left_right", "fast_slow", "merge_scan"]),
            dim("sliding_window", "Sliding window", "algorithm_pattern", ["fixed_window", "variable_window", "time_window"]),
            dim("prefix_sum", "Prefix sum", "algorithm_pattern", ["cumulative_sum", "difference_array", "range_query"]),
            dim("hash_lookup", "Hash lookup", "data_structure", ["set_membership", "dict_index", "frequency_map"]),
            dim("binary_search", "Binary search", "algorithm_pattern", ["sorted_array", "answer_space", "lower_bound"]),
            dim("heap_priority_queue", "Heap and priority queue", "data_structure", ["min_heap", "max_heap", "top_k"]),
            dim("tree_graph_traversal", "Tree and graph traversal", "algorithm_pattern", ["bfs", "dfs", "topological_sort", "union_find"]),
            dim("dynamic_programming", "Dynamic programming", "algorithm_pattern", ["memoization", "tabulation", "state_compression"]),
            dim("cache_hashing", "Cache and distributed hashing", "data_structure", ["lru_cache", "consistent_hashing", "rate_limit_bucket"]),
            dim("probabilistic_structure", "Probabilistic structure", "data_structure", ["bloom_filter", "count_min_sketch", "hyperloglog"]),
        ],
    },
    {
        "family_id": "fam:data_types_schema_semantics",
        "title": "Data types and schema semantics",
        "dimension_kind": "data_semantics",
        "dimensions": [
            dim("boolean_type", "Boolean type", "data_type", ["true_false", "nullable_bool", "tri_state"]),
            dim("integer_type", "Integer type", "data_type", ["signed", "unsigned", "bigint"]),
            dim("decimal_money", "Decimal and money", "data_type", ["fixed_precision", "currency_pair", "rounding_mode"]),
            dim("float_measurement", "Float and measurement", "data_type", ["float", "double", "unit_annotated"]),
            dim("string_text", "String and text", "data_type", ["plain_text", "localized_text", "tokenized_text"]),
            dim("bytes_binary", "Bytes and binary", "data_type", ["blob", "hash_digest", "encoded_payload"]),
            dim("date_time_timestamp", "Date time and timestamp", "data_type", ["date", "time", "timestamp", "timezone"]),
            dim("enum_taxonomy", "Enum and taxonomy", "data_type", ["closed_enum", "open_enum", "controlled_vocabulary"]),
            dim("json_xml", "JSON and XML", "data_type", ["object", "array", "document", "namespace"]),
            dim("geography_embedding_identifier", "Geography embedding and identifier", "data_type", ["geo_point", "vector", "uuid", "external_id"]),
        ],
    },
    {
        "family_id": "fam:data_layout_storage_modeling",
        "title": "Data layout, storage, and modeling",
        "dimension_kind": "data_layout",
        "dimensions": [
            dim("long_tidy_table", "Long or tidy table", "layout", ["entity_time_value", "narrow_facts", "tidy_columns"]),
            dim("wide_feature_table", "Wide feature table", "layout", ["one_row_per_entity", "feature_columns", "model_matrix"]),
            dim("normalized_schema", "Normalized schema", "layout", ["third_normal_form", "foreign_keys", "junction_table"]),
            dim("star_schema", "Star schema", "layout", ["fact_table", "dimension_table", "surrogate_key"]),
            dim("event_log", "Event log", "layout", ["append_only", "event_time", "actor_action_object"]),
            dim("snapshot_table", "Snapshot table", "layout", ["as_of_date", "state_snapshot", "point_in_time"]),
            dim("slowly_changing_dimension", "Slowly changing dimension", "layout", ["type_one", "type_two", "effective_date"]),
            dim("ledger_table", "Ledger table", "layout", ["double_entry", "append_only", "reversal_entry"]),
            dim("fact_dimension_model", "Fact and dimension model", "layout", ["grain", "measure", "dimension"]),
            dim("entity_attribute_value", "Entity attribute value", "layout", ["sparse_attributes", "attribute_registry", "typed_value"]),
        ],
    },
    {
        "family_id": "fam:file_message_artifact_formats",
        "title": "File, message, and artifact formats",
        "dimension_kind": "format",
        "dimensions": [
            dim("csv_tsv", "CSV and TSV", "file_format", ["delimiter", "quote_policy", "header_policy"]),
            dim("json_jsonl", "JSON and JSONL", "file_format", ["document", "records", "nested_objects"]),
            dim("xml_html", "XML and HTML", "file_format", ["namespace", "dom", "xpath"]),
            dim("parquet_arrow", "Parquet and Arrow", "file_format", ["columnar_file", "columnar_memory", "schema_metadata"]),
            dim("avro_orc", "Avro and ORC", "file_format", ["schema_evolution", "columnar_storage", "block_encoding"]),
            dim("protobuf", "Protocol buffers", "message_format", ["message", "field_number", "service_method"]),
            dim("edi_x12", "EDI X12", "message_format", ["segment", "transaction_set", "acknowledgement"]),
            dim("hl7_dicom", "HL7 and DICOM", "message_format", ["clinical_message", "imaging_metadata", "patient_context"]),
            dim("pdf_office", "PDF and office documents", "artifact_format", ["pdf", "spreadsheet", "presentation", "word_doc"]),
            dim("rss_atom_sitemap", "RSS Atom and sitemap", "web_format", ["feed_item", "entry", "url_set"]),
        ],
    },
    {
        "family_id": "fam:sql_database_query_engine",
        "title": "SQL, database, and query-engine dimensions",
        "dimension_kind": "database_query_engine",
        "dimensions": [
            dim("postgresql", "PostgreSQL", "sql_dialect", ["jsonb", "array", "indexing", "transactions"]),
            dim("mysql", "MySQL", "sql_dialect", ["numeric", "datetime", "json", "spatial"]),
            dim("sqlite", "SQLite", "sql_dialect", ["embedded", "pragma", "limited_alter", "file_db"]),
            dim("bigquery", "BigQuery Standard SQL", "sql_dialect", ["struct", "array", "partition", "cost_model"]),
            dim("snowflake", "Snowflake SQL", "sql_dialect", ["variant", "warehouse", "stage", "task"]),
            dim("duckdb", "DuckDB", "sql_dialect", ["local_olap", "parquet_scan", "vectorized"]),
            dim("spark_sql", "Spark SQL", "sql_dialect", ["distributed", "dataframe", "partition"]),
            dim("clickhouse", "ClickHouse", "sql_dialect", ["merge_tree", "columnar", "materialized_view"]),
            dim("trino_presto", "Trino and Presto", "sql_dialect", ["federated_query", "connector", "catalog"]),
            dim("sqlserver_oracle", "SQL Server and Oracle", "sql_dialect", ["stored_procedure", "isolation", "enterprise_feature"]),
        ],
    },
    {
        "family_id": "fam:language_runtime_stack",
        "title": "Language, runtime, and technology stack",
        "dimension_kind": "runtime_stack",
        "dimensions": [
            dim("python", "Python", "language_runtime", ["typing", "venv", "pytest", "pandas"]),
            dim("typescript_node", "TypeScript and Node", "language_runtime", ["node", "tsconfig", "npm", "vitest"]),
            dim("java_kotlin", "Java and Kotlin", "language_runtime", ["jvm", "maven", "gradle", "spring"]),
            dim("go", "Go", "language_runtime", ["module", "goroutine", "interface", "test"]),
            dim("rust", "Rust", "language_runtime", ["cargo", "ownership", "trait", "tokio"]),
            dim("csharp_dotnet", "C# and .NET", "language_runtime", ["dotnet", "aspnet", "linq", "nuget"]),
            dim("cpp", "C and C++", "language_runtime", ["compiler", "memory", "cmake", "abi"]),
            dim("r_julia", "R and Julia", "language_runtime", ["dataframe", "notebook", "statistics", "package"]),
            dim("shell_powershell", "Shell and PowerShell", "language_runtime", ["cli", "pipe", "environment", "script"]),
            dim("frontend_framework", "Frontend framework", "ui_runtime", ["react", "vue", "angular", "svelte"]),
        ],
    },
    {
        "family_id": "fam:api_web_event_integration",
        "title": "API, web, event, and integration surfaces",
        "dimension_kind": "integration_surface",
        "dimensions": [
            dim("rest", "REST", "api_style", ["resource", "http_status", "json"]),
            dim("http_method", "HTTP method", "api_style", ["get", "post", "put", "patch", "delete"]),
            dim("graphql", "GraphQL", "api_style", ["query", "mutation", "resolver", "connection"]),
            dim("grpc", "gRPC", "api_style", ["proto", "service", "stream"]),
            dim("soap", "SOAP", "api_style", ["wsdl", "envelope", "xml_schema"]),
            dim("websocket_sse", "WebSocket and SSE", "event_surface", ["bidirectional", "server_sent", "connection_state"]),
            dim("webhook", "Webhook", "event_surface", ["signature", "replay", "idempotency"]),
            dim("file_drop", "File drop", "integration_surface", ["sftp", "bucket", "watched_folder"]),
            dim("email_ingest", "Email ingest", "integration_surface", ["mailbox", "attachment", "thread"]),
            dim("browser_ui", "Browser-only UI", "integration_surface", ["session", "form", "selector"]),
        ],
    },
    {
        "family_id": "fam:web_browsing_source_surfaces",
        "title": "Web browsing and source-surface variations",
        "dimension_kind": "source_surface",
        "dimensions": [
            dim("dom_snapshot", "DOM snapshot", "source_capture", ["html", "computed_text", "shadow_dom"]),
            dim("selector_strategy", "Selector strategy", "source_capture", ["css_selector", "xpath", "aria_role"]),
            dim("structured_data_jsonld", "Structured data JSON-LD", "source_capture", ["schema_org", "jsonld", "microdata"]),
            dim("ocr_visual_extraction", "OCR and visual extraction", "source_capture", ["ocr_text", "bounding_box", "image_region"]),
            dim("sitemap_crawl", "Sitemap crawl", "source_discovery", ["sitemap_xml", "url_pattern", "recrawl_policy"]),
            dim("robots_terms_policy", "Robots and terms policy", "source_policy", ["robots_txt", "terms_review", "crawl_budget"]),
            dim("session_auth_context", "Session and auth context", "source_policy", ["logged_out", "user_session", "credential_scope"]),
            dim("rate_limit_politeness", "Rate limit and politeness", "source_policy", ["backoff", "retry_after", "crawl_delay"]),
            dim("source_span_receipt", "Source span receipt", "evidence", ["text_span", "selector", "line_ref"]),
            dim("screenshot_receipt", "Screenshot receipt", "evidence", ["viewport", "timestamp", "pixel_proof"]),
        ],
    },
    {
        "family_id": "fam:industry_domain_business_context",
        "title": "Industry, domain, and business context",
        "dimension_kind": "industry_domain",
        "dimensions": [
            dim("healthcare", "Healthcare", "industry", ["patient", "claim", "provider", "observation"]),
            dim("finance", "Finance", "industry", ["ledger", "payment", "risk", "reporting"]),
            dim("insurance", "Insurance", "industry", ["policy", "claim", "coverage", "loss"]),
            dim("legal", "Legal", "industry", ["contract", "matter", "clause", "obligation"]),
            dim("government", "Government", "industry", ["procurement", "permit", "grant", "public_record"]),
            dim("education", "Education", "industry", ["course", "student", "credential", "accommodation"]),
            dim("ecommerce_retail", "Ecommerce and retail", "industry", ["order", "product", "inventory", "return"]),
            dim("manufacturing_construction", "Manufacturing and construction", "industry", ["work_order", "asset", "rfi", "submittal"]),
            dim("logistics_transportation", "Logistics and transportation", "industry", ["shipment", "route", "fleet", "terminal"]),
            dim("devtools_saas", "Devtools and SaaS", "industry", ["repo", "tenant", "subscription", "support_ticket"]),
        ],
    },
    {
        "family_id": "fam:region_geography_localization_jurisdiction",
        "title": "Region, geography, localization, and jurisdiction",
        "dimension_kind": "region_jurisdiction",
        "dimensions": [
            dim("country", "Country", "geography", ["iso2", "iso3", "country_name"]),
            dim("state_province", "State or province", "geography", ["admin_level_one", "subdivision_code", "province_name"]),
            dim("municipality", "Municipality", "geography", ["city", "county", "local_authority"]),
            dim("postal_code", "Postal code", "geography", ["zip", "postcode", "postal_prefix"]),
            dim("timezone", "Timezone", "localization", ["iana_timezone", "offset", "daylight_saving"]),
            dim("business_calendar", "Business calendar", "localization", ["holiday", "workday", "cutoff_time"]),
            dim("currency", "Currency", "localization", ["iso4217", "minor_unit", "exchange_rate_policy"]),
            dim("tax_regime", "Tax regime", "jurisdiction", ["tax_rate", "tax_id", "effective_date"]),
            dim("address_format", "Address format", "localization", ["line_order", "postal_format", "script"]),
            dim("coordinate_reference_system", "Coordinate reference system", "geospatial", ["wgs84", "projected_crs", "transform"]),
        ],
    },
    {
        "family_id": "fam:legal_compliance_security_governance",
        "title": "Legal, compliance, security, and governance",
        "dimension_kind": "governance",
        "dimensions": [
            dim("gdpr_privacy", "GDPR and privacy", "compliance_profile", ["data_subject", "lawful_basis", "retention"]),
            dim("hipaa_phi", "HIPAA and PHI", "compliance_profile", ["covered_entity", "phi", "minimum_necessary"]),
            dim("pci_payment", "PCI and payment data", "compliance_profile", ["cardholder_data", "tokenization", "scope"]),
            dim("soc2_sox_audit", "SOC 2 and SOX audit", "compliance_profile", ["control", "evidence", "segregation"]),
            dim("ferpa_glba", "FERPA and GLBA", "compliance_profile", ["student_record", "financial_privacy", "access_policy"]),
            dim("cjis_fedramp_fisma", "CJIS FedRAMP and FISMA", "compliance_profile", ["government_system", "authorization", "control_baseline"]),
            dim("owasp_web_risk", "OWASP web risk", "security_risk", ["injection", "xss", "authz", "ssrf"]),
            dim("cis_controls", "CIS controls", "security_control", ["inventory", "configuration", "access_control"]),
            dim("nist_ai_rmf", "NIST AI risk management", "ai_governance", ["govern", "map", "measure", "manage"]),
            dim("prompt_injection_data_exfiltration", "Prompt injection and data exfiltration", "ai_security", ["tool_injection", "secret_leak", "retrieval_poisoning"]),
        ],
    },
    {
        "family_id": "fam:ui_visualization_media_artifact_design",
        "title": "UI, visualization, media, and artifact design",
        "dimension_kind": "artifact_design",
        "dimensions": [
            dim("web_page", "Web page", "ui_surface", ["route", "layout", "responsive"]),
            dim("mobile_screen", "Mobile screen", "ui_surface", ["touch", "safe_area", "offline"]),
            dim("admin_panel", "Admin panel", "ui_surface", ["table", "filter", "bulk_action"]),
            dim("form_table", "Form and table", "ui_component", ["validation", "editable_grid", "pagination"]),
            dim("wizard_modal", "Wizard and modal", "ui_component", ["stepper", "dialog", "confirmation"]),
            dim("chart_dashboard", "Chart and dashboard", "visualization", ["bar", "line", "scorecard", "dashboard"]),
            dim("map_geospatial", "Map and geospatial", "visualization", ["points", "choropleth", "route"]),
            dim("document_report", "Document and report", "artifact", ["markdown", "pdf", "docx"]),
            dim("media_image_video", "Image and video", "media", ["resize", "transcode", "thumbnail"]),
            dim("audio_transcript", "Audio and transcript", "media", ["transcribe", "align", "caption"]),
        ],
    },
    {
        "family_id": "fam:ml_ai_rag_benchmark",
        "title": "ML, AI, RAG, and benchmark dimensions",
        "dimension_kind": "ml_ai_benchmark",
        "dimensions": [
            dim("classification_regression", "Classification and regression", "ml_task", ["label", "target", "metric"]),
            dim("ranking_recommendation", "Ranking and recommendation", "ml_task", ["candidate", "rank", "feedback"]),
            dim("forecasting_anomaly", "Forecasting and anomaly detection", "ml_task", ["time_series", "horizon", "threshold"]),
            dim("clustering_segmentation", "Clustering and segmentation", "ml_task", ["cluster", "segment", "distance_metric"]),
            dim("entity_extraction", "Entity extraction", "ai_task", ["span", "entity_type", "confidence"]),
            dim("document_intelligence", "Document intelligence", "ai_task", ["layout", "field", "table"]),
            dim("rag_retrieval", "RAG retrieval", "rag_stage", ["chunk", "embedding", "top_k"]),
            dim("rerank_citation_check", "Rerank and citation check", "rag_stage", ["rerank", "source_span", "supportedness"]),
            dim("eval_dataset_rubric", "Eval dataset and rubric", "benchmark", ["fixture", "rubric", "scorecard"]),
            dim("model_card_repro_package", "Model card and reproducibility package", "benchmark", ["model_card", "dataset_card", "seed"]),
        ],
    },
    {
        "family_id": "fam:devops_observability_runtime_ops",
        "title": "DevOps, observability, and runtime operations",
        "dimension_kind": "runtime_operations",
        "dimensions": [
            dim("ci_cd", "CI and CD", "operations_surface", ["workflow", "check", "deployment"]),
            dim("container_image", "Container image", "runtime_artifact", ["dockerfile", "image_scan", "registry"]),
            dim("kubernetes", "Kubernetes", "runtime_target", ["deployment", "service", "job", "ingress"]),
            dim("cloud_function", "Cloud function", "runtime_target", ["trigger", "cold_start", "iam"]),
            dim("queue_worker", "Queue worker", "runtime_target", ["message", "ack", "dead_letter"]),
            dim("scheduler_cron", "Scheduler and cron", "runtime_target", ["schedule", "timezone", "missed_run"]),
            dim("logging_metrics_tracing", "Logging metrics and tracing", "observability", ["log", "metric", "span"]),
            dim("incident_runbook", "Incident runbook", "operations_artifact", ["timeline", "action", "handoff"]),
            dim("rollback_deploy", "Rollback and deploy", "resilience", ["rollback", "canary", "blue_green"]),
            dim("capacity_cost", "Capacity and cost", "operations_metric", ["latency", "throughput", "unit_cost"]),
        ],
    },
    {
        "family_id": "fam:source_mining_benchmarks_public_corpora",
        "title": "Source mining, benchmarks, and public corpora",
        "dimension_kind": "source_mining",
        "dimensions": [
            dim("github_repo", "GitHub repo", "source_surface", ["repo", "stars", "license", "examples"]),
            dim("pypi_package", "PyPI package", "source_surface", ["package", "version", "wheel", "readme"]),
            dim("npm_package", "npm package", "source_surface", ["package", "version", "exports", "readme"]),
            dim("openapi_spec", "OpenAPI spec", "source_surface", ["operation", "schema", "security_scheme"]),
            dim("asyncapi_spec", "AsyncAPI spec", "source_surface", ["channel", "message", "protocol"]),
            dim("kaggle_openml", "Kaggle and OpenML", "benchmark_surface", ["task", "dataset", "metric"]),
            dim("huggingface_dataset", "Hugging Face dataset", "benchmark_surface", ["dataset", "split", "license"]),
            dim("government_open_data", "Government open data", "public_corpus", ["catalog", "dataset", "publisher"]),
            dim("benchmark_suite", "Benchmark suite", "benchmark_surface", ["task", "fixture", "score"]),
            dim("docs_site_blog", "Docs site and blog", "source_surface", ["page", "example", "changelog"]),
        ],
    },
    {
        "family_id": "fam:job_role_seniority_workforce",
        "title": "Job role, seniority, and workforce dimensions",
        "dimension_kind": "role_workforce",
        "dimensions": [
            dim("backend_engineer", "Backend engineer", "role", ["api", "database", "idempotency"]),
            dim("frontend_engineer", "Frontend engineer", "role", ["ui", "state", "accessibility"]),
            dim("data_engineer", "Data engineer", "role", ["etl", "lineage", "quality"]),
            dim("ml_engineer", "ML engineer", "role", ["dataset", "model", "evaluation"]),
            dim("sre", "SRE", "role", ["observability", "rollback", "capacity"]),
            dim("security_engineer", "Security engineer", "role", ["threat", "secret", "policy"]),
            dim("gis_analyst", "GIS analyst", "role", ["spatial", "projection", "map"]),
            dim("procurement_analyst", "Procurement analyst", "role", ["notice", "deadline", "fit_score"]),
            dim("clinical_informaticist", "Clinical informaticist", "role", ["fhir", "privacy", "workflow"]),
            dim("seniority_level", "Seniority level", "role_context", ["junior", "mid", "senior", "staff"]),
        ],
    },
    {
        "family_id": "fam:embedding_affinity_search_materialization",
        "title": "Embedding, affinity, search, and materialization",
        "dimension_kind": "search_materialization",
        "dimensions": [
            dim("edge_io_embedding", "Edge I/O embedding", "embedding_view", ["input_edge", "output_edge", "type_compatibility"]),
            dim("blackbox_embedding", "Blackbox embedding", "embedding_view", ["does", "does_not", "behavior"]),
            dim("route_embedding", "Route embedding", "embedding_view", ["hidden_edges", "route_plan", "fallback"]),
            dim("schema_semantics_embedding", "Schema semantics embedding", "embedding_view", ["field", "type", "meaning"]),
            dim("algorithm_pattern_embedding", "Algorithm pattern embedding", "embedding_view", ["pattern", "complexity", "data_structure"]),
            dim("industry_domain_embedding", "Industry domain embedding", "embedding_view", ["domain_object", "workflow", "risk"]),
            dim("runtime_stack_embedding", "Runtime stack embedding", "embedding_view", ["language", "framework", "runtime"]),
            dim("proof_embedding", "Proof requirements embedding", "embedding_view", ["test", "receipt", "promotion_gate"]),
            dim("negative_memory_search", "Negative memory search", "search_mode", ["failure_pattern", "misuse", "known_bad_match"]),
            dim("materialization_trigger", "Materialization trigger", "storage_policy", ["hot_use", "benchmark", "customer_pack"]),
        ],
    },
    {
        "family_id": "fam:architecture_system_design_pattern",
        "title": "Architecture, system design, and pattern dimensions",
        "dimension_kind": "architecture_pattern",
        "dimensions": [
            dim("monolith", "Monolith", "architecture", ["single_deployable", "shared_database", "in_process"]),
            dim("modular_monolith", "Modular monolith", "architecture", ["module_boundary", "internal_api", "shared_deploy"]),
            dim("microservices", "Microservices", "architecture", ["service_boundary", "network_call", "service_contract"]),
            dim("serverless", "Serverless", "architecture", ["function", "event_trigger", "managed_runtime"]),
            dim("event_driven", "Event-driven architecture", "architecture", ["event", "consumer", "producer"]),
            dim("hexagonal_clean", "Hexagonal and clean architecture", "architecture", ["port", "adapter", "use_case"]),
            dim("cqrs_event_sourcing", "CQRS and event sourcing", "architecture", ["command", "query", "event_store"]),
            dim("data_mesh_lakehouse", "Data mesh and lakehouse", "architecture", ["domain_data_product", "table_format", "catalog"]),
            dim("offline_first_edge", "Offline-first and edge", "architecture", ["local_cache", "sync", "conflict_resolution"]),
            dim("api_gateway_cache_queue", "API gateway cache and queue", "system_component", ["gateway", "cache", "queue"]),
        ],
    },
    {
        "family_id": "fam:common_schema_interchange",
        "title": "Common schema and interchange variations",
        "dimension_kind": "schema_interchange",
        "dimensions": [
            dim("json_schema", "JSON Schema", "schema_standard", ["type", "constraint", "validation"]),
            dim("openapi_schema", "OpenAPI schema", "schema_standard", ["operation", "component", "security"]),
            dim("asyncapi_message", "AsyncAPI message", "schema_standard", ["channel", "message", "protocol"]),
            dim("graphql_schema", "GraphQL schema", "schema_standard", ["type", "query", "mutation"]),
            dim("protobuf_grpc", "Protobuf and gRPC", "schema_standard", ["message", "field", "service"]),
            dim("fhir_resource", "FHIR resource", "schema_standard", ["resource", "profile", "bundle"]),
            dim("schema_org_type", "Schema.org type", "schema_standard", ["type", "property", "jsonld"]),
            dim("xbrl_taxonomy", "XBRL taxonomy", "schema_standard", ["concept", "context", "unit"]),
            dim("gtfs_geojson", "GTFS and GeoJSON", "schema_standard", ["stop", "route", "feature_collection"]),
            dim("dcat_ckan_socrata", "DCAT CKAN and Socrata", "schema_standard", ["dataset", "package", "resource"]),
        ],
    },
    {
        "family_id": "fam:public_repo_package_codebase",
        "title": "Public repo, package, and codebase variations",
        "dimension_kind": "codebase_surface",
        "dimensions": [
            dim("language_stack_detect", "Language stack detect", "codebase_analysis", ["language", "framework", "runtime"]),
            dim("package_manager", "Package manager", "codebase_analysis", ["pip", "npm", "maven", "cargo"]),
            dim("public_api_surface", "Public API surface", "codebase_analysis", ["exported_symbol", "endpoint", "cli"]),
            dim("internal_helper_duplicate", "Internal helper duplicate", "codebase_analysis", ["duplicate", "near_match", "adapter_candidate"]),
            dim("test_gap", "Test gap", "codebase_analysis", ["uncovered_symbol", "missing_fixture", "missing_contract_test"]),
            dim("dependency_graph", "Dependency graph", "codebase_analysis", ["package", "import", "transitive"]),
            dim("license_inventory", "License inventory", "codebase_analysis", ["license", "notice", "compatibility"]),
            dim("security_hotspot", "Security hotspot", "codebase_analysis", ["secret", "injection", "unsafe_call"]),
            dim("readme_examples", "README and examples", "codebase_analysis", ["quickstart", "example", "usage_card"]),
            dim("changelog_breaking_change", "Changelog breaking change", "codebase_analysis", ["version_note", "migration", "deprecation"]),
        ],
    },
    {
        "family_id": "fam:geospatial_open_data_public_services",
        "title": "Geospatial, open-data, and public-services variations",
        "dimension_kind": "geospatial_public_service",
        "dimensions": [
            dim("osm_poi", "OSM POI", "geospatial_source", ["node", "way", "tag"]),
            dim("arcgis_feature_layer", "ArcGIS feature layer", "geospatial_source", ["layer", "feature", "geometry"]),
            dim("socrata_dataset", "Socrata dataset", "open_data_source", ["dataset_id", "field", "api_endpoint"]),
            dim("ckan_package", "CKAN package", "open_data_source", ["package", "resource", "organization"]),
            dim("geocoding", "Geocoding", "geospatial_operation", ["address", "lat_lon", "confidence"]),
            dim("spatial_join", "Spatial join", "geospatial_operation", ["point_in_polygon", "nearest", "intersect"]),
            dim("nearest_neighbor", "Nearest neighbor", "geospatial_operation", ["k_nearest", "distance_metric", "index"]),
            dim("isochrone", "Isochrone", "geospatial_operation", ["travel_time", "mode", "network"]),
            dim("administrative_boundary", "Administrative boundary", "geospatial_reference", ["country", "state", "municipality"]),
            dim("public_service_facility", "Public service facility", "public_service_object", ["clinic", "school", "office", "shelter"]),
        ],
    },
    {
        "family_id": "fam:response_format_user_output",
        "title": "Response format and user-output variations",
        "dimension_kind": "response_output",
        "dimensions": [
            dim("markdown_answer", "Markdown answer", "output_format", ["headings", "table", "citations"]),
            dim("json_response", "JSON response", "output_format", ["schema", "typed_fields", "validation"]),
            dim("csv_export", "CSV export", "output_format", ["columns", "delimiter", "encoding"]),
            dim("pdf_report", "PDF report", "output_format", ["layout", "page", "appendix"]),
            dim("ppt_slide_deck", "Slide deck", "output_format", ["slide", "speaker_note", "chart"]),
            dim("mermaid_diagram", "Mermaid diagram", "diagram_format", ["flowchart", "sequence", "class"]),
            dim("graphviz_dot", "Graphviz DOT", "diagram_format", ["node", "edge", "layout"]),
            dim("vega_lite_spec", "Vega-Lite spec", "visualization_format", ["mark", "encoding", "transform"]),
            dim("react_component", "React component", "ui_output", ["props", "state", "event"]),
            dim("receipt_bundle", "Receipt bundle", "proof_output", ["source", "execution", "proof"]),
        ],
    },
    {
        "family_id": "fam:variation_control_lattice",
        "title": "Variation-control and lattice dimensions",
        "dimension_kind": "variation_control",
        "dimensions": [
            dim("dimension_selection", "Dimension selection", "resolver_control", ["required", "optional", "inferred"]),
            dim("overlay_conflict_resolution", "Overlay conflict resolution", "resolver_control", ["precedence", "merge", "deny"]),
            dim("hot_combination_detection", "Hot combination detection", "resolver_control", ["usage_count", "benchmark_demand", "customer_pack"]),
            dim("proof_backed_materialization", "Proof-backed materialization", "resolver_control", ["proof_required", "receipt_required", "review_required"]),
            dim("negative_memory_gate", "Negative memory gate", "resolver_control", ["block", "warn", "adapt"]),
            dim("source_ref_gate", "Source ref gate", "resolver_control", ["official", "authorized", "missing"]),
            dim("license_gate", "License gate", "resolver_control", ["allowed", "review", "deny"]),
            dim("context_budget_policy", "Context budget policy", "resolver_control", ["edge_only", "contract", "source_slice"]),
            dim("route_portfolio_ranking", "Route portfolio ranking", "resolver_control", ["cost", "latency", "proof_strength"]),
            dim("promotion_evidence", "Promotion evidence", "resolver_control", ["tests", "benchmarks", "review"]),
        ],
    },
]


SPECIALIZATION_EXAMPLES = [
    {
        "example_id": "example:healthcare_bigquery_observation_filter",
        "title": "Healthcare BigQuery observation filter",
        "base_edge": "Collection[T]+Predicate[T]->FilteredCollection[T]",
        "resolved_edge": "BigQueryTable[FHIRObservation]+ObservationCodeDatePredicate+PHIPolicy->FilteredObservationTable+QueryReceipt",
        "dimension_refs": [
            "dim:core_computer_logic.filter",
            "dim:common_schema_interchange.fhir_resource",
            "dim:sql_database_query_engine.bigquery",
            "dim:legal_compliance_security_governance.hipaa_phi",
            "dim:region_geography_localization_jurisdiction.country",
        ],
    },
    {
        "example_id": "example:logistics_osm_route_candidate",
        "title": "Logistics OSM route candidate",
        "base_edge": "WeightedGraph+SourceNode+TargetNode+PathPolicy->Path+CostReceipt",
        "resolved_edge": "RoadNetworkGraph+Depot+DeliveryStop+TruckRoutingPolicy->DeliveryRouteCandidate+RouteCostReceipt",
        "dimension_refs": [
            "dim:algorithms_data_structures.tree_graph_traversal",
            "dim:industry_domain_business_context.logistics_transportation",
            "dim:geospatial_open_data_public_services.osm_poi",
            "dim:region_geography_localization_jurisdiction.coordinate_reference_system",
        ],
    },
    {
        "example_id": "example:ecommerce_shopify_postgres_import",
        "title": "Ecommerce Shopify Postgres import",
        "base_edge": "RawRecordBatch+ImportPolicy+ExistingEntityIndex->PreparedRecordImport+ImportReceipt",
        "resolved_edge": "ProductCSV+ShopifyCatalogImportPolicy+ExistingSKUIndex->ProductImportPreview+ShopifyMutationReceipt",
        "dimension_refs": [
            "dim:core_computer_logic.dedupe",
            "dim:industry_domain_business_context.ecommerce_retail",
            "dim:file_message_artifact_formats.csv_tsv",
            "dim:sql_database_query_engine.postgresql",
            "dim:api_web_event_integration.rest",
        ],
    },
    {
        "example_id": "example:ml_long_to_wide_feature_table",
        "title": "ML long-to-wide feature table",
        "base_edge": "LongEventTable+PivotPolicy->WideFeatureTable+SchemaReceipt",
        "resolved_edge": "LongCustomerEventTable+FeatureWindowPolicy->WideCustomerFeatureTable+LeakageScanReceipt",
        "dimension_refs": [
            "dim:data_layout_storage_modeling.long_tidy_table",
            "dim:data_layout_storage_modeling.wide_feature_table",
            "dim:ml_ai_rag_benchmark.classification_regression",
            "dim:ml_ai_rag_benchmark.eval_dataset_rubric",
        ],
    },
    {
        "example_id": "example:frontend_json_schema_form",
        "title": "Frontend JSON Schema form",
        "base_edge": "JsonSchema+UserRolePolicy->FormUiSpec+ValidationReceipt",
        "resolved_edge": "JsonSchema[CustomerSettings]+FrontendPolicy->ReactSettingsForm+AccessibilityReceipt",
        "dimension_refs": [
            "dim:common_schema_interchange.json_schema",
            "dim:language_runtime_stack.frontend_framework",
            "dim:ui_visualization_media_artifact_design.form_table",
            "dim:job_role_seniority_workforce.frontend_engineer",
        ],
    },
    {
        "example_id": "example:cyber_sbom_vulnerability_route",
        "title": "Cyber SBOM vulnerability route",
        "base_edge": "DependencyInventory+VulnerabilityPolicy->RemediationTaskSet+EvidenceReceipt",
        "resolved_edge": "CycloneDxSbom+CvePolicy+ServiceGraph->PrioritizedRemediationPlan+ProofReceipt",
        "dimension_refs": [
            "dim:legal_compliance_security_governance.owasp_web_risk",
            "dim:source_mining_benchmarks_public_corpora.benchmark_suite",
            "dim:public_repo_package_codebase.dependency_graph",
            "dim:job_role_seniority_workforce.security_engineer",
        ],
    },
]

ROLE_MATRIX = [
    {
        "role_id": "role:backend_engineer",
        "role_dimension_ref": "dim:job_role_seniority_workforce.backend_engineer",
        "preferred_dimension_refs": [
            "dim:algorithms_data_structures.cache_hashing",
            "dim:api_web_event_integration.webhook",
            "dim:devops_observability_runtime_ops.queue_worker",
            "dim:legal_compliance_security_governance.owasp_web_risk",
        ],
        "proof_style": ["contract_test", "idempotency_test", "integration_test"],
    },
    {
        "role_id": "role:data_engineer",
        "role_dimension_ref": "dim:job_role_seniority_workforce.data_engineer",
        "preferred_dimension_refs": [
            "dim:core_computer_logic.join",
            "dim:data_layout_storage_modeling.slowly_changing_dimension",
            "dim:file_message_artifact_formats.parquet_arrow",
            "dim:ml_ai_rag_benchmark.eval_dataset_rubric",
        ],
        "proof_style": ["schema_drift_test", "lineage_receipt", "data_quality_test"],
    },
    {
        "role_id": "role:frontend_engineer",
        "role_dimension_ref": "dim:job_role_seniority_workforce.frontend_engineer",
        "preferred_dimension_refs": [
            "dim:language_runtime_stack.frontend_framework",
            "dim:ui_visualization_media_artifact_design.form_table",
            "dim:response_format_user_output.react_component",
            "dim:web_browsing_source_surfaces.screenshot_receipt",
        ],
        "proof_style": ["accessibility_test", "visual_regression_test", "component_contract_test"],
    },
    {
        "role_id": "role:sre",
        "role_dimension_ref": "dim:job_role_seniority_workforce.sre",
        "preferred_dimension_refs": [
            "dim:devops_observability_runtime_ops.logging_metrics_tracing",
            "dim:devops_observability_runtime_ops.rollback_deploy",
            "dim:architecture_system_design_pattern.api_gateway_cache_queue",
            "dim:algorithms_data_structures.cache_hashing",
        ],
        "proof_style": ["smoke_test", "rollback_test", "observability_receipt"],
    },
    {
        "role_id": "role:security_engineer",
        "role_dimension_ref": "dim:job_role_seniority_workforce.security_engineer",
        "preferred_dimension_refs": [
            "dim:legal_compliance_security_governance.prompt_injection_data_exfiltration",
            "dim:legal_compliance_security_governance.owasp_web_risk",
            "dim:public_repo_package_codebase.security_hotspot",
            "dim:source_mining_benchmarks_public_corpora.github_repo",
        ],
        "proof_style": ["threat_model", "secret_scan_receipt", "policy_test"],
    },
    {
        "role_id": "role:gis_analyst",
        "role_dimension_ref": "dim:job_role_seniority_workforce.gis_analyst",
        "preferred_dimension_refs": [
            "dim:geospatial_open_data_public_services.spatial_join",
            "dim:geospatial_open_data_public_services.nearest_neighbor",
            "dim:region_geography_localization_jurisdiction.coordinate_reference_system",
            "dim:ui_visualization_media_artifact_design.map_geospatial",
        ],
        "proof_style": ["crs_transform_test", "geometry_validity_test", "map_attribution_receipt"],
    },
    {
        "role_id": "role:ml_engineer",
        "role_dimension_ref": "dim:job_role_seniority_workforce.ml_engineer",
        "preferred_dimension_refs": [
            "dim:ml_ai_rag_benchmark.classification_regression",
            "dim:ml_ai_rag_benchmark.model_card_repro_package",
            "dim:algorithms_data_structures.dynamic_programming",
            "dim:embedding_affinity_search_materialization.proof_embedding",
        ],
        "proof_style": ["leakage_scan", "metric_scorecard", "reproducibility_receipt"],
    },
    {
        "role_id": "role:clinical_informaticist",
        "role_dimension_ref": "dim:job_role_seniority_workforce.clinical_informaticist",
        "preferred_dimension_refs": [
            "dim:common_schema_interchange.fhir_resource",
            "dim:legal_compliance_security_governance.hipaa_phi",
            "dim:industry_domain_business_context.healthcare",
            "dim:region_geography_localization_jurisdiction.country",
        ],
        "proof_style": ["privacy_boundary_review", "schema_validation", "human_review_receipt"],
    },
]

RESOLVER_RULES = [
    {
        "rule_id": "rule:materialize_hot_or_proof_backed",
        "title": "Materialize only hot or proof-backed combinations",
        "input_edge": "BasePrimitive+DimensionSelection+UsageEvidence+ProofPolicy",
        "output_edge": "MaterializationDecision+ReasonReceipt",
        "decision_policy": "materialize when usage demand, benchmark demand, or proof-backed promotion evidence justifies the resolved card",
    },
    {
        "rule_id": "rule:dimension_conflict_to_gap_receipt",
        "title": "Turn overlay conflicts into gap receipts",
        "input_edge": "SelectedDimensionSet+OverlaySet",
        "output_edge": "ResolvedOverlaySet+GapReceipt",
        "decision_policy": "do not silently merge conflicting jurisdiction, schema, or runtime dimensions",
    },
    {
        "rule_id": "rule:smallest_context_first",
        "title": "Show smallest useful context first",
        "input_edge": "TaskIntent+CandidatePrimitiveSet+ContextBudget",
        "output_edge": "MinimalContextPack+ContextReceipt",
        "decision_policy": "start with visible edges and proof status; drill into hidden edges only on contract, proof, or repair gaps",
    },
]


def _dimension_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_index, family in enumerate(FAMILIES, start=1):
        for dimension_index, seed in enumerate(family["dimensions"], start=1):
            row = {
                "record_type": "primitive_variation_dimension",
                "dimension_id": f"dim:{family['family_id'].split(':', 1)[1]}.{seed['slug']}",
                "family_id": family["family_id"],
                "family_title": family["title"],
                "family_index": family_index,
                "dimension_index": dimension_index,
                "title": seed["title"],
                "dimension_kind": family["dimension_kind"],
                "variation_axis": seed["variation_axis"],
                "values_seed": seed["values_seed"],
                "applies_to": ["primitive_contract", "overlay_resolver", "proof_plan", "search_index"],
                "resolver_use": (
                    "Use this dimension as a selectable overlay axis; materialize resolved primitives "
                    "only for hot, benchmarked, or proof-backed combinations."
                ),
                "materialization_policy": "materialize_hot_or_proof_backed",
                "proof_implications": ["contract_fixture", "edge_case_fixture", "receipt_required"],
                **COMMON_ROW,
            }
            rows.append(row)
    return rows


def _with_common(row: dict[str, Any], record_type: str) -> dict[str, Any]:
    return {"record_type": record_type, **row, **COMMON_ROW}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_grouped_yaml(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["groups:"]
    for family in FAMILIES:
        family_id = family["family_id"]
        family_rows = [row for row in rows if row["family_id"] == family_id]
        lines.extend(
            [
                f"  - family_id: {family_id}",
                f"    title: {json.dumps(family['title'])}",
                f"    dimension_kind: {family['dimension_kind']}",
                "    dimensions:",
            ]
        )
        for row in family_rows:
            lines.append(f"      - {row['dimension_id']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sql(path: Path) -> None:
    path.write_text(
        """-- Primitive variation dimension atlas schema additions.
-- Candidate schema. Do not treat generated rows as promoted truth.

CREATE TABLE IF NOT EXISTS variation_dimension (
  dimension_id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL,
  title TEXT NOT NULL,
  dimension_kind TEXT NOT NULL,
  variation_axis TEXT NOT NULL,
  values_seed JSONB NOT NULL,
  candidate BOOLEAN NOT NULL DEFAULT TRUE,
  serves_truth BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS primitive_overlay_binding (
  binding_id TEXT PRIMARY KEY,
  base_primitive_id TEXT NOT NULL,
  dimension_id TEXT NOT NULL REFERENCES variation_dimension(dimension_id),
  overlay_ref TEXT NOT NULL,
  proof_policy_ref TEXT,
  materialization_policy TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resolved_specialized_primitive (
  resolved_primitive_id TEXT PRIMARY KEY,
  base_primitive_id TEXT NOT NULL,
  selected_dimensions JSONB NOT NULL,
  input_edge TEXT NOT NULL,
  output_edge TEXT NOT NULL,
  proof_plan JSONB NOT NULL,
  runtime_plan JSONB NOT NULL,
  candidate BOOLEAN NOT NULL DEFAULT TRUE,
  serves_truth BOOLEAN NOT NULL DEFAULT FALSE
);
""",
        encoding="utf-8",
    )


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    dimension_rows = _dimension_rows()
    example_rows = [_with_common(row, "primitive_variation_specialization_example") for row in SPECIALIZATION_EXAMPLES]
    role_rows = [_with_common(row, "primitive_variation_role_algorithm_matrix") for row in ROLE_MATRIX]
    resolver_rows = [_with_common(row, "primitive_variation_resolver_rule") for row in RESOLVER_RULES]

    _write_jsonl(PACK_DIR / "primitive_variation_dimensions_250.jsonl", dimension_rows)
    _write_jsonl(PACK_DIR / "primitive_specialization_examples.jsonl", example_rows)
    _write_jsonl(PACK_DIR / "role_algorithm_data_structure_matrix.jsonl", role_rows)
    _write_jsonl(PACK_DIR / "variation_resolver_rules.jsonl", resolver_rows)
    _write_grouped_yaml(PACK_DIR / "primitive_variation_dimensions_grouped.yaml", dimension_rows)
    _write_sql(PACK_DIR / "variation_dimension_schema_additions.sql")

    manifest = {
        "record_type": "primitive_variation_dimension_atlas_manifest",
        "pack_id": "primitive-variation-dimension-atlas",
        "version": "0.1.0",
        "candidate": True,
        "serves_truth": False,
        "source_status": SOURCE_STATUS,
        "description": "Variation dimensions for resolving specialized primitives without materializing the full Cartesian product.",
        "files": {
            "variation_dimensions": "primitive_variation_dimensions_250.jsonl",
            "grouped_yaml": "primitive_variation_dimensions_grouped.yaml",
            "specialization_examples": "primitive_specialization_examples.jsonl",
            "role_algorithm_matrix": "role_algorithm_data_structure_matrix.jsonl",
            "resolver_rules": "variation_resolver_rules.jsonl",
            "schema_additions_sql": "variation_dimension_schema_additions.sql",
        },
        "family_count": len(FAMILIES),
        "dimensions_per_family": 10,
        "dimension_count": len(dimension_rows),
        "specialization_example_count": len(example_rows),
        "role_matrix_count": len(role_rows),
        "resolver_rule_count": len(resolver_rows),
        "materialization_rule": "Store dimensions and overlays; materialize only high-value, hot, benchmarked, or proof-backed resolved primitives.",
    }
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("family_count", "dimension_count", "specialization_example_count", "role_matrix_count", "resolver_rule_count")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
