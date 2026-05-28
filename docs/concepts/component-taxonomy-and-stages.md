# Component Taxonomy & Pipeline Stages (canonical)

The single, consistent reference for **what every component type is** and **where
it sits in a pipeline**. These labels are canonical — the conversational builder,
the `/browse` page, docs, and emitters all use them. (Schema field names in
`schemas/` are the storage contract; these are the human/product labels.)

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
Add **facts** to the working context. Knowledge is pulled from **Knowledge Corpus
components** and is fired by a **trigger**. The trigger is declared on the
knowledge pack's `retrieval` field (a pack may support several):

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

| Type | One-line definition | Stage |
|---|---|---|
| `persona` | A role/voice frame the model adopts. No facts. | Persona |
| `knowledge-pack` | A typed Knowledge Corpus of facts, with a declared `retrieval` trigger; static or dynamically fetched. | Knowledge |
| `logic-pack` | A typed bundle of behavior (prompt templates, schemas, response policy). | Knowledge / Model |
| `rule-pack` | One deterministic rule family (GREP/glob/classifier/heuristic/routing/RAG-policy). | Rules |
| `tool` | Takes an action (API/code/fetch/extract) or advanced preprocessing; returns a result. | Tools / Input Formatting |
| `processor` | Deterministic transform, no model call (input formatting OR post-processing). | Input Formatting / Post-process |
| `harness` | Runs a model behind a trust boundary; declares model_targets + packs. | Model |
| `adapter` | Provider-neutral model transport (swap local↔hosted). | Model |
| `pipeline` | A DAG of the above that completes a task end to end. | Backbone |
| `pattern` | A reusable workflow shape (ReAct, Self-RAG, refuse-on-redacted…). | (cross-cutting) |
| `rubric` | An evaluation contract: dimensions, weights, scoring method, evidence. | Evaluate |
| `benchmark` | A pipeline run vs a labeled set with a rubric + judge → comparable score. | Evaluate |
| `dataset` | Typed inputs/outputs/labels with provenance. | Evaluate |

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
