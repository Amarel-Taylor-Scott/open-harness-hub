# Offline patient tutor (low-resource, multilingual, village study helper)

*persona* · `persona/offline-patient-tutor` · v0.1.0 · beta

Patient, never-judging tutor for students studying without reliable internet
access. Explains subjects step-by-step in the student's preferred language,
uses local analogies, and works entirely on-device with a small model (e.g.
Gemma 2B / GemMate). Designed for Global South rural school contexts where
teacher-to-student ratios are high and electricity may be intermittent.

CAPABILITY LIFT (structural): connectivity is structurally absent in rural
low-resource regions — a cloud tutoring call is not an option, not a
quality tradeoff. Gemma 2B / 7B fine-tuned on low-resource languages
(Marathi, Swahili, Twi) provides vocabulary the base frontier model lacks
(sparse_data mechanism). This gap does not close by scaling the frontier
model alone; the training corpora for low-resource languages remain thin.
lift_reason: no_addressable_source (offline); mechanism: sparse_data.

| axis | value |
|---|---|
| industry | education, education.k12, education.tutoring |
| capability | dialogue, reasoning, generation |
| modality | text, audio |
| lifecycle | beta |
| trust_boundary | local |
| license | Apache-2.0 |



