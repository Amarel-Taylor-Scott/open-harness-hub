# YC-demo readiness (development plane; serves_truth=false)

**Score: 0.667 / 1.0**  `█████████████░░░░░░░`  →  not yet ready (bar: 0.85)

The loop steers toward this: the `demo` flywheel files the open gaps below into the proposal backlog.

| dim | weight | status | detail |
|---|---|---|---|
| live_backend_proof | 3 | ✅ | 3 live backend receipt(s) — a real run was executed |
| backends_green | 3 | ⬜ | core proof gates: unknown |
| surfaces_present | 2 | ✅ | 3/3 demo-able surfaces present |
| demo_dashboard | 1 | ✅ | demo dashboard built |
| demo_urls | 1 | ✅ | demo URL manifest present |
| deploy_artifacts | 1 | ✅ | deploy configs: 16 fly config(s), cloudflare tofu |
| go_live_seams | 1 | ⬜ | 7 blocking production seam(s) remain (demo≠go-live) |

## Top gaps (highest-weight first — the loop's marching orders)
- **[backends_green]** run the health flywheel until gates are green: ./loop run  (or scripts/flywheel_orchestrator.py --run)
- **[go_live_seams]** toward full go-live, next blocking seam: live LLM inference
