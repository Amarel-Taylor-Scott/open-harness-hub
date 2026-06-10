# Portfolio websites - build, serve, launch

Rubric-gated static launch sites (one source: `scripts/portfolio_lib.py`).
The current set is computed from `SITE_ORDER`; do not hard-code the count in
new checks or docs.

## Build
```bash
PYTHONPATH=. python3 scripts/build_portfolio_sites.py            # → dist/sites/<site>/index.html
PYTHONPATH=. python3 scripts/build_portfolio_sites.py --self-test
```
Local CSS only; no external CDN/JS/analytics/secrets.

## Serve locally (exact-PID; ports 9100 hub, contiguous site ports from `SITE_ORDER`)
```bash
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --restart   # start (idempotent)
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --status    # HTTP 200 probe
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --stop      # SIGTERM EXACT pids only
```
PIDs → `.agent/portfolio-sites/pids.json`; logs → `.agent/portfolio-sites/logs/<site>.log`.

## TryCloudflare preview
```bash
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --restart
```
URLs → `.agent/portfolio-sites/urls.json` + `dist/portfolio-share-urls.{json,md,txt}`.
Tunnel PIDs → `.agent/portfolio-sites/tunnel-pids.json`. Stop: `--stop` (exact PIDs).
See `trycloudflare-portfolio-launch.md`.

## Stop everything (exact PIDs, never a broad sweep)
```bash
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --stop
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --stop
```

## Rubrics / proofs
All under `scripts/check_portfolio_*.py --self-test` (logic in `scripts/portfolio_checks.py`); rubrics in
`rubrics/portfolio/*.json`. Full table: `scripts/check_portfolio_launch_full_stack.py --self-test`. See
`website-rubrics.md`. GREEN = every rubric passes; PARTIAL = sites built/served but a non-blocker rubric is
short; RED = a blocker fails (fix before launch).

## Reuse rule
Do not add a second site framework. The single source is `portfolio_lib.py`; existing `serve_*.sh` (showcase/
products) are unrelated and untouched. Discovery: `.agent/portfolio-website-discovery.json`.
