# Annex IV technical documentation — OSH fall-protection & scaffold compliance check (DO 198 / OSHA 1926)

> Generated from Open Harness Hub manifest `pipeline/osh-fall-protection-scaffold-compliance-check` v0.1.0. EU AI Act Regulation 2024/1689, Annex IV.

## 1. General description of the AI system

- **Name**: OSH fall-protection & scaffold compliance check (DO 198 / OSHA 1926)
- **Provider**: Open Harness Hub contributors
- **Intended purpose**: Review a construction-site safety packet (job hazard analysis, scaffold
inspection tags, toolbox-talk logs, safety-officer accreditation) for
fall-protection and scaffolding compliance, grounded in the Philippine
Occupational Safety and Health Standards (RA 11058 + DOLE Department Order
198 s. 2018) cross-walked to OSHA 29 CFR 1926 (Subpart L scaffolds, Subpart
M fall protection, Focus Four). It flags: working at height without fall
protection, scaffold erected/used without a competent person, scaffold
defects, and a site at/above the size threshold operating without a
DOLE/PRC-accredited safety officer — then routes worker-safety flags to the
DOLE Regional Office (OSH division) alongside the building-code path.

Standard hybrid RAG bundle (Bundle A) over the OSHA-1926 corpus with a
deterministic grep pre-screen for the Focus-Four signals; the
safety-officer accreditation is an accountability_or_license signal a model
cannot hold, so its absence is flagged and routed, never assumed satisfied.
Detection + routing + citations only; no worker PII stored; no advice on
evading safety requirements.
- **Version**: 0.1.0
- **EU AI Act risk classification**: `high_risk`

## 2. Detailed description of the elements

### 2.1 Methods and steps used to develop the system

Pipeline composed of:

1. **structured_to_prose** (processor) → `processor/structured-to-prose`
2. **redact_pii** (processor) → `processor/redact-pii-text`
3. **injection_gate** (processor) → `processor/prompt-injection-detector`
4. **grep_red_flags** (rule_pack) → `rule-pack/grep-construction-safety-flags`
5. **rag_against_osha** (rule_pack) → `rule-pack/hybrid-retrieval-policy`
6. **review_harness** (harness) → `harness/workplace-safety-incident-review`
7. **calibrate_severity** (processor) → `processor/severity-calibrator`
8. **citation_coverage** (processor) → `processor/citation-coverage`
9. **route_owner** (processor) → `processor/remediation-owner-router`
10. **escalate_human** (processor) → `processor/escalate-human-review`
11. **grade** (processor) → `processor/llm-judge`
12. **audit** (processor) → `processor/audit-trace-emitter`

### 2.2 Design specifications

- Lifecycle position: `api.review`
- Trust boundary: `external`
- Industry tags: construction, construction.safety, infrastructure
- Modality: text, structured

### 2.3 Computational resources and architecture


## 3. Information about the data and data governance

Data protection metadata not declared on the source manifest. Add a `data_protection:` block with DPV-aligned categories.

## 4. Risk management system

- NIST AI RMF controls referenced: —
- ISO/IEC 42001 controls: —

## 5. Monitoring, functioning and control of the AI system

Logging and audit trail: emit OpenLineage events per pipeline run (see `dist/openlineage/`) and `processor/audit-trace-emitter` outputs.

## 6. Description of changes

Version-controlled in git; see commit history. Hub manifests use semver; `superseded_by` and `deprecated_on` fields document changes.

## 7. Compliance instruments

- CycloneDX-ML 1.6 AIBOM: `dist/aibom/cyclonedx-ml.cdx.json`
- Hugging Face Model Card: `dist/hf/model_cards/.../README.md`
- Croissant 1.0 (for any backing datasets): `dist/croissant/`

## 8. Reference documentation

- Source manifest: in the hub catalog repo, search for the id above.
- JSON-LD `@context`: `/ns/context.jsonld`
- Hub specification: `taxonomy/SPEC.md`
