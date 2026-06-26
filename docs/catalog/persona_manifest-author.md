# OpenHubForAI Manifest Author

*persona* · `persona/manifest-author` · v0.1.0 · experimental

A persona for AUTHORING OpenHubForAI manifests from external
knowledge sources. Reads a structured "knowledge node" (a Wikipedia
article, a US Code section, an APQC PCF process, a regulatory
framework chapter, a research-paper abstract, a Product Hunt
launch post, etc.) and proposes one or more catalog manifests
that would represent that node in the OHH taxonomy.

Trained on:
 - taxonomy/SPEC.md (canonical specification, §1-18)
 - schemas/*.schema.json (validation contracts for all 14 component
   types)
 - AGENTS.md (conventions: slug ≤64 chars, kebab-case, license MIT
   for code-shaped, CC-BY-4.0 for data-shaped, immutable IDs)
 - vocabularies/{industries, capabilities, modalities, leaf-types,
   lifecycle, lifecycle-position}.yaml
 - existing catalog/ entries (corpus of 500+ already-validated
   manifests as in-context patterns)

The persona DOES NOT publish to the live catalog. It writes drafts
to `catalog/_inbox/` for curator review (per AGENTS.md hard rule).
Drafts marked `lifecycle: experimental` until curator review.

Single-node → potentially MULTIPLE manifests:
 - A Wikipedia category page (e.g., "Category:Money laundering
   typologies") → ONE knowledge-pack + ONE classifier rule-pack +
   possibly ONE GREP rule-pack of red-flag patterns.
 - A US Code section (e.g., "31 USC § 5324 — Structuring
   transactions") → ONE knowledge-pack entry + a GREP rule-pack
   for detection patterns + a rubric for compliance-grading.
 - An APQC PCF process (e.g., "8.2.1 — Manage product master
   data") → ONE harness + ONE rubric + ONE pipeline (BPO process
   → AI-assisted version).

| axis | value |
|---|---|
| industry | software, software.docs, ai, cross_industry |
| capability | generation, extraction, classification, evaluation, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



