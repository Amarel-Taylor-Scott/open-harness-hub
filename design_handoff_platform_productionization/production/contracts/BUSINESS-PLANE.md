# Business Plane — analytics · transactional email · payments (contracts)

The product-side services every realm needs, behind ports we own (S12). Vendors are
adapters; code outside an adapter file never names a vendor. Prices verified Jun 2026;
re-verify at adoption.

## 1. Analytics & tracking

**Port:** the events plane we already have — `POST /api/events` with the EVENTS.md
shape (site, event, name, experiment/variant, anon, props). That POST **is** the
abstraction; everything else is a downstream sink.

| Sink (adapter) | When | Cost |
|---|---|---|
| core JSONL + `/summary` (shipped) | now | $0 |
| **PostHog** (product analytics: funnels, retention, session replay) | first real users; self-host option keeps local-first credible | free tier generous; self-host $0 + VM |
| BigQuery / DuckDB | warehouse questions across products | DuckDB $0 → BigQuery usage |

Rules: anon ids only, never PII in events (S7) · A/B = OHExp assignment + exposure/
conversion events (shipped) · every funnel stage below maps to ONE named event.

**PMF instrumentation (the funnel, per product):**
```
discover (hub page view) → engage (demo run / browse) → signup (realm register)
→ activate: Baltor = first verified pack SERVED · Teleon = first capability PROVEN
            · hub = first pull/publish
→ retain (7d return) → revenue (key with billing attached)
```
Activation events are the PMF signal; review weekly per realm via /summary (later PostHog).

## 2. Transactional email

**Port:** `email.send(realm, template, to, props)` — one module, realm-branded
templates (accent from products.js), audit receipt per send, request-id correlated.
Needed by: register/verify, password reset, key-minted notice, receipts digest.

| Adapter | When | Cost (Jun 2026) |
|---|---|---|
| **console/file adapter** (dev) | now — writes the rendered email to audit log; honest no-send | $0 |
| **Resend** (default first real adapter) | first external user | free 3k/mo · $20/mo for 50k |
| **Postmark** (if deliverability becomes critical) | auth emails missing inboxes | $15/mo for 10k; best inbox rates, hard transactional/broadcast separation |
| **Amazon SES** (scale) | >200k/mo and engineering time exists | $0.10/1k |

Rules: SPF+DKIM+DMARC on every sending domain before the first real send · no
marketing mail through the transactional stream, ever (deliverability isolation) ·
dev mode never silently sends (Mode Protocol S2 applies to email too).

## 3. Payments & billing

**Port:** `billing` plane — `customer`, `subscription`, `usage_record`, `invoice` —
keyed by realm + user, fed by the receipts we already emit (LLM usage per key is
attributable from day one; that IS the metered-billing feed).

| Adapter | When | Notes |
|---|---|---|
| **ledger-only adapter** (shipped concept) | now | records what WOULD be billed from receipts; $0; proves the meter before charging |
| **Stripe** (default) | first paying customer | usage-based billing on metered events; webhooks → events plane |
| **Paddle / Lemon Squeezy** (merchant-of-record) | selling globally without tax entity overhead | higher take rate buys VAT/sales-tax handling — decide at first international revenue |

Rules: prices/plans live in ONE config (no magic numbers in checkout code) · the
ledger adapter runs FOREVER in parallel (receipts reconcile Stripe, not vice versa —
the house thesis applied to our own billing) · refunds/disputes append events, never
mutate history.

## 4. Adoption order (one per pass, each with proof)

1. Ledger-only billing adapter over LLM receipts → a "what would this month cost"
   statement per key. Proof: statement matches receipt sums.
2. Email port + console adapter wired into register/reset flows. Proof: rendered
   emails in audit log with request ids.
3. PostHog sink behind the events plane (env-gated). Proof: funnel chart shows
   discover→activate for one realm.
4. Resend adapter (vault-keyed). Proof: one real verification email round-trip.
5. Stripe adapter in test mode. Proof: metered usage invoice draft matches ledger.
