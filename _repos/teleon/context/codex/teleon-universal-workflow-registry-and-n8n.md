# Teleon Universal Workflow Registry And n8n Ingestion

This document memorializes the next expansion of the Teleon primitive/compiler architecture:
external workflow systems should become first-class registry sources.

The immediate target is n8n because n8n workflows are already graph-shaped, JSON-exportable, source-control
friendly, and built around reusable nodes. n8n is not the only target, but it is a good first acquisition
surface for workflow primitives, workflow templates, connector patterns, trigger patterns, and side-effect
profiles.

## Core Thesis

```text
Teleon should ingest workflow systems as candidate graph evidence.
Teleon should not make any external workflow format its canonical IR.
```

n8n, ComfyUI, Zapier-style automation, Make-style scenarios, GitHub Actions, Argo Workflows, Airflow DAGs,
Temporal workflows, Dagster assets, Flyte workflows, CWL/WDL/Nextflow pipelines, and cloud-native job graphs
can all be treated as workflow-source surfaces.

The common path is:

```text
external workflow artifact
  -> source-specific parser
  -> credential/secret redaction
  -> normalized workflow graph
  -> candidate WorkflowCard / NodeCard / EdgeCard records
  -> compact generated views
  -> CandidateBundle
  -> deterministic compiler
  -> PlanLock
  -> proof/promotion
```

## Research And Product Anchors

- [n8n export/import docs](https://docs.n8n.io/workflows/export-import/) say n8n stores workflows as JSON and
  supports JSON export/import through UI, URL, file, and command-line paths. They also warn that exported JSON
  can include credential names/IDs and that HTTP Request nodes imported from cURL may contain authentication
  headers.
- [n8n connections docs](https://docs.n8n.io/workflows/components/connections/) define connections as links
  between nodes that route data from an output to an input. That maps directly to Teleon graph edges.
- [n8n public REST API docs](https://docs.n8n.io/api/) describe programmatic access for many GUI-like tasks
  and name the CLI as useful for command-line automation, CI/CD, and AI-agent integration.
- [n8n templates docs](https://docs.n8n.io/workflows/templates/) describe workflow templates and self-hosted
  template-library customization. This is useful for harvesting reusable workflow patterns.
- [n8n source-control docs](https://docs.n8n.io/source-control-environments/understand/git/) state that n8n
  can push workflows/tags plus credential and variable stubs to Git, and pull them back into n8n. This gives
  Teleon a cleaner acquisition path than scraping UI pages when the user controls the instance.
- [Compiled AI](https://arxiv.org/abs/2604.05150), [LLMCompiler](https://arxiv.org/abs/2312.04511), and
  [LLM+P](https://arxiv.org/abs/2304.11477) remain the conceptual backbone: model output proposes a formal
  plan, deterministic tooling validates and executes it.
- [ComfyUI workflow JSON](https://docs.comfy.org/specs/workflow_json) and
  [ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes) are the media-graph
  analogues: another graph runtime whose native JSON should be an adapter target, not the registry truth.

## External Workflow Source Families

Teleon should support multiple source families under one contract.

```text
workflow_source.n8n_export_json
workflow_source.n8n_template_library
workflow_source.n8n_git_source_control
workflow_source.n8n_public_api_owned_instance
workflow_source.comfyui_workflow_json
workflow_source.github_actions_yaml
workflow_source.argo_workflow_yaml
workflow_source.airflow_dag_python
workflow_source.temporal_workflow_python
workflow_source.dagster_asset_graph
workflow_source.flyte_workflow
workflow_source.cwl
workflow_source.wdl
workflow_source.nextflow
```

Each source family needs:

```text
parser
normalizer
redactor
node classifier
edge extractor
secret detector
side-effect detector
runtime adapter
license/provenance policy
compact view renderer
promotion proof strategy
```

## n8n As Candidate Graph Evidence

n8n workflow JSON is valuable because it usually contains:

```text
workflow metadata
nodes
node type names
node parameters
node positions
connections
credentials references
expressions
settings
tags
static data or execution hints in some exports
```

Teleon should distill it into:

```text
ExternalWorkflowCard
ExternalNodeCard
ExternalEdgeCard
CredentialUseRecord
ExpressionRecord
SideEffectProfile
DataShapeProfile
WorkflowPatternRecord
TeleonLiftPlan
```

The native n8n artifact remains stored as an immutable source artifact. The registry truth is the normalized
Teleon record set derived from it.

## n8n Ingestion Pipeline

```text
acquire_workflow_json
  -> validate_json_shape
  -> redact_credentials_and_headers
  -> normalize_workflow_identity
  -> extract_nodes
  -> extract_connections
  -> classify_triggers
  -> classify_side_effects
  -> classify_data_shapes
  -> extract_expressions
  -> detect_dynamic_code_or_unbounded_http
  -> emit_candidate_workflow_cards
  -> emit_compact_llm_views
  -> build_search_and_blocking_indexes
  -> store_source_artifact_hash
  -> mark serves_truth=false
```

All imported n8n workflows start as candidate evidence. They cannot serve truth until proof/promotion.

## n8n Record Mapping

| n8n surface | Teleon record | Notes |
| --- | --- | --- |
| workflow JSON | `ExternalWorkflowCard` | Canonical source artifact hash, source URL/path, license/provenance, tag/category summary |
| node | `ExternalNodeCard` or candidate `PrimitiveCard` | Node type, operation, params, credentials, side effects, input/output shape hints |
| connection | `ExternalEdgeCard` | From-node/output to to-node/input; maps to graph edge candidates |
| credential ref | `CredentialUseRecord` + `SecretRef` | Never preserve real credential values; redact names if sensitive |
| expression | `ExpressionRecord` | Useful for data mapping; high-risk if complex or source-dependent |
| Code node | `DynamicCodeSurface` | Candidate only; requires sandbox and review before promotion |
| HTTP Request node | `ExternalApiOperationCandidate` | Must detect method, host, auth/header risk, rate limits, secrets |
| Webhook/Schedule trigger | `TriggerPrimitiveCandidate` | Runtime event source, not ordinary transform |
| Execute Workflow node | `CompositeWorkflowReference` | Sub-workflow edge; useful for composite primitive discovery |
| Error workflow | `FailureRouteRecord` | Maps to compensation/retry/failure handling |

## Candidate ExternalWorkflowCard

```yaml
record_type: external_workflow_card
schema_version: external_workflow_card.v0
serves_truth: false

identity:
  uid: extwf_01j...
  source_family: n8n_export_json
  source_slug: lead-intake-enrich-and-crm-sync
  source_version: observed
  source_aliases:
    - n8n.workflow.lead_intake_enrich_crm_sync

source:
  artifact_uri: artifact://source/n8n/lead-intake.json
  artifact_sha256: sha256:...
  acquired_from: https://example.invalid/workflow.json
  acquired_at: "2026-06-28T00:00:00Z"
  license_status: unknown_or_user_owned

graph:
  node_count: 9
  edge_count: 10
  trigger_nodes:
    - Webhook
  side_effect_nodes:
    - HTTP Request
    - HubSpot
    - Send Email
  dynamic_nodes:
    - Code

contracts:
  input_profile:
    kind: WebhookPayload
    confidence: inferred
  output_profile:
    kind: CRMUpdateReceipt
    confidence: inferred

policy:
  credential_redaction: required
  dynamic_code_review: required
  external_side_effect_review: required
  can_auto_execute: false

views:
  compact: "W7 lead_intake WebhookPayload>CRMUpdateReceipt nodes:9 fx:webhook,http,crm,email risk:H tr:C"
```

## Candidate ExternalNodeCard

```yaml
record_type: external_node_card
schema_version: external_node_card.v0
serves_truth: false

identity:
  uid: extnode_01j...
  source_family: n8n
  node_type: n8n-nodes-base.httpRequest
  observed_name: Enrich Company

surface:
  workflow_uid: extwf_01j...
  node_id: node_4
  parameters_digest: sha256:...
  credential_ref_present: true

contracts:
  input_profile:
    kind: JsonItem
    fields:
      - email
      - company_domain
  output_profile:
    kind: HttpResponse
    fields:
      - statusCode
      - body

effects:
  - network_write_or_read
  - external_api_call

memory:
  input_policy: inline_or_artifact_ref
  output_policy: inline_or_artifact_ref

risk:
  credential_exposure: possible
  auth_header_exposure: possible
  replay_safety: unknown
  promotion_review: required

views:
  compact: "N4 http_enrich JsonItem>HttpResponse fx:net api cred risk:H tr:C"
```

## Credential And Secret Law

n8n is especially useful, but exported workflow JSON is not automatically safe to publish or index.

Hard rules:

```text
Never store raw credential values.
Never preserve authentication headers from imported cURL-derived HTTP Request nodes.
Credential names may be sensitive; store a redacted stable digest and optional owner-approved label.
All credential references become SecretRef or CredentialUseRecord.
Any workflow containing credentials, auth headers, tokens, basic auth, OAuth settings, private hosts, or webhook secrets remains candidate-only.
```

## Dynamic Code And Expression Law

n8n workflows often use expressions and Code nodes. Treat them as power surfaces, not trusted primitives.

```text
simple field expression:
  candidate data binding; can be normalized into a FieldMappingPrimitive after proof

complex expression:
  ExpressionRecord; requires deterministic replay fixture before promotion

Code node:
  DynamicCodeSurface; sandbox proof + human review required

HTTP Request with expression-built URL:
  ExternalApiOperationCandidate; SSRF and egress policy required
```

The compiler should reject automatic execution when dynamic code or unbounded egress is present.

## Workflow Pattern Distillation

The main value of n8n ingestion is not executing arbitrary imported workflows. The main value is mining
reusable workflow patterns.

Examples:

```text
webhook -> validate payload -> enrich record -> write CRM -> notify
schedule -> fetch API -> transform rows -> append spreadsheet
email trigger -> parse attachment -> extract records -> route by condition
form trigger -> classify request -> create ticket -> send acknowledgement
rss trigger -> summarize item -> post to channel
```

Each recurring chain can become:

```text
WorkflowPatternRecord
PipelineTemplateCandidate
CompositePrimitiveCandidate
CandidateBundle exemplar
negative memory if historically failing
```

## Lifting n8n To Teleon

There are three lift levels.

```text
L0 source artifact:
  store n8n JSON, hash, source, license/provenance, redaction report

L1 candidate graph:
  normalized nodes/edges, side effects, credentials, expressions, compact views

L2 Teleon candidate plan:
  map n8n nodes to Teleon primitive candidates, infer contracts, insert gates

L3 executable PlanLock:
  only after contracts, secrets, egress, policy, runtime placement, and proof pass

L4 promoted composite:
  only after repeated proofed executions or human promotion review
```

Promotion must not be skipped. n8n workflows are strong examples; they are not automatically trusted code.

## n8n CandidateBundle

For LLM planning, render the n8n-derived graph as compact aliases, not full workflow JSON.

```text
Q build_lead_intake_crm_sync
O CRMUpdateReceipt
T0 workflow_pattern.webhook_enrich_write_notify

S0 trigger WebhookPayload>JsonItem req:redact
S1 validate JsonItem>ValidatedLead gate
S2 enrich ValidatedLead>CompanyProfile fx:net
S3 write ValidatedLead+CompanyProfile>CRMReceipt fx:crm write
S4 notify CRMReceipt>EmailReceipt fx:email

C0.0 n8n_webhook WebhookPayload>JsonItem fx:webhook tr:C
C1.0 n8n_if_required JsonItem>ValidatedLead gate tr:C
C2.0 http_enrich ValidatedLead>CompanyProfile fx:net cred tr:C
C3.0 hubspot_create ValidatedLead+CompanyProfile>CRMReceipt fx:crm write cred tr:C
C4.0 send_email CRMReceipt>EmailReceipt fx:email cred tr:C
```

LLM output should stay compact:

```json
{"v":1,"p":"dense","t":0,"b":[0,0,0,0,0],"r":[],"g":[]}
```

The compiler then decides whether the plan can compile or must remain a candidate/gap record.

## Remix Tools For Workflow Imports

External workflow graphs create useful deterministic remixes.

```text
credential_ref_redactor
auth_header_redactor
node_type_alias_mapper
field_expression_to_mapping
http_request_to_api_operation
webhook_to_trigger_primitive
schedule_to_trigger_primitive
code_node_to_dynamic_code_surface
subworkflow_to_composite_reference
side_effect_gate_inserter
egress_policy_inserter
idempotency_wrapper
retry_wrapper
artifact_ref_wrapper
schema_gate_inserter
```

Every remix creates a `VariationRecord` with proof obligations and `serves_truth=false`.

## n8n Registry Contracts

Add these contract families:

```text
external_workflow_source_contract
external_workflow_card
external_node_card
external_edge_card
workflow_pattern_record
workflow_distillation_manifest
credential_use_record
expression_record
dynamic_code_surface
teleon_lift_plan
n8n_import_redaction_report
n8n_candidate_bundle
n8n_compiler_gap_record
```

Required fields for every n8n-derived workflow record:

```text
record_type
schema_version
source_family
source_artifact_hash
source_license_or_owner_status
redaction_status
node_count
edge_count
trigger_profile
side_effect_profile
credential_profile
dynamic_code_profile
input_profile
output_profile
compact_view
candidate=true
serves_truth=false
```

## Compiler Checks

For n8n-derived candidates, the compiler must check:

```text
workflow JSON parsed successfully
credential material redacted
auth headers redacted
private URLs and private hosts flagged
node types recognized or quarantined
connections form a valid graph
trigger nodes mapped to runtime event sources
side-effecting nodes appear after required gates
Code nodes are sandboxed or rejected
expressions are either normalized or quarantined
data shape compatibility is inferred or explicitly unknown
secrets are SecretRef only
binary payloads are ArtifactRef only
external API calls have egress policy
idempotency exists for write/send/publish effects
source license/ownership allows storage and reuse
```

## Benchmark Slice

First benchmark:

```text
n8n JSON workflow -> Teleon candidate graph -> compact views -> PlanDelta -> compile/reject report
```

Use three fixtures:

```text
safe_fixture:
  webhook -> validate -> transform -> emit local artifact

credential_fixture:
  webhook -> HTTP Request with credential ref -> CRM write -> email

dynamic_fixture:
  schedule -> HTTP Request with expression-built URL -> Code node -> write side effect
```

Acceptance:

```text
safe_fixture compiles to candidate PlanLock with serves_truth=false
credential_fixture redacts and refuses auto-execution until secret policy exists
dynamic_fixture produces DynamicCodeSurface and compiler gap records
compact views use fewer tokens than raw JSON
all source artifacts are hashed
all outputs remain candidate-only
```

## Final Position

Teleon should treat n8n workflows as a high-volume source of workflow primitives, graph patterns, trigger
patterns, connector surfaces, side-effect profiles, and composite candidates.

The strongest route is:

```text
scrape/import n8n workflows
  -> redact
  -> normalize
  -> distill graph records
  -> index compact views
  -> use as CandidateBundle evidence
  -> compile only through Teleon contracts
  -> promote only after proof
```

n8n becomes one of many external workflow registries feeding Teleon. It is a rich acquisition surface, not
the runtime truth boundary.
