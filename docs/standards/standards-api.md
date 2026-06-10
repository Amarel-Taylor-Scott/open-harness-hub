# Standards API + `/standards` page

The Standards API is a **projection-only** read surface over the standards-system truth files. It never
mutates truth, never writes files, never serves secrets or private memory. The `/standards` page consumes
this projection and computes no truth of its own.

- **Handler (pure, importable):** `scripts/api_standards_handler.py`
- **Page (projection-only):** `web/baltor/standards.html` (served at `/standards`)
- **Proofs:** `scripts/check_standards_api.py --self-test`, `scripts/check_standards_ui.py --self-test`

The handler is a pure `handle(method, path, body) -> (status, json)` function modeled on
`scripts/api_context_handler.py`, so the contract is testable without a socket; the admin server just
delegates to it.

## Endpoints

| Method | Route | Returns | Source (produced by sibling lanes) |
|---|---|---|---|
| GET | `/api/standards/patterns` | `{available, patterns[], total}` | `architecture/pattern_registry.json` |
| GET | `/api/standards/templates` | `{available, templates[], total}` | `architecture/template_catalog.json` |
| GET | `/api/standards/routines` | `{available, routines[], total}` | `architecture/routine_library.json` |
| GET | `/api/standards/waivers` | `{available, waivers[], total}` | `architecture/pattern_waivers.json` |
| GET | `/api/standards/maturity` | `{available, patterns[], total}` | `architecture/pattern_maturity_matrix.json` |
| POST | `/api/standards/generate-preview` | `{dry_run:true, would_create[]}` | DRY-RUN plan; **writes no files** |

### Graceful degradation

The truth files are produced by other lanes. The handler reads them **at call time** and degrades to
`{"available": false, "<list>": [], "total": 0, "note": "<file> not produced yet"}` when a file is absent
or unreadable — it never raises. This keeps the projection (and its proof) robust whether or not the
sibling lanes have landed.

### `generate-preview` is a dry-run

`POST /api/standards/generate-preview` returns **what would be generated**, with every entry flagged
`"written": false`. It first tries a sibling-lane generator's own dry-run (`scripts.standards_generator` /
`scripts.pattern_generator`, imported lazily); if none is present it builds a deterministic local plan from
the pattern registry + template catalog. **No filesystem write occurs in either path.** The API proof
snapshots both a temp dir and `architecture/` before/after the call and asserts neither changed.

## Projection-only guarantees (enforced by the proofs)

- No truth mutation, no file writes, no durable store, no network.
- No secrets / no private memory: payloads are scrubbed of `OH_SHOWCASE_TOKEN`, `sk-`, `api_key`,
  `Authorization`, `MEMORY.md`, `.agent/`.
- The page fetches **only** `/api/standards/*`, uses no client storage (`localStorage` / `sessionStorage` /
  `indexedDB`), and renders loading / error / empty / degraded states.

The `/standards` page panels: Pattern registry, Standards catalog, Template catalog, Routine library,
Waivers, Pattern miner report, New-code compliance, Examples, Opportunities, Risks, plus a Generate-preview
(dry-run) panel.

## Wiring (done by MAIN — this lane does not edit the monolith)

`scripts/baltor_admin_demo_server.py` delegates, exactly as it does for the Consumption API:

- `do_GET`: when `path.startswith("/api/standards/")`, import
  `from scripts.api_standards_handler import handle as _std_handle`, build the query dict, call
  `_std_handle("GET", path, q)`, and send the JSON. Also serve the page:
  `elif path in ("/standards", "/standards.html"): self._serve_web("standards.html")`.
- `do_POST`: when `parsed.path.rstrip("/") == "/api/standards/generate-preview"`, call
  `_std_handle("POST", "/api/standards/generate-preview", self._read_json())` and send the JSON.

The 6 routes are registered (owner `scripts/api_standards_handler.py`, `projection_only: true`) in
`architecture/contract_registry.json#api_routes` by MAIN.
