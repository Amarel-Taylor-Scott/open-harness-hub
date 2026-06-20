# Primitive source surface map

This map defines the surfaces to scan routinely when building a large primitive database. The target shape is a searchable, embeddable, tagged corpus with more than one million primitives across tools, rules, rubrics, datasets, deployment patterns, source connectors, evaluation tasks, policy facts, and workflow blueprints.

The product search path should support:

1. keyword retrieval for exact policies, names, fields, and identifiers.
2. vector retrieval for semantic task matching.
3. model-polished search for query rewriting, candidate explanation, ranking, and blueprint generation.
4. verified-source channels where governments, standards bodies, universities, and trusted institutions can publish signed facts, laws, policies, schemas, and updates.

## What Counts As A Primitive

A primitive is any reusable unit that helps construct, verify, deploy, or operate an AI pipeline:

- tool contract
- MCP connector
- browser workflow
- data source connector
- rule or grep pattern
- retrieval policy
- rubric
- benchmark task
- dataset descriptor
- schema mapping
- transformation step
- deployment module
- cost model
- monitoring check
- human escalation policy
- legal or factual authority record
- pipeline pattern

## Routine Scan Surfaces

| Surface | Examples | Primitive opportunities |
|---|---|---|
| Open government data catalogs | Data.gov, data.europa.eu, CKAN portals | dataset descriptors, source connectors, schemas, domain pipelines |
| Laws and regulations | Federal Register, Regulations.gov, EUR-Lex, national legal portals | legal facts, citation resolvers, compliance rules, change monitors |
| Scientific literature | OpenAlex, Semantic Scholar, arXiv, PubMed, Crossref | methods, benchmarks, failure studies, domain rubrics |
| ML datasets and benchmarks | Kaggle, Hugging Face datasets, Papers With Code | eval tasks, dataset loaders, baseline tests, domain task templates |
| Security and safety | NVD, CVE, MITRE ATT&CK, OWASP, bug bounty reports | threat rules, red-team probes, vulnerability triage pipelines |
| Health and life sciences | openFDA, ClinicalTrials.gov, PubMed, CDC, WHO | adverse-event workflows, clinical safety gates, terminology mappings |
| Finance and corporate filings | SEC EDGAR, central-bank data, sanctions lists | filing extractors, fraud flags, risk rubrics, entity-resolution tools |
| Procurement and RFPs | SAM.gov, EU TED, agency procurement portals | demand signals, deployment gaps, compliance primitives |
| Hiring and task marketplaces | RentAHuman-style task boards, Upwork, Fiverr, Freelancer, local task marketplaces, public gig marketplaces | task archetypes, acceptance criteria, skill bundles, workflow steps, human escalation patterns, cost and turnaround priors |
| Developer ecosystems | GitHub, GitLab, npm, PyPI, Docker Hub, Terraform Registry | tool wrappers, container runtimes, infra modules, recurring setup failures |
| Standards and controls | NIST, ISO pages, SOC2/PCI public docs, CISA, ENISA | control mappings, audit checks, governance workflows |
| Forums and help sites | Stack Overflow, community forums, vendor issue trackers | repeated integration pain, error patterns, missing primitives |
| Red-team events and hackathons | AI safety evals, CTFs, public challenge reports | adversarial datasets, exploit patterns, guardrail tests |

## Verified Publisher Lane

Verified sources should be able to publish signed update streams into the primitive database.

Examples:

- a government agency publishes regulation text, guidance, deadlines, forms, or enforcement bulletins.
- a standards body publishes control mappings or updated requirements.
- a university lab publishes benchmark datasets and task definitions.
- a regulator publishes complaint categories, reporting thresholds, or supervised examples.
- an open-source project publishes an MCP connector contract or runtime module.

Verified-source records need stronger metadata:

```yaml
publisher_id: string
publisher_type: government | regulator | standards_body | university | nonprofit | vendor | open_source_project
verification_method: dns | signature | repository_attestation | manual_review | delegated_authority
authority_scope: string
jurisdiction: string
license: string
effective_date: date
expires_or_review_by: date
source_url: string
content_hash: string
change_type: add | update | deprecate | revoke
supersedes: string
trust_boundary: verified_external
```

Verified records should not become unqualified model memory. They should become citeable knowledge objects, retrieval entries, rules, or update signals with provenance and effective dates.

## Million-Primitive Architecture

At one million primitives, the database should be treated as a search product and a build graph.

Minimum indexes:

- `keyword_index`: BM25 or equivalent over names, tags, source titles, identifiers, and exact fields.
- `vector_index`: embeddings over task descriptions, examples, source summaries, and primitive behavior.
- `graph_index`: dependency edges between primitives, pipelines, models, datasets, rubrics, laws, and deployments.
- `facet_index`: industry, capability, modality, jurisdiction, trust boundary, deployment target, license, source type, maintenance burden.
- `freshness_index`: effective dates, update cadence, last verified date, deprecation status.
- `quality_index`: rating, usage, eval score, failure rate, citation coverage, publisher reputation.

Search flow:

1. User enters a problem, solution idea, or attempted task.
2. Query planner expands the task into domains, capabilities, constraints, and deployment needs.
3. Keyword search finds exact terms, laws, tools, model names, and identifiers.
4. Vector search finds semantically similar primitives and prior blueprints.
5. Graph traversal pulls dependencies and alternatives.
6. Model-polished ranking explains candidate choices and gaps.
7. Blueprint generator emits pipeline, tools, rules, evals, runtime, Terraform/container plans, pricing assumptions, and MCP setup steps.

## Source Scoring

Use this score to prioritize scanning surfaces:

```text
Source Priority =
primitive_density
x authority
x update_frequency
x demand_signal
x verifiability
x license_reusability
x automation_feasibility
/ ingestion_risk
```

High-priority surfaces have many machine-readable records, clear provenance, permissive access, and strong evidence that users want workflows in that domain.

## First 30 Surfaces To Add

Start with sources that have useful metadata, stable identifiers, or public APIs:

- Data.gov Catalog API
- data.europa.eu and European legal data dumps
- Federal Register API
- Regulations.gov API
- EUR-Lex
- OpenAlex
- Semantic Scholar
- arXiv
- PubMed
- Crossref
- Papers With Code
- Kaggle datasets and competitions
- Hugging Face datasets
- GitHub repositories, topics, issues, and releases
- npm, PyPI, Docker Hub, and Terraform Registry
- NIST NVD
- MITRE ATT&CK
- OWASP projects
- openFDA
- ClinicalTrials.gov
- SEC EDGAR
- sanctions lists and corporate registries
- SAM.gov and public procurement portals
- public hiring and task marketplace metadata
- court and legal open-data projects
- patent databases
- standards/control catalogs
- cloud provider docs and pricing pages
- vector database and inference benchmark reports
- MCP server registries and connector lists
- public red-team reports, CTFs, and AI safety challenges

## Data Product Guardrails

- Track source license and redistribution terms before indexing content.
- For hiring and task marketplaces, prefer metadata, aggregate task archetypes, synthetic examples, and user-provided exports; do not store real worker/client PII, private messages, proprietary listing text, or terms-prohibited scraped content.
- Store source metadata separately from derived primitive metadata.
- Keep volatile facts in tools or verified-source knowledge streams, not personas.
- Attach citation and content hashes for every primitive derived from public sources.
- Mark generated primitives as proposals until reviewed or benchmarked.
- Keep source freshness explicit; old laws, prices, APIs, and model capabilities must expire.
- Support takedown, revocation, supersession, and deprecation.

## Scale Targets

The first scale target should not be one million hand-authored YAML files. Use layered storage:

- curated manifests for stable public primitives.
- JSONL/object-store rows for large generated primitive candidates.
- relational tables for metadata and dependency graph edges.
- vector index for semantic search.
- append-only trace store for scans, ratings, usage, and verification events.

Promotion path:

```text
raw source record -> normalized source item -> candidate primitive -> evaluated primitive -> curated manifest -> marketplace listing
```

This lets the database grow to millions of indexed primitives while keeping the curated catalog smaller, reviewable, and high-trust.
