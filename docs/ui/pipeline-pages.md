# Pipeline Journey pages (projection-only, lossless)

A cohesive series of web pages that let a user follow **one** Baltor pipeline run, stage by stage:
**upload → decomposition → reconciliation → enhancement → optimization → verification → consumption**,
plus a **journey index** that overviews all seven. Every page is a **projection over the existing
runtime** — it computes no truth; it fetches read-only `/api/pipeline/*` and renders.

The **lossless distillation law** ([`docs/codex/lossless-distillation.md`](../codex/lossless-distillation.md))
is the star of this UI. Every stage page makes visible, where applicable, the INPUT, the derived OUTPUT,
**and** what was held out, what candidates were rejected, the source handles, and the lineage/receipts.
"Omitted from the answer" is shown as held-out — never hidden, never erased.

## Purpose

Turn the governed CFPB run into a walkable story so a viewer sees, at each step, not just the winner but
the alternatives the system kept beside it: decomposition shows the held-out narrative allegations;
reconciliation shows the losing FAQ value ("30 days") beside the authoritative winner ("10 business
days") with the rule; optimization shows the rejected candidate packs + the baseline; verification shows
per-artifact allow/hold_out; consumption shows served facts + held_out_warnings + the
verification → optimization → consumption receipt lineage.

## Owner

- **Pages** — `web/baltor/pipeline/` :
  `index.html` (journey), `upload.html`, `decomposition.html`, `reconciliation.html`,
  `enhancement.html`, `optimization.html`, `verification.html`, `consumption.html`.
- **Shared design system** — `web/baltor/pipeline/pipeline.css` (the cohesive web/baltor language:
  GitHub-dark `#0d1117`, blue accent `#58a6ff`, violet lossless accent `#a47ef7`). The 7 stage pages
  inline this same language; the index references the consolidated stylesheet. The stylesheet is
  **additive** — it does not alter the inlined stage pages.
- **Projection API** — `scripts/api_pipeline_handler.py` (a pure read-only projection over the existing
  runtime; it does not reimplement the pipeline).
- **Live wiring (MAIN integrates)** — `scripts/baltor_admin_demo_server.py` serves the pages and
  delegates the `/api/pipeline/*` routes.

## Inputs

- The existing runtime: `scripts/runtime/consumption.run_cfpb_to_consumption`,
  `scripts/runtime/source_consumption`, `scripts/runtime/verification_gate`,
  `scripts/runtime/optimization`, `scripts/artifact_graph/*`, `scripts/ingest/source_adapters`.
- Each page reads only its contracted endpoint(s) with query `?tenant=demo&corpus=cfpb`.

## Outputs

Rendered, read-only projections. No durable writes, no client-side truth storage, no secrets. The journey
index aggregates per-stage in/out/held-out/rejected counts into a totals strip and links into each stage.

## Contracts (shared endpoint contract — all GET, projection-only)

| Page | Endpoint(s) |
|---|---|
| `index.html` | `GET /api/pipeline/overview` |
| `upload.html` | `GET /api/pipeline/upload` (+ overview) |
| `decomposition.html` | `GET /api/pipeline/decomposition` (+ overview) |
| `reconciliation.html` | `GET /api/pipeline/reconciliation` (+ overview) |
| `enhancement.html` | `GET /api/pipeline/enhancement` (+ overview) |
| `optimization.html` | `GET /api/pipeline/optimization` (+ overview) |
| `verification.html` | `GET /api/pipeline/verification` (+ overview) |
| `consumption.html` | `GET /api/pipeline/consumption` (+ overview) |

Endpoint shapes are the `standard.ui_projection.v1` contract (see the lane brief and
`scripts/check_pipeline_api.py`). Pages **degrade gracefully** when a key is absent.

### Cohesion guarantees (every page)

- A 7-stage **pipeline stepper** with the current stage highlighted and prev/next links — continuous
  across the whole series (the last stage loops back to the index).
- INPUT panel · OUTPUT panel · **HELD-OUT / REJECTED (lossless) panel** · source-handle / lineage panel.
- A **Run / Refresh** button hitting the projection API; loading / empty / error / degraded states.
- An explicit `PROJECTION ONLY` marker; no forbidden tokens (`.agent/`, `MEMORY.md`, `baltor-goal-loop`,
  `.claude/`, `INSERT INTO`, `UPDATE `, `DELETE FROM`, `sqlite3`, secrets, client truth storage).

## Proofs

- **Full series (this lane)** — `scripts/check_pipeline_pages_full_stack.py`: all 8 pages exist; the
  stepper is continuous (each stage links next + prev; last loops to index); every page is
  projection-only; every stage page surfaces a lossless / held-out panel; the index references
  `/api/pipeline/overview`; the live projection API answers all 8 shapes. Prints
  `STAGE | PAGE | API | LOSSLESS_PANEL | PROJECTION_ONLY | STEPPER | STATUS`.
- **Per-stage** — `scripts/check_pipeline_<stage>_ui.py` (upload, decomposition, reconciliation,
  enhancement, optimization, verification, consumption).
- **API** — `scripts/check_pipeline_api.py` (the projection contract + REFERENCE regulatory result).

## Commands

```bash
# the full-series synthesis proof
PYTHONPATH=. python3 scripts/check_pipeline_pages_full_stack.py --self-test
# (equivalently)  python3 -m scripts.check_pipeline_pages_full_stack --self-test

# the API contract + per-stage page proofs
PYTHONPATH=. python3 scripts/check_pipeline_api.py --self-test
for s in upload decomposition reconciliation enhancement optimization verification consumption; do
  PYTHONPATH=. python3 "scripts/check_pipeline_${s}_ui.py" --self-test
done

# live (after MAIN wires the routes): open the journey
#   http://127.0.0.1:9307/pipeline
```

## Limitations

- Pages render the projection as returned; deep per-artifact drill-down (full vector ids, complete graph
  path expansion) is summarized, not exhaustive.
- The stepper is static markup / a small JS catalogue per page; it intentionally does not fetch the stage
  list (so the journey reads coherently even before a run / under a degraded overview).
- The shared `pipeline.css` is referenced by the index; the 7 stage pages keep their inlined styles (same
  language) to avoid any risk of breaking them on integration.

## Next

- MAIN wires the page routes (`/pipeline` + `/pipeline/<stage>`) and the `/api/pipeline/*` delegations in
  `scripts/baltor_admin_demo_server.py` (see `registrations_needed` in the lane return) and adds the
  `pipeline_pages` section to the maturity matrix + the `OPP-pipeline-pages` opportunity.
- Optional: migrate the stage pages from inlined styles to `pipeline.css` once the live wiring is proven,
  to collapse to a single stylesheet.
