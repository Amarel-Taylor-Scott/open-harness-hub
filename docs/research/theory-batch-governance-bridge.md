# Theory Batch Governance Bridge

Theory-derived component candidates need the same governance boundary as daily production rows. The bridge reads a theory batch summary plus its staged load-audit summary, then emits:

- promotion readiness rows;
- review queue rows;
- embedding model profiles;
- sharded embedding execution plans;
- vector readiness summaries;
- one rollup summary that separates staged rows from active promotion.

It does not call models, write vectors, mutate Postgres, or promote components.

## Command

```bash
python3 -m scripts.db.theory_batch_governance_bridge \
  --theory-batch-summary dist/theory-component-batch/YYYY-MM-DD/theory-component-batch-summary.json \
  --load-audit-summary dist/theory-component-batch-load-audit/YYYY-MM-DD/summary.json \
  --output-dir dist/theory-batch-governance-bridge/YYYY-MM-DD \
  --run-id theory-batch-governance-YYYY-MM-DD
```

## Promotion Boundary

Candidate-table load readiness only proves the rows are structurally coherent: source records, dedupe clusters, content hashes, index records, and embedding work rows exist. Active promotion is stricter. High-risk theory-derived rows stay blocked until review tickets are resolved and real vectors are available.

## Embedding Boundary

The bridge emits local-first embedding plans by default. Hosted embedding profiles remain placeholders until pricing, privacy boundary, and tenant approval are attached to the run.
