# User-journey videos — the three wired full-design apps

Generated 2026-06-10T18:04:22.461Z by `e2e/record_user_journeys.mjs` (re-run anytime; services up via
`python3 scripts/start_local_services.py`). Files land in `artifacts/e2e/videos/` (webm + mp4,
1280×800; mp4 rendered by the repo's static ffmpeg). This manifest is GENERATED from
`artifacts/e2e/reports/user-journeys.json` — regenerate, don't hand-edit.

Every journey is narrated by an on-screen HUD and follows the honesty rules: REAL seams are
exercised for real (per-realm sign-up, /api/build, the live event bus, API-key mint/revoke);
designed simulations are captioned as such (sample tiers, emulated billing).

## Open Harness Hub — landing → browse → sign-up → live build → configuration

`artifacts/e2e/videos/journey-1-openharnesshub.mp4` · 123s · 23 chapters

| t | chapter |
|---|---|
| 5s | Open Harness Hub — landing on the homepage |
| 11s | Describing a task — the backend assembles a governed pipeline for it |
| 14s | Build → the REAL /api/build endpoint assembles the flow |
| 21s | The preview shows the REAL assembled flow — live components, stages, and cost (no made-up lift numbers) |
| 30s | Browsing the catalog — components, knowledge corpora, governed pipelines |
| 35s | Opening a component — lift, provenance, license, lifecycle |
| 44s | Comparing pipelines side by side |
| 51s | SDG solution tracks |
| 53s | Case studies |
| 56s | Pricing — the spec and exports are free; sign up to run flows |
| 63s | Creating a REAL account — the per-realm identity service (no SSO, no fake sessions) |
| 66s | Sign up — the identity service registers, onboards, and mints a session |
| 74s | Signed in — the workspace, now in app mode (real session detected) |
| 80s | Product use — confirming the parsed task and constraints |
| 83s | Assemble — the live backend builds while the console animates |
| 88s | Three costed tier options (designed sample tiers) |
| 90s | The interactive flow canvas — nodes, gates, and the model boundary |
| 94s | Run console (designed simulation of a run) |
| 104s | Foundry console — distillation & verification tooling |
| 106s | Governance — provenance, signing, review gates |
| 109s | Configuration — workspace settings |
| 118s | Dark mode — the same surface on dark tokens |
| 123s | Open Harness Hub journey complete — landing → browse → real sign-up → live build → configuration |

## Baltor — landing → browse → sign-up → emulated billing → console → LIVE pipeline

`artifacts/e2e/videos/journey-2-baltor.mp4` · 145s · 26 chapters

| t | chapter |
|---|---|
| 5s | Baltor — landing on the homepage (context assurance) |
| 15s | Why context — the thesis |
| 22s | The Context Engine — six governed stages with a verification rail |
| 33s | Case studies |
| 34s | Opening a case study |
| 39s | Docs — integration surface |
| 41s | Pricing — plans before sign-up |
| 48s | Creating a REAL Baltor account (its own identity realm — separate from OHH, no SSO) |
| 52s | Sign up — real register → onboarding → session |
| 60s | The console — corpora, freshness, serving health |
| 67s | Sources — what feeds the corpus |
| 70s | Connecting a source |
| 73s | Governed corpora — raw, compressed, hyper-efficient tiers |
| 74s | Opening a corpus — tiers, freshness, citations |
| 83s | Serving context packages to agents |
| 86s | Verification — every claim checked against live sources |
| 89s | Governance — provenance and policy |
| 92s | The audit log — every serve and reconciliation |
| 95s | Billing — plan, invoices, payment (EMULATED — no real charges) |
| 100s | Managing the plan (emulated checkout) |
| 104s | Configuration — workspace settings |
| 107s | Usage metering |
| 111s | A guided demo — CFPB regulatory context, end to end |
| 124s | Live ops — the REAL event bus behind the product |
| 125s | Run Full Pipeline — a REAL pipeline run, streaming real events |
| 145s | Baltor journey complete — landing → browse → real sign-up → emulated billing → console → live pipeline |

## AI Done Right → Control Tower → OpenContextHub — real account + REAL key mint

`artifacts/e2e/videos/journey-3-portfolio-hub.mp4` · 87s · 22 chapters

| t | chapter |
|---|---|
| 5s | AI Done Right — the parent portfolio |
| 6s | Thesis |
| 8s | Architecture |
| 10s | Portfolio |
| 13s | Proof |
| 15s | How it fits |
| 18s | Dark mode across the family |
| 25s | The Demo Control Tower — operator index over all 24 surfaces |
| 31s | Running the live health sweep |
| 41s | Into an open registry — OpenContextHub (one of 21 hubs from a single engine) |
| 50s | Browsing registry entries |
| 51s | An entry — provenance, signing, install command |
| 55s | Hub pricing |
| 58s | A REAL account on the hub — its own separate identity realm |
| 62s | Sign up — real realm session |
| 70s | Configuration — API keys |
| 70s | Minting a REAL API key through the identity service |
| 75s | The raw key is shown exactly once — the service stores only a hash |
| 78s | Revoking it — real revocation, gone from the realm |
| 83s | Hub billing (emulated) |
| 86s | Hub settings |
| 87s | Portfolio journey complete — parent → control tower → open hub → real account → real key lifecycle |

