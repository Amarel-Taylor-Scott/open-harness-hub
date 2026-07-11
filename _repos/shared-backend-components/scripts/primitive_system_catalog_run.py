#!/usr/bin/env python3
"""scripts.primitive_system_catalog_run — the owner's autonomous catalog-run spec (2026-07-07) executed as a
DETERMINISTIC generator. One run emits the full ``artifacts/{RUN_ID}/`` tree: run_config, 80+ research
queries, ontology, primitive/transformation/schema/architecture catalogs (the spec's required record formats,
stable dot-path IDs), CRUD/transformation/architecture matrices, a tool registry, 20 agent playbooks, the
pattern documents, concrete schemas rendered into SQL / JSON Schema / Pydantic / TypeScript / OpenAPI / Avro
from ONE field-spec table per object, starter code + tests, Mermaid diagrams, coverage/gap/final reports, a
source ledger seeded with the owner-supplied decompositions, and pending web-tool requests (live scraping
stays opt-in per repo source policy — the governed executor is continuous_primitive_scrape_loop).

Everything is candidate-only (serves_truth=false), byte-deterministic for a fixed (run_id, timestamp), and
validated by an in-run checklist (JSONL parse, unique IDs, required fields, taxonomy coverage, SQL executes,
generated code runs). Re-run with a different --domain to catalog another area; the taxonomy tables are the
single source and extending any of them is a data-row edit, never a rewrite.

    python3 scripts/primitive_system_catalog_run.py --self-test
    python3 scripts/primitive_system_catalog_run.py --run [--run-id ID] [--out DIR] [--domain TEXT]
    python3 scripts/primitive_system_catalog_run.py --validate --out DIR
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
import csv  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import sqlite3  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_DEFAULT_RUN_ID = "run-structured-systems-v1"
#: fixed for byte-determinism (VERIFY-THE-VERIFIER: artifact builds byte-identical twice); --run may override.
_FIXED_TIMESTAMP = "2026-07-07T00:00:00Z"
_DEFAULT_DOMAIN = ("modern software, data, SaaS, ML, and LLM-agent systems — the union of the owner-supplied "
                   "role/structure decompositions (ML engineer; AI-assisted engineer; structured objects)")
_USER_GOAL = ("grow the governed primitive registry: a deterministic, source-backed, iteratively expanded "
              "catalog of primitives, structures, schemas, transformations, CRUD operations, architectures, "
              "tools, and playbooks that any relevant engineering workflow can consume")
_CONSTRAINTS = ("candidate=true, serves_truth=false at this layer", "no raw source bodies persisted",
                "stable lowercase dot-path IDs", "deterministic settings (fixed timestamp, stable sorts)",
                "public sources only; live scraping opt-in via the governed scrape loop",
                "no secrets/PII; synthetic or public metadata only")
_OWNER_SOURCES = (  # the owner-supplied decompositions already distilled into vocabularies (real sources)
    ("src.owner.ml_engineer_role_matrix", "vocabularies/ml-engineer-role-matrix.yaml",
     "Machine Learning Engineer role decomposition (owner-supplied, BLS/O*NET-adjacent)"),
    ("src.owner.ai_assisted_engineer_role_matrix", "vocabularies/ai-assisted-engineer-role-matrix.yaml",
     "AI-assisted Software/Platform/Data Engineer decomposition (owner-supplied, SO-2025-adjacent)"),
    ("src.owner.data_structures_role_matrix", "vocabularies/data-structures-role-matrix.yaml",
     "Structured-objects/data-structures decomposition (owner-supplied)"),
)

#: references CITED inside the owner-supplied decompositions (iteration 2, PASS A): ledgered as
#: source_type=owner_cited_reference and attached to records whose names match the tags. Content not yet
#: independently fetched — the full web verification pass stays in pending_tool_requests.jsonl.
_CITED_SOURCES: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("src.cited.bls_data_scientists", "https://www.bls.gov/ooh/math/data-scientists.htm", "BLS Occupational Outlook: Data Scientists", "bls.gov", ("feature_definition", "model_artifact")),
    ("src.cited.json_schema_docs", "https://json-schema.org/docs", "JSON Schema documentation", "json-schema.org", ("json_schema",)),
    ("src.cited.openapi_spec", "https://spec.openapis.org/oas/v3.2.0.html", "OpenAPI Specification v3.2.0", "openapis.org", ("openapi", "api_gateway")),
    ("src.cited.avro_docs", "https://avro.apache.org/docs/", "Apache Avro documentation", "apache.org", ("avro", "event_schema")),
    ("src.cited.confluent_schema_registry", "https://docs.confluent.io/platform/current/schema-registry/index.html", "Confluent Schema Registry", "confluent.io", ("schema_evolve", "event_schema")),
    ("src.cited.parquet", "https://parquet.apache.org/", "Apache Parquet", "apache.org", ("parquet_schema", "column_store")),
    ("src.cited.arrow", "https://arrow.apache.org/", "Apache Arrow", "apache.org", ("arrow_schema",)),
    ("src.cited.dbt_semantic_layer", "https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl", "dbt Semantic Layer", "getdbt.com", ("dbt_model", "metric_record", "data_warehouse")),
    ("src.cited.sklearn_pca", "https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html", "scikit-learn PCA", "scikit-learn.org", ("pca", "svd", "reduce_dimension")),
    ("src.cited.docker_container", "https://www.docker.com/resources/what-container/", "What is a Container?", "docker.com", ("container_registry",)),
    ("src.cited.kubernetes", "https://kubernetes.io/", "Kubernetes", "kubernetes.io", ("kubernetes_cluster", "autoscaler", "deployment", "liveness_probe", "readiness_probe")),
    ("src.cited.s3_docs", "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html", "Amazon S3 user guide", "aws.amazon.com", ("object_storage",)),
    ("src.cited.feast", "https://docs.feast.dev/", "Feast: the Open Source Feature Store", "feast.dev", ("feature_store", "feature_definition", "feature_value")),
    ("src.cited.mlflow", "https://mlflow.org/", "MLflow", "mlflow.org", ("model_registry", "model_artifact", "eval_result", "experiment")),
    ("src.cited.kserve", "https://kserve.github.io/website/", "KServe", "kserve.github.io", ("model_server", "model_deployment", "canary")),
    ("src.cited.airflow", "https://airflow.apache.org/", "Apache Airflow", "apache.org", ("workflow_engine", "scheduler", "workflow_definition", "workflow_run")),
    ("src.cited.spark", "https://spark.apache.org/", "Apache Spark", "apache.org", ("stream_processor", "batch_process", "stream_process")),
    ("src.cited.prometheus", "https://prometheus.io/", "Prometheus", "prometheus.io", ("ops_metric", "alert", "metric_record")),
    ("src.cited.opentelemetry", "https://opentelemetry.io/", "OpenTelemetry", "opentelemetry.io", ("ops_trace", "span", "trace_span", "ops_log")),
    ("src.cited.mcp", "https://modelcontextprotocol.io/docs/getting-started/intro", "Model Context Protocol", "modelcontextprotocol.io", ("tool_schema_record", "tool_call", "tool_result", "tool_schema", "agent_runtime")),
    ("src.cited.openai_agents_sdk", "https://openai.github.io/openai-agents-python/agents/", "OpenAI Agents SDK", "openai.github.io", ("handoff", "guardrail", "subagent", "structured_output", "agent_plan")),
    ("src.cited.github_copilot_agent", "https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/", "GitHub Copilot coding agent", "github.blog", ("agent_task", "agent_step", "agent_trace")),
    ("src.cited.claude_code", "https://claude.com/product/claude-code", "Claude Code", "claude.com", ("agent_runtime", "human_approval", "policy_check")),
    ("src.cited.so_survey_2025_ai", "https://survey.stackoverflow.co/2025/ai", "2025 Stack Overflow Developer Survey: AI", "stackoverflow.co", ("prompt_template", "prompt_instance")),
)


def _cited_refs_for(name: str) -> list[str]:
    return sorted(sid for sid, _u, _t, _p, tags in _CITED_SOURCES if name in tags)


_RESEARCH_CATEGORIES: tuple[str, ...] = (
    "software architecture", "saas architecture", "crud systems", "api design", "database schemas",
    "document data structures", "event-driven systems", "stream processing", "batch data engineering",
    "etl and elt", "data lakes and lakehouses", "data warehouses", "graph databases", "vector databases",
    "search indexing", "embeddings and retrieval", "rag systems", "llm agent architectures",
    "tool-calling systems", "workflow engines", "orchestration systems", "infrastructure as code",
    "cloud architecture", "distributed systems", "compute scheduling", "storage systems",
    "networking and bandwidth", "observability", "logging and tracing", "metrics and alerting",
    "security engineering", "privacy engineering", "governance and audit", "testing and qa", "ci-cd",
    "devops", "sre", "ml model lifecycle", "feature stores", "model serving", "schema evolution",
    "data contracts", "json schema", "openapi", "graphql", "protobuf", "avro", "parquet", "arrow",
    "sql ddl", "nosql document structures", "knowledge graphs", "ontology modeling", "dimensional modeling",
    "dimensionality reduction", "transformations and data normalization", "compilers and asts",
    "code generation", "static analysis", "program repair", "agentic coding", "saas billing systems",
    "authentication and authorization", "tenant isolation", "permission models", "audit logs",
    "user activity logs", "product analytics", "experimentation systems", "workflow state machines",
    "background jobs", "queues", "caches", "message brokers", "deployment patterns",
    "data migration patterns", "system migration patterns", "llm evaluation", "prompt management",
    "production ai governance")

# ── Section-5 taxonomy families (single source; each item becomes a primitive record) ────────────────────────
_FAMILIES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("business_saas_objects", "logical", "data", (
        "user", "organization", "tenant", "workspace", "account", "role", "permission", "subscription",
        "invoice", "payment", "entitlement", "project", "task", "ticket", "comment", "notification", "file",
        "document", "integration", "webhook", "audit_event", "feature_flag", "experiment", "customer_event",
        "usage_record")),
    ("data_structures", "logical", "data", (
        "scalar", "record", "row", "column", "table", "relation", "primary_key", "foreign_key", "index",
        "partition", "snapshot", "event", "stream", "batch", "log", "metric", "trace", "graph_node",
        "graph_edge", "vector", "embedding", "tensor", "sparse_matrix", "dense_matrix", "hierarchy", "tree",
        "trie", "heap", "queue", "stack", "map", "set", "bloom_filter", "time_series", "geospatial_record",
        "document_chunk", "schema", "metadata_record")),
    ("document_structures", "logical", "document", (
        "raw_document", "parsed_document", "page", "section", "heading", "paragraph", "doc_table", "figure",
        "image", "footnote", "citation", "doc_metadata", "chunk", "embedding_record", "summary",
        "extracted_entity", "extracted_relationship", "redacted_document", "versioned_document",
        "permissioned_document", "indexed_document")),
    ("schema_types", "conceptual", "schema", (
        "sql_ddl", "json_schema", "openapi", "graphql_schema", "protobuf", "avro", "parquet_schema",
        "arrow_schema", "xml_schema", "yaml_config_schema", "pydantic_model", "typescript_interface",
        "orm_model", "dbt_model", "data_contract", "event_schema", "tool_schema", "prompt_input_schema",
        "llm_output_schema")),
    ("crud_state_operations", "operational", "workflow", (
        "create", "read", "update", "delete", "soft_delete", "restore", "archive", "upsert", "merge",
        "patch", "replace", "clone", "fork", "version", "approve", "reject", "publish", "unpublish",
        "promote", "rollback", "expire", "revoke", "grant", "replay", "reprocess")),
    ("systems", "physical", "storage", (
        "relational_database", "document_database", "key_value_store", "column_store", "graph_database",
        "vector_database", "search_engine", "cache", "message_broker", "event_bus", "stream_processor",
        "workflow_engine", "scheduler", "object_storage", "file_system", "data_warehouse", "data_lake",
        "lakehouse_table_format", "api_gateway", "service_mesh", "load_balancer", "identity_provider",
        "secrets_manager", "observability_platform", "ci_system", "cd_system", "container_registry",
        "kubernetes_cluster", "serverless_runtime", "feature_store", "model_registry", "model_server",
        "prompt_registry", "agent_runtime", "evaluation_harness")),
    ("llm_agent_primitives", "runtime", "agent", (
        "prompt_template", "prompt_instance", "system_message", "developer_message", "user_message",
        "tool_schema_record", "tool_call", "tool_result", "observation", "agent_plan", "agent_step",
        "agent_trace", "memory", "vector_memory", "episodic_memory", "semantic_memory", "retrieved_context",
        "context_window", "token_budget", "structured_output", "guardrail", "policy_check", "human_approval",
        "eval_case", "eval_result", "model_response", "conversation", "session", "handoff", "subagent",
        "planner", "executor", "critic", "verifier", "repair_loop")),
    ("operations_primitives", "operational", "observability", (
        "ops_log", "ops_metric", "ops_trace", "span", "alert", "dashboard", "incident", "runbook",
        "postmortem", "slo", "sla", "error_budget", "deployment", "release", "canary", "blue_green",
        "ops_rollback", "health_check", "readiness_probe", "liveness_probe", "autoscaler", "capacity_plan",
        "cost_record", "token_usage_record")),
)
_CROSS_DOMAINS = ("saas_crud", "backend", "frontend", "data_engineering", "analytics", "ml_systems",
                  "llm_systems", "agentic_systems", "cloud_infrastructure", "distributed_systems",
                  "security", "observability", "devops_cicd", "document_processing", "search_retrieval",
                  "streaming", "batch")

# ── Section-5 family F transformations: (name, category, lossy, reversible, streaming, llm_role) ─────────────
_TRANSFORMS: tuple[tuple[str, str, bool, bool, bool, str], ...] = (
    ("parse", "parse", False, True, True, "extraction"), ("extract", "parse", True, False, True, "extraction"),
    ("validate", "validate", False, True, True, "none"), ("clean", "clean", True, False, True, "repair"),
    ("normalize", "normalize", False, True, True, "none"), ("denormalize", "denormalize", False, True, False, "none"),
    ("flatten", "flatten", True, False, True, "none"), ("explode", "explode", False, True, True, "none"),
    ("join", "join", False, False, False, "none"), ("aggregate", "aggregate", True, False, True, "none"),
    ("group_by", "aggregate", True, False, True, "none"), ("window", "window", False, True, True, "none"),
    ("filter", "filter", True, False, True, "none"), ("sort", "sort", False, True, False, "none"),
    ("sample", "sample", True, False, True, "none"), ("split", "split", False, True, True, "none"),
    ("merge", "merge", False, False, True, "none"), ("deduplicate", "deduplicate", True, False, True, "none"),
    ("impute", "clean", False, False, True, "repair"), ("encode", "encode", False, True, True, "none"),
    ("decode", "decode", False, True, True, "none"), ("tokenize", "tokenize", False, True, True, "none"),
    ("chunk_text", "other", False, True, True, "none"), ("summarize", "summarize", True, False, False, "summarization"),
    ("classify", "classify", True, False, True, "classification"), ("embed", "embed", True, False, True, "none"),
    ("vectorize", "embed", True, False, True, "none"), ("index_build", "index", False, True, False, "none"),
    ("retrieve", "retrieve", False, True, True, "none"), ("rerank", "rank", False, True, True, "routing"),
    ("cluster", "cluster", True, False, False, "none"), ("reduce_dimension", "reduce_dimension", True, False, False, "none"),
    ("pca", "reduce_dimension", True, False, False, "none"), ("svd", "reduce_dimension", True, False, False, "none"),
    ("umap", "reduce_dimension", True, False, False, "none"), ("tsne", "reduce_dimension", True, False, False, "none"),
    ("autoencode", "reduce_dimension", True, False, False, "none"), ("quantize", "compress", True, False, True, "none"),
    ("compress", "compress", False, True, True, "none"), ("encrypt", "encrypt", False, True, True, "none"),
    ("decrypt", "encrypt", False, True, True, "none"), ("hash_digest", "encode", True, False, True, "none"),
    ("redact", "redact", True, False, True, "extraction"), ("anonymize", "anonymize", True, False, True, "none"),
    ("pseudonymize", "anonymize", False, True, True, "none"), ("serialize", "serialize", False, True, True, "none"),
    ("deserialize", "deserialize", False, True, True, "none"), ("compile_source", "compile", False, False, False, "none"),
    ("transpile", "compile", False, True, False, "generation"), ("package", "build", False, True, False, "none"),
    ("deploy", "deploy", False, True, False, "none"), ("monitor", "monitor", False, True, True, "none"),
    ("alert_eval", "monitor", False, True, True, "none"), ("audit_record", "audit", False, True, True, "none"),
    ("migrate", "migrate", False, False, False, "planning"), ("backfill", "backfill", False, True, False, "none"),
    ("replicate", "replicate", False, True, True, "none"), ("stream_process", "stream", False, True, True, "none"),
    ("batch_process", "batch", False, True, False, "none"), ("cache_store", "cache", False, True, True, "none"),
    ("materialize", "other", False, True, False, "none"), ("checkpoint", "other", False, True, True, "none"),
    ("replay_events", "other", False, True, True, "none"), ("rollback_state", "other", False, True, False, "none"),
    ("sessionize", "window", False, True, True, "none"), ("enrich", "other", False, True, True, "extraction"),
    ("entity_resolve", "deduplicate", True, False, False, "classification"),
    ("schema_evolve", "migrate", False, False, False, "planning"),
    ("prompt_render", "other", False, True, True, "none"), ("output_validate", "validate", False, True, True, "validation"),
)

# ── family G architectures: (name, category, when_to_use, when_not_to_use) ───────────────────────────────────
_ARCHITECTURES: tuple[tuple[str, str, str, str], ...] = (
    ("layered_architecture", "monolith", "clear separation of ui/logic/data in one deployable", "high independent-scaling needs"),
    ("hexagonal_architecture", "modular_monolith", "domain isolation behind ports/adapters", "tiny scripts and one-off tools"),
    ("clean_architecture", "modular_monolith", "long-lived business core independent of frameworks", "throwaway prototypes"),
    ("monolith", "monolith", "small team, one product, fast iteration", "many teams shipping independently"),
    ("modular_monolith", "modular_monolith", "module boundaries without ops overhead", "independent scaling/deploy needs"),
    ("microservices", "microservices", "independent teams, independent scaling", "small team; latency-sensitive chatty calls"),
    ("service_oriented_architecture", "microservices", "enterprise integration across systems", "single small product"),
    ("event_driven_architecture", "event_driven", "loose coupling, audit trails, async workflows", "simple synchronous crud"),
    ("message_queue_architecture", "event_driven", "spiky load leveling, retries, DLQs", "hard real-time request/response"),
    ("stream_processing_architecture", "streaming", "continuous transforms and real-time features", "small nightly batches"),
    ("batch_processing_architecture", "batch", "scheduled large-volume recomputation", "sub-second freshness needs"),
    ("etl", "batch", "transform before load into curated stores", "warehouse-native transform teams"),
    ("elt", "batch", "load raw then transform in-warehouse (dbt-style)", "strict pre-load compliance filtering"),
    ("lakehouse", "lakehouse", "one storage layer for BI + ML with table formats", "tiny relational-only workloads"),
    ("data_warehouse", "warehouse", "governed analytics and BI", "unstructured/media-heavy data"),
    ("data_lake", "lakehouse", "cheap raw multi-format storage", "strong transactional guarantees"),
    ("data_mesh", "lakehouse", "domain-owned data products at org scale", "single small data team"),
    ("cqrs", "event_driven", "read/write models with different shapes/scale", "simple symmetrical crud"),
    ("event_sourcing", "event_driven", "full history, replay, audit as first-class", "teams unready for eventual consistency"),
    ("workflow_orchestration", "workflow", "multi-step long-running processes with retries", "single-step handlers"),
    ("state_machine_architecture", "workflow", "explicit states/transitions with guards", "free-form unbounded flows"),
    ("serverless_architecture", "serverless", "spiky event-driven compute, low ops", "long-running stateful compute"),
    ("edge_architecture", "edge", "latency-critical or offline-capable clients", "centralized heavy compute"),
    ("mobile_offline_first", "edge", "unreliable connectivity with sync", "always-online admin tools"),
    ("search_architecture", "search", "keyword/faceted retrieval at scale", "pure key lookups"),
    ("semantic_search_architecture", "search", "meaning-based retrieval over embeddings", "exact-match compliance lookups"),
    ("rag_architecture", "rag", "grounded LLM answers over private corpora", "closed-book creative generation"),
    ("agentic_architecture", "agentic", "multi-step tool-using LLM tasks with traces", "single-shot classification"),
    ("tool_calling_architecture", "agentic", "typed function calls from model outputs", "free-text-only integrations"),
    ("multi_agent_architecture", "agentic", "decomposed roles (planner/executor/critic)", "tasks one agent handles cheaper"),
    ("ml_training_architecture", "ml", "reproducible experiment/training pipelines", "static rule-based systems"),
    ("model_serving_architecture", "ml", "low-latency/batch inference with rollout gates", "offline-only analytics"),
    ("feature_store_architecture", "ml", "shared online/offline features, point-in-time", "single-model one-off features"),
    ("observability_architecture", "observability", "logs/metrics/traces with SLOs and alerts", "unmonitored throwaway scripts"),
    ("zero_trust_architecture", "security", "identity-based least-privilege everywhere", "isolated single-user tools"),
    ("ci_cd_architecture", "other", "automated build/test/deploy gates", "manual one-off deployments"),
    ("gitops_architecture", "other", "declarative infra reconciled from git", "imperative snowflake environments"),
    ("plugin_architecture", "other", "third-party extensibility behind stable seams", "fully closed products"),
    ("compiler_pipeline_architecture", "other", "staged parse/analyze/transform/emit", "trivial string templating"),
    ("distributed_database_architecture", "distributed", "horizontal scale with replication/consensus", "single-node fits-in-RAM data"),
)

_TYPE_MAP = {"id": ("TEXT PRIMARY KEY", "string", "str", "string"), "string": ("TEXT", "string", "str", "string"),
             "text": ("TEXT", "string", "str", "string"), "int": ("INTEGER", "integer", "int", "number"),
             "float": ("REAL", "number", "float", "number"), "bool": ("INTEGER", "boolean", "bool", "boolean"),
             "timestamp": ("TIMESTAMP", "string", "str", "string"), "json": ("TEXT", "object", "dict", "Record<string, unknown>"),
             "string_list": ("TEXT", "array", "list", "string[]")}

# ── Section-6 schema objects: name -> ((field, type, required, note), ...); flags: relational/api/event ──────
_F = lambda *rows: tuple(rows)  # noqa: E731
_SCHEMA_OBJECTS: dict[str, dict[str, Any]] = {
    "user": {"relational": True, "api": True, "event": False, "fields": _F(
        ("user_id", "id", True, "stable id"), ("organization_id", "string", True, "tenant scope"),
        ("email", "string", True, "unique per org"), ("display_name", "string", False, "full words"),
        ("status", "string", True, "active|suspended|deactivated"), ("created_at", "timestamp", True, ""),
        ("updated_at", "timestamp", True, ""), ("deleted_at", "timestamp", False, "soft delete"))},
    "organization": {"relational": True, "api": True, "event": False, "fields": _F(
        ("organization_id", "id", True, ""), ("name", "string", True, ""), ("plan", "string", True, "free|pro|enterprise"),
        ("region", "string", False, ""), ("created_at", "timestamp", True, ""), ("deleted_at", "timestamp", False, ""))},
    "role": {"relational": True, "api": True, "event": False, "fields": _F(
        ("role_id", "id", True, ""), ("organization_id", "string", True, ""), ("name", "string", True, ""),
        ("permissions", "string_list", True, "permission keys"), ("created_at", "timestamp", True, ""))},
    "permission": {"relational": True, "api": True, "event": False, "fields": _F(
        ("permission_id", "id", True, ""), ("principal_type", "string", True, "user|role|service"),
        ("principal_id", "string", True, ""), ("resource_type", "string", True, ""), ("resource_id", "string", True, ""),
        ("actions", "string_list", True, "read|write|admin"), ("scope", "string", True, "org|project|resource"),
        ("expires_at", "timestamp", False, ""))},
    "document": {"relational": True, "api": True, "event": False, "fields": _F(
        ("document_id", "id", True, ""), ("organization_id", "string", True, ""), ("title", "string", True, ""),
        ("source", "string", True, "origin system"), ("mime_type", "string", True, ""),
        ("storage_uri", "string", True, "object-storage handle, never the body"), ("content_digest", "string", True, "sha256"),
        ("owner_id", "string", True, ""), ("created_at", "timestamp", True, ""), ("deleted_at", "timestamp", False, ""))},
    "parsed_document": {"relational": True, "api": False, "event": False, "fields": _F(
        ("parsed_document_id", "id", True, ""), ("document_id", "string", True, ""), ("parser_version", "string", True, ""),
        ("language", "string", False, ""), ("page_count", "int", True, ""), ("sections", "json", False, "section tree"),
        ("parsed_at", "timestamp", True, ""))},
    "document_chunk": {"relational": True, "api": True, "event": False, "fields": _F(
        ("chunk_id", "id", True, ""), ("document_id", "string", True, ""), ("section_path", "string_list", False, ""),
        ("page_start", "int", False, ""), ("page_end", "int", False, ""), ("text", "text", True, ""),
        ("token_count", "int", True, ""), ("chunker_version", "string", True, ""))},
    "embedding_record": {"relational": True, "api": False, "event": True, "fields": _F(
        ("embedding_id", "id", True, ""), ("chunk_id", "string", True, ""), ("model", "string", True, ""),
        ("dimension", "int", True, ""), ("vector_ref", "string", True, "store handle; vectors live in the index"),
        ("visibility", "string", True, "internal|tenant|public"), ("created_at", "timestamp", True, ""))},
    "support_ticket": {"relational": True, "api": True, "event": False, "fields": _F(
        ("ticket_id", "id", True, ""), ("organization_id", "string", True, ""), ("requester_user_id", "string", True, ""),
        ("subject", "string", True, ""), ("status", "string", True, "open|pending|resolved|closed"),
        ("priority", "string", False, "low|medium|high|urgent"), ("assigned_agent_id", "string", False, ""),
        ("created_at", "timestamp", True, ""), ("updated_at", "timestamp", True, ""))},
    "ticket_message": {"relational": True, "api": True, "event": False, "fields": _F(
        ("message_id", "id", True, ""), ("ticket_id", "string", True, ""), ("sender_type", "string", True, "customer|agent|system"),
        ("sender_id", "string", True, ""), ("body", "text", True, ""), ("channel", "string", False, "email|chat|api"),
        ("created_at", "timestamp", True, ""))},
    "event_envelope": {"relational": False, "api": False, "event": True, "fields": _F(
        ("event_id", "id", True, ""), ("event_type", "string", True, "object.verb"), ("event_version", "int", True, ""),
        ("occurred_at", "timestamp", True, ""), ("actor_type", "string", True, "user|service|agent"),
        ("actor_id", "string", True, ""), ("object_type", "string", True, ""), ("object_id", "string", True, ""),
        ("before", "json", False, "prior state"), ("after", "json", False, "new state"), ("context", "json", False, "org/ip/ua"))},
    "audit_event": {"relational": True, "api": False, "event": True, "fields": _F(
        ("audit_id", "id", True, ""), ("actor_id", "string", True, ""), ("action", "string", True, "resource.verb"),
        ("resource_type", "string", True, ""), ("resource_id", "string", True, ""), ("occurred_at", "timestamp", True, ""),
        ("metadata", "json", False, "model/prompt/review flags"))},
    "workflow_definition": {"relational": True, "api": True, "event": False, "fields": _F(
        ("workflow_id", "id", True, ""), ("name", "string", True, ""), ("schema_version", "int", True, "version in metadata"),
        ("steps", "json", True, "ordered step specs"), ("created_at", "timestamp", True, ""))},
    "workflow_run": {"relational": True, "api": True, "event": True, "fields": _F(
        ("run_id", "id", True, ""), ("workflow_id", "string", True, ""), ("organization_id", "string", True, ""),
        ("status", "string", True, "pending|running|completed|failed|cancelled"), ("current_step", "string", False, ""),
        ("started_at", "timestamp", True, ""), ("ended_at", "timestamp", False, ""))},
    "agent_task": {"relational": True, "api": True, "event": True, "fields": _F(
        ("task_id", "id", True, ""), ("user_id", "string", True, ""), ("goal", "text", True, ""),
        ("status", "string", True, "pending|in_progress|completed|failed"), ("allowed_tools", "string_list", True, ""),
        ("requires_human_approval", "bool", True, ""), ("created_at", "timestamp", True, ""))},
    "agent_step": {"relational": True, "api": False, "event": True, "fields": _F(
        ("step_id", "id", True, ""), ("task_id", "string", True, ""), ("step_index", "int", True, ""),
        ("kind", "string", True, "plan|tool_call|observation|repair|approval"), ("summary", "text", True, ""),
        ("started_at", "timestamp", True, ""), ("ended_at", "timestamp", False, ""))},
    "tool_call": {"relational": True, "api": False, "event": True, "fields": _F(
        ("tool_call_id", "id", True, ""), ("task_id", "string", True, ""), ("tool_name", "string", True, ""),
        ("arguments", "json", True, ""), ("status", "string", True, "pending|completed|failed"),
        ("output_ref", "string", False, "handle to stored output"), ("started_at", "timestamp", True, ""),
        ("ended_at", "timestamp", False, ""))},
    "tool_result": {"relational": False, "api": False, "event": True, "fields": _F(
        ("tool_call_id", "id", True, ""), ("ok", "bool", True, ""), ("result", "json", False, ""),
        ("error", "string", False, ""), ("duration_ms", "int", True, ""))},
    "prompt_template": {"relational": True, "api": True, "event": False, "fields": _F(
        ("template_id", "id", True, ""), ("name", "string", True, ""), ("schema_version", "int", True, ""),
        ("system_message", "text", True, ""), ("input_variables", "string_list", True, ""),
        ("output_schema", "json", True, ""), ("created_at", "timestamp", True, ""))},
    "prompt_instance": {"relational": True, "api": False, "event": True, "fields": _F(
        ("prompt_instance_id", "id", True, ""), ("template_id", "string", True, ""), ("model", "string", True, ""),
        ("inputs", "json", True, ""), ("retrieved_context_ids", "string_list", False, ""),
        ("token_count_input", "int", True, ""), ("token_count_output", "int", False, ""), ("created_at", "timestamp", True, ""))},
    "structured_llm_output": {"relational": False, "api": True, "event": True, "fields": _F(
        ("output_id", "id", True, ""), ("prompt_instance_id", "string", True, ""), ("payload", "json", True, "schema-validated"),
        ("confidence", "float", False, ""), ("requires_human_review", "bool", True, ""),
        ("review_reason", "string", False, ""), ("created_at", "timestamp", True, ""))},
    "eval_case": {"relational": True, "api": False, "event": False, "fields": _F(
        ("eval_case_id", "id", True, ""), ("suite", "string", True, ""), ("input", "json", True, ""),
        ("expected_output", "json", True, ""), ("tags", "string_list", False, ""))},
    "eval_result": {"relational": True, "api": False, "event": True, "fields": _F(
        ("eval_result_id", "id", True, ""), ("eval_case_id", "string", True, ""), ("model", "string", True, ""),
        ("model_output", "json", True, ""), ("passed", "bool", True, ""), ("failure_reason", "string", False, ""),
        ("evaluated_at", "timestamp", True, ""))},
    "model_artifact": {"relational": True, "api": True, "event": False, "fields": _F(
        ("model_artifact_id", "id", True, ""), ("name", "string", True, ""), ("model_version", "string", True, ""),
        ("dataset_version", "string", True, ""), ("parameters", "json", False, ""), ("metrics", "json", False, ""),
        ("artifact_uri", "string", True, "registry handle"), ("registered_at", "timestamp", True, ""))},
    "model_deployment": {"relational": True, "api": True, "event": True, "fields": _F(
        ("deployment_id", "id", True, ""), ("model_artifact_id", "string", True, ""), ("environment", "string", True, "dev|staging|prod"),
        ("endpoint", "string", True, ""), ("rollout", "string", True, "shadow|canary|full"),
        ("status", "string", True, "active|rolled_back|retired"), ("deployed_at", "timestamp", True, ""))},
    "metric_record": {"relational": False, "api": False, "event": True, "fields": _F(
        ("metric_name", "string", True, ""), ("occurred_at", "timestamp", True, ""), ("value", "float", True, ""),
        ("tags", "json", False, "service/model/endpoint/env"))},
    "trace_span": {"relational": False, "api": False, "event": True, "fields": _F(
        ("trace_id", "string", True, ""), ("span_id", "id", True, ""), ("parent_span_id", "string", False, ""),
        ("name", "string", True, ""), ("started_at", "timestamp", True, ""), ("duration_ms", "int", True, ""),
        ("attributes", "json", False, ""))},
    "data_contract": {"relational": True, "api": True, "event": False, "fields": _F(
        ("contract_id", "id", True, ""), ("producer", "string", True, ""), ("consumer", "string", True, ""),
        ("schema_ref", "string", True, ""), ("schema_version", "int", True, ""), ("freshness_sla", "string", False, ""),
        ("quality_checks", "string_list", False, ""), ("effective_at", "timestamp", True, ""))},
    "feature_definition": {"relational": True, "api": True, "event": False, "fields": _F(
        ("feature_id", "id", True, ""), ("name", "string", True, ""), ("entity", "string", True, "customer|user|ticket"),
        ("dtype", "string", True, "int|float|string|bool"), ("source", "string", True, ""),
        ("window", "string", False, "7d|30d|90d"), ("created_at", "timestamp", True, ""))},
    "feature_value": {"relational": True, "api": False, "event": True, "fields": _F(
        ("feature_id", "string", True, ""), ("entity_id", "string", True, ""), ("event_timestamp", "timestamp", True, ""),
        ("value", "json", True, "typed by definition"))},
}

_TOOLS: tuple[tuple[str, str, str, bool, bool], ...] = (  # (name, category, description, approval, safe_auto)
    ("read_file", "file", "read a file by path", False, True),
    ("write_file", "file", "write/overwrite a file", False, True),
    ("edit_file", "file", "apply a patch to a file", False, True),
    ("list_files", "file", "list a directory tree", False, True),
    ("search_repository", "code", "search code/text across the repo", False, True),
    ("parse_code", "code", "parse source into an AST/symbols", False, True),
    ("run_tests", "test", "run the test suite in a sandbox", False, True),
    ("run_shell_command", "shell", "execute a shell command", True, False),
    ("query_database", "database", "run a read-only SQL query", False, True),
    ("execute_sql_mutation", "database", "run INSERT/UPDATE/DELETE SQL", True, False),
    ("generate_sql", "database", "draft SQL from natural language", False, True),
    ("search_web", "web", "public web search", False, True),
    ("fetch_url", "web", "fetch a public page", False, True),
    ("fetch_pdf", "web", "fetch and extract a public PDF", False, True),
    ("extract_document", "docs", "parse a document into sections/tables", False, True),
    ("embed_text", "vector", "embed text into a vector", False, True),
    ("vector_search", "vector", "nearest-neighbor search over an index", False, True),
    ("call_llm", "llm", "call a model with a prompt (+ optional schema)", False, True),
    ("validate_json", "code", "validate JSON against a schema", False, True),
    ("validate_schema", "code", "check a schema definition itself", False, True),
    ("call_api", "api", "call a registered external API", True, False),
    ("create_ticket", "api", "open a ticket in the tracker", False, True),
    ("update_ticket", "api", "update ticket fields/status", False, True),
    ("open_pull_request", "code", "open a PR from a branch", False, True),
    ("comment_on_pull_request", "code", "add a PR review comment", False, True),
    ("deploy_service", "deploy", "deploy a service version", True, False),
    ("rollback_deployment", "deploy", "revert to the previous version", True, False),
    ("query_logs", "monitor", "search structured logs", False, True),
    ("query_metrics", "monitor", "query metric time series", False, True),
    ("create_alert", "monitor", "configure an alert rule", True, False),
    ("scan_dependencies", "security", "scan deps for CVEs", False, True),
    ("scan_secrets", "security", "scan for leaked secrets", False, True),
    ("summarize_incident", "docs", "draft an incident summary from telemetry", False, True),
    ("request_human_approval", "other", "block on an explicit human approval gate", False, True),
)

_PLAYBOOKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("issue_to_pull_request", "turn a tracked issue into a reviewed pull request",
     ("read issue + linked context", "locate affected files via repository search", "draft plan with file list",
      "edit files + generate tests", "run tests and repair failures", "open PR with summary + trace")),
    ("log_to_root_cause", "triage an error signature to a root-cause hypothesis",
     ("collect log window + trace ids", "cluster error signatures", "correlate deploys/config changes",
      "rank hypotheses with evidence", "draft remediation + verification steps")),
    ("schema_to_crud_api", "generate a CRUD API from an object schema",
     ("load field spec", "render SQL DDL + migrations", "render handlers + validation", "render tests",
      "wire audit + permission checks", "run tests")),
    ("document_to_rag_index", "ingest a document set into a retrieval index",
     ("register sources with digests", "parse + section documents", "chunk with overlap", "embed chunks",
      "upsert vectors + metadata", "run retrieval smoke queries")),
    ("database_to_analytics_model", "derive fact/dimension models from an OLTP schema",
     ("profile tables + keys", "propose star schema", "render dbt-style models + tests", "backfill plan",
      "metric definitions")),
    ("source_system_to_data_pipeline", "stand up an incremental extract-load pipeline",
     ("catalog source objects", "choose sync keys + watermarks", "render extract/load jobs", "add validation checks",
      "schedule + monitor")),
    ("event_schema_to_stream_processor", "generate a stream job from an event schema",
     ("load event schema", "define transforms/windows", "render processor + DLQ handling", "replay/backfill plan",
      "lag + error monitoring")),
    ("prompt_template_to_eval_harness", "build an eval suite for a prompt template",
     ("enumerate input variables + output schema", "draft eval cases incl. adversarial", "run cases",
      "score + segment failures", "gate promotion on pass rate")),
    ("model_artifact_to_serving_endpoint", "deploy a registered model behind an endpoint",
     ("load artifact + schema contract", "render server + health checks", "shadow deploy", "canary compare",
      "promote or rollback")),
    ("support_ticket_to_recommended_response", "draft a grounded reply for a support ticket",
     ("summarize thread", "retrieve KB chunks", "draft structured reply with citations", "risk-check + confidence",
      "route to human review")),
    ("security_finding_to_patch", "turn a scanner finding into a reviewed fix",
     ("reproduce finding", "locate vulnerable path", "draft minimal patch + test", "re-scan", "open PR flagged for security review")),
    ("failing_test_to_fix", "repair a failing test",
     ("run test + capture failure", "localize fault", "draft fix", "re-run suite", "explain change in PR")),
    ("legacy_code_to_modernized_code", "migrate a module to the target stack",
     ("inventory symbols + callers", "define equivalence tests", "transform incrementally", "run both paths side-by-side",
      "cut over + keep rollback")),
    ("requirements_to_architecture", "turn requirements into candidate architectures",
     ("extract constraints + scale targets", "shortlist architectures from the catalog", "score tradeoffs",
      "draft ADR with the runner-ups preserved")),
    ("architecture_to_implementation_plan", "expand an ADR into a build plan",
     ("decompose into components", "map to primitives + schemas", "order by dependency", "define gates + tests per step")),
    ("cloud_cost_spike_to_remediation_plan", "diagnose and remediate a cost spike",
     ("pull cost by service/day", "diff against baseline", "attribute to resources/queries", "draft remediations with savings estimates",
      "approval gate before applying")),
    ("incident_to_postmortem", "produce a postmortem from incident telemetry",
     ("assemble timeline from alerts/logs/deploys", "identify contributing causes", "draft action items with owners",
      "review gate")),
    ("raw_data_to_feature_store", "promote raw signals into governed features",
     ("profile candidate signals", "define features + windows", "point-in-time backfill", "online materialization",
      "drift monitors")),
    ("workflow_spec_to_state_machine", "compile a workflow spec into a state machine",
     ("parse steps + transitions", "validate reachability/terminality", "render machine + retries/compensation",
      "simulate runs", "emit run telemetry")),
    ("api_spec_to_client_and_server_stubs", "generate stubs from an OpenAPI spec",
     ("validate spec", "render server stubs + validators", "render typed client", "contract tests", "publish artifacts")),
)

_LLM_OBSERVABILITY = ("prompt_version", "model_version", "input_tokens", "output_tokens", "total_tokens",
                      "latency", "cost", "retrieved_context_count", "retrieval_score", "tool_call_count",
                      "tool_error_count", "human_approval_count", "refusal_count", "invalid_output_count",
                      "schema_validation_failure_count", "hallucination_report_count", "user_feedback_score",
                      "eval_pass_rate")


# ── record builders ───────────────────────────────────────────────────────────────────────────────────────────
def _jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def build_primitive_records() -> list[dict]:
    out = []
    for family, layer, category, items in _FAMILIES:
        for name in items:
            words = name.replace("_", " ")
            cited = _cited_refs_for(name)
            out.append({
                "id": f"primitive.{layer}.{name}", "name": words.title(), "aliases": [], "category": category,
                "layer": layer, "definition": f"The {words} primitive of the {family.replace('_', ' ')} family.",
                "what_it_represents": f"A {words} as used across {category} systems in this domain.",
                "why_it_is_useful": f"Standardizes how {words} objects are created, validated, transformed, indexed, and governed.",
                "example_instances": [f"generated_schemas/json_schema/{name}.example.json"
                                      if name in _SCHEMA_OBJECTS else f"{name}_example_1"],
                "domains": list(_CROSS_DOMAINS[:6]),
                "source_refs": [s[0] for s in _OWNER_SOURCES] + cited,
                "confidence": 0.7 if cited else 0.6,
                "crud": {"create": [f"op.{name}.create"], "read": [f"op.{name}.read"],
                         "update": [f"op.{name}.update"], "delete": [f"op.{name}.delete"],
                         "soft_delete": [f"op.{name}.soft_delete"], "archive": [f"op.{name}.archive"],
                         "restore": [f"op.{name}.restore"]},
                "transformations": [f"transform.validate.validate", f"transform.serialize.serialize"],
                "schemas": [f"schema.json_schema.{name}" if name in _SCHEMA_OBJECTS else "schema.json_schema.event_envelope"],
                "storage_options": ["relational_database", "object_storage", "jsonl_staging"],
                "index_options": ["btree_by_id", "lexical_inverted", "vector_semantic", "lsh_blocking"],
                "compute_requirements": ["cpu_baseline"], "bandwidth_transfer_considerations": ["payload_size", "egress_cost"],
                "security_privacy_considerations": ["tenant_isolation", "least_privilege", "no_raw_pii"],
                "observability_metrics": ["count", "error_rate", "latency"],
                "failure_modes": ["schema_drift", "orphaned_references", "stale_state"],
                "tests": ["schema_validation", "crud_roundtrip"], "related_primitives": [],
                "parent_ids": [], "child_ids": [], "llm_assistance_opportunities": ["summarize", "classify"],
                "agentic_tool_opportunities": ["validate_json", "query_database"],
                "human_review_required_for": ["delete", "permission_changes"],
                "implementation_notes": ["ids stable; version in schema_version metadata, never in the name"],
                "generation_pass": "pass_b_normalization",
                "provenance": "owner_cited_reference" if cited else "inferred_from_owner_decompositions",
                **BOUNDARY})
    return out


def build_transform_records() -> list[dict]:
    out = []
    for name, category, lossy, reversible, streaming, llm_role in _TRANSFORMS:
        words = name.replace("_", " ")
        cited = _cited_refs_for(name)
        out.append({
            "id": f"transform.{category}.{name}", "name": words.title(), "category": category,
            "definition": f"{words} applied to catalog structures.",
            "input_types": ["record", "table", "document_chunk", "event"], "output_types": ["record", "table", "event"],
            "preconditions": ["input validates against its schema"], "postconditions": ["output validates against its schema"],
            "is_reversible": reversible, "is_lossy": lossy, "is_idempotent": name not in ("merge", "backfill", "replay_events"),
            "batch_compatible": True, "streaming_compatible": streaming, "real_time_compatible": streaming,
            "deterministic": llm_role == "none", "llm_enhanced": llm_role != "none", "llm_role": llm_role,
            "common_tools": ["python", "sql", "spark"], "example": f"{words} over a support-ticket table",
            "pseudo_code": f"def {name}(rows): ...", "schemas_involved": ["schema.json_schema.event_envelope"],
            "failure_modes": ["schema_mismatch", "partial_failure"], "quality_checks": ["row_counts", "null_rates"],
            "security_privacy_considerations": ["redact_before_export"] if lossy else [],
            "bandwidth_transfer_considerations": ["chunked_io"],
            "source_refs": [s[0] for s in _OWNER_SOURCES] + cited,
            "confidence": 0.7 if cited else 0.6,
            "provenance": "owner_cited_reference" if cited else "inferred_from_owner_decompositions",
            "generation_pass": "pass_f_synthesis", **BOUNDARY})
    return out


def build_architecture_records() -> list[dict]:
    out = []
    for name, category, use, avoid in _ARCHITECTURES:
        words = name.replace("_", " ")
        out.append({
            "id": f"arch.{category}.{name}", "name": words.title(), "category": category,
            "definition": f"The {words} pattern.", "when_to_use": [use], "when_not_to_use": [avoid],
            "components": ["api", "storage", "workers"], "data_structures": ["record", "event", "index"],
            "schemas": ["schema.json_schema.event_envelope"], "transformations": ["transform.validate.validate"],
            "compute_patterns": ["horizontal_scaling"], "storage_patterns": ["tiered_storage"],
            "network_patterns": ["same_region_low_latency"], "serving_patterns": ["api_endpoint"],
            "crud_patterns": ["audited_writes"], "failure_modes": ["partial_outage", "backpressure"],
            "observability": ["logs", "metrics", "traces", "alerts"],
            "security_privacy_governance": ["least_privilege", "tenant_isolation", "audit_log"],
            "tradeoffs": [f"use: {use}; avoid: {avoid}"], "example_system": f"{name}_reference",
            "diagram_mermaid": f"flowchart LR; client-->{name}; {name}-->storage",
            "source_refs": [s[0] for s in _OWNER_SOURCES], "confidence": 0.6,
            "provenance": "inferred_from_owner_decompositions", "generation_pass": "pass_f_synthesis", **BOUNDARY})
    return out


def build_schema_records() -> list[dict]:
    out = []
    for name, spec in sorted(_SCHEMA_OBJECTS.items()):
        fields = [{"name": f, "type": t, "required": req, "note": note} for f, t, req, note in spec["fields"]]
        out.append({
            "id": f"schema.json_schema.{name}", "name": name.replace("_", " ").title(), "format": "json_schema",
            "purpose": f"canonical {name.replace('_', ' ')} contract", "represents": name,
            "fields": fields, "relationships": [], "constraints": ["required fields non-null"],
            "versioning_strategy": "schema_version integer in metadata; additive evolution",
            "evolution_rules": ["add optional fields only", "never repurpose a field"],
            "crud_operations": ["create", "read", "update", "soft_delete"],
            "validations": ["type check", "required check"], "transformations": ["serialize", "validate", "redact"],
            "example_schema": f"generated_schemas/json_schema/{name}.json",
            "example_payload": f"generated_schemas/json_schema/{name}.example.json",
            "source_refs": [s[0] for s in _OWNER_SOURCES] + _cited_refs_for(name),
            "confidence": 0.75 if _cited_refs_for(name) else 0.7,
            "provenance": "owner_cited_reference" if _cited_refs_for(name) else "inferred_from_owner_decompositions",
            "generation_pass": "pass_f_synthesis", **BOUNDARY})
    return out


# ── concrete schema renderers (ONE field spec -> every format) ───────────────────────────────────────────────
def render_sql(name: str, spec: dict) -> str:
    cols = ",\n    ".join(f"{f} {_TYPE_MAP[t][0]}{'' if req or t == 'id' else ''}" for f, t, req, _ in spec["fields"])
    return f"CREATE TABLE IF NOT EXISTS {name}s (\n    {cols}\n);\n"


def render_json_schema(name: str, spec: dict) -> dict:
    props = {f: {"type": _TYPE_MAP[t][1], "description": note} for f, t, _, note in spec["fields"]}
    for f, t, _, _n in spec["fields"]:
        if t == "string_list":
            props[f]["items"] = {"type": "string"}
    return {"$id": f"schema.json_schema.{name}", "title": name, "type": "object",
            "required": [f for f, _, req, _ in spec["fields"] if req], "properties": props,
            "additionalProperties": False}


def render_pydantic(name: str, spec: dict) -> str:
    camel = "".join(w.title() for w in name.split("_"))
    py = {"id": "str", "string": "str", "text": "str", "int": "int", "float": "float", "bool": "bool",
          "timestamp": "str", "json": "dict", "string_list": "list[str]"}
    lines = [f"class {camel}(BaseModel):", f'    """{name.replace("_", " ")} record (candidate; serves_truth=false)."""']
    for f, t, req, note in spec["fields"]:
        default = "" if req else " = None"
        typ = py[t] if req else f"Optional[{py[t]}]"
        lines.append(f"    {f}: {typ}{default}{('  # ' + note) if note else ''}")
    return "\n".join(lines) + "\n"


def render_typescript(name: str, spec: dict) -> str:
    camel = "".join(w.title() for w in name.split("_"))
    lines = [f"export interface {camel} {{"]
    for f, t, req, note in spec["fields"]:
        lines.append(f"  {f}{'' if req else '?'}: {_TYPE_MAP[t][3]};{(' // ' + note) if note else ''}")
    return "\n".join(lines) + "\n}\n"


def render_avro(name: str, spec: dict) -> dict:
    amap = {"id": "string", "string": "string", "text": "string", "int": "long", "float": "double",
            "bool": "boolean", "timestamp": "string", "json": "string", "string_list": {"type": "array", "items": "string"}}
    fields = [{"name": f, "type": amap[t] if req else ["null", amap[t]]} for f, t, req, _ in spec["fields"]]
    return {"type": "record", "name": "".join(w.title() for w in name.split("_")),
            "namespace": "catalog.generated", "fields": fields}


def render_protobuf(name: str, spec: dict) -> str:
    pmap = {"id": "string", "string": "string", "text": "string", "int": "int64", "float": "double",
            "bool": "bool", "timestamp": "string", "json": "string", "string_list": "repeated string"}
    camel = "".join(w.title() for w in name.split("_"))
    lines = ['syntax = "proto3";', "package catalog.generated;", "", f"message {camel} {{"]
    for i, (f, t, _req, note) in enumerate(spec["fields"], 1):
        lines.append(f"  {pmap[t]} {f} = {i};{('  // ' + note) if note else ''}")
    return "\n".join(lines) + "\n}\n"


def render_graphql(name: str, spec: dict) -> str:
    gmap = {"id": "ID", "string": "String", "text": "String", "int": "Int", "float": "Float",
            "bool": "Boolean", "timestamp": "String", "json": "String", "string_list": "[String!]"}
    camel = "".join(w.title() for w in name.split("_"))
    lines = [f"type {camel} {{"]
    for f, t, req, _note in spec["fields"]:
        lines.append(f"  {f}: {gmap[t]}{'!' if req else ''}")
    return "\n".join(lines) + "\n}\n"


def render_openapi_component(name: str, spec: dict) -> dict:
    js = render_json_schema(name, spec)
    js.pop("$id", None)
    return {name: js}


def _example_payload(spec: dict) -> dict:
    ex = {"id": "example_1", "string": "example", "text": "example text", "int": 1, "float": 0.5, "bool": True,
          "timestamp": _FIXED_TIMESTAMP, "json": {}, "string_list": ["example"]}
    return {f: ex[t] for f, t, req, _ in spec["fields"] if req}


# ── artifact writers ─────────────────────────────────────────────────────────────────────────────────────────
def _w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write_run(out_dir: Path, *, run_id: str = _DEFAULT_RUN_ID, timestamp: str = _FIXED_TIMESTAMP,
              domain: str = _DEFAULT_DOMAIN, max_iterations: int = 5) -> dict[str, Any]:
    root = out_dir / run_id
    primitives = build_primitive_records()
    transforms = build_transform_records()
    schemas = build_schema_records()
    architectures = build_architecture_records()

    _w(root / "run_config.json", json.dumps({
        "run_id": run_id, "domain": domain, "objective": _USER_GOAL, "constraints": list(_CONSTRAINTS),
        "available_tools": ["file", "shell", "sqlite", "local_embedders", "governed_scrape_loop(opt-in)"],
        "timestamp": timestamp, "deterministic_settings": {"temperature": 0, "fixed_timestamp": timestamp,
                                                           "stable_sorting": True, "stable_ids": True},
        "max_iterations": max_iterations, "iteration": 2,
        "source_policy": "public sources only; live scraping via continuous_primitive_scrape_loop --live after review",
        "artifact_paths": sorted(["primitive_catalog.jsonl", "transformation_catalog.jsonl", "schema_catalog.jsonl",
                                  "architecture_catalog.jsonl", "crud_matrix.csv", "transformation_matrix.csv",
                                  "architecture_matrix.csv", "tool_registry.json", "agent_playbooks.md"]),
        "known_limitations": ["full web verification pass pending (see pending_tool_requests.jsonl)",
                              "owner-cited references attached but not independently fetched",
                              "records without cited refs remain inferred"],
        **BOUNDARY}, indent=2, sort_keys=True))

    queries = [{"query_id": f"q{str(i + 1).zfill(3)}", "query_text": f"{c}: canonical structures, schemas, operations, and failure modes",
                "category": c, "intended_information": f"primitives + transformations + architectures for {c}",
                "priority": 1 if i < 20 else 2, "expected_source_types": ["official_spec", "official_docs", "standards_body"]}
               for i, c in enumerate(_RESEARCH_CATEGORIES)]
    _w(root / "research_queries.jsonl", _jsonl(queries))
    _w(root / "pending_tool_requests.jsonl", _jsonl([
        {"request": "web.search+web.fetch pass over research_queries.jsonl", "status": "blocked_by_missing_tool",
         "reason": "live scraping is opt-in per repo source policy; run continuous_primitive_scrape_loop --live "
                   "--use-llm after source-policy review to fill source_ledger.jsonl", "query_ids": [q["query_id"] for q in queries]}]))
    _w(root / "source_ledger.jsonl", _jsonl([
        {"source_id": sid, "url": path, "title": title, "publisher": "owner", "retrieved_at": timestamp,
         "source_type": "owner_supplied_decomposition", "query_ids": [], "useful_sections": ["all"],
         "reliability_score": 4, "notes": "distilled into the role-matrix vocabulary seam",
         "claims_extracted": "facet taxonomies (see vocabularies/*-role-matrix.yaml)"}
        for sid, path, title in _OWNER_SOURCES] + [
        {"source_id": sid, "url": url, "title": title, "publisher": publisher, "retrieved_at": timestamp,
         "source_type": "owner_cited_reference", "query_ids": [], "useful_sections": ["as cited"],
         "reliability_score": 3, "notes": "cited inside an owner-supplied decomposition; content not yet "
                                          "independently fetched (full verification pass pending)",
         "claims_extracted": f"attached to records tagged: {', '.join(tags)}"}
        for sid, url, title, publisher, tags in _CITED_SOURCES]))

    _w(root / "ontology.json", json.dumps({
        "families": {family: {"layer": layer, "category": category, "count": len(items), "items": sorted(items)}
                     for family, layer, category, items in _FAMILIES},
        "transform_categories": sorted({t[1] for t in _TRANSFORMS}),
        "architecture_categories": sorted({a[1] for a in _ARCHITECTURES}),
        "cross_domains": list(_CROSS_DOMAINS), **BOUNDARY}, indent=2, sort_keys=True))

    _w(root / "primitive_catalog.jsonl", _jsonl(primitives))
    _w(root / "transformation_catalog.jsonl", _jsonl(transforms))
    _w(root / "schema_catalog.jsonl", _jsonl(schemas))
    _w(root / "architecture_catalog.jsonl", _jsonl(architectures))

    # matrices
    buf = io.StringIO()
    cw = csv.writer(buf)
    cw.writerow(["object_id", "object_name", "create_action", "create_actor", "create_endpoint_or_tool",
                 "read_action", "read_actor", "read_endpoint_or_tool", "update_action", "update_actor",
                 "update_endpoint_or_tool", "delete_action", "delete_actor", "delete_endpoint_or_tool",
                 "soft_delete_supported", "archive_supported", "restore_supported", "audit_required",
                 "permission_required", "validation_required", "common_failure_modes", "tests_required"])
    for name in sorted(_SCHEMA_OBJECTS):
        cw.writerow([f"primitive.logical.{name}", name, f"op.{name}.create", "api_user", f"POST /{name}s",
                     f"op.{name}.read", "api_user", f"GET /{name}s/{{id}}", f"op.{name}.update", "api_user",
                     f"PATCH /{name}s/{{id}}", f"op.{name}.delete", "admin", f"DELETE /{name}s/{{id}}",
                     "yes", "yes", "yes", "yes", "yes", "yes", "schema_drift;orphaned_refs",
                     "schema_validation;crud_roundtrip"])
    _w(root / "crud_matrix.csv", buf.getvalue())

    buf = io.StringIO(); cw = csv.writer(buf)
    cw.writerow(["transformation_id", "transformation_name", "input_structure", "output_structure",
                 "example_input", "example_output", "batch", "streaming", "realtime", "deterministic", "lossy",
                 "reversible", "idempotent", "requires_llm", "can_be_llm_enhanced", "typical_tools",
                 "validation_checks", "failure_modes", "security_privacy_risks",
                 "bandwidth_cost_considerations", "monitoring_metrics"])
    for t in transforms:
        cw.writerow([t["id"], t["name"], ";".join(t["input_types"]), ";".join(t["output_types"]),
                     t["example"], "transformed output", "yes", "yes" if t["streaming_compatible"] else "no",
                     "yes" if t["real_time_compatible"] else "no", "yes" if t["deterministic"] else "no",
                     "yes" if t["is_lossy"] else "no", "yes" if t["is_reversible"] else "no",
                     "yes" if t["is_idempotent"] else "no", "no",
                     "yes" if t["llm_role"] != "none" else "no", ";".join(t["common_tools"]),
                     ";".join(t["quality_checks"]), ";".join(t["failure_modes"]),
                     ";".join(t["security_privacy_considerations"]) or "none",
                     ";".join(t["bandwidth_transfer_considerations"]), "count;error_rate;latency"])
    _w(root / "transformation_matrix.csv", buf.getvalue())

    buf = io.StringIO(); cw = csv.writer(buf)
    cw.writerow(["architecture_id", "architecture_name", "primary_use_case", "data_structures_used",
                 "schemas_used", "transformations_used", "storage_systems", "compute_systems",
                 "network_patterns", "serving_patterns", "operations_patterns", "security_patterns",
                 "governance_patterns", "tradeoffs", "failure_modes", "when_to_use", "when_not_to_use",
                 "source_refs"])
    for a in architectures:
        cw.writerow([a["id"], a["name"], a["when_to_use"][0], ";".join(a["data_structures"]),
                     ";".join(a["schemas"]), ";".join(a["transformations"]), ";".join(a["storage_patterns"]),
                     ";".join(a["compute_patterns"]), ";".join(a["network_patterns"]),
                     ";".join(a["serving_patterns"]), ";".join(a["observability"]),
                     ";".join(a["security_privacy_governance"][:2]), "audit_log",
                     a["tradeoffs"][0], ";".join(a["failure_modes"]), a["when_to_use"][0],
                     a["when_not_to_use"][0], ";".join(a["source_refs"])])
    _w(root / "architecture_matrix.csv", buf.getvalue())

    _w(root / "tool_registry.json", json.dumps({"tools": [{
        "tool_id": f"tool.{cat}.{name}", "name": name, "category": cat, "description": desc,
        "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
        "side_effects": [] if safe else ["mutates external state"], "requires_human_approval": approval,
        "safe_for_autonomous_use": safe, "rate_limits": [], "permissions_required": [cat],
        "failure_modes": ["timeout", "permission_denied"], "observability": ["tool_call_count", "tool_error_count"],
        "example_call": {"tool": name}, "example_result": {"ok": True}}
        for name, cat, desc, approval, safe in _TOOLS], **BOUNDARY}, indent=2, sort_keys=True))

    pb = ["# Agent Playbooks\n", "Deterministic stepwise playbooks; every playbook ends with the standard gates:",
          "validation gate -> human approval gate (when flagged) -> artifact + audit trace + rollback target.\n"]
    for name, goal, steps in _PLAYBOOKS:
        pb.append(f"## workflow.playbook.{name}\n")
        pb.append(f"- goal: {goal}")
        pb.append("- required inputs: task record + referenced object ids")
        pb.append("- required tools: see tool_registry.json (subset per step)")
        pb.append("- permissions: least-privilege per tool category")
        for i, s in enumerate(steps, 1):
            pb.append(f"- step {i} (deterministic unless marked): {s}")
        pb.append("- llm-enhanced steps: drafting/summarizing/classifying steps above; outputs schema-validated")
        pb.append("- validation gates: schema validation + tests where applicable")
        pb.append("- human approval gates: any tool with requires_human_approval=true")
        pb.append("- rollback plan: keep prior version; revert artifact; replay from checkpoint")
        pb.append("- artifacts: diff/report/PR + agent trace")
        pb.append("- telemetry: " + ", ".join(_LLM_OBSERVABILITY[:6]))
        pb.append("- failure modes: missing input, failed gate, tool error -> repair loop, then escalate\n")
    _w(root / "agent_playbooks.md", "\n".join(pb))

    # generated schemas + code
    openapi_components: dict[str, Any] = {}
    for name, spec in sorted(_SCHEMA_OBJECTS.items()):
        js = render_json_schema(name, spec)
        _w(root / "generated_schemas" / "json_schema" / f"{name}.json", json.dumps(js, indent=2, sort_keys=True))
        _w(root / "generated_schemas" / "json_schema" / f"{name}.example.json",
           json.dumps(_example_payload(spec), indent=2, sort_keys=True))
        if spec["relational"]:
            _w(root / "generated_schemas" / "sql" / f"{name}.sql", render_sql(name, spec))
        if spec["api"]:
            openapi_components.update(render_openapi_component(name, spec))
        if spec["event"]:
            _w(root / "generated_schemas" / "avro" / f"{name}.avsc",
               json.dumps(render_avro(name, spec), indent=2, sort_keys=True))
            _w(root / "generated_schemas" / "protobuf" / f"{name}.proto", render_protobuf(name, spec))
        _w(root / "generated_schemas" / "pydantic" / f"{name}.py",
           "from typing import Optional\nfrom pydantic import BaseModel\n\n\n" + render_pydantic(name, spec))
        _w(root / "generated_schemas" / "typescript" / f"{name}.ts", render_typescript(name, spec))
        _w(root / "generated_schemas" / "graphql" / f"{name}.graphql", render_graphql(name, spec))
    _w(root / "generated_schemas" / "openapi" / "components.json",
       json.dumps({"components": {"schemas": openapi_components}}, indent=2, sort_keys=True))

    models_py = ["\"\"\"Generated primitive models (candidate-only; stdlib fallback validators in validators.py).\"\"\"",
                 "from typing import Optional", "try:", "    from pydantic import BaseModel",
                 "except ImportError:  # pydantic optional; validators.py is stdlib-only",
                 "    class BaseModel:  # type: ignore[no-redef]",
                 "        def __init__(self, **kw):",
                 "            for k, v in kw.items(): setattr(self, k, v)", "", ""]
    for name in ("event_envelope", "document_chunk", "embedding_record", "agent_task", "agent_step",
                 "tool_call", "prompt_template", "eval_case", "metric_record", "audit_event"):
        models_py.append(render_pydantic(name, _SCHEMA_OBJECTS[name]))
    _w(root / "generated_code" / "primitives" / "models.py", "\n".join(models_py))
    _w(root / "generated_code" / "validators" / "validators.py", '''"""Stdlib JSON-Schema-subset validator for the generated schemas (type + required checks)."""
_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}


def validate_payload(payload: dict, schema: dict) -> list[str]:
    """Return a list of violations (empty = valid) for the generated json_schema subset."""
    errors = [f"missing required field: {f}" for f in schema.get("required", []) if f not in payload]
    for field, value in payload.items():
        prop = schema.get("properties", {}).get(field)
        if prop is None:
            if not schema.get("additionalProperties", True):
                errors.append(f"unexpected field: {field}")
            continue
        expected = _TYPES.get(prop.get("type"))
        if expected and value is not None and not isinstance(value, expected):
            errors.append(f"wrong type for {field}: expected {prop['type']}")
    return errors
''')
    _w(root / "generated_code" / "transforms" / "transforms.py", '''"""Deterministic starter transforms over generated primitives."""


def flatten_json(obj: dict, prefix: str = "") -> dict:
    """Flatten nested dicts into dot-path keys (arrays kept as values)."""
    out: dict = {}
    for key, value in obj.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(flatten_json(value, path))
        else:
            out[path] = value
    return out


def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    """Sliding-window character chunking with overlap (deterministic)."""
    if size <= overlap:
        raise ValueError("size must exceed overlap")
    return [text[i:i + size] for i in range(0, max(len(text), 1), size - overlap)]


def deduplicate_records(rows: list[dict], key: str) -> list[dict]:
    """Keep the first record per key value, preserving order."""
    seen: set = set()
    out = []
    for row in rows:
        k = row.get(key)
        if k not in seen:
            seen.add(k)
            out.append(row)
    return out
''')
    _w(root / "generated_code" / "examples" / "example_usage.py",
       "from validators.validators import validate_payload  # run from generated_code/ with PYTHONPATH=.\n")
    _w(root / "generated_code" / "README.md",
       "# Generated starter code\nprimitives/models.py (pydantic-optional) · validators/ (stdlib) · transforms/ · examples/.\n"
       "All candidate-only. Tests: ../tests/ plans + the generator self-test executes these modules.\n")

    # diagrams
    _w(root / "diagrams" / "system_context.mmd",
       "flowchart LR\n  user-->frontend-->backend-->database\n  backend-->object_storage\n  backend-->event_bus-->data_warehouse\n"
       "  backend-->vector_database\n  backend-->llm_provider\n  agent_runtime-->backend\n  backend-->observability\n  backend-->security_governance\n")
    _w(root / "diagrams" / "data_flow.mmd",
       "flowchart LR\n  raw_data-->validation-->transformation-->storage-->indexing-->serving-->monitoring-->feedback-->transformation\n")
    _w(root / "diagrams" / "agent_loop.mmd",
       "flowchart TD\n  task-->plan-->retrieve_context-->call_tool-->observe_result-->validate\n  validate--fail-->repair-->call_tool\n"
       "  validate--risky-->request_approval-->produce_artifact\n  validate--pass-->produce_artifact-->audit_trace\n")
    _w(root / "diagrams" / "architecture_options.mmd",
       "flowchart LR\n  requirements-->monolith\n  requirements-->modular_monolith\n  requirements-->microservices\n"
       "  requirements-->event_driven\n  requirements-->rag\n  requirements-->agentic\n  requirements-->data_platform\n  requirements-->observability_platform\n")

    # pattern documents (rendered views over the catalogs)
    dim_methods = [t for t in transforms if t["category"] == "reduce_dimension"] + \
                  [t for t in transforms if t["id"].endswith(("summarize", "cluster", "quantize", "compress", "sample"))]
    ds_lines = ["# Data structures — representations and reductions\n",
                "Representations per major structure: raw · normalized · denormalized · event · document · vector ·",
                "graph · time-series · fact/dimension · prompt-context · api · storage · monitoring. For each move,",
                "record what is preserved, what is lost, which indexes help, and which queries become easy/hard.\n",
                "## Dimensionality reduction and representation-change methods\n",
                "| method | lossy | deterministic | streaming |", "|---|---|---|---|"]
    ds_lines += [f"| {t['name']} | {'yes' if t['is_lossy'] else 'no'} | {'yes' if t['deterministic'] else 'no'} | "
                 f"{'yes' if t['streaming_compatible'] else 'no'} |" for t in dim_methods]
    ds_lines += ["\n## Structures\n"] + [f"- {p['id']}: {p['definition']}" for p in primitives
                                         if p["id"].startswith("primitive.logical.")]
    _w(root / "data_structures.md", "\n".join(ds_lines))
    _w(root / "document_structures.md", "# Document structures\n\n" + "\n".join(
        f"- {p['id']}: {p['definition']}" for p in primitives if p["category"] == "document"))
    _w(root / "schema_designs.md", "# Schema designs\n\nOne field-spec per object renders every format "
       "(sql/json_schema/pydantic/typescript/openapi/avro) — see generated_schemas/.\n\n" + "\n".join(
        f"- schema.json_schema.{n} ({len(s['fields'])} fields; relational={s['relational']}, api={s['api']}, "
        f"event={s['event']})" for n, s in sorted(_SCHEMA_OBJECTS.items())))
    _w(root / "systems_map.md", "# Systems map\n\n" + "\n".join(
        f"- {p['id']}" for p in primitives if p["layer"] == "physical"))
    _w(root / "workflow_patterns.md", "# Workflow patterns\n\n" + "\n".join(
        f"- workflow.playbook.{name}: {goal}" for name, goal, _ in _PLAYBOOKS))
    _w(root / "llm_agent_patterns.md", "# LLM agent patterns\n\n" + "\n".join(
        f"- {p['id']}" for p in primitives if p["category"] == "agent") +
       "\n\nLoop: task -> plan -> retrieve -> tool -> observe -> validate -> repair/approve -> artifact + trace.\n")
    _w(root / "serving_patterns.md", "# Serving patterns\n\nreal-time api · batch scoring · streaming inference · "
       "edge · database-side · ranking · rag · human-in-the-loop; rollout via shadow -> canary -> full with rollback.\n")
    _w(root / "storage_patterns.md", "# Storage patterns\n\nconfig=versioned files · operational=relational+pgvector · "
       "history=warehouse · raw/bronze -> cleaned/silver -> curated/gold; object storage for bodies, rows keep handles+digests.\n")
    _w(root / "compute_patterns.md", "# Compute patterns\n\nlocal cpu/gpu · vm · kubernetes · serverless · batch · "
       "spark/ray clusters · edge; choose by latency, scale, cost; autoscale with backpressure.\n")
    _w(root / "bandwidth_transfer_patterns.md", "# Bandwidth and transfer patterns\n\n" + "\n".join(
        f"- {c}: primitive involved, tools, failure modes, monitoring, optimization" for c in (
            "input_tokens", "output_tokens", "context_windows", "repo_context_transfer", "logs_to_llm",
            "documents_to_embeddings", "database_to_warehouse", "warehouse_to_training", "stream_to_feature_store",
            "api_to_tool_call", "cloud_egress", "region_replication", "batch_transfer", "streaming_transfer",
            "compression", "chunking", "pagination", "checkpointing", "retries", "idempotency", "deduplication",
            "backpressure", "throughput", "latency", "concurrency", "queue_depth", "cache_hit_rate", "cost_tracking")))
    sec = ["# Security, privacy, governance\n",
           "Per primitive: authn, authz, tenant isolation, PII/secret risk, prompt-injection risk, exfiltration",
           "risk, audit + retention + deletion + encryption requirements, human approval gates.\n",
           "## Agent action classification\n"]
    sec += [f"- {name}: {'requires approval' if approval else ('safe autonomous' if safe else 'safe with review')}"
            for name, _c, _d, approval, safe in _TOOLS]
    _w(root / "security_privacy_governance.md", "\n".join(sec))
    _w(root / "observability_operations.md", "# Observability and operations\n\nPer system: logs, metrics, traces, "
       "alerts, dashboards, runbooks, SLOs, rollback steps, cost metrics.\n\n## LLM/agent metrics\n" +
       "\n".join(f"- {m}" for m in _LLM_OBSERVABILITY))

    _w(root / "tests" / "schema_validation_plan.md", "# Schema validation plan\nValidate every example payload "
       "against its json_schema with validators.validate_payload; execute SQL DDL in sqlite; import pydantic models.\n")
    _w(root / "tests" / "transformation_test_plan.md", "# Transformation test plan\nProperty tests per flag: "
       "idempotent transforms applied twice equal once; reversible transforms round-trip; lossy transforms documented.\n")
    _w(root / "tests" / "agent_eval_plan.md", "# Agent eval plan\nPer playbook: golden run + failure injection per "
       "failure mode + gate coverage (validation/approval fire when they must).\n")

    n_prims = len(primitives)
    coverage = {"primitives": n_prims, "transformations": len(transforms), "schemas": len(schemas),
                "architectures": len(architectures), "tools": len(_TOOLS), "playbooks": len(_PLAYBOOKS),
                "research_queries": len(queries),
                "families": {f: len(items) for f, _l, _c, items in _FAMILIES}}
    _w(root / "coverage_report.md", "# Coverage report\n\n" + "\n".join(
        f"- {k}: {v}" for k, v in coverage.items() if not isinstance(v, dict)) +
       "\n\n## Family coverage\n" + "\n".join(f"- {f}: {n} items, all with records" for f, n in coverage["families"].items()) +
       f"\n\nSources: {len(_OWNER_SOURCES)} owner decompositions + {len(_CITED_SOURCES)} owner-cited "
       "references (iteration 2); records matching a cited reference carry provenance=owner_cited_reference, "
       "the rest remain inferred until the web verification pass runs (pending_tool_requests.jsonl). "
       "No exhaustiveness claim; gaps in gaps_and_unknowns.md.\n")
    _w(root / "gaps_and_unknowns.md", "# Gaps and unknowns\n\n"
       "- full web VERIFICATION pass pending (owner-cited references attached in iteration 2 but not "
       "independently fetched; live scraping opt-in via the governed scrape loop)\n"
       "- xml/parquet/arrow schema renders pending (protobuf + graphql closed in iteration 2)\n"
       "- cross-domain variants (PASS D) recorded as domains lists, not split records (documented decision)\n"
       "- property tests cover the starter transforms; catalog-wide per-flag property tests pending\n"
       "- records without cited references remain provenance=inferred\n")
    _w(root / "final_report.md", "\n".join([
        "# Final report\n",
        f"- domain: {domain}",
        f"- run: {run_id} @ {timestamp} (deterministic; re-run reproduces byte-identical artifacts)",
        f"- catalogs: {n_prims} primitives across {len(_FAMILIES)} families · {len(transforms)} transformations · "
        f"{len(schemas)} concrete schemas x 6 formats · {len(architectures)} architectures · {len(_TOOLS)} tools · "
        f"{len(_PLAYBOOKS)} playbooks",
        f"- sources: {len(_OWNER_SOURCES)} owner decompositions + {len(_CITED_SOURCES)} owner-cited references "
        "ledgered (iteration 2); 80-query web VERIFICATION pass pending (governed opt-in)",
        "- highest-value first implementations: event_envelope, document_chunk, embedding_record, tool_call, "
        "audit_event, prompt_template, eval_case, workflow_run, metric_record, agent_trace",
        "- highest-risk autonomous actions: execute_sql_mutation, deploy_service, rollback_deployment, "
        "run_shell_command, call_api, create_alert (all gated requires_human_approval)",
        "- next steps: run the governed source pass to convert inferred -> source-backed; attach property tests "
        "to transformation flags; feed catalog rows into the registry intake as candidates",
        "- all rows candidate=true, serves_truth=false\n"]))
    _w(root / "README.md", f"# Catalog run {run_id}\n\nGenerated by scripts/primitive_system_catalog_run.py "
       f"(deterministic; candidate-only). Regenerate:\n\n"
       f"    python3 scripts/primitive_system_catalog_run.py --run --run-id {run_id}\n\n"
       "Start with final_report.md, then the four catalogs + three matrices; concrete schemas under "
       "generated_schemas/; starter code under generated_code/.\n")

    return {"run_id": run_id, "root": str(root), **coverage, **BOUNDARY}


# ── validation (Section 18 checklist, computable parts) ──────────────────────────────────────────────────────
def validate_run(root: Path) -> dict[str, Any]:
    checks: list[tuple[str, bool]] = []
    ids: list[str] = []
    for fn in ("primitive_catalog.jsonl", "transformation_catalog.jsonl", "schema_catalog.jsonl",
               "architecture_catalog.jsonl", "research_queries.jsonl", "source_ledger.jsonl"):
        ok = True
        try:
            rows = [json.loads(line) for line in (root / fn).read_text().splitlines() if line]
            ids += [r["id"] for r in rows if "id" in r]
            if fn == "primitive_catalog.jsonl":
                required = {"id", "name", "category", "layer", "definition", "crud", "confidence",
                            "source_refs", "generation_pass"}
                ok = all(required <= set(r) for r in rows)
                items_expected = {f"primitive.{layer}.{n}" for _f, layer, _c, items in _FAMILIES for n in items}
                ok = ok and items_expected <= {r["id"] for r in rows}
            if fn == "transformation_catalog.jsonl":
                ok = all({"id", "category", "is_reversible", "is_lossy", "llm_role"} <= set(r) for r in rows)
        except Exception:
            ok = False
        checks.append((f"{fn} parses with required fields (+ full taxonomy coverage)", ok))
    checks.append(("all catalog IDs unique", len(ids) == len(set(ids))))
    sql_ok = True
    con = sqlite3.connect(":memory:")
    for sql_file in sorted((root / "generated_schemas" / "sql").glob("*.sql")):
        try:
            con.executescript(sql_file.read_text())
        except Exception:
            sql_ok = False
    con.close()
    checks.append(("every generated SQL DDL executes in sqlite", sql_ok))
    code_ok = True
    try:
        scope: dict[str, Any] = {}
        exec(compile((root / "generated_code" / "validators" / "validators.py").read_text(), "validators", "exec"), scope)
        exec(compile((root / "generated_code" / "transforms" / "transforms.py").read_text(), "transforms", "exec"), scope)
        schema = json.loads((root / "generated_schemas" / "json_schema" / "event_envelope.json").read_text())
        payload = json.loads((root / "generated_schemas" / "json_schema" / "event_envelope.example.json").read_text())
        code_ok = scope["validate_payload"](payload, schema) == [] \
            and scope["validate_payload"]({}, schema) != [] \
            and scope["flatten_json"]({"a": {"b": 1}}) == {"a.b": 1} \
            and len(scope["chunk_text"]("x" * 1000)) > 2 \
            and len(scope["deduplicate_records"]([{"k": 1}, {"k": 1}, {"k": 2}], "k")) == 2
        # PROPERTY TESTS (iteration 2): the transformation-catalog flags, executed on the starter transforms
        rows = [{"k": 2}, {"k": 1}, {"k": 2}, {"k": 3}]
        once = scope["deduplicate_records"](rows, "k")
        prop_ok = scope["deduplicate_records"](once, "k") == once  # idempotent: f(f(x)) == f(x)
        prop_ok = prop_ok and scope["flatten_json"]({"a": {"b": {"c": 1}}, "d": 2}) \
            == scope["flatten_json"]({"a": {"b": {"c": 1}}, "d": 2})  # deterministic
        text = "abcdefghij" * 60
        chunks = scope["chunk_text"](text, size=100, overlap=20)
        prop_ok = prop_ok and chunks == scope["chunk_text"](text, size=100, overlap=20) \
            and "".join(c[:80] for c in chunks[:-1]) + chunks[-1] == text  # lossless coverage with overlap
    except Exception:
        code_ok = prop_ok = False
    checks.append(("generated code executes: validator accepts examples, rejects empties; transforms behave", code_ok))
    checks.append(("property tests: idempotency/determinism/coverage of starter transforms hold", prop_ok))
    checks.append(("every required top-level artifact exists", all((root / f).exists() for f in (
        "README.md", "run_config.json", "ontology.json", "crud_matrix.csv", "transformation_matrix.csv",
        "architecture_matrix.csv", "tool_registry.json", "agent_playbooks.md", "coverage_report.md",
        "gaps_and_unknowns.md", "final_report.md", "pending_tool_requests.jsonl",
        "diagrams/system_context.mmd", "diagrams/agent_loop.mmd"))))
    return {"checks": checks, "passed": all(ok for _n, ok in checks), **BOUNDARY}


def _tree_digest(root: Path) -> str:
    h = hashlib.blake2b(digest_size=16)
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        rec = write_run(Path(td) / "a", run_id="run-selftest", timestamp=_FIXED_TIMESTAMP)
        root = Path(td) / "a" / "run-selftest"
        val = validate_run(root)
        for name, ok in val["checks"]:
            checks.append((f"validate: {name}", ok))
        checks.append(("run covers every Section-5 family with records",
                       rec["primitives"] >= 200 and len(rec["families"]) == len(_FAMILIES)))
        checks.append(("80+ research queries across the spec categories", rec["research_queries"] >= 80))
        checks.append(("30 concrete schema objects render into json_schema (+ sql/avro/pydantic/ts/openapi)",
                       rec["schemas"] == len(_SCHEMA_OBJECTS) == 30
                       and len(list((root / "generated_schemas" / "json_schema").glob("*.json"))) >= 60))
        checks.append(("iteration 2: protobuf renders for every event-facing object + graphql for all",
                       len(list((root / "generated_schemas" / "protobuf").glob("*.proto")))
                       == sum(1 for s in _SCHEMA_OBJECTS.values() if s["event"])
                       and len(list((root / "generated_schemas" / "graphql").glob("*.graphql"))) == len(_SCHEMA_OBJECTS)))
        ledger = [json.loads(x) for x in (root / "source_ledger.jsonl").read_text().splitlines() if x]
        prims = [json.loads(x) for x in (root / "primitive_catalog.jsonl").read_text().splitlines() if x]
        cited_prims = [p for p in prims if p["provenance"] == "owner_cited_reference"]
        checks.append(("iteration 2: cited-source ledger (>=20 refs) attached to matching records with "
                       "raised confidence", len(ledger) >= 20 and len(cited_prims) >= 15
                       and all(p["confidence"] > 0.6 for p in cited_prims)))
        write_run(Path(td) / "b", run_id="run-selftest", timestamp=_FIXED_TIMESTAMP)
        checks.append(("DETERMINISM: two runs are byte-identical",
                       _tree_digest(root) == _tree_digest(Path(td) / "b" / "run-selftest")))
        cat = root / "primitive_catalog.jsonl"
        good = cat.read_text()
        cat.write_text(good + "{not json\n")  # MUTATION GATE: corrupt -> validation must go red
        checks.append(("mutation gate: corrupted catalog fails validation", not validate_run(root)["passed"]))
        cat.write_text(good)
        checks.append(("restored catalog passes again", validate_run(root)["passed"]))
        checks.append(("boundary on receipts", rec.get("serves_truth") is False))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_system_catalog_run: deterministic catalog run generator — "
          f"{sum(len(i) for *_x, i in _FAMILIES)} taxonomy items, {len(_TRANSFORMS)} transforms, "
          f"{len(_SCHEMA_OBJECTS)} schema objects x 6 formats, {len(_ARCHITECTURES)} architectures, "
          f"{len(_TOOLS)} tools, {len(_PLAYBOOKS)} playbooks. Byte-deterministic, mutation-gated, "
          f"candidate-only. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--run-id", default=_DEFAULT_RUN_ID)
    ap.add_argument("--out", default=None, help="artifact root (default data/dev-intel/primitive_system_catalog/artifacts)")
    ap.add_argument("--domain", default=_DEFAULT_DOMAIN)
    ap.add_argument("--timestamp", default=_FIXED_TIMESTAMP)
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else resource("data") / "dev-intel" / "primitive_system_catalog" / "artifacts"
    if args.self_test:
        return _self_test()
    if args.run:
        rec = write_run(out, run_id=args.run_id, timestamp=args.timestamp, domain=args.domain)
        val = validate_run(out / args.run_id)
        rec["validation_passed"] = val["passed"]
        print(json.dumps(rec, indent=2, sort_keys=True))
        return 0 if val["passed"] else 1
    if args.validate:
        val = validate_run(out / args.run_id)
        for n, ok in val["checks"]:
            print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        return 0 if val["passed"] else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
