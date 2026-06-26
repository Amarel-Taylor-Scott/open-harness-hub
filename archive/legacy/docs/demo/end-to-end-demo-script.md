# End-to-end demo script — AI Done Right portfolio

**Start here (one page):** local `http://127.0.0.1:9000/` · public `https://judicial-separation-gig-charge.trycloudflare.com`
**Share sheet (all URLs):** `dist/demo-all-urls.md` (+ `.json`/`.txt`)

The Demo Control Tower aggregates every surface with local + TryCloudflare URLs, honest status, and this script.
Build/refresh: `PYTHONPATH=. python3 scripts/build_demo_control_tower.py`. Surfaces: `architecture/demo_surface_registry.json`.

## 3-minute investor/YC demo
1. Open the Demo Control Tower (the public URL above).
2. Open **AI Done Right** → the portfolio thesis (OpenContextHub → Teleon → Baltor; AI Done Right coordinates).
3. Open **Teleon** (purpose-driven runtime) and **Baltor** (governed context).
4. Run the Baltor CFPB demo (below) — the proof point.

## 10-minute technical demo
1. Demo Control Tower → walk the static portfolio launch sites (each: what it is / is not / boundary).
2. **Baltor CFPB e2e (PROVEN, offline):** `PYTHONPATH=. python3 scripts/demo_offline_full_baltor.py --self-test`
   → answer **10 business days** · FAQ **"30 days" held out** · **receipt + source handles** preserved.
3. Open the public open-hub spine — Context · Skills · Tools · MCP · Compression · Benchmark · Harness.
   The broader AI Done Right prototype family is verified separately by
   `python3 scripts/check_ai_done_right_surface_family.py --self-test`.
4. Explain: hubs supply parts · **Teleon runs** capabilities · **Baltor governs** truth · none of the open hubs is a truth authority.
5. Show the platform proofs are green: `PYTHONPATH=. python3 scripts/baltor_flywheel.py --once` (340/340).

## Customer-safe demo
Use the public site URLs + the CFPB result. Do not show staff dashboards or internal tools (marked CANDIDATE/INTERNAL).

## Restart / stop (exact PIDs — never a broad sweep)
- Control tower server + tunnel: pids in `.agent/demo-control-tower/{pids,tunnel-pids}.json` → `kill <pid>`.
- Portfolio sites + tunnels: `python3 scripts/launch_portfolio_trycloudflare.py --stop && python3 scripts/serve_portfolio_sites.py --stop`.

## Caveats
TryCloudflare URLs are temporary/random session URLs — preview, not production hosting. CANDIDATE/INTERNAL surfaces
are not live web pages yet (shown honestly). No paid cloud. Production = named tunnels + the real domains after clearance.
