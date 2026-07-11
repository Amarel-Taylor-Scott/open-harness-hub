# shared-backend-components (`aidoneright-shared-backend-components`)

The **computational substrate for executable capability** — the backend layer the whole **AI Done Right**
portfolio sits on. It is a database-backed **registry federation** of reusable AI-pipeline components,
subcomponents, primitives, primitive templates/cards, task/pipeline templates, and registry metadata rows, the
**factory** that generates and stages them, the **service-plane**
of small HTTP services behind the seams, the **code graph**, and the two deterministic-naming planes.

It is product-neutral reusable infrastructure. It returns **pointers and shapes, never truth**
(`serves_truth = false` at this layer) — truth is a downstream product's job. Products consume the
substrate; the substrate never consumes a product.

**North star (one line):** the database-backed component network + factory + service-plane that scales
from thousands to millions of rows without turning every row into a static file, and that every product in
the portfolio consumes.

## What lives here (its own job)

- **Seven primitives + component/template taxonomy** — everything reduces to Input · Knowledge Corpus · If
  Statement · Action · Loop · Stop/End · Output; a component is an active reusable unit, a subcomponent is
  a smaller unit inside it, and templates/cards are reusable shapes derived from real artifacts. Use
  **components / subcomponents / templates** in new prose.
- **Registry federation** — many source catalogs behind ONE uniform port
  (`list / lookup / search / explain`), layered `core_curated` → `staged_massive` → `candidate_feeds` so it
  scales without drowning the model, with a strict staged→core promotion boundary.
- **Factory** — generates candidate rows into JSONL staging + Postgres/pgvector load plans, preserving the
  required row families; admission is two-axis (must **lift** AND the lift must be **structural/durable**).
- **Storage tiers** — Config (JSON in git) / Operational (SQLite → Postgres + pgvector) / History
  (warehouse), all behind one `record_store` port.
- **Service-plane** — small HTTP services behind same-origin seams; the catalog projection the frontends
  read is served over the `/registry/...` seam.
- **Code graph** — grep-as-graph over the substrate's own code, ranking the strong connections you must
  audit before/after a change.
- **Two naming planes** — the pyprefix scheme for CODE objects and the `canonical_id` single source for
  generated DATA ids, which make grep-as-graph exact.

The internal picture, with the exact backing modules, config registries, and current live/partial status
of each substrate layer, is in [`context/blackbox.md`](context/blackbox.md).

## Layout

- **[`context/`](context/)** — this repo's grounding. Start with:
  - [`context/blackbox.md`](context/blackbox.md) — the standalone internal view: what the substrate owns,
    section by section, each claim linking its backing repo doc or machine source.
  - [`context/edges.md`](context/edges.md) — the detailed edges view: the dependency law, inbound/outbound
    interfaces, the seam table, and the ten compatibility contracts to preserve when the substrate is
    managed separately.
  - Supporting notes and sub-folders (`architecture/`, `concepts/`, `ingestion/`, `status/`, `strategy/`,
    `workers/`, and more) hold the deeper reference material the two files above link into.
- **[`EDGES.md`](EDGES.md)** — the generated, minimal cross-repo contract: this repo's role, what it
  exposes, who consumes it, what it may consume, and the forbidden edges. This is the only cross-repo
  context a session here needs — the neighbors' published edges, not their internals.
- **[`CLAUDE.md`](CLAUDE.md)** — the agent operating manual: the inherited laws, the default fast path, how
  to add work, and safety/scope.

The **standards** (the eight inherited laws) live in
[`../dev-rules-context/standards/`](../dev-rules-context/standards/) — linked, never copied. `CLAUDE.md`
carries their operating summaries; the standard files are canonical.

## How to work in this repo

1. Read `CLAUDE.md`, then `context/blackbox.md`, then `context/edges.md` + `EDGES.md`.
2. **Reuse-first.** Before building anything, confirm it does not already exist — the reinvention guard,
   the substrate-map check, and a codegraph audit answer "this already exists, don't rebuild it," the
   highest-ROI decision here.
3. **Fast path, not full rebuilds.** Validate and index only the changed paths and run the proof umbrella;
   full release gates only on schema/vocabulary/broad-ref changes.
4. **Audit neighbors** on the code graph before and after editing any `.py` symbol, and update
   load-bearing neighbors in the same change.
5. **Honor the boundaries.** Every generated row is born a candidate (`serves_truth = false`); ids come
   from the one `canonical_id` authority; version lives in metadata, never a name; keep the registry port
   verbs and the row families stable; report the six promotion stages separately.

## Edges (from `EDGES.md`)

- **This repo's role:** the SUBSTRATE every product consumes — registry + factory + catalog, codegraph,
  naming planes, eval, storage tiers, pipelines, credential plane. Reusable infrastructure,
  product-neutral.
- **Exposes:** registry, primitives, codegraph, eval-harness, storage-tiers, credential-plane.
- **May consume (via its published interface only):** `dev-rules-context`
  (`aidoneright-dev-rules-context`) — standards, `contracts/surface-registry.json`, check tools, `_shared`.
- **Who consumes this repo (keep these interfaces stable):** aidevobserver, api-endpoint-wrappers, baltor,
  context-injection, openhubforai, scraping, teleon.
- **Forbidden (never depend on these — the boundary law):** `teleon` and `baltor` — the substrate is
  product-neutral; products consume it, not the reverse. Consume a neighbor only via its exposed interface,
  never by reading or importing its source.
