# Gap-closure plan — toward fully working + go-live (2026-06-22)

Principle (owner): fill ALL gaps, fully working, fully flexible, **no shortcuts** (no JSONL-where-a-DB-belongs), real
abstractions / agnostic layers / tool + API wrappers everywhere. Status below is honest: BUILDABLE (I close it on the
loop, no owner input) vs OWNER (irreducible — external action / owner-only fact / spend; best-effort draft provided).

**No-shortcut audit (done):** operational data is a REAL indexed SQLite DB (`.agent/state-index/*.db`, WAL) behind the
`record_store` port — JSONL is only the durable append-log/interchange; Postgres+pgvector is the cloud backend via the
SAME port. Locked by `check_registry_storage_tiers` ("operational store is a REAL SQLite DB, not a JSONL shortcut").
Config stays JSON/git by design (bounded, PR-reviewed). Every tool category is an agnostic PLANE (30) behind a port;
LLM/browser/OCR/source-search/credential/storage are all wrapped.

## Go-live seams (was 7 blocking → now 6)
| seam | status | who | next |
|---|---|---|---|
| live LLM inference | **CLOSED** ✅ — primary Ollama/Gemma lane live-verified (`data/dev-intel/live-llm-smoke.json`, gemma4:31b) | — | other lanes are key-gated add-ons |
| live source fetch + CDC freshness | BUILDABLE — keyless search/Wikipedia/Federal-Register already run live (`real_steps`) | me | wire a source poller → CDC `changed` → self-heal reheal |
| real distillation (LLM→rule) | BUILDABLE — the LLM lane is live now | me | distill one verified rule from a fork end-to-end |
| real per-vertical eval data | BUILDABLE (public datasets) | me | ingest RuleArena + a vertical eval so the A/B scorer is live |
| Postgres/pgvector load + promotion boundary | **~DONE** — port operational tier (SQLite local / Postgres cloud) + `promote_tools` boundary + staged≠descent-visible; round-trip proven | owner | a cloud **Postgres URL** to run the live load (logic is wired) |
| auth + tenancy (separate realms) | **~DONE** this session — `access_policy` + credential plane + key_holder + per-principal entitlement + auth_kit | me/owner | per-tenant isolation wiring in the live product |
| hosting deploy executed + verified | OWNER — needs `FLY_API_TOKEN` + account/billing | owner | then the agent runs the Fly deploy from `deploy_topology.json` |

## YC scorecard owner gaps (0.75 — all 3 are owner-only; drafts below)
**founder_market_fit (draft to fill):** answer, in 3–4 sentences — *what do you know about governed AI context that almost
no one else does (the earned insight)? what is the hardest thing you've built, and why does it prove you can build this?
why you, why now?* → paste into `docs/strategy/teleon-naming-and-domain.md` founder section. (Owner-only fact.)

**decisions_locked (recommendation to ratify):** raise — a pre-seed/seed sized to ~18mo runway at the chosen host (~$40–50/mo
infra is negligible; the spend is people); pricing — **usage + governed-seat** (per verified-capability-run + a platform
seat), free export funnel, paid governed live layer (per the monetization memory); one-liner — *"AI, done right: the
governed runtime that makes every AI capability cheap, bounded, and provably true."* → ratify or edit. (Owner decision.)

**traction_design_partner (outreach + pilot package draft):** ICP = a compliance/ops team drowning in document-heavy
adjudication (the insurance-free adjacent verticals). Offer: a 90-day pilot that EXPORTS a governed capability package
their own agent/RAG consumes, with a **before/after report** (cost per decision, error rate, provenance coverage). The
sanctions/OFAC + CFPB receipts are the proof. → owner sends; the agent builds the pilot package + the report. (Owner GTM.)

## What I'm closing next (no owner input needed)
1. live source fetch + CDC (#2 above) — a real poller → CDC → reheal.
2. real distillation — one LLM→deterministic-rule, verified.
3. then eval data ingest. Each lands proof-gated; the daemon keeps looping in parallel.
