# Taedri go-live runbook — payments · domain · Cloudflare · monitoring · email

> Single source for taking https://taedri.fly.dev from "deployed and working" to "charging customers on a
> real domain with monitoring". Copied verbatim to the deploy-bundle root as `RUNBOOK.md` by
> `scripts/build_capability_saas_bundle.py`. Every claim about live state is COMPUTED by an endpoint or a
> command listed here — trust those over any prose literal. Steps are labeled **[owner]** (needs your
> account/payment) or **[agent]** (Claude can run it once the owner step before it is done).

## 0. What is already live (verify, don't trust)

- App: https://taedri.fly.dev (Fly app `taedri`, region `iad`, 2 CPU / 4 GB, volume `capability_data`).
- Deploy pipeline: push to `main` of `aidonerightcorp/taedri` → `fly-deploy` workflow → `flyctl deploy`
  (`FLY_API_TOKEN` repo secret is set and working).
- Ops workflows: `fly-ops` (any flyctl command by dispatch), `sync-fly-secrets` (GitHub secrets → Fly),
  `healthcheck` (15-minute live probes; a failure fails the run and GitHub emails watchers).
- Payments: the gateway ships the full Stripe seam but it is DISABLED until the three `STRIPE_*` secrets
  exist — `curl -s https://taedri.fly.dev/v1/billing/status` computes the current truth.

```bash
curl -s https://taedri.fly.dev/healthz               # {"ok": true, "service": "taedri-gateway", ...}
curl -s https://taedri.fly.dev/v1/billing/status     # payments_enabled + the exact missing secret names
gh run list --repo aidonerightcorp/taedri --limit 5  # deploy + healthcheck history
```

## 1. Payments — activate Stripe (~20 minutes)

1. **[owner]** Create the account: https://dashboard.stripe.com → complete the business profile. Start in
   **test mode**; repeat step 5 with live keys when ready.
2. **[owner]** Create the product: Products → Add product → name `Taedri Capability Pro` → recurring →
   **$29.00 / month** (that is the draft price in `billing_plane.PLANS`; you may change it here — the
   charged amount is ALWAYS the Stripe Price object, so no code change is needed). Copy the price id
   (`price_…`).
3. **[owner]** Copy the API key: Developers → API keys → secret key (`sk_test_…` now, `sk_live_…` later).
4. **[owner]** Create the webhook: Developers → Webhooks → Add endpoint →
   `https://taedri.fly.dev/v1/billing/webhook` (update to the custom domain later) → subscribe to
   `checkout.session.completed` and `customer.subscription.deleted` → copy the signing secret (`whsec_…`).
5. **[owner or agent given the values]** Set the secrets and sync them to Fly:

   ```bash
   gh secret set STRIPE_API_KEY        --repo aidonerightcorp/taedri   # paste sk_…
   gh secret set STRIPE_PRICE_ID_PRO   --repo aidonerightcorp/taedri   # paste price_…
   gh secret set STRIPE_WEBHOOK_SECRET --repo aidonerightcorp/taedri   # paste whsec_…
   gh workflow run sync-fly-secrets    --repo aidonerightcorp/taedri
   ```

6. **[agent]** Verify end to end:

   ```bash
   curl -s https://taedri.fly.dev/v1/billing/status          # payments_enabled: true, mode: test|live
   KEY=$(curl -s -X POST https://taedri.fly.dev/v1/signup -d '{"email":"you@example.com"}' \
         | python3 -c 'import json,sys; print(json.load(sys.stdin)["api_key"])')
   curl -s -X POST https://taedri.fly.dev/v1/billing/checkout -H "Authorization: Bearer $KEY"
   # open checkout_url → test card 4242 4242 4242 4242 → then:
   curl -s https://taedri.fly.dev/v1/usage -H "Authorization: Bearer $KEY"   # plan: capability_pro
   ```

Behavior once enabled: `/v1/upgrade` to a paid plan returns **402 payment-required** (no more free flips);
only the signature-verified webhook changes a plan. Nothing is ever charged while disabled — the honest
"plans are recorded, nothing is charged" state is computed, not asserted.

## 2. Domain — buy `taedri.dev`

RDAP-checked available on 2026-07-11: `taedri.dev`, `taedri.com`, `taedri.io`, `taedri.app`, `taedri.net`.
The repo's standing convention is **`taedri.dev`** (matches `teleon.dev` / `aidoneright.dev`); grabbing
`taedri.com` too as a redirect is cheap insurance, optional.

1. **[owner]** Easiest path — buy it inside Cloudflare (at-cost, WHOIS privacy included): create the
   Cloudflare account first (section 3), then Domain Registration → Register Domain → `taedri.dev`
   (≈ $10–13/year). Alternative registrars (Porkbun, Namecheap) work — set the nameservers to the ones
   Cloudflare shows when you add the zone.
2. **[agent]** Attach the domain to Fly (TLS certs + the DNS targets):

   ```bash
   gh workflow run fly-ops --repo aidonerightcorp/taedri -f command="ips list"
   gh workflow run fly-ops --repo aidonerightcorp/taedri -f command="certs add taedri.dev"
   gh workflow run fly-ops --repo aidonerightcorp/taedri -f command="certs add www.taedri.dev"
   gh workflow run fly-ops --repo aidonerightcorp/taedri -f command="certs show taedri.dev"
   ```

3. **[agent, needs the Cloudflare API token]** Create the DNS records the `certs` output asks for —
   typically `A @ → <fly IPv4>`, `AAAA @ → <fly IPv6>`, `CNAME www → taedri.fly.dev`, plus the
   `_acme-challenge` CNAME. Keep records **DNS-only (grey cloud)** until `certs show` says Ready, then
   optionally flip to Proxied for the CDN.
4. **[owner]** Update the Stripe webhook endpoint URL to `https://taedri.dev/v1/billing/webhook`.

## 3. Cloudflare — DNS, CDN, email (free plan is enough)

1. **[owner]** Account: https://dash.cloudflare.com sign-up → add site `taedri.dev` (skip if registered
   through Cloudflare — the zone exists automatically).
2. **[owner]** API token so the agent can automate DNS: My Profile → API Tokens → Create Token → "Edit
   zone DNS" template → zone `taedri.dev` (+ `Zone → Zone → Read`) → paste into the monorepo `.env`:
   `CLOUDFLARE_API_TOKEN=…` and `CLOUDFLARE_ACCOUNT_ID=…` (both names are already scaffolded in
   `.env.example`; the current values there are placeholders).
3. **[agent]** DNS records per section 2; verification: `curl -sI https://taedri.dev/healthz`.
4. **CDN**: after certs are Ready, set the `A`/`AAAA`/`www` records to Proxied. The gateway sends
   `Cache-Control: no-store` on API responses, so proxying is safe — the CDN accelerates the landing and
   static surfaces and hides the origin.
5. **Email**:
   - Inbound (free): Cloudflare Email Routing → route `hello@taedri.dev` → your Gmail; also add
     `support@`. Cloudflare inserts the required MX/SPF records itself.
   - Outbound transactional (signup receipts, payment confirmations): pick Resend (free tier 100/day) or
     Postmark later; verify the domain (DKIM/SPF records in Cloudflare). The gateway does not send email
     yet — signup returns the key in-response, so email is a growth nicety, not a launch blocker. When
     wanted, the seam is one env-gated sender in the gateway (same pattern as the Stripe seam).

## 4. Monitoring, alerts, logs

- **Shipped — `healthcheck` workflow**: probes `/healthz`, the landing marker, `/v1/stats/domains`, and
  `/v1/billing/status` every 15 minutes; any failure fails the run. **[owner, 1 minute]** Watch the repo
  (GitHub → Watch → All activity) and keep Actions email notifications on — that is the alert channel.
- **Fly-side**: `fly.toml` already declares a `/healthz` machine check every 30s (Fly restarts unhealthy
  machines). Metrics dashboard: https://fly-metrics.net (Grafana, free, per-app CPU/RAM/requests).
  Logs on demand: `gh workflow run fly-ops --repo aidonerightcorp/taedri -f command="logs --no-tail"`.
- **App-side receipts** (already on the volume): metering receipts (`/v1/usage`, `/v1/logs` per tenant),
  abuse events with IP digests only, contribution rows — all under `/data`.
- **Optional next tier**: UptimeRobot or BetterStack free external ping + public status page; Sentry for
  exception tracking. Not launch blockers — the healthcheck workflow plus Fly checks cover detection.

## 5a. Key-vault model and secret best practices (verified 2026-07-11)

Two write-only encrypted vaults + one local convenience layer — no separate vault product needed at this
scale:

| Layer | What it is | Properties (verified) |
|---|---|---|
| **Fly.io app secrets** (the RUNTIME vault) | `flyctl secrets set` on app `taedri` | Encrypted at rest by Fly; WRITE-ONLY (list shows names+digests, values are never readable back); injected as env at machine boot; every set creates a new release (auditable, versioned) |
| **GitHub Actions secrets** (the CI vault) | repo secrets on `aidonerightcorp/taedri` | Libsodium-sealed; write-only; auto-MASKED in every workflow log; only workflows on `main` can read them |
| **Local `.env`** (dev convenience) | monorepo root, plaintext | GITIGNORED and never tracked (verified); the weakest layer — hold only what local work needs |

Standing rules (all enforced in code or process, not prose): secret VALUES never in git — code carries env
NAMES only (credential-plane law); values never passed as workflow inputs (inputs are logged) — the
`sync-fly-secrets` workflow reads the masked secrets context instead; the gateway compares the owner key
with `hmac.compare_digest` (no timing leak), stores tenant keys as HASHES only, returns raw keys exactly
once at signup, and keeps raw IPs out of receipts (digests); payment/billing activation is COMPUTED from
secret presence (`/v1/billing/status`) so state can never be asserted falsely; the agent itself is
permission-gated on secret reads/rotations (a rotation requires the owner to name the secret).

Plan-gated gaps (facts, not misconfigurations — `aidonerightcorp` is a **User** account on the **free**
plan): branch protection on private repos needs GitHub Pro; secret scanning + push protection need
Advanced Security. Mitigations in place: private repo, single-owner account, deploys only from `main`,
healthcheck alerts on drift. **[owner]** two things only you can do: keep 2FA enabled on the
`aidonerightcorp` GitHub account, and if the current `FLY_API_TOKEN` is a broad personal token, replace it
with an app-scoped deploy token (`fly tokens create deploy -a taedri`) → update the GH secret → run
sync-fly-secrets. Rotation policy: rotate any key on suspicion or team change; Stripe keys rotate in the
Stripe dashboard then re-run §1 step 5; every rotation is one `gh secret set` + one workflow run.

## 5. Secrets and keys inventory (what lives where)

| Name | Where it lives | State |
|---|---|---|
| `TAEDRI_ADMIN_KEY` — the administrator password for the Taedri server (unlocks adding primitives + rebuilding the search index at `/v1/admin/*`) | Fly app secret (set 2026-07-10 under its legacy name `OH_SAAS_OWNER_KEY`, which the server still accepts) | DEPLOYED but the value is not recorded locally — owner must either paste it or authorize a rotation |
| `FLY_API_TOKEN` | GitHub repo secret on `aidonerightcorp/taedri` | WORKING (all deploys green) |
| `FLY_API_TOKEN` (local `.env` line) | monorepo `.env` | STALE — auth fails; refresh via `fly auth login` or `fly tokens create deploy -a taedri` if local flyctl is wanted (not required; workflows cover ops) |
| `STRIPE_API_KEY` / `STRIPE_PRICE_ID_PRO` / `STRIPE_WEBHOOK_SECRET` | owner → GitHub secrets → `sync-fly-secrets` | MISSING — section 1 |
| `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` | owner → monorepo `.env` | PLACEHOLDER — section 3 |
| GitHub CLI auth | `gh` (accounts `aidonerightcorp` active + `Amarel-Taylor-Scott`) | WORKING |

## 6. Copy-paste verification block (run after any activation step)

```bash
base=https://taedri.fly.dev            # swap to https://taedri.dev after the domain lands
curl -s $base/healthz
curl -s $base/v1/billing/status
curl -s $base/v1/stats/domains
curl -s $base/ | grep -c "This already exists"     # 2 = designed landing is serving
gh run list --repo aidonerightcorp/taedri --limit 3
```

Everything here operates on candidate-governed data (`serves_truth=false`); payments/domain/monitoring are
operational concerns and do not promote any row to truth.
