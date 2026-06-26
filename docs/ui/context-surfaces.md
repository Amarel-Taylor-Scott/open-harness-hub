# Context surfaces (the served UI index, projection-only)

Baltor serves six **context surfaces** — read-only web pages, each a **projection over the API**. Every
surface computes no truth: it fetches `/api/...` and renders. None writes durable truth, stores truth or a
secret client-side, or shows private memory. Together they let a viewer follow the whole context motion —
ingestion, the seven-stage pipeline, the served `ContextResponse`, configuration standards, the Determinism
Factory, and the native-output preview — without ever leaving a projection.

This file is the single index of every served surface. The discoverability / no-dead-surface guard
(`scripts/check_context_surfaces_index.py`) keeps it honest: every listed page must exist on disk, declare
itself projection-only, fetch a projection API, and carry no forbidden token. Adding a surface means adding it
here, to that guard's `SURFACES` table, and (MAIN integrates) to the hub cards in `web/baltor/hub.html`.

## Served surfaces

| Route | Page | What it shows | API namespace | Per-page proof |
|---|---|---|---|---|
| `/pipeline` | `web/baltor/pipeline/index.html` | the seven-stage pipeline journey (upload → decomposition → reconciliation → enhancement → optimization → verification → consumption), with the lossless / held-out lens at every stage | `/api/pipeline/*` | `scripts/check_pipeline_pages_full_stack.py` |
| `/memory` | `web/baltor/memory.html` | the memory projection — artifacts with `claim_status`, source handles, held-out vs promoted, connectors, sync, contradictions, freshness, reconciliation receipts, providers, traces | `/api/memory/*` | `scripts/check_memory_page_projection_only.py` |
| `/consume` | `web/baltor/consume.html` | ingestion → consumption: the served `ContextResponse` for the governed CFPB run (answer "10 business days", served facts + source handles, FAQ-30 held out, the three receipt ids, section maturity, candidate providers) | `/api/context/*`, `/api/runtime/*` | `scripts/check_consumption_ui.py` |
| `/standards` | `web/baltor/standards.html` | configuration standards — patterns, routines, templates, maturity scoreboard, waivers, and a generate-preview | `/api/standards/*` | `scripts/check_configuration_standards.py` |
| `/determinism` | `web/baltor/determinism.html` | the Determinism Factory — LLM traces → verified traces → consensus runs → pattern candidates → rule candidates → replay → shadow → promotions → fallback rate → safety blocks; `can_serve_fact` is permanently False; lossless `distilled_from_trace_ids` | `/api/determinism/*` | `scripts/check_determinism_ui.py` |
| `/native` | `web/baltor/native.html` | native-output preview — paste a doc, pick a format + one of the 8 output modes, see the native output / lossless sidecar (`field_facts`/`held_out_claims`/`conflicts`/`receipts`/`field_map`) / diff (`changed_fields` old→new + `receipt_id`); original never overwritten + `source_hash` | `/api/native/*` | `scripts/check_native_ui.py` |

## Shared conventions (every surface honours these)

- **Projection-only.** The page fetches `/api/...` and renders; it never constructs `served_facts` /
  `ContextResponse` / canonical truth in JS, and it carries an explicit `PROJECTION ONLY` declaration.
- **No durable write, no client truth/secret storage, no private memory.** Forbidden anywhere in a page:
  `.agent/`, `MEMORY.md`, `baltor-goal-loop`, `.claude/`, `INSERT INTO`, `sqlite3`, `localStorage`,
  `sessionStorage`, `indexedDB`, `api_key`, `Authorization`, `Bearer `, `OH_SHOWCASE_TOKEN`, and any `sk-`
  secret literal. Gated POSTs (e.g. `/native` ingest) read the token from the URL, never a hardcoded literal.
- **States.** Each page handles loading / empty / error (and, where the API can degrade, degraded) states.

## Proofs

- **Cross-surface (no dead surface)** — `scripts/check_context_surfaces_index.py`: every surface above exists on
  disk, declares projection-only, fetches a projection API, and carries no forbidden token; the set is the
  canonical six with no duplicate route or page; and this index names every route. This guard owns *completeness
  and uniform projection-safety of the SET*; the per-page proofs (right-hand column) own each page's contents.

```bash
PYTHONPATH=. python3 scripts/check_context_surfaces_index.py --self-test
# the per-page proofs
PYTHONPATH=. python3 scripts/check_memory_page_projection_only.py --self-test
PYTHONPATH=. python3 scripts/check_consumption_ui.py --self-test
PYTHONPATH=. python3 scripts/check_configuration_standards.py --self-test
PYTHONPATH=. python3 scripts/check_determinism_ui.py --self-test
PYTHONPATH=. python3 scripts/check_native_ui.py --self-test
PYTHONPATH=. python3 scripts/check_pipeline_pages_full_stack.py --self-test
```

## Live (after MAIN wires the routes)

The admin demo server (`scripts/baltor_admin_demo_server.py`) serves the pages and delegates the
`/api/*` route namespaces. Open the surfaces at:

```
http://127.0.0.1:9307/pipeline
http://127.0.0.1:9307/memory
http://127.0.0.1:9307/consume
http://127.0.0.1:9307/standards
http://127.0.0.1:9307/determinism
http://127.0.0.1:9307/native
```

`web/baltor/hub.html` links all six as cards (MAIN integrates the `/determinism` + `/native` cards alongside
the existing `/pipeline` + `/memory` + `/consume` + `/standards` cards).

## Adding a surface

1. Build the page (`web/baltor/<name>.html`) and its projection API + per-page proof, following the analogues.
2. Add the row to the table above and to `SURFACES` in `scripts/check_context_surfaces_index.py`.
3. Hand MAIN the hub card + the admin-server route delegation via `registrations_needed`.

## Limitations / opportunities

- Each surface renders its API projection as returned; deep per-artifact drill-down (full vector ids, complete
  graph-path expansion) is summarized, not exhaustive.
- Serving the pages + delegating every `/api/*` namespace grows the admin-server monolith
  (split target — `OPP-admin-monolith-split`).
