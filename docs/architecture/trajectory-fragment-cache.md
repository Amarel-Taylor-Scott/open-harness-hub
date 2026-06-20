# Trajectory Fragment Cache

A million-object registry can become more than a catalog. It can become an
experience layer: a searchable store of solved subproblems, intermediate
fragments, tool-call patterns, verification steps, and cost traces.

The useful unit is not a whole prompt. It is a fragment:

- plan node;
- tool call and result;
- code patch pattern;
- reasoning summary;
- verification step;
- error recovery;
- prompt template;
- response snippet.

## How The Database Helps

The object database can store fragments with:

- task signatures and input/output fingerprints;
- embeddings and keyword text;
- labels, domains, and dimensions;
- provenance and privacy boundaries;
- verification status;
- model route and cost traces;
- reuse events showing when a fragment saved cost or latency.

At serving time, a harness can retrieve candidate fragments, ask a cheap
verifier or reranker to select safe pieces, stitch them into a plan or draft,
and fall back to a stronger model only when novelty or risk requires it.

## Retrieval Shape

```text
new request
-> normalize task signature
-> retrieve fragments by keyword/vector/label/graph
-> filter by privacy, license, freshness, and domain
-> rerank with cheap verifier
-> stitch plan/tool-call/code/answer draft
-> verify against tests, schemas, citations, or rubrics
-> record cache reuse event and cost delta
```

This does not replace a model. It reduces repeated work and gives the model
better candidates for recurring subproblems.

## Safety Boundary

Only fragments that are legally reusable, privacy-screened, and verified should
enter the shared cache. Tenant-private fragments can still be useful inside a
tenant boundary but must not leak into public or cross-tenant indexes.

For Open Harness Hub, this means public synthetic examples and curated
fragments can be shared broadly, while real customer trajectories require
tenant isolation, redaction, retention controls, and explicit consent.

## Why Harness Diversity Matters

Long agentic and multimodal harnesses generate richer fragments than one-shot
Q&A. They expose plans, tool calls, failed attempts, recoveries, test results,
review tickets, cost traces, and deployment choices. Those traces are exactly
the material needed for cache-assisted pipeline construction.
