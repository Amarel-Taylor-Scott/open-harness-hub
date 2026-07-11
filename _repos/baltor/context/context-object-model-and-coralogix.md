# Context Object Model (COM v0.2) + Coralogix positioning (owner design input, 2026-06-05)

Captured from two owner messages so the architecture isn't lost. **Status:** design direction, NOT
built. External standards/products cited by the owner (JSON-LD, W3C PROV, OpenLineage, MCP resources,
Coralogix capabilities/funding) are **owner-provided + pending independent verification** — verify
before any enters the runtime (verify-first). This doc records the *shape* + the *decisions*.

## 1. Context Object Model — COM v0.2 (the registry's data model)
This IS the design for Baltor's context registry (the repo's deepest north star). The owner's model:
a **property-document hypergraph** — stable envelope + flexible facets, relationships as first-class
objects, event-sourced versions/lineage, typed numeric dimensions.

```
context object = stable identity + flexible document body + facets + dimensions
               + unlimited relationship edges (first-class) + versions + lineage
               + policies + retrieval artifacts + runtime telemetry
```

Key decisions to adopt (all consistent with existing Baltor principles):
- **Stable envelope, flexible facets.** `id, type, tenant, source, title, body, facets, dimensions,
  security, versions, lineage` are stable; `facets/dimensions/attributes` are open + versioned.
  JSON-LD-compatible. (Matches our `ctx://…#fragment` handle contract + decomposition tree.)
- **5W1H facets** (`who/what/when/where/why/how`) on every object AND every relationship. `what.claims`
  carry `source_handle` — exactly our claims-attach-to-leaves rule.
- **Relationships are first-class objects** (`ctxrel://…`) + **hyperedges** (n-ary, e.g. an incident
  causal chain). Carry their own facets/dimensions/evidence/confidence/lineage. This is how you get
  "unlimited relationships" without fragile embedded arrays. (Our `context_memory_block` already emits
  `relationship.created` supersedes-edges — same idea; generalize it.)
- **Typed numeric dimensions** — never a naked `risk: 0.8`. Each score = `{value, scale, meaning,
  method, evidence[], computed_at, model/version}` and **is itself an artifact with lineage**. Useful
  set: risk, verifiability, authority, freshness, confidence, volatility, sensitivity, blast_radius,
  business_impact, retrieval_relevance, token_value_density, compression_loss, contradiction_score,
  compliance_criticality. (This is our two-axis lift gate generalized — keep `reason_codes.py` as the
  single source for the durability enums; dimensions reference it, don't redefine it.)
- **Event-sourced versioning/lineage** → immutable `ctxv://` versions, `ctxa://` artifacts,
  `ctxpack://` packs, `ContextEvent` for every ingest/retrieve/compress/approve/feedback. Map lineage
  to **W3C PROV + OpenLineage**. (Our receipts + content-hash CDC already do the spine of this.)
- **Typed projections** off one object: document(JSONB) · graph(nodes/edges) · search(BM25) ·
  vector(embeddings) · metric(dimensions) · lineage(PROV/OpenLineage) · **MCP(`ctx://` resources)**.
- **Layered storage** (NOT one DB): object store (raw) · Postgres JSONB (envelope+long tables) ·
  edge tables→graph later · OpenSearch (keyword) · pgvector/Qdrant (embeddings) · ClickHouse/Coralogix
  (telemetry) · OpenFGA+OPA (authz). Matches our existing storage rule.

→ **Action:** evolve `_repos/shared-backend-components/schemas/context/*` toward this envelope; generalize relationship objects +
hyperedges; make every score a lineage-carrying dimension. Sequence behind the proof point; this is the
registry substrate, built incrementally (one proven schema increment per pass), not a big-bang rewrite.

## 2. Does Coralogix overlap / compete with Baltor?
**Verdict: complementary, not a competitor — with ONE overlap zone and ONE strategic risk.**

| | Baltor | Coralogix |
|---|---|---|
| Plane | **Context** — what context exists, governed, versioned, source-linked, served | **Observability/Ops** — what *happened*, agent monitoring, telemetry, cost/usage |
| Owns | context-object graph, relationships, versioning, lineage, source-precedence, context-pack compression, policy/promotion, portable receipts | logs/metrics/traces/RUM, AI Center (guardrails/evals/AI-SPM), Code-Agents Observability, MCP server + `cx` CLI, Olly |
| Data gravity | durable governed/regulated knowledge | runtime production telemetry |
| Time | mostly pre-serve (governance gate) | mostly runtime/after-the-fact |

- **Genuine overlap — AI eval/guardrails:** Coralogix AI Center does guardrails+evals (hallucination,
  PII, injection, quality). Baltor has a Verification rail (lift matrix, swarm, verified_context_flow,
  context_diff). BUT different lifecycle points: **Baltor gates CONTENT before serving** (held-out
  would-be violations, source lineage); **Coralogix monitors RUNTIME LLM interactions** (app-level,
  observability). Adjacent, not the same job.
- **Narrow overlap — token-efficient agent output:** Coralogix `cx --o agents` (~90% fewer tokens)
  rhymes with our compression thesis, but it compresses *its own telemetry query results*, not general
  governed context. Not a competing compressor.
- **Complement (the 90%):** Coralogix is a **source** for Baltor (telemetry → debugging packs:
  `ctx://…/coralogix/{log,trace,metric,incident}`) AND an **observability backend** for Baltor (emit
  OTel GenAI spans for every context op → Coralogix dashboards/alerts). Coralogix explicitly states it
  is NOT the canonical context DB, relationship graph, version registry, or context-pack layer — i.e.
  it cedes exactly Baltor's territory.
- **Strategic RISK (be honest):** a well-capitalized adjacent player (owner cites $550M total) moving
  aggressively into "agent-native observability" + evals + guardrails + telemetry-as-context + MCP has
  the distribution (5k+ customers) and OTel ingestion to expand *down* into context/memory. The threat
  isn't today's product; it's platform-expansion + data-gravity (same shape as the Snowflake/Databricks
  risk in [[contextual-ai-competitor]] / [[moat-reframe-data-not-capability-gap]]).
- **Mitigation / position:** **integrate, don't compete.** Baltor = the governed context layer that
  feeds agents and emits OTel that Coralogix observes. Differentiate hard on **governed + regulated +
  versioned + source-linked + provable** data (the compliance beachhead), which is orthogonal to
  runtime telemetry and is not Coralogix's data gravity.

→ **Action (backlog, no-pip-friendly first steps):** (a) define an **OTel span vocabulary** for context
ops (`context.ingest/retrieve/compress/pack/verify…`) as a doc + a labeled SEAM (emit our existing bus
events shaped as OTel GenAI spans; a Coralogix exporter is a later swap); (b) add a `coralogix` source
adapter contract (telemetry→context object) as a SEAM. Both behind capability ports; Coralogix is a
swappable backend, never the canonical store. Owner-decision items (vendor selection, paid account)
stay parked.
