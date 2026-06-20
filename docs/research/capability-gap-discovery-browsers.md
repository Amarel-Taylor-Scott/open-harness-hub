# Capability gap discovery browsers

This internal workflow uses multiple browser/search agents to find areas where out-of-box LLMs are weak, but structured pipelines can create a meaningful capability lift.

The goal is not to scrape broadly. The goal is to discover reusable primitive components and pipeline opportunities where the hub can make LLM systems cheaper, more reliable, more verifiable, or easier to deploy.

## Core Thesis

```text
Pipeline opportunity ~= economic value x data coverage x verifiability x LLM capability gap
```

The browser fleet should prioritize areas where:

- people already collect data, publish tasks, or run competitions.
- current LLMs are inconsistent without retrieval, rules, tools, domain rubrics, or human review.
- deployment is low because workflow complexity, compliance, cost, or integration burden is high.
- a reusable primitive could reduce cost, improve accuracy, improve auditability, or make model switching easier.

## Browser Lanes

| Lane | Primary sources | What to look for |
|---|---|---|
| Dataset scout | Kaggle, Hugging Face datasets, data.gov, sector portals | Repeated data schemas, hard labels, underused datasets, niche domain tasks |
| Paper scout | arXiv, Semantic Scholar, Papers With Code, PubMed, SSRN | New methods, benchmark gaps, failure studies, domain-specific workflows |
| Red-team scout | public red-team events, bug bounty writeups, safety evals, hackathons | Failure modes, attack patterns, unmet guardrail needs, evaluation prompts |
| Low-adoption scout | industry forums, procurement docs, professional associations, public RFPs | Workflows with clear value but low LLM deployment |
| Cost scout | model pricing pages, cloud pricing docs, vector DB pricing, inference benchmarks | Places where routing, caching, local models, or browser models reduce cost |
| Deployment scout | GitHub issues, Stack Overflow, cloud docs, MCP/tool registries | Recurring setup pain, auth, runtime, container, Terraform, observability gaps |

## Agent Roles

Each browser should run with a narrow role and write structured findings:

- `dataset_scout`: finds datasets and competitions that imply repeatable tasks.
- `paper_scout`: finds papers that describe capability gaps, benchmarks, or new pipeline methods.
- `red_team_scout`: finds adversarial cases and safety failures that can become eval/rule packs.
- `deployment_scout`: finds where teams struggle to run, monitor, or swap LLM systems.
- `cost_scout`: finds cost-sensitive workflows and possible routing/cache/local-first savings.
- `primitive_scout`: maps findings to candidate primitives such as routers, gates, normalizers, evaluators, or runtime emitters.

## Finding Schema

Every finding should be normalized before it enters the catalog:

```yaml
source_url: string
source_type: dataset | competition | paper | benchmark | red_team | forum | rfp | docs | repo
domain: string
task: string
evidence_summary: string
data_coverage: 1-5
verifiability: 1-5
economic_value: 1-5
llm_capability_gap: 1-5
deployment_friction: 1-5
cost_savings_potential: 1-5
candidate_primitives:
  - string
candidate_pipeline:
  name: string
  expected_lift: low | medium | high
confidence: 0.0-1.0
review_status: inbox | accepted | rejected | needs_more_evidence
```

## Scoring

Use this score to rank findings:

```text
Gap Discovery Score =
economic_value
x data_coverage
x verifiability
x llm_capability_gap
x deployment_friction
x cost_savings_potential
x reuse_potential
/ maintenance_burden
```

High scores become:

1. candidate primitives.
2. candidate pipelines.
3. new rule packs, rubrics, datasets, or knowledge packs.
4. benchmark tasks for measuring capability lift over an out-of-box LLM baseline.

## Out-Of-Box Baseline Test

Before promoting a finding, run a cheap baseline:

1. Ask a frontier model, a small hosted model, and a local model to solve the task without special scaffolding.
2. Score outputs with deterministic checks, a rubric, or human review.
3. Add one layer at a time: grep/rules, retrieval, reranking, tool use, domain rubric, human escalation.
4. Promote only if the pipeline creates measurable lift or meaningful cost savings.

This prevents building components for tasks that modern models already solve well enough without help.

## Promotion Rules

Promote a finding into the catalog when it has:

- at least one cited public source.
- a clear task statement.
- evidence that a reusable primitive or pipeline can help.
- an evaluation path.
- privacy and trust-boundary notes.
- a deployment shape: local, browser, serverless, container, Kubernetes, managed cloud, or air-gapped.

## Useful Discovery Surfaces

- Kaggle exposes datasets and competitions that show where labeled tasks and practitioner demand exist.
- arXiv provides a public API for paper search and metadata.
- Semantic Scholar provides paper search and graph APIs for literature discovery.
- Papers With Code is useful for task, dataset, and benchmark mapping.
- Red-team events and hackathons surface failure modes that can become tests, rule packs, and guardrail primitives.

## Output Cadence

Run the browser fleet in weekly batches:

- 50-100 raw findings.
- 20 normalized findings.
- 5 high-priority primitive proposals.
- 2 candidate pipeline blueprints.
- 1 validated lift experiment against an out-of-box LLM baseline.

The output should land first in `catalog/_inbox/` or as a review packet. Curated findings can then become stable manifests.
