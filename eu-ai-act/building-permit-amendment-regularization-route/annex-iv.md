# Annex IV technical documentation — Building-permit amendment / regularization router (PH·ID·NG)

> Generated from Open Harness Hub manifest `pipeline/building-permit-amendment-regularization-route` v0.1.0. EU AI Act Regulation 2024/1689, Annex IV.

## 1. General description of the AI system

- **Name**: Building-permit amendment / regularization router (PH·ID·NG)
- **Provider**: Open Harness Hub contributors
- **Intended purpose**: Detect when reported as-built construction has materially deviated from the
approved building permit such that a revised/amended permit (a regularization
path) is legally required, then route the case to the jurisdiction-specific
authority with citations. Material-alteration definitions, the
added-story/added-use trigger, and the regularization workflow are
jurisdiction-specific and thinly represented online — exactly the
low-digitization valley the national permit/occupancy corpus targets. The
pattern generalizes across PH (PD 1096 / LGU OBO), Indonesia (PBG via SIMBG,
PP 16/2021), and Nigeria (state building-control agencies, e.g. LASBCA);
only the corpus and routing targets change — the deviation logic and the
abstain gate are reusable.

Agentic / corrective-RAG bundle (Bundle D): a two-time retrieval refines the
query from "is this a material alteration?" toward the controlling clause,
official-source verification grades the retrieval, and a corrective human
escalation fires when the retrieval is weak or the approved scope is not
human-verified (tier-4 OBO/PUPR/state record). The router NEVER infers the
approved scope from the model; an unverifiable approved scope yields
PERMIT_RECORD_UNVERIFIABLE. Detection + routing + citations only; no PII; no
guidance on avoiding permits or inspection.
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
6. **retrieve_material_alteration** (processor) → `processor/two-time-retrieval`
7. **verify_sources** (processor) → `processor/official-sources-checker`
8. **decide_harness** (harness) → `harness/municipal-permit-review-review`
9. **calibrate_severity** (processor) → `processor/severity-calibrator`
10. **citation_coverage** (processor) → `processor/citation-coverage`
11. **route_owner** (processor) → `processor/remediation-owner-router`
12. **escalate_human** (processor) → `processor/escalate-human-review`
13. **redaction_audit** (processor) → `processor/packet-redaction-audit`
14. **grade** (processor) → `processor/llm-judge`
15. **audit** (processor) → `processor/audit-trace-emitter`

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
