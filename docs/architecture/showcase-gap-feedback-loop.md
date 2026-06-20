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

The first run converted 4 humanitarian disaster-response partial coverage requests into:

- 4 targeted normalized component candidates;
- 20 index records;
- 60 label assignments;
- 28 dimension values;
- 50 object/entity refs;
- 50 canonical entities;
- 4 dedupe clusters;
- 4 embedding work rows;
- 4 review tickets.

These are database-backed candidates. They are not public component definitions and they are not promoted automatically.

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
