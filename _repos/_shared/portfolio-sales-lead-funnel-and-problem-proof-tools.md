# /workflows /portfolio-sales-lead-funnel-and-problem-proof-tools

> **STATUS (2026-06-07).** GUARDRAIL CORE BUILT + proven (`scripts/check_sales_guardrails.py`, flywheel-
> registered). Everything outward-facing is HELD pending owner authorization on three decisions (bottom).

## Strategy (owner, locked direction)
Portfolio = a sales machine, not just architecture. **OpenHubForAI websites = inbound proof funnels · diagnostics =
credibility · Teleon = operational efficiency · Baltor = governance/compliance/trust · AI Done Right =
routes leads.** Sell a **specific pain diagnosis**, not abstract architecture. Every lead gets a **proof
artifact**, not a generic pitch. Product routing:
- "spending too much money/time creating + maintaining tasks/actions/services" → **Teleon** (Task Sprawl Audit)
- "chatbot can produce harmful/non-compliant/legally-risky guidance" → **Baltor** (Chatbot Guardrail Audit)
- "many skills/tools/prompts, no provenance/eval/promotion gate" → **OpenSkillsHub / OpenToolsHub**
- "context artifacts but no source handles/freshness/reconciliation" → **OpenContextHub / Baltor**
- eval/regression/redteam gap → **OpenHarnessHub**

Lead magnets per hub: Skill Sprawl Audit (Skills) · Tool Exposure Audit (Tools) · Source-Handle Audit (Context) ·
Eval Gap Audit (Harness). Teleon wedge = Task Sprawl Analyzer (duplicate work, failure loops, model waste,
runtime cost → CapabilityTask conversion). Baltor wedge = Chatbot Guardrail Audit (decompose claims → check
source → detect fragile/conflicting/regulated → hold out/escalate → receipt; the CFPB demo is the proof skeleton).

## ⚠️ Legal/sales guardrails (BUILT — the gate everything passes through)
"appears risky / requires review", never "illegal" · private evidence first · no public accusation against a named
real company without legal review+approval · authorized inputs only (own/customer-provided/written-authorization/
public-static) · live third-party probe REQUIRES written authorization · no login/paywall/security bypass · no
scraping private data · no abusive traffic · respect ToS · outreach draft-only · regulated categories force legal
review · Baltor≠legal advice, Teleon≠replaces K8s. Enforced by `_repos/baltor/backend/src/baltor/sales/claim_guard.py` +
`architecture/sales_{public_claim,engagement}_policy.json`.

## The 17 parts — status
1. Discovery → `.agent/sales-lead-funnel-discovery.json` — *(greenfield confirmed inline)*
2. Sales contracts — **BUILT (4 of 10):** EvidencePack/TargetCompany/DiagnosticRun/ReviewApproval. QUEUED:
   ProductPainHypothesis/PublicAISurface/LeadScore/OutreachSequence/PilotProposal/SalesLead.
3. Sales registries — **BUILT:** `sales_public_claim_policy`, `sales_engagement_policy`, `sales_pain_hypothesis_catalog`.
   QUEUED: target_registry, diagnostic_tool_catalog, lead_funnel_policy, outreach_policy(folded).
4. Target company seeds — **BUILT (synthetic only):** `fixtures/sales/synthetic_targets_seed.json`. **HELD:** real
   named seeds (require owner approval + legal review).
5. **HELD — Teleon Task Sprawl Analyzer** (runs on provided/public-static docs; no third-party probe).
6. **HELD — Baltor Chatbot Guardrail Audit** (runs on customer-provided transcripts by default; live third-party
   probe requires written authorization).
7. **HELD — OpenHubForAI diagnostics** (self/provided audits).
8. **HELD — Evidence pack generator** (must pass `gate_evidence_pack`).
9. **HELD — Lead scorer.**
10. **HELD — Outreach generator** (draft-only; must pass `gate_outreach`).
11. **HELD — OpenHubForAI lead CTAs** (website copy).
12. **HELD — Example evidence packs** (synthetic/category-only; real-company packs gated).
13. **HELD — Sales dashboard/API** (internal only).
14. Redteam — **BUILT (core):** `check_sales_guardrails.py` (A–M). QUEUED: full `check_sales_lead_funnel_redteam`.
15. Docs — **BUILT:** `docs/sales/public-claim-and-engagement-policy.md`. QUEUED: the rest.
16/17. Proofs/acceptance — guardrail proof green; rest tracked above.

## THREE decisions gating the outward-facing build (owner's call)
1. **Diagnostic input/authorization model** — self+customer-provided only · also authorized third-party live
   probes (per-target written authorization recorded) · public-static-metadata only.
2. **Outreach handling** — draft-only internal (recommended) · draft + you send manually · automated send (advise against).
3. **First diagnostic to build** — Teleon Task Sprawl (on provided docs) · Baltor Chatbot Guardrail (on provided
   transcripts) · OpenHubForAI self-audits. + whether to seed any **real** named companies (with approval).
