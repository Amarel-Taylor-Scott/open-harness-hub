# web/ — two product front-ends, one shared backend

Each product has its **own self-contained front-end folder**. Only the **backend** is shared
(`scripts/` — the engine, the catalog, the `/api/*` endpoints). See
`docs/strategy/two-services-shared-infrastructure.md`.

```
web/
  harness-hub/         Open Harness Hub — bounded: assemble + monitor a governed pipeline.
                       index.html · app.js · data.js · pages/ · styles/ · design/ (its README.md too)
  context-enrichment/  Context Enrichment (CEaaS) — unbounded content refinery: tiers, hosting,
                       agent serving. index.html · app.js (own tiny router) · pages/ · styles/
```

**How a product is served:** one server instance per product, picked by env —
`OH_PRODUCT=harness-hub | context-enrichment` selects `web/<product>/` as the document root
(`scripts/showcase/server.py`; default `harness-hub`). The backend (`/api/*`) is identical regardless.

- **Both at once, each behind its own tunnel:** `bash scripts/serve_two_products.sh`
  (:8000 harness-hub, :8001 context-enrichment; URLs in `dist/showcase-share-url-<slug>.txt`).
- **One product locally:** `OH_PRODUCT=context-enrichment python3 -m scripts.showcase --port 8001`.
- **Polish loop for both:** the `/launch` skill (`.claude/commands/launch.md`).

**Rules:** no build (vanilla JS + ported CSS). Do **not** cross-import between the two front-end
folders — if something is truly common it belongs in the backend, not a shared front-end module. Each
folder keeps its own copy of the design-token CSS so it stays independently shippable.
