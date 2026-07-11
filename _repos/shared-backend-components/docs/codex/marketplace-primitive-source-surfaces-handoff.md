# Marketplace Primitive Source Surfaces Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes mining existing
marketplaces, registries, package indexes, model hubs, workflow libraries, and
cloud catalogs for primitive candidates.

Status: generated seed registry. These rows are candidate source-surface
artifacts, not promoted truth.

## Core Thesis

The world already contains many primitive-like blocks:

```text
MCP tools
OpenAPI operations
Terraform modules
GitHub Actions
serverless apps
workflow templates
Helm charts
Kubernetes Operators
container images
model hub assets
data products
package APIs
enterprise app listings
cloud marketplace products
```

They usually do not expose clean AI-readable primitive contracts. The adapter
layer should translate them into:

```text
input edge
output edge
blackbox behavior
effects
runtime target
auth or permission requirements
source refs
proof requirements
deployment wrapper
receipt shape
negative memory
```

## Seed Pack

The generated pack is:

```text
catalog/knowledge-packs/data/marketplace-primitive-source-surfaces/
```

It contains:

- `marketplace_source_surfaces.jsonl` with 20 ranked source surfaces;
- `marketplace_factory_patterns.jsonl` with 8 extraction patterns;
- `example_marketplace_primitive_cards.jsonl` with 6 candidate examples;
- `extraction_policy.json` that forbids source-code copying and requires
  contract/effect/runtime/proof extraction.

The generator is:

```bash
python3 scripts/generate_marketplace_primitive_source_surface_pack.py
```

The checker is:

```bash
python3 scripts/check_marketplace_primitive_source_surface_pack.py --self-test
```

## Priority Order

The first source surfaces are intentionally ranked:

```text
1. MCP registry and MCP server catalogs
2. APIs.guru and OpenAPI directories
3. Postman API Network and public collections
4. Terraform Registry
5. Pulumi Registry
6. CDK Construct Hub
7. CloudFormation Registry
8. AWS Serverless Application Repository
9. GitHub Actions Marketplace
10. n8n, Zapier, Make, and Pipedream workflows
```

These are high-value because they already carry tool schemas, API contracts,
deployment parameters, workflow routes, or runtime effects.

## Universal Adapter Output

Every marketplace adapter should emit:

```text
SourceSurfaceCard
MarketplaceListingCard
PrimitiveCandidateSet
PrimitiveGroupCandidateSet
RuntimeWrapperCandidateSet
ProofObligationSet
LicensePolicyReview
DeploymentRecipe
ReceiptSchema
NegativeMemoryHintSet
```

When a marketplace item represents a recurring buyer/user problem, also emit or
link a problem-solution detail record. The compact marketplace primitive card
should say what the listing can do; the detail record should say which problem
it solves, what route should be assembled, what can fail, and what proof is
needed before promotion. See:

```text
docs/codex/primitive-problem-solution-details-handoff.md
```

The extraction policy is strict:

```json
{
  "copy_code": false,
  "extract_contracts": true,
  "extract_effects": true,
  "extract_runtime_targets": true,
  "extract_proof_requirements": true
}
```

## Validation

Run:

```bash
python3 scripts/generate_marketplace_primitive_source_surface_pack.py
python3 scripts/check_marketplace_primitive_source_surface_pack.py --self-test
```
