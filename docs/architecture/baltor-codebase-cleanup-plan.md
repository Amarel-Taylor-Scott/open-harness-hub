# Baltor Codebase Cleanup Plan

This plan turns the current prototype surfaces into maintainable product
modules without breaking the static-site and local-demo workflow.

## Monolith Inventory

| Area | Current risk | Target shape |
|---|---|---|
| `scripts/showcase/server.py` | Static serving and generic showcase APIs still share one stdlib HTTP handler. | Keep it as product/static/generic API dispatch; admin-demo internals now live under `scripts/showcase/admin_demo/*`. |
| `web/harness-hub/styles/admin-demo.css` | All layout, cards, sources, processing, outputs, and download styles in one file. | Split complete: `styles/admin-demo.css` is now an import shell for `styles/admin-demo/*.css`. |
| `scripts/context_workers/tasks.py` | All default workers in one file. | Split complete: `tasks.py` is now a compatibility shell for `scripts/context_workers/workers/*.py`. |
| `web/harness-hub/admin-demo-assets/app.js` | Acceptable now, but will grow as routes deepen. | Split into `state.js`, `routes.js`, `events.js`, and route-specific view modules. |

## Backend Split

Target:

```text
scripts/showcase/admin_demo/
  __init__.py
  analysis.py
  exports.py
  routes.py
  runs.py
  source_sync.py
  serializers.py
```

Responsibilities:

- `analysis.py`: deterministic local analysis and source status normalization.
- `runs.py`: run state, persistence, polling, background thread orchestration.
- `source_sync.py`: source status, hash, version, freshness labels.
- `exports.py`: text/RAG/graph/audit package generation.
- `routes.py`: request parsing and response helpers for admin-demo endpoints.
- `serializers.py`: stable API payload shapes.

Current status:

- `scripts/showcase/server.py` now delegates admin-demo API routes to
  `scripts/showcase/admin_demo/routes.py`; it still owns shared static serving
  and generic showcase APIs.
- `scripts/showcase/admin_demo/routes.py` owns admin-demo request parsing,
  run-polling responses, export download headers, and mutation endpoints.
- `scripts/showcase/admin_demo/analysis.py` owns deterministic chunking, entity
  extraction, claim extraction, graph edge generation, refresh candidates, and
  source status payloads.
- `scripts/showcase/admin_demo/runs.py` owns queued/running/complete state,
  persistence under `dist/admin-demo-runs`, and the background local run thread.
- `scripts/showcase/admin_demo/source_sync.py` owns source status, hashes,
  versions, freshness labels, and next actions.
- `scripts/showcase/admin_demo/exports.py` owns text/RAG/graph/audit package
  generation.
- Next backend split: add `serializers.py` for stable API payload shapes and
  keep the front-end renderers aligned to those shapes.

## CSS Split

Target:

```text
web/harness-hub/styles/admin-demo/
  tokens.css
  layout.css
  cards.css
  sources.css
  processing.css
  outputs.css
  download.css
```

Keep `styles/admin-demo.css` as an import shell for compatibility.

Current status:

- `web/harness-hub/styles/admin-demo.css` imports the split module files.
- `base.css` owns tokens, topbar, shell layout, flow cards, panel structure, and
  heading typography.
- `sources.css` owns source cards, selected source rows, raw text fallback,
  buttons, status tags, and intake controls.
- `processing.css` owns metrics, source sync rows, run cards, progress bars,
  stage lists, and worker tier cards.
- `outputs.css` owns graph, list, item, and chip presentation.
- `download.css` owns serving package/download cards.
- `responsive.css` owns viewport breakpoints.

## Worker Split

Target:

```text
scripts/context_workers/workers/
  chunk.py
  keyword.py
  entity.py
  claim.py
  graph.py
  fragility.py
  refresh.py
  pipeline.py
  hermes.py
  openclaw.py
```

Current status:

- `scripts/context_workers/common.py` owns shared deterministic helpers.
- `scripts/context_workers/tasks.py` is an import shell that preserves the old
  public function names and `ensure_registered()`.
- Built-in workers now live in:
  - `workers/chunk.py`
  - `workers/keyword.py`
  - `workers/entity.py`
  - `workers/claim.py`
  - `workers/graph.py`
  - `workers/fragility.py`
  - `workers/refresh.py`
  - `workers/pipeline.py`

Next split:

- Add lifecycle hooks around the registry: `preflight`, `load`, `execute`,
  `write_artifacts`, `emit_followups`, and `shutdown`.
- Add lane-based container manifests for CPU, browser, OCR, ML, and GPU worker
  images.
- Add Hermes/OpenClaw workers only as bounded expensive paths that emit reusable
  deterministic artifacts.

Hermes/OpenClaw workers should not become permanent expensive paths. They should
emit deterministic artifacts:

- resolver rules
- extraction templates
- source precedence policies
- query templates
- verification checklists
- graph edge rules
- promotion gates

## Cleanup Policy For Legacy Context

Do not mass-delete older docs. Instead:

1. Add or update the canonical Baltor docs.
2. Point active commands at the canonical docs.
3. Add supersession notes when old docs are actively misleading.
4. Only delete generated or stale artifacts when the owning workflow is known.

This avoids losing useful substrate while preventing autonomous agents from
starting from outdated product framing.
