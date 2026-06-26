# Sales — public-claim + engagement policy (the safety gate)

The sales/lead-proof system is **proof-first selling**: OpenHubForAI attracts → diagnostics prove → evidence packs
convert → Teleon sells operational efficiency, Baltor sells governed context / chatbot safety. This doc is the
**guardrail that everything else passes through** (built first, on purpose).

> Single sources: `architecture/sales_public_claim_policy.json`, `architecture/sales_engagement_policy.json`.
> Guard: `src/baltor/sales/claim_guard.py`. Proof (redteam): `scripts/check_sales_guardrails.py`.

## The non-negotiables

- **"Appears risky / requires review", never "illegal".** A diagnostic describes an observed *answer pattern*; it
  is **not a legal conclusion** and **not legal advice**. Legal-conclusion wording is blocked and auto-rewritten.
- **Private evidence first.** No public accusation against a **named real company** without recorded **legal
  review + approval**. `public_claim_safe` defaults **false**.
- **Authorized inputs only.** Diagnostics run on your **own systems**, **customer-provided** data/transcripts, an
  **authorized engagement** (`written_authorization`), or **public static metadata**. Sending prompt suites to a
  third party's **live/production** chatbot is a *live probe* and **requires written authorization**.
- **No bypass / no scrape / no abuse.** No login/paywall/security bypass, no scraping private data, no automated
  abusive traffic or unsolicited load-testing. Respect ToS.
- **Outreach is draft-only.** Never auto-sent; evidence-based; includes an opt-out; no public accusation.
- **Regulated categories** (consumer-finance, credit, debt, loans, wage/employment, health, legal) **force legal
  review** before any public claim.
- **Product-message guardrails.** Baltor never claims "legal advice"/"guarantees compliance"; Teleon never claims
  to "replace Kubernetes/cloud functions" or "deploy agents in minutes".
- **No real-company seeds without owner approval.** Committed target fixtures are **synthetic exemplars** only.

## What the guard enforces (proven)

`gate_evidence_pack` returns *not publishable* on: legal-conclusion text · named-real-company public claim without
approval · regulated public claim without approved review · missing source/authorization. `authorization_ok`
blocks live third-party probes without written authorization. `gate_outreach` blocks auto-send / missing opt-out /
legal-conclusion bodies. `classify_claim_language` + `safe_rewrite` keep wording in the "appears/requires review"
register.

## Status of the larger build (see `prompts/portfolio-sales-lead-funnel-and-problem-proof-tools.md`)

**BUILT (this slice):** the guardrail core — policies, the four contracts (EvidencePack/TargetCompany/
DiagnosticRun/ReviewApproval), the pain-hypothesis catalog, synthetic seeds, the guard module, the redteam proof.

**HELD for owner authorization (outward-facing / legal blast radius):** the live diagnostic tools (Task Sprawl
Analyzer, Chatbot Guardrail Audit, OpenHubForAI scanners), the evidence-pack generator, lead scorer, **outreach
generator**, the sales dashboard/API, and **any real named-company seeds**. These are scoped behind the three
decisions in the build prompt and are not built until the owner confirms input/authorization model + outreach
handling + first target.
