# WHO syndromic surveillance case definitions and outbreak thresholds (offline)

*knowledge-pack* · `knowledge-pack/syndromic-surveillance-case-definitions` · v0.1.0 · beta

Offline Knowledge Corpus of public-domain WHO syndromic surveillance case
definitions covering: acute watery diarrhoea (cholera), acute respiratory
illness (ARI/ILI), meningitis syndrome, acute haemorrhagic fever, acute
jaundice, severe acute malnutrition (SAM), and measles-like rash illness.
Each entry includes the WHO IDSR (Integrated Disease Surveillance and
Response) or EWARN alert threshold, the minimum case definition criteria,
and the escalation tier (Green/Yellow/Red) used by the AfyaEdge triage
pattern.

DEFENSIVE INGESTION CONTRACT:
- All content sourced from public-domain WHO IDSR 3rd edition and WHO
  EWARN field guides; no novel clinical criteria are generated.
- This corpus is a decision-SUPPORT reference only. It does NOT replace
  clinical diagnosis or official epidemiological investigation.
- Every harness consuming this pack MUST surface the disclaimer:
  "These are surveillance thresholds for triage support only — always
  confirm with a trained health officer and escalate to MoH as required."
- Alert thresholds may be superseded by in-country MoH guidance; treat
  this corpus as a baseline pending local calibration.
- Volatile facts (active outbreak status, local MoH contacts) are
  excluded; only stable syndromic definitions and baseline thresholds
  are included.

CAPABILITY LIFT (structural): in remote/low-resource community health
settings, network connectivity is absent or unreliable. Field health
workers cannot query WHO servers mid-consultation. This corpus encodes
the stable syndromic decision rules so the on-device triage assistant
can function when cloud retrieval is impossible.
lift_reason: no_addressable_source (network unavailable in the field);
mechanism: context_length (no model can reliably recall all IDSR
thresholds at inference time without retrieval).

| axis | value |
|---|---|
| industry | healthcare.public_health, public_safety, government.regulatory, cross_industry |
| capability | retrieval, safety, classification |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | CC-BY-4.0 |



