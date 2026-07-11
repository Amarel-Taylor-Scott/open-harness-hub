# AIDR Standards — the production handbook (v1, Pass 4)

The frameworks, policies and standardizations the whole portfolio adopts — design →
wiring → testing → CI/CD → distribution → monitoring. Each standard states the RULE,
the CONTRACT (what code must do), the PROOF (the check that enforces it), and STATUS
(✓ adopted · ◐ partial · ○ proposed). Honest by construction: nothing is "done" without
its proof named.

Conventions used by every standard:
- **Realm** = one product/hub (parent, baltor, teleon, 9 live hubs). No cross-realm anything.
- **Plane** = a shared backend capability (identity, events, llm, receipts).
- Paths: `/api/<plane>/<realm>/…`. Correlation: `X-AIDR-Request-Id` on every call.

---

## S1 · Design system (branded house)
**Rule.** One scale/type/primitive set for all 24 surfaces; only `--accent` differs.
**Contract.** Color/size only from `shared/oh-tokens.css`; every card = `.oh-card`
physics; new sites build on `oh-site.jsx` / `makeHub()`; brand text lives only in
`products.js`. Zero horizontal overflow, light+dark clean, console clean.
**Proof.** `Design Acceptance Scorecard.html` (family gate, 94%) + per-surface checks:
no hardcoded hex lint (`grep -rE '#[0-9a-f]{3,8}' --include='*.css' sites/ | grep -v tokens`),
scrollWidth === innerWidth probe, console-error probe.
**Status.** ✓ adopted (the strongest layer in the house).

## S2 · Mode Protocol (simulated vs real actions)
**Rule.** Every client that talks to a backend has exactly three modes — `live`
(backend answered), `simulated` (clearly-flagged in-tab stand-in, same contract,
nothing persists), `unknown` (probing) — and may NEVER silently fake a real action.
**Contract.** `client.probe()` sets mode; 404/unreachable → `simulated`; every response
record carries `simulated: true|false`; UIs show a mode pill + amber SIMULATED banner
with the real command to start the backend; raw secrets are never minted silently in
live mode. Reference implementations: `shared/oh-identity.js`, `shared/oh-service-auth.js`.
**Proof.** Contract test per client: kill backend → mode flips + banner renders + records
flagged; with backend → no `sim` flags.
**Status.** ✓ adopted (identity, service-auth) · extend to events/LLM clients next.

## S3 · API & auth conventions
**Rule.** One vocabulary for all planes.
**Contract.**
- Paths `/api/<plane>/<realm>/<resource>`; JSON in/out; errors are `{ "error": "…" }` + correct HTTP status.
- `X-AIDR-Request-Id` accepted on every route, echoed into the audit log.
- Secrets: raw shown EXACTLY once at mint; hash-only storage; revoke + re-mint to rotate.
- Service tier: `SERVICE_<ID>_SECRET` env per realm; handshakes are one-directional
  `from → to` with explicit scopes from the shared scope vocabulary
  (`llm:invoke events:write registry:read registry:publish serve:cited verify:run state:read state:write`).
- No SSO; cross-realm requests are rejected, not proxied.
**Proof.** The user's proof modules (`check_identity_local_service_runtime` 27/27 pattern)
+ ENDPOINTS-map contract tests (the maps in `shared/oh-*.js` are the single alignment point).
**Status.** ✓ adopted for identity · ◐ service tier (contract proposed, backend Phase-1 remaining).

## S4 · Testing pyramid
**Rule.** Every increment ships with its proof; no green claim without a named check.
**Contract.**
1. **Proof modules** (backend): pure-python `check_*.py` per service, registered centrally — the user's existing pattern stays canonical.
2. **Contract tests** (seam): for each ENDPOINTS map, a test that the live service and the simulated stand-in return the same shapes.
3. **Surface smokes** (frontend): Playwright per surface — the golden path (register → onboard → portal → mint key → revoke → logout), plus the three structural probes from S1 (overflow / console / tokens).
4. **Held-out checks**: governance surfaces must prove the negative too (cross-realm rejected, revoked key fails, stale value held out).
**Proof.** CI stage `test` runs 1–4; a pass is the list of named checks + counts (e.g. "27/27"), never "tests pass".
**Status.** ◐ — proof modules adopted (backend); Playwright smokes proposed (`production/ci/` has the pipeline slot).

## S5 · CI/CD pipeline
**Rule.** One pipeline shape for every deployable; deploy is one click/command from green.
**DECISION (Pass 5, reviewed vs GitLab CI / Buildkite / CircleCI / Jenkins / TeamCity /
Woodpecker / Dagger / Argo-Tekton — see `CICD Options Review — S5 Decision.html`):
GitHub Actions is the orchestrator** — repo already on GitHub, native OIDC for keyless
cosign, zero ops burden. Reversible by design via S5a.
**S5a · Pipeline Contract.** Workflow YAML may ONLY orchestrate; every step body is a
`just` recipe (justfile in repo root: `just lint|test|build|package|smoke`) that runs
identically on the local machine. Local run = CI run; swapping orchestrators = ~60
lines of glue. Agents call stages directly.
**S5b · Pull-based deploy.** CI never reaches into the host (no SSH from CI, no
self-hosted runner on a public repo). The host pulls: systemd timer runs
`just deploy-pull` → fetch signed images → `cosign verify` → `compose up -d` → post a
deploy receipt to the events plane. CI's deploy job only tags the release.
**Hardening.** Third-party actions pinned by commit SHA (Dependabot refreshes);
`permissions: {}` default-deny, per-job grants; OIDC keyless only; concurrency groups;
path filters; caching; required checks = the standards gate; flaky tests quarantined
in a day, fixed or deleted in a week.
**Contract.** Stages (see `production/ci/github-actions.yaml` — refactor to thin
orchestration on next touch):
`lint` (tokens lint, py_compile, gitleaks) → `test` (S4 pyramid) → `build` (precompiled
JSX via Vite) → `package` (containers, digest-pinned bases, CycloneDX SBOM, cosign) →
`deploy` (tag; host pulls per S5b) → `smoke` (every `/health` through the tunnel).
Conventional commits; semver per service; changelog from commits.
**Proof.** The workflow file + required-checks branch rule + a justfile↔workflow drift
check (every workflow step body is `just <stage>`).
**Status.** ◐ — decision taken + contract written; ○ until the pipeline runs green in the real repo.

## S6 · Distribution (the container thesis)
**Rule.** Discovery is not trust — applied to our own artifacts.
**Contract.** Every published image: digest-pinned pulls in all docs (`image@sha256:…`),
SBOM (CycloneDX) + cosign signature + provenance attestation published alongside; hub
release pages reuse the registry entry's provenance panel (one design, both uses).
`status:'private'` enforced server-side, not just a hidden banner.
**Proof.** `cosign verify` + SBOM presence as a `package`-stage gate; a check that no
doc contains an unpinned `docker pull`.
**Status.** ○ proposed (contract written; first signed image is the adoption moment).

## S7 · Monitoring & observability
**Rule.** Every service self-reports; the Control Tower aggregates; no silent failures.
**Contract.**
- `/health` per service returns `{ ok, service, at, … }` (platform-core shape).
- Audit JSONL per service with request-id correlation (identity service pattern) — append-only, greppable.
- Events plane (`/api/events`) is the single sink for product analytics + A/B exposures/conversions (shape in `production/contracts/EVENTS.md`); PII never enters events (anon ids only).
- Control Tower's health check reads every `/health` + tunnel URL and shows version/digest per deployment (Deployments lane, queued).
- `OhStatus` pages render from real `/health` aggregation, not fixtures, once wired.
**Proof.** A `smoke` CI stage curling every `/health`; an events round-trip test (emit → summary count increments).
**Status.** ◐ — health + audit adopted on identity; events sink shipped (platform-core) but unwired; Tower lane queued.

## S8 · Secrets & security policy
**Rule.** No fake secrets, no bypasses, least privilege everywhere.
**Contract.** `.env` never committed (`.env.example` only, no working defaults);
`SERVICE_<ID>_SECRET` per realm; scopes minimal by default (`llm:invoke` alone);
password hashing scrypt/argon2 (blake2b refs are dev-only — flagged, not production
crypto); provider keys (Anthropic/OpenAI) only via env; an unset key = 501 with
instructions, never a stub response.
**Proof.** Secret-scan in `lint` stage (gitleaks); the 501 behavior covered by contract tests.
**Status.** ✓ adopted as policy · argon2/OAuth/SSO adapters remain owner-gated (their call).

## S9 · Releases, versioning, flip-to-public
**Rule.** Opening a surface to the public stays a one-line event, end to end.
**Contract.** `products.js` `status:'private'→'live'` flips branding + banner (shipped);
the same flip in `terraform/main.tf`'s surfaces map creates DNS + tunnel ingress; the
same key gains a `SERVICE_<ID>_SECRET`. One key, three layers, one diff.
**Proof.** A drift check that the three maps (products.js / terraform surfaces / service
secrets) agree — the user's registry-drift-gate pattern, extended.
**Status.** ◐ — design layer shipped; terraform map mirrors it; drift check proposed.

## S10 · Documentation & honesty policy
**Rule.** Every folder has a README; every pass updates the gap ledger; claims name
their proof or say "not run here".
**Contract.** Pass log + gap ledger in `production/README.md` (G-numbers are stable
ids); "SIMULATED", "CONTRACT PROPOSAL", "skeleton — never applied" labels are part of
the deliverable, not shame; design workspace authors runnable files and never claims
execution (G-8).
**Proof.** This file's status fields; a doc check that each `production/` subfolder has a README.
**Status.** ✓ adopted.

---

## S11 · Cloud graduation & economics (monitoring · latency · cost)
**Rule.** The platform stays modular and portable: everything that runs is a container
(or a declared host service) behind the same gateway namespace, so moving local → cloud
changes WHERE containers run, never HOW services talk. Latency and cost are budgets in
the manifest, not vibes.
**Contract.**
- **Latency budgets** live in `services.json` (`latency_p95_ms` per service); measured
  through the gateway by `scripts/latency_probe.py` (`just bench`, receipts to
  `dist/bench-receipts.jsonl`, exit 1 on breach — CI-usable). LLM provider time is
  excluded: we budget OUR overhead only.
- **Monitoring ladder** (adopt in order, never skip to the heavy end): 1) `/health` per
  service + deploy-verify (shipped) → 2) uptime-kuma container watching every route +
  the tunnel URL (one compose entry) → 3) Prometheus+Grafana only when >1 host or >10
  containers. Every rung keeps the events plane as the product-analytics sink (S7).
- **Cost measures**: every cloud candidate gets a monthly ceiling BEFORE adoption;
  deploy receipts record image sizes; the LLM plane records usage per key (receipt per
  invocation) so model spend is attributable from day one. No resource without an owner
  and a ceiling.
- **Graduation path** (each step reversible, same compose file):
  L0 laptop + quick tunnel (now) → L1 named tunnel (terraform/, stable URLs, still
  laptop) → L2 one small VM (Hetzner/DO, ~$5–15/mo ceiling) running the SAME
  `just up`, host pulls per S5b → L3 split planes onto managed services only when a
  measured budget (latency, uptime, or cost) is breached — never speculatively.
- **Portability gates**: no service may depend on a cloud-only primitive without a
  documented local equivalent (the dev/prod parity rule); secrets stay env-injected
  (vault seam, S8); state stays in declared volumes so any host can be rebuilt from
  repo + vault + volume snapshot.
**Proof.** `just bench` green against budgets · uptime-kuma showing 24h uptime on all
routes · a cost table in `production/cloud/GRADUATION.md` with ceilings + actuals once
on L2.
**Status.** ◐ — budgets + probe + receipts shipped; monitoring rung 2 queued; L1/L2 not
executed (G-5).

---

## S12 · Anti-fragility & abstraction (ports, naming, no magic values)
**Rule.** The platform must survive any single vendor, host, orchestrator, or schema
decision being reversed. Fragility from infrastructure, naming, or hidden constants is
a defect class, not a style issue.
**Contract.**
- **Ports & adapters.** Every external dependency (email, payments, analytics sink,
  LLM provider, DB, host/orchestrator) sits behind a port module we own; vendors are
  adapter files. Code outside an adapter never names a vendor — `email.send()`, not
  `resend.send()`. Which adapter is live is config (env/manifest), not code.
- **No magic words or numbers.** Every meaningful literal lives in exactly one named
  place: `services.json` (ports, routes, budgets), the scope vocabulary (S3), realm
  ids (`products.js`), plan/price config (BUSINESS-PLANE.md), named constants modules.
  The review question "where is this value defined?" must always have a one-place answer.
  Proof tool: a lint that flags bare numeric literals outside constants/config (allow
  0/1/-1 and indices).
- **Naming.** Stable internal ids (realm, plane, service id) are the only names that
  cross seams; vendor and product-marketing names never appear in identifiers, paths,
  or schemas. Renaming a brand = `products.js` + docs, zero code.
- **Flexible schemas without lock-in.** Relational spine + JSONB `props` for the open
  part; every record carries `schema_version`; events/receipts append-only; migrations
  forward-only. (Full data-layer decisions: `cloud/PLATFORM-REVIEW.md`.)
- **K8s/function readiness without adoption.** 12-factor discipline (env-only config,
  stateless containers, stdout logs, declared volumes); `services.json` is the
  portable topology from which compose now — and Helm/K8s manifests later — are
  GENERATED; HTTP handlers stay framework-thin so any plane can repackage as a cloud
  function. Adopt K8s only managed and only at the S11 rung-3 trigger.
**Proof.** Adapter-swap test (switch email adapter via env, flows unchanged) ·
magic-literal lint in `just lint` · gen-from-manifest drift checks.
**Status.** ◐ — manifest/env/scope layers comply; magic-literal lint and the first
real port (email) are queued.

## S13 · Business plane (analytics · email · payments · PMF)
**Rule.** Product-side services are planes with ports like everything else; growth
claims need instrumentation the same way deploys need receipts.
**Contract.** `contracts/BUSINESS-PLANE.md`: events plane is the analytics port
(PostHog/BigQuery are sinks); transactional email behind `email.send()` with a
console adapter in dev (Mode Protocol applies — no silent sends); billing fed by the
receipts we already emit, with a ledger-only adapter running forever in parallel to
reconcile any processor (receipts audit Stripe, not vice versa). PMF funnel per realm:
discover → engage → signup → **activate** (Baltor: first verified pack served ·
Teleon: first capability proven · hub: first pull/publish) → retain → revenue; each
stage is ONE named event.
**Proof.** Funnel chart from real events for one realm · ledger statement matching
receipt sums · adapter-swap test.
**Status.** ○ proposed — adoption order 1–5 in BUSINESS-PLANE.md.

---

## Adoption queue (ordered)
1. **S4.3 Playwright smokes** for the two shipped consoles (identity wiring, service connections) — they define the golden paths already.
2. **S2 extension** — events + LLM clients get the Mode Protocol (one shared `oh-plane-client.js` base would remove the copy between oh-identity/oh-service-auth).
3. **S5** — land `production/ci/github-actions.yaml` in the real repo; wire `lint`+`test` first, `package` signing when the first container builds.
4. **S9 drift check** — products.js ⇄ terraform ⇄ service-secrets agreement.
5. **S7 Tower Deployments lane** — the visible face of monitoring.
