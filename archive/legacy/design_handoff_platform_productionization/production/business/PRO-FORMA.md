# Pro-Forma — costs, expenses, revenue (honest startup model, Pass 11)

**Every number below is an ASSUMPTION to validate, not a claim.** Infra prices are
Jun-2026 verified (see cloud/ docs); revenue numbers are illustrative scenarios with
stated conversion assumptions. Update monthly against actuals (OPERATIONS.md cadence).

## 1. Cost structure by stage (monthly, USD)

### Stage 0 — now (pre-revenue, L0/L1)
| Line | Cost | Note |
|---|---|---|
| Infra | $0 | laptop + tunnels |
| Domain portfolio | ~$8–100 | aidoneright.dev + baltor.ai + teleon.dev ≈ $100/yr total. **The 21 hub .io domains ≈ $35–60/yr EACH (~$700–1,250/yr)** — recommendation: hubs live as subdomains (context.aidoneright.dev) until a hub earns its flip; buy each .io at its launch event, not before. |
| Email/analytics/CI | $0 | Resend free 3k/mo · PostHog free tier · Actions free tier |
| LLM providers | usage | dev-scale; attributable per key via receipts from day one |
| **Total burn** | **≈$10–20/mo** | + LLM usage |

### Stage 1 — first users (L2)
Infra $9.49–24 (one VM) · email $0–20 · monitoring $0 (uptime-kuma self-hosted) ·
**total ≈ $15–50/mo**.

### Stage 2 — first revenue
VM + maybe Cloud Run split ($50–200) · email $20 · PostHog $0–50 · Stripe fees
(2.9% + 30¢ — a COGS line, not fixed) · **total ≈ $100–300/mo**.

### Stage 3 — growth (only on S-F triggers)
K8s or multi-VM $500–2k · tooling $100–300 · **total ≈ $600–2,500/mo** — by this
stage MRR must already cover it (see break-even below), or we don't enter.

**Structural note:** payroll/founder time dominates any real startup P&L; this model
prices infrastructure + tooling only and assumes founder-operated until revenue
justifies otherwise. That assumption is the biggest one on this page.

## 2. Revenue model (pricing TO VALIDATE with first 10 customers)

| Product | Tier | Price (assumption) | What gates it |
|---|---|---|---|
| Baltor | Team | $99/mo | realms, packs, verification rail limits |
| Baltor | Growth | $499/mo | volume + SLA + private sources |
| Teleon | Team / Growth | $99 / $499/mo | capabilities count, proof runs |
| Either | Enterprise / self-host | $2k+/mo | signed containers + verified-deployment handshake (S-E: $0 infra for us) |
| Hubs | Free | $0 | top-of-funnel; paid private registries are a LATER experiment |
| LLM plane | usage passthrough + 20–30% margin | metered | receipts are the meter (shipped) |

## 3. Funnel arithmetic (12-month scenarios)

Assumptions: visitor→signup 2% · signup→activated 40% (activation events defined in
BUSINESS-PLANE.md) · activated→paid 7% (range 3–15%) · blended ACV $150/mo ·
churn 3%/mo. Visitors come from the hub content engine (MARKETING.md).

| Scenario | Hub visitors/mo @ M12 | Paying @ M12 | MRR @ M12 | Infra+tools cost |
|---|---|---|---|---|
| Conservative | 5,000 | 3–4 | ~$500 | $50 |
| Base | 20,000 | 11–12 | ~$1,700 | $150 |
| Optimistic | 75,000 | 40+ | ~$6,300 | $400 |

**Break-even on infrastructure: 1 paying customer.** That is the punchline of the
whole cost discipline — the ladder keeps fixed costs under one seat of revenue until
growth is measured, so the company cannot die of infrastructure. The real risk line
is founder time, not hosting.

## 4. Unit economics to watch (receipts make these computable)
- LLM gross margin per key: (billed − provider cost) / billed — receipts give both sides.
- Infra cost per active realm: bench + deploy receipts ÷ active realms.
- CAC stays ≈$0 while channels are organic (hubs/SEO/launches); first paid channel
  experiment needs its own pro-forma line before spend (S10).

## 5. Review cadence
Monthly: actuals vs this file; any assumption off by >2× gets rewritten, with the
delta recorded in the pass log. This file is a living model, not a pitch.
