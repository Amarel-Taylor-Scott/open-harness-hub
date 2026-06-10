# Component Taxonomy & Pipeline Stages (canonical)

The single, consistent reference for **what every component type is** and **where
it sits in a pipeline**. These labels are canonical — the conversational builder,
the `/browse` page, docs, and emitters all use them. (Schema field names in
`schemas/` are the storage contract; these are the human/product labels.)

## The seven primitives (the foundation)

Everything in a pipeline reduces to **seven primitives**, and they all extend one
**generic shell** — `scripts/primitives/base.py::Primitive` — whose contract is
compatible with the pipeline object: `run(po) -> po`. Every catalog component
`type` is a subtype/extension of exactly one primitive. The folder structure
mirrors this taxonomy: **one file per primitive** under `scripts/primitives/`,
each owning its own label/stage/description (the single source — there are no
magic-string label tables elsewhere; product labels are derived via
`label_for_type` / `stage_for_type`).

1. **Input** — the payload to work on.
2. **Knowledge Corpus** — a store of facts, queried by a trigger.
3. **If Statement** — the condition (the IF), kept separate from the THEN.
4. **Action** — anything that *does* something (the THEN) — incl. add-persona, model-call, evaluate.
5. **Loop** — control flow / iteration over sub-steps.
6. **Stop / End** — halt early on a guard / terminal condition.
7. **Output** — finalize the result + trace.

| Primitive | File | Schema `type`(s) — subtypes | Notes |
|---|---|---|---|
| **Input** | `input.py` | (pipeline `inputs`) | text · document · HTML · PDF · image · combination |
| **Knowledge Corpus** | `knowledge_corpus.py` | `knowledge-pack`, `dataset` | typed by `retrieval`: keyword / regex / rag / exact-id / classifier / graph; static or dynamic |
| **If Statement** | `if_statement.py` | `rule-pack`, `logic-pack` | the IF: contains-Y · matches /…/ · similar-to-X · classifier=Z · graph |
| **Action** | `action.py` | `persona`, `tool`, `processor`, `harness`, `adapter`, `rubric`, `benchmark` | persona = add-persona · tool = execute/call · processor = transform · harness = model-call · adapter = model-transport · rubric = evaluate |
| **Loop** | `loop.py` | `pattern`, `pipeline` | for-each · while · branch · parallel · map-reduce; pipeline orchestrates |
| **Stop / End** | `stop_end.py` | (structural) | guard / terminal halt |
| **Output** | `output.py` | (structural) | result + trace into the pipeline object |

Schema `type` keys are internal storage names; the user only ever sees the
primitive/product labels. The "stages" below are a conventional *arrangement* of
these primitives for a typical task — the primitives are the foundation.

### Not an eighth primitive: the capability-request (a typed empty slot)

There is **no eighth primitive**. When a user needs something the catalog does
not yet provide, that unmet need is captured as a **capability-request**
(`schemas/capability-request.schema.json`) — a *typed empty slot*, not a new
role. It carries the `target_type` it will eventually become (one of the
fourteen component types above, so it stays inside the seven-primitive model),
at maturity **`abstract`** — the only pre-component tier (see
`vocabularies/lifecycle.yaml`). A capability-request is **never tenant-visible as
a component**; it is an operational object (like a review-ticket), not a catalog
`type`, so it is absent from `validate.py`'s `TYPE_TO_SCHEMA`.

This keeps "what role does it play" (the seven primitives) and "how mature is it"
(the lifecycle ladder: `abstract` < `experimental` < `beta` < `stable`) as two
orthogonal axes, mirroring the existing `lifecycle` vs `lifecycle_position` split.

Promotion path (the guard that stops a build-agent from manufacturing junk):

```
requested → triaged → researching → building → built → verifying
          → [two-axis lift gate: lift AND durability]
          → promoted   (mints a real component at lifecycle `experimental`)
          | rejected / duplicate
```

The gate is the existing `scripts/eval/durable_gap_harness.py` (admit only on
structural lift). Fulfillment is either a **premium agent build** (hosted
build-on-demand) or a **community build** (a contributor earns credits when the
shared component passes the lift gate). Seed material for the build is the
mined repo catalog (`data/repo-catalog/`); ranking/dedup of gaps reuses the
research queue (`data/research-queue/areas.jsonl`).

> Pricing boundary (why this exists): export of pure **text-operation /
> static-information** components is freezable and stays free (the funnel);
> recurring value is the **code-executing + dynamic-corpus** layer and
> build-on-demand fulfillment of capability-requests. The execution-class table
> below is that boundary.

A pipeline is a left-to-right flow of stages. Each stage is filled by one or
more component *types*. Not every pipeline uses every stage.

```
Input → Input Formatting → Persona → Knowledge (triggered) → Rules
      → Tools → Model (Harness) → Post-process → Evaluate → Output
```

## The stages

### 1. Input
The raw payload. May be a string, a document, an HTML page, a PDF, an image, an
audio/video file, or a **combination**. Declared by a pipeline's `inputs`.

### 2. Input Formatting
Turn the raw input into clean, model-ready content **before** anything else:
HTML→Markdown, PDF/﻿image OCR, boilerplate/noise stripping, encoding/whitespace
normalization, table flattening, chunking. Deterministic where possible.
- **Component types here:** `processor` (deterministic transforms — `normalize.*`,
  `convert.*`, `extract.*` process kinds); a `tool` when the reformatting needs an
  *action* (e.g. render a page, run OCR, call a parsing service — see Tools).

### 3. Persona
Apply a role frame the model adopts for the task ("ESG auditor", "cite-first
counsel"). Sets stance and voice; holds **no** volatile facts.
- **Component type:** `persona`.

### 4. Knowledge (triggered)
Add **facts** to the working context. Knowledge is pulled from a **Knowledge
Corpus** and is fired by a **trigger**. The trigger is declared on the Knowledge
Corpus's `retrieval` field (a corpus may support several):

| Trigger (`retrieval`) | Fires when… | Example |
|---|---|---|
| `rag_vector` | semantic similarity to the query | policy/framework corpora |
| `exact_id` | an identifier appears (code, accession, K-number) | CVE, NDC, FIPS, HGVS |
| `regex` | a pattern matches | structured codes, citations |
| `keyword` | a term/alias appears | glossaries, slang, synonyms |
| `classifier` | a learned class is detected | recordability, abstention |
| `graph` | a relationship traversal is needed | ownership, ratification, corridors |

**Knowledge Corpus components** (`knowledge-pack`) come in two forms:
- **Static / standardized** — a fixed, versioned fact set (e.g. CWE Top-25, APWA
  color codes, DEA schedules). The default.
- **Dynamic** — a component **builds or extends a corpus** by going out and
  fetching information (via a Tool), then adding it to a new or pre-existing
  corpus. The fetch is a Tool action; the result is a Knowledge Corpus component
  with provenance + freshness + (for volatile facts) CDC/revocation.

### 5. Rules
Deterministic checks/filters applied to text **before** the model, to catch,
gate, or route. Cheap and explainable; they reduce what the model must read.
- **Component type:** `rule-pack`, one family each: GREP/regex, glob, classifier,
  heuristic, routing, RAG-retrieval-policy. *A rule pack reaches the model only
  through a harness — never wired raw (hard wiring rule).*

### 6. Tools
**Take an action** and return a result. Tools *do* things; processors and rule
packs only transform/check text. A tool may: run a program, make an API call,
execute code, visit a website, download HTML, extract information — and handle
**advanced preprocessing/reformatting beyond simple text rules** (e.g. render +
scrape a page, OCR a scan, query a database, call a public-data API).
- **Component type:** `tool` (with `parameters`, `returns`, `side_effects` ∈
  none/read/write/external_call, and an implementation contract).

### 7. Model (Harness)
Run the model behind a **trust boundary**. The harness declares its applied
layers, the packs it consumes/emits, and its `model_targets`; the **adapter** is
the provider-neutral transport — swap local↔hosted↔tenant-key here without
touching the rest of the flow.
- **Component types:** `harness`, `adapter`.

### 8. Post-process
Deterministic transforms on the model's output: coerce to a typed envelope /
strict JSON, redact, summarize-to-budget, stitch, format.
- **Component type:** `processor` (`format.*`, `redact.*`, `envelope.*` kinds),
  `pattern` (reusable output-shaping shapes).

### 9. Evaluate
Score and verify the result against a contract; prove the capability lift.
- **Component types:** `rubric` (dimensions + scoring method), `benchmark`
  (rubric + dataset + judge, with reproducibility fields), `dataset`.

### 10. Output
The delivered result plus a trace (what fired, what was cited, cost, review
status). Declared by a pipeline's `outputs`.

## Component types at a glance (consistent definitions)

| Schema `type` (storage) | Product label · one-line definition | Primitive |
|---|---|---|
| `persona` | **Action: Add Persona** — frames the role/voice (no facts) | Action |
| `knowledge-pack` | **Knowledge Corpus** — facts with a `retrieval` trigger; static or dynamic | Knowledge Corpus |
| `dataset` | **Knowledge Corpus (Dataset)** — labeled inputs/outputs/labels with provenance | Knowledge Corpus |
| `rule-pack` | **If Statement** — one condition family (keyword/regex/similarity/classifier/routing) | If Statement |
| `logic-pack` | **If Statement** — conditional prompt/schema/response policy | If Statement |
| `tool` | **Action: Execute/Call** — code / API / fetch / extract / post / webhook | Action |
| `processor` | **Action: Transform** — deterministic text op (format/redact/rerank/compress) | Action |
| `harness` | **Action: Model Call** — runs the model behind a trust boundary | Action |
| `adapter` | **Action: Model Transport** — swap local↔hosted | Action |
| `rubric` | **Action: Evaluate** — score against a contract | Action |
| `benchmark` | **Action: Benchmark** — comparable score vs a bare model | Action |
| `pipeline` | **Pipeline** — orchestrates a DAG end to end | Loop |
| `pattern` | **Loop / Flow** — reusable shape (loop / branch / parallel) | Loop |

## Conditions (IF) and Actions (THEN) — decoupled

A "rule" is fundamentally **IF condition THEN action**. For composability we keep
the two halves as separate, recombinable pieces — one condition can drive many
actions; one action can be triggered by many conditions.

- **Condition (IF)** — a predicate over the working text/state:
  - `text contains Y` (keyword), `text matches /…/` (regex),
  - `text is similar to X` (vector similarity ≥ threshold),
  - `classifier(text) = Z`, or a structured/graph check.
  Conditions are the matching half of a `rule-pack` (a rule pack = a set of
  `{when: <condition>, then: <action ref>}`).

- **Action (THEN)** — what fires when a condition is true. Actions compose:
  - **Retrieve** facts from a Knowledge Corpus (keyword / regex / RAG),
  - **Rerank / prioritize** retrieved results,
  - **Compress / polish** with a small model (e.g. Gemma 4),
  - **Transform** text (format, redact, normalize) — a `processor`,
  - **Execute** code / call an API / fetch / extract — a `tool`,
  - **Post / request** — HTTP call-out, fire a webhook, push a notification,
  - **Evaluate** — score against a rubric / judge,
  - **Monitor** — watch a source or metric and re-trigger on change,
  - **Loop / branch / parallel** — control flow over sub-steps (the pipeline
    step kinds `loop`, `branch`, `parallel`),
  - route, gate, escalate, or call the main model via a `harness`.

Action categories by execution model: retrieve/rerank/transform/evaluate are
text-operations; execute/post-request/webhook/monitor are code-executing (need
credentials, rate limits, sandboxing); loop/branch/parallel are control flow.

This separation is why an Action like "retrieve by keyword then rerank" is built
from small reusable pieces rather than baked into one monolithic rule. (Schema
note: `rule-pack` rules currently carry `when`/`then`; formalizing standalone
`condition` and `action` leaf types is a queued refinement.)

## Knowledge Corpus (the fact store)

The product term is **Knowledge Corpus** (the schema `type` key stays
`knowledge-pack` for back-compat storage only — never shown to users). A corpus
is typed by **how it is queried** — its `retrieval` triggers: `keyword`, `regex`,
`rag_vector`, `exact_id`, `classifier`, `graph` (a corpus may support several).
Static (versioned fixed set) or dynamic (fetched/extended by an Action). The
Action "search this keyword corpus and pull down X" is the THEN that consumes it.

## Execution model (orthogonal classification — by what runs)

Every component falls into exactly one of three execution classes. This is
orthogonal to the stage and is what governs **safety, sandboxing, caching, and
cost**: only the third class executes code or touches the world.

| Execution class | What it does at runtime | Types | Side effects |
|---|---|---|---|
| **Static-information** | Holds/returns fixed data; read into context | `knowledge-pack`, `dataset`, `persona`, `logic-pack`, `rubric` | none (read-only) |
| **Text-operation** | Transforms or checks text deterministically, in-process | `processor`, `rule-pack`, `pattern` | none (pure) |
| **Code-executing** | Runs a program, calls an API, executes code, invokes a model, fetches/extracts | `tool`, `harness`, `adapter`, `pipeline` (orchestrates) | read / write / external_call |

Why it matters: static-information and text-operation components are pure and
trivially cacheable and safe to run anywhere; **code-executing components are the
only ones that need sandboxing, credentials, rate limits, and cost gates** — so a
"only call the model if these conditions are not met" gate belongs here.

## The pipeline object (runtime state contract)

Every run carries ONE `PipelineObject` (`scripts/pipeline_object.py`) threaded
through every component. It holds the input (+ `input_type`), metadata/call info,
a **shared mutable variable scope** (`.variables`) that each component reads and
writes, a step-by-step log (`StepLog` per invocation, with stage, exec-model,
model-call flag, tokens, cost, timing, status), accumulated cost/tokens, outputs,
and errors. It is JSON-round-trippable, so a finished run is a complete,
replayable audit record — the substrate for tracking, recommendations, and
**data + drift** sharing (value prop 4).

```
component(pipeline_object) -> reads .input/.variables, does work,
                              appends a StepLog, writes results to .variables/.outputs
```

## Distinctions that must stay consistent
- **Processor vs Tool vs Rule-pack:** a *processor* transforms text
  deterministically (no model, no external action); a *tool* takes an *action*
  (API/code/fetch) and can do advanced preprocessing; a *rule-pack* is a
  declarative text-rule family. If it *acts on the world*, it's a Tool; if it
  *reshapes text in-process*, it's a Processor; if it *matches/gates text by a
  rule*, it's a Rule-pack.
- **Knowledge vs Rules:** Knowledge adds *facts* (triggered retrieval); Rules
  apply *behavior/checks*. A pack never holds logic; a rule pack never holds facts.
- **Static vs dynamic knowledge:** static corpora are versioned fixed sets;
  dynamic corpora are fetched/extended via a Tool and carry freshness + revocation.
- **Version is metadata, never in a name/ID** (see AGENTS.md).

> Builder note: the conversational builder renders these stages as a flowchart.
> Splitting `processor` into Input-Formatting vs Post-process per-instance needs
> the `process_kind` in the index (queued); today it groups them as deterministic
> transforms.
