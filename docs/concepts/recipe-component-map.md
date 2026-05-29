# Recipe → component map (canonical, no placeholders)

Every step in the governed-model-call recipe (`scripts/showcase/builder.py::harness_recipe`)
resolves to a **real catalog component** — either a dynamically-selected one (persona, the
Knowledge Corpus being retrieved, the model harness, the rubric, the loop pattern) or a
**canonical default component** wired by name. No step is a bare "built-in" placeholder where a
component exists. Single source: the `canon` map in `harness_recipe` (mirrored in `web/app.js`).

## Organization: one bucket directory per phase

```
catalog/processors/
  retrieval/   R0–R6 + prompt steps  (chunkers, BM25/dense/fuzzy/exact-id retrieve, RRF, rerank,
               MMR/dedupe/source-precedence, context placement, HyDE/multi-query, compress,
               system-prompt, injection screen, JSON recover)   ← seed_retrieval_taxonomy_components.py
  clinical/    domain-specific decision-support gates                ← seed_clinical_triage_components.py
  deliver/     Deliver / emit (OUTBOUND): return · webhook · email · report · notify · escalate
  platform/    Platform actions (ON-PLATFORM): run-store · object-store · pgvector · postgres ·
               register-component · data-store+view · dashboard-widget · cache · memory
```
All seeded by the shared standardized builder `scripts/seed/component_seed.py` (consistent shape +
`attribution` provenance → traceable to the taxonomy + license).

## The canonical map (built-in step → component)

| Recipe step (phase) | Canonical component |
|---|---|
| Build the system prompt *(enrichment)* | `processor/system-prompt-builder` |
| Query transform *(enrichment)* | `processor/hyde-query-expander` |
| Chunk *(enrichment)* | `processor/recursive-character-chunker` |
| Rerank / fuse *(enrichment)* | `processor/cross-encoder-reranker` |
| Summarize / compress *(polishing)* | `processor/extractive-span-selector` |
| Select · order · de-conflict *(polishing)* | `processor/source-precedence-select` |
| Render the model-query template *(polishing)* | `processor/context-placer-edge` |
| Prompt-injection check *(query verification)* | `processor/prompt-injection-screen` |
| Verify JSON (recover) *(response verification)* | `processor/json-repair-coerce` |
| Deliver / emit *(deliver)* | `processor/deliver-return` (default; options → `deliver/*`) |
| Persist to platform storage *(platform)* | `processor/persist-run-store` (default; options → `platform/*`) |

Dynamically slotted (from catalog selection, not the canon map): **Add persona** → a `persona/*`;
**Retrieve** → the `knowledge-pack/*` corpus; **Call the right-sized model** → a `harness`/`adapter`;
**Re-verify** → a `rubric`/`benchmark`; **retry loop** → a `pattern`. Each step's `options` list is
the swappable-method menu (see `retrieval-and-prompt-taxonomy.md`); the default option's component is
the canonical one above.

## Why this matters
- **No placeholders** — the preview links each step to a real component ID, not "built-in".
- **Standardization** — one generator, one attribution convention, one bucket-per-phase layout.
- **Swappability** — an engineer (or the foundry) swaps a step's component without touching the flow.
