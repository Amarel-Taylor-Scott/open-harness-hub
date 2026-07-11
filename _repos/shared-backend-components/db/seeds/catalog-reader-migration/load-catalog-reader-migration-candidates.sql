-- Load catalog reader migration candidate seed rows.
-- Review db/seeds/catalog-reader-migration/catalog_reader_migration_candidate.jsonl before loading.

BEGIN;

CREATE TEMP TABLE tmp_catalog_reader_migration_candidate_jsonl (
  body jsonb NOT NULL
);

\copy tmp_catalog_reader_migration_candidate_jsonl(body) FROM 'db/seeds/catalog-reader-migration/catalog_reader_migration_candidate.jsonl' WITH (FORMAT text);

INSERT INTO catalog_reader_migration_candidate (
  reader_candidate_id,
  tenant_id,
  source_path,
  source_kind,
  classification,
  migration_status,
  priority,
  recommended_action,
  matches,
  samples,
  note,
  owner_team,
  detected_by,
  body
)
SELECT
  body->>'reader_candidate_id',
  body->>'tenant_id',
  body->>'source_path',
  body->>'source_kind',
  body->>'classification',
  body->>'migration_status',
  (body->>'priority')::integer,
  body->>'recommended_action',
  body->'matches',
  body->'samples',
  NULLIF(body->>'note', ''),
  NULLIF(body->>'owner_team', ''),
  body->>'detected_by',
  body->'body'
FROM tmp_catalog_reader_migration_candidate_jsonl
ON CONFLICT (tenant_id, source_path)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  classification = EXCLUDED.classification,
  migration_status = EXCLUDED.migration_status,
  priority = EXCLUDED.priority,
  recommended_action = EXCLUDED.recommended_action,
  matches = EXCLUDED.matches,
  samples = EXCLUDED.samples,
  note = EXCLUDED.note,
  owner_team = EXCLUDED.owner_team,
  detected_by = EXCLUDED.detected_by,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
