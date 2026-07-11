# Primitive Agent Graph Path Mixtures Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes expanding
primitive route portfolios with more varied agent mixtures, troubleshooting,
and country or industry specificity.

Status: execution brief plus seed registry. These rows are candidate route
planning artifacts, not promoted truth.

## Core Move

Customize primitive execution through graph-path mixtures:

```text
task intent
  + primitive candidates
  + specialization overlays
  + agent path family
  + troubleshooting playbook
  + country or industry overlay
  = ranked route portfolio
```

This is different from adding another primitive row. A primitive says what edge
can be transformed. A graph-path mixture says which agent roles, fallback paths,
debug loops, proof gates, and jurisdiction overlays should be used to assemble
and test that transformation.

## Seed Pack

The concrete seed pack is:

```text
catalog/knowledge-packs/data/primitive-agent-graph-path-mixtures/
```

It contains:

- `agent_roles.jsonl` for planner, retriever, schema mapper, browser operator,
  runtime executor, proof auditor, debugger, country-policy resolver, and human
  reviewer roles;
- `path_families.jsonl` for reusable graph shapes;
- `graph_path_mixtures.jsonl` for concrete task portfolios;
- `troubleshooting_playbooks.jsonl` for reproduce, isolate, classify, repair,
  retest, and receipt steps;
- `country_industry_overlays.jsonl` for country or region sensitive route
  deltas.

All rows keep:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

Do not promote a route mixture because it sounds plausible. Promotion requires
source refs, effect declarations, proof receipts, and country or industry
review gates.

## Guardrail Runtime Routes

Cloud-deployed guardrails are route mixtures too. Read
`docs/codex/primitive-cloud-guardrail-runtime-handoff.md` and use:

```text
catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/
```

Treat cloud provider safety products as adapters under a portable primitive
contract. For agentic systems, prefer route mixtures that include tool-call
guards, approval gates, rollback requirements, and decision receipts.

## Path Families

The first seed families are:

```text
pathfam:planner_retriever_tool_exec_proof
pathfam:browser_extract_schema_validate
pathfam:code_patch_test_review
pathfam:incident_diagnose_isolate_repair
pathfam:regulated_intake_verify_human_review
pathfam:country_jurisdiction_fact_ladder
pathfam:multi_model_disagreement_resolve
pathfam:source_adapter_to_primitive_factory
```

Each family has an agent sequence and a fallback policy. The resolver should
rank cheap, balanced, and quality variants before executing.

## Troubleshooting Contract

Every playbook follows the same minimum ladder:

```text
reproduce
isolate
classify
repair or swap
retest
emit receipt
escalate or report NeedsEvidence
```

This matches the existing synthesis discipline:

```bash
PYTHONPATH=. python3 scripts/check_synthesis_discipline.py --self-test
```

Do not backtrack or escalate to a dearer model path before the same-plane
troubleshooting playbook has run.

## Country And Industry Specificity

Country overlays should add source and review requirements, not unsupported
legal conclusions. Good overlay fields are:

```text
country_scope
industry_scope
sensitivity
adds_to_path
proof_requirements
human_review_triggers
source_refs
source_evidence_status
```

Keep `source_refs` empty and
`source_evidence_status=unverified_intake_requires_source_ref_resolution` until
the source resolver has attached official or owner-approved references.

Seed overlays cover examples such as:

```text
US procurement
Philippines overseas-worker recruitment review
EU privacy workflows
UK company registry research
Canada healthcare privacy
India invoice/tax data
Singapore financial compliance
Australia aged-care intake
Brazil and Mexico electronic invoice workflows
Germany workplace privacy
Japan invoice/tax data
```

These are route-planning overlays. They are not legal, tax, medical, or
regulatory advice.

## Example

For a request like:

```text
Review possible Philippines overseas-worker fee overcharge content.
```

the resolver should combine:

```text
pathfam:regulated_intake_verify_human_review
jur:ph.ofw_recruitment
trouble:country_rule_conflict
trouble:source_staleness
trouble:model_disagreement
agent:country_policy_resolver
agent:source_retriever
agent:human_reviewer
agent:proof_auditor
```

and emit a route portfolio with:

```text
cheap route: language/OCR triage plus source-needed receipt
balanced route: official-source resolution plus privacy redaction plus review queue
quality route: destination-country context plus conflict receipt plus evidence packet
```

The output is a review packet and proof receipt, not an autonomous conclusion.

## Resolver Inputs And Outputs

Resolver input:

```text
TaskIntent
+ CandidatePrimitiveSet
+ SpecializationOverlaySet
+ ProjectAffinityProfile
+ CountryScope
+ IndustryScope
+ ProofPolicy
+ BudgetPolicy
```

Resolver output:

```text
RankedRoutePortfolio
+ AgentGraphPath
+ TroubleshootingPlan
+ CountryIndustryOverlaySet
+ ProofObligationSet
+ RuntimePlan
+ SourceEvidenceRequirements
+ NegativeMemoryQueries
```

## Validation

Run:

```bash
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
python3 scripts/check_primitive_customization_overlays.py --self-test
PYTHONPATH=. python3 scripts/check_synthesis_discipline.py --self-test
```

Before using these rows in broader product docs, also run:

```bash
python3 scripts/check_handoff_docs_freshness.py --self-test
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_portfolio_dependency_law.py --self-test
```
