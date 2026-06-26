# Fragile Context Audit — offer catalogue

> GENERATED from `architecture/fragile_context_atlas.json` by `python3 scripts/check_fragile_context_audit_offers.py --emit`. Do not hand-edit — edit the atlas and regenerate; the proof asserts this file is in lock-step with the registry.

A **Fragile Context Audit** is a *diagnostic*, not a verdict. It shows where a team's own AI surface (a support chatbot, a RAG index, agent memory, enterprise search, a workflow agent) is serving a fragile answer — one that is stale, conflicting, jurisdiction-specific, or sourced from the wrong authority — and what the source-of-record answer is instead. It is **proof-first selling**: the OpenHubForAI surfaces attract, the diagnostic proves, an evidence pack converts. Every output is a **draft** in "appears / requires review" language; nothing here is a legal conclusion or legal advice.

## How an audit runs (reuses the sales subsystem — no new pipeline)

- `schemas/sales/TargetCompany.schema.json` — the (synthetic or authorized) **TargetCompany** the audit is scoped to.
- `schemas/sales/DiagnosticRun.schema.json` — the **DiagnosticRun**: the prompts asked and the answers observed.
- `schemas/sales/EvidencePack.schema.json` — the **EvidencePack**: the findings, drafted, `public_claim_safe` false by default.
- `schemas/sales/ReviewApproval.schema.json` — the **ReviewApproval**: a human (and, for regulated categories, legal) signs off before anything leaves.

Everything passes through the safety gate in `docs/sales/public-claim-and-engagement-policy.md` (single sources: `architecture/sales_public_claim_policy.json`, `architecture/sales_engagement_policy.json`; guard `src/baltor/sales/claim_guard.py`, redteam `scripts/check_sales_guardrails.py`).

## The audit output (10 fields)

1. The prompt / question asked
2. The raw system answer, as observed
3. The source handles behind that answer
4. The conflicting sources found
5. The governed answer (supported by the source of record)
6. The held-out warnings (contradictions, never served)
7. The freshness status + refresh cadence
8. The risk category (which fragility modes)
9. The recommended control (gate / refresh / human review)
10. The matching demo link, where one is live

## Safety (non-negotiable)

- **"Appears risky / requires review", never a legal conclusion.** A diagnostic describes an observed answer pattern; it is not legal advice.
- **Authorized inputs only.** Synthetic exemplars or customer-provided/authorized data. Sending a prompt suite to a third party's live/production system is a live probe and requires **written authorization**.
- **No public accusation against a named real company without recorded legal review + approval.** `public_claim_safe` defaults false; committed target fixtures are synthetic exemplars only.
- **Regulated categories** (consumer-finance, credit, debt, wage/employment, health, legal) force legal review before any public claim.
- **Outreach is draft-only** — evidence-based, with an opt-out, never auto-sent.

## Offers

### Consumer-Finance Chatbot Guardrail Audit
- **Domains:** Consumer finance / fintech / banking
- **Fragility modes:** Authority-fragile, Compliance-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.consumer_finance.cfpb_reg_e_timing
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Consumer finance / fintech / banking context is authority-fragile, compliance-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Coverage-Context Contradiction Audit
- **Domains:** Insurance / claims / coverage
- **Fragility modes:** Action-fragile, Authority-fragile, Customer-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.insurance.coverage_appeal_deadline
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Insurance / claims / coverage context is action-fragile, authority-fragile, customer-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Dangerous-Goods SOP Audit
- **Domains:** Logistics / shipping / transport
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Source-fragile
- **Atlas packs:** fragile.logistics_shipping.dangerous_goods_soc
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Logistics / shipping / transport context is action-fragile, authority-fragile, compliance-fragile, source-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Data-Retention & Residency Audit
- **Domains:** Data privacy / retention / residency
- **Fragility modes:** Compliance-fragile, Jurisdiction-fragile, Privacy-fragile, Time-fragile
- **Atlas packs:** fragile.data_privacy_residency.gdpr_retention
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Data privacy / retention / residency context is compliance-fragile, jurisdiction-fragile, privacy-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Developer-Docs Deprecation Audit
- **Domains:** Developer docs / API copilots
- **Fragility modes:** Authority-fragile, Conflict-fragile, Source-fragile, Time-fragile
- **Atlas packs:** fragile.developer_docs_api.deprecation
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Developer docs / API copilots context is authority-fragile, conflict-fragile, source-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Disclosure-Basis Source Audit
- **Domains:** Capital-markets / financial disclosure
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Model-fragile
- **Atlas packs:** fragile.capital_markets_disclosure.reserves_basis
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Capital-markets / financial disclosure context is action-fragile, authority-fragile, compliance-fragile, model-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### EUDR / ESG Deadline Freshness Audit
- **Domains:** Supply chain / ESG / EUDR
- **Fragility modes:** Action-fragile, Authority-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.supply_chain_esg.eudr_deadline
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Supply chain / ESG / EUDR context is action-fragile, authority-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Enterprise-Brain Context Hygiene Audit
- **Domains:** Enterprise search / company brain
- **Fragility modes:** Authority-fragile, Conflict-fragile, Freshness-fragile, Privacy-fragile, Source-fragile
- **Atlas packs:** fragile.enterprise_company_brain.source_authority
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Enterprise search / company brain context is authority-fragile, conflict-fragile, freshness-fragile, privacy-fragile, source-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Environmental-Limit Source Audit
- **Domains:** Environmental / utility regulatory limits
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.environmental_regulatory.epa_lead_rule
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Environmental / utility regulatory limits context is action-fragile, authority-fragile, compliance-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### HR / Payroll Guidance Risk Audit
- **Domains:** HR / payroll / benefits
- **Fragility modes:** Authority-fragile, Compliance-fragile, Customer-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.hr_payroll_benefits.wage_deduction
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where HR / payroll / benefits context is authority-fragile, compliance-fragile, customer-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Labor-Recruitment Licensing Freshness Audit
- **Domains:** Labor mobility / recruitment licensing
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Freshness-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.labor_mobility.ph_employment_agency_license
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Labor mobility / recruitment licensing context is action-fragile, authority-fragile, compliance-fragile, freshness-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Legal-Context Provenance Audit
- **Domains:** Legal / contract / compliance
- **Fragility modes:** Authority-fragile, Customer-fragile, Jurisdiction-fragile, Source-fragile, Time-fragile
- **Atlas packs:** fragile.legal_compliance.clause_playbook
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Legal / contract / compliance context is authority-fragile, customer-fragile, jurisdiction-fragile, source-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Lending-Disclosure Freshness Audit
- **Domains:** Real estate / mortgage / lending
- **Fragility modes:** Compliance-fragile, Customer-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.real_estate_mortgage.disclosure_timing
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Real estate / mortgage / lending context is compliance-fragile, customer-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Marine-Fuel Spec Audit
- **Domains:** Logistics / shipping / transport
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.logistics_shipping.marine_fuel_sulphur
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Logistics / shipping / transport context is action-fragile, authority-fragile, compliance-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Medical-Coding Freshness Audit
- **Domains:** Clinical coding / payer policy
- **Fragility modes:** Action-fragile, Authority-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.clinical_coding.icd11_in_force
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Clinical coding / payer policy context is action-fragile, authority-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Operational-Rule SOP Audit
- **Domains:** Logistics / shipping / transport
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Conflict-fragile
- **Atlas packs:** fragile.logistics_shipping.driving_hours
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Logistics / shipping / transport context is action-fragile, authority-fragile, compliance-fragile, conflict-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Refund / Billing Policy Contradiction Audit
- **Domains:** Customer support / refunds / billing
- **Fragility modes:** Authority-fragile, Conflict-fragile, Customer-fragile, Source-fragile
- **Atlas packs:** fragile.customer_support_refunds.refund_window
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Customer support / refunds / billing context is authority-fragile, conflict-fragile, customer-fragile, source-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Regulatory-Limit Grounding Audit
- **Domains:** Pharma / regulatory limits
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Time-fragile
- **Atlas packs:** fragile.pharma_regulatory.fda_limit
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Pharma / regulatory limits context is action-fragile, authority-fragile, compliance-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Sales-Claims Governance Audit
- **Domains:** Sales / marketing / approved claims
- **Fragility modes:** Authority-fragile, Compliance-fragile, Conflict-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.sales_marketing_claims.approved_claim
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Sales / marketing / approved claims context is authority-fragile, compliance-fragile, conflict-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Sanctions / Screening Freshness Audit
- **Domains:** Sanctions / KYC / screening
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Freshness-fragile
- **Atlas packs:** fragile.sanctions_kyc.ofac_sdn_match
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Sanctions / KYC / screening context is action-fragile, authority-fragile, compliance-fragile, freshness-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Shipping-Promise vs Contract Audit
- **Domains:** Logistics / shipping / transport
- **Fragility modes:** Action-fragile, Conflict-fragile, Customer-fragile, Source-fragile
- **Atlas packs:** fragile.logistics_shipping.transit_sla
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Logistics / shipping / transport context is action-fragile, conflict-fragile, customer-fragile, source-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Supplier-Evidence Source Audit
- **Domains:** Procurement / vendor risk
- **Fragility modes:** Action-fragile, Authority-fragile, Source-fragile, Time-fragile
- **Atlas packs:** fragile.procurement_vendor_risk.cert_expiry
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Procurement / vendor risk context is action-fragile, authority-fragile, source-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Tariff Classification Fragility Audit
- **Domains:** Trade / tariffs / customs
- **Fragility modes:** Action-fragile, Authority-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.trade_tariffs_customs.hs_classification
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Trade / tariffs / customs context is action-fragile, authority-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Tax-Rule Freshness Audit
- **Domains:** Tax / accounting guidance
- **Fragility modes:** Action-fragile, Authority-fragile, Jurisdiction-fragile, Time-fragile
- **Atlas packs:** fragile.tax_accounting.rule_freshness
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Tax / accounting guidance context is action-fragile, authority-fragile, jurisdiction-fragile, time-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.

### Workplace-Safety Limit Audit
- **Domains:** Occupational / workplace safety
- **Fragility modes:** Action-fragile, Authority-fragile, Compliance-fragile, Jurisdiction-fragile
- **Atlas packs:** fragile.occupational_safety.osha_pel
- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.
- **Finds:** where Occupational / workplace safety context is action-fragile, authority-fragile, compliance-fragile, jurisdiction-fragile — an answer served from a stale, conflicting, or wrong-authority source instead of the source of record.
