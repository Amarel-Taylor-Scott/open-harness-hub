# Capability Platform — Launch Checklist (inventory + gaps)

> 2026-07-06. What the 500K-primitive platform needs to ship as a product — grounded in what ALREADY EXISTS
> (reuse-first: most of the shell is built) vs named gaps. Product-structure/pricing/brand decisions are
> OWNER-GATED (change-verification law); this file inventories and names, it does not decide.

## Exists today (don't rebuild — wire and polish)

| Layer | Asset | Where |
|---|---|---|
| Website surfaces | 5 built-out apps (AI Done Right / Teleon / Baltor / OpenHubForAI / AIDevObserver) served by the showcase over the shared kit | `web/<brand>/` + `OH_PRODUCT=<brand> python3 -m scripts.showcase`; `docs/DESIGN-BIBLE.md` |
| Serving API | The capability front door: `/retrieve` `/compose` `/health` `/stats` over the stored lanes (112K→465K pool) — LIVE tonight behind a tunnel | `scripts/serve_capability_api.py`; tunnel via `cloudflared` |
| MCP | Retrieval MCP (`find_reuse` / `primitive_search` / `capability_compose`), AIDevObserver MCP, Teleon capability gateway, Baltor context gateway | `scripts/capability_retrieval_mcp_server.py` + `.mcp.json` (atomic-write fix noted in adversarial queue) |
| Registry plane | Registry federation port (list/lookup/search/explain), projection API seams (`/registry/…`, `/api/observer/…`) | `src/teleon/registry/port.py`; `OH_SEAM_*_BASE` |
| Auth design | Separate login per product, NO SSO, shared kit; identity seam; service-auth + consumption model designed | `/api/identity/` seam; `docs/architecture/service-auth-and-consumption-model.md` |
| Hosting lanes | Local-first + tunnels doc; Fly/compose deploy layer (`deploy_topology`) | `docs/architecture/local-dev-tunnels-and-auth.md`; fly lane owner-creds-gated |
| Installation | Phase-0 quickstart (receipts: quickstart green, launch 61/61, preflight GO); deps: `numpy`, `model2vec`, `fastembed`, Ollama; store builds `--build`/`--build-registers [--include-staged]` | `docs/codex/saas-north-star-roadmap.md` |
| Plugins/dev pack | Claude Code hooks (`pretooluse-aidevobserver`), commands (`find-reuse`, `review-session`, `refresh-primitives`), Observer CLI/ext/app design | `hooks/`, `commands/`, Observer memory |
| Docs | BIBLE, INTEGRATION-BIBLE, DESIGN-BIBLE, EXTENSION-POINTS table, handoffs, receipts under `data/dev-intel/session_emulation/` | repo docs |
| Proof/benchmark plane | 20+ registered gated modules; savings dashboard; real-token receipts (6 frontier models); coverage suites (SaaS/Kaggle/agentic/scenario/real-prompts/agent-actions) | `scripts/flywheel_proof_modules.py` |

## Gaps to launch (buildable now unless marked OWNER)

1. **API keys + rate limiting on the public API** — the design exists (service-auth doc); `serve_capability_api`
   currently serves unauthenticated. Add key check + per-key quotas + usage metering rows (telemetry
   write-only loop finding applies).
2. **Hosted persistence** — Fly machine + volume for the store artifacts (~$3–5/mo). OWNER: account/creds.
3. **Signup → key issuance flow** — wire the existing identity seam to key minting; per-product login per the
   auth-realms decision. OWNER: product naming/pricing on the signup surface.
4. **Docs site publish** — quickstart + API reference (`/retrieve`,`/compose`,MCP tools) + EXTENSION-POINTS;
   mkdocs build exists in repo tooling; publish target OWNER (aidoneright.dev subpath vs per-product).
5. **MCP distribution** — a one-line install (`npx`/`uvx` wrapper or `.mcp.json` snippet) for the retrieval
   MCP so any Claude/agent user mounts the 500K pool; document in README of the public repo. OWNER: which
   org repo publishes.
6. **Usage/analytics loop** — retrieval hits → observer `/outcome` (roadmap #1) = free labels + the online
   gold set; closes benchmark trust too.
7. **Status/health surface** — `/stats` exists; surface it on the product status page (kit component exists).
8. **Billing** — OWNER entirely (Stripe primitives exist in-corpus, fittingly).
9. **Promotion pipeline UI** — staged→verified review queue surface for the 352K staged candidates
   (candidate-truth law; review tickets exist as row family).
10. **Kaggle/app/idea ingestion lanes** — writeups scraper (auth-gated: needs Kaggle creds), app-manifest
    ingester, idea intake (request_intake IS the intake engine — wire it to a public form).

*serves_truth=false — an inventory, not a roadmap decision. Supersede lines here as gaps close.*
