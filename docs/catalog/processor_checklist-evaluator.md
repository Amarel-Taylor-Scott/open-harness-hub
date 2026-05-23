# Checklist evaluator (GO/NO-GO)

*processor* · `processor/checklist-evaluator` · v0.1.0 · beta

Reads a named procedural checklist (knowledge-pack/technician-checklists record) plus a candidate input, returns per-item disposition (verified|unverified|nogo) + overall verdict (go|nogo). NO-GO triggers override otherwise-clean inputs.

| axis | value |
|---|---|
| industry | compliance, healthcare, aviation, energy, construction |
| capability | safety_gating, evaluation, extraction |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



