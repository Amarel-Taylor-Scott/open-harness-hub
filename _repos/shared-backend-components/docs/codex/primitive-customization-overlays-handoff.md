# Primitive Customization Overlays Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes expanding
specialized primitives for common websites, industries, and data schemas.

Status: execution brief plus seed registry. The rows below are candidate
planning artifacts, not promoted truth.

## Core Move

Customize primitives by composition, not duplication.

```text
base capability
  + canonical object
  + platform or website overlay
  + industry policy
  + schema map
  + runtime wrapper
  + proof overlay
  = specialized primitive
```

Do not fork a new primitive for every platform/workflow combination when a
base family plus overlays can express the same contract. The LLM should see the
visible input edge, visible output edge, blackbox behavior, effects, runtime
shape, source/proof status, and negative-memory warnings first. Hidden member
edges are drill-down context.

## Seed Pack

The first concrete pack is:

```text
catalog/knowledge-packs/data/primitive-customization-overlays/
```

It contains:

- `canonical_objects.jsonl` for stable cross-platform business objects;
- `platform_overlays.jsonl` for platform, website, and schema-specific deltas;
- `specialized_primitives.jsonl` for composed primitive groups;
- `specialization_mutators.jsonl` for deterministic glue;
- `negative_memory.jsonl` for known bad matches and repeat failure patterns;
- `manifest.json` for the pack contract.

All row IDs are stable and version-free. Put version metadata in fields, never
in IDs or slugs. All rows stay:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

until source refs, license review, contract tests, privacy review, and runtime
proof receipts pass.

## Specialization Ladder

Use this ladder to decide where a customization belongs:

```text
L0 base capability: import, sync, reconcile, extract, classify, report
L1 canonical object: customer, order, invoice, payment, product, claim
L2 schema standard: JSON Schema, OpenAPI, AsyncAPI, FHIR, XBRL, GS1
L3 platform or website: Shopify, Stripe, HubSpot, QuickBooks, Jira
L4 industry: retail, healthcare, finance, insurance, SaaS, construction
L5 workflow: dedupe, sync, route, reconcile, normalize, alert
L6 runtime shape: API endpoint, queue worker, cron job, workflow step
L7 policy and proof: idempotency, audit, privacy, security, benchmark
```

A specialized primitive is a selected path through that ladder, expressed as a
compact edge contract.

## Variation Dimensions

For broad specialization, use the variation atlas before generating more
overlays. Read `docs/codex/primitive-variation-dimension-atlas-handoff.md`.

The seed pack is:

```text
catalog/knowledge-packs/data/primitive-variation-dimension-atlas/
```

This keeps base primitives compact while allowing dimensions for algorithms,
data structures, storage, SQL dialects, runtime stacks, source surfaces,
industries, regions, roles, proof policies, and materialization rules.

## Agent Graph Path Mixtures

After a specialized primitive is selected, choose an agent graph path mixture
for planning, source retrieval, schema mapping, execution, troubleshooting,
proof, and review. Read
`docs/codex/primitive-agent-graph-path-mixtures-handoff.md`.

The seed pack is:

```text
catalog/knowledge-packs/data/primitive-agent-graph-path-mixtures/
```

Use mixtures when the request needs:

- more than one route variant, such as cheap, balanced, and quality;
- reproducible troubleshooting before backtracking;
- country or jurisdiction-specific source requirements;
- industry-specific proof gates;
- human review for regulated, safety-sensitive, or high-impact outputs.

Validate the pack with:

```bash
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
```

## Example Composition

The request:

```text
Sync Shopify orders to an ERP queue worker with refunds, payment linkage, and
audit receipts.
```

should retrieve:

```text
grp:base.external_object_sync
obj:canonical.order
obj:canonical.customer
obj:canonical.payment
overlay:shopify.order
mut:platform_field_map
mut:platform_pagination_expand
mut:industry_money_reconcile
mut:platform_idempotency_key
neg:shopify.order_refund_not_silent_drop
```

and compile:

```text
grp:shopify.retail.order_to_erp_sync
```

Only drill into official docs or source slices when the contract, field map,
auth scope, version, or proof fixture is missing.

## Registry Shapes

Canonical object rows answer:

```text
What stable business object is this platform object trying to become?
```

Platform overlay rows answer:

```text
What does this platform call the object, which fields map roughly, what needs
source verification, and which pitfalls repeat?
```

Specialized primitive rows answer:

```text
Which base primitive, canonical objects, overlays, runtime target, mutators,
proof requirements, and negative-memory records should be assembled for this
specific workflow?
```

Negative-memory rows answer:

```text
What has gone wrong before, and which deterministic mutator or proof gate
prevents repeating it?
```

## Expansion Commands

Use these as handoff prompts for model lanes. Keep the output as candidate
JSONL, not promoted primitives.

### Create Platform Pack

```text
Create a specialized primitive pack for {platform}. Mine official API docs,
object schemas, webhooks, auth scopes, pagination behavior, common workflows,
sandbox or fixture options, and known pitfalls. Output platform overlays,
specialized primitive candidates, mutators, proof requirements, and negative
memory. Do not copy restricted source. Keep all IDs version-free and set
candidate=true, serves_truth=false.
```

### Create Industry Pack

```text
Create an industry primitive pack for {industry}. Identify common business
objects, workflows, schema standards, source systems, compliance constraints,
reports, and proof policies. Emit specialized primitive groups with compact
visible edges and hidden member edges. Model industry-specific terms as leaf
instances, not new top-level taxonomy entries.
```

### Create Schema Pack

```text
Create a schema primitive pack for {schema_standard}. Extract resource types,
required fields, common transforms, validation rules, canonical mappings,
versioning issues, and proof fixtures. Emit source-backed candidate primitives
only after source_ref_resolver and license_gate receipts exist.
```

### Create Website Extractor Pack

```text
Create browser extraction primitives for common {website_type} websites. Use
canonical business-object schemas or public structured-data schemas as targets.
Include selector or source-span proof, screenshot receipts, field validation,
and negative memory for missing currency, stale markup, and ambiguous identity.
```

## Generation Matrices

Scale comes from crossing small, governed dimensions:

```text
platform x business_object x workflow
industry x canonical_object x proof_policy
schema_standard x transformation x runtime_shape
website_type x extraction_target x receipt_policy
```

Do not materialize every combination blindly. Rank by demand evidence,
available source refs, proof feasibility, and repeated user tasks.

## Promotion Gates

Before any customized row can serve truth, require:

- source refs resolved to public or authorized references;
- license review receipt;
- validated input and output edge contracts;
- declared effects and privacy boundary;
- fixture, contract, idempotency, and side-effect tests where relevant;
- runtime wrapper proof receipt;
- negative-memory retrieval smoke test;
- benchmark hook or scorecard when the row is used for AIDevObserver evals.

## Validation

Run the focused checker after editing this pack:

```bash
python3 scripts/check_primitive_customization_overlays.py --self-test
```

Also keep the broader primitive gates green when wiring this into other
registries:

```bash
python3 scripts/check_handoff_docs_freshness.py --self-test
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_portfolio_dependency_law.py --self-test
```
