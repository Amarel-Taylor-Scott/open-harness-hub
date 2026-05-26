# /goal: Scale Open Harness Hub Toward Billions Of Components

You are Codex working in Open Harness Hub.

## Mission

Expand this repository toward a validated, fully vectorized registry of
**thousands of millions** of reusable AI pipeline components and subcomponents
— procedure components, signed knowledge components, source surfaces, tools,
RAG packs, rubrics, benchmarks, deployment blueprints, and runtime patterns —
reachable by hybrid search and through an easy conversational builder. The
headline interaction: a user pastes an LLM challenge or use-case description
and gets back a working, costed, deployable flow.

One million validated components is the proven floor
(`docs/codex/million-object-goal.md`); the north star is
`docs/codex/billion-component-goal.md`. For long unattended sessions, follow
`docs/codex/autonomous-session-runbook.md`: small validated batches, switch
paths when blocked, never stop.

## Read First

1. `AGENTS.md`
2. `README.md`
3. `taxonomy/SPEC.md`
4. `docs/codex/billion-component-goal.md`
5. `docs/codex/million-object-goal.md`
6. `docs/codex/autonomous-session-runbook.md`
7. `docs/codex/no-magic-values.md`
8. `docs/codex/object-factory-workflow.md`
9. `docs/codex/quality-gates.md`
10. `docs/codex/multi-day-goal-runbook.md`
11. `docs/architecture/source-governance-and-entity-resolution.md`
12. `docs/architecture/low-cost-hosting-plan.md`
13. `docs/architecture/object-factory-worker-fleet.md`
14. `docs/codex/speed-guardrails.md`

## Operating Rules

- Make durable repo changes, not only suggestions, unless explicitly asked to brainstorm.
- Add small, coherent, validated batches.
- Use knowledge packs and JSONL for high-volume component rows.
- Add tools and pipelines that can generate more components later.
- Normalize raw source material before publishing: source governance, entity linking, fuzzy dedupe, and index record emission.
- Prefer dedicated object factory workers for source ingest, Markdown conversion, document digestion, sensitive-data gates, LLM polishing, verification, labeling, dedupe, cost metering, and publish review.
- Route model work through provider-neutral wrappers so jobs can use local models, OpenAI-compatible endpoints, managed APIs, or tenant-provided keys.
- Preserve provenance, licensing, trust boundaries, privacy boundaries, and freshness.
- Do not store real PII, secrets, confidential data, or proprietary job-posting dumps.
- Do not republish anything under `_reference/`.
- Default to database-first incremental ingestion for high-volume work. Full validation and full catalog page rebuilds are release gates, not the daily scaling loop.
- Prefer focused validation and selected page rendering for changed public definitions; use JSONL, load plans, index deltas, and Postgres/pgvector audits for large batches.
- Vectorize everything promotable: every promoted row carries a real embedding from a declared model + dimension drawn from one config source; placeholder vectors block promotion. Make all of it reachable by hybrid (keyword + vector + graph + facet) search.
- No magic values: never hand-type a value that must be updated in more than one place. Repo-state counts/versions are computed; shared values (embedding dimension, model IDs, thresholds, paths, type/row-family lists) get one definition and are imported/read everywhere. See `docs/codex/no-magic-values.md`.
- Treat Kaggle competitions (LLM usage, tuning, RAG, eval, multimodal, tabular) as the use-case + builder-test corpus: each becomes a use-case and a `pasted challenge -> expected component flow` benchmark. Permissive licenses only; carry author + URL + license; route uncertain sources to review tickets.

## Default Batch

Each work cycle should create or improve:

1. one architecture/research/use-case doc;
2. one knowledge pack;
3. one seed JSONL data file;
4. one to three tools;
5. one pipeline;
6. optional rubric/benchmark;
7. MkDocs nav entry if the doc is user-facing.

For ingestion or factory work, include these stages unless there is a clear reason not to:

1. source governance routing;
2. component factory job routing;
3. page/document to Markdown conversion when needed;
4. sensitive-data and publication safety gates;
5. normalized object schema;
6. entity recognition/linking;
7. fuzzy dedupe clustering;
8. keyword/vector/graph/facet index record emission;
9. review ticket routing.

## Validation

For release snapshots, broad schema/vocabulary changes, or final full-check requests, run:

```bash
python3 scripts/validate.py
python3 scripts/build_component_id_index.py
python3 scripts/build_catalog_pages.py
```

For normal daily factory turns, run focused validation on changed public definitions and selected page rendering:

```bash
python3 scripts/validate.py <changed catalog yaml paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog yaml paths> --update-index
```

Report which path was used, the component definition count when available, generated/staged/committed database counts, and any validation/build failures.

## Expansion Priorities

Prioritize components by:

`usefulness x demand x complexity x time_savings x frequency_of_deployment x not_solved_by_out_of_box_llms x cost_savings x deployment_management_value x model_swap_value`

Look for capability gaps where:

`capability_spike ~= verifiability x training_attention x data_coverage x economic_value`

## Source Surfaces

Strong source surfaces include:

- occupation taxonomies: O*NET, ESCO, BLS ORS, SOC, ISCO;
- public facts: CDC, Federal Register, Regulations.gov, Data.gov, data.europa.eu, EUR-Lex;
- research: OpenAlex, Semantic Scholar, arXiv, PubMed, Crossref, Papers With Code, Kaggle;
- software and workflow ecosystems: GitHub, package registries, MCP servers, ComfyUI workflows, n8n, Flowise, Dify, Langflow;
- agent and skill ecosystems: OpenClaw, Claude Code skill repositories, Hermes-style agent systems, CrewAI, LangGraph, AutoGen, Dify, Flowise, n8n, ComfyUI;
- risk and compliance: NVD, MITRE, OWASP, sanctions lists, SEC EDGAR, openFDA, ClinicalTrials.gov;
- government and verified publishers: agencies, standards bodies, public forms, archived pages, signed knowledge feeds.

## Hosting Bias

Start with the cheapest working product shape:

- static docs on GitHub Pages or Cloudflare Pages;
- API and workers on Render for speed;
- Postgres plus pgvector for canonical data, keyword search, and first vector search;
- object storage for raw snapshots and generated assets;
- Redis or managed queue for scan, embed, eval, and pricing jobs;
- split heavy tools into Cloud Run, cloud functions, or container workers only when needed;
- add BigQuery or ClickHouse later for telemetry, cost traces, ranking, and billing analytics.

## Expected Closeout

Final response should state:

- what changed;
- which files matter;
- validation result;
- catalog page rebuild result;
- next logical factory area.
