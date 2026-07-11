# Showcase Gap Feedback Loop

Showcase coverage should feed the next component-generation batch. A partial or missing template step is not only a report; it is a targeted request for a better component candidate.

## Flow

```text
showcase templates
-> showcase candidate coverage
-> missing-component-requests.jsonl
-> targeted component seeds
-> standard candidate row families
-> load audit, review, promotion, CDC
```

The feedback loop keeps daily showcase pipelines and daily component generation aligned. Product demos reveal weak spots, and weak spots become the next generated candidates.

## Current Command

```bash
python3 -m scripts.factory.showcase_gap_component_seeds \
  --missing-requests dist/showcase-candidate-coverage/2026-05-28/missing-component-requests.jsonl \
  --output-dir dist/showcase-gap-components/2026-05-28
```

## Output

The generator writes:

- `showcase-gap-component-seeds.jsonl`;
- standard row families under `rows/`;
- `showcase-gap-component-summary.json`.

Each partial/missing coverage request becomes one targeted normalized component candidate plus its standard row families (index records, label assignments, dimension values, object/entity refs, canonical entities, dedupe cluster, embedding work row, and a review ticket). These are database-backed candidates. They are not public component definitions and they are not promoted automatically.

## Coverage reporter (consolidated)

> Folds the durable design of the merged showcase-candidate-coverage plan — the deterministic coverage reporter that produces the `missing-component-requests.jsonl` this loop consumes. Frozen per-run sample counts live in the archived source.

Daily showcase pipelines are not disconnected demos: each template step needs a path to staged component candidates, and weak spots feed the next generation batch. The coverage reporter (`scripts/factory/showcase_candidate_coverage`) reads generated showcase template JSON + staged `normalized-objects.jsonl` and emits `showcase-step-coverage.jsonl`, `missing-component-requests.jsonl`, and a coverage summary. It is deterministic and side-effect free — it does not promote candidates, load Postgres, or publish templates. Each step is scored `covered` (strong domain + role match in staged candidates), `partial` (weak signal), or `missing` (create a generation request for the next daily batch). Matching is intentionally simple at this stage — domain aliases, industry overlap, step-role keywords, risk tier, pipeline-step labels — and later versions can add pgvector, BM25, graph edges, and LLM reranking. This closes the loop between daily product demos and the daily component factory: missing strong components become new generation requests carrying the needed domain, role, risk tier, cost profile, deployment target, and labels.

## Review Boundary

Gap-derived candidates often come from high-risk templates. They must keep the same gates as other generated rows:

- source governance;
- normalized object schema;
- entity recognition and linking;
- fuzzy dedupe;
- keyword/vector/graph/facet index records;
- review tickets;
- content approval before promotion;
- CDC before active use.
