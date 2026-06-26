"""OpenHubForAI — runnable showcase pipelines that COMPOSE the real processors.

Each module here chains the actual `scripts/processors/**/run()` callables end-to-end
into a governed flow for a real scenario, and self-tests the whole composition. These
are the proof that the 56 processor method-components compose — not prose, runnable code.

The ONE simulated seam in each pipeline is the model call itself (clearly labeled
`# MODEL SEAM`): a deterministic stand-in derived from the retrieved evidence so the
pipeline runs offline. Everything around it — screen, retrieve, fuse, rerank, dedupe,
source-precedence, extract, place, build-prompt, verify, deliver — is the real
governed machinery. Swap the seam for `scripts.foundry.model_route` to go live.

Every pipeline here is kept green by the flywheel gate (registered in
`scripts/flywheel_proof_modules.py` as `showcase_*`) — a processor change that breaks a
composition is caught, not just discoverable. They span durability classes and domains
beyond the CFPB/regulated-fact flagship.

Pipelines:
  regulated_fact_qa     — governed regulated-fact QA (state usury caps): screen →
                          hybrid retrieve → rerank → dedupe → source-precedence →
                          extract → edge-place → cite-or-abstain prompt → verify →
                          report. The flagship (matches the CAPSTONE thesis).
  governed_rag          — the general hybrid-RAG default: retrieve → fuse → rerank →
                          place → prompt, with injection screening.
  clinical_support      — defensive clinical decision-support: the clinical family
                          composed (interactions → dosing → labs → abstain → escalate).
  low_resource_alert    — disaster-alert pipeline for a low-resource language:
                          faithful-extract → english-pivot → language-lock →
                          tts-preprocess → escalate (human signs off before broadcast).
  context_efficiency_loop — usage-gated context compression: classify the tenant's
                          usage shape → cohort compression curve → serve only what's
                          needed (the consumer-behavior efficiency loop).
  sanctions_aml_screening — OFAC 50% Rule (durability: AGGREGATION): an UNLISTED entity
                          majority-owned by listed persons through an ownership chain is
                          BLOCKED — graph arithmetic a bare model can't do.
  cve_dependency_triage — CVE/dependency triage (durability: FRESHNESS + exactness):
                          exact CVE-id lookup → deterministic version-range match vs the
                          lockfile → NVD/KEV precedence → escalate; abstain on unknowns.
  icd10_coding          — ICD-10 coding assistant (durability: CODED VOCABULARY): SOAP
                          structure → ground each documented diagnosis to the terminology
                          → ABSTAIN over fabricate → propose to a human coder.
  related_party_network — shell-network discovery (durability: AGGREGATION): normalize
                          identifiers → shared-address/phone/officer graph → union-find
                          components; "independent" agencies sharing identifiers collapse
                          into one HIGH-risk network; a disclosed M&A group stays NORMAL.
  common_control_resolver — common control from M&A news (durability: AGGREGATION +
                          FRESHNESS): chain acquisitions by date → ultimate parent; a
                          vendor↔customer transaction under one parent is flagged as a
                          related-party (self-dealing) transaction — temporal/as-of aware.
  procurement_collusion_ring — bid-rigging detection (durability: AGGREGATION):
                          aggregate bids across tenders → a co-bidding group whose wins
                          rotate and whose losing bids are cover bids is flagged as a ring;
                          an honest undercutter is excluded, a competitive ledger is not.
"""
