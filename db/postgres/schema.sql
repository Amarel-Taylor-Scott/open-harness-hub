-- ----------------------------------------------------------------------------
-- Open Harness Hub — canonical PostgreSQL schema (v0.1.0)
--
-- Maps one row per component, with JSONB body for type-specific fields and
-- small join tables for the array-valued cross-cutting axes (industry,
-- capability, modality, tag). Rule and knowledge leaves get their own
-- query-friendly tables.
--
-- This schema is the SOURCE OF TRUTH for relational stores. Document /
-- key-value / vector mappings derive from this.
-- ----------------------------------------------------------------------------

BEGIN;

-- Optional but recommended for the default hosted shape. Deployments that
-- cannot install pgvector can omit vector columns and use the JSONL/object
-- storage path as an interchange layer.
CREATE EXTENSION IF NOT EXISTS vector;

-- The component table holds one row per active reusable component.
-- Repository files are seed/export definitions; Postgres is the canonical
-- operational store for the hosted product.
CREATE TABLE IF NOT EXISTS component (
  id              TEXT PRIMARY KEY,
  type            TEXT NOT NULL
                       CHECK (type IN ('harness','pipeline','benchmark','rule-pack','knowledge-pack','logic-pack','tool','persona','adapter','rubric','dataset','schema','processor','pattern')),
  component_layer TEXT
                       CHECK (component_layer IS NULL OR component_layer IN ('pre_llm','llm','post_llm','control_flow','data','evaluation','deployment','governance')),
  control_flow_kind TEXT
                       CHECK (control_flow_kind IS NULL OR control_flow_kind IN ('loop','iterate','map','reduce','branch','retry','parallel','human_review','cache_lookup','fallback','stop')),
  version         TEXT NOT NULL,
  name            TEXT NOT NULL,
  description     TEXT NOT NULL,
  license         TEXT NOT NULL,
  lifecycle       TEXT NOT NULL
                       CHECK (lifecycle IN ('experimental','beta','stable','deprecated')),
  trust_boundary  TEXT
                       CHECK (trust_boundary IS NULL OR trust_boundary IN ('local','hub','external','mixed')),
  freshness       TEXT
                       CHECK (freshness IS NULL OR freshness IN ('stable','volatile','dated')),
  created         DATE,
  updated         DATE,
  superseded_by   TEXT REFERENCES component(id),
  deprecated_on   DATE,
  attribution     JSONB,
  links           JSONB,
  body            JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS component_type_idx     ON component (type);
CREATE INDEX IF NOT EXISTS component_lifecycle_idx ON component (lifecycle);
CREATE INDEX IF NOT EXISTS component_layer_idx ON component (component_layer);
CREATE INDEX IF NOT EXISTS component_control_flow_idx ON component (control_flow_kind) WHERE control_flow_kind IS NOT NULL;

CREATE TABLE IF NOT EXISTS component_version (
  component_version_id TEXT PRIMARY KEY,
  component_id         TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  version              TEXT NOT NULL,
  version_status       TEXT NOT NULL CHECK (version_status IN ('draft','review','active','deprecated','superseded')),
  change_summary       TEXT,
  definition_source    TEXT CHECK (definition_source IS NULL OR definition_source IN ('database','repo_seed','signed_publisher','generated_factory','tenant_private','import')),
  source_ref           TEXT,
  definition_hash      TEXT,
  body                 JSONB NOT NULL,
  created_at           TIMESTAMPTZ DEFAULT now(),
  activated_at         TIMESTAMPTZ,
  UNIQUE (component_id, version)
);
CREATE INDEX IF NOT EXISTS component_version_component_idx ON component_version (component_id, version_status);

-- Database-backed settings registry for values that otherwise rot as YAML,
-- prose, or scattered literals: model routes, embedding dimensions, vector
-- backends, thresholds, cloud targets, feature flags, and object defaults.
-- Repo files may seed/export these rows, but the hosted product should read
-- effective settings from the database.
CREATE TABLE IF NOT EXISTS setting_profile (
  setting_profile_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  namespace          TEXT NOT NULL,
  setting_key        TEXT NOT NULL,
  setting_kind       TEXT NOT NULL CHECK (setting_kind IN (
    'model_route',
    'embedding_model',
    'rerank_model',
    'judge_model',
    'vector_index',
    'storage_backend',
    'cloud_backend',
    'threshold',
    'batching',
    'feature_flag',
    'object_default',
    'policy',
    'custom'
  )),
  value_type         TEXT NOT NULL CHECK (value_type IN (
    'string',
    'number',
    'boolean',
    'json',
    'uri',
    'duration',
    'dimension',
    'enum',
    'secret_ref'
  )),
  default_value      JSONB NOT NULL,
  allowed_values     JSONB NOT NULL DEFAULT '[]'::jsonb,
  validation         JSONB NOT NULL DEFAULT '{}'::jsonb,
  owner_team         TEXT,
  source_of_truth    TEXT NOT NULL CHECK (source_of_truth IN (
    'database',
    'repo_seed',
    'environment',
    'tenant_override',
    'external_control_plane'
  )),
  lifecycle          TEXT NOT NULL DEFAULT 'active'
                       CHECK (lifecycle IN ('draft','active','deprecated','archived')),
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, namespace, setting_key)
);
CREATE INDEX IF NOT EXISTS setting_profile_kind_idx ON setting_profile (tenant_id, setting_kind);
CREATE INDEX IF NOT EXISTS setting_profile_namespace_idx ON setting_profile (tenant_id, namespace);
CREATE INDEX IF NOT EXISTS setting_profile_body_gin_idx ON setting_profile USING GIN (body);

CREATE TABLE IF NOT EXISTS setting_value (
  setting_value_id   TEXT PRIMARY KEY,
  setting_profile_id TEXT NOT NULL REFERENCES setting_profile(setting_profile_id) ON DELETE CASCADE,
  tenant_id          TEXT NOT NULL,
  scope              JSONB NOT NULL DEFAULT '{}'::jsonb,
  value              JSONB NOT NULL,
  effective_from     TIMESTAMPTZ NOT NULL DEFAULT now(),
  effective_to       TIMESTAMPTZ,
  version            TEXT,
  value_hash         TEXT,
  set_by             JSONB NOT NULL DEFAULT '{}'::jsonb,
  lineage_event_id   TEXT,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS setting_value_profile_idx ON setting_value (setting_profile_id, effective_from DESC);
CREATE INDEX IF NOT EXISTS setting_value_scope_gin_idx ON setting_value USING GIN (scope);
CREATE INDEX IF NOT EXISTS setting_value_body_gin_idx ON setting_value USING GIN (body);

-- Import/export ledger for repository manifests. Catalog YAML/Markdown files
-- are reviewable seed/export artifacts; these rows record when a file was
-- imported into the operational database, which content hash was used, and
-- whether the seed artifact now looks stale, deprecated, duplicated, or
-- otherwise unsafe to treat as current operational truth.
CREATE TABLE IF NOT EXISTS manifest_import_batch (
  manifest_import_batch_id TEXT PRIMARY KEY,
  source_kind              TEXT NOT NULL CHECK (source_kind IN ('repo_catalog','repo_docs','jsonl_export','database_export','tenant_export','manual')),
  source_ref               TEXT,
  importer                 TEXT,
  import_mode              TEXT NOT NULL CHECK (import_mode IN ('dry_run','stage','upsert','export_only')),
  policy                   JSONB NOT NULL DEFAULT '{}'::jsonb,
  summary                  JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS manifest_import_batch_created_idx ON manifest_import_batch (created_at DESC);

CREATE TABLE IF NOT EXISTS manifest_import_record (
  manifest_import_record_id TEXT PRIMARY KEY,
  manifest_import_batch_id  TEXT NOT NULL REFERENCES manifest_import_batch(manifest_import_batch_id) ON DELETE CASCADE,
  component_id              TEXT,
  component_type            TEXT,
  manifest_path             TEXT NOT NULL,
  manifest_hash             TEXT NOT NULL,
  manifest_updated          DATE,
  manifest_lifecycle        TEXT,
  manifest_freshness        TEXT,
  definition_source         TEXT NOT NULL CHECK (definition_source IN ('repo_seed','database_export','jsonl_export','tenant_export','manual')),
  import_status             TEXT NOT NULL CHECK (import_status IN ('mapped','staged','upserted','skipped','failed')),
  recommended_action        TEXT NOT NULL CHECK (recommended_action IN ('import','review','archive_seed','deprecate','supersede','hold')),
  rotted_context_flags      JSONB NOT NULL DEFAULT '[]'::jsonb,
  row_counts                JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_ref                TEXT,
  error_message             TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (manifest_import_batch_id, manifest_path)
);
CREATE INDEX IF NOT EXISTS manifest_import_record_component_idx ON manifest_import_record (component_id, created_at DESC);
CREATE INDEX IF NOT EXISTS manifest_import_record_path_idx ON manifest_import_record (manifest_path);
CREATE INDEX IF NOT EXISTS manifest_import_record_hash_idx ON manifest_import_record (manifest_hash);
CREATE INDEX IF NOT EXISTS manifest_import_record_action_idx ON manifest_import_record (recommended_action, import_status);
CREATE INDEX IF NOT EXISTS manifest_import_record_flags_gin_idx ON manifest_import_record USING GIN (rotted_context_flags);

-- Review ledger for stale, superseded, duplicated, or otherwise fragile
-- repository context. This table is deliberately advisory: a candidate row
-- does not approve a file move. It records what the audit found, why it was
-- flagged, what replacement was inferred, and which checks must happen before
-- a curator archives or supersedes the file.
CREATE TABLE IF NOT EXISTS context_archive_candidate (
  archive_candidate_id       TEXT PRIMARY KEY,
  tenant_id                  TEXT NOT NULL,
  source_path                TEXT NOT NULL,
  source_kind                TEXT NOT NULL CHECK (source_kind IN ('repo_doc','repo_prompt','repo_spec','repo_strategy','repo_research','repo_howto','repo_architecture','repo_codex','other')),
  source_hash                TEXT,
  status                     TEXT NOT NULL CHECK (status IN ('candidate','keep_active','supersede','archive_ready','archived')),
  suggested_action           TEXT NOT NULL CHECK (suggested_action IN ('candidate','keep_active','supersede','archive_ready')),
  severity_score             INTEGER NOT NULL CHECK (severity_score >= 0),
  confidence                 TEXT NOT NULL CHECK (confidence IN ('low','medium','high')),
  canonical_replacement_hint TEXT,
  reasons                    JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_next_checks       JSONB NOT NULL DEFAULT '[]'::jsonb,
  detected_by                TEXT NOT NULL,
  detection_source           TEXT NOT NULL,
  body                       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source_path, detection_source)
);
CREATE INDEX IF NOT EXISTS context_archive_candidate_path_idx ON context_archive_candidate (source_path);
CREATE INDEX IF NOT EXISTS context_archive_candidate_status_idx ON context_archive_candidate (tenant_id, status, severity_score DESC);
CREATE INDEX IF NOT EXISTS context_archive_candidate_replacement_idx ON context_archive_candidate (canonical_replacement_hint) WHERE canonical_replacement_hint IS NOT NULL;
CREATE INDEX IF NOT EXISTS context_archive_candidate_reasons_gin_idx ON context_archive_candidate USING GIN (reasons);

-- Registry of scripts/docs that still read catalog YAML directly. Some readers
-- are intentional seed/export tooling; others are operational migration
-- candidates that should move to database row sources. Tracking these as rows
-- prevents YAML-reader drift from living only in prose audit output.
CREATE TABLE IF NOT EXISTS catalog_reader_migration_candidate (
  reader_candidate_id TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  source_path         TEXT NOT NULL,
  source_kind         TEXT NOT NULL CHECK (source_kind IN ('script','doc','other')),
  classification      TEXT NOT NULL CHECK (classification IN (
    'seed_export_validation',
    'seed_export_bridge',
    'migration_infrastructure',
    'row_backed_consumer',
    'operational_migration_candidate',
    'draft_generation',
    'data_jsonl_utility',
    'documentation_or_example',
    'unknown_yaml_reader'
  )),
  migration_status    TEXT NOT NULL CHECK (migration_status IN ('not_required','row_backed','candidate','review','planned','done')),
  priority            INTEGER NOT NULL CHECK (priority >= 0),
  recommended_action  TEXT NOT NULL CHECK (recommended_action IN ('keep_seed_export','keep_row_backed_fallback','migrate_to_catalog_row_source','classify_reader','review')),
  matches             JSONB NOT NULL DEFAULT '{}'::jsonb,
  samples             JSONB NOT NULL DEFAULT '[]'::jsonb,
  note                TEXT,
  owner_team          TEXT,
  detected_by         TEXT NOT NULL,
  body                JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source_path)
);
CREATE INDEX IF NOT EXISTS catalog_reader_migration_candidate_class_idx ON catalog_reader_migration_candidate (tenant_id, classification, migration_status);
CREATE INDEX IF NOT EXISTS catalog_reader_migration_candidate_priority_idx ON catalog_reader_migration_candidate (tenant_id, priority DESC);
CREATE INDEX IF NOT EXISTS catalog_reader_migration_candidate_matches_gin_idx ON catalog_reader_migration_candidate USING GIN (matches);

-- Query-friendly expansion of rubric manifest dimensions. The full manifest
-- remains in component.body, but these rows let the hosted product filter,
-- score, compare, and report rubric dimensions without reparsing YAML/JSON.
CREATE TABLE IF NOT EXISTS rubric_dimension (
  rubric_dimension_id TEXT PRIMARY KEY,
  rubric_id           TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  dimension_path      TEXT NOT NULL,
  parent_path         TEXT,
  dimension_level     INTEGER,
  label               TEXT NOT NULL,
  weight              NUMERIC NOT NULL,
  scale               TEXT NOT NULL,
  evidence_required   TEXT,
  gate                BOOLEAN NOT NULL DEFAULT FALSE,
  body                JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ DEFAULT now(),
  updated_at          TIMESTAMPTZ DEFAULT now(),
  UNIQUE (rubric_id, dimension_path)
);
CREATE INDEX IF NOT EXISTS rubric_dimension_rubric_idx ON rubric_dimension (rubric_id, dimension_path);
CREATE INDEX IF NOT EXISTS rubric_dimension_parent_idx ON rubric_dimension (rubric_id, parent_path);
CREATE INDEX IF NOT EXISTS rubric_dimension_gate_idx ON rubric_dimension (rubric_id, gate) WHERE gate;
CREATE INDEX IF NOT EXISTS rubric_dimension_body_gin_idx ON rubric_dimension USING GIN (body);

CREATE TABLE IF NOT EXISTS rubric_evaluation (
  rubric_evaluation_id TEXT PRIMARY KEY,
  rubric_id            TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  subject_id           TEXT NOT NULL,
  subject_type         TEXT NOT NULL,
  evaluator_type       TEXT CHECK (evaluator_type IS NULL OR evaluator_type IN ('human','model','deterministic','ensemble','system')),
  evaluator_ref        TEXT,
  score                NUMERIC,
  max_score            NUMERIC NOT NULL DEFAULT 1,
  gate_status          TEXT CHECK (gate_status IS NULL OR gate_status IN ('pass','warn','fail','not_applicable')),
  evidence_packet      JSONB NOT NULL DEFAULT '{}'::jsonb,
  trace_id             TEXT,
  created_at           TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS rubric_evaluation_rubric_idx ON rubric_evaluation (rubric_id, created_at DESC);
CREATE INDEX IF NOT EXISTS rubric_evaluation_subject_idx ON rubric_evaluation (subject_id, subject_type, created_at DESC);

CREATE TABLE IF NOT EXISTS rubric_dimension_score (
  rubric_dimension_score_id TEXT PRIMARY KEY,
  rubric_evaluation_id      TEXT NOT NULL REFERENCES rubric_evaluation(rubric_evaluation_id) ON DELETE CASCADE,
  rubric_dimension_id       TEXT NOT NULL REFERENCES rubric_dimension(rubric_dimension_id) ON DELETE CASCADE,
  score                     NUMERIC NOT NULL,
  max_score                 NUMERIC NOT NULL DEFAULT 1,
  normalized_score          DOUBLE PRECISION CHECK (normalized_score IS NULL OR (normalized_score >= 0 AND normalized_score <= 1)),
  gate_status               TEXT CHECK (gate_status IS NULL OR gate_status IN ('pass','warn','fail','not_applicable')),
  evidence                  JSONB NOT NULL DEFAULT '[]'::jsonb,
  rationale                 TEXT,
  created_at                TIMESTAMPTZ DEFAULT now(),
  UNIQUE (rubric_evaluation_id, rubric_dimension_id)
);
CREATE INDEX IF NOT EXISTS rubric_dimension_score_eval_idx ON rubric_dimension_score (rubric_evaluation_id);
CREATE INDEX IF NOT EXISTS rubric_dimension_score_dimension_idx ON rubric_dimension_score (rubric_dimension_id, normalized_score);

-- One row per (component, industry) — supports filter by industry.
CREATE TABLE IF NOT EXISTS component_industry (
  component_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  industry    TEXT NOT NULL,
  PRIMARY KEY (component_id, industry)
);
CREATE INDEX IF NOT EXISTS component_industry_industry_idx ON component_industry (industry);

CREATE TABLE IF NOT EXISTS component_capability (
  component_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  capability  TEXT NOT NULL,
  PRIMARY KEY (component_id, capability)
);
CREATE INDEX IF NOT EXISTS component_capability_capability_idx ON component_capability (capability);

CREATE TABLE IF NOT EXISTS component_modality (
  component_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  modality    TEXT NOT NULL,
  PRIMARY KEY (component_id, modality)
);

CREATE TABLE IF NOT EXISTS component_tag (
  component_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  tag         TEXT NOT NULL,
  PRIMARY KEY (component_id, tag)
);

-- Inter-component edges — consumes / emits / step_ref / contributes_to / etc.
CREATE TABLE IF NOT EXISTS component_ref (
  src_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  dst_id TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  role   TEXT NOT NULL,
  PRIMARY KEY (src_id, dst_id, role)
);
CREATE INDEX IF NOT EXISTS component_ref_dst_idx ON component_ref (dst_id, role);

-- Rule leaves (inside rule packs). One row per rule.
CREATE TABLE IF NOT EXISTS rule (
  rule_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  family     TEXT NOT NULL
                  CHECK (family IN ('grep','glob','classifier','heuristic','rag','citation','online_search','privacy','schema','routing')),
  severity   TEXT,
  category   TEXT,
  pattern    TEXT,
  body       JSONB NOT NULL,
  enabled    BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS rule_pack_idx ON rule (pack_id);
CREATE INDEX IF NOT EXISTS rule_family_idx ON rule (family);
CREATE INDEX IF NOT EXISTS rule_category_idx ON rule (category);
CREATE INDEX IF NOT EXISTS rule_severity_idx ON rule (severity);

-- Knowledge leaves (inside knowledge / logic packs). One row per leaf.
CREATE TABLE IF NOT EXISTS knowledge_leaf (
  leaf_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  leaf_type  TEXT NOT NULL,
  industry   TEXT,
  language   TEXT,
  body       JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_leaf_pack_idx     ON knowledge_leaf (pack_id);
CREATE INDEX IF NOT EXISTS knowledge_leaf_type_idx     ON knowledge_leaf (leaf_type);
CREATE INDEX IF NOT EXISTS knowledge_leaf_industry_idx ON knowledge_leaf (industry);

-- Source records and high-volume normalized objects. These support object
-- factories without requiring every extracted atom to become a manifest.
CREATE TABLE IF NOT EXISTS source_record (
  source_record_id TEXT PRIMARY KEY,
  source_url       TEXT,
  archive_url      TEXT,
  publisher        TEXT,
  license          TEXT,
  trust_tier       TEXT,
  privacy_boundary TEXT,
  freshness        TEXT,
  retrieved_at     TIMESTAMPTZ,
  effective_date   DATE,
  content_hash     TEXT,
  body             JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS source_record_hash_idx ON source_record (content_hash);
CREATE INDEX IF NOT EXISTS source_record_publisher_idx ON source_record (publisher);

-- Immutable change records for component definition CDC. The hash fields make
-- version identity reproducible across exports, imports, and signed publishers.
CREATE TABLE IF NOT EXISTS component_change_event (
  change_event_id               TEXT PRIMARY KEY,
  component_id                  TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  previous_component_version_id TEXT REFERENCES component_version(component_version_id) ON DELETE SET NULL,
  new_component_version_id      TEXT REFERENCES component_version(component_version_id) ON DELETE SET NULL,
  change_type                   TEXT NOT NULL CHECK (change_type IN (
    'created','updated','superseded','deprecated','reactivated','source_refreshed',
    'approval_changed','hash_recomputed','publisher_signed'
  )),
  previous_definition_hash      TEXT,
  new_definition_hash           TEXT,
  previous_content_hash         TEXT,
  new_content_hash              TEXT,
  changed_fields                JSONB DEFAULT '[]'::jsonb,
  source_record_id              TEXT REFERENCES source_record(source_record_id) ON DELETE SET NULL,
  actor_type                    TEXT CHECK (actor_type IS NULL OR actor_type IN ('system','publisher','curator','tenant','worker','import')),
  actor_ref                     TEXT,
  signature_ref                 TEXT,
  event_body                    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at                    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS component_change_event_component_idx ON component_change_event (component_id, created_at);
CREATE INDEX IF NOT EXISTS component_change_event_new_hash_idx ON component_change_event (new_definition_hash);

CREATE TABLE IF NOT EXISTS subcomponent (
  subcomponent_id   TEXT PRIMARY KEY,
  component_id      TEXT REFERENCES component(id) ON DELETE CASCADE,
  parent_object_id  TEXT,
  subcomponent_type TEXT NOT NULL CHECK (subcomponent_type IN (
    'fact','rule','check','question','criterion','prompt_fragment','tool_call',
    'schema_field','cost_dimension','label','dimension','entity_ref','index_record',
    'embedding_work_item','review_route','deployment_step','source_span'
  )),
  name              TEXT,
  body              JSONB NOT NULL,
  source_record_id  TEXT REFERENCES source_record(source_record_id) ON DELETE SET NULL,
  trust_tier        TEXT,
  privacy_boundary  TEXT,
  freshness         TEXT,
  content_hash      TEXT,
  review_status     TEXT,
  created_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS subcomponent_component_idx ON subcomponent (component_id);
CREATE INDEX IF NOT EXISTS subcomponent_parent_idx ON subcomponent (parent_object_id);
CREATE INDEX IF NOT EXISTS subcomponent_type_idx ON subcomponent (subcomponent_type);
CREATE INDEX IF NOT EXISTS subcomponent_body_gin_idx ON subcomponent USING GIN (body);

CREATE TABLE IF NOT EXISTS normalized_object (
  object_id        TEXT PRIMARY KEY,
  object_type      TEXT NOT NULL,
  source_record_id TEXT REFERENCES source_record(source_record_id) ON DELETE SET NULL,
  title            TEXT NOT NULL,
  body             JSONB NOT NULL,
  trust_tier       TEXT,
  privacy_boundary TEXT,
  quality_status   TEXT,
  review_status    TEXT,
  content_hash     TEXT,
  dedupe_cluster_id TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS normalized_object_type_idx ON normalized_object (object_type);
CREATE INDEX IF NOT EXISTS normalized_object_cluster_idx ON normalized_object (dedupe_cluster_id);
CREATE INDEX IF NOT EXISTS normalized_object_body_gin_idx ON normalized_object USING GIN (body);

CREATE TABLE IF NOT EXISTS component_candidate (
  component_candidate_id TEXT PRIMARY KEY,
  source_object_id       TEXT REFERENCES normalized_object(object_id) ON DELETE SET NULL,
  component_type         TEXT NOT NULL,
  component_layer        TEXT CHECK (component_layer IS NULL OR component_layer IN ('pre_llm','llm','post_llm','control_flow','data','evaluation','deployment','governance')),
  control_flow_kind      TEXT CHECK (control_flow_kind IS NULL OR control_flow_kind IN ('loop','iterate','map','reduce','branch','retry','parallel','human_review','cache_lookup','fallback','stop')),
  name                   TEXT NOT NULL,
  trust_tier             TEXT,
  privacy_boundary       TEXT,
  review_status          TEXT,
  quality_status         TEXT,
  content_hash           TEXT,
  promotion_state        TEXT NOT NULL CHECK (promotion_state IN ('candidate','review','promoted','held','rejected')),
  body                   JSONB NOT NULL,
  created_at             TIMESTAMPTZ DEFAULT now(),
  promoted_component_id  TEXT REFERENCES component(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS component_candidate_source_idx ON component_candidate (source_object_id);
CREATE INDEX IF NOT EXISTS component_candidate_type_idx ON component_candidate (component_type);
CREATE INDEX IF NOT EXISTS component_candidate_layer_idx ON component_candidate (component_layer);
CREATE INDEX IF NOT EXISTS component_candidate_control_flow_idx ON component_candidate (control_flow_kind) WHERE control_flow_kind IS NOT NULL;
CREATE INDEX IF NOT EXISTS component_candidate_review_idx ON component_candidate (promotion_state, review_status);
CREATE INDEX IF NOT EXISTS component_candidate_body_gin_idx ON component_candidate USING GIN (body);

CREATE TABLE IF NOT EXISTS component_pipeline_template (
  template_id       TEXT PRIMARY KEY,
  name              TEXT NOT NULL,
  task_family       TEXT NOT NULL,
  cost_profile      TEXT CHECK (cost_profile IS NULL OR cost_profile IN ('cheap','balanced','quality','local_first')),
  modality          TEXT[] DEFAULT '{}',
  industry          TEXT[] DEFAULT '{}',
  body              JSONB NOT NULL,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS component_pipeline_template_family_idx ON component_pipeline_template (task_family);
CREATE INDEX IF NOT EXISTS component_pipeline_template_body_gin_idx ON component_pipeline_template USING GIN (body);

CREATE TABLE IF NOT EXISTS component_pipeline_template_step (
  template_step_id  TEXT PRIMARY KEY,
  template_id       TEXT NOT NULL REFERENCES component_pipeline_template(template_id) ON DELETE CASCADE,
  step_order        INTEGER NOT NULL,
  component_id      TEXT REFERENCES component(id) ON DELETE SET NULL,
  component_candidate_id TEXT REFERENCES component_candidate(component_candidate_id) ON DELETE SET NULL,
  component_layer   TEXT NOT NULL CHECK (component_layer IN ('pre_llm','llm','post_llm','control_flow','data','evaluation','deployment','governance')),
  control_flow_kind TEXT CHECK (control_flow_kind IS NULL OR control_flow_kind IN ('loop','iterate','map','reduce','branch','retry','parallel','human_review','cache_lookup','fallback','stop')),
  required          BOOLEAN NOT NULL DEFAULT TRUE,
  inputs            JSONB,
  outputs           JSONB,
  body              JSONB NOT NULL,
  UNIQUE (template_id, step_order)
);
CREATE INDEX IF NOT EXISTS component_pipeline_template_step_template_idx ON component_pipeline_template_step (template_id, step_order);
CREATE INDEX IF NOT EXISTS component_pipeline_template_step_layer_idx ON component_pipeline_template_step (component_layer);

CREATE TABLE IF NOT EXISTS subcomponent_candidate (
  subcomponent_candidate_id TEXT PRIMARY KEY,
  component_candidate_id    TEXT REFERENCES component_candidate(component_candidate_id) ON DELETE SET NULL,
  parent_object_id          TEXT,
  subcomponent_type         TEXT NOT NULL,
  name                      TEXT,
  review_status             TEXT,
  content_hash              TEXT,
  body                      JSONB NOT NULL,
  created_at                TIMESTAMPTZ DEFAULT now(),
  promoted_subcomponent_id  TEXT REFERENCES subcomponent(subcomponent_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS subcomponent_candidate_component_idx ON subcomponent_candidate (component_candidate_id);
CREATE INDEX IF NOT EXISTS subcomponent_candidate_parent_idx ON subcomponent_candidate (parent_object_id);
CREATE INDEX IF NOT EXISTS subcomponent_candidate_type_idx ON subcomponent_candidate (subcomponent_type);
CREATE INDEX IF NOT EXISTS subcomponent_candidate_body_gin_idx ON subcomponent_candidate USING GIN (body);

CREATE TABLE IF NOT EXISTS source_component_link (
  source_record_id TEXT REFERENCES source_record(source_record_id) ON DELETE CASCADE,
  component_candidate_id TEXT REFERENCES component_candidate(component_candidate_id) ON DELETE CASCADE,
  publisher        TEXT,
  license          TEXT,
  trust_tier       TEXT,
  privacy_boundary TEXT,
  content_hash     TEXT,
  created_at       TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (source_record_id, component_candidate_id)
);
CREATE INDEX IF NOT EXISTS source_component_link_candidate_idx ON source_component_link (component_candidate_id);

-- Canonical embedding table for generated and curated objects. The vector
-- dimension defaults to 384 for the local MiniLM baseline; larger hosted
-- embeddings can be stored in parallel rows by embedding_model. The default is
-- exported by scripts.db.vector_config_registry and should seed/check
-- setting_profile rows instead of being copied into new SQL by hand.
CREATE TABLE IF NOT EXISTS object_embedding (
  embedding_id     TEXT PRIMARY KEY,
  subject_id       TEXT NOT NULL,
  subject_type     TEXT NOT NULL,
  embedding_model  TEXT NOT NULL,
  text_hash        TEXT NOT NULL,
  text             TEXT NOT NULL,
  embedding        vector(384),   -- single source: scripts._config.DEFAULT_EMBEDDING_DIMENSIONS (drift-guarded by scripts/validate.py)
  metadata         JSONB,
  created_at       TIMESTAMPTZ DEFAULT now(),
  UNIQUE (subject_id, subject_type, embedding_model, text_hash)
);
CREATE INDEX IF NOT EXISTS object_embedding_subject_idx ON object_embedding (subject_id, subject_type);
CREATE INDEX IF NOT EXISTS object_embedding_model_idx ON object_embedding (embedding_model);
-- Create an ANN index after embeddings are populated in production, e.g.:
-- CREATE INDEX object_embedding_hnsw_idx ON object_embedding USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS canonical_entity (
  entity_id      TEXT PRIMARY KEY,
  entity_type    TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  aliases        JSONB,
  identifiers    JSONB,
  description    TEXT,
  confidence     NUMERIC,
  review_status  TEXT
);
CREATE INDEX IF NOT EXISTS canonical_entity_type_idx ON canonical_entity (entity_type);
CREATE INDEX IF NOT EXISTS canonical_entity_name_idx ON canonical_entity (canonical_name);

CREATE TABLE IF NOT EXISTS object_entity_ref (
  object_id TEXT NOT NULL REFERENCES normalized_object(object_id) ON DELETE CASCADE,
  entity_id TEXT NOT NULL REFERENCES canonical_entity(entity_id) ON DELETE CASCADE,
  role      TEXT NOT NULL,
  confidence NUMERIC,
  PRIMARY KEY (object_id, entity_id, role)
);

CREATE TABLE IF NOT EXISTS dedupe_cluster (
  dedupe_cluster_id TEXT PRIMARY KEY,
  canonical_object_id TEXT REFERENCES normalized_object(object_id),
  method          TEXT,
  threshold       JSONB,
  status          TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dedupe_resolution (
  resolution_id       TEXT PRIMARY KEY,
  dedupe_cluster_id   TEXT REFERENCES dedupe_cluster(dedupe_cluster_id) ON DELETE CASCADE,
  canonical_object_id TEXT REFERENCES normalized_object(object_id) ON DELETE SET NULL,
  member_ids          JSONB NOT NULL,
  resolution_action   TEXT NOT NULL CHECK (resolution_action IN (
    'mark_singleton_resolved',
    'merge_exact_duplicates',
    'route_to_curator',
    'reject_cluster',
    'hold_for_more_evidence'
  )),
  review_status       TEXT NOT NULL,
  confidence          NUMERIC,
  reason              TEXT NOT NULL,
  evidence            JSONB NOT NULL,
  created_at          TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS dedupe_resolution_cluster_idx ON dedupe_resolution (dedupe_cluster_id);
CREATE INDEX IF NOT EXISTS dedupe_resolution_action_idx ON dedupe_resolution (resolution_action, review_status);

CREATE TABLE IF NOT EXISTS review_ticket (
  review_ticket_id TEXT PRIMARY KEY,
  object_id        TEXT REFERENCES normalized_object(object_id) ON DELETE SET NULL,
  source_record_id TEXT REFERENCES source_record(source_record_id) ON DELETE SET NULL,
  review_type      TEXT NOT NULL,
  reason           TEXT NOT NULL,
  status           TEXT NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS promotion_decision (
  decision_id         TEXT PRIMARY KEY,
  object_id           TEXT REFERENCES normalized_object(object_id) ON DELETE SET NULL,
  source_record_id    TEXT REFERENCES source_record(source_record_id) ON DELETE SET NULL,
  score               NUMERIC NOT NULL,
  max_score           NUMERIC NOT NULL DEFAULT 100,
  decision            TEXT NOT NULL CHECK (decision IN ('promote_candidate','review_before_promotion','hold','reject')),
  criteria            JSONB NOT NULL,
  risk_flags          JSONB,
  review_reasons      JSONB,
  recommended_outputs JSONB,
  created_at          TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS promotion_decision_object_idx ON promotion_decision (object_id);
CREATE INDEX IF NOT EXISTS promotion_decision_decision_idx ON promotion_decision (decision, score DESC);
CREATE INDEX IF NOT EXISTS promotion_decision_criteria_gin_idx ON promotion_decision USING GIN (criteria);

CREATE TABLE IF NOT EXISTS content_approval_decision (
  approval_id          TEXT PRIMARY KEY,
  object_id            TEXT REFERENCES normalized_object(object_id) ON DELETE SET NULL,
  component_candidate_id TEXT REFERENCES component_candidate(component_candidate_id) ON DELETE SET NULL,
  dedupe_resolution_id TEXT REFERENCES dedupe_resolution(resolution_id) ON DELETE SET NULL,
  decision             TEXT NOT NULL CHECK (decision IN ('approve_for_promotion','review_before_promotion','hold','reject')),
  confidence           NUMERIC,
  criteria             JSONB NOT NULL,
  risk_flags           JSONB,
  review_reasons       JSONB,
  promotion_decision_id TEXT REFERENCES promotion_decision(decision_id) ON DELETE SET NULL,
  created_at           TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS content_approval_object_idx ON content_approval_decision (object_id);
CREATE INDEX IF NOT EXISTS content_approval_candidate_idx ON content_approval_decision (component_candidate_id);
CREATE INDEX IF NOT EXISTS content_approval_decision_idx ON content_approval_decision (decision, confidence DESC);

-- Search/index records are canonical rows in Postgres first. Derived search
-- backends, pgvector rows, or external vector stores consume from here.
CREATE TABLE IF NOT EXISTS index_record (
  index_record_id TEXT PRIMARY KEY,
  index_kind      TEXT NOT NULL CHECK (index_kind IN ('keyword','vector','graph','facet','freshness','quality','cost')),
  subject_id      TEXT NOT NULL,
  subject_type    TEXT,
  text            TEXT NOT NULL,
  metadata        JSONB,
  embedding_model TEXT,
  embedding_ref   TEXT,
  graph_edges     JSONB,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS index_record_subject_idx ON index_record (subject_id, subject_type);
CREATE INDEX IF NOT EXISTS index_record_kind_idx ON index_record (index_kind);
CREATE INDEX IF NOT EXISTS index_record_metadata_gin_idx ON index_record USING GIN (metadata);
CREATE INDEX IF NOT EXISTS index_record_text_fts_idx ON index_record USING GIN (to_tsvector('english', text));

CREATE TABLE IF NOT EXISTS partition_manifest (
  partition_id      TEXT PRIMARY KEY,
  partition_kind    TEXT NOT NULL,
  run_id            TEXT NOT NULL,
  source_surface_id TEXT,
  tenant_id         TEXT,
  object_count      INTEGER NOT NULL DEFAULT 0,
  shard_paths       JSONB NOT NULL,
  index_delta_paths JSONB,
  schema_versions   JSONB,
  content_hash      TEXT NOT NULL,
  trust_boundary    TEXT,
  privacy_summary   JSONB,
  quality_summary   JSONB,
  created           TIMESTAMPTZ NOT NULL,
  updated           TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS partition_manifest_kind_idx ON partition_manifest (partition_kind);
CREATE INDEX IF NOT EXISTS partition_manifest_run_idx ON partition_manifest (run_id);

CREATE TABLE IF NOT EXISTS index_delta (
  delta_id       TEXT PRIMARY KEY,
  partition_id   TEXT NOT NULL REFERENCES partition_manifest(partition_id) ON DELETE CASCADE,
  run_id         TEXT,
  operation      TEXT NOT NULL CHECK (operation IN ('upsert','delete','tombstone')),
  index_record_id TEXT,
  index_record   JSONB NOT NULL,
  sequence       INTEGER,
  created        TIMESTAMPTZ,
  content_hash   TEXT,
  replay_policy  JSONB,
  applied_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS index_delta_partition_idx ON index_delta (partition_id, sequence);
CREATE INDEX IF NOT EXISTS index_delta_record_idx ON index_delta (index_record_id);

CREATE TABLE IF NOT EXISTS label_assignment (
  label_id          TEXT PRIMARY KEY,
  label_set         TEXT NOT NULL,
  label             TEXT NOT NULL,
  path              TEXT,
  subject_id        TEXT NOT NULL,
  subject_type      TEXT,
  confidence        NUMERIC,
  assigned_by       TEXT,
  assignment_method TEXT,
  model_route_id    TEXT,
  provenance        JSONB,
  review_status     TEXT
);
CREATE INDEX IF NOT EXISTS label_assignment_subject_idx ON label_assignment (subject_id);
CREATE INDEX IF NOT EXISTS label_assignment_label_idx ON label_assignment (label_set, label);
CREATE INDEX IF NOT EXISTS label_assignment_path_idx ON label_assignment (path);

CREATE TABLE IF NOT EXISTS dimension_value (
  dimension_id      TEXT PRIMARY KEY,
  name              TEXT NOT NULL,
  subject_id        TEXT NOT NULL,
  subject_type      TEXT,
  value             JSONB NOT NULL,
  value_type        TEXT,
  scale             TEXT,
  confidence        NUMERIC,
  assigned_by       TEXT,
  assignment_method TEXT,
  model_route_id    TEXT,
  provenance        JSONB,
  review_status     TEXT
);
CREATE INDEX IF NOT EXISTS dimension_value_subject_idx ON dimension_value (subject_id);
CREATE INDEX IF NOT EXISTS dimension_value_name_idx ON dimension_value (name);

-- Context Object Fabric persistence. These tables back the Baltor context
-- object graph export contract without forcing every source or industry into
-- one rigid relational shape. Stable identifiers and promoted fields are
-- indexed; source-specific and long-tail attributes remain in JSONB facets.
CREATE TABLE IF NOT EXISTS context_object (
  context_object_id TEXT PRIMARY KEY,
  tenant_id         TEXT NOT NULL,
  object_type       TEXT NOT NULL,
  subkind           TEXT,
  title             TEXT,
  summary           TEXT,
  source_system     TEXT,
  native_id         TEXT,
  source_url        TEXT,
  current_version_id TEXT,
  acl_id            TEXT,
  classification    TEXT,
  source_handles    JSONB NOT NULL DEFAULT '[]'::jsonb,
  facets            JSONB NOT NULL DEFAULT '{}'::jsonb,
  five_w_one_h      JSONB NOT NULL DEFAULT '{}'::jsonb,
  dimension_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  document          JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_object_tenant_type_idx ON context_object (tenant_id, object_type);
CREATE INDEX IF NOT EXISTS context_object_source_idx ON context_object (source_system, native_id);
CREATE INDEX IF NOT EXISTS context_object_acl_idx ON context_object (tenant_id, acl_id, classification);
CREATE INDEX IF NOT EXISTS context_object_updated_idx ON context_object (updated_at DESC);
CREATE INDEX IF NOT EXISTS context_object_facets_gin_idx ON context_object USING GIN (facets);
CREATE INDEX IF NOT EXISTS context_object_5w1h_gin_idx ON context_object USING GIN (five_w_one_h);
CREATE INDEX IF NOT EXISTS context_object_document_gin_idx ON context_object USING GIN (document);

-- Governance package for every meaningful business/database object type. This
-- records the required rubric, contract, schemas, layouts, diagrams, context
-- rules, lifecycle, ownership, and database/storage mappings for object types
-- such as account, billing account, invoice, context object, flow, connection,
-- process, data source, integration, workspace, tenant, user, policy, and run.
CREATE TABLE IF NOT EXISTS object_governance_profile (
  object_governance_profile_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  object_type      TEXT NOT NULL,
  object_family    TEXT NOT NULL CHECK (object_family IN (
    'account_management',
    'billing',
    'context',
    'flow',
    'connection',
    'process',
    'identity',
    'policy',
    'catalog',
    'database',
    'integration',
    'analytics',
    'security',
    'support',
    'custom'
  )),
  display_name     TEXT NOT NULL,
  description      TEXT NOT NULL,
  owner_team       TEXT,
  steward          TEXT,
  lifecycle        JSONB NOT NULL DEFAULT '{}'::jsonb,
  required_rubrics JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_contracts JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_schemas JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_layouts JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_diagrams JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_context_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_relationships JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_events  JSONB NOT NULL DEFAULT '[]'::jsonb,
  database_mapping JSONB NOT NULL DEFAULT '{}'::jsonb,
  cloud_mapping    JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy           JSONB NOT NULL DEFAULT '{}'::jsonb,
  body             JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type)
);
CREATE INDEX IF NOT EXISTS object_governance_profile_family_idx ON object_governance_profile (tenant_id, object_family);
CREATE INDEX IF NOT EXISTS object_governance_profile_rubrics_gin_idx ON object_governance_profile USING GIN (required_rubrics);
CREATE INDEX IF NOT EXISTS object_governance_profile_rules_gin_idx ON object_governance_profile USING GIN (required_context_rules);
CREATE INDEX IF NOT EXISTS object_governance_profile_body_gin_idx ON object_governance_profile USING GIN (body);

CREATE TABLE IF NOT EXISTS object_contract (
  object_contract_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  object_type        TEXT NOT NULL,
  contract_kind      TEXT NOT NULL CHECK (contract_kind IN (
    'api',
    'database',
    'event',
    'ui',
    'context',
    'policy',
    'billing',
    'security',
    'integration',
    'analytics',
    'custom'
  )),
  name               TEXT NOT NULL,
  version            TEXT NOT NULL,
  applies_to_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
  inputs             JSONB NOT NULL DEFAULT '{}'::jsonb,
  outputs            JSONB NOT NULL DEFAULT '{}'::jsonb,
  invariants         JSONB NOT NULL DEFAULT '[]'::jsonb,
  failure_modes      JSONB NOT NULL DEFAULT '[]'::jsonb,
  compatibility      JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy             JSONB NOT NULL DEFAULT '{}'::jsonb,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type, contract_kind, name, version)
);
CREATE INDEX IF NOT EXISTS object_contract_type_idx ON object_contract (tenant_id, object_type, contract_kind);
CREATE INDEX IF NOT EXISTS object_contract_actions_gin_idx ON object_contract USING GIN (applies_to_actions);
CREATE INDEX IF NOT EXISTS object_contract_body_gin_idx ON object_contract USING GIN (body);

CREATE TABLE IF NOT EXISTS object_schema_profile (
  object_schema_profile_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  object_type        TEXT NOT NULL,
  schema_kind        TEXT NOT NULL CHECK (schema_kind IN (
    'document',
    'long_attribute',
    'wide_columnar',
    'relational',
    'graph',
    'event',
    'vector_metadata',
    'ui_view',
    'api_payload',
    'export'
  )),
  schema_ref         TEXT,
  version            TEXT NOT NULL,
  required_fields    JSONB NOT NULL DEFAULT '[]'::jsonb,
  optional_fields    JSONB NOT NULL DEFAULT '[]'::jsonb,
  promoted_indexes   JSONB NOT NULL DEFAULT '[]'::jsonb,
  validation         JSONB NOT NULL DEFAULT '{}'::jsonb,
  evolution_policy   JSONB NOT NULL DEFAULT '{}'::jsonb,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type, schema_kind, version)
);
CREATE INDEX IF NOT EXISTS object_schema_profile_type_idx ON object_schema_profile (tenant_id, object_type, schema_kind);
CREATE INDEX IF NOT EXISTS object_schema_profile_indexes_gin_idx ON object_schema_profile USING GIN (promoted_indexes);
CREATE INDEX IF NOT EXISTS object_schema_profile_body_gin_idx ON object_schema_profile USING GIN (body);

CREATE TABLE IF NOT EXISTS object_layout_profile (
  object_layout_profile_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  object_type        TEXT NOT NULL,
  layout_kind        TEXT NOT NULL CHECK (layout_kind IN (
    'admin_detail',
    'developer_detail',
    'customer_detail',
    'list',
    'graph',
    'timeline',
    'audit',
    'billing',
    'support',
    'mobile',
    'export'
  )),
  version            TEXT NOT NULL,
  audience           TEXT,
  sections           JSONB NOT NULL DEFAULT '[]'::jsonb,
  actions            JSONB NOT NULL DEFAULT '[]'::jsonb,
  masks              JSONB NOT NULL DEFAULT '[]'::jsonb,
  accessibility      JSONB NOT NULL DEFAULT '{}'::jsonb,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type, layout_kind, version)
);
CREATE INDEX IF NOT EXISTS object_layout_profile_type_idx ON object_layout_profile (tenant_id, object_type, layout_kind);
CREATE INDEX IF NOT EXISTS object_layout_profile_sections_gin_idx ON object_layout_profile USING GIN (sections);

CREATE TABLE IF NOT EXISTS object_architecture_diagram (
  object_architecture_diagram_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  object_type        TEXT NOT NULL,
  diagram_kind       TEXT NOT NULL CHECK (diagram_kind IN (
    'lifecycle',
    'relationship',
    'data_flow',
    'state_machine',
    'storage_mapping',
    'security_boundary',
    'billing_flow',
    'integration',
    'deployment',
    'custom'
  )),
  title              TEXT NOT NULL,
  version            TEXT NOT NULL,
  diagram_format     TEXT NOT NULL CHECK (diagram_format IN ('mermaid','plantuml','graphviz','svg','png','markdown','json','external')),
  diagram_text       TEXT,
  diagram_uri        TEXT,
  related_objects    JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_handles     JSONB NOT NULL DEFAULT '[]'::jsonb,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type, diagram_kind, version)
);
CREATE INDEX IF NOT EXISTS object_architecture_diagram_type_idx ON object_architecture_diagram (tenant_id, object_type, diagram_kind);
CREATE INDEX IF NOT EXISTS object_architecture_diagram_related_gin_idx ON object_architecture_diagram USING GIN (related_objects);

CREATE TABLE IF NOT EXISTS object_context_rule (
  object_context_rule_id TEXT PRIMARY KEY,
  tenant_id          TEXT NOT NULL,
  object_type        TEXT NOT NULL,
  rule_kind          TEXT NOT NULL CHECK (rule_kind IN (
    'required_context',
    'forbidden_context',
    'freshness',
    'source_precedence',
    'masking',
    'retrieval',
    'expansion',
    'lineage',
    'dimension',
    'relationship',
    'event',
    'retention',
    'billing',
    'custom'
  )),
  name               TEXT NOT NULL,
  severity           TEXT CHECK (severity IS NULL OR severity IN ('info','warning','error','blocker')),
  applies_to_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
  condition          JSONB NOT NULL DEFAULT '{}'::jsonb,
  requirement        JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence_required  TEXT,
  body               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, object_type, rule_kind, name)
);
CREATE INDEX IF NOT EXISTS object_context_rule_type_idx ON object_context_rule (tenant_id, object_type, rule_kind);
CREATE INDEX IF NOT EXISTS object_context_rule_actions_gin_idx ON object_context_rule USING GIN (applies_to_actions);
CREATE INDEX IF NOT EXISTS object_context_rule_condition_gin_idx ON object_context_rule USING GIN (condition);

-- Bridge catalog components to context objects. This is the practical path for
-- treating rubrics, tools, masks, transformers, schemas, processors, prompts,
-- adapters, and pipelines as first-class context objects while keeping the
-- catalog component contract intact.
CREATE TABLE IF NOT EXISTS component_context_object (
  component_id      TEXT NOT NULL REFERENCES component(id) ON DELETE CASCADE,
  context_object_id TEXT NOT NULL REFERENCES context_object(context_object_id) ON DELETE CASCADE,
  role              TEXT NOT NULL CHECK (role IN (
    'is_context_object',
    'describes',
    'evaluates',
    'masks',
    'transforms',
    'calls',
    'routes',
    'indexes',
    'packs',
    'governs',
    'implements',
    'has_rubric_dimension_context'
  )),
  binding_status    TEXT NOT NULL DEFAULT 'active' CHECK (binding_status IN ('draft','active','deprecated','superseded')),
  source_ref        TEXT,
  binding_hash      TEXT,
  body              JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (component_id, context_object_id, role)
);
CREATE INDEX IF NOT EXISTS component_context_object_component_idx ON component_context_object (component_id, role);
CREATE INDEX IF NOT EXISTS component_context_object_object_idx ON component_context_object (context_object_id, role);
CREATE INDEX IF NOT EXISTS component_context_object_body_gin_idx ON component_context_object USING GIN (body);

-- Masks are represented as context objects plus a query-friendly contract row.
-- A mask can redact, project, filter, summarize, suppress, transform, or route
-- fields based on policy, user, source, destination, model, purpose, or task.
CREATE TABLE IF NOT EXISTS context_mask_contract (
  mask_contract_id TEXT PRIMARY KEY,
  context_object_id TEXT NOT NULL REFERENCES context_object(context_object_id) ON DELETE CASCADE,
  component_id      TEXT REFERENCES component(id) ON DELETE SET NULL,
  mask_kind         TEXT NOT NULL CHECK (mask_kind IN (
    'redaction',
    'projection',
    'field_selection',
    'permission_view',
    'retention_view',
    'model_destination_view',
    'local_sync_view',
    'export_view',
    'summary_view'
  )),
  target_types      JSONB NOT NULL DEFAULT '[]'::jsonb,
  include_paths     JSONB NOT NULL DEFAULT '[]'::jsonb,
  exclude_paths     JSONB NOT NULL DEFAULT '[]'::jsonb,
  redact_paths      JSONB NOT NULL DEFAULT '[]'::jsonb,
  policy_trigger    JSONB NOT NULL DEFAULT '{}'::jsonb,
  redaction_reason  TEXT,
  reversible        BOOLEAN NOT NULL DEFAULT FALSE,
  contract          JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_mask_contract_object_idx ON context_mask_contract (context_object_id);
CREATE INDEX IF NOT EXISTS context_mask_contract_component_idx ON context_mask_contract (component_id);
CREATE INDEX IF NOT EXISTS context_mask_contract_kind_idx ON context_mask_contract (mask_kind);
CREATE INDEX IF NOT EXISTS context_mask_contract_trigger_gin_idx ON context_mask_contract USING GIN (policy_trigger);
CREATE INDEX IF NOT EXISTS context_mask_contract_contract_gin_idx ON context_mask_contract USING GIN (contract);

-- Transformers are also context objects. This row makes transformation
-- contracts queryable: what representation is consumed, what is emitted, how
-- lossy it is, whether it calls a model, and how outputs are validated.
CREATE TABLE IF NOT EXISTS context_transformer_contract (
  transformer_contract_id TEXT PRIMARY KEY,
  context_object_id TEXT NOT NULL REFERENCES context_object(context_object_id) ON DELETE CASCADE,
  component_id      TEXT REFERENCES component(id) ON DELETE SET NULL,
  transformer_kind  TEXT NOT NULL CHECK (transformer_kind IN (
    'raw_to_normalized',
    'normalized_to_chunk',
    'chunk_to_claim',
    'object_to_artifact',
    'artifact_to_embedding',
    'candidate_to_reranked_list',
    'object_to_context_pack',
    'pack_to_ui_view',
    'mask_application',
    'schema_conversion',
    'custom'
  )),
  input_contract    JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_contract   JSONB NOT NULL DEFAULT '{}'::jsonb,
  deterministic     BOOLEAN,
  model_required    BOOLEAN NOT NULL DEFAULT FALSE,
  lossiness         TEXT CHECK (lossiness IS NULL OR lossiness IN ('none','low','medium','high','unknown')),
  reversible        BOOLEAN NOT NULL DEFAULT FALSE,
  validation        JSONB NOT NULL DEFAULT '{}'::jsonb,
  lineage_policy    JSONB NOT NULL DEFAULT '{}'::jsonb,
  contract          JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_transformer_contract_object_idx ON context_transformer_contract (context_object_id);
CREATE INDEX IF NOT EXISTS context_transformer_contract_component_idx ON context_transformer_contract (component_id);
CREATE INDEX IF NOT EXISTS context_transformer_contract_kind_idx ON context_transformer_contract (transformer_kind);
CREATE INDEX IF NOT EXISTS context_transformer_contract_input_gin_idx ON context_transformer_contract USING GIN (input_contract);
CREATE INDEX IF NOT EXISTS context_transformer_contract_output_gin_idx ON context_transformer_contract USING GIN (output_contract);

CREATE TABLE IF NOT EXISTS context_version (
  context_version_id TEXT PRIMARY KEY,
  context_object_id  TEXT NOT NULL REFERENCES context_object(context_object_id) ON DELETE CASCADE,
  content_hash       TEXT NOT NULL,
  metadata_hash      TEXT,
  acl_hash           TEXT,
  valid_from         TIMESTAMPTZ,
  valid_to           TIMESTAMPTZ,
  observed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  recorded_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw_snapshot_uri   TEXT,
  normalized_uri     TEXT,
  normalized_format  TEXT,
  version_document   JSONB NOT NULL DEFAULT '{}'::jsonb,
  tombstone          BOOLEAN NOT NULL DEFAULT FALSE,
  policy             JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_version_object_idx ON context_version (context_object_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS context_version_content_hash_idx ON context_version (content_hash);
CREATE INDEX IF NOT EXISTS context_version_valid_time_idx ON context_version (valid_from, valid_to);

CREATE TABLE IF NOT EXISTS context_relationship (
  context_relationship_id TEXT PRIMARY KEY,
  tenant_id         TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  from_id           TEXT,
  to_id             TEXT,
  endpoints         JSONB NOT NULL DEFAULT '[]'::jsonb,
  confidence        DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  strength          DOUBLE PRECISION CHECK (strength IS NULL OR (strength >= 0 AND strength <= 1)),
  source_handles    JSONB NOT NULL DEFAULT '[]'::jsonb,
  evidence_ids      JSONB NOT NULL DEFAULT '[]'::jsonb,
  valid_from        TIMESTAMPTZ,
  valid_to          TIMESTAMPTZ,
  observed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  recorded_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by        TEXT,
  attributes        JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy            JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_relationship_from_idx ON context_relationship (from_id, relationship_type);
CREATE INDEX IF NOT EXISTS context_relationship_to_idx ON context_relationship (to_id, relationship_type);
CREATE INDEX IF NOT EXISTS context_relationship_type_idx ON context_relationship (tenant_id, relationship_type);
CREATE INDEX IF NOT EXISTS context_relationship_valid_time_idx ON context_relationship (valid_from, valid_to);
CREATE INDEX IF NOT EXISTS context_relationship_endpoints_gin_idx ON context_relationship USING GIN (endpoints);
CREATE INDEX IF NOT EXISTS context_relationship_attributes_gin_idx ON context_relationship USING GIN (attributes);

CREATE TABLE IF NOT EXISTS context_assertion (
  context_assertion_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  subject_id       TEXT NOT NULL,
  predicate        TEXT NOT NULL,
  object_id        TEXT,
  value            JSONB,
  value_type       TEXT,
  confidence       DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  evidence         JSONB NOT NULL DEFAULT '[]'::jsonb,
  asserted_by      JSONB NOT NULL DEFAULT '{}'::jsonb,
  valid_from       TIMESTAMPTZ,
  valid_to         TIMESTAMPTZ,
  attributes       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_assertion_subject_idx ON context_assertion (subject_id, predicate);
CREATE INDEX IF NOT EXISTS context_assertion_object_idx ON context_assertion (object_id);
CREATE INDEX IF NOT EXISTS context_assertion_predicate_idx ON context_assertion (tenant_id, predicate);
CREATE INDEX IF NOT EXISTS context_assertion_value_gin_idx ON context_assertion USING GIN (value);
CREATE INDEX IF NOT EXISTS context_assertion_attributes_gin_idx ON context_assertion USING GIN (attributes);

CREATE TABLE IF NOT EXISTS context_dimension_definition (
  dimension_id     TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  namespace        TEXT NOT NULL,
  name             TEXT NOT NULL,
  description      TEXT,
  value_type       TEXT NOT NULL,
  normalized_min   DOUBLE PRECISION DEFAULT 0,
  normalized_max   DOUBLE PRECISION DEFAULT 1,
  higher_is        TEXT,
  aggregation      TEXT,
  display          JSONB NOT NULL DEFAULT '{}'::jsonb,
  definition       JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_dimension_definition_namespace_idx ON context_dimension_definition (tenant_id, namespace);
CREATE INDEX IF NOT EXISTS context_dimension_definition_name_idx ON context_dimension_definition (name);

CREATE TABLE IF NOT EXISTS context_dimension_value (
  dimension_value_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  dimension_id     TEXT NOT NULL REFERENCES context_dimension_definition(dimension_id) ON DELETE CASCADE,
  subject_id       TEXT NOT NULL,
  subject_kind     TEXT,
  value            JSONB NOT NULL,
  normalized_value DOUBLE PRECISION CHECK (normalized_value IS NULL OR (normalized_value >= 0 AND normalized_value <= 1)),
  label            TEXT,
  confidence       DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  scope            JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence         JSONB NOT NULL DEFAULT '[]'::jsonb,
  method           JSONB NOT NULL DEFAULT '{}'::jsonb,
  valid_from       TIMESTAMPTZ,
  valid_to         TIMESTAMPTZ,
  assessed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_dimension_value_subject_idx ON context_dimension_value (subject_id, dimension_id);
CREATE INDEX IF NOT EXISTS context_dimension_value_dimension_idx ON context_dimension_value (tenant_id, dimension_id, normalized_value DESC);
CREATE INDEX IF NOT EXISTS context_dimension_value_label_idx ON context_dimension_value (dimension_id, label);
CREATE INDEX IF NOT EXISTS context_dimension_value_assessed_idx ON context_dimension_value (assessed_at DESC);
CREATE INDEX IF NOT EXISTS context_dimension_value_scope_gin_idx ON context_dimension_value USING GIN (scope);

CREATE TABLE IF NOT EXISTS context_artifact (
  context_artifact_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  context_object_id TEXT REFERENCES context_object(context_object_id) ON DELETE SET NULL,
  context_version_id TEXT REFERENCES context_version(context_version_id) ON DELETE SET NULL,
  artifact_type    TEXT NOT NULL,
  content_uri      TEXT,
  content_text     TEXT,
  content_hash     TEXT NOT NULL,
  token_count      INTEGER,
  derived_from     JSONB NOT NULL DEFAULT '[]'::jsonb,
  generator        JSONB NOT NULL DEFAULT '{}'::jsonb,
  lineage_event_id TEXT,
  quality          JSONB NOT NULL DEFAULT '{}'::jsonb,
  attributes       JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_artifact_object_idx ON context_artifact (context_object_id);
CREATE INDEX IF NOT EXISTS context_artifact_version_idx ON context_artifact (context_version_id);
CREATE INDEX IF NOT EXISTS context_artifact_type_idx ON context_artifact (tenant_id, artifact_type);
CREATE INDEX IF NOT EXISTS context_artifact_hash_idx ON context_artifact (content_hash);
CREATE INDEX IF NOT EXISTS context_artifact_text_fts_idx ON context_artifact USING GIN (to_tsvector('english', coalesce(content_text, '')));
CREATE INDEX IF NOT EXISTS context_artifact_derived_from_gin_idx ON context_artifact USING GIN (derived_from);

CREATE TABLE IF NOT EXISTS context_lineage_event (
  context_lineage_event_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  event_type       TEXT NOT NULL,
  actor            JSONB NOT NULL DEFAULT '{}'::jsonb,
  inputs           JSONB NOT NULL DEFAULT '[]'::jsonb,
  outputs          JSONB NOT NULL DEFAULT '[]'::jsonb,
  pipeline         JSONB NOT NULL DEFAULT '{}'::jsonb,
  trace_id         TEXT,
  policy_decision  TEXT,
  occurred_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  attributes       JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS context_lineage_event_type_idx ON context_lineage_event (tenant_id, event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS context_lineage_event_trace_idx ON context_lineage_event (trace_id);
CREATE INDEX IF NOT EXISTS context_lineage_event_inputs_gin_idx ON context_lineage_event USING GIN (inputs);
CREATE INDEX IF NOT EXISTS context_lineage_event_outputs_gin_idx ON context_lineage_event USING GIN (outputs);

CREATE TABLE IF NOT EXISTS context_pack (
  context_pack_id TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  pack_type       TEXT NOT NULL,
  task            TEXT,
  query           TEXT,
  object_ids      JSONB NOT NULL DEFAULT '[]'::jsonb,
  artifact_ids    JSONB NOT NULL DEFAULT '[]'::jsonb,
  relationship_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  summary         TEXT,
  claims          JSONB NOT NULL DEFAULT '[]'::jsonb,
  conflicts       JSONB NOT NULL DEFAULT '[]'::jsonb,
  risks           JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_handles  JSONB NOT NULL DEFAULT '[]'::jsonb,
  trace_id        TEXT,
  token_budget    INTEGER,
  token_count     INTEGER,
  policy          JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_pack_tenant_type_idx ON context_pack (tenant_id, pack_type, created_at DESC);
CREATE INDEX IF NOT EXISTS context_pack_trace_idx ON context_pack (trace_id);
CREATE INDEX IF NOT EXISTS context_pack_objects_gin_idx ON context_pack USING GIN (object_ids);
CREATE INDEX IF NOT EXISTS context_pack_source_handles_gin_idx ON context_pack USING GIN (source_handles);

CREATE TABLE IF NOT EXISTS context_model_profile (
  model_profile_id TEXT PRIMARY KEY,
  tenant_id        TEXT NOT NULL,
  tier             INTEGER NOT NULL,
  slot             TEXT NOT NULL,
  example_families JSONB NOT NULL DEFAULT '[]'::jsonb,
  deployment_modes JSONB NOT NULL DEFAULT '[]'::jsonb,
  default_tasks    JSONB NOT NULL DEFAULT '[]'::jsonb,
  max_risk         TEXT NOT NULL,
  cost_profile     TEXT,
  privacy          JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_model_profile_tier_idx ON context_model_profile (tenant_id, tier, slot);
CREATE INDEX IF NOT EXISTS context_model_profile_tasks_gin_idx ON context_model_profile USING GIN (default_tasks);
CREATE INDEX IF NOT EXISTS context_model_profile_policy_gin_idx ON context_model_profile USING GIN (policy);

CREATE TABLE IF NOT EXISTS context_model_routing_policy (
  routing_policy_id TEXT PRIMARY KEY,
  tenant_id         TEXT NOT NULL,
  score_formula     JSONB NOT NULL,
  thresholds        JSONB NOT NULL,
  escalation_triggers JSONB NOT NULL DEFAULT '[]'::jsonb,
  policy            JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_model_routing_policy_triggers_gin_idx ON context_model_routing_policy USING GIN (escalation_triggers);
CREATE INDEX IF NOT EXISTS context_model_routing_policy_policy_gin_idx ON context_model_routing_policy USING GIN (policy);

CREATE TABLE IF NOT EXISTS context_reranker_profile (
  reranker_profile_id TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  stage               INTEGER NOT NULL,
  slot                TEXT NOT NULL,
  example_families    JSONB NOT NULL DEFAULT '[]'::jsonb,
  deployment_modes    JSONB NOT NULL DEFAULT '[]'::jsonb,
  default_tasks       JSONB NOT NULL DEFAULT '[]'::jsonb,
  candidate_pool      JSONB NOT NULL DEFAULT '{}'::jsonb,
  latency_profile     TEXT,
  training            JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy              JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_reranker_profile_stage_idx ON context_reranker_profile (tenant_id, stage, slot);
CREATE INDEX IF NOT EXISTS context_reranker_profile_tasks_gin_idx ON context_reranker_profile USING GIN (default_tasks);
CREATE INDEX IF NOT EXISTS context_reranker_profile_training_gin_idx ON context_reranker_profile USING GIN (training);
CREATE INDEX IF NOT EXISTS context_reranker_profile_policy_gin_idx ON context_reranker_profile USING GIN (policy);

CREATE TABLE IF NOT EXISTS context_reranking_policy (
  reranking_policy_id TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  score_formula       JSONB NOT NULL,
  pipeline            JSONB NOT NULL,
  escalation_triggers JSONB NOT NULL DEFAULT '[]'::jsonb,
  policy              JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_reranking_policy_pipeline_gin_idx ON context_reranking_policy USING GIN (pipeline);
CREATE INDEX IF NOT EXISTS context_reranking_policy_triggers_gin_idx ON context_reranking_policy USING GIN (escalation_triggers);
CREATE INDEX IF NOT EXISTS context_reranking_policy_policy_gin_idx ON context_reranking_policy USING GIN (policy);

CREATE TABLE IF NOT EXISTS context_local_memory_profile (
  local_memory_profile_id TEXT PRIMARY KEY,
  tenant_id               TEXT NOT NULL,
  memory_class            TEXT NOT NULL,
  scope                   JSONB NOT NULL DEFAULT '{}'::jsonb,
  storage                 JSONB NOT NULL DEFAULT '{}'::jsonb,
  encryption              JSONB NOT NULL DEFAULT '{}'::jsonb,
  search                  JSONB NOT NULL DEFAULT '{}'::jsonb,
  sync                    JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy                  JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_local_memory_profile_class_idx ON context_local_memory_profile (tenant_id, memory_class);
CREATE INDEX IF NOT EXISTS context_local_memory_profile_scope_gin_idx ON context_local_memory_profile USING GIN (scope);
CREATE INDEX IF NOT EXISTS context_local_memory_profile_encryption_gin_idx ON context_local_memory_profile USING GIN (encryption);
CREATE INDEX IF NOT EXISTS context_local_memory_profile_policy_gin_idx ON context_local_memory_profile USING GIN (policy);

CREATE TABLE IF NOT EXISTS context_local_sync_policy (
  local_sync_policy_id TEXT PRIMARY KEY,
  tenant_id            TEXT NOT NULL,
  sync_modes           JSONB NOT NULL DEFAULT '[]'::jsonb,
  offline_policy       JSONB NOT NULL DEFAULT '{}'::jsonb,
  cloud_visibility     JSONB NOT NULL DEFAULT '{}'::jsonb,
  tool_contract        JSONB NOT NULL DEFAULT '{}'::jsonb,
  policy               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS context_local_sync_policy_modes_gin_idx ON context_local_sync_policy USING GIN (sync_modes);
CREATE INDEX IF NOT EXISTS context_local_sync_policy_offline_gin_idx ON context_local_sync_policy USING GIN (offline_policy);
CREATE INDEX IF NOT EXISTS context_local_sync_policy_visibility_gin_idx ON context_local_sync_policy USING GIN (cloud_visibility);
CREATE INDEX IF NOT EXISTS context_local_sync_policy_policy_gin_idx ON context_local_sync_policy USING GIN (policy);

CREATE TABLE IF NOT EXISTS model_route_decision (
  model_route_id      TEXT PRIMARY KEY,
  task_type           TEXT NOT NULL,
  selected_adapter    TEXT NOT NULL,
  selected_model      TEXT,
  candidate_adapters  JSONB,
  trust_boundary      TEXT,
  cost_estimate       JSONB,
  latency_budget_ms   INTEGER,
  quality_tier        TEXT,
  route_reason        TEXT NOT NULL,
  pricing_snapshot_id TEXT,
  fallbacks           JSONB,
  created_at          TIMESTAMPTZ DEFAULT now()
);

-- Reusable solved subproblem fragments extracted from agent and pipeline
-- trajectories. These rows are the experience-cache layer: they are not
-- provider claims and do not store private user data unless a deployment has
-- explicit tenant consent and privacy controls.
CREATE TABLE IF NOT EXISTS trajectory_fragment (
  fragment_id        TEXT PRIMARY KEY,
  fragment_kind      TEXT NOT NULL CHECK (fragment_kind IN ('plan_node','tool_call','tool_result','code_patch','reasoning_summary','verification_step','error_recovery','prompt_template','response_snippet')),
  source_run_id      TEXT,
  source_component_id TEXT,
  subject_domain     TEXT,
  task_signature     TEXT NOT NULL,
  input_fingerprint  TEXT,
  output_fingerprint TEXT,
  prompt_hash        TEXT,
  tool_name          TEXT,
  model_route_id     TEXT REFERENCES model_route_decision(model_route_id) ON DELETE SET NULL,
  text               TEXT NOT NULL,
  body               JSONB NOT NULL,
  privacy_boundary   TEXT,
  license            TEXT,
  quality_status     TEXT,
  verification       JSONB,
  cost_trace         JSONB,
  created_at         TIMESTAMPTZ DEFAULT now(),
  expires_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS trajectory_fragment_kind_idx ON trajectory_fragment (fragment_kind);
CREATE INDEX IF NOT EXISTS trajectory_fragment_task_idx ON trajectory_fragment (task_signature);
CREATE INDEX IF NOT EXISTS trajectory_fragment_domain_idx ON trajectory_fragment (subject_domain);
CREATE INDEX IF NOT EXISTS trajectory_fragment_body_gin_idx ON trajectory_fragment USING GIN (body);
CREATE INDEX IF NOT EXISTS trajectory_fragment_text_fts_idx ON trajectory_fragment USING GIN (to_tsvector('english', text));

CREATE TABLE IF NOT EXISTS fragment_cache_candidate (
  candidate_id        TEXT PRIMARY KEY,
  request_signature  TEXT NOT NULL,
  fragment_id        TEXT NOT NULL REFERENCES trajectory_fragment(fragment_id) ON DELETE CASCADE,
  retrieval_method   TEXT NOT NULL,
  similarity         NUMERIC,
  rank               INTEGER,
  verifier_status    TEXT,
  verifier_score     NUMERIC,
  stitch_role        TEXT,
  rejection_reason   TEXT,
  created_at         TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS fragment_cache_candidate_request_idx ON fragment_cache_candidate (request_signature, rank);
CREATE INDEX IF NOT EXISTS fragment_cache_candidate_fragment_idx ON fragment_cache_candidate (fragment_id);

CREATE TABLE IF NOT EXISTS cache_reuse_event (
  reuse_event_id      TEXT PRIMARY KEY,
  request_signature  TEXT NOT NULL,
  selected_fragment_ids JSONB NOT NULL,
  composition_strategy TEXT NOT NULL,
  fallback_model_used BOOLEAN NOT NULL DEFAULT FALSE,
  estimated_saved_cost_usd NUMERIC,
  estimated_saved_latency_ms INTEGER,
  verifier_status    TEXT,
  user_visible       BOOLEAN NOT NULL DEFAULT FALSE,
  privacy_boundary   TEXT,
  created_at         TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS cache_reuse_event_request_idx ON cache_reuse_event (request_signature);
CREATE INDEX IF NOT EXISTS cache_reuse_event_status_idx ON cache_reuse_event (verifier_status);

-- Operational views for the seed/export transition. These views make it clear
-- which rows came from reviewable repository manifests, which seeds are stale
-- or flagged for archive review, and how much queryable database structure was
-- expanded from each manifest.
CREATE OR REPLACE VIEW catalog_manifest_import_status AS
SELECT
  r.component_id,
  r.component_type,
  r.manifest_path,
  r.manifest_hash,
  r.manifest_updated,
  r.manifest_lifecycle,
  r.manifest_freshness,
  r.definition_source,
  r.import_status,
  r.recommended_action,
  r.rotted_context_flags,
  r.row_counts,
  r.created_at AS imported_at,
  b.source_kind,
  b.source_ref,
  b.import_mode
FROM manifest_import_record r
JOIN manifest_import_batch b
  ON b.manifest_import_batch_id = r.manifest_import_batch_id;

CREATE OR REPLACE VIEW component_database_readiness AS
SELECT
  c.id AS component_id,
  c.type,
  c.version,
  c.lifecycle,
  c.freshness,
  c.updated,
  cv.component_version_id,
  cv.definition_source,
  cv.definition_hash,
  cv.source_ref,
  COALESCE(rd.dimension_count, 0) AS rubric_dimension_count,
  COALESCE(ref.outbound_ref_count, 0) AS outbound_ref_count,
  COALESCE(ctx.context_object_count, 0) AS context_object_count,
  COALESCE(mask.mask_contract_count, 0) AS mask_contract_count,
  COALESCE(transformer.transformer_contract_count, 0) AS transformer_contract_count,
  CASE
    WHEN cv.definition_source IS NULL THEN 'missing_version_record'
    WHEN c.type = 'rubric' AND COALESCE(rd.dimension_count, 0) = 0 THEN 'rubric_dimensions_not_expanded'
    WHEN c.type = 'processor' AND COALESCE(transformer.transformer_contract_count, 0) = 0 THEN 'processor_transformer_contract_not_expanded'
    ELSE 'database_ready'
  END AS readiness_status
FROM component c
LEFT JOIN LATERAL (
  SELECT *
  FROM component_version cv
  WHERE cv.component_id = c.id
  ORDER BY
    CASE cv.version_status WHEN 'active' THEN 0 WHEN 'review' THEN 1 ELSE 2 END,
    cv.created_at DESC
  LIMIT 1
) cv ON TRUE
LEFT JOIN (
  SELECT rubric_id, count(*) AS dimension_count
  FROM rubric_dimension
  GROUP BY rubric_id
) rd ON rd.rubric_id = c.id
LEFT JOIN (
  SELECT src_id, count(*) AS outbound_ref_count
  FROM component_ref
  GROUP BY src_id
) ref ON ref.src_id = c.id
LEFT JOIN (
  SELECT component_id, count(*) AS context_object_count
  FROM component_context_object
  GROUP BY component_id
) ctx ON ctx.component_id = c.id
LEFT JOIN (
  SELECT component_id, count(*) AS mask_contract_count
  FROM context_mask_contract
  WHERE component_id IS NOT NULL
  GROUP BY component_id
) mask ON mask.component_id = c.id
LEFT JOIN (
  SELECT component_id, count(*) AS transformer_contract_count
  FROM context_transformer_contract
  WHERE component_id IS NOT NULL
  GROUP BY component_id
) transformer ON transformer.component_id = c.id;

CREATE OR REPLACE VIEW rubric_dimension_tree AS
SELECT
  d.rubric_id,
  c.name AS rubric_name,
  d.dimension_path,
  d.parent_path,
  parent.label AS parent_label,
  d.dimension_level,
  d.label,
  d.weight,
  d.scale,
  d.evidence_required,
  d.gate,
  d.body
FROM rubric_dimension d
JOIN component c
  ON c.id = d.rubric_id
LEFT JOIN rubric_dimension parent
  ON parent.rubric_id = d.rubric_id
 AND parent.dimension_path = d.parent_path;

CREATE OR REPLACE VIEW object_governance_profile_readiness AS
SELECT
  p.tenant_id,
  p.object_type,
  p.object_family,
  p.display_name,
  p.owner_team,
  p.steward,
  p.body->>'seed_scope' AS seed_scope,
  p.body->>'registry_owner' AS registry_owner,
  p.lifecycle->>'status' AS lifecycle_status,
  p.body->>'specialization_level' AS specialization_level,
  jsonb_array_length(p.required_rubrics) AS required_rubric_count,
  jsonb_array_length(p.required_relationships) AS required_relationship_count,
  jsonb_array_length(p.required_dimensions) AS required_dimension_count,
  jsonb_array_length(p.required_events) AS required_event_count,
  EXISTS (
    SELECT 1 FROM object_contract c
    WHERE c.tenant_id = p.tenant_id
      AND c.object_type = p.object_type
  ) AS has_contract,
  EXISTS (
    SELECT 1 FROM object_schema_profile s
    WHERE s.tenant_id = p.tenant_id
      AND s.object_type = p.object_type
  ) AS has_schema_profile,
  EXISTS (
    SELECT 1 FROM object_layout_profile l
    WHERE l.tenant_id = p.tenant_id
      AND l.object_type = p.object_type
  ) AS has_layout_profile,
  EXISTS (
    SELECT 1 FROM object_architecture_diagram d
    WHERE d.tenant_id = p.tenant_id
      AND d.object_type = p.object_type
  ) AS has_architecture_diagram,
  EXISTS (
    SELECT 1 FROM object_context_rule r
    WHERE r.tenant_id = p.tenant_id
      AND r.object_type = p.object_type
  ) AS has_context_rule,
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM object_contract c
      WHERE c.tenant_id = p.tenant_id
        AND c.object_type = p.object_type
    ) THEN 'missing_contract'
    WHEN NOT EXISTS (
      SELECT 1 FROM object_schema_profile s
      WHERE s.tenant_id = p.tenant_id
        AND s.object_type = p.object_type
    ) THEN 'missing_schema_profile'
    WHEN NOT EXISTS (
      SELECT 1 FROM object_layout_profile l
      WHERE l.tenant_id = p.tenant_id
        AND l.object_type = p.object_type
    ) THEN 'missing_layout_profile'
    WHEN NOT EXISTS (
      SELECT 1 FROM object_architecture_diagram d
      WHERE d.tenant_id = p.tenant_id
        AND d.object_type = p.object_type
    ) THEN 'missing_architecture_diagram'
    WHEN NOT EXISTS (
      SELECT 1 FROM object_context_rule r
      WHERE r.tenant_id = p.tenant_id
        AND r.object_type = p.object_type
    ) THEN 'missing_context_rule'
    WHEN COALESCE(p.body->>'specialization_level', 'generic') = 'generic'
      AND p.body->>'seed_scope' = 'concrete_object_baseline'
      THEN 'generic_concrete_baseline'
    ELSE 'governance_ready'
  END AS readiness_status
FROM object_governance_profile p;

CREATE OR REPLACE VIEW object_governance_family_coverage AS
SELECT
  tenant_id,
  object_family,
  count(*) AS profile_count,
  count(*) FILTER (WHERE seed_scope = 'family_baseline') AS family_baseline_count,
  count(*) FILTER (WHERE seed_scope = 'concrete_object_baseline') AS concrete_object_count,
  count(*) FILTER (WHERE readiness_status = 'governance_ready') AS ready_profile_count,
  count(*) FILTER (WHERE readiness_status <> 'governance_ready') AS not_ready_profile_count,
  jsonb_agg(
    jsonb_build_object(
      'object_type', object_type,
      'display_name', display_name,
      'seed_scope', seed_scope,
      'specialization_level', specialization_level,
      'readiness_status', readiness_status
    )
    ORDER BY object_type
  ) AS profiles
FROM object_governance_profile_readiness
GROUP BY tenant_id, object_family;

CREATE OR REPLACE VIEW object_governance_specialization_status AS
SELECT
  p.tenant_id,
  p.object_type,
  p.object_family,
  p.display_name,
  p.body->>'seed_scope' AS seed_scope,
  COALESCE(p.body->>'specialization_level', 'generic') AS specialization_level,
  c.contract_kind,
  s.schema_kind,
  l.layout_kind,
  d.diagram_kind,
  r.rule_kind,
  p.database_mapping,
  p.cloud_mapping,
  p.policy
FROM object_governance_profile p
LEFT JOIN object_contract c
  ON c.tenant_id = p.tenant_id
 AND c.object_type = p.object_type
LEFT JOIN object_schema_profile s
  ON s.tenant_id = p.tenant_id
 AND s.object_type = p.object_type
LEFT JOIN object_layout_profile l
  ON l.tenant_id = p.tenant_id
 AND l.object_type = p.object_type
LEFT JOIN object_architecture_diagram d
  ON d.tenant_id = p.tenant_id
 AND d.object_type = p.object_type
LEFT JOIN object_context_rule r
  ON r.tenant_id = p.tenant_id
 AND r.object_type = p.object_type;

-- A pipeline / benchmark / harness run. Append-only.
CREATE TABLE IF NOT EXISTS run (
  run_id      TEXT PRIMARY KEY,
  component_id TEXT NOT NULL REFERENCES component(id),
  started_at  TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status      TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
  adapter_id  TEXT REFERENCES component(id),
  inputs      JSONB,
  outputs     JSONB,
  trace       JSONB,
  cost_usd    NUMERIC,
  trust_boundary TEXT
);
CREATE INDEX IF NOT EXISTS run_component_started_idx ON run (component_id, started_at DESC);

COMMIT;
