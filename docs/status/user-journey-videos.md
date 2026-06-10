# User-journey videos — the wired full-design family

Generated 2026-06-10T20:10:31.350Z by `e2e/record_user_journeys.mjs` (1600×900; the OpenHarnessHub
and Teleon cuts record THROUGH THEIR PUBLIC TUNNEL URLS). Files in `artifacts/e2e/videos/`
(webm + mp4). GENERATED from `artifacts/e2e/reports/user-journeys.json` — regenerate, don't
hand-edit.

Honesty rules on camera: REAL seams exercised for real (per-realm sign-up, /api/build, the live
registry, the REAL Teleon capability lifecycle — deterministic execution, receipts, promotion
gate — real installs, key mint/revoke, the live event bus, ⌘K, A/B variants); the few designed
surfaces are captioned as such (run console, emulated billing/checkout, copy pages).

## Open Harness Hub — PUBLIC URL: landing → live build → live registry → sign-up → live canvas + real export → configuration

`artifacts/e2e/videos/journey-1-openharnesshub.mp4` · 106s · 25 chapters · recorded against `expansion-cat-manual-podcasts.trycloudflare.com`

| t | chapter |
|---|---|
| 6s | OpenHarnessHub.io — live on the public link: expansion-cat-manual-podcasts.trycloudflare.com |
| 12s | Describe a task — the REAL backend assembles a governed pipeline |
| 15s | Build → /api/build assembles from 2,400+ governed components |
| 22s | The REAL assembled flow — live components, recipe phases, real cost. No invented lift numbers. |
| 29s | Explore — the live registry: 2,400+ real components |
| 31s | Search and facets run over the real catalog |
| 36s | A real component — license, lifecycle, provenance from the catalog |
| 44s | Create a REAL account — per-realm identity, no SSO, no fake sessions |
| 48s | The identity service registers, onboards, and mints a session |
| 55s | The workspace — “recent flows” is YOUR real build history |
| 61s | Confirm the task and constraints |
| 63s | Assemble — live backend build |
| 68s | Three REAL cost tiers — cheap / balanced / quality, from the live cost model. Lift: honestly “unproven”. |
| 70s | The flow canvas — the REAL build in the designed topology |
| 74s | Every node is a real catalog component — click to inspect |
| 77s | Swap alternatives are the build’s REAL dropped candidates, ranked by match |
| 79s | Deploy → downloads the REAL open-spec YAML bundle |
| 82s | Run console (designed simulation — captioned, not faked) |
| 87s | Foundry — distillation & verification tooling |
| 89s | Governance — provenance, signing, review gates |
| 92s | Checkout — the commercial surface (payment EMULATED, no charges) |
| 95s | Plans & upgrade (emulated) |
| 97s | Configuration — workspace settings |
| 101s | Dark mode — same surface, dark tokens |
| 106s | OpenHarnessHub — fully wired: live registry, live builds, real accounts, real exports |

## Baltor — landing → sign-up → console → emulated billing → LIVE pipeline on the real event bus

`artifacts/e2e/videos/journey-2-baltor.mp4` · 84s · 17 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 5s | Baltor — context assurance (the paid product) |
| 13s | Why context — the thesis |
| 16s | The Context Engine — six governed stages + verification rail |
| 22s | Case studies |
| 24s | Pricing |
| 26s | A REAL Baltor account — its own identity realm (no SSO) |
| 31s | Real register → onboarding → session |
| 38s | The console — corpora, freshness, serving health |
| 44s | Governed corpora — raw / compressed / hyper tiers |
| 45s | Inside a corpus — tiers, freshness, citations |
| 49s | Serving context packages to agents |
| 52s | Verification — claims checked against live sources |
| 54s | The audit log |
| 57s | Billing — plan & invoices (payment EMULATED, no charges) |
| 65s | Live ops — the REAL event bus behind the product |
| 66s | Run Full Pipeline — a REAL run, streaming real events and receipts |
| 84s | Baltor — real console, real events, honest billing emulation |

## AI Done Right → Control Tower → OpenContextHub — real account + REAL key mint/revoke

`artifacts/e2e/videos/journey-3-portfolio-hub.mp4` · 62s · 17 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 5s | AI Done Right — the parent portfolio (2 products + 21 open hubs) |
| 6s | Thesis |
| 8s | Architecture |
| 10s | Portfolio |
| 12s | Proof |
| 14s | One design system, light and dark |
| 19s | The Demo Control Tower — operator index over all 24 surfaces |
| 30s | An open registry — OpenContextHub (21 hubs, one engine) |
| 36s | Browsing registry entries |
| 38s | A REAL account on the hub — separate identity realm |
| 43s | Sign up — real realm session |
| 49s | Configuration — API keys |
| 50s | Minting a REAL API key (the service stores only a hash) |
| 55s | The raw key appears exactly once — copy it now |
| 57s | Real revocation — gone from the realm immediately |
| 61s | Hub billing (emulated) |
| 62s | One portfolio: parent → tower → hubs — real accounts, real keys, one design system |

## Teleon — PUBLIC URL: landing → sign-up → REAL capability build (gate + receipts) → REAL key lifecycle → tower

`artifacts/e2e/videos/journey-4-teleon.mp4` · 107s · 29 chapters · recorded against `national-horizontal-rankings-katrina.trycloudflare.com`

| t | chapter |
|---|---|
| 6s | Teleon.dev — live on the public link: national-horizontal-rankings-katrina.trycloudflare.com |
| 7s | Capabilities, not code — the hero ships with live A/B variants (see the chip) |
| 12s | How it works |
| 16s | Case studies |
| 19s | Pricing |
| 21s | Docs |
| 23s | Create a REAL account — Teleon has its own identity realm (no SSO) |
| 27s | Real register → onboarding → session |
| 35s | Capabilities — the REAL runtime state: status from a real promotion gate |
| 39s | Build a capability — this executes FOR REAL (deterministic examples, receipts) |
| 41s | Building — every example runs now; the gate scores the real pass-rate |
| 49s | Shipped by the REAL gate — real score, real version bump, receipts on disk |
| 54s | The capability table updates from the run that just happened |
| 57s | The console — REAL counters from your recorded runs |
| 61s | ⌘K — the command palette, on every app surface |
| 64s | Evidence — what was tried, how it scored, why it shipped |
| 66s | Library — building blocks drawn from the open hubs |
| 68s | Configuration — API keys |
| 69s | Minting a REAL API key on the teleon realm |
| 74s | The raw key is shown exactly once — the service stores only a hash |
| 76s | Real revocation — gone immediately |
| 80s | Team |
| 82s | Usage — REAL recorded runs and execution time |
| 85s | Billing — plan & invoices (payment EMULATED, no charges) |
| 87s | Audit log |
| 90s | Settings |
| 93s | Dark mode — same tokens, dark theme |
| 101s | The PurposeTask Control Tower — operator view (designed prototype) |
| 107s | Teleon — real accounts, real keys, and a REAL capability lifecycle: build → gate → ship |

## The open registries — 8 live hubs (one engine) + bespoke depth + a REAL install

`artifacts/e2e/videos/journey-5-open-hubs.mp4` · 104s · 27 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 4s | The open registries — 8 live hubs, every one rendered by ONE engine |
| 8s | openbenchmarkhub — landing |
| 12s | openbenchmarkhub — browse the registry |
| 16s | opencompressionhub — landing |
| 20s | opencompressionhub — browse the registry |
| 23s | opencontexthub — landing |
| 28s | opencontexthub — browse the registry |
| 31s | openmcphub — landing |
| 36s | openmcphub — browse the registry |
| 39s | openreviewhub — landing |
| 43s | openreviewhub — browse the registry |
| 47s | openskillshub — landing |
| 51s | openskillshub — browse the registry |
| 55s | openskilltotool — landing |
| 59s | openskilltotool — browse the registry |
| 62s | opentoolshub — landing |
| 67s | opentoolshub — browse the registry |
| 71s | OpenSkillToTool — bespoke depth: the conversion architecture |
| 77s | The convert wizard |
| 81s | OpenReviewHub — governed reviews |
| 82s | A review entry |
| 88s | OpenContextHub — a REAL account + a REAL install |
| 91s | Real realm sign-up |
| 98s | Pick an entry |
| 99s | The entry — provenance, signing, install |
| 104s | Installed — the REAL workspace row from the registry service |
| 104s | The open funnel: 8 live registries + the OpenHarnessHub product, one design system, real accounts everywhere |

## The private bench (13 hubs) + internal planes + the Design Acceptance Scorecard

`artifacts/e2e/videos/journey-6-private-bench.mp4` · 72s · 19 chapters · recorded against `127.0.0.1`

| t | chapter |
|---|---|
| 4s | The operator index — and behind it, the PRIVATE BENCH |
| 8s | 13 private-bench registries — muted accent + “Private preview” banner until the owner flips them live |
| 11s | openagenthub — private preview |
| 14s | openendpointhub — private preview |
| 17s | openenrichmenthub — private preview |
| 20s | openenvhub — private preview |
| 23s | openhardeninghub — private preview |
| 26s | openoptimizationhub — private preview |
| 29s | openreceipthub — private preview |
| 32s | openreconciliationhub — private preview |
| 35s | openroutinghub — private preview |
| 38s | opensandboxhub — private preview |
| 42s | openstatehub — private preview |
| 45s | opentemplateshub — private preview |
| 48s | openverificationhub — private preview |
| 51s | Shared Inference Gateway — the internal routing plane |
| 59s | Shared Template Registry — the internal template plane |
| 66s | The Design Acceptance Scorecard — the branded-house consistency gate |
| 72s | The whole family: 24+ surfaces, one design system, verified end to end |

