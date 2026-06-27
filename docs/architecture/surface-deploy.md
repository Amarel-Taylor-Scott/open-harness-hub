# Surface deploy: local testing to cloud (the 5 surfaces)

The 5 product surfaces are full apps under `web/<brand>/`, rendered by the **showcase**
(`scripts/showcase/server.py`). `OH_PRODUCT=<brand> python3 -m scripts.showcase --port <N>` serves
`web/<OH_PRODUCT>/` at the origin root over the shared kit in `web/<brand>/kit/`, with the service plane behind
same-origin `/api/*` seams. This is the canonical renderer. `scripts/surface_server.py` is a demoted lightweight
**fallback** that renders a minimal standalone surface when the full app + kit are not available; it is not the
shipped product. Design reference: `docs/DESIGN-BIBLE.md` (the UI); FE/BE seams + deploy: `docs/INTEGRATION-BIBLE.md`.

## The 5 surfaces

| Surface (`OH_PRODUCT=`) | Brand | Accent | Prod domain | Notes |
|---|---|---|---|---|
| `context-is-everything` | AI Done Right | `#5a6b87` | aidoneright.dev | the hub (portfolio index; legacy parent path) |
| `teleon` | Teleon.dev | `#6d5ef0` | teleon.dev | |
| `baltor` | Baltor.ai | `#0e7c86` | baltor.ai | |
| `aidevobserver` | AIDevObserver | `#b25fd6` | aidevobserver.dev | |
| `openhubforai` | OpenHubForAI | `#3b6fd4` | openhubforai.io | carries the faceted `/browse` |

Each app is its own entry HTML + brand main file (for example `web/teleon/index.html` + `web/teleon/teleon-main.jsx`);
the backend (`/api/*`, the engine, the catalog) is shared. `OH_PRODUCT` defaults to `openhubforai`.

## Config (env or args)

| Knob | Env | Arg | Default |
|---|---|---|---|
| surface | `OH_PRODUCT` | (none) | `openhubforai` |
| port | (none) | `--port` | `8000` |
| bind host | `OH_BIND_HOST` | (none) | `127.0.0.1` (set `0.0.0.0` in container deploys) |
| seam backends | `OH_SEAM_*_BASE` | (none) | local service ports (see `docs/INTEGRATION-BIBLE.md`) |

## Local testing (what's running now)

```bash
OH_PRODUCT=baltor python3 -m scripts.showcase --port 8001     # one surface (the full web/baltor app)
# all 5: run each on its own port, then tunnel each:
for s in context-is-everything:8002 teleon:8003 baltor:8001 aidevobserver:8110 openhubforai:8130; do
  OH_PRODUCT=${s%%:*} nohup python3 -m scripts.showcase --port ${s##*:} >/dev/null 2>&1 &
done
```
`bash scripts/serve_showcase.sh` wraps a single surface with an optional TryCloudflare tunnel and local Gemma.
Proof: `python3 -m scripts.showcase --self-test` (the renderer); `PYTHONPATH=. python3 scripts/showcase/verify_tunnels.py`
checks each brand surface serves the *right* app (health + brand string in the served HTML).

## Cloud (ready to move): one service per surface

Each frontend surface deploys via the showcase (one service per `OH_PRODUCT`), `OH_BIND_HOST=0.0.0.0`, the platform's
injected port passed through as `--port`:

```bash
OH_BIND_HOST=0.0.0.0 OH_PRODUCT=baltor python3 -m scripts.showcase --port "$PORT"   # serves web/baltor
```

- **Render / Cloud Run / Fly / Railway:** one web service per surface. Set `OH_PRODUCT` (+ `OH_BIND_HOST=0.0.0.0`), let
  the platform inject the port, and set the `OH_SEAM_*_BASE` envs so the same-origin seams point at the cloud backends.
  The same frontend code + seam paths work unchanged across local and cloud; only the `OH_SEAM_*_BASE` values differ.
  Canonical runbook: `docs/INTEGRATION-BIBLE.md` (section 6) + `docs/architecture/fly-deploy-runbook.md`.
- **Fallback image:** `deploy/surface.Dockerfile` + `deploy/render.yaml` currently wire the demoted
  `scripts/surface_server.py` (a `SURFACE` env, ports 8001-8005). Keep them as the minimal standalone fallback; point a
  real deploy at the showcase serving `web/<OH_PRODUCT>/`.

**Production cross-nav:** point each surface's nav at the real sibling domains (aidoneright.dev / teleon.dev /
baltor.ai / aidevobserver.dev / openhubforai.io) so links resolve across services. (The `dist/surface-urls.json`
URL map is a `surface_server.py` fallback mechanism.) TryCloudflare quick tunnels are for local sharing only
(ephemeral); production uses the real domains + a named tunnel or the platform's TLS.

serves_truth=false · the BYO-key demo runs with the user's key for that one request and never stores it.
