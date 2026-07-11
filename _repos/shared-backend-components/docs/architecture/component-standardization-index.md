# Component Standardization Index (2026-06-10)

**The single map of how every cross-cutting component works across the AI Done Right family** —
website, login, registration, sessions, API keys, service-to-service auth, analytics/A-B,
transactional email, billing. For each: the standard, the one implementation, its proof, and an
HONEST status. The standards themselves were real but scattered across ~15 docs + the design
bundle's S1–S13; this is the index that ties them together. Counts/rosters are gated by the named
proofs, never this prose.

Status key: **STANDARDIZED** = one contract + one implementation + a proof, used everywhere ·
**PARTIAL** = standardized for part of the surface, rest is spec · **SPEC** = contract written,
not yet built.

## The matrix

| Component | Standard (contract) | One implementation | Proof | Status |
|---|---|---|---|---|
| **Website / design** | S1 branded house · `oh-tokens.css` (single color source) · `products.js` (single brand source) · `makeHub` (config-driven hub engine) · `docs/standards/DESIGN.md` | the design bundle + the 21 hubs are ONE engine; `web/` SPAs share the kit | `check_ai_done_right_surface_family` | **STANDARDIZED** (roll-out of shared tokens to `web/` is the one open item) |
| **Login / registration / sessions** | one shared auth KIT, separate realms, no SSO (`docs/architecture/auth-identity-kit.md`) · S3 API conventions (`/api/identity/<realm>/*`, `X-AIDR-Request-Id`) | `_repos/openhubforai/backend/src/openhubforai/auth_kit` + `scripts/identity_local_service.py` (register→onboard→login→session, all 12 realms) · client `_repos/openhubforai/frontend/identity.js` | `check_auth_kit_realm_isolation` · `check_identity_local_service_runtime` · `check_openhubforai_auth_wiring` | **STANDARDIZED** |
| **User API keys** | raw shown ONCE, hash-only at rest, session-gated mint/list/revoke (S8) | the identity service's `api-keys/*` actions | `check_identity_local_service_runtime` | **STANDARDIZED** |
| **Service-to-service auth** | `service_auth_consumption_model.json` · `/service/*` handshake · 8-scope vocabulary (S3) · `SERVICE_<REALM>_SECRET` from env | the identity service's `service/handshake|verify|revoke|connections` | `check_service_auth_consumption_model` · `check_service_handshake_slice` | **STANDARDIZED** |
| **Analytics / events / A-B** | `EVENTS.md` — one event shape (`site·event·name·experiment·variant·anon·props`) · `POST /api/events` · `/summary` | `scripts/events_local_service.py` + beacon `_repos/openhubforai/frontend/events.js` (PII-guarded, anon-only) | `check_local_events_plane` · `check_events_beacon_wiring` | **STANDARDIZED** (PostHog sink is an env-gated seam) |
| **Transactional email** | `email.send(realm, template, to, props)` — one port, realm-branded, Mode Protocol (never silently sends) — BUSINESS-PLANE §2 | `scripts/email_port.py` — console adapter (renders to outbox + audit, `sent=False`); **WIRED into identity registration** (register renders a realm-branded `verify_email`); Resend/Postmark owner-gated seams | `email_port` · `check_identity_local_service_runtime` | **STANDARDIZED (local + wired)** — real-send adapters owner-gated (provider keys) |
| **Billing** | receipts reconcile the provider never vice versa (BUSINESS-PLANE §3) · CLASS→rate single source · plans single-sourced | `scripts/billing_ledger.py` (statements + `reconcile()`) + `scripts/billing_plane.py` (meter → DRAFT invoice = subscription + overage; Stripe owner-gated seam) | `billing_ledger` · `billing_plane` | **STANDARDIZED (local)** — full metered draft-invoice chain built; live Stripe test-mode + webhooks→events is the owner-gated next step |
| **Secrets** | `secret_ref://` / env only; never in repo/log/artifact (S8) | enforced by every service above (key hashes, `secret_ref`) | `check_no_raw_secrets_in_e2e_artifacts` + per-service guards | **STANDARDIZED** |
| **Component build (factory)** | `architecture/standard_catalog.json` + `template_catalog.json` + status enum draft→active→enforced→deprecated | `scripts/generate_from_template.py` | the catalog's own proofs | **STANDARDIZED** |
| **Mode Protocol (honesty)** | S2 — every client is live / simulated / unknown; a real action is NEVER silently faked | implemented by oh-identity.js, the email port, the demos | the surface proofs | **STANDARDIZED** |
| **Service map / deploy** | `services.json` (one manifest) → generated routes; one `/api/<plane>/*` namespace everywhere | the productionization handoff (gateway running on :8080) | `check_local_services_health` · `check_service_auth_consumption_model` | **STANDARDIZED** |

## Honest answer to "do we have standardization?"

**Yes for the front-of-house and identity/events/service-auth/secrets layers** — website, login,
registration, sessions, API keys, service-to-service auth, analytics/A-B, and (as of 2026-06-10)
transactional email are each ONE contract + ONE implementation + a proof, used across every
product/realm. The 21 hubs are literally one engine; the 12 identity realms are one kit.

**Remaining gaps are now OWNER-GATED, not unbuilt** (closed 2026-06-10):
1. **Billing** — the metered draft-invoice chain IS built (`billing_plane.py`: subscription +
   overage-above-allowance on the ledger authority); only the **live Stripe test-mode transport +
   webhooks→events** remains, and that's an owner-gated seam (needs `STRIPE_API_KEY`).
2. **Email** — the port + console adapter are built AND **wired into registration** (a real
   `verify_email` renders on register, honestly not sent); only the **real Resend/Postmark
   transport** remains, owner-gated (needs a provider key). Wiring into the password-reset flow is
   the one small follow-up.

The full customer flow — landing → register (→ verification email rendered) → onboard → configure
→ integrate (API key) → product use (pipeline + Baltor engine) → first draft invoice — is recorded
end-to-end in `artifacts/e2e/videos/full-journey.mp4` (12 stages).

**Design roll-out:** the shared design tokens are standardized in the bundle but not yet rolled
into the production `web/` SPAs (fonts differ) — tracked, low risk.

## Where the standards live (so this index stays the front door)
- Design + lifecycle: design bundle `production/standards/STANDARDS.md` (S1–S13)
- Component build: `_repos/baltor/context/standards/README.md` + `architecture/standard_catalog.json`
- Identity: `docs/architecture/auth-identity-kit.md`
- Service auth: `docs/architecture/service-auth-and-consumption-model.md`
- Events / email / billing contracts: design bundle `production/contracts/{EVENTS,BUSINESS-PLANE}.md`
