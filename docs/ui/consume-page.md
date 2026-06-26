# /consume page (ingestion → consumption, projection-only)

**Purpose.** A single page that shows the whole governed CFPB path firing — ingestion → … → served
`ContextResponse` — as a **projection over the API**. It computes no truth: it fetches and renders.

**Owner.** `web/baltor/consume.html` (served by `scripts/baltor_admin_demo_server.py` at `GET /consume`).
**Data sources.** `GET /api/context/serve?tenant_id=demo&corpus=cfpb&require_optimized=true` (ungated projection
of the served `ContextResponse`) and `GET /api/runtime/sections` (the maturity scoreboard).

## Panels

One **"Run CFPB Ingestion → Consumption"** button →
Answer · Ingestion/Source artifacts · Atomic facts (served) · Held-out allegations/warnings · Artifact
ledger·Vectors·Graph (lineage) · Conflicts·Reconciliation · Receipts (verification·optimization·consumption) ·
Freshness · ContextResponse (raw) · Section maturity · Provider status (candidates).

## Reference result visible

answer **"10 business days"** · served facts with their source handles · **FAQ-30 only under held-out
warnings** · the three receipt ids · section maturity (reference M10 count) · candidate providers.

## Rules (enforced by `check_consumption_ui` + `check_architecture_dashboard_projection_only`)

- Projection-only: the page contains no durable writes (`durable.db`/`INSERT`/`sqlite3`), no secrets
  (`OH_SHOWCASE_TOKEN`/`sk-`), no private memory (`.agent/`, `MEMORY.md`, `/memory/`, `baltor-goal-loop`).
- Reads the API only; never fabricates `served_facts`/`ContextResponse` in JS.
- Uses the **ungated GET** projection so the page needs no token; the POST `/api/context/serve` stays token-gated.

## Commands

```
PYTHONPATH=. python3 scripts/check_consumption_ui.py --self-test
PYTHONPATH=. python3 scripts/check_demo_console_links.py --self-test
PYTHONPATH=. python3 scripts/check_architecture_dashboard_projection_only.py --self-test
# live: open http://127.0.0.1:9307/consume
```

## Known limitations / opportunities

- Panels render the API projection; deep per-artifact drill-down (vector ids, full graph path) lands with the
  vector/graph lineage opportunity (`OPP-vector-graph-lineage`).
- Adding the page route grows the admin-server monolith (split target — `OPP-admin-monolith-split`).
