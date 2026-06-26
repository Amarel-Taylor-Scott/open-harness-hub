# Surface deploy — local testing → cloud (the 5 surfaces)

The 5 product surfaces are ONE config-driven server (`scripts/surface_server.py`, stdlib-only, no pip). The same
binary serves any surface; the surface + port + host come from env (or args). Design reference: `docs/DESIGN-BIBLE.md`.

## The 5 surfaces

| Surface (`SURFACE=`) | Brand | Accent | Prod domain | Notes |
|---|---|---|---|---|
| `ai-done-right` | AI Done Right | `#5a6b87` | aidoneright.dev | the hub (portfolio index) |
| `teleon` | Teleon.dev | `#6d5ef0` | teleon.dev | |
| `baltor` | Baltor.ai | `#0e7c86` | baltor.ai | |
| `aidevobserver` | AIDevObserver | `#b25fd6` | aidevobserver.dev | |
| `open-star-hubs` | OpenHubForAI | `#3b6fd4` | openhubforai.io | carries the faceted `/browse` |

Routes per surface: `/` (home; AIDoneRight = hub) · `/demo` (BYO-key) · `POST /run` · `/browse` (OpenHubForAI) · `204` favicon.

## Config (env or args — args win)

| Knob | Env | Arg | Default |
|---|---|---|---|
| surface | `SURFACE` | positional | — (required) |
| port | `PORT` | `--port` | per-surface (8001–8005) |
| host | `HOST` | `--host` | `0.0.0.0` |

## Local testing (what's running now)

```bash
PYTHONPATH=. python3 scripts/surface_server.py baltor --port 8001     # one surface
# all 5: run each on its own port, then tunnel each:
for s in ai-done-right:8002 teleon:8003 baltor:8001 aidevobserver:8110 open-star-hubs:8130; do
  PYTHONPATH=. nohup python3 scripts/surface_server.py ${s%%:*} --port ${s##*:} >/dev/null 2>&1 &
done
```
Cross-surface nav reads `dist/surface-urls.json` ({surface-id: url}); the launcher writes the live TryCloudflare URLs there.
Proof: `PYTHONPATH=. python3 scripts/check_surface_server.py --self-test` (122 assertions, byte-identical CSS).

## Cloud (ready to move) — one image, 5 services

```bash
docker build -f deploy/surface.Dockerfile -t aidr-surface .
docker run -e SURFACE=baltor -e PORT=8080 -p 8080:8080 aidr-surface   # → http://localhost:8080
```

- **Render:** `deploy/render.yaml` declares all 5 as web services (same image, `SURFACE` per service). New → Blueprint → this repo → map each to its domain.
- **Cloud Run:** `gcloud run deploy baltor --source . --set-env-vars SURFACE=baltor` (Cloud Run injects `PORT`; the server honors it). One service per surface.
- **Fly / Railway:** same pattern — set `SURFACE`, let the platform inject `PORT`.

**Production cross-nav:** set `dist/surface-urls.json` to the real domains (aidoneright.dev / teleon.dev / baltor.ai /
aidevobserver.dev / openhubforai.io) so the nav links resolve across services. TryCloudflare quick tunnels are for
local sharing only (ephemeral); production uses the real domains + a named tunnel or the platform's TLS.

serves_truth=false · the BYO-key demo runs with the user's key for that one request and never stores it.
