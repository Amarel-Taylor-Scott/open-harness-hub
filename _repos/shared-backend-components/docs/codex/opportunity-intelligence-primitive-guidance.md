# Opportunity Intelligence Primitive Guidance

Last updated: 2026-06-30

This memo expands the Primitive Database Agent Brief into an opportunity-intelligence mining plan. It focuses on official opportunity feeds, taxonomy sources, API contracts, proof receipts, and primitive groups that can feed a high-volume primitive factory without promoting unverified rows.

The operating rule is unchanged:

```text
candidate=true
serves_truth=false
```

until source references, license/policy review, contracts, side effects, fixture tests, and promotion receipts exist.

## What Changes

The earlier broad link catalogs are useful for discovery, but opportunity intelligence needs a stricter graph:

```text
official source adapter
  -> source observation
  -> normalized opportunity record
  -> taxonomy and eligibility signals
  -> deadline and market signals
  -> review packet
  -> proof receipt
  -> candidate primitive or primitive group
```

This is the opportunity-intelligence graph. It keeps facts traceable to official source surfaces and keeps every generated primitive as a candidate until promotion.

## Companion Files

- `catalog/knowledge-packs/data/opportunity-intelligence-source-map/sources.jsonl`
  Official-first source map for APIs, taxonomies, schema standards, lineage, and supply-chain proof sources.
- `data/dev-intel/aidevobserver_edge_foundry/opportunity_intelligence_group_candidates.jsonl`
  Candidate primitive-group rows with visible input/output edges, hidden member edges, proof requirements, blockers, and source refs.
- `scripts/check_opportunity_intelligence_guidance.py`
  Local structural checker for the source map, group candidates, and this memo.

## Source-Backed Surfaces

Use official surfaces first. The initial map is intentionally small because the value comes from adapters and proof gates, not from hand-maintaining thousands of links.

High-priority opportunity feeds:

- USAJOBS Search API: https://developer.usajobs.gov/api-reference/get-api-search
- USAJOBS API reference and code lists: https://developer.usajobs.gov/api-reference/
- SAM.gov Contract Opportunities Public API: https://open.gsa.gov/api/get-opportunities-public-api/
- USAspending API: https://api.usaspending.gov/docs/
- Grants.gov API: https://www.grants.gov/api
- Simpler.Grants.gov developer resources: https://simpler.grants.gov/developers
- Data.gov Catalog API: https://resources.data.gov/catalog-api/

High-priority enrichment taxonomies:

- Census NAICS: https://www.census.gov/naics/
- Acquisition.gov PSC Manual: https://www.acquisition.gov/psc-manual
- SBA Table of Size Standards: https://www.sba.gov/document/support-table-size-standards
- BLS Standard Occupational Classification: https://www.bls.gov/soc/
- O*NET Web Services: https://services.onetcenter.org/

Contract and proof vocabulary:

- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- JSON Schema Specification: https://json-schema.org/specification
- Frictionless Table Schema: https://specs.frictionlessdata.io/table-schema/
- OpenLineage Specification: https://openlineage.io/docs/spec/
- SPDX Specifications: https://spdx.dev/use/specifications/
- SLSA Specification: https://slsa.dev/spec/v1.1/
- CycloneDX Specification: https://cyclonedx.org/specification/overview/
- Sigstore docs: https://docs.sigstore.dev/
- in-toto attestations: https://in-toto.io/attestation/

Implementation and package mining surfaces:

- GitHub REST API: https://docs.github.com/en/rest
- PyPI JSON API: https://docs.pypi.org/api/json/

## Design Principle: Separate Source Adapters

Do not make one generic government adapter. Separate adapters by source surface and contract:

```text
USAJOBS search adapter
USAJOBS code-list adapter
SAM.gov contract opportunities adapter
SAM.gov attachment manifest adapter
Grants.gov opportunity adapter
USAspending award-history adapter
Data.gov catalog adapter
NAICS lookup adapter
PSC lookup adapter
SBA size-standard lookup adapter
SOC/O*NET enrichment adapter
```

Each adapter should emit a source observation envelope:

```json
{
  "source_ref_id": "sam_opportunities_api",
  "source_url": "https://open.gsa.gov/api/get-opportunities-public-api/",
  "retrieved_at": "2026-06-30T00:00:00Z",
  "request_envelope": {},
  "response_metadata": {},
  "raw_record_ref": "artifact://...",
  "license_policy_notes": [],
  "candidate": true,
  "serves_truth": false
}
```

This keeps network fetching, parsing, enrichment, and ranking as separate proofable edges.

## Canonical Domain Objects

Use stable object names so factory output dedupes cleanly:

```text
OpportunitySource
SourceObservation
FederalJobOpportunity
ContractOpportunity
GrantOpportunity
DatasetOpportunity
OpportunityAttachmentManifest
TaxonomyCode
NaicsCode
PscCode
SocCode
SizeStandardSignal
EligibilitySignal
DeadlineSignal
SpendMarketSignal
OpportunityEvidenceBundle
BidNoBidDecisionPacket
SourceEvidenceReceipt
PromotionGateScorecard
SupplyChainProofPacket
```

Keep raw source fields under observation artifacts. Normalized records should point back to them rather than copying everything into every candidate row.

## Primitive Group Shape

Every useful opportunity workflow should become a primitive group when it hides three or more repeated steps behind one useful edge.

Example:

```text
OpportunityEvidenceBundle+BidNoBidPolicy -> BidNoBidDecisionPacket+ReviewReceipt
```

Hidden member edges:

```text
OpportunityEvidenceBundle -> RequirementSignalBatch
RequirementSignalBatch+BidNoBidPolicy -> FitGapSignalBatch
FitGapSignalBatch -> RiskAndDeadlineSignalBatch
RiskAndDeadlineSignalBatch -> BidNoBidDecisionPacket
```

The visible input edge and visible output edge are what retrieval should show by default. The hidden member edges are for drill-down, testing, and implementation.

Representative candidate groups now modeled:

- `grp:opportunity.sam_contract_opportunity_ingestion@candidate`
- `grp:opportunity.grants_discovery_ranking@candidate`
- `grp:opportunity.procurement_taxonomy_enrichment@candidate`
- `grp:opportunity.bid_no_bid_packet@candidate`
- `grp:opportunity.openapi_operation_to_primitive@candidate`
- `grp:opportunity.supply_chain_proof_packet@candidate`

## Factory Lanes

### Lane 1: Official Feed Ingestion

Goal: source-backed opportunity records with stable receipts.

Inputs:

```text
USAJobsSearchQuery+SourcePolicy
SamOpportunitySearchQuery+SourcePolicy
GrantSearchIntent+EligibilityPolicy
DatasetDiscoveryIntent+CatalogPolicy
```

Outputs:

```text
FederalJobOpportunityBatch+SourceEvidenceReceipt
ContractOpportunityBatch+SourceEvidenceReceipt
RankedGrantOpportunityDigest+EvidenceReceipt
RankedDatasetSourceDigest+DistributionReceipt
```

Proof gates:

```text
API fixture response
pagination fixture
required field validation
source timestamp receipt
license policy review
candidate boundary gate
```

### Lane 2: Taxonomy Enrichment

Goal: attach reviewable labels and codes without claiming final classification truth.

Sources:

```text
NAICS
PSC
SBA size standards
SOC
O*NET
```

Outputs:

```text
TaxonomyEnrichedOpportunityBatch+ClassificationEvidenceReceipt
SkillMappedOpportunityBatch+RoleEvidenceReceipt
```

Reject conditions:

```text
missing taxonomy version
inferred code without confidence receipt
size standard without effective date
role/skill mapping without source taxonomy link
```

### Lane 3: Deadline and Market Signals

Goal: turn records into reviewable action signals.

Signals:

```text
deadline date
timezone or missing timezone
days to deadline
notice status
set-aside
agency
NAICS/PSC
past award history
vendor concentration
fit/gap notes
```

Outputs:

```text
RankedDeadlineSignalDigest+CalendarRiskReceipt
AwardHistoryMarketSignalPack+EvidenceReceipt
```

These outputs must be labeled as heuristic candidates. They are not source truth.

### Lane 4: Review Packet Groups

Goal: collapse many source and signal edges into a compact decision-support packet.

Primary group:

```text
OpportunityEvidenceBundle+BidNoBidPolicy -> BidNoBidDecisionPacket+ReviewReceipt
```

This is one of the highest-value group rows because it hides many repeated internal steps while giving an agent a useful reusable capability.

### Lane 5: Contract and Proof Infrastructure

Goal: generate validation and promotion infrastructure around the rows.

Key groups:

```text
OpenApiOperationObject+ToolPolicy -> ApiEndpointPrimitiveCandidate+ContractReceipt
SampleOpportunityRecords+SchemaPolicy -> OpportunityContractSchemaSet+FixturePlan
PrimitiveFactoryRunEventBatch+LineagePolicy -> OpenLineageCompatibleReceiptBatch+RunEvidenceGraph
ImplementationBackedPrimitiveCandidate+SupplyChainPolicy -> SupplyChainProofPacket+PromotionRiskSignal
PrimitiveGroupCandidate+PromotionGatePolicy -> PromotionGateScorecard+ReviewerQueueReceipt
```

This lane turns the source map into a durable primitive economy. It is how a high-volume candidate factory avoids becoming a pile of untestable rows.

## Candidate Scoring

Use cheap deterministic scoring before expensive model review:

```text
source authority score
+ contract completeness score
+ source-reference density score
+ taxonomy version score
+ fixture coverage score
+ side-effect clarity score
+ dedupe novelty score
+ group reuse score
- license uncertainty penalty
- missing-deadline penalty
- missing-test penalty
- copied-content penalty
```

Do not let high semantic relevance override missing proof. A great-looking candidate with no source ref stays low priority.

## Dedupe Keys

At 20,000+ candidates/day, dedupe is part of correctness:

```text
exact primitive_id
visible input edge + visible output edge
normalized title
source_ref_id + source native id
taxonomy code + source native id
content hash of normalized record
semantic cluster of blackbox.does
hidden member edge set hash
```

Conflict preservation matters. If two feeds disagree about a deadline or code, preserve both values and emit a conflict receipt.

## Promotion Rules

No candidate moves beyond review until it has:

```text
source_ref_resolution
license_policy_review
input_contract_test
output_contract_test
side_effect_audit
candidate_boundary_gate
fixture or property test
runtime profile
promotion blocker review
```

Extra gates for implementation-backed primitives:

```text
dependency inventory
license identifier normalization
vulnerability signal
build provenance signal
signature or attestation signal when available
unit or smoke test
```

Promotion should write a separate receipt. Never mutate the original candidate row to erase its discovery history.

## Agent Roles

Use narrow agents with strict JSONL outputs:

```text
SourceMapCuratorAgent
OfficialApiAdapterAgent
SourceObservationNormalizerAgent
ContractInferenceAgent
TaxonomyEnrichmentAgent
DeadlineSignalAgent
MarketSignalAgent
GroupFactoryAgent
ProofPlanAgent
DedupClusterAgent
PromotionGateAgent
RegistryWriterAgent
```

Failure mode should be explicit:

```json
{
  "status": "rejected",
  "reason": "missing_source_ref",
  "candidate": true,
  "serves_truth": false
}
```

## Model-Parallel Execution

Codex can orchestrate the local repo edits, validation, and registry writes while cheap parallel model calls generate or critique candidate rows. This session confirmed the direct Ollama Cloud HTTP path with the existing `OLLAMA_API_KEY`:

```text
POST https://ollama.com/api/generate
model=kimi-k2.7-code -> KIMI_OK
model=glm-5.2 -> GLM_OK
```

The local Ollama daemon was not running, so `ollama list` and `ollama ps` could not connect to `localhost:11434`. For this workspace, use the cloud API path unless a local `ollama serve` process is intentionally started.

Recommended split:

```text
Codex
  orchestrates repo edits, scripts, checker failures, final curation, and commits.

Kimi
  drafts high-volume primitive/group candidates from source observations and route plans.

GLM
  critiques contracts, finds missing proof gates, proposes hidden member edges, and checks taxonomy fit.

Deterministic scripts
  validate JSONL, dedupe, enforce candidate boundaries, score proof completeness, and reject weak rows.
```

Parallel loop:

```text
1. Source miner writes SourceObservation JSONL.
2. Kimi generates candidate primitive/group cards from observations.
3. GLM reviews candidate cards for edge clarity, proof gaps, and duplicate shape.
4. Deterministic validators reject schema errors and boundary violations.
5. Codex applies accepted artifacts to the repo and runs checkers/tests.
```

Do not let any model, including Kimi or GLM, mark `serves_truth=true`. Their role is candidate generation and critique. Promotion remains a deterministic plus human-review gate.

## Implementation Backlog

Phase 1: source and contract foundation

- Add local fixtures for USAJOBS Search, SAM.gov opportunities, Grants.gov, USAspending, and Data.gov catalog responses.
- Build one adapter per official API surface.
- Emit `SourceObservation` JSONL with request envelopes, response metadata, raw artifact refs, and source timestamps.
- Generate JSON Schema contracts for normalized opportunity records.

Phase 2: enrichment and scoring

- Add NAICS, PSC, SBA size standards, SOC, and O*NET lookup snapshots.
- Build taxonomy version receipts.
- Build deadline normalization and ambiguity receipts.
- Build award-history market-signal extraction from USAspending.

Phase 3: primitive groups

- Materialize candidate group cards from repeated routes.
- Add group-level fixture tests for visible edges.
- Keep hidden member edges available for drill-down and proof.
- Add ranking for group reuse value so high-utility groups rise above tiny one-off primitives.

Phase 4: proof and promotion

- Attach OpenLineage-compatible run receipts to factory stages.
- Attach SPDX/CycloneDX/SLSA/Sigstore/in-toto evidence where implementation-backed packages are involved.
- Add a reviewer queue that sorts by proof completeness, source authority, and reuse value.
- Promote slowly. Search broadly.

## Prompt Template

Use this when asking an agent to mine a source:

```text
Mine this official source for reusable opportunity-intelligence primitive candidates.

Extract source-backed capabilities only.
For each candidate emit JSONL with:
- primitive_id
- kind
- title
- input_edge
- output_edge
- contract
- group_contract.visible_input_edge
- group_contract.visible_output_edge
- group_contract.hidden_member_edges
- blackbox.does
- effects
- source_ref_ids
- source_refs
- edge_mutation_options
- proof_requirements
- promotion_blockers
- candidate=true
- serves_truth=false

Prefer primitive groups when three or more internal steps form a repeated workflow.
Do not copy restricted source content.
Do not mark anything as promoted truth.
```

## Practical Takeaway

The goal is not 20,000 trusted primitives per day. The goal is a factory that can create many source-linked candidates, reject weak rows cheaply, cluster near-duplicates, and promote a small number of durable reusable groups.

For opportunity intelligence, the best near-term ROI is:

```text
official adapters
+ taxonomy enrichment
+ deadline and market signals
+ compact review packet groups
+ rigorous proof receipts
```

That gives agents reusable capability without hiding uncertainty or source obligations.
