# Critical-tier output override (one dominant message on critical finding)

*pattern* · `pattern/critical-tier-output-override` · v0.1.0 · beta

When a classifier / judge step finds a critical-tier issue, every
user-facing output component is FORCED into one consistent message
rather than mixing the issue with the original task output. This
is architectural control over which message dominates the screen,
not a model decision.

Counters the "mixed message" failure mode: a single-stream LLM
generates "pay if the amount is correct" + "this might be a scam"
in the same response. A stressed user picks the more action-oriented
advice and gets defrauded. Architectural override forces ONE
dominant message.

Bill_info AI is the reference implementation: on `likely_scam`
classification, the urgency banner → red, recommendations → ["do
not pay", "verify via Verbraucherzentrale", "save as evidence"],
reply draft → empty. The user sees ONE coherent anti-scam screen.

Published in Sviatoslav Grabovsky's Bill_info AI (Gemma 4 Good
Hackathon).

| axis | value |
|---|---|
| industry | ai, cross_industry, bureaucracy_translation, humanitarian, compliance |
| capability | safety_gating, verification |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | CC-BY-4.0 |



