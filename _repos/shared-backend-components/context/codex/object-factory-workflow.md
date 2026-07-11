# Object Factory Workflow

Object factories turn large source surfaces into validated, indexed primitives.

## Factory Loop

1. **Select source surface**
   Choose a high-value source such as O*NET, ESCO, BLS ORS, CDC, Federal Register, Regulations.gov, Kaggle, GitHub, package registries, workflow repos, SOP libraries, public forms, or standards indexes.

2. **Define extraction schema**
   Decide which object types to extract: tasks, questions, facts, evidence requirements, tools, policies, checklists, decision gates, rubrics, benchmarks, or deployment blueprints.

3. **Create or reuse tools**
   Prefer abstract tools that can support multiple providers: source lookup, archive lookup, normalizer, work atom extractor, safety scanner, deduper, cost estimator, and index writer.

   For a no-key local baseline, use:

   ```bash
   python3 -m scripts.factory.object_factory_workers --self-test
   ```

   This exercises the first worker slice: page-to-Markdown conversion, normalized object extraction, sensitive-data screening, and deterministic polish/verification.

4. **Create knowledge pack**
   Store high-volume objects in the database-backed component store. Use `catalog/knowledge-packs/data/<pack>/*.jsonl` only as portable staging/import/export data, and add a public component definition with provenance and indexing settings when useful.

5. **Create pipeline**
   Add a pipeline that shows how the source becomes indexed objects and how the objects feed RAG or pipeline generation.

   Daily operation should create or refresh 5 to 25 preconfigured showcase pipelines. A showcase pipeline should have a named use case, expected inputs and outputs, suggested component sequence, cost profile, review gates, and deployment target. Keep these as reusable templates or database-backed rows when volume is high.

6. **Score candidates**
   Rank generated objects using demand, usefulness, complexity, deployment frequency, cost savings, and out-of-box LLM weakness.

7. **Deduplicate**
   Use keyword, vector, graph, and model-polished dedupe. Link near-duplicates rather than losing provenance.

   For daily partitions, dedupe before load planning. Multiple partitions can share source records, canonical entities, labels, or stable IDs, so raw JSONL line counts must be merged by primary key before they are reported as staged database counts.

8. **Validate and rebuild**
   For small batches, validate and render only changed component definitions:

   ```bash
   python3 scripts/validate.py <changed component-definition paths>
   python3 scripts/build_catalog_pages.py --paths <changed component-definition paths> --update-index
   ```

   For release snapshots or schema migrations, run the full commands:

   ```bash
   python3 scripts/validate.py
   python3 scripts/build_catalog_pages.py
   ```

   If the batch rewires component references, refresh the component-id cache and run a selected global ref check:

   ```bash
   python3 scripts/build_component_id_index.py
   python3 scripts/validate.py --global-ref-check <changed component-definition paths>
   ```

## Batch Shape

For manual Codex sessions, keep a batch small enough to validate:

- one architecture or research doc;
- one knowledge pack;
- one data JSONL seed;
- one to three tools;
- one pipeline;
- optional nav update.

For daily-scale runs, the batch must also produce or refresh:

- 1,000 to 5,000 database-backed component candidates;
- 5 to 25 showcase pipeline templates;
- a staged load audit when two or more partitions are involved;
- review tickets for high-risk domains.

For automated factories, generate to `_inbox/` or a staging branch, validate, sample review, then publish.

For worker fleets, route each job through a narrow worker contract. Do not let a single LLM prompt fetch, convert, redact, extract, verify, label, dedupe, and publish in one opaque step.

## Daily Showcase Pipeline Criteria

A showcase pipeline is useful when it demonstrates a complete product path:

- problem sentence a user might type;
- pre-LLM components such as intake, OCR, normalization, entity linking, or retrieval;
- LLM or model-routing components;
- post-LLM components such as verification, scoring, escalation, formatting, or CDC propagation;
- cost profile such as cheap, balanced, quality, local-first, or high-assurance;
- review boundary and risk tier;
- deployment shape such as local Python, Render worker, Postgres/pgvector, container worker, MCP setup, or cloud function.

Good daily showcase output is better than another generic example. Prefer specific pipelines that would help a buyer understand the product: “cheap OFW placement-fee overcharge triage,” “water sample public notice gate,” “used-car listing evidence review,” “SOC alert quality and escalation,” or “government fact update propagation.”

## Output Types

Prefer this progression:

1. source surface map;
2. extraction tool;
3. normalized object pack;
4. index build pipeline;
5. example use-case pipeline;
6. rubric and benchmark;
7. deployment blueprint.
