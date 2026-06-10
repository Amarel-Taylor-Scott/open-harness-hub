-- Load context archive candidate seed rows.
-- Review db/seeds/archive-candidates/context_archive_candidate.jsonl before running this in a shared database.

BEGIN;

CREATE TEMP TABLE tmp_context_archive_candidate_jsonl (
  body jsonb NOT NULL
);

\copy tmp_context_archive_candidate_jsonl(body) FROM 'db/seeds/archive-candidates/context_archive_candidate.jsonl' WITH (FORMAT text);

INSERT INTO context_archive_candidate (
  archive_candidate_id,
  tenant_id,
  source_path,
  source_kind,
  source_hash,
  status,
  suggested_action,
  severity_score,
  confidence,
  canonical_replacement_hint,
  reasons,
  required_next_checks,
  detected_by,
  detection_source,
  body
)
SELECT
  body->>'archive_candidate_id',
  body->>'tenant_id',
  body->>'source_path',
  body->>'source_kind',
  NULLIF(body->>'source_hash', ''),
  body->>'status',
  body->>'suggested_action',
  (body->>'severity_score')::integer,
  body->>'confidence',
  NULLIF(body->>'canonical_replacement_hint', ''),
  body->'reasons',
  body->'required_next_checks',
  body->>'detected_by',
  body->>'detection_source',
  body->'body'
FROM tmp_context_archive_candidate_jsonl
ON CONFLICT (tenant_id, source_path, detection_source)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  source_hash = EXCLUDED.source_hash,
  status = EXCLUDED.status,
  suggested_action = EXCLUDED.suggested_action,
  severity_score = EXCLUDED.severity_score,
  confidence = EXCLUDED.confidence,
  canonical_replacement_hint = EXCLUDED.canonical_replacement_hint,
  reasons = EXCLUDED.reasons,
  required_next_checks = EXCLUDED.required_next_checks,
  detected_by = EXCLUDED.detected_by,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
