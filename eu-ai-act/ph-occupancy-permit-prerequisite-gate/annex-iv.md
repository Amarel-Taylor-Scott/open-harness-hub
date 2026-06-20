# Annex IV technical documentation — PH Certificate-of-Occupancy prerequisite gate

> Generated from Open Harness Hub manifest `pipeline/ph-occupancy-permit-prerequisite-gate` v0.1.0. EU AI Act Regulation 2024/1689, Annex IV.

## 1. General description of the AI system

- **Name**: PH Certificate-of-Occupancy prerequisite gate
- **Provider**: Open Harness Hub contributors
- **Intended purpose**: A yes/no occupancy-readiness gate for a Philippine building before a
Certificate of Occupancy (CO) can issue under PD 1096 Sec. 307. It checks
that every statutory prerequisite is present and currently valid: the
Fire Safety Inspection Certificate (FSIC) under RA 9514, the licensed
structural / architectural sign-off recorded on the building permit, and
the final building inspection record — then returns OCCUPANCY_READY or
NOT_READY with the specific missing/expired prerequisite and a citation,
routing each gap to the responsible authority (OBO, BFP).

High-precision legal RAG bundle (Bundle B): a dense + exact-id leg over the
national permit/occupancy corpus, official-source verification of each
retrieved clause, per-claim citation coverage, and a hard abstain. Because
FSIC status (BFP) and the OBO inspection record are tier-4 (counter-only),
any prerequisite whose status is not human-verified forces a NOT_READY +
PERMIT_RECORD_UNVERIFIABLE route to a human — the gate never infers a
"probably issued" CO. Detection and routing with citations only; no
occupant PII.
- **Version**: 0.1.0
- **EU AI Act risk classification**: `high_risk`

## 2. Detailed description of the elements

### 2.1 Methods and steps used to develop the system

Pipeline composed of:

1. **structured_to_prose** (processor) → `processor/structured-to-prose`
2. **redact_pii** (processor) → `processor/redact-pii-text`
3. **injection_gate** (processor) → `processor/prompt-injection-detector`
4. **normalize_evidence** (processor) → `processor/packet-evidence-normalizer`
5. **grep_flags** (rule_pack) → `rule-pack/grep-municipal-permit-review-flags`
6. **retrieve_prereqs** (rule_pack) → `rule-pack/rag-municipal-permit-review-retrieval-policy`
7. **verify_sources** (processor) → `processor/official-sources-checker`
8. **gate_harness** (harness) → `harness/municipal-permit-review-review`
9. **dedupe_findings** (processor) → `processor/finding-deduplicator`
10. **calibrate_severity** (processor) → `processor/severity-calibrator`
11. **citation_coverage** (processor) → `processor/citation-coverage`
12. **route_owner** (processor) → `processor/remediation-owner-router`
13. **escalate_human** (processor) → `processor/escalate-human-review`
14. **redaction_audit** (processor) → `processor/packet-redaction-audit`
15. **grade** (processor) → `processor/llm-judge`
16. **audit** (processor) → `processor/audit-trace-emitter`

### 2.2 Design specifications

- Lifecycle position: `api.review`
- Trust boundary: `external`
- Industry tags: construction.permitting, government.permitting, infrastructure
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
