# Open Harness Hub

> **Repository history note.** This project previously lived at
> `github.com/taylor-s-amarel/open-harness-hub`. Its canonical home is now
> [`github.com/Amarel-Taylor-Scott/open-harness-hub`](https://github.com/Amarel-Taylor-Scott/open-harness-hub).
> All git history is preserved; the old URL may continue to resolve via
> GitHub's automatic redirect but new pushes go to the new account.

> A **database-backed registry of reusable AI-pipeline components** — and a
> **conversational builder** — whose one admission rule is **measurable capability
> lift over a bare LLM**. The protocol + engine are open; the governed, measured, and
> *fresh* content is the commercial layer (see the
> [open-core model](docs/strategy/open-core-model.md)).

**The headline interaction:** *paste a task → get back a working, costed, deployable
flow built from existing components.* Everything else — the catalog, the governance, the
generation foundry — exists to make that returned flow trustworthy, cheap, and current.

The open core runs from a clone and deploys unchanged to GitHub Pages, Hugging Face
Spaces, Vercel, Netlify, or Cloudflare Pages; the live/governed layer runs as a queue +
worker service ([cloud architecture](docs/architecture/cloud-architecture.md)).

## AI Done Right design family

This repo also carries the current high-fidelity AI Done Right portfolio design
bundle in [`dist/sites/openharness-design/`](dist/sites/openharness-design/).
That bundle is the Claude Code Max handoff for the parent brand, Baltor, Teleon,
and the Open*Hub registry family. Start with
[`START-HERE-CLAUDE-CODE.md`](dist/sites/openharness-design/START-HERE-CLAUDE-CODE.md),
then read the bundle
[`README.md`](dist/sites/openharness-design/README.md),
[`CLAUDE-CODE.md`](dist/sites/openharness-design/CLAUDE-CODE.md), and
[`HANDOFF.md`](dist/sites/openharness-design/HANDOFF.md).

Current design-family snapshot: AI Done Right parent + Baltor + Teleon + 22
Open*Hubs. The Open*Hub set is 9 live open registries plus 13 private-bench
registries, including the full Baltor method spine
(OpenReconciliationHub, OpenHardeningHub, OpenEnrichmentHub,
OpenOptimizationHub, OpenVerificationHub) and OpenRoutingHub
(model-routing policy). Treat this as a reviewed handoff
snapshot, not a hard-coded source of truth; the owning registry is
`dist/sites/openharness-design/shared/products.js`.

Run the focused design-family proof:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

Parser-safe loop handoff:

```text
/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md
```

Handoff freshness lives in
[`docs/handoff/handoff-freshness.md`](docs/handoff/handoff-freshness.md) and is
validated by:

```bash
python3 scripts/check_handoff_docs_freshness.py --self-test
```

Production work must also answer service-to-service consumption: API keys,
service accounts, OAuth/client credentials, workload identity, tenant-scoped
authorization, and audit receipts. The current architecture brief is
[`docs/architecture/service-auth-and-consumption-model.md`](docs/architecture/service-auth-and-consumption-model.md).

Local development does not require paid cloud hosting. Use local servers,
containerized local stacks, and temporary TryCloudflare quick tunnels for
preview/review. The local tunnel/auth plan is
[`docs/architecture/local-dev-tunnels-and-auth.md`](docs/architecture/local-dev-tunnels-and-auth.md)
and is validated by:

```bash
python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test
```

## What this is

The Open Harness Hub gives you a standard way to describe and combine the
modular pieces of a real AI pipeline:

Everything reduces to **seven primitives** — each catalog component is a subtype of
exactly one of them (full mapping: `docs/concepts/component-taxonomy-and-stages.md`):

| Primitive | Catalog component types | What it is |
|---|---|---|
| **Input** | _(pipeline `inputs`)_ | The typed thing coming in — text, document, HTML, PDF, image, or a combination. |
| **Knowledge Corpus** | `knowledge-pack`, `dataset` | A store of *facts* queried by a trigger — RAG corpora, fact tables, contact directories, citation graphs, labeled datasets (typed by retrieval: keyword / regex / rag / exact-id / classifier / graph; static or dynamic). |
| **If Statement** | `rule-pack`, `logic-pack` | The condition — the *IF*, kept separate from the *THEN*: contains-Y · matches /…/ · similar-to-X · classifier=Z · graph. GREP-regex, glob, classifier and heuristic rule families; prompt/schema/policy bundles. |
| **Action** | `persona`, `tool`, `processor`, `harness`, `adapter`, `rubric`, `benchmark` | Anything that *does* something — the *THEN*: add a persona, call a tool, transform via a processor, run a model through a harness, route through a provider-neutral model **adapter** (local Gemma / Ollama / OpenAI-compatible / Anthropic / Gemini / HF endpoint / frontier API / callable / none), or **evaluate** with a rubric or scored benchmark. |
| **Loop** | `pattern`, `pipeline` | Orchestration — for-each · while · branch · parallel · map-reduce. A **pipeline** is a DAG that wires the other primitives into a task. |
| **Stop / End** | _(structural)_ | A guard or a terminal halt. |
| **Output** | _(structural)_ | The result + trace, captured into the pipeline object. |

Each open component is a small YAML definition validated against a JSON Schema in
`schemas/`, and the static site renders a browsable, searchable index. At scale,
components are **database-backed rows** (Postgres + pgvector) generated by the **foundry**
(below) and gated on measured lift — not thousands of hand-written files.

## The two big goals

1. **Help people work out a benchmark for any task.** Pick a pipeline,
   plug in a dataset, declare a rubric, choose a judge — get a comparable
   score across models, harness configurations, and the If-Statement rules applied.
2. **Help people work out a tool for any task.** Pick the right modular
   primitives — an Action or two (a harness, a tool), a Knowledge Corpus, an
   If Statement — and compose them into a pipeline that solves a real problem.

Both goals share the same primitives. The catalog is the substrate.

## How a component earns its place (the capability-lift gate)

The only admission rule: a component must **measurably lift capability over a bare LLM**
— `pipeline_score − bare_model_score > 0` on a real task — and the lift must be
*structural* (it won't vanish when the next model ships). Anything a frontier model
already does zero-shot is out of scope by design. That keeps the registry parked on the
moving frontier of *what models still can't do reliably* — long-tail facts, esoteric
rules, verifiable procedures, fast-changing regulation. See
[`docs/codex/master-goal.md`](docs/codex/master-goal.md).

## The foundry — evidence-driven generation (no filler)

Components are produced by the **foundry** (`scripts/foundry/`, <!--N:foundry_modules-->23<!--/N--> self-tested modules):
a gap is admitted only with (1) a **measured** bare-model failure, (2) a **real, licensed
source**, and (3) a **measured lift** — then standardized, deduped (SimHash + LSH +
source-key), benchmark-measured, gated, and human-approved (knowledge always routes to a
human, because the model can't self-certify its own gaps). A clone cross-product can't
satisfy that, so filler is impossible by construction. Run the proof:
`python -m scripts.foundry.pipeline --self-test`. Design:
[`docs/architecture/evidence-driven-component-factory.md`](docs/architecture/evidence-driven-component-factory.md).

## Open-core, pricing, and freshness

**Open / free / exportable:** the protocol + schemas + engine, and externally-verified
**public knowledge** (government / standards bodies). **Commercial / recurring:** verified
**RAG databases**, **dynamic corpora kept fresh** (scrape → date + provenance + CDC),
hosted processing, and build-on-demand. **Public-good** components (e.g. anti-trafficking)
are free. The split is enforced automatically per component — see
[open-core](docs/strategy/open-core-model.md) and the 20
[monetization mechanisms](docs/strategy/monetization-mechanisms.md).

## Catalog status

<!-- BEGIN GENERATED:catalog-stats -->
<!-- Generated by scripts/build_readme_stats.py — do not edit by hand (see docs/codex/no-magic-values.md). -->

- **Catalog manifests (schema-validated): 2,682** — 2,682 committed to git, 0 machine-generated candidates pending review/promotion.
- **By type:** knowledge-packs 427 · pipelines 420 · rule-packs 402 · rubrics 245 · personas 233 · datasets 205 · harnesses 195 · processors 180 · tools 173 · benchmarks 111 · patterns 56 · adapters 33 · logic-packs 2.
- **Loaded into the derived query DB** (`dist/catalog.sqlite`): 505 objects, 1,024 relationship edges, 0 embeddings (vector search pending — see docs/codex/billion-component-goal.md).
- **Emitters** (`scripts/emit/`): 13.

_Counts are generated; run `python3 scripts/build_readme_stats.py` to refresh (`--check` fails on drift)._
<!-- END GENERATED:catalog-stats -->

- **2 deep verticals shipped**:
  - **ESG / Supply-Chain Due Diligence** — full E + S + G coverage,
    12 jurisdictions (EU CSDDD + CSRD + EUDR + Conflict Minerals,
    UK MSA, German LkSG, French Loi Vigilance, Norway Åpenhetsloven,
    Swiss CO 964j, Netherlands CLDD, CA SB 657, US UFLPA + Tariff
    Act §307, Canada S-211, Australia MSA, Japan METI), 13 GREP-
    rule languages, 4 rubrics (combined + sub-rubrics E/S/G),
    3 pipelines, k-anonymity cross-org pattern, CBP-WRO tool, 3
    synthetic disclosure samples, regression benchmark. The GREP
    rules have been LIVE-TESTED — see `data/esg-grep-findings.json`
    and `docs/use-cases/esg-supply-chain-due-diligence.md`.
  - **Kaggle-mined verified pipelines** — verified-evidence shapes,
    each attributed to a permissively-licensed source repo or
    competition kernel with explicit author + URL + license in the
    component definition (LoRA-QLoRA pairwise pref, TF-IDF+LightGBM, DeBERTa,
    Self-RAG concrete, code-act Jupyter, SWE-patch sample-and-
    review, STORM persona curation, deep-research supervisor-
    workers, multi-agent debate, GraphRAG, quantized inference,
    synthetic data gen, perplexity baseline, large-model FAISS
    RAG, multi-model ensemble, LLM-judge essay grading, 20-
    questions agent, plus vLLM batch / AWQ / Qwen-EEDI rerank /
    DeepSeek-R1 code-interpreter / two-time-retrieval).
- **<!--N:design_patterns-->56<!--/N--> design patterns** (e.g. Self-RAG, ReAct, ToT, SoT, Reflexion,
  Self-Refine, Plan-Execute, Orchestrator-Workers, Evaluator-
  Optimizer, Multi-Agent-Debate, Routing, Prompt-Chaining,
  Naive/Corrective/Fusion RAG, HyDE, Step-Back, Two-Stage-Retrieve-
  Rerank, K-Anonymity-Aggregation).
- **<!--N:code_templates-->10<!--/N--> zero-LLM-cost code templates** (extract_email/url/phone,
  normalize_date, validate_iban with mod-97, validate_luhn, count_tokens,
  fuzzy_jaro_winkler, cosine_similarity, sha256_hash).
- **<!--N:model_adapters-->33<!--/N--> model adapters** (e.g. Ollama-default, vLLM-AWQ-local, BGE-embeddings-
  local, OpenAI-embeddings, SDXL-local, Anthropic-Claude-Sonnet,
  Anthropic-Claude-Opus, OpenAI-GPT-frontier, Google-Gemini).
- **<!--N:emitters-->13<!--/N--> emitters** under `scripts/emit/`: Croissant, MCP, Agent
  Skills, HF cards, lm-eval-harness, promptfoo, CycloneDX-ML,
  OpenLineage, C2PA, EU AI Act, SPDX 3.0, JSON-LD, DPV.

## What lives in the catalog

The hub hosts every shape of pipeline that can be built by composing the
primitives above:

- **Research an entity** — sourced one-page profile of a company / person / place.
- **Verify data** — claim + corpus → supports / contradicts / no-evidence.
- **Format response** — coerce model output into a strict typed envelope.
- **Classify / extract / summarize / translate / redact / route.**
- **Agent loops** — plan + tool-call + verify + reflect.
- **Generate text** — free-form text generation with a defined harness.
- **Generate image** — prompt-shaping + style RAG + guard GREP rules + output-safety review.
- **Generate audio and video** — same primitive stack, different tools.
- **System-prompt / persona library** — reusable role frames.
- **RAG / GREP / classifier / heuristic libraries** — curated If-Statement rule families ready to plug in.
- **Tool library** — function-call schemas, MCP servers, OpenAPI ops.

The full list and the `pipeline_kind` vocabulary live in
`taxonomy/SPEC.md §11`.

## Where new content comes from

Two ingest paths feed the catalog (see `taxonomy/SPEC.md §12`):

1. **Direct PRs** — a contributor writes a component definition and opens a PR.
2. **Reference ports** — curators hand-port patterns from established
   permissively-licensed harness/safety repos (e.g. DueCare,
   llm-safety-framework) with full upstream attribution + license
   propagation.

## Quick tour

- **`taxonomy/SPEC.md`** — the controlled vocabulary and field definitions.
  Start here.
- **`schemas/`** — JSON Schemas that every component definition must validate against.
- **`vocabularies/`** — controlled lists (industries, capabilities,
  modalities, trust boundaries, lifecycle stages).
- **`catalog/`** — the actual content. One YAML per component, organized by
  type (`catalog/harnesses/`, `catalog/rule-packs/`, etc.).
- **`examples/`** — worked end-to-end examples. `examples/migrant-worker-safety/`
  is a generic instance of the reference DueCare safety harness ecosystem.
- **`docs/`** — MkDocs source for the published site.
- **`scripts/`** — `validate.py` (run schemas across the catalog),
  `build_catalog_pages.py` (turn component definitions into doc pages), `new.py`
  (scaffold a new component).

## CLI — `oh-hub`

The ergonomic catalog interface. Works for humans + for AI agents
(Claude Code / Cursor / Aider — invoke as a sub-process and the
output is structured).

```bash
python scripts/oh_hub.py stats                         # catalog summary
python scripts/oh_hub.py list pipeline                 # list by type
python scripts/oh_hub.py describe persona/esg-auditor  # full describe + deps
python scripts/oh_hub.py search forced-labor           # fuzzy search
python scripts/oh_hub.py depends pipeline/supplier-policy-grading
python scripts/oh_hub.py industries esg                # filter by industry
python scripts/oh_hub.py validate                      # run validator
python scripts/oh_hub.py run pipeline/X --inputs input.json
python scripts/oh_hub.py emit persona/esg-auditor mcp  # emit to MCP / Croissant / etc.
```

<!--N:demo_scripts-->21<!--/N--> demo scripts (`scripts/demo_*.py`) are pre-baked end-to-end runs spanning the verticals; the core set:

```bash
python3 scripts/demo_esg_pipeline.py          # ESG / CSDDD supplier grading
python3 scripts/demo_radiology_pipeline.py    # RADS / Fleischner report grading
python3 scripts/demo_contract_pipeline.py     # contract clause review
python3 scripts/demo_appsec_pipeline.py       # CWE secret + vuln detection
python3 scripts/demo_new_verticals.py         # GxP + climate + threat-intel
python3 scripts/demo_v3_verticals.py          # GDPR + HR + trade
python3 scripts/demo_v4_verticals.py          # real estate + M&A + aviation + food safety
python3 scripts/demo_v5_verticals.py          # construction + NERC CIP + maritime + tax
python3 scripts/demo_v6_verticals.py          # defense + election integrity + water utility
python3 scripts/demo_more_verticals.py        # insurance + academic + gov benefits
python3 scripts/demo_vendor_onboarding.py     # kitchen-sink: ESG + AppSec + Legal
```

## Notable integrations

- **Bill_info AI** (Sviatoslav Grabovsky, Gemma 4 Good Hackathon —
  Impact Track: Digital Equity & Inclusivity) — refugee bureaucracy
  translation with Verbraucherzentrale-grounded fraud detection.
  Three reusable design patterns extracted: `two-stage-extract-then-judge`,
  `critical-tier-output-override`, `refuse-on-redacted`. Live demo:
  [Svityk/bill-info-ai](https://huggingface.co/spaces/Svityk/bill-info-ai).
- **MedLabel** (Gemma 4 Good Hackathon 2026) — offline-first
  multilingual medicine-safety AI. Reference shape integrated;
  author confirmation pending.
- **Verified-evidence pipelines** ported from permissively-licensed
  competition kernels and production repos. Each pipeline component definition
  references its source(s) + author(s) + license in the definition header.
- **Hassan Gasim's "Docker-Hub-for-harnesses" framing** seeded the
  portable spec at [`docs/spec/HARNESS_HUB_SPEC.md`](docs/spec/HARNESS_HUB_SPEC.md)
  and the peer-registry comparison at
  [`docs/comparison/peer-registries.md`](docs/comparison/peer-registries.md).

Full attribution log: [`ATTRIBUTION.md`](ATTRIBUTION.md).

## Run the site locally

```bash
pip install mkdocs-material mkdocs-awesome-pages-plugin jsonschema pyyaml
python scripts/validate.py        # validate every component definition
python scripts/build_catalog_pages.py   # generate docs/catalog/*.md
mkdocs serve                      # http://127.0.0.1:8000
```

## Deploy targets (host-agnostic)

The same `mkdocs build` output deploys unchanged to:

- **GitHub Pages** — `.github/workflows/pages.yml` builds and publishes on push to `main`.
- **Hugging Face Spaces** — `hf-space/README.md` carries the HF frontmatter; serve `site/` as static.
- **Vercel** — `vercel.json` runs `mkdocs build` and serves `site/`.
- **Netlify** — `netlify.toml` does the same.
- **Cloudflare Pages** — same build, same output directory.

Pick one or all four; the build is identical.

## Reference inheritance

The reference for the harness/knowledge/pipeline pattern is Taylor Amarel's
DueCare safety ecosystem ([`TaylorAmarelTech/gemma4_comp`](https://github.com/TaylorAmarelTech/gemma4_comp))
plus the LLM Safety Framework ([`TaylorAmarelTech/llm-safety-framework`](https://github.com/TaylorAmarelTech/llm-safety-framework)).
Those repos are cloned into `_reference/` for offline study; nothing under
`_reference/` is republished here.

The taxonomy generalizes the DueCare contract — `HarnessSpec`,
`HarnessLogicPath`, `HarnessModelTarget`, `HarnessPackContract`,
`KnowledgeObject` — to apply across any industry: healthcare, finance,
legal, manufacturing, retail, education, gov, security, climate, and so on.

## License

MIT. See `LICENSE`.
