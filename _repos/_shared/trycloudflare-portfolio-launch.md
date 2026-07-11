# TryCloudflare portfolio launch

`scripts/launch_portfolio_trycloudflare.py` runs one `cloudflared tunnel --url http://127.0.0.1:<port>` per
`scripts.portfolio_lib.SITE_ORDER` static launch site and captures the generated `*.trycloudflare.com` URL from
each tunnel log.

```bash
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --restart   # launch + capture
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --status    # show urls.json
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --stop      # kill EXACT tunnel pids
```

Outputs: `.agent/portfolio-sites/urls.json`, `.agent/portfolio-sites/tunnel-pids.json`,
`dist/portfolio-share-urls.{json,md,txt}`.

## Discipline
- **No fake URLs.** A site with no captured URL is recorded with an honest status — `MISSING_CLOUDFLARED`
  (cloudflared absent, with install link) or `TUNNEL_UNREACHABLE` (no URL within the timeout) — never invented.
- **Exact-PID cleanup** only; never a broad process sweep.

## Caveat — temporary, not production
TryCloudflare quick tunnels are **temporary, random session URLs** — not production hosting. They die when the
tunnel process stops. **Next step for real domains:** a named Cloudflare tunnel + the real domains
(`teleon.dev`, `baltor.ai`, `openhubforai.org`, the holding-company domain) once brand/trademark clears.
