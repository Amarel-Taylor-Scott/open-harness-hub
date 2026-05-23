# Differential Diagnosis

*pipeline* · `pipeline/differential-diagnosis` · v0.1.0 · experimental

Educational decision-support pipeline. Given (presentation, history,
exam) text, returns a ranked differential diagnosis with cited
guideline sections, ICD-10 code candidates, and red-flag
escalation. PHI is redacted before any model call.

Not a substitute for a licensed clinician. Intended as a
reproducible reference instance for the catalog.

| axis | value |
|---|---|
| industry | healthcare, healthcare.clinical |
| capability | reasoning, retrieval, tool_use, safety_gating |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a clinical vignette (presentation, history, exam), produce a
PHI-safe, cite-or-omit differential diagnosis with red-flag
escalation and ICD-10 code candidates.

**pipeline_kind:** `classify`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_phi` | harness | `harness/redact-pii-text` | — |
| 2 | `red_flag_screen` | rule_pack | `rule-pack/clinical-red-flags` | — |
| 3 | `retrieve_guidelines` | knowledge_pack | `knowledge-pack/clinical-guidelines-sample` | — |
| 4 | `lookup_codes` | tool | `tool/lookup-icd10` | — |
| 5 | `reason` | harness | `harness/clinical-decision-support` | — |

## Sample runs

### chest-pain-vignette
```json
{
  "pipeline": "pipeline/differential-diagnosis",
  "scenario": "chest-pain-vignette",
  "_synthetic_note": "Composite vignette. Not a real patient. PHI placeholders only.",
  "inputs": {
    "presentation": "Adult with crushing substernal chest pain radiating to left arm, onset 45 minutes ago, diaphoresis.",
    "history": "Hypertension, dyslipidemia, family history of premature coronary disease.",
    "exam": "BP 162/98, HR 104, SpO2 96% RA. Diaphoretic. No murmurs. No focal neuro deficits."
  },
  "trace": [
    {
      "step_id": "redact_phi",
      "kind": "harness",
      "ref": "harness/redact-pii-text",
      "input": {
        "text": "Adult with crushing substernal chest pain radiating to left arm, onset 45 minutes ago, diaphoresis."
      },
      "output": {
        "redacted_text": "Adult with crushing substernal chest pain radiating to left arm, onset 45 minutes ago, diaphoresis.",
        "audit": []
      },
      "ms": 6,
      "simulated": false
    },
    {
      "step_id": "red_flag_screen",
      "kind": "rule_pack",
      "ref": "rule-pack/clinical-red-flags",
      "input": {
        "text": "Adult with crushing substernal chest pain radiating to left arm, onset 45 minutes ago, diaphoresis."
      },
      "output": {
        "fired": [
          {
            "rule_id": "chest_pain_with_radiation",
            "severity": "critical"
          }
        ],
        "pack": "rule-pack/clinical-red-flags"
      },
      "ms": 4,
      "simulated": false
    },
    {
      "step_id": "retrieve_guidelines",
      "kind": "knowledge_pack",
      "ref": "knowledge-pack/clinical-guidelines-sample",
      "input": {
        "query": "crushing substernal chest pain radiating to left arm",
        "top_k": 6
      },
      "output": {
        "docs": [
          {
            "id": "acs-acc-aha-2026-\u00a73.1",
            "score": 0.93,
            "text": "Patients presenting with chest pain suggestive of acute coronary syndrome should receive an ECG within 10 minutes of arrival and troponin testing per institutional protocol. Risk stratification follows the HEART score; admit pathways are defined for high-risk strata."
          },
          {
            "id": "acs-acc-aha-2026-\u00a73.2",
            "score": 0.87,
            "text": "STEMI activation requires ST-segment elevation \u22651 mm in two contiguous leads (\u22652 mm in V2\u2013V3) on ECG. Door-to-balloon time goal is 90 minutes for percutaneous coronary intervention."
          }
        ]
      },
      "ms": 22,
      "simulated": false
    },
    {
      "step_id": "lookup_codes",
      "kind": "tool",
      "ref": "tool/lookup-icd10",
      "input": {
        "query": "myocardial chest pain",
        "max": 8
      },
      "output": {
        "matches": [
          {
            "code": "I21.9",
            "label": "Acute myocardial infarction, unspecified",
            "category": "cardiovascular"
          },
          {
            "code": "I71.0",
            "label": "Dissection of aorta",
            "category": "cardiovascular"
          },
          {
            "code": "I26.9",
            "label": "Pulmonary embolism without acute cor pulmonale",
            "category": "cardiovascular"
          },
          {
            "code": "R10.9",
            "label": "Unspecified abdominal pain",
            "category": "symptom"
          }
        ]
      },
      "ms": 18,
      "simulated": false
    },
    {
      "step_id": "reason",
      "kind": "harness",
      "ref": "harness/clinical-decision-support",
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "Produce a ranked differential with cited guideline sections; surface any red flag in the first sentence."
          }
        ]
      },
      "output": {
        "red_flag": "Chest pain with radiation to left arm in an adult with cardiovascular risk factors \u2014 possible acute coronary syndrome; recommend emergent ECG within 10 minutes and troponin per ACC/AHA ACS 2026 \u00a73.1.",
        "differentials": [
          {
            "icd10": "I21.9",
            "label": "Acute myocardial infarction, unspecified",
            "prior": 0.55,
            "supports": [
              "radiation to left arm",
              "diaphoresis",
              "risk factors"
            ],
            "argues_against": [
              "normal SpO2"
            ],
            "citations": [
              "acs-acc-aha-2026-\u00a73.1",
              "acs-acc-aha-2026-\u00a73.2"
            ]
          },
          {
            "icd10": "I71.0",
            "label": "Dissection of aorta",
            "prior": 0.1,
            "supports": [
              "radiation"
            ],
            "argues_against": [
              "pain quality is crushing, not tearing"
            ],
            "citations": []
          },
          {
            "icd10": "I26.9",
            "label": "Pulmonary embolism",
            "prior": 0.08,
            "supports": [
              "chest pain"
            ],
            "argues_against": [
              "no dyspnea reported"
            ],
            "citations": []
          }
        ],
        "next_steps": [
          "Emergent 12-lead ECG within 10 minutes (ACC/AHA ACS 2026 \u00a73.1).",
          "Serial troponin per institutional protocol.",
          "Continuous cardiac monitoring.",
          "If STEMI criteria met \u2192 activate cath lab; door-to-balloon goal 90 min (ACC/AHA ACS 2026 \u00a73.2)."
        ],
        "citations": [
          "acs-acc-aha-2026-\u00a73.1",
          "acs-acc-aha-2026-\u00a73.2"
        ]
      },
      "ms": 1240,
      "simulated": false
    }
  ],
  "output": {
    "red_flag": "Chest pain with radiation to left arm \u2014 possible ACS; recommend emergent ECG and troponin.",
    "differentials": [
      {
        "icd10": "I21.9",
        "prior": 0.55,
        "label": "Acute MI, unspecified"
      },
      {
        "icd10": "I71.0",
        "prior": 0.1,
        "label": "Aortic dissection"
      },
      {
        "icd10": "I26.9",
        "prior": 0.08,
        "label": "Pulmonary embolism"
      }
    ],
    "next_steps": [
      "ECG within 10 min",
      "Serial troponin",
      "Cardiac monitoring",
      "Cath lab if STEMI"
    ],
    "citations": [
      "acs-acc-aha-2026-\u00a73.1",
      "acs-acc-aha-2026-\u00a73.2"
    ]
  },
  "model": "ollama/llama3.1:8b",
  "frozen_at": "2026-05-19T13:00:00Z",
  "license": "MIT"
}
```