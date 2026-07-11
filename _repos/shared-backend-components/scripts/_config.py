"""Single source of truth for shared constants across the AI Done Right portfolio scripts.

Per `_repos/shared-backend-components/docs/codex/no-magic-values.md`: any value used in more than one place gets
ONE definition here and is imported everywhere else — never re-typed as a
literal, and never embedded in a parallel string. Strings that include one of
these values must be built from the constant (e.g. `pgvector_type(dim)`), not
hand-copied.

Import convention matches the rest of the package (scripts are run as modules
from the repo root, e.g. `python -m scripts.db.<name>`):

    from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, pgvector_type
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

from copy import deepcopy
from pathlib import Path
from typing import Any

# --- Canonical repo paths ---------------------------------------------------
# Resolve from this file's location so callers never string-concatenate or rely
# on the current working directory.
REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
CATALOG_DIR = _resource("catalog")
SCHEMAS_DIR = _resource("schemas")
VOCAB_DIR = _resource("vocabularies")
DIST_DIR = _resource("dist")
DOCS_DIR = _resource("docs")

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
DEFAULT_LOCAL_POSTGRES_DATABASE_URL = "postgresql://openhubforai:openhubforai_dev@localhost:5432/openhubforai"
MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER = "<managed-postgres-url-with-pgvector>"
DEFAULT_DATABASE_URL_ENV = "DATABASE_URL"
# Operational Postgres DSN env vars, checked IN ORDER (single source for the RecordStore + durable
# fleet-ledger cloud backends — never re-type these names). OH_PG_DSN is the deployment/staging-specific
# override; DATABASE_URL is the platform default. When neither is set, the libpq PG* environment
# (PGHOST/PGDATABASE/PGUSER/...) is honored by the driver via an empty DSN.
OH_PG_DSN_ENV = "OH_PG_DSN"
POSTGRES_DSN_ENV_VARS: tuple[str, ...] = (OH_PG_DSN_ENV, DEFAULT_DATABASE_URL_ENV)
LIBPQ_PG_ENV_PREFIX = "PG"  # libpq connection-parameter env prefix (PGHOST/PGPORT/PGUSER/PGDATABASE/...)

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
DEFAULT_OPENAI_JUDGE_MODEL = "gpt-5.6-sol"
DEFAULT_GEMMA_RERANK_MODEL = "gemma2:2b"
DEFAULT_OPENAI_CHAT_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_OLLAMA_MAX_TOKENS = 512
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 300

# --- AIDevObserver intelligence/model-control defaults ---------------------
# The browser control deck and local observer service use these constants so
# model IDs, provider labels, feature toggles, and env names do not drift.
AIDEVOBSERVER_MODEL_PROVIDER_ENV = "OH_OBSERVER_MODEL_PROVIDER"
AIDEVOBSERVER_KIMI_MODEL_ENV = "OH_OBSERVER_KIMI_MODEL"
AIDEVOBSERVER_GLM_MODEL_ENV = "OH_OBSERVER_GLM_MODEL"
AIDEVOBSERVER_OLLAMA_API_KEY_ENV = "OLLAMA_API_KEY"
AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL = "https://ollama.com/v1"
AIDEVOBSERVER_DEFAULT_MODEL_PROVIDER = "kimi"
AIDEVOBSERVER_KIMI_MODEL_ID = "kimi-k2.7-code"
AIDEVOBSERVER_GLM_MODEL_ID = "glm-5.2"
AIDEVOBSERVER_MODEL_PROVIDERS: tuple[str, ...] = ("kimi", "glm")

# --- NVIDIA Build inference lane (OpenAI-compatible; owner-provided key) ----
# integrate.api.nvidia.com serves hosted open-weight models (incl. GLM 5.2) behind an OpenAI-compatible
# /v1 surface, so it rides the same _openai_compatible path as Ollama Cloud / Mistral / OpenRouter. Single
# source for the env name + endpoint + default model (no parallel literals); key = NVIDIA_API_KEY
# (secret://provider/nvidia). See _repos/shared-backend-components/architecture/model_provider_graph.json node model.nvidia_build.glm@candidate.
NVIDIA_BUILD_API_KEY_ENV = "NVIDIA_API_KEY"
NVIDIA_BUILD_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_BUILD_DEFAULT_MODEL = "z-ai/glm-5.2"
# Tencent Hy3 via OpenRouter — 295B MoE / 21B active, native 256K context, 3 configurable reasoning modes,
# agentic-optimized. FREE on OpenRouter for a limited window (2026-07); live-verified 2026-07-08 (cost $0).
# Reasons HEAVILY by default (most output tokens go to reasoning) — give it a generous max_tokens. Good for
# testing, primitive generation, and raw-material digestion/interrogation/preprocessing lanes.
OPENROUTER_HY3_FREE_MODEL = "tencent/hy3:free"
OPENROUTER_HY3_CONTEXT_TOKENS = 262144
AIDEVOBSERVER_AUTO_REUSE_POLICY_ID = "aidevobserver.auto_reuse_policy.v1"
AIDEVOBSERVER_AUTO_REUSE_POLICY_LABEL = "Automatic reuse guidance"
AIDEVOBSERVER_AUTO_REUSE_POLICY_STEPS: tuple[str, ...] = (
    "Treat the user's task as the intent; do not require them to ask for reuse or registry search.",
    "Before creating new implementation code, search global primitives, local source helpers, prior sessions, and workflow/template records.",
    "Prefer an existing component, helper, template, or primitive when the input/output edge and blackbox behavior fit.",
    "If an exact edge does not fit, consider registered deterministic mutation options such as map_sequence, field_rename, output_wrapper, cache, retry, artifact_ref, and idempotency.",
    "When a reusable route is selected, compile it with deterministic template workers first.",
    "Use a coding harness only for missing glue, unresolved recipes, or new component definitions, and pass only compact component labels, blackbox behavior, edges, source refs, and required mutations.",
    "Attach source references, input/output edge notes, candidate confidence, and estimated tokens/model calls avoided to the review report.",
)
AIDEVOBSERVER_AUTO_REUSE_POLICY_FLOW: tuple[str, ...] = (
    "accept_plain_task",
    "search_global_and_local_primitives",
    "match_input_output_edges",
    "consider_registered_mutators",
    "compile_deterministic_route_or_harness_fallback",
    "capture_session_or_live_hook",
    "emit_ranked_candidate_findings",
    "triage_accept_reuse_dismiss",
)
AIDEVOBSERVER_ROUTE_PACKET_LABEL = "AIDEVOBSERVER_ROUTE_PACKET v1"
AIDEVOBSERVER_ROUTE_PACKET_COMPONENT_LIMIT = 2
AIDEVOBSERVER_ROUTE_PACKET_BLACKBOX_CHARS = 140
AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS = 1200
AIDEVOBSERVER_ROUTE_PACKET_NO_MATCH = "components:none; build required glue and record missing primitive candidate"
AIDEVOBSERVER_ROUTE_PACKET_ACTION = (
    "fetch/import refs; wire components into a template/DAG; write only missing glue/tests"
)
AIDEVOBSERVER_ROUTE_PACKET_BUILD_INSTRUCTION = (
    "Use repo instructions. Fetch/import listed refs, wire the DAG/template, then run focused checks."
)
AIDEVOBSERVER_CSV_PRIMITIVE_SOURCE_PATH = "_repos/teleon/backend/src/teleon/ingest/csv_import.py"
AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS = "read_uploaded_csv_rows"
AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE = "validate_required_columns"
AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE = "summarize_csv_import"
AIDEVOBSERVER_CSV_RECIPE_TEMPLATE_ID = "template.data.csv_import.validate.summarize@candidate"
AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH = "_repos/teleon/backend/src/teleon/ingest/browser_table.py"
AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML = "fetch_page_html_with_playwright"
AIDEVOBSERVER_BROWSER_TABLE_EXTRACT = "extract_html_tables"
AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV = "write_table_csv"
AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET = "write_table_parquet"
AIDEVOBSERVER_BROWSER_TABLE_RECIPE_TEMPLATE_ID = "template.web.browser_table.extract.persist@candidate"
AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH = "_repos/teleon/backend/src/teleon/api/policy_flow.py"
AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST = "validate_company_enrichment_request"
AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT = "fetch_account_state"
AIDEVOBSERVER_API_POLICY_APPLY_DECISION = "apply_enrichment_policy"
AIDEVOBSERVER_API_POLICY_PERSIST_DECISION = "persist_policy_decision"
AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE = "emit_api_response"
AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID = "template.api.browser_table.policy.persist.respond@candidate"
AIDEVOBSERVER_WORKSPACE_SOURCE_PREFIX = "_repos/teleon/backend/src/teleon"
AIDEVOBSERVER_WORKSPACE_PRIMITIVE_ROOT = "primitives"
AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT = "primitives.teleon"
AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH = "build_manifest.json"
AIDEVOBSERVER_WORKSPACE_TEST_PATH = "tests/test_generated_flow.py"
AIDEVOBSERVER_WORKSPACE_TEST_TIMEOUT_SECONDS = 20
AIDEVOBSERVER_COMPLEX_TASK_MIN_CAPABILITY_GROUPS = 2
AIDEVOBSERVER_DETERMINISTIC_WORKER_IDS: tuple[str, ...] = (
    "edge_matcher",
    "route_recipe_compiler",
    "template_materializer",
    "artifact_writer",
    "workspace_proof_runner",
    "ledger_writer",
    "gap_recorder",
)
AIDEVOBSERVER_NOOP_EXECUTION_MODE = "needs_build_task"
AIDEVOBSERVER_BUILD_TASK_MIN_CHARS = 12
AIDEVOBSERVER_GREETING_TASKS: tuple[str, ...] = (
    "hello",
    "hi",
    "hey",
    "help",
    "test",
    "ping",
    "yo",
)
AIDEVOBSERVER_BUILD_INTENT_TERMS: tuple[str, ...] = (
    "add",
    "analyze",
    "audit",
    "build",
    "check",
    "classify",
    "clean",
    "compile",
    "connect",
    "create",
    "debug",
    "design",
    "detect",
    "extract",
    "fix",
    "generate",
    "implement",
    "ingest",
    "integrate",
    "migrate",
    "normalize",
    "parse",
    "pipeline",
    "refactor",
    "review",
    "route",
    "scrape",
    "summarize",
    "test",
    "validate",
    "wire",
)
AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS: dict[str, str] = {
    "global_primitives": "OH_OBSERVER_GLOBAL_PRIMITIVES_ENABLED",
    "local_registry": "OH_OBSERVER_EXPOSE_LOCAL_REGISTRY",
    "local_sessions": "OH_OBSERVER_EXPOSE_LOCAL_SESSIONS",
    "mcp": "OH_OBSERVER_MCP_ENABLED",
    "plugins": "OH_OBSERVER_PLUGINS_ENABLED",
    "live_hook": "OH_OBSERVER_LIVE_HOOK_ENABLED",
    "token_savings": "OH_OBSERVER_TOKEN_SAVINGS_ENABLED",
    "llm_rerank": "OH_OBSERVER_LLM_RERANK_ENABLED",
}
#: Deployment-surface mode: when truthy, the observer runs PUBLIC-DEMO-SAFE — local filesystem
#: search + review enrichment default OFF (deny-by-default; contract: check_observer_local_service
#: E-block). Server-side env, never a request parameter (a request must not widen its own scope).
#: Public tunnels/demo launchers MUST set OH_OBSERVER_PUBLIC_DEMO=1; the local developer service
#: leaves it unset. Explicit OH_OBSERVER_EXPOSE_LOCAL_REGISTRY always wins over the mode default.
AIDEVOBSERVER_PUBLIC_DEMO_ENV = "OH_OBSERVER_PUBLIC_DEMO"
AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS: dict[str, bool] = {
    "global_primitives": True,
    # local_registry: DEV default ON (the wedge's first-session value — "your repo already has
    # read_rows" — needs local search on a 127.0.0.1 developer service). Public demos flip it off
    # via AIDEVOBSERVER_PUBLIC_DEMO_ENV above.
    "local_registry": True,
    "local_sessions": True,
    "mcp": True,
    "plugins": True,
    "live_hook": True,
    "token_savings": True,
    "llm_rerank": True,
}
AIDEVOBSERVER_ENABLED_HARNESSES_ENV = "OH_OBSERVER_ENABLED_HARNESSES"
AIDEVOBSERVER_HARNESS_DEFAULTS: dict[str, dict[str, str]] = {
    "opencode": {
        "label": "OpenCode build loop",
        "role": "Ollama Cloud coding lane with GLM/Kimi model IDs",
        "proof": "build script + opencode.json",
        "launch": "./build run --harness opencode",
    },
    "codex": {
        "label": "Codex CLI",
        "role": "local agentic coding session reviewed after or during the run",
        "proof": "session transcript + AIDevObserver review",
        "launch": "codex",
    },
    "claude_code": {
        "label": "Claude Code",
        "role": "MCP server plus optional PreToolUse live hook",
        "proof": "aidevobserver_mcp_server.py + hook",
        "launch": "claude mcp add aidevobserver -- python3 scripts/aidevobserver_mcp_server.py",
    },
    "aider": {
        "label": "Aider",
        "role": "open-source coding harness with observer review on transcript/output",
        "proof": "AIDevObserver review endpoint",
        "launch": "aider",
    },
}
AIDEVOBSERVER_IDE_SESSION_DIR_ENV = "OH_OBSERVER_IDE_SESSION_DIR"
AIDEVOBSERVER_IDE_SESSION_DIR_DEFAULT = ".agent/aidevobserver/ide-sessions"
AIDEVOBSERVER_IDE_SESSION_ID_HEX_CHARS = 16
AIDEVOBSERVER_IDE_SESSION_TITLE_CHARS = 80
AIDEVOBSERVER_IDE_SESSION_LIST_DEFAULT_LIMIT = 12
AIDEVOBSERVER_IDE_SESSION_LIST_MAX_LIMIT = 50
AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT = 6
AIDEVOBSERVER_ROUTE_LEVEL_OUTPUT_EDGES: tuple[str, ...] = (
    "CapabilityBlueprint",
    "PipelineRecipe",
)
AIDEVOBSERVER_ROUTE_LEVEL_KINDS: tuple[str, ...] = (
    "artifact.use_case_blueprint",
    "artifact.microsurface_blueprint",
    "artifact.capability_blueprint",
    "artifact.task_archetype_blueprint",
    "artifact.scenario_blueprint",
    "artifact.capability_template_route",
    "artifact.primitive_group",
)
AIDEVOBSERVER_ROUTE_SLOT_KINDS: tuple[str, ...] = (
    "artifact.capability_slot",
)
AIDEVOBSERVER_ROUTE_BLUEPRINT_QUERY_SUFFIX = " capability blueprint template route pipeline recipe slots"
AIDEVOBSERVER_PLANNER_TOOL_LOOP_MAX_CALLS = 2
AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT = 8
AIDEVOBSERVER_PLANNER_TOOL_RESULT_CHARS = 3600
AIDEVOBSERVER_PLANNER_TOOL_REQUEST_MAX_TOKENS = 700
AIDEVOBSERVER_PLANNER_ROUTE_MAX_TOKENS = 3200
AIDEVOBSERVER_PLANNER_TOOL_REGISTRY_SEARCH = "registry.search"
AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED = "registry.preindexed"
AIDEVOBSERVER_PLANNER_ROUTE_TEMPLATE_ID = "template.aidevobserver.planner_selected_route@candidate"
AIDEVOBSERVER_TOKEN_CHAR_DIVISOR = 4
AIDEVOBSERVER_TOKEN_ESTIMATE_SOURCE_OVERHEAD = 240
PRIMITIVE_THROUGHPUT_LANES_PATH = "catalog/knowledge-packs/data/primitive-throughput-lanes/lanes.jsonl"
PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED = 5000
PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED = 20000
PRIMITIVE_THROUGHPUT_REQUIRED_PROOF_GATES: tuple[str, ...] = (
    "source_evidence_gate",
    "contract_schema_gate",
    "deterministic_factory_gate",
    "fixture_or_property_test_gate",
    "candidate_boundary_gate",
)
OPPORTUNITY_INTELLIGENCE_GUIDANCE_PATH = "docs/codex/opportunity-intelligence-primitive-guidance.md"
OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH = (
    "catalog/knowledge-packs/data/opportunity-intelligence-source-map/sources.jsonl"
)
OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/opportunity_intelligence_group_candidates.jsonl"
)
OPPORTUNITY_INTELLIGENCE_MIN_SOURCE_MAP_ROWS = 18
OPPORTUNITY_INTELLIGENCE_MIN_GROUP_CANDIDATE_ROWS = 16
OPPORTUNITY_INTELLIGENCE_REQUIRED_PROOF_REQUIREMENTS: tuple[str, ...] = (
    "source_ref_resolution",
    "license_policy_review",
    "input_contract_test",
    "output_contract_test",
    "side_effect_audit",
    "candidate_boundary_gate",
)
PRIMITIVE_FACTORY_5K_LANES_PATH = "catalog/knowledge-packs/data/primitive-factory-5k-lanes/lanes.jsonl"
PRIMITIVE_FACTORY_DAILY_SHARDS_DIR = "data/dev-intel/primitive_factory/daily_shards"
PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR = "data/dev-intel/primitive_factory/daily_shards_20k"
PRIMITIVE_FACTORY_BATCH_RUNS_DIR = "data/dev-intel/primitive_factory/batch_runs"
PRIMITIVE_FACTORY_FLEET_RUNS_DIR = "data/dev-intel/primitive_factory/fleet_runs"
PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE = "data/dev-intel/primitive_factory/GEMMA_PAUSE.json"
PRIMITIVE_FACTORY_OLLAMA_PAUSE_FILE = "data/dev-intel/primitive_factory/OLLAMA_PAUSE.json"
#: Gemma/Open WebUI lane infrastructure breaker (distinct from the operator-controlled GEMMA_PAUSE file above):
#: written by the CDP/HTTP client circuit breaker when the Open WebUI ORIGIN behind the Cloudflare edge is
#: down/degraded (edge 5xx family: 521/522/523/530 down, 502/504/520/524 degraded), so shard workers fail fast
#: with a labeled error instead of burning shards against a dead origin (observed 2026-07-02: 100+ shards burned
#: on status=521 "Web server is down" in one batch run).
PRIMITIVE_FACTORY_GEMMA_SESSION_DOWN_FILE = "data/dev-intel/primitive_factory/GEMMA_SESSION_DOWN.json"
#: SEVERE cross-process pacing for the shared Gemma GPU behind Open WebUI (owner 2026-07-02: "we have overloaded
#: something on that GPU hardware"). ONE gemma call at a time fleet-wide (fcntl lock on the state file) plus a
#: minimum spacing between calls measured across ALL processes. The state file's `min_interval_seconds` field is
#: the owner-tunable override (no code change needed); `enabled: false` in the state file disables the limiter.
PRIMITIVE_FACTORY_GEMMA_RATE_LIMIT_FILE = "data/dev-intel/primitive_factory/GEMMA_RATE_LIMIT.json"
GEMMA_MIN_CALL_INTERVAL_SECONDS = 45  # >= 45s between gemma call starts, fleet-wide (severe by owner request 2026-07-02)
GEMMA_RATE_LIMIT_MAX_SLEEP_SECONDS = 20  # waits <= this sleep-then-proceed; longer waits fail fast with a labeled
#: error so shard workers requeue instead of queueing on the lock and piling onto the GPU when it reopens.
PRIMITIVE_FACTORY_MONITOR_DIST_DIR = "dist/primitive-factory-monitor"
PRIMITIVE_FACTORY_GEMMA_MONITOR_DEFAULT_PORT = 9174
PRIMITIVE_FACTORY_MONITOR_REFRESH_SECONDS = 5
PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL = PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED
PRIMITIVE_FACTORY_TARGET_DAILY_RAW = PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED
PRIMITIVE_FACTORY_20K_TARGET_DAILY_USEFUL = PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED
PRIMITIVE_FACTORY_20K_TARGET_MULTIPLIER = (
    PRIMITIVE_FACTORY_20K_TARGET_DAILY_USEFUL // PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL
)
PRIMITIVE_FACTORY_20K_TARGET_DAILY_RAW = (
    PRIMITIVE_FACTORY_TARGET_DAILY_RAW * PRIMITIVE_FACTORY_20K_TARGET_MULTIPLIER
)
PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET = 25
PRIMITIVE_FACTORY_FAST_SHARD_USEFUL_TARGET = 10
PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER = "kimi-k2.7-code"
PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER = "glm-5.2"
LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS = 65536
OPENWEBUI_BASE_URL_ENV = "OPENWEBUI_BASE_URL"
OPENWEBUI_MODEL_ENV = "OPENWEBUI_MODEL"
OPENWEBUI_TOKEN_ENV = "OPENWEBUI_TOKEN"
OPENWEBUI_CDP_URL_ENV = "OPENWEBUI_CDP_URL"
OPENWEBUI_DEFAULT_BASE_URL = "https://ui.iamretarded.net"
OPENWEBUI_DEFAULT_MODEL = "gemma-4-coding"
OPENWEBUI_CHAT_COMPLETIONS_PATH = "/api/chat/completions"
PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER = OPENWEBUI_DEFAULT_MODEL
PRIMITIVE_FACTORY_PROVIDER_FLEET_LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "gemma_openwebui_cdp_candidate_writer",
        "role": "efficient_candidate_writer",
        "provider": "openwebui",
        "model": PRIMITIVE_FACTORY_MODEL_GEMMA_CANDIDATE_WRITER,
        "mode": "cdp",
        "workers": 2,
        "batch_size": 25,
        "max_batches": 1,
        "timeout": 420,
    },
    {
        "lane_id": "glm_ollama_direct_candidate_writer",
        "role": "high_yield_candidate_writer",
        "provider": "ollama",
        "model": PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
        "mode": "direct",
        "workers": 2,
        "batch_size": 10,
        "max_batches": 1,
        # 480s (was 300): healthy GLM candidate-writer calls measured median 192s / max 296s
        # (2026-07-01-g0090 call_events), so 300s left near-zero headroom — under 2026-07-02 API
        # queueing every call timed out at exactly 300.2s. Match the Kimi lane's 480s.
        "timeout": 480,
    },
    {
        "lane_id": "kimi_ollama_direct_long_expander",
        "role": "long_expansion_and_diversity_reviewer",
        "provider": "ollama",
        "model": PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
        "mode": "direct",
        "workers": 2,
        "batch_size": 4,
        "max_batches": 1,
        "timeout": 480,
    },
)
#: SINGLE SOURCE for the model-lane output contract + example row (imported by every shard-prompt builder —
#: build_primitive_factory_5k_shards.py and build_primitive_pipeline_catalog_intake.py — never retyped).
#: Rationale (2026-07-02): all 440 Kimi + 166 GLM slow-tier rejects were json_decode_error = truncated objects;
#: an explicit complete-rows-over-truncation rule + a one-line schema example are the two highest-yield
#: standardization levers for small/slow model lanes.
PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT = (
    "OUTPUT CONTRACT (follow exactly): respond with JSONL only — one COMPLETE JSON object per line. "
    "No markdown fences, no prose, no headings, no reasoning text in the response body; put the final JSONL in the "
    "message content. Use double-quoted keys and strings, no trailing commas, escape internal newlines as \\n, and "
    "never split one object across lines. Every line must independently parse with json.loads. "
    "TRUNCATION RULE: if the token budget runs low, STOP after the last complete line — fewer complete rows always "
    "beat one truncated row; never emit a partial object. "
)
PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW = (
    "SCHEMA SHAPE EXAMPLE (shape only — REPLACE EVERY VALUE with row-specific content; source_refs must cite this "
    "shard's Sources list, never this example URL): "
    '{"primitive_id":"prim:LANE:slug:001","kind":"primitive","title":"Short capability title",'
    '"input_edge":"TypedInputBatch+Policy","output_edge":"TypedResult+Receipt",'
    '"input_edge_description":"What a caller must construct, field by field, to invoke this.",'
    '"output_edge_description":"What comes back, when it is safe to consume, and the receipt to verify first.",'
    '"contract":{"summary":"One-sentence behavior.","input":{"TypedInputBatch":"fields"},'
    '"output":{"TypedResult":"fields"},"errors":["typed_error_one","typed_error_two"]},'
    '"edge_contract":{"input_edge_description":"...","output_edge_description":"...","preconditions":["..."],'
    '"postconditions":["..."],"failure_modes":["..."],"composition_notes":"wiring + idempotency + tests"},'
    '"blackbox":"What it does without implementation detail.","effects":[{"type":"compute","description":"local"}],'
    '"source_refs":[{"label":"official_docs","url":"https://docs.python.org/3/"}],"mutators":["field_rename"],'
    '"proof_requirements":["golden fixture roundtrip","candidate_boundary_gate"],'
    '"promotion_blockers":["no adapter receipts yet"],"dedupe_key":"typedinputbatch->typedresult::slug",'
    '"candidate":true,"serves_truth":false}'
)
PRIMITIVE_FACTORY_REQUIRED_MODEL_ROLES: tuple[str, ...] = (
    "codex_orchestrator",
    "kimi_candidate_writer",
    "glm_contract_reviewer",
    "deterministic_validator",
)
PRIMITIVE_FACTORY_REQUIRED_USEFULNESS_GATES: tuple[str, ...] = (
    "source_ref_resolution",
    "visible_edge_contract",
    "hidden_member_edge_or_single_step_contract",
    "proof_plan_attached",
    "dedupe_key_attached",
    "candidate_boundary_gate",
)
AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl"
)
AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_MANIFEST_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/manifest.json"
)
AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS = 10000
AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/tasks.jsonl"
)
AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_MANIFEST_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/manifest.json"
)
AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS = 10000
AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl"
)
AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards_manifest.json"
)
AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_FAMILY = "aidevexplorer_runtime_shape_task_corpus"
AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_EVIDENCE_STATUS = "curated_synthetic_benchmark_seed"
AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/families.jsonl"
)
AIDEVEXPLORER_PRIMITIVE_KIND_FAMILY_CATALOG_MANIFEST_PATH = (
    "catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/manifest.json"
)
BENCHMARK_LAB_ADAPTER_CATALOG_ROWS_PATH = (
    "catalog/knowledge-packs/data/benchmark-lab-adapter-catalog/benchmarks.jsonl"
)
BENCHMARK_LAB_ADAPTER_CATALOG_MANIFEST_PATH = (
    "catalog/knowledge-packs/data/benchmark-lab-adapter-catalog/manifest.json"
)
BENCHMARK_LAB_ADAPTER_CATALOG_SOURCE_FAMILY = "external_brief_benchmark_adapter_catalog"
BENCHMARK_LAB_ADAPTER_CATALOG_EVIDENCE_STATUS = "unverified_intake_names_require_adapter_verification"
COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR = (
    "catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds"
)
COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_MANIFEST_PATH = (
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR + "/manifest.json"
)
COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_FAMILY = "compiled_primitive_route_benchmark_seed_pack"
COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_STATUS = "handoff_seed_needs_local_benchmark_adapters"
COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS = "external_prior_art_not_local_measured_evidence"
AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl"
)
AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards_manifest.json"
)
AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY = "aidevexplorer_primitive_kind_family_catalog"
AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_EVIDENCE_STATUS = "curated_synthetic_kind_seed"
AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards_manifest.json"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_proof_bundles.jsonl"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_proof_bundles_manifest.json"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_promotion_gates.jsonl"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_promotion_gates_manifest.json"
)
AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_PATH = "_repos/teleon/backend/src/teleon/primitives/groups.py"
AIDEVOBSERVER_SOURCE_BACKED_GROUP_UNIT_TEST_PATH = "tests/unit/test_teleon_primitive_groups.py"
AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY = "curated_first_party_primitive_group"
AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH = (
    "data/dev-intel/implemented_code_primitives/daily_20260702_2k/implemented_code_primitives.jsonl"
)
AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_COMPAT_PATH = (
    "data/dev-intel/implemented_code_primitives/daily_20260702_2k/primitive_candidate_records_compatible.jsonl"
)
AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVE_SOURCE_FAMILY = "implemented_code_ast_mining"
AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND = "implemented_code_primitive_registry"
AIDEVEXPLORER_RUNTIME_SHAPES: tuple[str, ...] = (
    "py.fn",
    "api.endpoint",
    "microservice",
    "webhook.handler",
    "queue.consumer",
    "cron.job",
    "cli.command",
    "workflow.automation",
    "kubernetes.job",
    "dashboard.report",
)
AIDEVEXPLORER_TASK_AUDIENCES: tuple[str, ...] = (
    "solo_developer",
    "freelancer",
    "dev_team",
    "software_architect",
)
AIDEVEXPLORER_REQUIRED_TASK_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "source_kind",
    "corpus_kind",
    "audience",
    "task_family",
    "industry",
    "intent",
    "expected_template",
    "expected_primitives",
    "expected_primitive_groups",
    "expected_deliverables",
    "acceptance_criteria",
    "observed_reinvention_patterns",
    "common_pitfalls",
    "aidevexplorer_eval_hooks",
    "trust",
    "serves_truth",
)
AIDEVEXPLORER_REQUIRED_RUNTIME_SHAPE_TASK_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "source_kind",
    "corpus_kind",
    "business_task",
    "task_family",
    "industry",
    "audience",
    "primitive_kind",
    "runtime_shape",
    "input_edge",
    "output_edge",
    "core_group_edge",
    "wrapper_edges",
    "hidden_member_edges",
    "likely_primitives",
    "expected_primitive_groups",
    "adapter_mutators",
    "effects",
    "proof_requirements",
    "common_pitfalls",
    "aidevexplorer_eval_hooks",
    "trust",
    "serves_truth",
)
AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR = "data/dev-intel/aidevexplorer_task_benchmarks"
AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE = 100
AIDEVEXPLORER_TASK_BENCHMARK_SUITE_COUNT = (
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS
    // AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE
)
AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME = "task_decompositions.jsonl"
AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME = "task_decompositions_manifest.json"
AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS = 4
AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT = 30
AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards.jsonl"
)
AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_MANIFEST_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards_manifest.json"
)
AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY = "aidevexplorer_benchmark_task_decomposition"
AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_EVIDENCE_STATUS = "curated_synthetic_benchmark_decomposition_seed"
AIDEVOBSERVER_FLYWHEEL_RUNS_DIR = "data/dev-intel/aidevobserver_flywheel_runs"
AIDEVOBSERVER_ROUTE_QUALITY_BASE_SCORE = 25
AIDEVOBSERVER_ROUTE_QUALITY_EXACT_EDGE_POINTS = 8
AIDEVOBSERVER_ROUTE_QUALITY_NODE_POINTS = 4
AIDEVOBSERVER_ROUTE_QUALITY_PLANNER_POINTS = 10
AIDEVOBSERVER_ROUTE_QUALITY_DETERMINISTIC_POINTS = 18
AIDEVOBSERVER_ROUTE_QUALITY_TEST_POINTS = 10
AIDEVOBSERVER_ROUTE_QUALITY_HARNESS_PENALTY = 18
AIDEVOBSERVER_ROUTE_QUALITY_MAX_SCORE = 100
AIDEVOBSERVER_RUNTIME_TARGET_LOCAL = "local.python"
AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER = "container.python"
AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB = "k8s.job"
AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT = "k8s.deployment"
AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB = "k8s.cronjob"
AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION = "cloud.function.http"
AIDEVOBSERVER_RUNTIME_TARGET_NONE = "none"
AIDEVOBSERVER_RUNTIME_TARGETS: tuple[str, ...] = (
    AIDEVOBSERVER_RUNTIME_TARGET_LOCAL,
    AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION,
)
AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE = "public_demo_safe_candidate"
AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY = "private_internal_only"
AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC = "public"
AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL = "local"
AIDEVOBSERVER_VISIBILITY_SCOPE_ALL = "all"
AIDEVOBSERVER_VISIBILITY_SCOPES: tuple[str, ...] = (
    AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL,
    AIDEVOBSERVER_VISIBILITY_SCOPE_ALL,
)
AIDEVOBSERVER_MUTATOR_MAP_SEQUENCE = "map_sequence"
AIDEVOBSERVER_MUTATOR_FILTER_PREDICATE = "filter_predicate"
AIDEVOBSERVER_MUTATOR_FIELD_RENAME = "field_rename"
AIDEVOBSERVER_MUTATOR_FIELD_PROJECT = "field_project"
AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER = "output_wrapper"
AIDEVOBSERVER_MUTATOR_INPUT_ENVELOPE_WRAPPER = "input_envelope_wrapper"
AIDEVOBSERVER_MUTATOR_TYPE_CAST = "type_cast"
AIDEVOBSERVER_MUTATOR_UNIT_CONVERSION = "unit_conversion"
AIDEVOBSERVER_MUTATOR_DATE_TIME_NORMALIZE = "date_time_normalize"
AIDEVOBSERVER_MUTATOR_ARTIFACT_MATERIALIZE = "artifact_materialize"
AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE = "artifact_reference"
AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER = "cache_wrapper"
AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER = "retry_wrapper"
AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER = "idempotency_wrapper"
AIDEVOBSERVER_MUTATOR_PAGINATION_EXPANDER = "pagination_expander"
AIDEVOBSERVER_MUTATOR_BATCH_CHUNKER = "batch_chunker"
AIDEVOBSERVER_MUTATOR_FANOUT_FANIN = "fanout_fanin"
AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER = "schema_validator_inserter"
AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER = "provenance_wrapper"
AIDEVOBSERVER_MUTATOR_REDACTION_WRAPPER = "redaction_wrapper"
AIDEVOBSERVER_MUTATOR_SECRET_REF_WRAPPER = "secret_ref_wrapper"
AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER = "api_endpoint_wrapper"
AIDEVOBSERVER_MUTATOR_CLI_WRAPPER = "cli_wrapper"
AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER = "cloud_function_wrapper"
AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER = "k8s_job_wrapper"
AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER = "k8s_deployment_wrapper"
AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER = "k8s_cronjob_wrapper"
AIDEVOBSERVER_DETERMINISTIC_MUTATOR_IDS: tuple[str, ...] = (
    AIDEVOBSERVER_MUTATOR_MAP_SEQUENCE,
    AIDEVOBSERVER_MUTATOR_FILTER_PREDICATE,
    AIDEVOBSERVER_MUTATOR_FIELD_RENAME,
    AIDEVOBSERVER_MUTATOR_FIELD_PROJECT,
    AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_INPUT_ENVELOPE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_TYPE_CAST,
    AIDEVOBSERVER_MUTATOR_UNIT_CONVERSION,
    AIDEVOBSERVER_MUTATOR_DATE_TIME_NORMALIZE,
    AIDEVOBSERVER_MUTATOR_ARTIFACT_MATERIALIZE,
    AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE,
    AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_PAGINATION_EXPANDER,
    AIDEVOBSERVER_MUTATOR_BATCH_CHUNKER,
    AIDEVOBSERVER_MUTATOR_FANOUT_FANIN,
    AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER,
    AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_REDACTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_SECRET_REF_WRAPPER,
    AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
)

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
# env-overridable DEFAULT in _repos/shared-backend-components/scripts/model_gateway.py (OH_LLM_CHATANYWHERE_MODEL)
# and is documented once in baltor-free-llm-demo-routing.md; registering it here
# is the single source of truth so the same id in the doc/gateway is not flagged
# as drift (_repos/shared-backend-components/docs/codex/no-magic-values.md).
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
# as a fallback_adapter across _repos/shared-backend-components/architecture/external_capability_catalog.json and
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

# --- Primitive registry operational schema ---------------------------------
# Hot-path Teleon/AIDevObserver primitive tables. Keep this list here so
# validators, load planners, and future migration generators do not carry
# parallel hand-maintained schema contracts.
PRIMITIVE_REGISTRY_OPERATIONAL_TABLES = (
    "registry_record",
    "primitive_edge",
    "primitive_graph_edge",
    "primitive_effect",
    "registry_embedding",
    "primitive_blocking_profile",
    "primitive_blocking_key",
    "mutator_agent",
    "primitive_mutation_option",
    "primitive_quality_assessment",
    "variation_record",
    "primitive_runtime_profile",
    "runtime_observation",
    "registry_source",
    "registry_source_link",
    "proof_bundle",
    "search_event",
    "search_result_event",
    "reuse_outcome_event",
)

PRIMITIVE_REGISTRY_OPERATIONAL_LOAD_DIRNAME = "primitive-registry-operational-load"
PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIRNAME = "csv"
PRIMITIVE_REGISTRY_OPERATIONAL_LOAD_DIR = DIST_DIR / PRIMITIVE_REGISTRY_OPERATIONAL_LOAD_DIRNAME
PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIR = (
    PRIMITIVE_REGISTRY_OPERATIONAL_LOAD_DIR / PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIRNAME
)

PRIMITIVE_REGISTRY_OPERATIONAL_VIEWS = (
    "primitive_search_view",
    "edge_compatible_view",
    "primitive_quality_latest_view",
    "aidevobserver_reuse_view",
    "aidevobserver_surfaceable_reuse_view",
)

# --- Primitive registry quality/promotion sieve ----------------------------
# These settings define the deterministic line between broad real-code
# candidate substrate and the smaller AIDevObserver-safe suggestion surface.
# Scores are not truth claims; they select candidate rows for enrichment,
# review, and source-ref search without promoting them.
PRIMITIVE_QUALITY_DIRNAME = "quality"
PRIMITIVE_QUALITY_ARTIFACT_FILES = {
    "assessments": "primitive_quality_assessments.jsonl",
    "high_value": "high_value_candidates.jsonl",
    "surfaceable": "aidevobserver_surfaceable_primitives.jsonl",
    "needs_contract_enrichment": "needs_contract_enrichment.jsonl",
    "noise": "noise_low_level_symbols.jsonl",
    "registry_record_quality_patches": "registry_record_quality_patches.jsonl",
    "manifest": "quality_manifest.json",
    "summary": "summary.md",
}
PRIMITIVE_QUALITY_READINESS_R3 = "R3_contract_known"
PRIMITIVE_QUALITY_READINESS_R5 = "R5_enriched_candidate"
PRIMITIVE_QUALITY_READINESS_R8 = "R8_aidevobserver_surfaceable"
PRIMITIVE_QUALITY_TRUST_CANDIDATE = "candidate"
PRIMITIVE_QUALITY_TRUST_VALIDATED = "validated"
PRIMITIVE_QUALITY_CLASS_SURFACEABLE = "surfaceable_reuse_candidate"
PRIMITIVE_QUALITY_CLASS_HIGH_VALUE = "high_value_candidate"
PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT = "needs_contract_enrichment"
PRIMITIVE_QUALITY_CLASS_NOISE = "noise_low_level_symbol"
PRIMITIVE_QUALITY_CLASS_HOLD = "hold_for_review"
# Minimum deterministic quality score to enter broad reuse-review queues.
PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE = 58
# Minimum deterministic quality score to appear in default AIDevObserver reuse
# suggestions. Surfaceability also requires no blocking quality defects.
PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE = 74
# Bound emitted examples/reasons in summaries so large corpus runs stay readable.
PRIMITIVE_QUALITY_SUMMARY_EXAMPLE_LIMIT = 12
# A blackbox description below this token count is treated as too thin for a
# developer/agent to understand the primitive without reading source.
PRIMITIVE_QUALITY_MIN_BLACKBOX_TOKENS = 6
PRIMITIVE_QUALITY_UNKNOWN_CONTRACT_MARKERS = (
    "",
    "unknown",
    "unknown_candidate",
    "repo_default_or_unknown",
    "any",
)
PRIMITIVE_QUALITY_NOISE_PATH_PARTS = (
    "__pycache__",
    ".pytest_cache",
    "tests",
    "__tests__",
    "fixtures",
)
PRIMITIVE_QUALITY_NOISE_NAME_MARKERS = (
    "py_local_",
    "py_arg_",
    "test_",
    "_test_",
    "__main__",
    "self_test",
)
PRIMITIVE_QUALITY_GENERIC_HELPER_SYMBOL_NAMES = (
    "main",
    "run_cli",
    "cli",
    "get",
    "post",
    "put",
    "write",
    "read",
    "load",
    "save",
    "slug",
    "headers",
    "classify_has",
    "has",
)
PRIMITIVE_QUALITY_PREFERRED_SYMBOL_KINDS = (
    "function",
    "method",
    "class",
)
PRIMITIVE_QUALITY_LOW_VALUE_SYMBOL_KINDS = (
    "arg",
    "var",
    "const",
    "instance",
)
PRIMITIVE_QUALITY_DOMAIN_RULES = {
    "parsing": ("parse", "parser", "read", "reader", "csv", "json", "yaml", "xml", "pdf", "html"),
    "validation": ("validate", "validator", "schema", "check", "verify", "iban", "luhn"),
    "normalization": ("normalize", "clean", "canonical", "standardize", "format", "date"),
    "extraction": ("extract", "regex", "email", "phone", "url", "entity", "field"),
    "retrieval_search": ("search", "retrieve", "query", "index", "lookup", "rank", "rerank"),
    "embedding_similarity": ("embed", "embedding", "similarity", "cosine", "vector", "hash"),
    "caching_retry": ("cache", "retry", "backoff", "ttl", "idempotency"),
    "api_integration": ("api", "http", "client", "request", "response", "endpoint"),
    "database": ("db", "sql", "postgres", "sqlite", "database", "query"),
    "file_artifact": ("file", "path", "artifact", "parquet", "upload", "download"),
    "ml_data_science": ("model", "train", "feature", "score", "metric", "regression", "classification"),
    "frontend_quality": ("tsx", "react", "frontend", "a11y", "snapshot", "css", "design"),
    "devops_cloud": ("deploy", "kubernetes", "k8s", "cloud", "container", "helm", "terraform"),
    "workflow_observer": ("session", "ledger", "observer", "workflow", "agent", "planlock"),
}
PRIMITIVE_GLOBAL_SEARCH_STOPWORDS = (
    "a",
    "about",
    "add",
    "agent",
    "an",
    "and",
    "as",
    "be",
    "build",
    "by",
    "code",
    "create",
    "custom",
    "do",
    "existing",
    "for",
    "from",
    "helper",
    "i",
    "implement",
    "in",
    "into",
    "make",
    "me",
    "new",
    "of",
    "on",
    "or",
    "please",
    "py",
    "python",
    "registry",
    "reuse",
    "the",
    "this",
    "to",
    "use",
    "using",
    "want",
    "with",
    "write",
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
