---
description: No-stop loop — bring up + heal until all THREE brand sites have a functional trycloudflare URL
---

Adopt the autonomous **site-reliability** role and **begin immediately**. Single goal: get and keep
**three fully-functional public trycloudflare URLs** — one each for the three brand surfaces — and do
not stop until the gate is green. Full spec + branch-on-block playbook: `docs/codex/three-sites-live-goal.md`.

## The three sites (one shared backend)

- **Context is Everything** — parent / mission landing · `OH_PRODUCT=context-is-everything` · :8002 · `web/context-is-everything/`
- **Baltor** — verified-context SaaS · `OH_PRODUCT=baltor` · :8001 · `web/baltor/`
- **OpenHubForAI** — open builder funnel · `OH_PRODUCT=openhubforai` · :8000 · `web/openhubforai/`

Brand/identity is LOCKED: `docs/strategy/brand-architecture.md`. Don't rename or restyle the brands here.

## Success condition (the ONLY definition of done)

```bash
python3 -m scripts.showcase.verify_tunnels      # exit 0  ⟺  all three live + serving the right brand
```

## The loop (never end on a failure — branch on the block)

1. Bring up / heal: `bash scripts/serve_all_sites.sh` (idempotent; re-up only what's down; tunnels are
   detached so they persist and URLs stay stable).
2. Verify: `python3 -m scripts.showcase.verify_tunnels`. Exit 0 → **report the three `…/?token=` URLs and stop.**
3. For each site still `○DOWN`, diagnose and switch paths, then loop back to step 1:
   - server `health --` → read `/tmp/ohh-<id>.log`, fix (import error / `fuser -k <port>/tcp`), restart that server.
   - `(no url yet)` → read `/tmp/ohh-tunnel-<id>.log`; cloudflared rate-limit/network → wait, restart that one tunnel.
   - brand `--` but health ok → wrong/stale folder → confirm `OH_PRODUCT` + `web/<id>/index.html` marker, restart.
   - no `cloudflared` binary → install it, then retry.
4. Repeat. Don't ask the owner; decide from the repo and the logs (`docs/codex/change-verification-contract.md`,
   `.claude/commands/direction.md`). Only stop when `verify_tunnels` exits 0 — then print the table
   (`bash scripts/serve_all_sites.sh --status`) with all three URLs.

## Standing notes

- One shared access token across all three (reused from `dist/showcase-share-url.txt`, else minted once).
- Web assets serve `no-store`; HTML/CSS/JS edits go live with no restart — only `server.py` changes need a relaunch.
- Stop everything (rarely needed): `pkill -f 'cloudflared tunnel'; pkill -f scripts.showcase`.
