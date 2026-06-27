# Auth & Identity — one shared kit, completely separate realms per product

**Owner decision (2026-06-09):** *"completely separate and independent logins / register / onboarding, but we
can have similar UI, backend elements."* This is the standard.

## The model

- **Shared KIT** — one set of flow shapes, object shapes, and primitives lives in
  `src/openhubforai/auth_kit/` (the open, bottom layer). Same UI components, same backend elements.
- **Separate, INDEPENDENT realms** — each product (Baltor, Teleon, every OpenHubForAI) calls `make_realm(...)` to
  get its **own** identity realm: its own accounts, its own sessions, its own registration. **There is no
  cross-realm account and no single-sign-on.** Logging in to Baltor has nothing to do with Teleon.

This mirrors two existing laws: the **portfolio dependency law** (Baltor and Teleon are *identity-separated*,
separable services) and the **branded house** (shared kit + per-product instance; only the accent differs).

## Placement + dependency law

The kit is in **OpenHarnessHub** because it's the open bottom layer: Baltor → Teleon → OpenHarnessHub. So
Baltor and Teleon may both import the kit; OHH imports neither (enforced by `check_portfolio_dependency_law`).
The kit is reference infrastructure — **not** a deployed auth service.

## The standard flow (shared shape, independent per realm)

`register → onboarding → login` (`STANDARD_FLOW`):
1. **register(identifier, secret)** → an account in *this* realm. The secret is hashed to a one-way
   `credential_ref`; **the cleartext secret is never stored or echoed**.
2. **onboard(account_id, step)** → advance the realm's onboarding steps; the account becomes `active` only when
   all steps are done.
3. **login(identifier, secret)** → realm-scoped: the account must exist *in this realm*, be active, and pass
   credential verification → mints an opaque, realm-scoped **session** handle (validated only by this realm).

## Objects

| Object | Notes |
|---|---|
| `Realm` | one product's isolated realm — own `accounts` + `sessions` + registration; realm-scoped login/validate. |
| account | `{account_id, realm_id, identifier, credential_ref, status∈ACCOUNT_STATUSES, onboarding_done, created_at}`. `credential_ref` is a **one-way ref** (`credref:…`), never cleartext. |
| session | `{session_id, realm_id, account_id, issued_at, expires_at}` — an opaque handle, **not** truth and **not** a secret; valid only in its own realm. |

## Seams (where the real, deployed pieces drop in — owner-gated)

- **`CredentialProviderPort`** — verify a presented secret against the stored ref. Reference impl is a blake2b
  one-way ref (deterministic, **NOT production crypto**); a real provider (argon2/bcrypt password hash, OAuth
  subject, SSO assertion, passkey) drops in here.
- **Session/clock** — sessions use a deterministic handle + an **injected logical clock** (`now: int`) for
  offline determinism; a real JWT/cookie + wall-clock TTL is the production swap.

No real secrets, crypto keys, or network live in the kit (stdlib-only, deterministic, offline).

## Proof

`scripts/check_auth_kit_realm_isolation.py` — shared-kit/separate-realms, the standard flow (login rejected
until onboarded; wrong credential rejected), realm **isolation** (a session from realm A is invalid in B; an
A-only identifier can't log in to B), **no cross-realm SSO** (disjoint stores), **no cleartext secret**
(credential is a ref), deterministic + injected-clock expiry.

## Built (2026-06-09): the local Identity & Access service

Per-product realm **instantiation is done** — realms are DATA in
`architecture/identity_realm_registry.json` (parent + Baltor + Teleon + every **live** OpenHubForAI, drift-gated
against the owning `products.js`; private bench hubs are excluded — internal service identity only), run by
`scripts/identity_local_service.py`:

- the standard flow over HTTP (`/api/identity/<realm>/register|onboard|login|logout|session/validate`),
- **API keys** per realm — hash-only at rest, raw value shown exactly once at mint, session-gated
  mint/list/revoke, `verify` for service callers (service-auth Phase 1 slice),
- audit JSONL with `X-AIDR-Request-Id` correlation; restart-safe persistence under `dist/identity/`
  (the kit gained realm-guarded `snapshot()`/`restore()` for this — a cross-realm snapshot is rejected).

Run: `PYTHONPATH=. python3 scripts/identity_local_service.py --serve` (port from the realm registry).
Proof: `scripts/check_identity_local_service_runtime.py` (in `PROOF_MODULES`). Still a **local dev
equivalent** — blake2b refs are not production crypto; the owner-gated seams below are unchanged.

**Also built (2026-06-09): the first wired product UI.** `web/openhubforai/identity.js` (realm client:
drift-gated port, `OHH_IDENTITY_BASE` deploy override, request-id correlation, session-handle-only storage)
+ `pages/auth.js` rewired — real register→onboard→login→session, an `/account/keys` console (raw key shown
once), SSO/Google rendered as **disabled owner-gated seams**, honest degradation when the service is down
(never fakes a login). Proof: `scripts/check_harness_hub_auth_wiring.py` (static contract + `node --check`).
Browser-session (DOM-level) verification still pending a browser run.

## Queued (not yet built; some owner-gated)

- The shared **UI kit** — promote the now-wired openhubforai flow (`identity.js` + `pages/auth.js`) into the
  shared design kit so every surface (Baltor, Teleon, each hub) renders one flow against its OWN realm.
- **Real** `CredentialProvider` / session adapters (password hash, OAuth, SSO, passkey) — **owner-gated**,
  built when deploying; never with real secrets in this repo.
- Formal `schemas/identity/*.schema.json` + fixtures wired to `scripts/validate.py`.
