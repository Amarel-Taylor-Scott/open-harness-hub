# Wrapper Contracts — stable surface, replaceable bones (C32 + C34 direction)

**Stable envelope outside. Replaceable logic inside.** Modules depend on versioned input/output contracts,
never on each other's bones — so we can change a parser, queue, vector DB, LLM, graph backend, storage
backend, or tenant-isolation model without breaking the outside shape.

Every change-prone boundary has three layers:
1. **Contract** — the stable data shape (the five envelopes + artifact/LLM/vector schemas).
2. **Port / wrapper** — the interface the rest of the system calls (`src/baltor/ports/*`, `scripts/runtime/ports.py`).
3. **Adapter / implementation** — the swappable logic behind it (`src/baltor/adapters/*`, providers).

| Stable | Swappable |
|---|---|
| CommandEnvelope / EventEnvelope / ArtifactEnvelope / ProcessorResult / ErrorEnvelope | queue, bus, storage backend |
| ProcessorResult | processor implementation |
| LLMRequest / LLMResponse | model / provider / endpoint |
| Vector request/result | embedding model / vector DB |
| Conflict / Reconciliation | detection + reconciliation logic |
| TenantPolicy | tenant isolation implementation |

## Already shipped (C32) + governed (C33)
The envelopes, `ProcessorHarness`, `ProcessorRegistry`, `RuntimeContext` + ports, the deterministic vector
provider, and the stub-first **LLM gateway** all exist and are proven; CFPB decomposition runs through the
harness. C33 added the spine + the **anti-bypass rule**: a processor may not call a boundary directly when a
port exists (`check_no_direct_provider_bypass`) — no raw `sqlite3`, no global `BUS`, no vendor LLM SDK
outside the gateway.

## Anti-patterns (now failing checks)
- `from scripts.ingest.decompose_structured import …` inside the runtime core → use the registry.
- `openai.chat.completions.create(...)` anywhere → use `ctx.llm_gateway.complete(...)`.
- `sqlite3.connect(".agent/durable.db")` in a processor → use `ctx.artifact_store` / the durable port.
- `BUS.publish(...)` in a processor → use `ctx.event_bus.publish_event(...)`.
- a web page writing durable truth → dashboards are projections only.

## Next (C34 wrapper migration — deferred, reason recorded)
Formalize the remaining ports (SourceAdapter / ParserProvider / Decomposer / ConflictDetector / Reconciler /
ContextPackBuilder / ReceiptRenderer) under `src/baltor/ports`, migrate `scripts/runtime` →
`src/baltor/runtime`, and move the C32 contract layer into the spine. The contracts + harness + key ports
+ CFPB-via-harness + stub LLM + vector provider already exist (C32) and are now governed (C33); the
remaining work is wiring/migration, not new substrate — a coherent standalone pass.
