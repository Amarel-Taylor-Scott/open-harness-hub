# Design Bundle Review — full file-by-file (2026-06-09)

Source: `https://api.anthropic.com/v1/design/h/_8PmBC6pX8y6qEMwN7AzMQ` (2.7 MB gzip, 317 files).
Reviewed: every file — the productionization handoff (standards/contracts/cloud/business), the
nested `uploads/Designs/openharness/` design docs, and the reference-design consoles + clients.
**No zip files inside** (the bundle itself is the archive; raw copy archived at
`dist/handoff-archives/aidoneright-productionization-2026-06-09.tgz`). Three parallel reviewers
read the unreviewed remainder; this is the synthesis + what I implemented from it.

## What this bundle is

Two layers in one export: (1) the **AIDR Platform Productionization handoff** (Passes 1–12) — a
runnable scaffold + 9-phase backlog + S1–S13 standards + contracts + cloud ladder + economics +
pro-forma; and (2) the **`openharness/` design workspace** — the 24 prototype surfaces and their
product docs (positioning audit, UX backlog, experiments, marketing). The handoff README confirms
**our `scripts/identity_local_service.py` is canonical** — the bundle's Node `core/` is reference
for the events/LLM planes only.

## Standards extracted (S1–S13) — the binding rules

S1 tokens-only design · S2 Mode Protocol (live/simulated/unknown, never silently fake) · S3 API
`/api/<plane>/<realm>/<resource>` + `X-AIDR-Request-Id` + the 8-scope vocabulary · S4 testing
pyramid · S5 GitHub Actions orchestrates, logic in `just`, pull-based deploy · S6 signed
digest-pinned images · S7 monitoring/health shape · S8 secrets (raw-once, hash-only, unset→501) ·
S9 release flip (products.js status private→live) · S10 docs/proofs · S11 cloud graduation
(latency budgets, L0–L3) · S12 anti-fragility (vendors behind ports we own; no magic literals) ·
S13 business plane (events port, email port, ledger-only billing reconciles Stripe never vice
versa). **Assessment:** these match the repo's existing laws almost 1:1 (no-magic-values,
candidate≠active, lossless, dependency law). Adopt as the production-side articulation; no conflict.

## Economics & business (the CEO-relevant numbers)

- **LLM five lanes:** L-dev (Ollama local $0) · L-agent (Ollama Cloud flat $0/$20/$100) ·
  L-interactive (budget API ~$0.10–0.27/M) · **L-batch (Baltor verification rail = canonical batch
  workload, ~50% off — building this once halves the biggest predictable line)** · L-selfhost
  (vLLM, triple-gated: provider spend ≥2× all-in GPU for 3 months OR privacy mandate; the 3–5×
  ops-tax trap is real). Code uses model **classes**, not names.
- **Pro-forma:** Stage 0 ~$10–20/mo + usage; Stage 1 ~$15–50/mo (one Hetzner CPX22 €7.99); break-
  even = **1 paying customer**; the real risk line is founder time, not hosting. Pricing to
  validate: Baltor Team $99 / Growth $499; Teleon same; Enterprise self-host $2k+; hubs free funnel;
  LLM metered passthrough (receipts are the meter). 12-mo base case ≈ $1,700 MRR / 11–12 paying.

## Positioning audit findings (designers flagged)

DONE in the prototypes: category-bridge hero ("Context engineering picks it. Baltor governs it.");
"Hardening" over "Anti-Fragility" on buyer surfaces; "the governed context layer" as the category
noun. **STILL OPEN (and now actionable for our sites):** (3) add a true-by-construction metric to
the governance report ("N conflicts held out, 100% of served facts cited" — never "100% accurate");
(4) keep pages narrow — resist "enterprise knowledge" category creep; the moat is regulated-fact
depth. These align with my CEO review's "lead with the proof point" call.

## Experiments defined (my events plane is now ready for them)

`baltor_hero` (9 variants A–I, I locked) · `baltor_subhead` (A–E, E locked) · `baltor_cta` (A–D) ·
`teleon_hero` (A–D second line) · `<brand>_landing` (default vs trust-first, all 21) ·
`<brand>_subhead` (per hub) · `cmdk_select`. Sticky per-visitor (`localStorage('oh-exp')`),
forceable `?exp=key:Variant`, exposure auto-emitted. **The native events plane I built (Pass 13,
port 9420) implements exactly the EVENTS.md shape these emit** — wiring the beacon is the next step.

## UX backlog (designers' priorities)

SHIPPED in prototypes: portfolio switcher. **OPEN (highest reuse first):** P1 empty/loading/error
kit primitives (`OhEmpty/OhSkeleton/OhError`); P1 first-run onboarding checklist; P2 ⌘K palette;
P2 mobile-responsive app shells; P2 unify pricing into `OhPricing`. These are the design-fidelity
gaps between the prototypes and the wired `web/` apps (my G-10 in the codebase review: tokens not
yet rolled to `web/`).

## What I IMPLEMENTED from this bundle (this session, proof-backed)

1. **Landed + archived** the bundle losslessly; read every doc.
2. **Platform executes** (after operator authorized the allow rules): `docker compose up` →
   Caddy gateway :8080 + platform-core :8787 **up and serving**; core `/api/core/healthz` green
   THROUGH the gateway; LLM plane returns no-key-no-bypass honestly. Recorded:
   `artifacts/e2e/videos/gateway-journey.mp4`. (Identity-through-gateway needs host networking →
   G-12; core+sites proven.)
3. **Events/A-B plane, native** (`scripts/events_local_service.py`, EVENTS.md contract in Python —
   reference Node core stays reference): ingest + per-variant summary + PII guard + restart-safe;
   proof `check_local_events_plane`.
4. **`/service/*` handshake slice** (backlog 1.2, `contracts/SERVICE-CONNECTIONS.md`) implemented
   in the canonical identity service: env-keyed service accounts (`SERVICE_<REALM>_SECRET`, 503
   when unset — never faked), 8-scope vocabulary, directional verify, both-realm connection lists,
   revoke with receipts, asymmetric grants, no raw token on disk. **This makes the Service
   Connections dev console real** (it was SIMULATED). Proof `check_service_handshake_slice` (14/14).
5. PROOF_MODULES 425→428; watchdog cycled pid-exact each time.

## Gaps recorded (honest)

- **G-11** host classifier blocks agent-initiated downloaded-code execution — cleared for compose
  via the operator allow rules; binary fetches (`just`) still gated.
- **G-12** (new) identity-through-gateway needs host networking on the gateway container or an
  operator-authorized non-loopback bind (classifier correctly blocked 0.0.0.0 on a credential
  service); core+sites proven through the gateway meanwhile.
- Measured-lift still unpopulated (embeddings) — unchanged, still the #1 product gap.

## Next from this bundle (no new permission needed)

Wire the `oh-experiments` beacon → the 9420 events plane (backlog 2.1) → A/B readout; align
`oh-identity.js` ENDPOINTS to our routes (1.1); ledger-only billing over receipts (3.1); the
empty/loading/error kit primitives (UX P1). Each one proof-gated, each recorded on video.
