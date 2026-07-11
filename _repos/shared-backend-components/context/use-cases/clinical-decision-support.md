# Use case 5 - Clinical decision support

> Differential diagnosis with red-flag escalation, cited guidelines, and ICD-10 lookups. PHI-safe.

## When to use

- Clinician-facing decision support tools
- Triage assistant in low-resource settings
- Educational case-review tooling
- Medical-records-review for QA

## Primary pipeline

[`pipeline/differential-diagnosis`](../catalog/pipeline_differential-diagnosis.md)

## Primitives used

| Layer | Component |
|---|---|
| Privacy | `rule-pack/phi-hipaa-en` (HIPAA Safe-Harbor 18 identifiers) |
| Redact | `harness/redact-pii-text` |
| Classify | `rule-pack/clinical-red-flags` (ACS, stroke, SAH, anaphylaxis, OB emergency, psych crisis) |
| RAG | `knowledge-pack/clinical-guidelines-sample` |
| RAG | `knowledge-pack/icd10-sample` |
| RAG | `knowledge-pack/drug-interactions-sample` |
| Tool | `tool/lookup-icd10` |
| Persona | `persona/clinical-reasoner` (no Dx, no Rx, citation-first) |
| Harness | `harness/clinical-decision-support` |

## Composition

```
presentation + history + exam
  → redact-pii-text (HIPAA Safe Harbor)
  → clinical-red-flags screen   (output: red_flag if any fires)
  → IF red_flag: first sentence states it + recommends emergent eval
  → retrieve clinical-guidelines-sample (top-6)
  → lookup-icd10 (candidate codes)
  → clinical-decision-support harness (persona/clinical-reasoner)
  → ranked differential[], next_steps[], citations[]
```

## Sample inputs / outputs

```python
inputs = {
  "presentation": "Adult with crushing substernal chest pain radiating to left arm, onset 45 min ago, diaphoresis.",
  "history":      "HTN, dyslipidemia, FH premature CAD.",
  "exam":         "BP 162/98, HR 104, SpO2 96% RA. Diaphoretic."
}
# → red_flag: "Chest pain with radiation in adult with cardiovascular risk factors - possible ACS; recommend emergent ECG within 10 min and troponin per ACC/AHA ACS 2026 §3.1."
# → differentials:
#     [{ icd10: I21.9, prior: 0.55, supports: [...], argues_against: [...], citations: [acs-acc-aha-2026-§3.1, §3.2] },
#      { icd10: I71.0, prior: 0.10, ... },
#      { icd10: I26.9, prior: 0.08, ... }]
# → next_steps: [ECG in 10 min, serial troponin, monitoring, cath lab if STEMI]
```

## Install path

### Claude Code (educational, not for clinical deployment)

```
/plugin marketplace add Amarel-Taylor-Scott/openhubforai@dist-published
/differential-diagnosis
```

### On-prem clinical deployment (recommended)

This pipeline's defaults use `adapter/ollama-default` - local model only. **No PHI leaves the host**. For production:

1. Configure your local Gemma / Llama / DeepSeek on the EHR-network host.
2. Replace `knowledge-pack/clinical-guidelines-sample` with a licensed full corpus (ACC/AHA, NICE, RCP, WHO).
3. Replace `knowledge-pack/icd10-sample` with the full ICD-10 release (WHO licensing).
4. Set `data_protection.hipaa_safe_harbor_categories` on the pipeline manifest to enumerate every PHI category your input pipeline might see.
5. Wire the audit emitter to your hospital SIEM.

## Customization knobs

- **Add specialty packs**: write `knowledge-pack/cardiology-acc-aha`, `knowledge-pack/neurology-aha`, etc.
- **Add medication checking**: chain `knowledge-pack/drug-interactions-sample` into the harness for med-list review.
- **Stricter PHI gate**: enable `rule-pack/phi-hipaa-en` `severity: critical` rules to halt on any unredacted PHI.
- **External judge for QA**: add a final `processor/llm-judge` step using a frontier model - but only on the redacted output, never on raw PHI.

## Important disclaimer

This pipeline is intended for **educational decision support**, not as
a substitute for licensed clinical judgment. The persona refuses to
provide definitive diagnoses or prescribe medications. Surface red
flags in the FIRST sentence of every response.
