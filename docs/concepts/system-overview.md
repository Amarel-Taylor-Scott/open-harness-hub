# System overview — how it all fits together

One read that connects everything: the **conceptual model** (what a component is), the **compiler** (how a sentence
becomes a running pipeline), the **registries** (the substrate), the **storage of context** (where it lives and how it
scales), the **tools** (and how they're invoked uniformly), the **skills**, and the **platform** that serves it — all
held together by one **governance spine**.

> The whole thing in a sentence: **a database-backed network of reusable components, plus a compiler (the descent) that
> turns a capability statement into the cheapest *bounded, verified* DAG of those components, under governance that keeps
> truth and efficiency separable.** The model proposes; the registry, the type system, and the descent dispose.

The product family: a holding company over **Baltor** (governs **truth** — provenance, verify, CDC), **Teleon** (governs
**efficiency** — the compiler/runtime, the descent), and **OpenHarnessHub** (the open ecosystem + the CapabilityTask
spec). Canonical: `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`, visual map at `dist/architecture/index.html`.

---

## 1. The conceptual model — what a "component" is
Everything is built from a small set of **primitives** that compose upward into bigger reusable units.

- **Primitives → harnesses → pipelines → benchmarks** — the four layers. See [Layers & primitives](layers.md).
- **The seven primitives** — Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output. A persona,
  tool, processor, harness, or rubric is all an **Action**. See [Taxonomy](taxonomy.md).
- **Pre-API / API / post-API processes** — what happens before, during, and after a model call (intake/normalize/route
  → the call → verify/score/review). See [Pre/post-API processes](pre-post-api.md).
- **Multimodal pipelines** — text, image, audio, video components in the same graph. See [Multimodal pipelines](multimodal.md).
- **The capability-gap lens** — we build for the **negative space** where base models lack capability, not the head of
  the distribution. See [Capability valleys](capability-valleys.md).

## 2. From a sentence to a running pipeline — the compiler
A capability statement (or conversation) is **compiled** into the cheapest bounded, verified DAG:
**retrieve → compose → bound & verify → descend → execute**. The descent is "make it work, then make it efficient":
deterministic components first, the LLM only for the residual. Full mechanism:
[Compiling capabilities into bounded DAGs](compiling-capabilities-into-bounded-dags.md).

## 3. The registries — the substrate (single source of truth)
Components and their wiring live in **versioned registries**, never hand-typed in two places (`docs/codex/no-magic-values.md`).
The canonical config registries (JSON in git, the *config* storage tier) include:

- `architecture/tool_registry.json` — the curated tools; `architecture/tool_planes.json` — agnostic tool **planes**.
- `architecture/capability_ladders.json` — each capability as a cost-ordered, deterministic-first descent ladder.
- `architecture/plane_io_contracts.json` — the typed I/O (consumes→produces) per plane.
- `architecture/ml_model_registry.json` — classical/predictive ML model **types** (random forest → forecasting → …).
- `architecture/external_api_registry.json` — third-party APIs (RapidAPI/Apify) as components.
- `architecture/credential_registry.json` + `architecture/access_policy.json` — keys/secrets and who may use what.
- `architecture/registry_layers.json` — the **layered** model + `architecture/storage_tier_policy.json` — the storage tiers.

The catalog is **layered** so it scales without drowning the model: a **curated core** (read by the descent), a
**staged-massive** tier (scraped candidates, thousands → millions, candidate-only until promoted), and a **vector search
index** (every component labeled with text + keywords + a vector). Background:
[Database-backed component store](../architecture/database-backed-component-store.md),
[Compiled-unit registry](../architecture/compiled-unit-registry.md),
[External capability catalog](../architecture/external-capability-catalog.md),
[Vectorized registry hosting](../architecture/vectorized-registry-hosting-2026.md),
[Peer registries](../comparison/peer-registries.md). The **promotion boundary** (source + dedupe + content-hash +
license + review) is what separates a *candidate* from an *active* component.

## 4. Storage of context — where it all lives and how it scales
Three **storage tiers**, each fit for purpose (`src/teleon/storage/record_store.py`, `architecture/storage_tier_policy.json`):

- **Config** — JSON in git (the registries above): reviewable, diffable, versioned.
- **Operational** — SQLite locally / **Postgres + pgvector** in the cloud (the live records: staged tools, discovered
  tools, the component search index) behind one `record_store` port.
- **History** — the warehouse (CDC events, versions, audits) for scale to millions/billions.

Context itself is first-class: **context objects** with standards + an event-driven sync + a control loop, plus a
**cache-shaped prompt ABI** so context is token-efficient. See [Database-backed context catalog](../architecture/database-backed-context-catalog.md),
[Baltor context object standards](../architecture/baltor-context-object-standards.md),
[Context control loop](../architecture/context-control-loop.md),
[Prompt ABI & cache-shaped context](../architecture/prompt-abi-and-cache-shaped-context.md),
[Context worker registry](../architecture/context-worker-registry.md). Scale + lineage:
[100M-component infrastructure](../architecture/hundred-million-component-infrastructure.md),
[Component CDC versioning](../architecture/component-cdc-versioning.md),
[Source sync versioning](../architecture/source-sync-versioning.md),
[Generated object storage](../architecture/generated-object-storage.md),
[Postgres pgvector bootstrap](../architecture/postgres-pgvector-bootstrap.md),
[Database representations](databases.md).

## 5. Tools — and how they're invoked uniformly
Tools are grouped into agnostic **planes** (an LLM plane, an embedding plane, an OCR plane, a search plane, …). Each
plane sits behind an **agnostic port** (`select_X("auto")` + `register_X_adapter` drop-in), so a future provider drops in
with zero caller change. On top, a **uniform Component layer** gives every tool one shape —
`Component.invoke(typed_inputs) → typed_outputs` — and lets a compiled DAG actually **run** on real ports; swapping a
component in is **proof-gated** by a conformance check; an unwired plane is **honestly unavailable**, never faked. See
`docs/strategy/component-standardization-and-dag-verification-2026-06.md`. Third-party APIs are components too
(`external_api_registry.json`), gated by the **credential plane** + **access policy**.

## 6. Skills — reusable capability units
A **skill** is just a high-level **Action** (a packaged persona/tool/processor/harness/rubric) and composes into a DAG
like any other component — so a skill can be retrieved, type-checked, descended, and verified the same way. Background on
the overlap with agent skill systems: [Claude Code skills overlap](../research/claude-code-skills.md). The open
CapabilityTask spec (CTS) is the portable definition that lets skills/capabilities move between Baltor, Teleon, and the
open hub.

## 7. The platform & runtime — how it's served
- **Primitive platform backend** — core services, storage layout, indexes, the search flow. See [Primitive platform backend](../architecture/primitive-platform-backend.md).
- **SaaS operating platform** — container topology, the core data model, the search stack, billing/metering, deployment
  phases. See [SaaS operating platform](../architecture/saas-operating-platform.md).
- **Service auth & consumption** — identity types, the consumption matrix, token/key rules. See [Service auth and consumption model](../architecture/service-auth-and-consumption-model.md)
  and [Local dev tunnels and auth](../architecture/local-dev-tunnels-and-auth.md).
- **North-star architecture** — [North star platform architecture](../architecture/north-star-platform-architecture.md).
- **Hosting** — agent-automatable deploy (Fly + Cloudflare Workers); `docs/strategy/hosting-decision-matrix.md`.

## 8. The governance spine (cross-cutting, always on)
The rules that hold across every layer (full contracts under `docs/codex/`):
- **`serves_truth=false`** on compute output — a result is a *candidate*; **Baltor** dispositions truth with provenance.
- **discovery ≠ trust** — finding a tool/source is not adopting it.
- **Dependency law** — Baltor → Teleon → OpenHarnessHub, never the reverse.
- **Lossless distillation** — distillation/compression/promotion never deletes the raw layer, lineage, or losers.
- **No magic values** — counts and shared constants are computed/single-sourced, never typed twice.
- **Change verification** — every change carries a *warrant* (intent / corroboration / principle); no orphaned contradictions.
- **Promotion boundary** — candidate-load-ready ≠ tenant-visible.
- **Plane separation** — product `src/` imports no dev tooling.
- **Honest-unavailable** — when a lane is offline we say so; we never fabricate.

---

## How one request flows through all of it (worked trace)
*"Extract the parties and rent from these lease PDFs into our schema."*
1. **Conceptual** — this is a pipeline of primitives: Input (PDF) → Actions (OCR, field-parse, validate) → Output (record).
2. **Retrieve** (§3) — hybrid search over the labeled registry returns a small pool of real components (an OCR tool, a
   field parser, the LLM), filtered by the caller's **access policy**.
3. **Compose** (§2) — the LLM wires a DAG from that pool, deterministic-first; a hallucinated tool is rejected.
4. **Bound & verify** (§2) — the DAG is type-checked, every input is satisfied, and a dry-run proves it's runnable.
5. **Descend** (§2) — the cheapest viable rung is chosen per step (text before OCR; parser before LLM).
6. **Execute** (§5) — the verified DAG is lowered to real ports via the uniform Component layer and run; large payloads
   pass as references, not blobs.
7. **Store & version** (§4) — inputs/outputs/lineage land in the right storage tier with CDC.
8. **Govern** (§8) — the extracted fields are `serves_truth=false` candidates; Baltor's verification rail dispositions
   them with provenance before anything is asserted as true.

## Documentation map
| Area | Start here |
|---|---|
| Concepts: layers & primitives | [layers.md](layers.md) · [taxonomy.md](taxonomy.md) · [pre-post-api.md](pre-post-api.md) · [multimodal.md](multimodal.md) |
| The compiler (sentence → DAG) | [compiling-capabilities-into-bounded-dags.md](compiling-capabilities-into-bounded-dags.md) |
| Registries | `architecture/*.json` (tool/planes/ladders/io-contracts/ml/external-api/credentials/access/registry-layers) · [database-backed-component-store](../architecture/database-backed-component-store.md) · [compiled-unit-registry](../architecture/compiled-unit-registry.md) · [external-capability-catalog](../architecture/external-capability-catalog.md) |
| Context storage & scale | [storage tiers](../architecture/postgres-pgvector-bootstrap.md) · [context catalog](../architecture/database-backed-context-catalog.md) · [context control loop](../architecture/context-control-loop.md) · [100M infra](../architecture/hundred-million-component-infrastructure.md) · [CDC versioning](../architecture/component-cdc-versioning.md) |
| Tools & uniform invoke | `docs/strategy/component-standardization-and-dag-verification-2026-06.md` · [tool planes](taxonomy.md) |
| Skills | [Claude Code skills overlap](../research/claude-code-skills.md) |
| Platform & runtime | [primitive platform backend](../architecture/primitive-platform-backend.md) · [SaaS operating platform](../architecture/saas-operating-platform.md) · [service auth & consumption](../architecture/service-auth-and-consumption-model.md) |
| Governance | `docs/codex/` (no-magic-values · lossless-distillation · change-verification-contract) |
