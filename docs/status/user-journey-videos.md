# User-journey videos — the three wired full-design apps

Generated 2026-06-10T19:06:53.153Z by `e2e/record_user_journeys.mjs` (v2: 1600×900, tighter pacing;
the OpenHarnessHub cut records THROUGH THE PUBLIC TUNNEL URL when it answers). Files land in
`artifacts/e2e/videos/` (webm + mp4). This manifest is GENERATED from
`artifacts/e2e/reports/user-journeys.json` — regenerate, don't hand-edit.

Honesty rules on camera: REAL seams exercised for real (per-realm sign-up, /api/build, the live
2,400+-component registry, the live flow canvas with real swap alternatives, a REAL open-spec
YAML export, the live event bus, API-key mint/revoke); designed simulations are captioned as
such (run console, emulated billing/checkout).

## Open Harness Hub — PUBLIC URL: landing → live build → live registry → sign-up → live canvas + real export → configuration

`artifacts/e2e/videos/journey-1-openharnesshub.mp4` · 107s · 25 chapters · recorded against `expansion-cat-manual-podcasts.trycloudflare.com`

| t | chapter |
|---|---|
| 7s | OpenHarnessHub.io — live on the public link: expansion-cat-manual-podcasts.trycloudflare.com |
| 14s | Describe a task — the REAL backend assembles a governed pipeline |
| 18s | Build → /api/build assembles from 2,400+ governed components |
| 24s | The REAL assembled flow — live components, recipe phases, real cost. No invented lift numbers. |
| 31s | Explore — the live registry: 2,400+ real components |
| 33s | Search and facets run over the real catalog |
| 39s | A real component — license, lifecycle, provenance from the catalog |
| 47s | Create a REAL account — per-realm identity, no SSO, no fake sessions |
| 50s | The identity service registers, onboards, and mints a session |
| 57s | The workspace — “recent flows” is YOUR real build history |
| 63s | Confirm the task and constraints |
| 65s | Assemble — live backend build |
| 70s | Three REAL cost tiers — cheap / balanced / quality, from the live cost model. Lift: honestly “unproven”. |
| 72s | The flow canvas — the REAL build in the designed topology |
| 76s | Every node is a real catalog component — click to inspect |
| 78s | Swap alternatives are the build’s REAL dropped candidates, ranked by match |
| 80s | Deploy → downloads the REAL open-spec YAML bundle |
| 83s | Run console (designed simulation — captioned, not faked) |
| 88s | Foundry — distillation & verification tooling |
| 90s | Governance — provenance, signing, review gates |
| 93s | Checkout — the commercial surface (payment EMULATED, no charges) |
| 96s | Plans & upgrade (emulated) |
| 98s | Configuration — workspace settings |
| 102s | Dark mode — same surface, dark tokens |
| 107s | OpenHarnessHub — fully wired: live registry, live builds, real accounts, real exports |

## Baltor — landing → sign-up → console → emulated billing → LIVE pipeline on the real event bus

`artifacts/e2e/videos/journey-2-baltor.mp4` · 83s · 17 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 4s | Baltor — context assurance (the paid product) |
| 12s | Why context — the thesis |
| 15s | The Context Engine — six governed stages + verification rail |
| 21s | Case studies |
| 23s | Pricing |
| 25s | A REAL Baltor account — its own identity realm (no SSO) |
| 30s | Real register → onboarding → session |
| 37s | The console — corpora, freshness, serving health |
| 43s | Governed corpora — raw / compressed / hyper tiers |
| 44s | Inside a corpus — tiers, freshness, citations |
| 49s | Serving context packages to agents |
| 51s | Verification — claims checked against live sources |
| 54s | The audit log |
| 56s | Billing — plan & invoices (payment EMULATED, no charges) |
| 64s | Live ops — the REAL event bus behind the product |
| 65s | Run Full Pipeline — a REAL run, streaming real events and receipts |
| 83s | Baltor — real console, real events, honest billing emulation |

## AI Done Right → Control Tower → OpenContextHub — real account + REAL key mint/revoke

`artifacts/e2e/videos/journey-3-portfolio-hub.mp4` · 63s · 17 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 5s | AI Done Right — the parent portfolio (2 products + 21 open hubs) |
| 6s | Thesis |
| 8s | Architecture |
| 10s | Portfolio |
| 12s | Proof |
| 15s | One design system, light and dark |
| 20s | The Demo Control Tower — operator index over all 24 surfaces |
| 30s | An open registry — OpenContextHub (21 hubs, one engine) |
| 37s | Browsing registry entries |
| 39s | A REAL account on the hub — separate identity realm |
| 43s | Sign up — real realm session |
| 50s | Configuration — API keys |
| 51s | Minting a REAL API key (the service stores only a hash) |
| 55s | The raw key appears exactly once — copy it now |
| 58s | Real revocation — gone from the realm immediately |
| 62s | Hub billing (emulated) |
| 63s | One portfolio: parent → tower → hubs — real accounts, real keys, one design system |

