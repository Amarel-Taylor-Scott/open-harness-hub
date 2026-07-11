-- Primitive variation dimension atlas schema additions.
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
