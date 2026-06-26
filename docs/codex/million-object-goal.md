# Million Component Goal

## Objective

Scale OpenHubForAI into a validated, searchable, signed, versioned, and deployable registry of more than one million AI pipeline components and subcomponents.

The registry should let a user describe a task, role, procedure, policy, alert workflow, or domain problem and receive:

- relevant pipeline ideas;
- reusable components;
- RAG packs;
- procedure questions;
- evidence requirements;
- tool and runtime options;
- model and hosting cost estimates;
- eval rubrics;
- deployment blueprints;
- Terraform/runtime/MCP setup plans where appropriate.

## Component Definition

A component is any durable, typed unit that can improve a pipeline. Subcomponents are smaller rows that belong to, configure, test, verify, or enrich a component.

- curated component definition;
- signed knowledge component;
- procedure knowledge component;
- review question;
- checklist item;
- decision gate;
- evidence requirement;
- versioned public fact;
- occupation work atom;
- tool adapter;
- source surface;
- evaluation rubric;
- benchmark case;
- deployment template;
- model/runtime cost record.

Components do not all need full standalone repository files. High-volume atoms should live as database-backed components and subcomponents, with JSONL used for staging/import/export and with representative public definitions for packs, extraction tools, and pipelines.

## Priority Formula

Prioritize components using:

`priority = usefulness x demand x complexity x time_savings x frequency_of_deployment x not_solved_by_out_of_box_llms x cost_savings x deployment_management_value x model_swap_value`

Also track capability gaps:

`capability_spike ~= verifiability x training_attention x data_coverage x economic_value`

High-value expansion areas are places where the economic value is large, the facts or procedures are verifiable, and out-of-box LLM behavior is weak without structured tools, RAG, or workflow logic.

## Target Composition

A practical first million could be:

- 250,000 occupation work atoms from O*NET, ESCO, BLS ORS, public job classifications, and curated role descriptions;
- 200,000 procedure questions and checklist items from SOPs, audits, standards, forms, and training materials;
- 150,000 versioned facts from government, regulatory, public health, standards, and market sources;
- 100,000 tools, adapters, API patterns, cloud functions, and containerized workers;
- 100,000 domain-specific RAG chunks with provenance and retrieval policies;
- 75,000 rubrics and benchmark cases;
- 75,000 deployment blueprints, Terraform snippets, MCP setup patterns, and runtime profiles;
- 50,000 workflow graph patterns from ComfyUI-like, n8n-like, agent, data, media, and enterprise automation ecosystems.
- 25,000 skill and agent-workflow components from controlled reference intake of systems such as OpenClaw, Claude Code skill repositories, Hermes-style agents, CrewAI, LangGraph, AutoGen, Dify, Flowise, n8n, and ComfyUI.

## Daily Production Target

The operating target is additive daily progress:

- generate at least 1,000 database-backed component candidates every day;
- stretch to 5,000 component candidates per day when source surfaces, workers, and validation are healthy;
- create or refresh 5 to 25 preconfigured showcase pipelines every day;
- keep public component definitions focused on tools, packs, pipelines, schemas, rubrics, and docs that make generation repeatable;
- keep high-volume candidates in Postgres/pgvector-ready JSONL row families until reviewed, deduped, approved, promoted, and versioned.

Daily component candidates must remain searchable and wireable. A valid daily batch should include normalized component rows, source governance rows, entity refs, dedupe clusters, labels, dimensions, embeddings or embedding work rows, index records, and review tickets where risk warrants review.

Preconfigured showcase pipelines are product proof. Each day should add or refresh use-case templates that show how components can be strung together for a specific domain, cost profile, modality, and deployment target. Good showcase families include AML alert review, social-media moderation, public fact update propagation, trades work-order triage, water quality, food quality, used-car sales, cyber SOC alert quality, disaster response, public procurement, and content creation.

User-provided theories and postmortems should be converted into defensive component families when they expose reusable pipeline structure. For example, an edge AI semantic-gap postmortem becomes components for recursive encoding sanitization, post-decode safety evaluation, micro-model-first authorization routing, main-model escalation, edge latency/cost estimation, and replayable audit traces.

If a daily run cannot reach 1,000 candidates through one source, it must switch paths rather than stop:

- use another source-surface matrix;
- run a smaller partition and then another partition;
- generate pipeline templates, rubrics, and benchmark rows while data ingestion is blocked;
- route uncertain sources into review tickets instead of publishing them;
- document the roadblock and the fallback used.

## Non-Negotiables

- Validate component definitions with `python3 scripts/validate.py`.
- Rebuild generated docs with `python3 scripts/build_catalog_pages.py`.
- Keep raw proprietary, personal, or confidential data out of the repo.
- Do not republish `_reference/`.
- Preserve source provenance, collection date, license, and trust boundary.
- Use knowledge packs and JSONL for high-volume components and subcomponents.
- Use signatures, archive captures, hashes, and revocation metadata for volatile or publisher-owned facts.
- Do not count raw generated lines as committed database state. Use staged load audits and committed Postgres count reports to separate generated, staged, and loaded rows.
