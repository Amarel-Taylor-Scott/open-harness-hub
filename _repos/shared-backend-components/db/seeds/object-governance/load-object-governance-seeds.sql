-- Object governance seed load example.
-- Run from the repository root with:
--   psql "$DATABASE_URL" -f db/seeds/object-governance/load-object-governance-seeds.sql
--
-- This is intentionally reviewable SQL, not a migration. The canonical schema
-- is db/postgres/schema.sql.

CREATE TEMP TABLE seed_object_governance_profile (row jsonb);
\copy seed_object_governance_profile(row) FROM 'db/seeds/object-governance/object_governance_profile.jsonl'
\copy seed_object_governance_profile(row) FROM 'db/seeds/object-governance/concrete_object_governance_profile.jsonl'

INSERT INTO object_governance_profile (
  object_governance_profile_id,
  tenant_id,
  object_type,
  object_family,
  display_name,
  description,
  owner_team,
  steward,
  lifecycle,
  required_rubrics,
  required_contracts,
  required_schemas,
  required_layouts,
  required_diagrams,
  required_context_rules,
  required_relationships,
  required_dimensions,
  required_events,
  database_mapping,
  cloud_mapping,
  policy,
  body
)
SELECT
  row->>'object_governance_profile_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'object_family',
  row->>'display_name',
  row->>'description',
  row->>'owner_team',
  row->>'steward',
  row->'lifecycle',
  row->'required_rubrics',
  row->'required_contracts',
  row->'required_schemas',
  row->'required_layouts',
  row->'required_diagrams',
  row->'required_context_rules',
  row->'required_relationships',
  row->'required_dimensions',
  row->'required_events',
  row->'database_mapping',
  row->'cloud_mapping',
  row->'policy',
  row->'body'
FROM seed_object_governance_profile
ON CONFLICT (tenant_id, object_type) DO UPDATE SET
  object_family = EXCLUDED.object_family,
  display_name = EXCLUDED.display_name,
  description = EXCLUDED.description,
  owner_team = EXCLUDED.owner_team,
  steward = EXCLUDED.steward,
  lifecycle = EXCLUDED.lifecycle,
  required_rubrics = EXCLUDED.required_rubrics,
  required_contracts = EXCLUDED.required_contracts,
  required_schemas = EXCLUDED.required_schemas,
  required_layouts = EXCLUDED.required_layouts,
  required_diagrams = EXCLUDED.required_diagrams,
  required_context_rules = EXCLUDED.required_context_rules,
  required_relationships = EXCLUDED.required_relationships,
  required_dimensions = EXCLUDED.required_dimensions,
  required_events = EXCLUDED.required_events,
  database_mapping = EXCLUDED.database_mapping,
  cloud_mapping = EXCLUDED.cloud_mapping,
  policy = EXCLUDED.policy,
  body = EXCLUDED.body,
  updated_at = now();

CREATE TEMP TABLE seed_object_contract (row jsonb);
\copy seed_object_contract(row) FROM 'db/seeds/object-governance/object_contract.jsonl'
\copy seed_object_contract(row) FROM 'db/seeds/object-governance/concrete_object_contract.jsonl'

INSERT INTO object_contract (
  object_contract_id,
  tenant_id,
  object_type,
  contract_kind,
  name,
  version,
  applies_to_actions,
  inputs,
  outputs,
  invariants,
  failure_modes,
  compatibility,
  policy,
  body
)
SELECT
  row->>'object_contract_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'contract_kind',
  row->>'name',
  row->>'version',
  row->'applies_to_actions',
  row->'inputs',
  row->'outputs',
  row->'invariants',
  row->'failure_modes',
  row->'compatibility',
  row->'policy',
  row->'body'
FROM seed_object_contract
ON CONFLICT (tenant_id, object_type, contract_kind, name, version) DO UPDATE SET
  applies_to_actions = EXCLUDED.applies_to_actions,
  inputs = EXCLUDED.inputs,
  outputs = EXCLUDED.outputs,
  invariants = EXCLUDED.invariants,
  failure_modes = EXCLUDED.failure_modes,
  compatibility = EXCLUDED.compatibility,
  policy = EXCLUDED.policy,
  body = EXCLUDED.body,
  updated_at = now();

CREATE TEMP TABLE seed_object_schema_profile (row jsonb);
\copy seed_object_schema_profile(row) FROM 'db/seeds/object-governance/object_schema_profile.jsonl'
\copy seed_object_schema_profile(row) FROM 'db/seeds/object-governance/concrete_object_schema_profile.jsonl'

INSERT INTO object_schema_profile (
  object_schema_profile_id,
  tenant_id,
  object_type,
  schema_kind,
  schema_ref,
  version,
  required_fields,
  optional_fields,
  promoted_indexes,
  validation,
  evolution_policy,
  body
)
SELECT
  row->>'object_schema_profile_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'schema_kind',
  row->>'schema_ref',
  row->>'version',
  row->'required_fields',
  row->'optional_fields',
  row->'promoted_indexes',
  row->'validation',
  row->'evolution_policy',
  row->'body'
FROM seed_object_schema_profile
ON CONFLICT (tenant_id, object_type, schema_kind, version) DO UPDATE SET
  schema_ref = EXCLUDED.schema_ref,
  required_fields = EXCLUDED.required_fields,
  optional_fields = EXCLUDED.optional_fields,
  promoted_indexes = EXCLUDED.promoted_indexes,
  validation = EXCLUDED.validation,
  evolution_policy = EXCLUDED.evolution_policy,
  body = EXCLUDED.body,
  updated_at = now();

CREATE TEMP TABLE seed_object_layout_profile (row jsonb);
\copy seed_object_layout_profile(row) FROM 'db/seeds/object-governance/object_layout_profile.jsonl'
\copy seed_object_layout_profile(row) FROM 'db/seeds/object-governance/concrete_object_layout_profile.jsonl'

INSERT INTO object_layout_profile (
  object_layout_profile_id,
  tenant_id,
  object_type,
  layout_kind,
  version,
  audience,
  sections,
  actions,
  masks,
  accessibility,
  body
)
SELECT
  row->>'object_layout_profile_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'layout_kind',
  row->>'version',
  row->>'audience',
  row->'sections',
  row->'actions',
  row->'masks',
  row->'accessibility',
  row->'body'
FROM seed_object_layout_profile
ON CONFLICT (tenant_id, object_type, layout_kind, version) DO UPDATE SET
  audience = EXCLUDED.audience,
  sections = EXCLUDED.sections,
  actions = EXCLUDED.actions,
  masks = EXCLUDED.masks,
  accessibility = EXCLUDED.accessibility,
  body = EXCLUDED.body,
  updated_at = now();

CREATE TEMP TABLE seed_object_architecture_diagram (row jsonb);
\copy seed_object_architecture_diagram(row) FROM 'db/seeds/object-governance/object_architecture_diagram.jsonl'
\copy seed_object_architecture_diagram(row) FROM 'db/seeds/object-governance/concrete_object_architecture_diagram.jsonl'

INSERT INTO object_architecture_diagram (
  object_architecture_diagram_id,
  tenant_id,
  object_type,
  diagram_kind,
  title,
  version,
  diagram_format,
  diagram_text,
  diagram_uri,
  related_objects,
  source_handles,
  body
)
SELECT
  row->>'object_architecture_diagram_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'diagram_kind',
  row->>'title',
  row->>'version',
  row->>'diagram_format',
  row->>'diagram_text',
  row->>'diagram_uri',
  row->'related_objects',
  row->'source_handles',
  row->'body'
FROM seed_object_architecture_diagram
ON CONFLICT (tenant_id, object_type, diagram_kind, version) DO UPDATE SET
  title = EXCLUDED.title,
  diagram_format = EXCLUDED.diagram_format,
  diagram_text = EXCLUDED.diagram_text,
  diagram_uri = EXCLUDED.diagram_uri,
  related_objects = EXCLUDED.related_objects,
  source_handles = EXCLUDED.source_handles,
  body = EXCLUDED.body,
  updated_at = now();

CREATE TEMP TABLE seed_object_context_rule (row jsonb);
\copy seed_object_context_rule(row) FROM 'db/seeds/object-governance/object_context_rule.jsonl'
\copy seed_object_context_rule(row) FROM 'db/seeds/object-governance/concrete_object_context_rule.jsonl'

INSERT INTO object_context_rule (
  object_context_rule_id,
  tenant_id,
  object_type,
  rule_kind,
  name,
  severity,
  applies_to_actions,
  condition,
  requirement,
  evidence_required,
  body
)
SELECT
  row->>'object_context_rule_id',
  row->>'tenant_id',
  row->>'object_type',
  row->>'rule_kind',
  row->>'name',
  row->>'severity',
  row->'applies_to_actions',
  row->'condition',
  row->'requirement',
  row->>'evidence_required',
  row->'body'
FROM seed_object_context_rule
ON CONFLICT (tenant_id, object_type, rule_kind, name) DO UPDATE SET
  severity = EXCLUDED.severity,
  applies_to_actions = EXCLUDED.applies_to_actions,
  condition = EXCLUDED.condition,
  requirement = EXCLUDED.requirement,
  evidence_required = EXCLUDED.evidence_required,
  body = EXCLUDED.body,
  updated_at = now();
