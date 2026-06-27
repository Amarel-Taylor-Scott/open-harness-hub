# web/ — four product front-ends, one shared backend

Each product has its **own self-contained front-end folder**. Only the **backend** is shared
(`scripts/` — the engine, the catalog, the `/api/*` endpoints). See
`docs/strategy/two-services-shared-infrastructure.md`.

Since 2026-06-10 each front-end IS the **full-design surface** transplanted from the design
handoff bundle (`dist/sites/aidoneright-design/` — the spec, final fidelity), wired to the real
local backends. The transplant is **generated**:

```
python3 scripts/port_full_design_to_web.py          # bundle → web/ (idempotent)
python3 scripts/port_full_design_to_web.py --check  # drift gate: web/ must match the bundle
```

**Never hand-edit a generated file** (`index.html`, `kit/`, the ported jsx/css/html — each entry
HTML carries a GENERATED marker; `.design-port-manifest.json` lists them). Change the bundle (or
the port script's recorded patches) and re-run. The previous hand-built front pages are preserved
as `legacy.html` (lossless), and every legacy functional page keeps its URL
(`admin-demo`, `dashboard.html`, `demo-console.html`, pipeline/stage pages, …).

```
web/
  context-is-everything/   AI Done Right — parent portfolio site (cie-main.jsx + kit) +
                           Demo Control Tower.html (operator index over every surface).
  openhubforai/             OpenHubForAI — full proto surface (~40 routes; proto-*.jsx) with the
                           logged-out funnel wired live: landing task → /api/build → real assembled
                           flow in the preview (openhub-live.js seam; no fixture lift claims on live builds).
  baltor/                  Baltor — full ce-* surface (marketing + docs + app console + 25+ guided
                           demo/deep-dive pages) + the legacy live-ops pages, now working on this
                           origin through the seam proxy.
  teleon/                  Teleon — the kit-reference runtime site (teleon-main.jsx) + the
                           PurposeTask Control Tower page (:8003, teleon_app). Real accounts/keys
                           via the kit seams; runtime surfaces are designed previews, captioned.
  vendor/                  Pinned React/ReactDOM/Babel UMD runtime (one copy, served at /vendor/;
                           hashes match the prototypes' SRI pins — see vendor/README.md).
```

**How a product is served:** one server instance per product, picked by env —
`OH_PRODUCT=openhubforai | baltor | context-is-everything` selects `web/<product>/` as the document
root (`scripts/showcase/server.py`; default `openhubforai`). The backend (`/api/*`) is identical
regardless, and every origin additionally serves:

- `/vendor/*` — the pinned runtime (above);
- `/design/*` + root mounts of the bundle's folders (`/teleon/…`, `/opencontexthub/…`, `/shared/…`)
  — so the 21 non-product design surfaces stay reachable and the **verbatim** `../<sibling>/…`
  cross-surface links inside the transplanted code resolve;
- same-origin service seams (ports single-sourced in `architecture/` registries):
  `/api/identity/*` → identity realms (9410) · `/registry/*` → OpenHubForAI registry (9423) ·
  `/analytics/*` → events plane (9420) · Baltor live-ops `/api/demo|events|context|…` →
  `baltor_admin_demo_server` (9301). The full-design kit clients honor these via the injected
  `OHH_*_BASE` overrides and fall back honestly to design data when a service is down.

- **Everything up:** `python3 scripts/start_local_services.py` (apps + identity + events +
  registry + live-ops backend), then open :8000/:8001/:8002.
- **All three behind tunnels:** `bash scripts/serve_all_sites.sh` (URLs in
  `dist/showcase-share-url-<slug>.txt`).
- **One product locally:** `OH_PRODUCT=baltor python3 -m scripts.showcase --port 8001`.
- **Verify the wired full-design apps:** `node e2e/full_design_apps.mjs` (route walk, console
  gate, real signup, live build, live events, parity screenshots). Parity record:
  `docs/status/web-full-design-parity-report.md`.

**Rules:** no build step (the prototypes' in-browser-Babel model, with the pinned local runtime).
Do **not** cross-import between the three front-end folders — common code belongs to the backend
or arrives via the generated `kit/` copies (each app keeps its own byte-identical copy of the kit
so it stays independently shippable; the `--check` gate keeps them in sync with the bundle).
`dist/sites/aidoneright-design/DESIGN-CONTRACT.md` governs all design changes — transplant, don't
re-create; copy is verbatim; tokens are the only source of color.
