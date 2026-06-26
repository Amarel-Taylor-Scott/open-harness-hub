# Claude Code Backlog — the long-running task list (Pass 12)

The ordered work queue for hours/days of unattended passes. Use with the OPERATING
LOOP in START-HERE-CLAUDE-CODE.md (orient→build→prove→record→repeat; never idle,
never ask, never overclaim). Each task: WHAT · PROOF · the working prompt. Mark tasks
done in this file with the pass number and proof reference; add discovered tasks to
the right phase rather than doing them ad hoc.

Rules that bind every task: Mode Protocol S2 · API conventions S3 · tokens-only design
S1 · no magic values S12 · every claim names its proof S10. The identity service
(`scripts/identity_local_service.py`) is canonical; production/core is reference-only
for events/LLM planes.

---

## Phase 0 — Make it run (clears G-9)
- [ ] **0.1 Execute the platform.** `cd production && just plan` (read-only) → fix what it reveals → `just up` → `just tunnel`.
      PROOF: deploy receipt in dist/ + every /health green through the gateway + a trycloudflare URL serving a hub page.
      PROMPT: "Run just plan in production/. Fix path/env assumptions it reveals (SITE_ROOT, ports) by editing services.json/.env — not the scripts — unless the scripts are wrong, then fix and note it. Then just up, just tunnel. Record receipt id + health table in the pass log."
- [ ] **0.2 Bench baseline.** `just bench`; tune or re-budget `latency_p95_ms` with recorded reasons.
      PROOF: bench receipt; budgets green or amended.
- [ ] **0.3 Vault adoption.** `just vault-init/edit/export`; secrets out of plain .env.
      PROOF: .env generated from vault; gitleaks clean.

## Phase 1 — Identity completion
- [ ] **1.1 Align oh-identity ENDPOINTS** with the real routes; run the Identity Wiring console LIVE end-to-end per realm.
      PROOF: golden path (register→onboard→login→validate→mint→list→revoke→logout) with zero `sim` flags; cross-realm rejected.
- [ ] **1.2 Implement /service/* slice** in the identity service per contracts/SERVICE-CONNECTIONS.md (or amend the map to your shape).
      PROOF: Service Connections console flips LIVE; handshake→verify→revoke round-trip; audit JSONL shows request ids.
- [ ] **1.3 Promote auth into the kit.** OhAuth/OhApiKeys pages call oh-identity.js instead of mock state, all realms.
      PROOF: register on Baltor through the tunnel in a clean browser; key visible in audit log.
- [ ] **1.4 Email port, console adapter.** `email.send()` wired into register/reset; renders to audit log; never silently sends (S2).
      PROOF: rendered emails in audit log with request ids.

## Phase 2 — Events & A/B end-to-end
- [ ] **2.1 Beacon.** oh-experiments.js sendBeacon → /api/events (graceful no-op when down).
      PROOF: exposure/conversion counts in /api/events/summary from a real browse session.
- [ ] **2.2 PMF events.** Wire the six funnel events (BUSINESS-PLANE.md) incl. activation per product.
      PROOF: discover→activate visible for one realm in summary.
- [ ] **2.3 A/B readout.** conversion/exposure per variant view (extend summary or small page).
      PROOF: a real experiment readout from browsed data.
- [ ] **2.4 PostHog sink (env-gated).** Events plane forwards when POSTHOG_KEY set.
      PROOF: funnel chart in PostHog; zero behavior change unset.

## Phase 3 — Business plane
- [ ] **3.1 Ledger-only billing.** Statement per key/realm from LLM receipts: "what this month would cost."
      PROOF: statement sums match receipt sums.
- [ ] **3.2 Resend adapter** (vault-keyed) behind email port.
      PROOF: one real verification email round-trip; SPF/DKIM/DMARC set first.
- [ ] **3.3 Stripe test mode.** Metered usage from ledger; webhooks → events plane.
      PROOF: draft invoice matches ledger; receipts reconcile Stripe, never vice versa.

## Phase 4 — LLM economics (cloud/LLM-ECONOMICS.md)
- [ ] **4.1 Model-class routing.** `class: budget|frontier|batch|local → model` config in the plane; class in every receipt.
- [ ] **4.2 Batch lane.** Queue + batch-endpoint submission for verification-rail jobs.
      PROOF: one batch round-trip at ~half rate.
- [ ] **4.3 Ollama adapter** (local; Cloud optional) for dev/agent lanes.
      PROOF: completion served via Ollama, callers unchanged, receipt emitted.
- [ ] **4.4 Spend dashboard.** $/realm/class/week from receipts vs PRO-FORMA.
- [ ] **4.5 Quotas (G-4).** Per-key rate limits + streaming on the plane.
      PROOF: 429 on breach covered by a contract test; streamed completion through a user key.

## Phase 5 — First real registry (G-2)
- [ ] **5.1 OpenContextHub CRUD + search** (store + Meilisearch or SQLite FTS to start) behind the hub UI.
      PROOF: publish→browse→pull round-trip locally.
- [ ] **5.2 Entries signed** by the receipts plane; provenance panel renders real data.
- [ ] **5.3 Deploy strip (I-1).** Digest-pinned pull command + parity card on the hub.

## Phase 6 — CI & supply chain
- [ ] **6.1 Land the workflow** refactored to thin `just` calls (S5a); lint+test first.
      PROOF: green run in the repo; required checks on.
- [ ] **6.2 Playwright smokes** for the two consoles + S1 structural probes (overflow/console/tokens).
- [ ] **6.3 Magic-literal lint** in `just lint` (S12; allow 0/1/-1, indices).
      PROOF: named findings then zero.
- [ ] **6.4 First signed image.** core: SBOM (syft) + cosign keyless; deploy refuses unsigned (S6).
- [ ] **6.5 S9 drift check.** products.js ⇄ services.json/terraform ⇄ SERVICE_*_SECRET as a check_* module.

## Phase 7 — Monitoring & graduation
- [ ] **7.1 uptime-kuma** in the manifest watching every route + tunnel URL.
      PROOF: induced outage alerts <60s.
- [ ] **7.2 L1 named tunnel.** Apply terraform (Cloudflare): stable hostnames; quick tunnel stays the fallback.
      PROOF: terraform output + stable URL serving.
- [ ] **7.3 Deploy receipts → events plane** (deploy.py posts after verify).
- [ ] **7.4 Weekly report generator.** bench + funnel + spend in one artifact (OPERATIONS.md cadence).

## Phase 8 — Product surface (design queue, after the rails work)
- [ ] **8.1 B-1 Baltor Live Run Console** — Contextual-grade run UX (pipeline, trajectory, artifacts, report) over the existing 20-scenario library, on real events.
- [ ] **8.2 Onboarding/empty/error states** (UX-BACKLOG P1) on the wired pages.
- [ ] **8.3 First hub flip rehearsal** — one private→live flip through all three layers (products.js / manifest / secret), as a launch dry-run.

---
**Discovered-task protocol:** found work goes into the matching phase with a proof
defined BEFORE building. **Stuck protocol:** 3 different attempts → record gap →
next task in the same phase → return next pass.
