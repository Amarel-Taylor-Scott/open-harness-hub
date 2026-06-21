# Development vs Product separation (2026-06-21)

> Owner directive: make it clear which research/tools/loops are for **development** (building + improving the platform)
> vs the **product** (the runtime that serves customers), and keep their storage + access separate. Development research
> must never mix with product modules/actions.

Canonical classification: `architecture/plane_separation.json` (enforced by `scripts/check_plane_separation.py`).

## Two planes

| | **DEVELOPMENT plane** | **PRODUCT plane** |
|---|---|---|
| **Purpose** | research + review + improve OUR codebase/product | the runtime that serves customers |
| **Lives in** | `scripts/` (tools) + `docs/goals/` (loops) | `src/teleon/`, `src/baltor/` (modules) |
| **Examples** | multi-model improvement loop, panel review, external review, **research radar** (competitors/repos/news/gaps), code/symbol graph, context-pack builder, archiver, dashboards | capability tasks (extraction, enrichment, OFAC screening), the descent runtime, dispatch + execution providers, serve + receipts |
| **Data** | `data/dev-intel/` (findings, research-radar hits, sweep cursor), `data/panel-reviews/`, `docs/reviews/`, `docs/context/` | `data/descent-attempts/` (runtime brain) + the `storage_tier_policy` product streams (cdc_events, version_history, component_candidates, object_embeddings) |
| **Access** | owner / CI / agents during development ONLY — never returned to a customer, never used in product serving | tenant-scoped + governed (serves_truth law, receipts, promotion boundary); customer-facing |
| **Launched by** | the owner via `/loop` or `/goal` (improvement loops) | the runtime, on a customer/agent request |

## Shared infra (the seam that keeps them decoupled)
Both planes need a couple of low-level pieces, so those live in **`shared_infra`** — NOT in either plane's tools:
- `scripts/_llm_client.py` — the OpenAI-compatible LLM client (product `real_steps` AND the dev review/sweep tools call it).
- `scripts/_jsonl_store.py` — the SQLite-WAL append-log behind the JSONL durability contract.

This is why **product never imports a dev tool**: when the runtime needs to call a model it imports `_llm_client`
(shared), not `external_review` (dev).

## The rules (enforced)
1. PRODUCT modules (`src/teleon`, `src/baltor`) MUST NOT import DEVELOPMENT tools (they MAY import `shared_infra`).
2. DEVELOPMENT tools live under `scripts/` (not `src/`), MAY read product infra, and MUST NOT write to product data paths.
3. DEVELOPMENT data lives under `data/dev-intel/` (+ `data/panel-reviews/`, `docs/reviews/`, `docs/context/`);
   PRODUCT data lives in the `storage_tier_policy` product streams.
4. Every `storage_tier_policy` stream declares `plane: development | product` (e.g. `panel_reviews` = development;
   `descent_attempts` = product).
5. Model output + research findings are CANDIDATES (`serves_truth=false`) on BOTH planes; a DEV candidate never reaches
   product serving.

## Why it matters
Mixing the two is how a competitor-research note or a code-review opinion accidentally ends up in a customer answer.
The boundary keeps **discovery ≠ trust** physical: dev intelligence is quarantined to `data/dev-intel/`, the runtime
serves only governed product data, and the only bridge is shared, dumb infra.
