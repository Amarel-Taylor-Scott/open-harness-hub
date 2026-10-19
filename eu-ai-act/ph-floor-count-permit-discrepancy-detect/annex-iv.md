# Annex IV technical documentation — PH floor-count / permit discrepancy detector (PD 1096)

> Generated from Open Harness Hub manifest `pipeline/ph-floor-count-permit-discrepancy-detect` v0.1.0. EU AI Act Regulation 2024/1689, Annex IV.

## 1. General description of the AI system

- **Name**: PH floor-count / permit discrepancy detector (PD 1096)
- **Provider**: Open Harness Hub contributors
- **Intended purpose**: Defensive detection + routing for Philippine building-permit violations,
grounded in the PH building-safety source registry
(data/source-registry/ph-building-safety.json) and the Angeles City collapse
fixture. Given a building case packet (address, reported as-built floor
count, permit-record fields obtained by a human router from the LGU Office
of the Building Official, PRC license number on the permit, Certificate of
Occupancy and Fire Safety Inspection Certificate status), the pipeline flags:
approved-floor-count vs reported-floor-count excess, missing PRC-licensed
structural-engineer sign-off, occupied-without-Certificate-of-Occupancy, and
missing/expired FSIC — then routes each flag to the correct authority (OBO,
DPWH Regional Office, PRC, BFP) with PD 1096 / RA 9514 citations.

This is a High-precision legal RAG bundle (Bundle B): an exact-id + dense leg
over the National Building Permit / Occupancy corpus, official-source
verification of every retrieved clause, per-claim citation coverage, and a
hard abstain gate. The dispositive as-built floor count is tier-5
(human-on-site) and the approved floor count is tier-4 (OBO counter record);
when the approved count is not human-verified the pipeline MUST emit
PERMIT_RECORD_UNVERIFIABLE and route to a human rather than infer a number
from the model. No evasion guidance; detection and routing with citations
only; no occupant/worker/owner PII stored.
- **Version**: 0.1.0
- **EU AI Act risk classification**: `high_risk`

## 2. Detailed description of the elements

### 2.1 Methods and steps used to develop the system

Pipeline composed of:

1. **structured_to_prose** (processor) → `processor/structured-to-prose`
2. **redact_pii** (processor) → `processor/redact-pii-text`
3. **injection_gate** (processor) → `processor/prompt-injection-detector`
4. **normalize_evidence** (processor) → `processor/packet-evidence-normalizer`
5. **grep_flags** (rule_pack) → `rule-pack/grep-building-code-inspection-flags`
6. **retrieve_code** (rule_pack) → `rule-pack/rag-building-code-inspection-retrieval-policy`
7. **verify_sources** (processor) → `processor/official-sources-checker`
8. **review_harness** (harness) → `harness/building-code-inspection-review`
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
