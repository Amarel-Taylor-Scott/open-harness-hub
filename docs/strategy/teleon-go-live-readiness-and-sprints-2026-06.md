# Teleon/Baltor — go-live readiness + sprint plan (2026-06)

**Status:** grounded in `scripts/check_teleon_go_live_readiness.py` (run it for the live snapshot). Honest by
design: the deterministic ENGINE is built + proof-gated; **go-live is gated on wiring the live seams below.** This
is the capability-gap + sprint list to get on real cloud hosting with real tenants.

## Where we are (verified by running it)

**Built + proof-gated (the engine):** 510 deterministic proofs green; preflight GO. The assurance/descent engine
runs end-to-end on sample skills (`scripts/demo_assurance_descent.py`): token-aware A/B descent (deterministic /
cheaper-model / compressed-prompt, within an accuracy floor) · tunable tenant preferences + hard blockers
(MIT-only, vetted-only, no-egress) compiled to a policy + objective · freshness (stale held out, never served) ·
cost + token (in/out) measurement · governed throughout (serves_truth=false). 2,282 governed candidate
capabilities; 17 descent axes; the meta-learner + skills DB; deploy topology config.

**The honest gap:** almost all of the above is **deterministic + offline** (specs, ports, stubs, representative
scorers). Going live = wiring the LIVE seams. `readiness_report().go_live_ready == False` and stays False until
the blocking seams are closed.

## Capability gap → blocking live seams (the readiness report)

| seam | what's there | what go-live needs |
|---|---|---|
| **hosting deploy** | `deploy_topology.json` + Fly/compose generator, runbook | actually run the deploy; container e2e against the live region; DNS/TLS/secrets |
| **live LLM inference** | lanes/adapters (Codex/Ollama/Gemma) degrade to provider_unavailable offline | provider keys + a live smoke per lane; route real calls through egress capture + receipts |
| **live source + CDC freshness** | freshness runtime holds stale out (values passed in) | a real source poller → freshness CDC `changed` events → self_healing reheal, per regulated-fact source |
| **real distillation** | forks are governed *specs* (the rule it represents) | wire the determinism factory to a model to GENERATE the rule from verified traces; shadow before promote |
| **real eval data** | RuleArena + vertical eval *fixtures* (representative) | ingest real benchmark/eval datasets so the A/B scorer is live, not representative |
| **Postgres + promotion** | candidates in JSONL staging; promotion boundary in code | load → Postgres/pgvector; enforce candidate ≠ tenant-visible at the DB |
| **auth + tenancy** | `auth_kit` (separate realms), API-key/service-auth design docs | wire per-product auth + per-tenant isolation + API keys/service accounts |
| **vetting workflow** | `vetted_only` hard blocker enforced | a human/eval vetting gate that *sets* `vetted=true` (the flag has no producer yet) |
| **observability** | RunLedger telemetry + receipts (in-memory) | ship receipts/metrics to a backend (OTel/Langfuse) + drift/staleness alerts |
| **tenant surface** | the descent-walkthrough journey + the demo | the Capability Assurance Portal UI (set preferences, watch a capability descend with receipts) |

## Sprint plan (prioritized — polish / review / connect / wire)

**S0 — Hosting live (1 sprint).** Run the Fly (lean ~$40-50; per the hosting-decision-matrix) deploy from
`deploy_topology.json`; same-region/private-network for Baltor→Teleon; container e2e against the live region;
secrets via env refs (never raw keys); DNS + TLS for teleon.dev / baltor.ai. *Exit:* a governed request round-trips
in prod; preflight + container e2e green against live.

**S1 — Live adapters (1–2 sprints).** (a) Wire live LLM inference: keys per lane, a live smoke, real calls through
egress capture + ModelInvocationReceipt (LLM output never truth). (b) Wire live source fetch + CDC: a poller per
regulated-fact source → freshness `changed` events → reheal; prove "rule changed → stale held out → re-synced" on a
REAL eCFR/Federal-Register source. *Exit:* one vertical answers from a live, freshness-synced, receipted source.

**S2 — Distillation live (1–2 sprints).** Wire the determinism factory to a model to GENERATE the deterministic
rule a fork represents, from verified traces; shadow + side-by-side before promote (lossless law). Ingest real
eval datasets so the A/B harness decides on live accuracy (the +0.71 RuleArena lift becomes a production signal;
the meta-learner lift moves off 0.0). *Exit:* a real model-bound capability is auto-distilled to a deterministic
rule that re-passes its benchmark; A/B picks it on live evals.

**S3 — Governance live (1 sprint).** Load staged candidates → Postgres/pgvector; enforce the promotion boundary at
the DB (candidate ≠ tenant-visible; open review tickets / placeholder embeddings / unresolved sources block).
Build the vetting gate that sets `vetted=true`. *Exit:* a tenant with `vetted_only` sees only DB-promoted, vetted
capabilities; nothing tenant-visible without a receipt.

**S4 — Auth + tenancy (1 sprint).** Wire `auth_kit` per product (separate realms, no SSO), per-tenant isolation,
API keys/service accounts, delegated calls. *Exit:* two isolated tenants run the same capability under their own
preferences + data; no cross-tenant leakage.

**S5 — Observability + surface (1–2 sprints).** Ship receipts/metrics to OTel/Langfuse; alerts on drift/staleness/
cost; build the Capability Assurance Portal (set preferences, watch descent + receipts). *Exit:* a tenant
self-serves preferences and sees a live, receipted assurance dashboard.

## Connect / wire checklist (cuts across sprints)
- Replace representative scorers (`ceiling_scorer`, eval fixtures) with live eval suites per vertical.
- Replace `model_*` distillation cost constants with observed RunLedger telemetry (close the meta-learner loop).
- Wire the `vetted` flag through the seeder → vetting gate → policy.
- Surface the cost/token/freshness measurements in the portal + receipts.
- Add the remaining descent axes the gateways gap (observability, caching, concurrency) as registry entries.

## Honest risks to own
- **Breadth is candidate-stage** (discovery ≠ trust) — convert candidates → DB-promoted, vetted, customer-facing.
- **The lift is demonstrated, not yet live** — S2 makes it a production number.
- **Competitors ship** (Probably/a16z, Pramaana/Khosla); our defensible wedge is *freshness + provable
  source-authority + multi-axis governed breadth as the layer above any model/gateway/prover* — S1/S2 make that
  real on a vertical.

**Definition of go-live (the gate flips true):** all blocking seams closed → one regulated-fact vertical, on real
cloud hosting, answering from a live freshness-synced + receipted source, with capabilities auto-descended (A/B on
live evals) within a tenant's hard/soft preferences, isolated per tenant — and `readiness_report().go_live_ready`
returns True.
