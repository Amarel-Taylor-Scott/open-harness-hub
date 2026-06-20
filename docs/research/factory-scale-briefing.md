# Open Harness Hub — Factory + Scale Briefing

> **Use this document as cold-start context for a Claude ideation session.**
> Paste the whole thing into a new conversation; ask Claude for fresh ideas
> on top. Last updated 2026-05-24 by Claude Opus 4.7 (1M context) during a
> Codex-style build sprint.

---

## 1. What Open Harness Hub (OHH) is

A **host-agnostic, industry-agnostic catalog** of modular AI-pipeline
components, deployed as a static site + a YAML-manifest content tree
validated by JSON Schema 2020-12.

**14 first-class component types**: harness · pipeline · benchmark ·
rule-pack · knowledge-pack · logic-pack · tool · persona · adapter ·
rubric · dataset · schema · processor · pattern.

**Two stated goals**:
1. Help anyone build a benchmark for any task.
2. Help anyone compose a pipeline that solves any task.

**Standards-emit philosophy** ("emit, don't replace"): each YAML manifest
fans out via 16 emitters in `scripts/emit/` to Croissant, MCP, Anthropic
Agent Skills, HF Model/Dataset/Space cards, lm-evaluation-harness,
promptfoo, CycloneDX-ML, OpenLineage, C2PA, EU AI Act Annex IV, SPDX 3.0,
JSON-LD, DPV. Source of truth stays YAML; the catalog becomes a fan-out
hub into every relevant 2026 standards format.

**License**: MIT for code-shaped components; CC-BY-4.0 for data-shaped;
permissive throughout.

**Canonical repo (as of 2026-05-22)**: `github.com/Amarel-Taylor-Scott/open-harness-hub`.

---

## 2. Current state — verified numbers (2026-05-24)

| Metric | Value | Notes |
|---|---|---|
| Total manifests | **~559** | All validate against schemas/*.schema.json on first run |
| Component types | 14 | Per `schemas/` |
| Personas | 58+ | Across 50+ verticals |
| Pipelines | 119+ | Including 5 review verticals shipped 2026-05-24 |
| Rule packs | 62 | 36 GREP regex packs, 1 classifier, others |
| Knowledge packs | 64 | Multi-lingual where applicable |
| Rubrics | 53 | One per major vertical |
| Tools | 16 | MCP-emittable function-call definitions |
| Processors | 70 | Deterministic runtime transforms |
| Adapters | 17 | Provider-neutral model transports |
| Datasets | 36 | With provenance + license metadata |
| Patterns | 46 | Self-RAG / ReAct / ToT / SoT / multi-agent-debate / etc. |
| Benchmarks | 1 | Reproducibility-pinned (commit_sha + dataset_version + run_date) |
| Emitters | 16 | Croissant, MCP, AIBOM, EU AI Act Annex IV, etc. |
| CI workflows | 4 | validate + emit + pages + release |
| Languages in GREP packs | 13 | ESG forced-labor pack covers EN/ZH/HI/BN/KO/VI/TH/ID/TL/ES/PT/FR/AR with kafala-specific Arabic |

**Validation**: `python3 scripts/validate.py` passes 100% on first run.

**Stat drift caveat**: the README still cites "172 manifests, 13 emitters,
20 patterns." These numbers are very stale. Auto-generating from
`scripts/oh_hub.py stats` would fix this.

---

## 3. Strategic positioning (May 2026 — research-validated)

**The winning pitch is narrow and commercial**:

> *"Open upstream substrate for every closed AI-governance platform —
> write one YAML manifest, emit an EU AI Act Annex IV dossier, an
> AIBOM (CycloneDX-ML), an SPDX 3.0 AI manifest, a NIST AI RMF
> crosswalk, and an MCP server."*

**Real buyer**: Compliance / governance teams at regulated enterprises
racing the EU AI Act Article 11 / Annex IV deadline (Aug 2, 2026).
Concrete pain: 40-80 engineering hours per system for an Annex IV file.
Concrete budget: Credo AI engagements at $30K-$150K/yr. Market trajectory:
AI governance TAM $420M (2025) → $6.27B (2034), 35% CAGR.

**Verticals to deprioritize** (category-defining incumbents own them):
- Contract review (Harvey $11B, Spellbook)
- AML / sanctions (SymphonyAI, Quantexa, ComplyAdvantage)
- Generic code security (Snyk, GitHub Advanced Security)
- Radiology-as-end-product (~1,000 FDA-cleared imaging tools)

**Verticals to double down on**:
- ESG / CSDDD (regulation fresh; vendor market still racing)
- Generic EU AI Act Annex IV dossier generation
- LLM-app-specific OWASP Top 10 (real gap; SaaS vendors have weak coverage)
- Humanitarian / labor-rights workflows (low rev, high mission fit; no commercial competitors)

**Timing forces**:
- EU AI Act Article 11 / Annex IV: effective Aug 2, 2026 (~10 weeks out)
- HELM → maintenance mode Jun 1, 2026 (eval-catalog vacuum opening)
- OpenAI acquired Promptfoo Mar 9, 2026 (eval consolidation)
- OpenAI Assistants API sunsets Aug 26, 2026 (registry-neutrality opening)
- MCP donated to Linux Foundation Dec 2025 (all major vendors backing)
- FY26 NDAA mandates AI BOMs in DoD procurement
- ISO 42001 = table-stakes for procurement in 2026

---

## 4. The factory pipeline (the 2000x scale lever)

**Intent**: scale the catalog from 559 hand-built manifests to **~1.1
million manifests** (2000x) using a Codex-orchestrated factory. Codex
provides strategy + edge-case curation; Python processors do the bulk
deterministic work (walking knowledge trees, slug generation, dedup,
schema validation, attribution recording, provenance, cost accounting).

**Shipped factory architecture**:

```
                ┌─────────────────────────────────────────┐
                │ external knowledge sources              │
                │ (Wikipedia / USC / Wikidata / NIST /    │
                │  EUR-Lex / FDA / OECD / arXiv / ...)    │
                └─────────────────┬───────────────────────┘
                                  │
                                  ▼ scripts/processors/{name}_walker.py
                          ┌────────────────────┐
                          │ walker             │  rate-limited, cached, frozen-revision
                          └─────────┬──────────┘
                                    │ knowledge nodes
                                    ▼
                          ┌────────────────────┐
                          │ draft-quality-gate │  deterministic; ~80% reject
                          └─────────┬──────────┘
                                    │ survivors
                                    ▼
                          ┌────────────────────┐
                          │ semantic-dedup     │  SimHash + Jaccard; no LLM
                          │ (vs. live catalog) │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │ LLM manifest       │  (currently a stub; LLM-backed
                          │ author (harness)   │   variant pending Codex/Claude wiring)
                          └─────────┬──────────┘
                                    │ draft YAML
                                    ▼
                          ┌────────────────────┐
                          │ YAML emitter +     │  validates per-file against
                          │ schema validator   │  schemas/{type}.schema.json
                          └─────────┬──────────┘
                                    │
                                    ▼
                  ┌──────────────────────────────────────┐
                  │ writes → catalog/_inbox/{type}/...   │
                  │         (NEVER live catalog)         │
                  └─────────┬────────────────────────────┘
                            │
                            ▼
                  ┌──────────────────────────────────────┐
                  │ factory-run-reporter → dist/factory- │
                  │ runs/{run_id}/REPORT.md (provenance) │
                  └─────────┬────────────────────────────┘
                            │
                            ▼
                  curator (Codex or human): reads inbox,
                  promotes survivors to live catalog
```

**Components shipped 2026-05-24**:

| Component | Purpose | File |
|---|---|---|
| `_walker_base.py` | Shared HTTP+cache+ratelimit | `scripts/processors/_walker_base.py` |
| Wikipedia walker | 6M+ articles | `scripts/processors/wikipedia_category_walker.py` |
| USC walker | ~50K US Code sections via Cornell LII | `scripts/processors/uscode_section_walker.py` |
| **Wikidata walker** | **140M items via SPARQL — the leverage walker** | `scripts/processors/wikidata_query_walker.py` |
| NIST walker | ~200 SPs + FIPS + AI RMF | `scripts/processors/nist_publications_walker.py` |
| Quality gate | Deterministic pre-LLM filter | `scripts/processors/draft_quality_gate.py` |
| Semantic dedup | SimHash + Jaccard vs. live | `scripts/processors/semantic_dedup.py` |
| YAML emitter | Per-file validate + `_inbox/` writer | `scripts/processors/draft_manifest_yaml_emitter.py` |
| Processor loader | Resolves any `implementations[].path` via importlib | `scripts/factory/processor_loader.py` |
| Factory orchestrator | walk → gate → dedup → emit → report | `scripts/factory/run_factory.py` |
| Run reporter | Provenance + cost + REPORT.md | `scripts/factory/run_report.py` |

**All components have offline self-tests**: `python3 -m {module} --self-test`.
All pass.

**Live smoke tests succeed**: Wikipedia walker fetched 4 articles from
"Category:Forced labour" in ~7s with revision IDs pinned, 43 citations
extracted from one article with proper cite-news/journal/web kind detection.

---

## 5. The pipeline-recommendation flow (shipped 2026-05-24)

When a user runs `python -m scripts.processors.pipeline_recommender
--prompt "I need a pipeline to do X"`, three stages execute:

1. **`processor/catalog-search`** — stdlib-only BM25 + tag-set Jaccard
   over the live catalog → top 30 candidates with matched tokens.
2. **`processor/gemma-reranker`** — Gemma 4 (or any chat adapter via
   `OH_RERANK_MODEL`) re-orders the candidates with one-sentence
   rationale + score 0.0-1.0; falls back to deterministic simulation
   if no model is reachable.
3. **`processor/pipeline-recommender`** — composition sketch keyed on
   the top candidate's component type ("use the pipeline as-is via
   `scripts/run_pipeline.py`" vs. "wrap this harness in a pipeline"
   vs. "expose via MCP server").

Validated end-to-end against the live catalog: ESG-grading query returned
the correct `pipeline/supplier-policy-grading` as the top match with BM25
score 30.6 / 6 tokens matched.

---

## 6. Open questions for the next ideation session

### A. Architecture / scale
- **Schema evolution at scale.** At 1M+ manifests, recurring fields the
  current schema doesn't capture will emerge. A schema-evolution proposer
  could aggregate `VOCAB-CHANGE-NEEDED` flags across factory runs and
  propose additions automatically. Currently flagged but not aggregated.
- **Curator UX at scale.** The `catalog/_inbox/` will balloon. A curator
  CLI for batch promote/reject + a static-site dashboard rendering the
  inbox by source/quality/dedup-distance would prevent a 1M-item
  backlog. Not built.
- **Cost-tier router.** Right now the rerank stage uses one model.
  A tier router that uses Gemma 4 for high-confidence rerank and only
  pulls in Anthropic Claude when the small model is uncertain would
  reduce cost ~10x at scale.
- **Cross-walker dedup at the FACTORY level**, not just within one run.
  Two walks against Wikipedia and Wikidata will frequently produce
  overlapping drafts for the same entity. A Wikidata Q-ID cross-link
  would catch this without per-pair LLM comparison.

### B. New walkers worth building
- **EUR-Lex** (~75K EU directives + regulations + decisions; structured
  ELI URLs; perfect for AI-governance vertical)
- **FDA guidance docs** (~3K; healthcare AI compliance)
- **OECD library** (~30K; sustainability / climate)
- **arXiv by topic** (~2M; for pattern manifests)
- **GitHub awesome-* lists** (curated topic indexes; cheaper than scraping)
- **Hugging Face Hub** (already structured; emit derives for models / datasets / spaces)
- **OpenLEX / national legal corpora** (for non-US law)

### C. Strategic / commercial
- **Partnership PRD with Credo AI / Modulos / Holistic / Trustible.** They
  sell $30-150K/yr governance dashboards. OHH could be their open
  upstream — they'd rather import schema-validated manifests than maintain
  their own catalogs. Not yet pitched.
- **CI-as-a-service** for enterprises wanting "your pipeline → Annex IV
  dossier in 1 minute" via emit chain. Free for OSS, paid for
  enterprises. Business-model untested.
- **OHH-as-MCP-Registry sub-namespace**. The official MCP Registry at
  registry.modelcontextprotocol.io explicitly invites sub-registries.
  OHH could publish as "the compliance-validated MCP sub-registry."
- **Codex agent loop for the curator role**. A Codex (or Claude Code)
  agent that wakes daily, picks the largest pending `_inbox/` directory,
  promotes high-quality drafts, files PRs for the rest. Half-built.

### D. Catalog gaps
- **Patterns annotated with EU-AI-Act-Annex-IV controls**. The 46 patterns
  currently lack governance metadata. Adding `nist_ai_rmf_controls` +
  `iso_42001_controls` + `eu_ai_act_risk` to each unlocks "patterns
  pre-vetted for high-risk AI systems."
- **Per-vertical Annex IV crosswalks**. Each vertical pipeline should
  ship with a draft Annex IV §1-9 dossier. None currently do.
- **A `processor/dpv-data-categories-classifier`**. Auto-tags inputs
  with W3C DPV data categories — feeds the privacy-impact-assessment story.

### E. Open research questions
- **What's the right granularity for Wikidata-seeded knowledge packs?**
  One pack per Q-ID is too fine; one per top-level category is too coarse.
  Cluster-by-property-co-occurrence?
- **How to handle multi-language catalogs?** Many sources have parallel
  multilingual content (EUR-Lex 24 languages; Wikipedia 300+; Wikidata
  labels in 400+). Single-language manifests vs. polyglot manifests vs.
  language-specific siblings?
- **At what scale does BM25 retrieval break?** At 1M manifests, BM25 over
  the full corpus is ~50ms/query (still fine). At 10M+, vector indexing
  becomes necessary.
- **Can the LLM-backed manifest author be replaced by templates?** Many
  proposals are mechanical (Wikidata Q-X → knowledge-pack-with-this-shape).
  Templating could eliminate LLM cost for ~60-80% of drafts.

---

## 7. Codex prompt suggestions for autonomous runs

**Daily catalog growth** (suggested cron):
```
You are the OHH catalog factory operator. Today's task: pick ONE walker
preset that produces high-signal compliance-relevant drafts. Run
`python -m scripts.factory.run_factory --walker {walker} ...` with
appropriate parameters. Read the resulting dist/factory-runs/{run_id}/
REPORT.md. For each draft in catalog/_inbox/, decide:
  - PROMOTE to catalog/{type}/ (move + commit + bump version)
  - REJECT (delete + log reason in catalog/_inbox/_rejected/)
  - DEFER (leave in inbox with TODO note)
Open a PR titled "factory run {run_id}: +N manifests, -M rejected".
```

**Curator-as-a-loop** (continuous):
```
Read catalog/_inbox/ ordered by quality-gate score (highest first).
For batches of ≤ 20 drafts:
 1. Verify schema validity (already done by emitter).
 2. Spot-check 3 random drafts for description quality.
 3. Confirm attribution is real (not fabricated URLs).
 4. Look for cross-vertical interactions (e.g., a new ESG pack that
    should reference the existing `knowledge-pack/csddd-and-forced-
    labor-indicators`).
 5. Approve the batch with `git mv` + a single commit.
```

---

## 8. Key files to read for full context

| File | Why |
|---|---|
| `README.md` | Top-level project pitch (stat counts stale; rewrite recommended) |
| `taxonomy/SPEC.md` | The 14 component types + §18 standards alignment (~1200 lines, load-bearing) |
| `AGENTS.md` | Hard rules for AI assistants editing the repo |
| `schemas/_common.schema.json` | The envelope every manifest carries |
| `vocabularies/{industries,capabilities,modalities,leaf-types}.yaml` | Controlled vocabs |
| `scripts/processors/_walker_base.py` | Walker DRY base |
| `scripts/factory/run_factory.py` | Orchestrator CLI |
| `scripts/processors/pipeline_recommender.py` | "I need a pipeline to do X" entrypoint |
| `docs/spec/HARNESS_HUB_SPEC.md` | Portable spec for forks |
| `docs/comparison/peer-registries.md` | Internal competitive analysis |
| `dist/factory-runs/` | Provenance dir (created on first factory run) |

---

## 9. Closing — what to think about next

The OHH thesis is structurally aligned with three independent waves:
(1) the EU AI Act Annex IV deadline forcing compliance documentation,
(2) the MCP standardization and donation to LF making protocol-neutral
catalogs valuable, and (3) the eval-tooling consolidation (HELM →
maintenance, Promptfoo → OpenAI) opening room for neutral benchmark
catalogs.

The 2000x factory is the lever that turns this from a hand-curated demo
into a defensible substrate. The remaining gaps are organizational
(curator UX, schema-evolution policy, commercial partnerships) more than
technical.

**Ideal next session**: load this briefing, then ask "given the factory
exists, what are the three highest-leverage moves we could make in the
next two weeks that would compound through August 2 (EU AI Act deadline)?"
