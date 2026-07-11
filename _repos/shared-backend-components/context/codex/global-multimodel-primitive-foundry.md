# Global Multi-Model Primitive Foundry

**Status:** design contract with offline proof  
**Scope:** OpenHubForAI, Teleon, Baltor, AIDevObserver, AI Done Right, DeterministicBuilds, and future domain surfaces  
**Truth boundary:** models propose candidate evidence. Deterministic gates, proofs, and promotion decide usable truth.

## Purpose

The primitive foundry should not be tied to one product surface. AIDevObserver supplies valuable AI-session reinvention signals, but the source-to-primitive loop is a global platform capability:

```text
source surface
  -> captured source candidate
  -> rights/privacy/source normalization
  -> model-assisted opportunity distillation
  -> cross-model critique
  -> contract authoring
  -> implementation candidate
  -> proof bundle
  -> lifecycle digest/search card/vector row
  -> promotion queue
  -> usable primitive only after proof and approval
```

The design supports Codex, GLM 5.2 through Ollama, Kimi Code 2.7 through Ollama, browser capture tools, and future model/browser lanes without making any one model authoritative.

## Lane Roles

| Lane | Best use | Not allowed to do |
| --- | --- | --- |
| Codex orchestrator | Apply repo patches, wire scripts/docs/tests, run proofs, summarize results. | Promote model output to truth by itself. |
| GLM 5.2 via Ollama | Broad source triage, capability extraction, taxonomy mapping, first-pass contract hypotheses, ranking rationale. | Copy source, emit final implementation, or flip `serves_truth`. |
| Kimi Code 2.7 via Ollama | Code-oriented critique, implementation plans, edge cases, tests, contract mismatch review. | Merge patches or certify proof. |
| Browser capture | Render pages, collect screenshots/HTML digests/clickables/provenance. | Treat captured content as licensed or safe without gates. |
| Deterministic gatekeeper | License/privacy/source gates, contract gates, PlanLock/proof/promotion gates, lifecycle packaging. | Skip human/policy approval for serving truth. |

Model tags are configuration, not code. Use env/provider registry values such as:

```bash
OLLAMA_API_KEY=...
OLLAMA_HOST=https://ollama.com
OH_PRIMITIVE_RESEARCH_MODEL=glm-5.2
OH_PRIMITIVE_CODE_MODEL=kimi-k2.7-code
OH_CHAT_MODEL=glm-5.2
```

The current default model IDs are:

```text
research / planning: glm-5.2
code critique / implementation planning: kimi-k2.7-code
fallback chat: glm-5.2
```

These IDs are deployment settings. Primitive records should reference role
lanes and receipts, not hard-code a model dependency as registry truth.

## Source Acquisition Ways To Expand

Use many source surfaces, but keep them rights-aware and metadata-first until gates pass.

- Package registries: PyPI, npm, crates.io, Maven, Go, RubyGems, Docker Hub metadata.
- Workflow registries: GitHub Actions, n8n templates, Zapier-style public recipes, Terraform Registry, Helm charts.
- Data and ML surfaces: Kaggle competitions/datasets/kernels metadata, Hugging Face datasets/models/spaces metadata, Papers With Code tasks.
- Official documentation: cloud provider docs, framework docs, language stdlib docs, Kubernetes/CNCF docs, browser platform docs.
- Public repo metadata: GitHub/GitLab repo topics, READMEs when license allows, issues/PR labels, examples, tests.
- Developer-session surfaces: opted-in Claude Code/Codex transcripts, Aider histories, SWE-agent/OpenHands trajectories, CI logs.
- Product microsurfaces: onboarding, auth, billing, settings, dashboards, uploads, search, tables, forms, notifications, admin panels, reporting.
- Demand surfaces: DeterministicBuilds votes, bounties, requests, failing repeated LLM skills, accepted AIDevObserver findings.

For third-party sources, default to metadata, links, hashes, short non-copyrightable facts, and generated summaries with attribution. Do not copy raw source or textbook content into public primitive records.

## Model-Assisted Stages

### 1. Source Discovery

Browser/API workers collect:

```text
url, title, publisher, license status, robots/terms status, captured_at,
content_hash, screenshot/artifact refs, outbound links, source kind
```

Output:

```text
source_candidate
```

### 2. Source Normalization

Deterministic gates classify:

```text
public metadata only
license reviewed compatible
first party reviewed
private local only
do not republish
```

This stage redacts secrets and strips raw local paths before any model context is prepared.

### 3. GLM Research Pass

The researcher model gets only normalized, allowed context and existing registry search cards. It returns compact JSON:

```json
{
  "record_type": "primitive_opportunity",
  "label": "csv_schema_validate",
  "capability": ["validation", "data_engineering"],
  "contract_hypothesis": {"input": "TableArtifact+SchemaSpec", "output": "SchemaValidationReport"},
  "effects": [],
  "proof_requirements": ["schema_fixture_pass", "bad_rows_reported"],
  "source_refs": ["source:..."],
  "serves_truth": false
}
```

### 4. Kimi Code Critique Pass

The code model critiques the contract and proposes tests:

```json
{
  "record_type": "primitive_contract_review",
  "contract_changes": [{"field": "input", "from": "TableArtifact", "to": "RawTableArtifact+SchemaSpec"}],
  "edge_cases": ["missing column", "extra column", "bad cast", "null policy"],
  "candidate_tests": ["valid table passes", "missing required column fails"],
  "risk": "medium",
  "serves_truth": false
}
```

### 5. Codex Implementation Pass

Codex may implement or wire a primitive only after the deterministic gatekeeper has a source-backed contract and test plan. The output is still a patch candidate until tests pass.

### 6. Proof and Lifecycle Packaging

The deterministic runtime runs:

```text
schema checks
unit/fixture tests
contract checks
privacy checks
artifact/ref checks
replay/digest checks
license/attribution checks
```

Then the global lifecycle script creates:

```text
primitive_lifecycle_digest
primitive_implementation_backlog
primitive_search_card
primitive_vector_row
manifest
summary
```

Vectors are staging retrieval aids, not promotion.

## Usable Primitive Definition

A primitive becomes usable for planning when it has:

- canonical identity;
- source refs and attribution state;
- input/output contract;
- effects, memory, and cache policy;
- proof requirements;
- deterministic fixtures or proof bundle;
- compact search card;
- vector row for retrieval;
- readiness/trust state;
- explicit `serves_truth=false` until promotion.

It can serve truth only after:

- proof bundle passes;
- license and attribution gate passes;
- privacy/redaction gate passes;
- promotion record is approved;
- `serves_truth` flips through a dedicated gate.

## Consensus Rules

Use multiple models to improve recall, not to decide truth.

- If GLM and Kimi agree on a contract, it still goes through deterministic contract validation.
- If they disagree, log a disagreement record and prefer the safer/narrower contract.
- If either model asks to copy source, disable gates, expose secrets, or mark truth, reject the output.
- If Codex can implement but proof fails, create negative memory and a backlog row.
- If browser capture changes hash, invalidate stale source-backed claims and re-run source normalization.

## Test Strategy

Use offline tests first.

```bash
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/check_ollama_free_limited_compatibility.py --self-test
python3 -m scripts.foundry.model_route
python3 -m scripts.foundry.batch_inference --self-test
```

Core fixture classes:

- clean public metadata source;
- license-unknown source;
- prompt-injection source page;
- source that changes content hash;
- GLM/Kimi contract disagreement;
- unlicensed source-copy attempt;
- primitive implementation that passes tests;
- primitive implementation that fails proof;
- vector row generated before promotion;
- promotion attempt without approval.

Live tests require explicit owner authorization and should write receipts:

```text
provider, model id, prompt hash, source digest, output digest, token/cost estimate, served_by_lane, candidate_only
```

## Config Contract

The current lane contract lives at:

```text
catalog/knowledge-packs/data/global-primitive-foundry/multimodel-lanes.json
```

Proof:

```bash
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
```

The contract proves:

- Codex, GLM/Ollama, Kimi/Ollama, browser capture, and deterministic gatekeeper lanes exist;
- only the deterministic gatekeeper can emit promotion candidates;
- model and browser lanes are candidate-only;
- source-to-promotion stages are ordered;
- license, privacy, contract, replay, vector, and promotion gates are required;
- usable primitives require proof/source/search/vector/promotion fields.

## Next Implementation Slices

1. Add an offline fixture runner that simulates GLM/Kimi JSON outputs and disagreement records.
2. Add a live Ollama route wrapper that records receipts without exposing raw prompts by default.
3. Add a browser source-capture ledger that stores screenshots/HTML digests as artifacts.
4. Add package/workflow registry connectors that emit metadata-only source candidates.
5. Add primitive implementation tickets from lifecycle backlog rows.
6. Add a promotion queue UI that clearly separates candidate, proofed, and promoted primitives.
