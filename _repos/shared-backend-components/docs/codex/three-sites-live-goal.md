# Goal: three sites live — three functional trycloudflare URLs, no-stop until green

A **runnable, self-healing goal**: do not stop until all **three brand surfaces** are reachable on a
public `*.trycloudflare.com` URL and serving the *right* brand. This is the operational companion to the
LOCKED brand architecture (`_repos/aidoneright/context/strategy/brand-architecture.md`).

## The three sites (one shared backend, three doors)

| Site | Brand surface | Port | `web_root` | Brand marker (must appear at `/`) |
|---|---|---|---|---|
| `context-is-everything` | **Context is Everything** — parent / mission landing | 8002 | `web/context-is-everything` | `Context is Everything` |
| `baltor` | **Baltor** — verified-context SaaS | 8001 | `web/baltor` | `Baltor` |
| `openhubforai` | **OpenHubForAI** — open builder funnel | 8000 | `web/openhubforai` | `OpenHubForAI` |

One backend (`scripts.showcase`); `OH_PRODUCT` pins which `web/<id>/` folder a server serves. Each site
gets its own port → its own persistent tunnel → one shared access token.

## Success condition (the gate — the only definition of "done")

```bash
python3 -m scripts.showcase.verify_tunnels      # exit 0  ⟺  ALL THREE are fully functional
```

A site passes only when: (1) its tunnel URL exists in `dist/showcase-tunnel-url-<id>.txt`,
(2) `GET <url>/api/health` → 200, and (3) `GET <url>/` → 200 **and contains the brand marker** (proves
the *right* product folder is served, not a stale one). The loop is **not done** until this exits `0`.

## The two custom tools

- **Orchestrator** — `scripts/serve_all_sites.sh`: brings up the three pinned servers + three
  **persistent** (`setsid`/`disown`) tunnels, reuses a still-answering tunnel so URLs stay stable, and
  runs its own **heal loop** (re-up only what's down) until the gate is green or `MAX_HEAL` rounds pass.
  `bash scripts/serve_all_sites.sh` to bring up; `--status` to just print the three URLs + health.
- **Gate** — `scripts/showcase/verify_tunnels.py`: the success-condition check above. Derives the site
  list from `services/registry.yaml` (products with a `web_root`) so it stays in sync — single source of
  truth, no hand-typed list. `--json` for machine-readable, `--quiet` for exit-code-only.

## The resilient loop (never stop on the first failure — branch on the block)

1. **Bring up:** `bash scripts/serve_all_sites.sh` (idempotent — safe to re-run; it heals in place).
2. **Verify:** `python3 -m scripts.showcase.verify_tunnels`. Exit 0 → **done**, report the 3 URLs.
3. **Diagnose + branch** on whatever is still `○DOWN`, then loop back to step 1:
   - *no `cloudflared`* → install it (`docs/showcase` / `.local/bin/cloudflared`), then retry.
   - *server unhealthy* (`health --`) → read `/tmp/ohh-<id>.log`; fix the cause (import error, port in
     use → `fuser -k <port>/tcp`), restart that server only.
   - *no tunnel URL* (`url (no url yet)`) → read `/tmp/ohh-tunnel-<id>.log`; cloudflared rate-limit or
     network blip → wait + restart that one tunnel (`pkill -f "cloudflared tunnel --url http://localhost:<port>"`).
   - *health ok but brand `--`* → wrong/stale folder served → confirm `OH_PRODUCT=<id>` and that
     `web/<id>/index.html` exists with the marker; restart the server.
   - *tunnel was up, now flaps* → the launcher reuses a live tunnel; if the URL changed, the new one is
     already written to the dist file — just re-verify.
4. Repeat until the gate is green. Don't end on a question; if one path is blocked, switch paths
   (per `.claude/commands/direction.md` / `docs/codex/change-verification-contract.md`).

## Run it

- One-shot autonomous: `bash scripts/serve_all_sites.sh && python3 -m scripts.showcase.verify_tunnels`
- Claude-driven no-stop loop: invoke **`/sites-live`** (`.claude/commands/sites-live.md`) — adopts the
  loop role and keeps healing until the gate exits 0.

## Task checklist

- [x] Third site built — `_repos/aidoneright/frontend/` (parent landing) + registered in `services/registry.yaml` (:8002).
- [x] Orchestrator — `scripts/serve_all_sites.sh` (bring up + persistent tunnels + heal loop).
- [x] Gate — `scripts/showcase/verify_tunnels.py` (registry-derived, exit 0 ⟺ all three live).
- [x] Goal doc — this file.
- [x] Runnable command — `.claude/commands/sites-live.md`.
- [x] **All three URLs verified green** (`verify_tunnels` exits 0) and reported to the owner.

## Output artifacts (where the URLs land)

`dist/showcase-share-url-<id>.txt` (URL **with** `?token=`) and `dist/showcase-tunnel-url-<id>.txt` (bare
URL) for each of `openhubforai`, `baltor`, `context-is-everything`. The shared token is reused from
`dist/showcase-share-url.txt` when present, else minted once.
