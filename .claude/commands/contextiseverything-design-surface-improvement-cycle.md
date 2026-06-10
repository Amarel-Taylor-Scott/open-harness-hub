---
description: Design loop — refine the Baltor/Teleon/portfolio HTML surfaces (web/baltor/, openharness tokens), one verified design increment per cycle. Design-only; never backend.
---

You extend the ContextIsEverything / Teleon / Baltor DESIGN portfolio — DESIGN + PROTOTYPE work ONLY. Build/refine
interactive HTML surfaces, preserve positioning, verify visual quality, cross-link correctly, stop after ONE
verified design increment. NOT backend: do not touch runtime/provider-routing/durable-workers/flywheel-proof
code, run no network/LLM calls, make no claim the prototypes don't support, imply no production hosting, create no
dead links, expose no secrets/keys/customer-data/private-memory/raw-receipts. STOP if `STOP_REQUESTED` exists.

## REALITY (verified 2026-06-08)
The literal `openharness/` tree referenced by the original spec is NOT in this working copy. The real surfaces are
**`web/baltor/*.html`** (index, guided-demos, context-stages, reconciliation/optimization/receipts surfaces,
determinism, inference-plane, temporal-graph, memory, native, hub, how-it-works, dashboard, …) with tokens at
`web/baltor/styles/oh-tokens.css` and the canonical spec at `docs/design/openharness-claude-design/`. ADAPT here.
**No browser tool in the headless loop** → the mandated 1280/390 SCREENSHOT + console verification is NOT possible
headless; new *visual* surfaces (increment A) are therefore **HELD** in headless runs (mark the reason). Do the
STATICALLY-verifiable increments (audit/polish/copy-guardrail/link-resolution/token-usage) and run the existing
static design proofs: check_baltor_guided_demos · check_demo_console_links · check_opencontext_fragile_atlas_page ·
check_pipeline_pages_full_stack · check_portfolio_website_discovery · check_portfolio_websites_are_distinct ·
check_memory_page_projection_only. (When run WITH a browser session, do the full A/B/C visual increments + screenshots.)

## POSITIONING (every surface)
Mission "Context is Everything." Baltor = governed-context engine; value is the FULL engine, pillars as PEERS:
Reconciliation · Anti-Fragility/Hardening · Enhancement · Optimization · Verification+Receipts/Provenance. Echo
**Verified · Current · Efficient · Provable**. Fragility/held-out is ONE lens, never the whole pitch. Teleon =
purpose-defined eval-gated self-adaptive runtime (CapabilityTask stable, implementation evolves, evidence decides,
policy gates promotion, humans approve boundaries). Open*Hubs = registries, not truth authorities (discovery≠trust).

## COPY/TRUTH GUARDRAILS
Served answer is governed; model never decides truth; held-out contradictions shown SEPARATELY, never served;
output≠truth; dashboards projection-only. Honest status only (label local/preview/proven; never imply production
hosting or a live model/cloud call that isn't real). FORBIDDEN: "100% accurate" / "fully autonomous" / "replaces
Kubernetes|CI/CD|engineers" / "guaranteed compliance" / legal|medical|financial advice. Sensitive domains
(FDA/ICD/OSHA/sanctions/clinical/legal/finance) carry "Not advice — source in force is the authority." No raw
secrets/keys/customer-data/private-memory.

## DESIGN SYSTEM (reuse, don't reinvent)
oh-tokens.css / oh-components.css / oh-site.css; Hanken Grotesk + IBM Plex Mono; `.oh-card`; the `.cd-*` layer in
context-enrichment/guided-demo.css for Baltor demo pages; additive backwards-compatible shared components; one
shared experiments engine. Accent ONLY differs per brand (Baltor dir-d teal). Never hardcode color/size — use tokens.

## QUALITY BAR (verify before done)
No horizontal overflow at 1280px AND 390px; long hashes/ids/handles wrap (overflow-wrap); chips/badges/mono-tags
white-space:nowrap; no mid-word break/clip/overlap; text ≥ shared scale; tables scroll in-container on narrow;
light+dark legible; keyboard-focusable; not color-only status; clean console; no dead links/missing pages/broken
anchors; no false production claims.

## PICK ONE INCREMENT (priority order; skip done; don't duplicate)
A. A Baltor engine stage WITHOUT a first-class surface (Anti-Fragility/Hardening deep-dive: volatile fact →
   refreshable object, freshness/decay, re-verify trigger, held-out stale copy; OR Enhancement deep-dive: citation
   + relationship attachment, source authority, verified external source). [HELD headless — needs browser screenshots.]
B. Light up one backlog atlas pack as a runnable guided demo (one SCENARIOS object in guided-demo.js + thin shell
   HTML + index entry + coverage-map link; same 7-stage governed shape, receipts, source handles, held-out contradiction).
C. Industry landing for ONE buyer (banks/logistics/HR-payroll/insurance/dev-docs) reusing existing demos, no new claims.
D. Polish/audit pass: hunt forbidden copy, missing disclaimers, overflow/clip artifacts, dead links, hardcoded
   colors-vs-tokens across existing surfaces — STATICALLY verifiable; the safe headless default.
If the chosen increment needs backend/live/owner-decision/browser-only verification → mark HELD (one-line reason) + pick another.

## BUILD + VERIFY + REPORT
Build in the design system; honor every guardrail; keep fragility as one lens; cross-link from the relevant index
(+ Demo Control Tower if a demo); no dead links. Verify statically (proofs above; grep guardrails) — and visually
(screenshots) only with a browser session; fix + re-check. Report one paragraph + bullets (what/which pillar/
on-positioning/verified/next candidate). Then STOP — one increment per cycle. Backend continuation stays on the
backend loop (owner standing choice: "keep the backend loop").
