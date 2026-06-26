"""Single source of truth for shared constants across the AI Done Right portfolio scripts.

Per `docs/codex/no-magic-values.md`: any value used in more than one place gets
ONE definition here and is imported everywhere else — never re-typed as a
literal, and never embedded in a parallel string. Strings that include one of
these values must be built from the constant (e.g. `pgvector_type(dim)`), not
hand-copied.

Import convention matches the rest of the package (scripts are run as modules
from the repo root, e.g. `python -m scripts.db.<name>`):

    from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, pgvector_type
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

# --- Canonical repo paths ---------------------------------------------------
# Resolve from this file's location so callers never string-concatenate or rely
# on the current working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "catalog"
SCHEMAS_DIR = REPO_ROOT / "schemas"
VOCAB_DIR = REPO_ROOT / "vocabularies"
DIST_DIR = REPO_ROOT / "dist"
DOCS_DIR = REPO_ROOT / "docs"

# --- Catalog row-source registry -------------------------------------------
# Hosted/runtime consumers should prefer database-shaped catalog rows. YAML
# remains a seed/export fallback when the bridge rows have not been generated.
OH_CATALOG_ROW_DIR_ENV = "OH_CATALOG_ROW_DIR"
DEFAULT_CATALOG_ROW_DIR = DIST_DIR / "catalog-manifest-bridge"

# --- Canonical database/runtime paths --------------------------------------
DEFAULT_POSTGRES_COMPOSE_FILE = "infra/postgres/docker-compose.pgvector.yml"
DEFAULT_POSTGRES_SCHEMA_FILE = "db/postgres/schema.sql"
DEFAULT_POSTGRES_COUNT_SQL = "db/postgres/object_count_report.sql"
DEFAULT_POSTGRES_LOAD_SQL = "dist/sql/factory-load.sql"
DEFAULT_LOCAL_POSTGRES_DATABASE_URL = "postgresql://open_harness:open_harness_dev@localhost:5432/open_harness_hub"
MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER = "<managed-postgres-url-with-pgvector>"
DEFAULT_DATABASE_URL_ENV = "DATABASE_URL"

# --- Baltor admin-demo runtime settings ------------------------------------
# The admin demo remains a lightweight script, but its runtime knobs are
# settings, not magic literals. Keep env names/defaults here so they can be
# exported to `setting_profile` rows and eventually read from tenant/deployment
# overrides.
ADMIN_DEMO_RUNTIME_SETTINGS: dict[str, dict[str, Any]] = {
    "redis_url": {
        "env": "REDIS_URL",
        "default": "redis://127.0.0.1:6379/0",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Redis URL used for queue and event-stream visibility.",
    },
    "context_queue_key": {
        "env": "CONTEXT_QUEUE_KEY",
        "default": "ohh:context:jobs",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Redis list/stream key for pending context jobs.",
    },
    "admin_event_stream": {
        "env": "ADMIN_EVENT_STREAM",
        "default": "ohh:admin:events",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Redis stream key for admin-demo events.",
    },
    "context_worker_event_stream": {
        "env": "CONTEXT_WORKER_EVENT_STREAM",
        "default": "ohh:context:events",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Redis stream key for worker lifecycle and progress events.",
    },
    "worker_ledger_path": {
        "env": "CONTEXT_WORKER_LEDGER",
        "default": "dist/context-workers-ledger.jsonl",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Local JSONL ledger path for context-worker runs.",
    },
    "upload_dir": {
        "env": "ADMIN_DEMO_UPLOAD_DIR",
        "default": "dist/admin-demo-uploads",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Local upload directory for admin-demo source intake.",
    },
    "queue_health_history_path": {
        "env": "BALTOR_QUEUE_HEALTH_HISTORY",
        "default": "dist/baltor-queue-health-history.jsonl",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Local JSONL history path for queue health samples.",
    },
    "active_worker_stale_seconds": {
        "env": "BALTOR_ACTIVE_WORKER_STALE_SECONDS",
        "default": 300,
        "value_type": "duration_seconds",
        "setting_kind": "threshold",
        "description": "Seconds before an active worker is treated as stale.",
    },
    "pending_job_stale_seconds": {
        "env": "BALTOR_PENDING_JOB_STALE_SECONDS",
        "default": 600,
        "value_type": "duration_seconds",
        "setting_kind": "threshold",
        "description": "Seconds before a pending job is treated as stale.",
    },
    "queue_health_sample_limit": {
        "env": "BALTOR_QUEUE_HEALTH_SAMPLE_LIMIT",
        "default": 60,
        "value_type": "number",
        "setting_kind": "batching",
        "description": "Maximum queue health samples retained in memory.",
    },
    "queue_health_trend_window": {
        "env": "BALTOR_QUEUE_HEALTH_TREND_WINDOW",
        "default": 10,
        "value_type": "number",
        "setting_kind": "threshold",
        "description": "Number of samples used when classifying queue trend state.",
    },
    "queue_health_flat_delta": {
        "env": "BALTOR_QUEUE_HEALTH_FLAT_DELTA",
        "default": 1,
        "value_type": "number",
        "setting_kind": "threshold",
        "description": "Smallest pending-count movement treated as non-flat queue trend.",
    },
    "queue_health_min_sample_seconds": {
        "env": "BALTOR_QUEUE_HEALTH_MIN_SAMPLE_SECONDS",
        "default": 5,
        "value_type": "duration_seconds",
        "setting_kind": "threshold",
        "description": "Minimum seconds between persisted queue health samples.",
    },
    "queue_throughput_min_completions": {
        "env": "BALTOR_QUEUE_THROUGHPUT_MIN_COMPLETIONS",
        "default": 2,
        "value_type": "number",
        "setting_kind": "threshold",
        "description": "Minimum completed jobs needed before reporting throughput as active.",
    },
    "queue_pending_family_scan_limit": {
        "env": "BALTOR_QUEUE_PENDING_FAMILY_SCAN_LIMIT",
        "default": 1000,
        "value_type": "number",
        "setting_kind": "batching",
        "description": "Maximum pending queue jobs scanned for family/status summaries.",
    },
    "catalog_manifest_bridge_dir": {
        "env": "BALTOR_CATALOG_MANIFEST_BRIDGE_DIR",
        "default": "dist/catalog-manifest-bridge",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Database-shaped manifest bridge directory used by admin-demo exports.",
    },
    "database_url": {
        "env": DEFAULT_DATABASE_URL_ENV,
        "default": "",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Optional Postgres database URL for live readiness probes.",
    },
}

# --- Baltor context gateway/client/cache settings --------------------------
# Shared local gateway/client/cache scripts should use these defaults rather
# than each carrying its own URL, timeout, or cache path literals.
CONTEXT_GATEWAY_RUNTIME_SETTINGS: dict[str, dict[str, Any]] = {
    "gateway_base_url": {
        "env": "BALTOR_CONTEXT_GATEWAY_URL",
        "default": "http://127.0.0.1:9304",
        "value_type": "uri",
        "setting_kind": "custom",
        "description": "Base URL for the local Baltor context gateway HTTP API.",
    },
    "client_timeout_seconds": {
        "env": "BALTOR_CONTEXT_CLIENT_TIMEOUT_SECONDS",
        "default": 20,
        "value_type": "duration_seconds",
        "setting_kind": "threshold",
        "description": "HTTP timeout for the lightweight Baltor context client.",
    },
    "local_cache_dir": {
        "env": "BALTOR_CONTEXT_CACHE_DIR",
        "default": "dist/baltor-context-cache",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Local Markdown cache directory for compact context packs and glossary packets.",
    },
    "local_cache_audit_log": {
        "env": "BALTOR_CONTEXT_CACHE_AUDIT_LOG",
        "default": "cache-writes.jsonl",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Default audit-log filename under the local context cache directory.",
    },
    "local_cache_manifest": {
        "env": "BALTOR_CONTEXT_CACHE_MANIFEST",
        "default": "cache-manifest.json",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Default manifest filename under the local context cache directory.",
    },
}

# --- Context worker runtime settings ---------------------------------------
# Worker orchestration settings are intentionally separate from admin-demo UI
# settings because they are deployable worker runtime knobs. Keep defaults here
# and export them to setting_profile rows for hosted/tenant overrides.
CONTEXT_WORKER_RUNTIME_SETTINGS: dict[str, dict[str, Any]] = {
    "ledger_path": {
        "env": "CONTEXT_WORKER_LEDGER",
        "default": "dist/context-workers-ledger.jsonl",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Append-only JSONL ledger for context worker job records.",
    },
    "context_queue_key": {
        "env": "CONTEXT_QUEUE_KEY",
        "fallback_env": "FOUNDRY_QUEUE_KEY",
        "default": "ohh:context:jobs",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Primary queue key used by context worker runner jobs.",
    },
    "context_event_stream": {
        "env": "CONTEXT_WORKER_EVENT_STREAM",
        "default": "ohh:context:events",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Redis stream key for context worker lifecycle events.",
    },
    "redis_url": {
        "env": "REDIS_URL",
        "default": "",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Optional Redis URL for queue/event publication.",
    },
    "local_auto_approve": {
        "env": "CONTEXT_AUTO_APPROVE_LOCAL",
        "default": "true",
        "value_type": "boolean",
        "setting_kind": "policy",
        "description": "Whether local-only worker actions are auto-approved.",
    },
    "runtime_dir": {
        "env": "CONTEXT_WORKER_RUNTIME_DIR",
        "default": "dist/context-worker-runtime",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Directory for worker heartbeats, status files, and idempotency markers.",
    },
    "artifact_dir": {
        "env": "CONTEXT_WORKER_ARTIFACT_DIR",
        "default": "dist/context-worker-artifacts",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Directory for context worker output artifact manifests and payloads.",
    },
    "backend": {
        "env": "CONTEXT_WORKER_BACKEND",
        "default": "local",
        "value_type": "string",
        "setting_kind": "storage_backend",
        "description": "Worker runtime backend identifier, such as local, celery, or temporal.",
    },
    "image": {
        "env": "CONTEXT_WORKER_IMAGE",
        "default": "local-python",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Runtime image/name reported by worker lifecycle metadata.",
    },
    "json_logs": {
        "env": "CONTEXT_WORKER_JSON_LOGS",
        "default": "1",
        "value_type": "boolean",
        "setting_kind": "feature_flag",
        "description": "Enable structured JSON lifecycle logs on stderr.",
    },
    "celery_broker_url": {
        "env": "CELERY_BROKER_URL",
        "fallback_env": "REDIS_URL",
        "default": "redis://localhost:6379/0",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Celery broker URL for optional distributed context worker backend.",
    },
    "celery_result_backend": {
        "env": "CELERY_RESULT_BACKEND",
        "fallback_setting": "celery_broker_url",
        "default": "",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Celery result backend URL; defaults to the resolved broker URL.",
    },
    "celery_default_queue": {
        "env": "CONTEXT_QUEUE_KEY",
        "default": "ohh.context.default",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Default Celery queue name for optional distributed worker backend.",
    },
}

# --- Context tool-adapter runtime settings ---------------------------------
# Optional document/NLP/OSINT adapters are deployment/runtime features. Keep
# their env names and defaults here so local scripts and hosted deployments can
# share one setting_profile contract instead of repeating tool-specific strings.
CONTEXT_TOOL_ADAPTER_RUNTIME_SETTINGS: dict[str, dict[str, Any]] = {
    "enabled_adapters": {
        "env": "CONTEXT_ENABLED_ADAPTERS",
        "default": "local",
        "value_type": "string",
        "setting_kind": "feature_flag",
        "description": "Comma-separated optional adapter allowlist, or local/all.",
    },
    "osint_authorized": {
        "env": "OSINT_AUTHORIZED",
        "default": "",
        "value_type": "boolean",
        "setting_kind": "policy",
        "description": "Explicit authorized-use gate for OpenOSINT adapter execution.",
    },
    "grobid_url": {
        "env": "GROBID_URL",
        "default": "",
        "value_type": "uri",
        "setting_kind": "storage_backend",
        "description": "Optional GROBID service URL for scholarly document parsing.",
    },
    "spacy_model": {
        "env": "SPACY_MODEL",
        "default": "en_core_web_sm",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Default spaCy model used by spaCy/textacy adapters.",
    },
    "gliner_model": {
        "env": "GLINER_MODEL",
        "default": "urchade/gliner_medium-v2.1",
        "value_type": "string",
        "setting_kind": "custom",
        "description": "Default GLiNER model for custom entity extraction.",
    },
}

# Optional service-backed adapters. These are endpoint env names, not secrets.
# Secrets/tokens remain deployment-owned values; this registry only defines the
# service contract so code, docs, and setting_profile seeds do not drift.
CONTEXT_TOOL_ADAPTER_SERVICE_ENDPOINTS: dict[str, dict[str, Any]] = {
    "grobid": {
        "env": "GROBID_URL",
        "description": "GROBID service URL for scholarly document parsing.",
        "category": "document_parse",
    },
    "open_semantic_etl": {
        "env": "OPEN_SEMANTIC_ETL_URL",
        "description": "Open Semantic ETL service for crawl/text extraction/OCR/enrichment/index handoff.",
        "category": "semantic_etl",
    },
    "open_semantic_entity_api": {
        "env": "OPEN_SEMANTIC_ENTITY_API_URL",
        "description": "Open Semantic Entity Search API for entity extraction, linking, and reconciliation.",
        "category": "entity_linking",
    },
    "fscrawler": {
        "env": "FSCRAWLER_URL",
        "description": "FSCrawler-style Elasticsearch indexing endpoint.",
        "category": "search_index",
    },
    "solr_tika": {
        "env": "SOLR_TIKA_URL",
        "description": "Solr/Tika extraction and search indexing endpoint.",
        "category": "search_index",
    },
    "llamaindex_property_graph": {
        "env": "LLAMAINDEX_GRAPH_URL",
        "description": "LlamaIndex PropertyGraphIndex service endpoint.",
        "category": "graph_rag",
    },
    "haystack_pipeline": {
        "env": "HAYSTACK_PIPELINE_URL",
        "description": "Haystack preprocessing/retrieval pipeline endpoint.",
        "category": "rag_pipeline",
    },
    "neo4j_graphrag": {
        "env": "NEO4J_GRAPHRAG_URL",
        "description": "Neo4j GraphRAG builder/retriever endpoint.",
        "category": "graph_rag",
    },
    "microsoft_graphrag": {
        "env": "MICROSOFT_GRAPHRAG_URL",
        "description": "Microsoft GraphRAG indexing endpoint.",
        "category": "graph_rag",
    },
    "ragflow": {
        "env": "RAGFLOW_URL",
        "description": "RAGFlow ingestion endpoint.",
        "category": "rag_pipeline",
    },
    "lightrag": {
        "env": "LIGHTRAG_URL",
        "description": "LightRAG graph-structured indexing endpoint.",
        "category": "graph_rag",
    },
    "falkordb_graphrag": {
        "env": "FALKORDB_GRAPHRAG_URL",
        "description": "FalkorDB GraphRAG SDK service endpoint.",
        "category": "graph_rag",
    },
    "docling_graph": {
        "env": "DOCLING_GRAPH_URL",
        "description": "Docling-Graph document extraction endpoint.",
        "category": "document_graph",
    },
    "cognee": {
        "env": "COGNEE_URL",
        "description": "Cognee graph/vector agent memory endpoint.",
        "category": "agent_memory",
    },
    "graphiti": {
        "env": "GRAPHITI_URL",
        "description": "Graphiti/Zep temporal knowledge graph endpoint.",
        "category": "agent_memory",
    },
    "cocoindex": {
        "env": "COCOINDEX_URL",
        "description": "CocoIndex incremental extraction pipeline endpoint.",
        "category": "index_pipeline",
    },
    "openspg_kag": {
        "env": "OPENSPG_KAG_URL",
        "description": "OpenSPG/KAG ontology-constrained KG construction endpoint.",
        "category": "knowledge_graph",
    },
    "langchain_graph_transformer": {
        "env": "LANGCHAIN_GRAPH_TRANSFORMER_URL",
        "description": "LangChain LLMGraphTransformer extraction endpoint.",
        "category": "llm_extraction",
    },
    "langextract": {
        "env": "LANGEXTRACT_URL",
        "description": "Source-grounded structured extraction endpoint.",
        "category": "llm_extraction",
    },
    "ontogpt": {
        "env": "ONTOGPT_URL",
        "description": "OntoGPT/SPIRES ontology-grounded extraction endpoint.",
        "category": "ontology_extraction",
    },
    "structured_output": {
        "env": "STRUCTURED_OUTPUT_URL",
        "description": "Structured-output service endpoint.",
        "category": "llm_extraction",
    },
    "constrained_decode": {
        "env": "CONSTRAINED_DECODE_URL",
        "description": "Constrained decoding service endpoint.",
        "category": "llm_extraction",
    },
    "deepke": {
        "env": "DEEPKE_URL",
        "description": "DeepKE/OneKE information extraction endpoint.",
        "category": "information_extraction",
    },
    "relik": {
        "env": "RELIK_URL",
        "description": "ReLiK entity linking and relation extraction endpoint.",
        "category": "information_extraction",
    },
    "raptor": {
        "env": "RAPTOR_URL",
        "description": "RAPTOR recursive summarization endpoint.",
        "category": "summarization",
    },
    "dify": {
        "env": "DIFY_URL",
        "description": "Dify workflow/app platform endpoint.",
        "category": "app_workflow",
    },
    "flowise": {
        "env": "FLOWISE_URL",
        "description": "Flowise visual workflow endpoint.",
        "category": "app_workflow",
    },
    "langflow": {
        "env": "LANGFLOW_URL",
        "description": "Langflow visual workflow endpoint.",
        "category": "app_workflow",
    },
    "anythingllm": {
        "env": "ANYTHINGLLM_URL",
        "description": "AnythingLLM private document chat/RAG endpoint.",
        "category": "app_workflow",
    },
    "diffbot_nlp": {
        "env": "DIFFBOT_NLP_URL",
        "description": "Diffbot-style managed NLP/entity/relationship extraction endpoint.",
        "category": "managed_nlp",
    },
}

# --- Node research runtime settings ----------------------------------------
NODE_RESEARCH_RUNTIME_SETTINGS: dict[str, dict[str, Any]] = {
    "setting_profile_path": {
        "env": "NODE_RESEARCH_SETTING_PROFILE_PATH",
        "default": "db/seeds/settings-registry/setting_profile.jsonl",
        "value_type": "path",
        "setting_kind": "custom",
        "description": "Setting-profile JSONL path used to load node research tool and route registry rows.",
    },
    "authorized": {
        "env": "NODE_RESEARCH_AUTHORIZED",
        "default": "",
        "value_type": "boolean",
        "setting_kind": "policy",
        "description": "Explicit authorized-use gate for sensitive node enrichment.",
    },
    "active_recon_authorized": {
        "env": "ACTIVE_RECON_AUTHORIZED",
        "default": "",
        "value_type": "boolean",
        "setting_kind": "policy",
        "description": "Explicit authorized-use gate for active reconnaissance tools.",
    },
    "enable_external": {
        "env": "NODE_RESEARCH_ENABLE_EXTERNAL",
        "default": "",
        "value_type": "boolean",
        "setting_kind": "feature_flag",
        "description": "Allow configured non-local node research tools to be proposed or run.",
    },
}

# --- Model runtime / judging registry --------------------------------------
# Runtime model IDs are operational settings, not durable taxonomy. Keep their
# defaults here until deployment-owned setting_profile rows take over.
OLLAMA_HOST_ENV = "OLLAMA_HOST"
OLLAMA_MODEL_ENV = "OLLAMA_MODEL"
OH_OLLAMA_MAX_TOKENS_ENV = "OH_OLLAMA_MAX_TOKENS"
OH_OLLAMA_TIMEOUT_ENV = "OH_OLLAMA_TIMEOUT"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
OH_ANTHROPIC_MODEL_ENV = "OH_ANTHROPIC_MODEL"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OH_OPENAI_MODEL_ENV = "OH_OPENAI_MODEL"
OH_OPENAI_ENDPOINT_ENV = "OH_OPENAI_ENDPOINT"
OH_RERANK_MODEL_ENV = "OH_RERANK_MODEL"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_JUDGE_MODEL = "llama3.1:8b"
DEFAULT_ANTHROPIC_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_JUDGE_MODEL = "gpt-5"
DEFAULT_GEMMA_RERANK_MODEL = "gemma2:2b"
DEFAULT_OPENAI_CHAT_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_OLLAMA_MAX_TOKENS = 512
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 300

OLLAMA_JUDGE_PROFILE_ID = "ollama-local-judge"
ANTHROPIC_JUDGE_PROFILE_ID = "anthropic-claude-sonnet-judge"
OPENAI_JUDGE_PROFILE_ID = "openai-frontier-judge"
OLLAMA_GEMMA_RERANK_PROFILE_ID = "ollama-gemma-rerank"

MODEL_RUNTIME_PROFILES: dict[str, dict[str, Any]] = {
    OLLAMA_JUDGE_PROFILE_ID: {
        "provider": "ollama",
        "model": DEFAULT_OLLAMA_JUDGE_MODEL,
        "runtime": "local_http",
        "trust_boundary": "local",
        "host_env": OLLAMA_HOST_ENV,
        "model_env": OLLAMA_MODEL_ENV,
        "default_host": DEFAULT_OLLAMA_HOST,
        "default_max_tokens": DEFAULT_OLLAMA_MAX_TOKENS,
        "timeout_seconds": DEFAULT_OLLAMA_TIMEOUT_SECONDS,
        "use_case": "low-cost local rubric judging when Ollama is available",
    },
    ANTHROPIC_JUDGE_PROFILE_ID: {
        "provider": "anthropic",
        "model": DEFAULT_ANTHROPIC_JUDGE_MODEL,
        "runtime": "external_api",
        "trust_boundary": "external",
        "api_key_env": ANTHROPIC_API_KEY_ENV,
        "model_env": OH_ANTHROPIC_MODEL_ENV,
        "use_case": "hosted rubric judging for higher-capability review paths",
    },
    OPENAI_JUDGE_PROFILE_ID: {
        "provider": "openai",
        "model": DEFAULT_OPENAI_JUDGE_MODEL,
        "runtime": "external_api",
        "trust_boundary": "external",
        "api_key_env": OPENAI_API_KEY_ENV,
        "model_env": OH_OPENAI_MODEL_ENV,
        "endpoint_env": OH_OPENAI_ENDPOINT_ENV,
        "default_endpoint": DEFAULT_OPENAI_CHAT_COMPLETIONS_ENDPOINT,
        "use_case": "frontier or hosted fallback rubric judging",
    },
    OLLAMA_GEMMA_RERANK_PROFILE_ID: {
        "provider": "ollama",
        "model": DEFAULT_GEMMA_RERANK_MODEL,
        "runtime": "local_http",
        "trust_boundary": "local",
        "host_env": OLLAMA_HOST_ENV,
        "model_env": OH_RERANK_MODEL_ENV,
        "default_host": DEFAULT_OLLAMA_HOST,
        "timeout_seconds": 60,
        "use_case": "local catalog reranking and recommendation scoring",
    },
}

# Tool/source tags that look like model IDs to string audits but are not model
# routes. Keep them registered separately so migration reports stay semantic.
CLAUDE_CODE_TOOL_TAG = "claude-code"
CLAUDE_FLOW_TOOL_TAG = "claude-flow"
REGISTERED_TOOL_TAGS: dict[str, dict[str, str]] = {
    CLAUDE_CODE_TOOL_TAG: {
        "kind": "agent_tool_tag",
        "owner": "agent_workflow_system_reference_intake",
        "description": "Catalog tag for Claude Code as an agent/tool surface, not a provider model ID.",
    },
    CLAUDE_FLOW_TOOL_TAG: {
        "kind": "agent_tool_tag",
        "owner": "claude_flow_swarm_orchestrator",
        "description": "Catalog tag for the claude-flow orchestration framework, not a provider model ID.",
    },
}

# Catalog model vocabulary that is intentionally broader than executable model
# routes. These values can later become normalized `model_family` and
# `model_class` rows instead of raw YAML text.
DEEPSEEK_R1_MODEL_FAMILY_TAG = "deepseek-r1"
REGISTERED_MODEL_FAMILY_TAGS: dict[str, dict[str, str]] = {
    DEEPSEEK_R1_MODEL_FAMILY_TAG: {
        "kind": "model_family_tag",
        "owner": "deepseek_r1_distill",
        "description": "Family/tag value for DeepSeek-R1 derivatives and pipelines.",
    },
}

GPT_PRICING_CLASS = "gpt-class"
REGISTERED_MODEL_CLASS_VALUES: dict[str, dict[str, str]] = {
    GPT_PRICING_CLASS: {
        "kind": "pricing_class",
        "owner": "model_pricing_lookup",
        "description": "Example pricing class bucket used by catalog pricing lookup components.",
    },
}

OLLAMA_LLAMA3_EXAMPLE_MODEL = "llama3"
OPENAI_GPT4O_EXAMPLE_MODEL = "gpt-4o"
OPENAI_GPT4O_MINI_EXAMPLE_MODEL = "gpt-4o-mini"
# Default model id for the non-commercial ChatAnywhere demo route. It is an
# env-overridable DEFAULT in scripts/model_gateway.py (OH_LLM_CHATANYWHERE_MODEL)
# and is documented once in baltor-free-llm-demo-routing.md; registering it here
# is the single source of truth so the same id in the doc/gateway is not flagged
# as drift (docs/codex/no-magic-values.md).
CHATANYWHERE_DEMO_MODEL = "gpt-3.5-turbo"

REGISTERED_EXAMPLE_MODEL_VALUES: dict[str, dict[str, str]] = {
    OLLAMA_LLAMA3_EXAMPLE_MODEL: {
        "provider": "ollama",
        "owner": "model_route_gateway",
        "description": "Catalog example route model; deployment-owned routes may override it.",
    },
    OPENAI_GPT4O_EXAMPLE_MODEL: {
        "provider": "openai",
        "owner": "model_route_gateway",
        "description": "Catalog example route model; deployment-owned routes may override it.",
    },
    OPENAI_GPT4O_MINI_EXAMPLE_MODEL: {
        "provider": "openai",
        "owner": "response_cache_fragment_reuse",
        "description": "Catalog example route model; deployment-owned routes may override it.",
    },
    CHATANYWHERE_DEMO_MODEL: {
        "provider": "chatanywhere",
        "owner": "model_gateway",
        "description": "Default model for the non-commercial ChatAnywhere demo lane; env-overridable.",
    },
}

# --- Embedding / vector configuration ---------------------------------------
# The canonical pgvector dimension for the default local embedding model. This
# is THE definition; load plans, workers, smoke tests, and audits import it
# rather than re-typing 384. Changing the default model below should be the
# only edit needed to move the whole fleet to a new dimension.
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL = f"sentence-transformers/{DEFAULT_EMBEDDING_MODEL}"
HASH_BOW_EMBEDDING_MODEL = "hash-bow"
TFIDF_SVD_EMBEDDING_MODEL = "tfidf+svd"
HASH_BOW_FALLBACK_DIMENSIONS = 256
TFIDF_SVD_DIMENSIONS = 128

# Registry of known embedding models -> their output dimension. Add a row to
# swap or offer a model; do not scatter model-id string literals across scripts.
EMBEDDING_MODELS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,            # sentence-transformers, local default
    "bge-small-en-v1.5": 384,           # local alternative, same dimension
    "all-minilm": 384,                  # Ollama tag (served via /v1/embeddings)
    "nomic-embed-text": 768,            # Ollama tag, stronger 768-dim option
    "text-embedding-3-small": 1536,     # OpenAI-compatible hosted route
    "text-embedding-ada-002": 1536,     # legacy OpenAI-compatible route
    "mistral-embed": 1024,              # Mistral OpenAI-compatible embeddings route
}

# Per-provider-lane DEFAULT embedding tags — the single source for the live model_route lanes (each MUST be a
# key above so its dimension stays authoritative). Override per-run with OH_EMBED_MODEL.
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_OPENAI_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_MISTRAL_EMBED_MODEL = "mistral-embed"

DEFAULT_EMBEDDING_DIMENSIONS: int = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]
assert all(_m in EMBEDDING_MODELS for _m in (DEFAULT_OLLAMA_EMBED_MODEL, DEFAULT_OPENAI_EMBED_MODEL, DEFAULT_MISTRAL_EMBED_MODEL))

# --- Model profile registry -------------------------------------------------
# Model profile IDs are routing/config records, not provider model IDs. These
# profiles are suitable for database-backed settings rows later; keep code
# importing them here until the operational store owns them.
LOCAL_BGE_SMALL_PROFILE_ID = "local-bge-small-en"
LOCAL_E5_SMALL_PROFILE_ID = "local-e5-small"
OPENAI_COMPATIBLE_SMALL_PROFILE_ID = "openai-compatible-small"
HOSTED_SMALL_PLACEHOLDER_PROFILE_ID = "hosted-small-placeholder"
DEFAULT_EMBEDDING_PROFILE_ID = LOCAL_BGE_SMALL_PROFILE_ID

EMBEDDING_MODEL_PROFILES: dict[str, dict[str, Any]] = {
    LOCAL_BGE_SMALL_PROFILE_ID: {
        "provider": "local",
        "model": "bge-small-en",
        "runtime": "sentence-transformers",
        "trust_boundary": "local",
        "dimensions": EMBEDDING_MODELS["bge-small-en-v1.5"],
        "usd_per_million_tokens": 0.0,
        "notes": ["Local baseline. Hardware cost is not included in token price."],
    },
    LOCAL_E5_SMALL_PROFILE_ID: {
        "provider": "local",
        "model": "intfloat/e5-small-v2",
        "runtime": "sentence-transformers",
        "trust_boundary": "local",
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "usd_per_million_tokens": 0.0,
        "notes": ["Alternate local profile for cheap reruns and model-swap testing."],
    },
    OPENAI_COMPATIBLE_SMALL_PROFILE_ID: {
        "provider": "openai_compatible",
        "model": "small-embedding-model",
        "runtime": "external_api",
        "trust_boundary": "external",
        "dimensions": EMBEDDING_MODELS["text-embedding-3-small"],
        "usd_per_million_tokens": None,
        "notes": ["Placeholder profile. Replace with a live pricing snapshot before external execution."],
    },
    HOSTED_SMALL_PLACEHOLDER_PROFILE_ID: {
        "provider": "external_api",
        "model": "small-embedding-model",
        "runtime": "hosted_embedding_api",
        "trust_boundary": "external",
        "dimensions": EMBEDDING_MODELS["text-embedding-3-small"],
        "usd_per_million_tokens": None,
        "notes": ["Placeholder; replace with a run-scoped live pricing snapshot before external execution."],
    },
}


def embedding_model_profiles(*, include_hosted_placeholder: bool = False) -> dict[str, dict[str, Any]]:
    """Return a copy of embedding route profiles for planners and workers.

    Callers receive a deep copy so test overrides cannot mutate the canonical
    registry. The hosted placeholder is opt-in because daily synthetic/public
    batches should default to local-only planning.
    """
    profiles = deepcopy(EMBEDDING_MODEL_PROFILES)
    if not include_hosted_placeholder:
        profiles.pop(HOSTED_SMALL_PLACEHOLDER_PROFILE_ID, None)
    return profiles


# --- Storage backend registry ----------------------------------------------
PGVECTOR_BACKEND_FAMILY = "pgvector"
JSONL_PGVECTOR_READY_BACKEND = "jsonl_pgvector_ready"
POSTGRES_PGVECTOR_BACKEND = "postgres_pgvector"
LOCAL_DOCKER_PGVECTOR_BACKEND = "local_docker_pgvector"
LOCAL_POSTGRES_PGVECTOR_BACKEND = "local_postgres_pgvector"
POSTGRES_PGVECTOR_RENDER_WORKER_TARGET = f"{POSTGRES_PGVECTOR_BACKEND}_render_worker"
LOCAL_DOCKER_PGVECTOR_COMPONENT_TARGET = f"{LOCAL_DOCKER_PGVECTOR_BACKEND}_component_rows_and_vectors"
LOCAL_DOCKER_PGVECTOR_CANDIDATE_TARGET = f"{LOCAL_DOCKER_PGVECTOR_BACKEND}_candidate_rows_and_vectors"
POSTGRES_PGVECTOR_DEPLOYMENT_LABEL = f"deployment.{POSTGRES_PGVECTOR_BACKEND}"
DEFAULT_VECTOR_STORAGE_BACKEND = JSONL_PGVECTOR_READY_BACKEND
DEFAULT_VECTOR_SIMILARITY = "cosine"
CATALOG_VECTOR_INDEX_ID = "catalog"
KNOWLEDGE_VECTOR_INDEX_ID = "knowledge"
SOURCE_OBJECT_VECTOR_INDEX_ID = "source_object"
ENTITY_VECTOR_INDEX_ID = "entity"

VECTOR_STORAGE_BACKENDS: dict[str, dict[str, Any]] = {
    JSONL_PGVECTOR_READY_BACKEND: {
        "kind": "interchange",
        "trust_boundary": "local",
        "description": "JSONL rows shaped for later pgvector load and replay.",
    },
    POSTGRES_PGVECTOR_BACKEND: {
        "kind": "database",
        "trust_boundary": "hub",
        "description": "Canonical Postgres store with pgvector enabled.",
    },
    LOCAL_DOCKER_PGVECTOR_BACKEND: {
        "kind": "database",
        "trust_boundary": "local",
        "description": "Developer smoke-test Postgres/pgvector container.",
    },
    LOCAL_POSTGRES_PGVECTOR_BACKEND: {
        "kind": "database",
        "trust_boundary": "local",
        "description": "Local Postgres deployment target with pgvector enabled.",
    },
}

BACKEND_FAMILY_TERMS: dict[str, dict[str, str]] = {
    PGVECTOR_BACKEND_FAMILY: {
        "kind": "backend_family",
        "description": "Registered shorthand for the pgvector storage/index family.",
    },
}

# --- Vector index profile registry -----------------------------------------
# Database and search-engine schema files cannot import Python constants
# directly. Keep their canonical shape here, export it through
# scripts.db.vector_config_registry, then seed/check hosted setting_profile rows
# from the same values.
VECTOR_INDEX_PROFILES: dict[str, dict[str, Any]] = {
    CATALOG_VECTOR_INDEX_ID: {
        "subject_type": "component",
        "index_names": {
            "jsonl": "oh_catalog",
            "neo4j": "catalog_vec",
            "elasticsearch": "oh-component",
            "opensearch": "oh-component",
            "postgres": "object_embedding",
        },
        "backend": POSTGRES_PGVECTOR_BACKEND,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "similarity": DEFAULT_VECTOR_SIMILARITY,
    },
    KNOWLEDGE_VECTOR_INDEX_ID: {
        "subject_type": "knowledge_leaf",
        "index_names": {
            "jsonl": "oh_knowledge",
            "neo4j": "knowledge_vec",
            "elasticsearch": "oh-knowledge",
            "opensearch": "oh-knowledge",
            "postgres": "object_embedding",
        },
        "backend": POSTGRES_PGVECTOR_BACKEND,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "similarity": DEFAULT_VECTOR_SIMILARITY,
    },
    SOURCE_OBJECT_VECTOR_INDEX_ID: {
        "subject_type": "normalized_object",
        "index_names": {
            "jsonl": "oh_source_object",
            "postgres": "object_embedding",
        },
        "backend": POSTGRES_PGVECTOR_BACKEND,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "similarity": DEFAULT_VECTOR_SIMILARITY,
    },
    ENTITY_VECTOR_INDEX_ID: {
        "subject_type": "canonical_entity",
        "index_names": {
            "jsonl": "oh_entity",
            "postgres": "object_embedding",
        },
        "backend": POSTGRES_PGVECTOR_BACKEND,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "similarity": DEFAULT_VECTOR_SIMILARITY,
    },
}

# --- Load-plan terminology registry ----------------------------------------
# These are canonical interface names that intentionally contain backend words.
# They are not backend choices. Keep them registered so audits distinguish
# stable contracts/metrics/steps from true hard-coded storage decisions.
PGVECTOR_LOAD_PLAN_SUMMARY_FIELD = "pgvector_load_plan_summary"
PGVECTOR_LOAD_PLAN_SUMMARY_INPUT_PATH = f"$.inputs.{PGVECTOR_LOAD_PLAN_SUMMARY_FIELD}"
PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC = "pgvector_load_accepted_rows"
PGVECTOR_LOAD_REJECTED_ROWS_METRIC = "pgvector_load_rejected_rows"
PGVECTOR_LOAD_PLAN_SUMMARY_FLAG = "--pgvector-load-plan-summary"
PGVECTOR_LOAD_PLAN_RUN_ID = "pgvector-embedding-load-plan"
PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME = "pgvector-embedding-load-plan-summary.json"
PGVECTOR_LOAD_PLAN_ACCEPTED_ROWS_FILENAME = "accepted-object-embedding-load-rows.jsonl"
PGVECTOR_LOAD_PLAN_REJECTED_ROWS_FILENAME = "rejected-object-embedding-load-rows.jsonl"
PGVECTOR_LOAD_PLAN_SQL_FILENAME = "object-embedding-load.sql"
PGVECTOR_COMMITTED_COUNTS_FILENAME = "committed-counts.json"
EMBEDDING_COMMITTED_LOAD_AUDIT_FILENAME = "embedding-committed-load-audit.json"
PGVECTOR_LOAD_PLAN_DIST_DIR = "dist/pgvector-embedding-load-plan"
THEORY_PGVECTOR_LOAD_PLAN_DIST_DIR = "dist/theory-pgvector-embedding-load-plan"
MODEL_OPS_DAILY_RUNS_DIST_DIR = "dist/model-ops-daily-runs"
PGVECTOR_LOAD_PLAN_SUBDIR = "pgvector-load-plan"
PGVECTOR_LOAD_PLAN_EXAMPLE_DATE = "2026-05-31"
PGVECTOR_LOAD_PLAN_EXAMPLE_SUMMARY_PATH = str(
    Path(PGVECTOR_LOAD_PLAN_DIST_DIR) / PGVECTOR_LOAD_PLAN_EXAMPLE_DATE / PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME
)
PGVECTOR_TYPE_SETTING_KEY = "pgvector_type"
PGVECTOR_LOAD_SQL_INPUT_NAME = "pgvector_load_sql"
PGVECTOR_EMBEDDING_LOAD_CHECK_SCHEMA = "pgvector_embedding_load_check"

# Output filenames for scripts.db.object_embedding_batch_loader. Defined here
# (single source) rather than typed into the module, so the load tool and any
# audit that reads its output agree on the names (no-magic-values).
OBJECT_EMBEDDING_BATCH_LOADER_RUN_ID = "object-embedding-batch-loader"
OBJECT_EMBEDDING_BATCH_LOADER_SQL_FILENAME = "object-embedding-batch-load.sql"
OBJECT_EMBEDDING_BATCH_LOADER_REJECTED_FILENAME = "rejected-object-embedding-rows.jsonl"
OBJECT_EMBEDDING_BATCH_LOADER_AUDIT_FILENAME = "object-embedding-batch-load-audit.jsonl"

# Output filenames for scripts.db.cdc_event_emitter. The emitter delegates the
# event computation to scripts.db.component_cdc_plan (lossless reuse) and just
# adapts the version-pair input shape declared by the catalog manifest.
CDC_EVENT_EMITTER_RUN_ID = "cdc-event-emitter"
CDC_EVENT_EMITTER_PREVIOUS_VERSIONS_FILENAME = "previous-component-versions.jsonl"
CDC_EVENT_EMITTER_NEW_VERSIONS_FILENAME = "new-component-versions.jsonl"
CDC_EVENT_EMITTER_SUMMARY_FILENAME = "cdc-event-emitter-summary.json"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID = "local-pgvector-embedding-smoke"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_SELF_TEST_RUN_ID = f"{LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID}-self-test"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_PLAN_FILENAME = f"{LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID}-plan.json"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_CHECK_SCHEMA = "local_pgvector_embedding_smoke_check"
START_LOCAL_PGVECTOR_STEP = "start_local_pgvector"
WAIT_FOR_PGVECTOR_HEALTH_STEP = "wait_for_pgvector_health"

LOAD_PLAN_TERMS: dict[str, dict[str, str]] = {
    MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER: {
        "kind": "deployment_placeholder",
        "owner": "postgres_bootstrap_plan",
        "description": "Intentional placeholder for managed pgvector database URLs in side-effect-free plans.",
    },
    PGVECTOR_LOAD_PLAN_SUMMARY_FIELD: {
        "kind": "field",
        "owner": "embedding_load_plan",
        "description": "Input or report key pointing to a pgvector embedding load-plan summary.",
    },
    PGVECTOR_LOAD_PLAN_SUMMARY_INPUT_PATH: {
        "kind": "json_path",
        "owner": "embedding_load_plan",
        "description": "Canonical manifest input path for the pgvector load-plan summary.",
    },
    PGVECTOR_LOAD_PLAN_EXAMPLE_SUMMARY_PATH: {
        "kind": "example_artifact_path",
        "owner": "pgvector_embedding_load_plan",
        "description": "Published example fixture path for pgvector load-plan summary references in catalog manifests.",
    },
    PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC: {
        "kind": "metric",
        "owner": "embedding_committed_load_audit",
        "description": "Count of vector rows accepted by the pgvector load planner.",
    },
    PGVECTOR_LOAD_REJECTED_ROWS_METRIC: {
        "kind": "metric",
        "owner": "embedding_committed_load_audit",
        "description": "Count of vector rows rejected by the pgvector load planner.",
    },
    PGVECTOR_LOAD_PLAN_SUMMARY_FLAG: {
        "kind": "cli_flag",
        "owner": "embedding_load_plan",
        "description": "CLI flag for the pgvector load-plan summary input.",
    },
    START_LOCAL_PGVECTOR_STEP: {
        "kind": "step_id",
        "owner": "local_postgres_smoke",
        "description": "Dry-run/smoke-plan step that starts the local pgvector Postgres container.",
    },
    WAIT_FOR_PGVECTOR_HEALTH_STEP: {
        "kind": "step_id",
        "owner": "local_postgres_smoke",
        "description": "Dry-run/smoke-plan step that waits for local pgvector Postgres readiness.",
    },
    PGVECTOR_TYPE_SETTING_KEY: {
        "kind": "registry_field",
        "owner": "vector_config_registry",
        "description": "Field carrying the rendered pgvector column type for a vector index profile.",
    },
    PGVECTOR_LOAD_SQL_INPUT_NAME: {
        "kind": "pipeline_input",
        "owner": "pgvector_load_plan",
        "description": "Canonical pipeline input name carrying rendered pgvector load SQL.",
    },
    PGVECTOR_EMBEDDING_LOAD_CHECK_SCHEMA: {
        "kind": "schema_name",
        "owner": "pgvector_embedding_load_plan",
        "description": "Knowledge-pack schema identifier for pgvector embedding load checks.",
    },
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID: {
        "kind": "run_id",
        "owner": "local_pgvector_embedding_smoke",
        "description": "Canonical local pgvector smoke planner run id and output directory stem.",
    },
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_CHECK_SCHEMA: {
        "kind": "schema_name",
        "owner": "local_pgvector_embedding_smoke",
        "description": "Knowledge-pack schema identifier for local pgvector smoke checks.",
    },
}

# --- Component reference registry ------------------------------------------
# These component IDs are repeated in YAML seed/export manifests. Keep their
# canonical identities here so hosted deployments can seed/check component_ref
# rows instead of treating YAML text as the operational source of truth.
PGVECTOR_EMBEDDING_LOAD_PLANNER_TOOL_ID = "tool/pgvector-embedding-load-planner"
POSTGRES_PGVECTOR_BOOTSTRAP_PLANNER_TOOL_ID = "tool/postgres-pgvector-bootstrap-planner"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_PLANNER_TOOL_ID = "tool/local-pgvector-embedding-smoke-planner"
PGVECTOR_EMBEDDING_LOAD_PATTERNS_PACK_ID = "knowledge-pack/pgvector-embedding-load-patterns"
POSTGRES_PGVECTOR_BOOTSTRAP_PATTERNS_PACK_ID = "knowledge-pack/postgres-pgvector-bootstrap-patterns"
LOCAL_PGVECTOR_EMBEDDING_SMOKE_PATTERNS_PACK_ID = "knowledge-pack/local-pgvector-embedding-smoke-patterns"
# Versioned capability-adapter id for the pgvector retrieval provider. It recurs
# as a fallback_adapter across architecture/external_capability_catalog.json and
# repo_replacement_matrix.json; register its canonical identity here so those
# manifests are seedable component_ref rows, not drifting literals.
PGVECTOR_RETRIEVAL_ADAPTER_ID = "vector.pgvector@v1"

REGISTERED_COMPONENT_REF_IDS: dict[str, dict[str, str]] = {
    PGVECTOR_EMBEDDING_LOAD_PLANNER_TOOL_ID: {
        "component_type": "tool",
        "role": "step_ref",
        "owner": "pgvector_embedding_load_plan",
    },
    POSTGRES_PGVECTOR_BOOTSTRAP_PLANNER_TOOL_ID: {
        "component_type": "tool",
        "role": "step_ref",
        "owner": "postgres_pgvector_bootstrap",
    },
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_PLANNER_TOOL_ID: {
        "component_type": "tool",
        "role": "step_ref",
        "owner": "local_pgvector_embedding_smoke",
    },
    PGVECTOR_EMBEDDING_LOAD_PATTERNS_PACK_ID: {
        "component_type": "knowledge-pack",
        "role": "knowledge_pack",
        "owner": "pgvector_embedding_load_plan",
    },
    POSTGRES_PGVECTOR_BOOTSTRAP_PATTERNS_PACK_ID: {
        "component_type": "knowledge-pack",
        "role": "knowledge_pack",
        "owner": "postgres_pgvector_bootstrap",
    },
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_PATTERNS_PACK_ID: {
        "component_type": "knowledge-pack",
        "role": "knowledge_pack",
        "owner": "local_pgvector_embedding_smoke",
    },
    PGVECTOR_RETRIEVAL_ADAPTER_ID: {
        "component_type": "adapter",
        "role": "fallback_adapter",
        "owner": "external_capability_catalog",
    },
}

# --- Backend infrastructure identifier registry ----------------------------
# Concrete third-party backend identifiers (container image tags, project URLs,
# product names) that intentionally recur across deploy/architecture descriptors.
# They are NOT logical backend-choice keys (see VECTOR_STORAGE_BACKENDS) and NOT
# load-plan interface terms (see LOAD_PLAN_TERMS) — they name real external
# artifacts. Registered here so the hard-coded-setting audit recognizes them as
# intentional, single-sourced identities instead of drift (no-magic-values).
PGVECTOR_CONTAINER_IMAGE = "pgvector/pgvector:pg16"
PGVECTOR_PROJECT_URL = "https://github.com/pgvector/pgvector"
QDRANT_BACKEND_NAME = "Qdrant"

REGISTERED_BACKEND_INFRA_IDENTIFIERS: dict[str, dict[str, str]] = {
    PGVECTOR_CONTAINER_IMAGE: {
        "kind": "container_image",
        "family": PGVECTOR_BACKEND_FAMILY,
        "description": "Postgres+pgvector container image used by deploy topology and local smoke.",
    },
    PGVECTOR_PROJECT_URL: {
        "kind": "project_url",
        "family": PGVECTOR_BACKEND_FAMILY,
        "description": "Upstream pgvector project URL referenced by backend candidate registries.",
    },
    QDRANT_BACKEND_NAME: {
        "kind": "product_name",
        "family": "qdrant",
        "description": "Vector-search backend candidate (provider name) tracked in the Open*Hub backend registry.",
    },
}

# --- Object governance registry --------------------------------------------
# These families are the required baseline for database-backed business and
# platform objects. The validator, seed exporters, and admin readiness checks
# should import this list instead of carrying parallel literals.
OBJECT_GOVERNANCE_PACKAGE_TABLES = (
    "object_governance_profile",
    "object_contract",
    "object_schema_profile",
    "object_layout_profile",
    "object_architecture_diagram",
    "object_context_rule",
)

OBJECT_GOVERNANCE_OPERATIONAL_VIEWS = (
    "object_governance_profile_readiness",
    "object_governance_family_coverage",
    "object_governance_specialization_status",
)

CATALOG_OPERATIONAL_VIEWS = (
    "catalog_manifest_import_status",
    "component_database_readiness",
    "rubric_dimension_tree",
)

OBJECT_GOVERNANCE_RUBRIC_ID = "rubric/baltor-business-object-governance-quality"
OBJECT_GOVERNANCE_STANDARD_DOC_PATH = DOCS_DIR / "architecture/baltor-business-object-governance-standard.md"
OBJECT_GOVERNANCE_REVIEW_RUBRIC_PATH = CATALOG_DIR / "rubrics/baltor-business-object-governance-quality.yaml"
OBJECT_GOVERNANCE_SEED_LOAD_SQL = "db/seeds/object-governance/load-object-governance-seeds.sql"
OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID = "object-governance-local-postgres-smoke"
OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_SELF_TEST_RUN_ID = f"{OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID}-self-test"
OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_PLAN_FILENAME = f"{OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID}-plan.json"

OBJECT_GOVERNANCE_REQUIRED_FAMILIES = (
    "account_management",
    "billing",
    "context",
    "flow",
    "connection",
    "process",
    "database",
    "identity",
    "policy",
    "integration",
    "analytics",
)

OBJECT_GOVERNANCE_FAMILY_PROFILES: dict[str, dict[str, Any]] = {
    "account_management": {
        "object_type": "account_object_family",
        "display_name": "Account Management Objects",
        "description": "Users, workspaces, roles, entitlements, team membership, support overrides, and identity-linked account state.",
        "schema_styles": ["document", "long_attribute", "relational"],
        "cloud_compatibility": ["postgres", "document_store", "warehouse_projection"],
        "required_dimensions": ["identity_authority", "access_risk", "supportability", "auditability"],
        "required_relationships": ["member_of", "entitled_to", "managed_by", "impersonated_by_support"],
        "database_mapping": {
            "canonical_style": "document_with_promoted_indexes",
            "wide_projection": "account_governance_daily",
        },
    },
    "billing": {
        "object_type": "billing_object_family",
        "display_name": "Billing Objects",
        "description": "Usage events, invoices, price snapshots, credits, disputes, subscription state, and cost allocation records.",
        "schema_styles": ["relational", "event", "wide_columnar", "document"],
        "cloud_compatibility": ["postgres", "warehouse", "event_log", "object_storage"],
        "required_dimensions": ["revenue_impact", "cost_traceability", "invoice_finality", "dispute_risk"],
        "required_relationships": ["billed_to", "priced_by", "metered_by", "allocated_to"],
        "database_mapping": {
            "canonical_style": "event_and_relational",
            "wide_projection": "billing_usage_daily",
        },
    },
    "context": {
        "object_type": "context_object_family",
        "display_name": "Context Objects",
        "description": "Versioned source-linked context nodes, artifacts, packs, claims, relationships, dimensions, and memory records.",
        "schema_styles": ["document", "long_attribute", "graph", "vector_metadata", "wide_columnar"],
        "cloud_compatibility": ["postgres_jsonb", "object_storage", "vector_index", "graph_index"],
        "required_dimensions": ["verifiability", "authority", "freshness", "risk_if_wrong", "prompt_injection_risk"],
        "required_relationships": ["derived_from", "references", "supersedes", "contradicts", "governed_by"],
        "database_mapping": {
            "canonical_style": "context_object_plus_external_edges",
            "large_payload_storage": "object_store",
        },
    },
    "flow": {
        "object_type": "flow_object_family",
        "display_name": "Flow Objects",
        "description": "Runs, steps, approvals, retries, tool calls, context expansions, queue state, and agent workflow timelines.",
        "schema_styles": ["event", "relational", "wide_columnar"],
        "cloud_compatibility": ["postgres", "event_log", "warehouse"],
        "required_dimensions": ["latency", "cost", "failure_risk", "approval_required"],
        "required_relationships": ["input_to", "output_of", "retry_of", "approved_by"],
        "database_mapping": {
            "canonical_style": "append_only_event",
            "timeline_projection": "flow_timeline",
        },
    },
    "connection": {
        "object_type": "connection_object_family",
        "display_name": "Connection Objects",
        "description": "Source connectors, credential bindings, MCP endpoints, webhook subscriptions, sync scopes, and freshness policy.",
        "schema_styles": ["relational", "document", "event"],
        "cloud_compatibility": ["postgres", "secret_manager", "event_log"],
        "required_dimensions": ["credential_risk", "freshness", "write_capability", "source_authority"],
        "required_relationships": ["connects_to", "uses_credential", "syncs_scope", "exposes_tool"],
        "database_mapping": {
            "canonical_style": "relational_with_secret_refs",
            "secret_material_policy": "references_only",
        },
    },
    "process": {
        "object_type": "process_object_family",
        "display_name": "Process Objects",
        "description": "Pipelines, processors, transformers, rerankers, loaders, exporters, evals, and recurring operational jobs.",
        "schema_styles": ["event", "document", "wide_columnar"],
        "cloud_compatibility": ["postgres", "queue", "event_log", "warehouse"],
        "required_dimensions": ["quality", "cost", "reproducibility", "drift"],
        "required_relationships": ["uses_model", "uses_tool", "generates", "depends_on"],
        "database_mapping": {
            "canonical_style": "versioned_process_contract",
            "quality_projection": "process_quality_daily",
        },
    },
    "database": {
        "object_type": "database_object_family",
        "display_name": "Database Objects",
        "description": "Tables, views, indexes, seed rows, exported rows, migrations, projections, storage backends, and materialized caches.",
        "schema_styles": ["relational", "document", "wide_columnar", "graph", "vector_metadata", "object_storage"],
        "cloud_compatibility": ["postgres", "redis", "object_storage", "vector_index", "warehouse"],
        "required_dimensions": ["source_of_truth_status", "rebuildability", "retention_risk", "tenant_isolation"],
        "required_relationships": ["materializes", "derived_from", "loads_into", "supersedes"],
        "database_mapping": {
            "canonical_style": "database_catalog_record",
            "wide_projections_not_canonical": True,
        },
    },
    "identity": {
        "object_type": "identity_object_family",
        "display_name": "Identity Objects",
        "description": "Principals, service accounts, groups, roles, access grants, delegated actions, and authentication context.",
        "schema_styles": ["relational", "document", "graph"],
        "cloud_compatibility": ["postgres", "idp", "policy_engine", "secret_manager"],
        "required_dimensions": ["assurance_level", "privilege_risk", "delegation_risk", "review_freshness"],
        "required_relationships": ["member_of", "can_act_as", "granted_role", "owns"],
        "database_mapping": {
            "canonical_style": "relationship_authorization_record",
            "authorization_model": "relationship_and_attribute_based",
        },
    },
    "policy": {
        "object_type": "policy_object_family",
        "display_name": "Policy Objects",
        "description": "Access rules, model routing rules, retention rules, DLP rules, write boundaries, escalation rules, and exception records.",
        "schema_styles": ["document", "relational", "event"],
        "cloud_compatibility": ["postgres", "policy_engine", "audit_log"],
        "required_dimensions": ["enforcement_strength", "exception_risk", "auditability", "coverage"],
        "required_relationships": ["applies_to", "overrides", "requires_approval", "blocks"],
        "database_mapping": {
            "canonical_style": "versioned_policy_contract",
            "decision_events_required": True,
        },
    },
    "integration": {
        "object_type": "integration_object_family",
        "display_name": "Integration Objects",
        "description": "Third-party systems, adapters, provider contracts, API capabilities, event subscriptions, and transformation bindings.",
        "schema_styles": ["document", "relational", "event"],
        "cloud_compatibility": ["postgres", "queue", "object_storage", "secret_manager"],
        "required_dimensions": ["provider_reliability", "schema_stability", "sync_freshness", "operational_risk"],
        "required_relationships": ["adapts", "maps_to", "subscribes_to", "emits"],
        "database_mapping": {
            "canonical_style": "adapter_contract_record",
            "provider_changes_require_review": True,
        },
    },
    "analytics": {
        "object_type": "analytics_object_family",
        "display_name": "Analytics Objects",
        "description": "Metrics, dashboards, outcome measures, usage summaries, cost reports, eval results, and adoption telemetry.",
        "schema_styles": ["wide_columnar", "relational", "document"],
        "cloud_compatibility": ["warehouse", "postgres", "event_log", "dashboard"],
        "required_dimensions": ["metric_quality", "attribution_strength", "freshness", "decision_impact"],
        "required_relationships": ["computed_from", "displayed_in", "owned_by", "alerts_on"],
        "database_mapping": {
            "canonical_style": "metric_definition_plus_timeseries",
            "wide_projection": "analytics_metric_daily",
        },
    },
}

OBJECT_GOVERNANCE_CONCRETE_OBJECTS: tuple[dict[str, Any], ...] = (
    {
        "object_type": "tenant",
        "object_family": "account_management",
        "display_name": "Tenant",
        "description": "Top-level isolation and administration boundary for accounts, workspaces, context, billing, and policy.",
        "owner_team": "platform-identity",
        "specialization_level": "priority_account_policy_contract",
        "contract_kind": "policy",
        "contract_actions": ["create", "configure", "suspend", "deprovision", "export", "audit"],
        "contract_inputs_required": ["tenant_id", "tenant_slug", "admin_principal_id", "isolation_policy", "regional_policy", "audit_policy"],
        "contract_outputs_required": ["tenant_row", "tenant_policy_refs", "admin_audit_event", "isolation_boundary_record"],
        "contract_invariants": ["tenant id is globally unique", "regional and isolation policy exist before activation", "deprovisioning creates tombstone and audit records"],
        "contract_failure_modes": ["tenant activated without isolation policy", "admin role assigned outside tenant boundary", "deprovision skips dependent context or billing objects"],
        "schema_kind": "document",
        "schema_required_fields": ["tenant_id", "tenant_slug", "lifecycle_state", "isolation_policy", "regional_policy", "admin_refs", "audit_refs"],
        "schema_optional_fields": ["workspace_refs", "billing_account_refs", "policy_refs", "support_visibility", "facets"],
        "schema_promoted_indexes": ["tenant_id", "tenant_slug", "lifecycle_state", "regional_policy"],
        "layout_sections": ["overview", "isolation", "admins", "workspaces", "billing", "policies", "regionality", "audit"],
        "context_rule_must_load": ["tenant_id", "tenant_slug", "lifecycle_state", "isolation_policy", "regional_policy", "admin_refs", "audit_refs"],
        "context_rule_must_forbid": ["cross_tenant_context_without_policy", "tenant_admin_action_without_audit", "unscoped_support_visibility"],
        "required_relationships": ["tenant_contains_workspace", "tenant_owns_billing_account", "tenant_scopes_policy"],
        "required_dimensions": ["tenant_isolation_strength", "admin_action_sensitivity", "support_visibility"],
        "required_events": ["tenant.created", "tenant.updated", "tenant.suspended", "tenant.deprovisioned"],
        "database_mapping": {"operational_tables": ["tenant"], "analytics_projection": "account_governance_daily"},
    },
    {
        "object_type": "membership",
        "object_family": "account_management",
        "display_name": "Membership",
        "description": "Relationship between a principal, account or workspace, roles, entitlements, and lifecycle state.",
        "owner_team": "platform-identity",
        "specialization_level": "priority_identity_security_contract",
        "contract_kind": "security",
        "contract_actions": ["grant", "change_role", "revoke", "review", "export", "audit"],
        "contract_inputs_required": ["tenant_id", "membership_id", "principal_id", "scope_id", "role_refs", "grant_reason", "policy_context"],
        "contract_outputs_required": ["membership_row", "authorization_delta", "membership_audit_event"],
        "contract_invariants": ["membership scope is tenant-bound", "role grants are explicit", "revocation removes active entitlement path"],
        "contract_failure_modes": ["membership grants privilege without role ref", "revoked membership remains active in derived cache", "cross-tenant membership leak"],
        "schema_kind": "relational",
        "schema_required_fields": ["membership_id", "tenant_id", "principal_id", "scope_id", "role_refs", "lifecycle_state", "audit_refs"],
        "schema_optional_fields": ["entitlement_refs", "expires_at", "review_state", "grant_reason", "facets"],
        "schema_promoted_indexes": ["tenant_id", "principal_id", "scope_id", "lifecycle_state"],
        "layout_sections": ["overview", "principal", "scope", "roles", "entitlements", "review", "revocation", "audit"],
        "context_rule_must_load": ["membership_id", "tenant_id", "principal_id", "scope_id", "role_refs", "lifecycle_state", "audit_refs"],
        "context_rule_must_forbid": ["implicit_role_grant", "active_revoked_membership", "cross_tenant_scope"],
        "required_relationships": ["principal_has_membership", "membership_grants_role", "membership_scopes_entitlement"],
        "required_dimensions": ["privilege_risk", "identity_authority", "review_freshness"],
        "required_events": ["membership.created", "membership.changed", "membership.revoked"],
        "database_mapping": {"operational_tables": ["membership"], "analytics_projection": "identity_governance_daily"},
    },
    {
        "object_type": "billing_account",
        "object_family": "billing",
        "display_name": "Billing Account",
        "description": "Billing owner record that groups subscriptions, invoices, credits, payment references, and usage cost allocation.",
        "owner_team": "finance-platform",
        "specialization_level": "priority_billing_contract",
        "contract_kind": "billing",
        "contract_actions": ["create", "update_terms", "attach_subscription", "close", "export", "audit"],
        "contract_inputs_required": ["tenant_id", "billing_account_id", "account_owner_ref", "currency", "billing_policy", "tax_context"],
        "contract_outputs_required": ["billing_account_row", "billing_policy_refs", "finance_audit_event"],
        "contract_invariants": ["billing account belongs to one tenant", "payment details are tokenized references only", "currency and tax context are explicit before invoicing"],
        "contract_failure_modes": ["billing account linked across tenants", "plaintext payment data stored", "invoice generated without tax context"],
        "schema_kind": "relational",
        "schema_required_fields": ["billing_account_id", "tenant_id", "account_owner_ref", "currency", "billing_policy", "lifecycle_state", "audit_refs"],
        "schema_optional_fields": ["tax_context", "payment_method_refs", "subscription_refs", "contract_refs", "facets"],
        "schema_promoted_indexes": ["tenant_id", "billing_account_id", "lifecycle_state", "currency"],
        "layout_sections": ["overview", "owner", "subscriptions", "payment_references", "tax_context", "invoices", "policies", "audit"],
        "context_rule_must_load": ["billing_account_id", "tenant_id", "account_owner_ref", "currency", "billing_policy", "tax_context", "audit_refs"],
        "context_rule_must_forbid": ["plaintext_payment_details", "cross_tenant_billing_link", "invoice_without_tax_context"],
        "required_relationships": ["billing_account_owns_subscription", "billing_account_belongs_to_tenant"],
        "required_dimensions": ["revenue_exposure", "invoice_visibility", "cost_traceability"],
        "required_events": ["billing_account.created", "billing_account.updated", "billing_account.closed"],
        "database_mapping": {"operational_tables": ["billing_account"], "analytics_projection": "billing_usage_cost_daily"},
    },
    {
        "object_type": "subscription",
        "object_family": "billing",
        "display_name": "Subscription",
        "description": "Commercial entitlement record binding a billing account to plan, term, price snapshots, usage limits, and status.",
        "owner_team": "finance-platform",
        "specialization_level": "priority_billing_contract",
        "contract_kind": "billing",
        "contract_actions": ["create", "activate", "change_plan", "apply_price_snapshot", "cancel", "renew", "audit"],
        "contract_inputs_required": ["tenant_id", "subscription_id", "billing_account_id", "plan_id", "price_snapshot_id", "term", "policy_context"],
        "contract_outputs_required": ["subscription_row", "entitlement_delta", "billing_audit_event", "effective_price_snapshot"],
        "contract_invariants": ["price snapshot is immutable after activation", "plan changes create auditable entitlement deltas", "subscription state changes are effective-dated"],
        "contract_failure_modes": ["plan changed without price snapshot", "entitlement drift from subscription state", "renewal or cancellation not effective-dated"],
        "schema_kind": "relational",
        "schema_required_fields": ["subscription_id", "tenant_id", "billing_account_id", "plan_id", "price_snapshot_id", "status", "term_start", "term_end", "audit_refs"],
        "schema_optional_fields": ["contract_ref", "discount_refs", "usage_limits", "renewal_policy", "cancellation_reason", "facets"],
        "schema_promoted_indexes": ["tenant_id", "billing_account_id", "status", "term_end", "price_snapshot_id"],
        "layout_sections": ["overview", "plan", "price_snapshot", "entitlements", "term", "usage_limits", "policy", "audit"],
        "context_rule_must_load": ["subscription_id", "billing_account_id", "plan_id", "price_snapshot_id", "status", "term", "policy_context", "audit_refs"],
        "required_relationships": ["subscription_uses_plan", "subscription_uses_price_snapshot", "subscription_billed_to_account"],
        "required_dimensions": ["revenue_exposure", "contract_authority", "renewal_risk"],
        "required_events": ["subscription.created", "subscription.changed", "subscription.cancelled", "subscription.renewed"],
        "database_mapping": {"operational_tables": ["subscription"], "analytics_projection": "billing_usage_cost_daily"},
    },
    {
        "object_type": "invoice",
        "object_family": "billing",
        "display_name": "Invoice",
        "description": "Immutable billing statement that summarizes charges, credits, taxes, payment state, and source usage evidence.",
        "owner_team": "finance-platform",
        "specialization_level": "priority_billing_contract",
        "contract_kind": "billing",
        "contract_actions": ["generate", "finalize", "void", "apply_credit", "export", "audit"],
        "contract_inputs_required": ["tenant_id", "invoice_id", "billing_account_id", "line_items", "price_snapshot_refs", "usage_evidence_refs", "policy_context"],
        "contract_outputs_required": ["invoice_row", "invoice_audit_event", "immutable_statement_ref", "customer_visible_projection"],
        "contract_invariants": ["finalized invoices are immutable except void or credit records", "line items reference usage evidence or contract charges", "customer projection masks internal costs"],
        "contract_failure_modes": ["invoice generated from stale price snapshot", "line item lacks usage evidence", "internal cost data exposed in customer view"],
        "schema_kind": "relational",
        "schema_required_fields": ["invoice_id", "tenant_id", "billing_account_id", "status", "currency", "issued_at", "line_item_refs", "audit_refs"],
        "schema_optional_fields": ["tax_summary", "credit_refs", "payment_state", "customer_visible_uri", "usage_evidence_refs", "facets"],
        "schema_promoted_indexes": ["tenant_id", "billing_account_id", "status", "issued_at", "currency"],
        "layout_sections": ["overview", "line_items", "usage_evidence", "taxes", "credits", "payment_state", "customer_projection", "audit"],
        "context_rule_must_load": ["invoice_id", "billing_account_id", "status", "line_item_refs", "price_snapshot_refs", "usage_evidence_refs", "audit_refs"],
        "context_rule_must_forbid": ["unmasked_internal_costs", "plaintext_payment_details", "unversioned_price_terms"],
        "required_relationships": ["invoice_billed_to_account", "invoice_uses_price_snapshot", "invoice_summarizes_usage"],
        "required_dimensions": ["invoice_finality", "revenue_exposure", "usage_verifiability"],
        "required_events": ["invoice.generated", "invoice.finalized", "invoice.voided", "credit.applied"],
        "database_mapping": {"operational_tables": ["invoice"], "analytics_projection": "billing_usage_cost_daily"},
    },
    {
        "object_type": "context_object",
        "object_family": "context",
        "display_name": "Context Object",
        "description": "Versioned, permissioned, source-linked node with flexible facets, relationships, dimensions, artifacts, and lineage.",
        "owner_team": "context-platform",
        "specialization_level": "priority_context_contract",
        "contract_kind": "context",
        "contract_actions": ["observe", "version", "relate", "assess_dimension", "derive_artifact", "tombstone", "audit"],
        "contract_inputs_required": ["tenant_id", "context_object_id", "kind", "source_handle", "acl_ref", "version_state"],
        "contract_outputs_required": ["context_object_row", "context_version_ref", "lineage_event", "policy_boundary"],
        "contract_invariants": ["current state is a pointer to immutable versions", "relationships and dimensions are separate rows", "source handle and ACL travel with the object"],
        "contract_failure_modes": ["raw source copied without source handle", "relationship embedded as unversioned object field", "dimension score stored as fragile column"],
        "schema_kind": "document",
        "schema_required_fields": ["context_object_id", "tenant_id", "kind", "source_handle", "acl_ref", "current_version_id", "audit_refs"],
        "schema_optional_fields": ["facets", "five_w_one_h", "quality", "ownership", "source_metadata", "facets_custom"],
        "schema_promoted_indexes": ["tenant_id", "kind", "acl_ref", "current_version_id", "source_handle"],
        "layout_sections": ["overview", "versions", "relationships", "dimensions", "artifacts", "source", "policy", "lineage"],
        "context_rule_must_load": ["context_object_id", "tenant_id", "kind", "source_handle", "acl_ref", "current_version_id", "lineage_refs"],
        "context_rule_must_forbid": ["unversioned_raw_content", "embedded_unbounded_relationships", "dimension_score_without_assessment_row"],
        "required_relationships": ["version_of", "derived_from", "governed_by", "supersedes", "contradicts"],
        "required_dimensions": ["verifiability", "authority", "freshness", "sensitivity", "risk_if_wrong"],
        "required_events": ["context.observed", "context.updated", "relationship.changed", "dimension.assessed"],
        "database_mapping": {"operational_tables": ["context_object", "context_version"], "analytics_projection": "context_quality_daily"},
    },
    {
        "object_type": "context_pack",
        "object_family": "context",
        "display_name": "Context Pack",
        "description": "Task-specific compressed package of source-linked context, claims, risks, relationships, policy decisions, and lineage.",
        "owner_team": "context-platform",
        "specialization_level": "priority_context_contract",
        "contract_kind": "context",
        "contract_actions": ["build", "retrieve", "compress", "mask", "expand_source", "attach_feedback", "audit"],
        "contract_inputs_required": ["tenant_id", "pack_request_id", "task_type", "source_handles", "policy_context", "token_budget"],
        "contract_outputs_required": ["context_pack_row", "claim_source_map", "policy_decision_refs", "retrieval_event", "lineage_event"],
        "contract_invariants": ["every claim has a source handle or explicit unsupported marker", "ACL is checked before model delivery", "raw source expansion is logged"],
        "contract_failure_modes": ["pack contains stale fragile fact without warning", "compressed claim loses source handle", "policy mask skipped before model delivery"],
        "schema_kind": "document",
        "schema_required_fields": ["context_pack_id", "tenant_id", "pack_type", "task_type", "source_handles", "claims", "policy_decision_refs", "lineage_refs"],
        "schema_optional_fields": ["token_budget", "token_budget_used", "risks", "conflicts", "suggested_next_fetches", "feedback_summary", "facets"],
        "schema_promoted_indexes": ["tenant_id", "pack_type", "task_type", "created_at", "policy_status"],
        "layout_sections": ["summary", "claims", "source_handles", "risks", "conflicts", "policy", "lineage", "feedback"],
        "layout_actions": ["view_pack", "expand_source", "open_lineage", "submit_feedback", "export_pack"],
        "context_rule_must_load": ["context_pack_id", "pack_type", "task_type", "source_handles", "policy_decision_refs", "lineage_refs", "freshness_state"],
        "context_rule_must_forbid": ["unlinked_claims", "raw_restricted_source_without_expansion_log", "pack_delivery_without_acl_check"],
        "required_relationships": ["context_pack_summarizes_object", "context_pack_generated_by_process", "context_pack_used_by_agent"],
        "required_dimensions": ["token_efficiency", "source_recall", "freshness", "risk_if_wrong"],
        "required_events": ["pack.generated", "pack.expanded", "pack.used", "pack.feedback_recorded"],
        "database_mapping": {"operational_tables": ["context_pack", "retrieval_event"], "analytics_projection": "context_quality_daily"},
    },
    {
        "object_type": "source_connection",
        "object_family": "connection",
        "display_name": "Source Connection",
        "description": "Configured source integration with scopes, credential references, sync mode, freshness policy, and egress controls.",
        "owner_team": "integration-platform",
        "specialization_level": "priority_integration_contract",
        "contract_kind": "integration",
        "contract_actions": ["install", "authorize", "sync", "rotate_secret", "disable", "audit"],
        "contract_inputs_required": ["tenant_id", "source_connection_id", "source_system", "scope_set", "credential_ref", "sync_mode", "egress_policy"],
        "contract_outputs_required": ["source_connection_row", "sync_cursor", "freshness_state", "connection_audit_event"],
        "contract_invariants": ["secret material is never stored in row body", "scope changes are versioned", "source permissions are checked before indexing"],
        "contract_failure_modes": ["scope creep without approval", "stale cursor treated as fresh", "credential value leaked into export"],
        "schema_kind": "relational",
        "schema_required_fields": ["source_connection_id", "tenant_id", "source_system", "scope_set", "credential_ref", "sync_mode", "freshness_state", "audit_refs"],
        "schema_optional_fields": ["webhook_config", "mcp_tools", "rate_limit_policy", "last_cursor", "error_state", "facets"],
        "schema_promoted_indexes": ["tenant_id", "source_system", "freshness_state", "sync_mode"],
        "layout_sections": ["overview", "source", "scopes", "credential_reference", "sync_health", "freshness", "egress", "audit"],
        "context_rule_must_load": ["source_connection_id", "source_system", "scope_set", "credential_ref", "sync_mode", "freshness_state", "egress_policy"],
        "context_rule_must_forbid": ["plaintext_credentials", "unapproved_scope_expansion", "freshness_claim_without_cursor"],
        "required_relationships": ["source_connection_connects_source", "source_connection_uses_secret_ref", "source_connection_feeds_sync_job"],
        "required_dimensions": ["credential_risk", "freshness", "write_capability", "source_authority"],
        "required_events": ["source_connection.created", "source_connection.synced", "source_connection.disabled"],
        "database_mapping": {"operational_tables": ["source_connection"], "analytics_projection": "integration_health_daily"},
    },
    {
        "object_type": "sync_job",
        "object_family": "flow",
        "display_name": "Sync Job",
        "description": "Append-only operational job that reads a source connection, emits observed changes, and updates freshness state.",
        "owner_team": "integration-platform",
        "specialization_level": "priority_flow_event_contract",
        "contract_kind": "event",
        "contract_actions": ["queue", "start", "checkpoint", "complete", "fail", "retry", "audit"],
        "contract_inputs_required": ["tenant_id", "sync_job_id", "source_connection_id", "sync_mode", "cursor_before", "policy_context"],
        "contract_outputs_required": ["sync_job_event", "cursor_after", "observed_change_refs", "freshness_state", "lineage_event"],
        "contract_invariants": ["sync jobs are append-only event timelines", "cursor changes are checkpointed", "failed jobs preserve error state and retry policy"],
        "contract_failure_modes": ["cursor advanced without observed changes", "failed job overwrites prior checkpoint", "freshness state updated without source validation"],
        "schema_kind": "event",
        "schema_required_fields": ["sync_job_id", "tenant_id", "source_connection_id", "event_type", "cursor_before", "cursor_after", "freshness_state", "audit_refs"],
        "schema_optional_fields": ["observed_change_refs", "error_state", "retry_policy", "worker_id", "facets"],
        "schema_promoted_indexes": ["tenant_id", "source_connection_id", "event_type", "freshness_state"],
        "layout_sections": ["overview", "source_connection", "timeline", "cursor", "observed_changes", "errors", "freshness", "audit"],
        "context_rule_must_load": ["sync_job_id", "source_connection_id", "sync_mode", "cursor_before", "cursor_after", "freshness_state", "lineage_refs"],
        "context_rule_must_forbid": ["freshness_update_without_source_validation", "cursor_advance_without_checkpoint", "overwritten_failure_event"],
        "required_relationships": ["sync_job_uses_source_connection", "sync_job_outputs_context_version", "sync_job_records_lineage"],
        "required_dimensions": ["latency", "failure_risk", "freshness", "cost"],
        "required_events": ["sync_job.queued", "sync_job.started", "sync_job.completed", "sync_job.failed"],
        "database_mapping": {"operational_tables": ["sync_job", "lineage_event"], "analytics_projection": "integration_health_daily"},
    },
    {
        "object_type": "pack_builder_process",
        "object_family": "process",
        "display_name": "Pack Builder Process",
        "description": "Versioned process contract for retrieving, reranking, compressing, masking, and emitting context packs.",
        "owner_team": "context-platform",
        "specialization_level": "priority_process_custom_contract",
        "contract_kind": "custom",
        "contract_actions": ["plan", "retrieve", "rerank", "compress", "mask", "emit_pack", "evaluate", "audit"],
        "contract_inputs_required": ["tenant_id", "process_version", "pack_request_id", "retrieval_policy", "model_route", "policy_context"],
        "contract_outputs_required": ["context_pack_ref", "retrieval_event", "compression_event", "policy_decision_refs", "evaluation_refs"],
        "contract_invariants": ["process version and prompt/model route are recorded", "policy mask runs before pack delivery", "evaluation and feedback can trace to process version"],
        "contract_failure_modes": ["pack emitted without process version", "model route changed without lineage", "reranker output not auditable"],
        "schema_kind": "event",
        "schema_required_fields": ["process_run_id", "tenant_id", "process_version", "pack_request_id", "retrieval_policy", "model_route", "lineage_refs"],
        "schema_optional_fields": ["rerank_policy", "compression_policy", "evaluation_refs", "cost_summary", "facets"],
        "schema_promoted_indexes": ["tenant_id", "process_version", "model_route", "pack_request_id"],
        "layout_sections": ["overview", "retrieval", "reranking", "compression", "masking", "model_route", "cost", "evaluation", "lineage"],
        "context_rule_must_load": ["process_run_id", "process_version", "retrieval_policy", "model_route", "policy_context", "lineage_refs"],
        "context_rule_must_forbid": ["pack_emit_without_policy_mask", "unrecorded_model_route", "reranker_result_without_lineage"],
        "required_relationships": ["pack_builder_uses_retriever", "pack_builder_uses_policy", "pack_builder_outputs_context_pack"],
        "required_dimensions": ["quality", "cost", "reproducibility", "drift"],
        "required_events": ["pack_builder.started", "pack_builder.completed", "pack_builder.evaluated"],
        "database_mapping": {"operational_tables": ["lineage_event", "retrieval_event", "context_pack"], "analytics_projection": "process_quality_daily"},
    },
    {
        "object_type": "principal",
        "object_family": "identity",
        "display_name": "Principal",
        "description": "Human, service, agent, or workload identity that can authenticate, receive grants, and perform audited actions.",
        "owner_team": "platform-identity",
        "specialization_level": "priority_identity_security_contract",
        "contract_kind": "security",
        "contract_actions": ["provision", "authenticate", "grant", "delegate", "revoke", "audit"],
        "contract_inputs_required": ["tenant_id", "principal_id", "principal_kind", "identity_authority", "assurance_level", "policy_context"],
        "contract_outputs_required": ["principal_row", "identity_audit_event", "authorization_subject_ref", "revocation_state"],
        "contract_invariants": ["principal authority is explicit", "credential material is referenced not stored", "delegation and revocation are auditable"],
        "contract_failure_modes": ["principal granted role without authority", "credential secret stored in row", "revocation not propagated to sessions"],
        "schema_kind": "document",
        "schema_required_fields": ["principal_id", "tenant_id", "principal_kind", "identity_authority", "assurance_level", "lifecycle_state", "audit_refs"],
        "schema_optional_fields": ["provider_subject", "credential_refs", "session_refs", "delegation_refs", "consent_refs", "facets"],
        "schema_promoted_indexes": ["tenant_id", "principal_id", "principal_kind", "identity_authority", "lifecycle_state"],
        "layout_sections": ["overview", "authority", "credentials", "sessions", "roles", "delegations", "revocation", "audit"],
        "context_rule_must_load": ["principal_id", "tenant_id", "principal_kind", "identity_authority", "assurance_level", "lifecycle_state", "audit_refs"],
        "context_rule_must_forbid": ["plaintext_credentials", "implicit_delegation", "grant_without_identity_authority"],
        "required_relationships": ["principal_has_membership", "principal_has_role", "principal_uses_credential"],
        "required_dimensions": ["authentication_assurance", "privilege_risk", "delegation_scope"],
        "required_events": ["identity.provisioned", "principal.updated", "session.revoked"],
        "database_mapping": {"operational_tables": ["principal", "grant"], "analytics_projection": "identity_governance_daily"},
    },
    {
        "object_type": "vector_index",
        "object_family": "database",
        "display_name": "Vector Index",
        "description": "Derived retrieval index with declared embedding model, dimensions, source rows, rebuild strategy, and privacy boundary.",
        "owner_team": "data-platform",
        "specialization_level": "priority_database_contract",
        "contract_kind": "database",
        "contract_actions": ["create", "rebuild", "query", "deprecate", "purge", "audit"],
        "contract_inputs_required": ["tenant_id", "vector_index_id", "embedding_profile_id", "source_artifact_refs", "dimensions", "privacy_boundary", "rebuild_strategy"],
        "contract_outputs_required": ["vector_index_row", "index_build_event", "source_coverage_report", "query_readiness_state"],
        "contract_invariants": ["embedding dimensions match registered profile", "embeddings are treated as sensitive derived data", "index is rebuildable from source artifact refs"],
        "contract_failure_modes": ["dimension mismatch with embedding profile", "private memory embeddings uploaded without approval", "index lacks rebuild source refs"],
        "schema_kind": "vector_metadata",
        "schema_required_fields": ["vector_index_id", "tenant_id", "embedding_profile_id", "dimensions", "source_artifact_refs", "privacy_boundary", "rebuild_strategy"],
        "schema_optional_fields": ["backend", "metric", "shard_count", "last_build_event", "query_policy", "facets"],
        "schema_promoted_indexes": ["tenant_id", "embedding_profile_id", "dimensions", "privacy_boundary", "backend"],
        "layout_sections": ["overview", "embedding_profile", "source_artifacts", "privacy", "rebuild_strategy", "query_policy", "lineage", "audit"],
        "context_rule_must_load": ["vector_index_id", "embedding_profile_id", "dimensions", "source_artifact_refs", "privacy_boundary", "rebuild_strategy"],
        "context_rule_must_forbid": ["dimension_mismatch", "unapproved_private_embedding_upload", "index_without_rebuild_sources"],
        "required_relationships": ["vector_index_derives_from_artifact", "vector_index_uses_embedding_model", "vector_index_feeds_retrieval"],
        "required_dimensions": ["rebuildability", "query_cost", "embedding_privacy_risk", "source_recall"],
        "required_events": ["index.created", "index.rebuilt", "index.deprecated"],
        "database_mapping": {"operational_tables": ["setting_profile", "setting_value"], "analytics_projection": "database_governance_daily"},
    },
)


def dated_artifact_path(base_dir: str, date_token: str, filename: str) -> str:
    """Build a dated artifact path from registered directory and filename pieces."""
    return str(Path(base_dir) / date_token / filename)


def dated_nested_artifact_path(base_dir: str, date_token: str, subdir: str, filename: str) -> str:
    """Build a dated artifact path with one registered nested output directory."""
    return str(Path(base_dir) / date_token / subdir / filename)


def pgvector_type(dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> str:
    """Render the pgvector column type for a dimension, e.g. ``vector(384)``.

    Always build pgvector type strings through this helper so a dimension
    change can never leave a stale ``vector(384)`` literal behind in a message,
    comment, or SQL fragment.
    """
    return f"vector({int(dimensions)})"
