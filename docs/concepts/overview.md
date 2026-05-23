# Overview

The Open Harness Hub is a **specification + content catalog + static
site**. It standardizes how the modular pieces of an AI-assisted
system are described, so they can be combined into pipelines,
benchmarks, and tools across any industry.

## Four layers

```
Layer 4 - Benchmarks & Evaluations
              ▲
Layer 3 - Pipelines (compositions of harnesses + rules + tools)
              ▲
Layer 2 - Harnesses (named workflows around a model or trust boundary)
              ▲
Layer 1 - Knowledge packs · Logic packs · Rule packs · Tools · Personas · Adapters · Schemas
```

## What you get

- A **manifest format** (YAML) for every layer, validated against
  JSON Schemas in `schemas/`.
- A **catalog** of starter artifacts you can copy and adapt.
- A **runner** (`scripts/run_pipeline.py`) that walks a pipeline DAG
  step-by-step and produces a trace.
- A **playground** (`hf-space/`) that exposes the runner over a
  Gradio UI so visitors can try a pipeline on sample data.
- A **set of database mappings** (PostgreSQL, MongoDB, Redis, vector
  DBs) so the catalog can persist anywhere.
- A **site** that renders the catalog as a browsable docs hub on any
  free host.

## What this is NOT

- It is not a hosted inference provider. Bring your own model adapter.
- It is not a fork of any existing eval framework. It plays well with
  them - a benchmark in this catalog can drive a run in any framework.
- It is not industry-specific. Industry tags are first-class but
  optional.

## Reference inheritance

The patterns were generalized from Taylor Amarel's
[DueCare safety ecosystem](https://github.com/TaylorAmarelTech/gemma4_comp)
and [LLM Safety Framework](https://github.com/TaylorAmarelTech/llm-safety-framework).
Those repos are cloned to `_reference/` for offline study and are
**not** republished here.
