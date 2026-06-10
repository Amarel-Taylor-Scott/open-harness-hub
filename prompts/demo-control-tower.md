> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the **Demo Control Tower** — one
> start-here page + one all-URLs manifest to demo the whole portfolio end-to-end. Executed INCREMENTALLY.
> **DONE + proven (flywheel 340):** `architecture/demo_surface_registry.json` (20 surfaces, honest
> active/candidate/internal) · `scripts/build_demo_control_tower.py` (renders
> `dist/sites/demo-control-tower/index.html` + the consolidated `dist/demo-all-urls.{json,md,txt}` by REUSING the
> running portfolio sites/tunnels — no reinvention) · `scripts/check_demo_control_tower.py` · served on :9000
> with its own TryCloudflare URL · `docs/demo/end-to-end-demo-script.md`. CFPB e2e evidence =
> `scripts/demo_offline_full_baltor.py` (offline GREEN). **QUEUED:** Playwright screenshots
> (`capture_demo_screenshots.py` + `check_demo_screenshots.py`); the full live e2e harness across the CANDIDATE
> dashboards (`check_demo_e2e_flows.py` — needs the Baltor admin server on :9307 + Teleon/registry/inference web
> surfaces); the demo rubrics (`rubrics/demo-control-tower/*` + `check_demo_rubrics.py`); the security/privacy
> sweep over generated demo HTML; the `serve_demo_surfaces.py`/`launch_demo_trycloudflare.py` unified managers
> (currently the portfolio serve/launch scripts + a dedicated :9000 server/tunnel cover the live surfaces).

# /workflows /contextiseverything-end-to-end-demo-control-tower

Single demo launcher: start every local website/dashboard/demo/API/registry, expose via TryCloudflare when
available, verify end-to-end, screenshot, write a machine-readable URL manifest, and create ONE start-here page.

## DEMO CONTROL TOWER CLAUSE (carry forward)
Every major portfolio surface must be discoverable from one start-here page with local URLs, TryCloudflare URLs
when available, health status, screenshots, and rubric scores. Demo launch is not complete until the Baltor CFPB
flow runs end-to-end, public/local URLs are verified, URL manifests are written, screenshots are captured or
limitations recorded, and existing flywheel regressions remain green. Do NOT fake TryCloudflare URLs; missing
cloudflared is PARTIAL with install instructions, not GREEN. Exact-PID stop only; no broad sweep.

**Reuse, don't reinvent:** the running portfolio sites (`scripts/portfolio_lib.py` + `serve_portfolio_sites.py` +
`launch_portfolio_trycloudflare.py` + `.agent/portfolio-sites/urls.json`), the Baltor CFPB demo
(`demo_offline_full_baltor.py` / `baltor_admin_demo_server.py`), and the durable worker/flywheel substrate.

*(Full PART 0–19 detail is in the owner's message + the proven core above; build the QUEUED items next.)*
