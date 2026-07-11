# Primitive Variation Dimension Atlas Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes expanding
primitive specialization without materializing the full Cartesian product.

Status: execution brief plus generated seed registry. These rows are candidate
planning artifacts, not promoted truth.

## Core Model

Resolve specialized primitives from dimensions:

```text
basic computer logic primitive
  + algorithm or data-structure overlay
  + data or schema overlay
  + file, database, or storage overlay
  + runtime or stack overlay
  + website, source, or API overlay
  + industry or domain overlay
  + region, geography, or legal overlay
  + role or seniority overlay
  + proof or benchmark overlay
  = resolved specialized primitive
```

Do not physically create every Cartesian product. Store base primitives,
variation dimensions, overlays, and resolver rules; materialize only hot,
high-value, benchmarked, or proof-backed combinations.

## Seed Pack

The generated seed pack is:

```text
catalog/knowledge-packs/data/primitive-variation-dimension-atlas/
```

It contains:

- `primitive_variation_dimensions_250.jsonl` with 250 dimensions across 25
  families;
- `primitive_variation_dimensions_grouped.yaml` as a grouped view;
- `primitive_specialization_examples.jsonl` for concrete resolution paths;
- `role_algorithm_data_structure_matrix.jsonl` for role-weighted algorithm and
  data-structure preferences;
- `variation_resolver_rules.jsonl` for materialization and conflict behavior;
- `variation_dimension_schema_additions.sql` for database shape.

The generator is:

```bash
python3 scripts/generate_primitive_variation_dimension_atlas.py
```

The checker is:

```bash
python3 scripts/check_primitive_variation_dimension_atlas.py --self-test
```

## Families

The atlas covers:

```text
primitive identity and granularity
core computer logic
algorithms and data structures
data types and schema semantics
data layout storage and modeling
file message and artifact formats
SQL database and query engines
language runtime and technology stack
API web event and integration surfaces
web browsing and source surfaces
industry domain and business context
region geography localization and jurisdiction
legal compliance security and governance
UI visualization media and artifact design
ML AI RAG and benchmark dimensions
DevOps observability and runtime operations
source mining benchmarks and public corpora
job role seniority and workforce dimensions
embedding affinity search and materialization
architecture system design and pattern dimensions
common schema and interchange variations
public repo package and codebase variations
geospatial open-data and public-services variations
response format and user-output variations
variation-control and lattice dimensions
```

## Operating Rule

The resolver should emit:

```text
resolved primitive card
+ proof plan
+ runtime plan
+ source/evidence requirements
+ ranking explanation
```

and should not persist a resolved card unless the materialization rule allows
it:

```text
hot combination
benchmark demand
customer pack
proof-backed promotion evidence
```

All rows remain:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

until source refs, license review, contract tests, runtime proof, and promotion
review pass.

## Example

Base edge:

```text
Collection[T]+Predicate[T] -> FilteredCollection[T]
```

Selected dimensions:

```text
filter
FHIR resource
BigQuery
PHI
country
```

Resolved edge:

```text
BigQueryTable[FHIRObservation]+ObservationCodeDatePredicate+PHIPolicy
  -> FilteredObservationTable+QueryReceipt
```

This is the intended direction: universal logic remains compact, while
dimension overlays specialize it for industry, schema, runtime, geography, and
proof.

## Validation

Run:

```bash
python3 scripts/generate_primitive_variation_dimension_atlas.py
python3 scripts/check_primitive_variation_dimension_atlas.py --self-test
python3 scripts/check_primitive_customization_overlays.py --self-test
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
```
