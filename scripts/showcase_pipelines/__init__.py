"""Open Harness Hub — runnable showcase pipelines that COMPOSE the real processors.

Each module here chains the actual `scripts/processors/**/run()` callables end-to-end
into a governed flow for a real scenario, and self-tests the whole composition. These
are the proof that the 56 processor method-components compose — not prose, runnable code.

The ONE simulated seam in each pipeline is the model call itself (clearly labeled
`# MODEL SEAM`): a deterministic stand-in derived from the retrieved evidence so the
pipeline runs offline. Everything around it — screen, retrieve, fuse, rerank, dedupe,
source-precedence, extract, place, build-prompt, verify, deliver — is the real
governed machinery. Swap the seam for `scripts.foundry.model_route` to go live.

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
"""
