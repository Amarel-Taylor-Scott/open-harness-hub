# START HERE — Claude Code Handoff (AIDoneRight productionization)

This workspace authored the productionization layer for the **AI Done Right** portfolio.
Your job is to make it run, wire the prototypes to the real backend, and keep shipping
one proof-backed increment per pass. The design prototypes (24 surfaces) live in the
design repo (`uploads/Designs/openharness/` here; your local checkout on the host); the
canonical identity backend is **already yours**: `scripts/identity_local_service.py`
(12 separate realms, port 9410, register→onboard→login→logout→session, hash-only keys,
audit JSONL with `X-AIDR-Request-Id`).

---

## 1. Paste this into Claude Code to begin

```
You are continuing the AI Done Right productionization loop.

/goal Continuously productionize the AI Done Right portfolio (parent + Baltor + Teleon
+ Open*Hubs) into a locally working, TryCloudflare-accessible, end-to-end platform:
auth, registration, portals, A/B tests, analytics/events, API keys, service accounts,
MCP/tool connections, Shared LLM Plane, service-consumption contracts, containerized
deployability, Terraform/OpenTofu-ready infra. Preserve product boundaries (12 realms,
NO SSO, cross-realm rejected). ONE proof-backed increment per pass; every increment
names its proof (check counts, not "tests pass"). Best judgment on implementation/copy/
positioning. Document gaps honestly in the G-ledger. No fake URLs, secrets, provider
bypasses, or overclaims.

Read in this order before writing code:
  1. production/README.md                  — run instructions, gap ledger G-1…G-10, pass log
  2. production/standards/STANDARDS.md     — S1–S10 binding standards (S5a: ALL pipeline
                                             logic lives in justfile recipes; S5b: pull-based
                                             deploy, CI never reaches into the host)
  3. production/services.json              — THE manifest: services, kinds, routes, health.
                                             Router (gen_caddy.py), deployer (deploy.py) and
                                             tunnel all read it. Add a service = one entry.
  4. production/justfile                   — the one-click interface; run `just plan` first
  5. production/contracts/SERVICE-CONNECTIONS.md + EVENTS.md — identity tiers, handshake,
                                             scopes, event shape
  6. shared/oh-identity.js                 — realm-aware auth/keys client; ENDPOINTS map is
                                             the single path-alignment point with your
                                             identity_local_service.py routes
  7. shared/oh-service-auth.js             — service↔service dev tokens: a PROPOSED contract
                                             (/api/identity/<realm>/service/handshake|
                                             connections|revoke|verify) — implement this
                                             slice in the identity service, or amend the map
  8. The two console prototypes (Identity Wiring, Service Connections) — the golden-path
                                             UIs; they auto-detect live vs simulated backend
  9. production/ci/github-actions.yaml     — refactor to thin orchestration (bodies = just <stage>)
 10. production/vault/README.md            — SOPS+age flow; OpenBao is the graduation path
 11. production/CLAUDE-CODE-BACKLOG.md     — THE LONG-RUNNING TASK LIST: phases 0–8, every
                                             task with its proof and prompt. Work it top-down;
                                             mark done with pass number; discovered tasks go
                                             into phases, never ad hoc.
 12. production/cloud/LLM-ECONOMICS.md     — inference spend policy: five lanes (dev/agent/
                                             interactive/batch/self-host), model CLASSES not
                                             names in code, batch lane for Baltor's verification
                                             rail, self-host only on receipt-proven triggers
                                             (the 3–5× ops-tax trap is documented — respect it)

Hard constraints:
  - Mode Protocol (S2): clients are live/simulated/unknown; a real action is NEVER
    silently faked; simulated is flagged in every record + a visible banner.
  - API conventions (S3): /api/<plane>/<realm>/…; X-AIDR-Request-Id everywhere; raw
    secrets shown exactly once, hash-only storage; SERVICE_<ID>_SECRET per realm.
  - Design (S1): tokens only, .oh-card physics, one accent per brand, zero overflow.
  - production/core (Node) is a REFERENCE for the events/LLM planes — identity stays in
    your Python service. Do not duplicate identity in Node.

Ordered next targets — work production/CLAUDE-CODE-BACKLOG.md top-down (Phase 0 first,
one proof-backed task per pass). Quick map of the first items:
  1. Execute the platform: `just plan` → `just up` → `just tunnel` on the host (clears
     G-9). Proof: deploy receipt + every /health green through the gateway.
  2. Implement the /service/* slice in identity_local_service.py per the proposed
     contract (or amend shared/oh-service-auth.js ENDPOINTS to your shape). Proof: the
     Service Connections console flips from SIMULATED to live; handshake→verify→revoke
     round-trips; receipts in the audit JSONL.
  3. Promote the Identity Wiring flow into the real site shells (OhAuth pages call
     oh-identity.js instead of mock state). Proof: register on Baltor through the
     tunnel URL in a clean browser; session + key visible in the audit log.
  4. Events plane: point OHExp dataLayer beacon at /api/events (graceful no-op when
     down). Proof: A/B exposure/conversion counts in /api/events/summary from a real
     browse session.
  5. LLM plane hardening: streaming + per-key quotas in production/core (G-4). Proof:
     a streamed completion through a user key, receipt per invocation, 501-no-bypass
     behavior covered by a contract test.
  6. S9 drift check: products.js ⇄ services.json/terraform ⇄ SERVICE_<ID>_SECRET
     agreement. Proof: a check_* module, registered, with counts.
  7. Monitoring rung 2: uptime-kuma container in the manifest watching every route +
     tunnel URL. Proof: 24h uptime view; an induced outage alerts within 60s.
  8. Latency baseline: `just bench` green against services.json budgets; tune or
     re-budget with a recorded reason. Proof: bench receipt in dist/.
  9. S12 magic-literal lint in `just lint` (bare numerics/strings outside config/
     constants; allow 0/1/-1). Proof: lint run with named findings, then zero.
 10. Business plane order 1–5 (contracts/BUSINESS-PLANE.md): ledger-only billing
     statement over LLM receipts → email port w/ console adapter → PostHog sink →
     Resend adapter → Stripe test mode. One per pass, each with its proof.

Ask the operator nothing; decide, ship, and record each pass in the ledger.

OPERATING LOOP — you are expected to run for HOURS, unattended:
  ORIENT   `just status` + read the pass log + G-ledger → pick the smallest unproven
           target (the ordered list above, or the most-blocking gap).
  BUILD    the smallest increment that could prove something real.
  PROVE    run the named check; through-the-gateway, never just unit-level. A proof is
           counts and receipts, not "looks good".
  RECORD   append to the pass log; update the G-ledger; commit with a conventional
           message. Unproven work is recorded as unproven — that's still progress.
  REPEAT   immediately. Do not stop to summarize, do not ask permission, do not wait.

SELF-TROUBLESHOOTING PLAYBOOK (exhaust this before abandoning ANY target):
  - Command fails → read the actual error; fix; retry. Three DIFFERENT approaches
    before you may switch targets — and switching means picking the next target and
    returning to this one next pass, never idling.
  - Missing tool → install it (brew/apt/pipx/npm — you have the machine); if install
    is impossible, write the stdlib fallback. "Not installed" is never a stopping state.
  - Port in use / stale state → `just down`; delete `.deploy-state.json`; `just up`.
  - Tunnel died → quick tunnels are ephemeral BY DESIGN; `just tunnel` again; graduate
    to L1 (named tunnel, terraform/) when churn costs more than setup.
  - Frontend↔backend path mismatch → fix the ENDPOINTS map in shared/oh-*.js (the one
    seam), never fork the UI.
  - A check fails the same way 3× → write a smaller probe to isolate the layer
    (curl the route directly, bypass the gateway, hit the service on its port), find
    which seam lies, fix THAT.
  - Something works → harden it (add its check to `just test`); nothing works → shrink
    the increment until something does.
  - NEVER: weaken an honesty rule to go green, fake a provider, delete realm data,
    or report unexecuted work as executed. A documented failure is a valid pass result;
    silence and overclaims are not.

AFTER LOCAL IS GREEN — the cloud path (S11, production/cloud/GRADUATION.md):
  Stay modular: every plane a container behind the same gateway namespace; moving to
  cloud changes WHERE containers run, never HOW services talk. Ladder: L0 laptop+quick
  tunnel → L1 named tunnel/DNS → L2 one $15-ceiling VM running the SAME `just up`
  (host pulls signed images, S5b) → L3 split planes ONLY on a measured breach.
  Monitoring ladder: /health+bench (shipped) → uptime-kuma container → Prom/Grafana
  only past 1 host. Latency budgets live in services.json; `just bench` enforces them
  with receipts. Cost: every level has a ceiling; LLM spend is attributable per key
  via invocation receipts. Never skip a level; never move speculatively.
```

---

## 2. What exists vs what's claimed (honesty table)

| Layer | Status | Proof available |
|---|---|---|
| Identity backend (12 realms) | RUNNING on your host | your check modules (27/27 etc.) |
| Identity/service-auth browser clients + consoles | BUILT, render clean, simulated mode exercised | this workspace's verifier passes |
| platform-core (events/LLM/receipts/handshake reference) | WRITTEN, never executed | smoke-test commands in production/README.md |
| justfile · deploy.py · gen_caddy.py · services.json | WRITTEN, never executed (G-9) | `just plan` is read-only — run it first |
| Latency budgets + probe (`just bench`) · cloud ladder L0–L3 | WRITTEN (S11); budgets are first guesses — re-budget with reasons | scripts/latency_probe.py · production/cloud/GRADUATION.md |
| Standards S1–S10, contracts, CI workflow | ADOPTED on paper; CI never ran | STANDARDS.md status fields per standard |
| Terraform | SKELETON, never applied (G-5) | file header says so |
| Vault (SOPS+age) | DECIDED + recipes written; needs sops+age installed (G-10) | vault/README.md |

## 3. Boundaries that must survive you
- 12 realms stay separate; no SSO, no cross-realm sessions, no shared accounts.
- Private-bench hubs stay excluded from realm registry until flipped (one line, three
  layers: products.js / services map / SERVICE_<ID>_SECRET — keep them in sync, S9).
- The design system is law (S1): never hardcode color/scale; prototypes are the spec.
- Raw credentials: shown once, hash-only, revoke+re-mint to rotate — everywhere.
- Every pass appends to the pass log and updates the G-ledger. Unsigned/unexecuted/
  simulated things say so in the artifact itself.
- The loop does not stop. A blocked target gets a documented gap and a successor
  target — the only invalid states are idling, asking, and overclaiming.
