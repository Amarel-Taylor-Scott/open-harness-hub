-- Load manifest import seed rows.
-- Review db/seeds/manifest-import/*.jsonl before running this in a shared database.

BEGIN;

CREATE TEMP TABLE tmp_manifest_import_batch_jsonl (
  body jsonb NOT NULL
);

CREATE TEMP TABLE tmp_manifest_import_record_jsonl (
  body jsonb NOT NULL
);

\copy tmp_manifest_import_batch_jsonl(body) FROM 'db/seeds/manifest-import/manifest_import_batch.jsonl' WITH (FORMAT text);
\copy tmp_manifest_import_record_jsonl(body) FROM 'db/seeds/manifest-import/manifest_import_record.jsonl' WITH (FORMAT text);

INSERT INTO manifest_import_batch (
  manifest_import_batch_id,
  source_kind,
  source_ref,
  importer,
  import_mode,
  policy,
  summary
)
SELECT
  body->>'manifest_import_batch_id',
  body->>'source_kind',
  body->>'source_ref',
  body->>'importer',
  body->>'import_mode',
  body->'policy',
  body->'summary'
FROM tmp_manifest_import_batch_jsonl
ON CONFLICT (manifest_import_batch_id)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  source_ref = EXCLUDED.source_ref,
  importer = EXCLUDED.importer,
  import_mode = EXCLUDED.import_mode,
  policy = EXCLUDED.policy,
  summary = EXCLUDED.summary;

INSERT INTO manifest_import_record (
  manifest_import_record_id,
  manifest_import_batch_id,
  component_id,
  component_type,
  manifest_path,
  manifest_hash,
  manifest_updated,
  manifest_lifecycle,
  manifest_freshness,
  definition_source,
  import_status,
  recommended_action,
  rotted_context_flags,
  row_counts,
  source_ref,
  error_message
)
SELECT
  body->>'manifest_import_record_id',
  body->>'manifest_import_batch_id',
  NULLIF(body->>'component_id', ''),
  NULLIF(body->>'component_type', ''),
  body->>'manifest_path',
  body->>'manifest_hash',
  NULLIF(body->>'manifest_updated', '')::date,
  NULLIF(body->>'manifest_lifecycle', ''),
  NULLIF(body->>'manifest_freshness', ''),
  body->>'definition_source',
  body->>'import_status',
  body->>'recommended_action',
  body->'rotted_context_flags',
  body->'row_counts',
  NULLIF(body->>'source_ref', ''),
  NULLIF(body->>'error_message', '')
FROM tmp_manifest_import_record_jsonl
ON CONFLICT (manifest_import_batch_id, manifest_path)
DO UPDATE SET
  component_id = EXCLUDED.component_id,
  component_type = EXCLUDED.component_type,
  manifest_hash = EXCLUDED.manifest_hash,
  manifest_updated = EXCLUDED.manifest_updated,
  manifest_lifecycle = EXCLUDED.manifest_lifecycle,
  manifest_freshness = EXCLUDED.manifest_freshness,
  definition_source = EXCLUDED.definition_source,
  import_status = EXCLUDED.import_status,
  recommended_action = EXCLUDED.recommended_action,
  rotted_context_flags = EXCLUDED.rotted_context_flags,
  row_counts = EXCLUDED.row_counts,
  source_ref = EXCLUDED.source_ref,
  error_message = EXCLUDED.error_message;

COMMIT;
