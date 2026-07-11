-- Load setting_profile seed rows.
-- Review db/seeds/settings-registry/setting_profile.jsonl before loading.

BEGIN;

CREATE TEMP TABLE tmp_setting_profile_jsonl (
  body jsonb NOT NULL
);

\copy tmp_setting_profile_jsonl(body) FROM 'db/seeds/settings-registry/setting_profile.jsonl' WITH (FORMAT text);

INSERT INTO setting_profile (
  setting_profile_id,
  tenant_id,
  namespace,
  setting_key,
  setting_kind,
  value_type,
  default_value,
  allowed_values,
  validation,
  source_of_truth,
  body
)
SELECT
  body->>'setting_profile_id',
  body->>'tenant_id',
  body->>'namespace',
  body->>'setting_key',
  body->>'setting_kind',
  body->>'value_type',
  body->'default_value',
  body->'allowed_values',
  body->'validation',
  body->>'source_of_truth',
  body->'body'
FROM tmp_setting_profile_jsonl
ON CONFLICT (tenant_id, namespace, setting_key)
DO UPDATE SET
  setting_kind = EXCLUDED.setting_kind,
  value_type = EXCLUDED.value_type,
  default_value = EXCLUDED.default_value,
  allowed_values = EXCLUDED.allowed_values,
  validation = EXCLUDED.validation,
  source_of_truth = EXCLUDED.source_of_truth,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
