---
name: ph-occupancy-permit-prerequisite-gate
description: Decide whether a Philippine building is occupancy-ready by checking that
  the Certificate of Occupancy prerequisites (valid FSIC under RA 9514, licensed sign-off
  on permit, final inspection record) are present and unexpired; return OCCUPANCY_READY
  or NOT_READY with the missing prerequisite, a PD 1096 / RA 9514 citation, and a
  route to the responsible authority; abstain to a human when any prerequisite status
  is not human-verified.
when_to_use: 'Pipeline kind: evaluate.'
---

# PH Certificate-of-Occupancy prerequisite gate

A yes/no occupancy-readiness gate for a Philippine building before a
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

## Task

Decide whether a Philippine building is occupancy-ready by checking that the Certificate of Occupancy prerequisites (valid FSIC under RA 9514, licensed sign-off on permit, final inspection record) are present and unexpired; return OCCUPANCY_READY or NOT_READY with the missing prerequisite, a PD 1096 / RA 9514 citation, and a route to the responsible authority; abstain to a human when any prerequisite status is not human-verified.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **injection_gate** — `processor` → `processor/prompt-injection-detector`
4. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
5. **grep_flags** — `rule_pack` → `rule-pack/grep-municipal-permit-review-flags`
6. **retrieve_prereqs** — `rule_pack` → `rule-pack/rag-municipal-permit-review-retrieval-policy`
7. **verify_sources** — `processor` → `processor/official-sources-checker`
8. **gate_harness** — `harness` → `harness/municipal-permit-review-review`
9. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
10. **calibrate_severity** — `processor` → `processor/severity-calibrator`
11. **citation_coverage** — `processor` → `processor/citation-coverage`
12. **route_owner** — `processor` → `processor/remediation-owner-router`
13. **escalate_human** — `processor` → `processor/escalate-human-review`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **grade** — `processor` → `processor/llm-judge`
16. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/permit-review-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/national-building-permit-and-occupancy-procedures-low-digitization`, `knowledge-pack/municipal-permit-review-frameworks`
- **rule_packs**: `rule-pack/grep-municipal-permit-review-flags`, `rule-pack/rag-municipal-permit-review-retrieval-policy`

## Success criteria

- rubric `rubric/municipal-permit-review-quality-v1` threshold 0.68
- deterministic `$.steps.injection_gate.output.allow` == `True`
- deterministic `$.steps.citation_coverage.output.passes` == `True`
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/ph-occupancy-permit-prerequisite-gate` v0.1.0
- License: `MIT`
- Industry: construction.permitting, government.permitting, infrastructure
- Full source manifest: see `references/manifest.yaml`
