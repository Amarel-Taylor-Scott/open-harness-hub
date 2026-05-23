# ESG governance red-flag detectors (the 'G' of ESG)

*rule-pack* · `rule-pack/grep-esg-governance-red-flags` · v0.1.0 · beta

GREP detectors for the governance dimension: beneficial-ownership
opacity, anti-bribery / corruption signals, whistleblower-channel
weaknesses, conflict-of-interest, board-independence gaps, audit-
trail integrity. Aligned to:
 - CSDDD Art. 26 (board oversight)
 - OECD Anti-Bribery Convention
 - UK Bribery Act 2010 §7 (failure-to-prevent)
 - US FCPA (anti-bribery + books-and-records)
 - EU Directive 2019/1937 (whistleblower protection)
 - Wolfsberg Anti-Bribery & Corruption Principles
 - ISO 37001 (anti-bribery management systems)

| axis | value |
|---|---|
| industry | esg, compliance, finance |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `beneficial_ownership_opaque` | high | governance.beneficial_ownership | `(?i)(ultimate beneficial owner|ubo|shareholder|owner)\s+(?:unknown|not disclo...` |
| `shell_jurisdiction` | medium | governance.opaque_jurisdiction | `(?i)(incorporat|register|domicile)\s+(?:in|at)\s+(?:cayman|bvi|british virgin...` |
| `facilitation_payment` | critical | governance.bribery | `(?i)(?<!prohibited\s)(?<!not\sallowed\s)(?<!against\spolicy\s)(?<!do\snot\spe...` |
| `third_party_agent_undisclosed` | high | governance.third_party_risk | `(?i)(third[- ]?party|local)\s+(?:agent|consultant|representative|intermediary...` |
| `conflict_of_interest_undisclosed` | high | governance.conflict_of_interest | `(?i)conflict[- ]?of[- ]?interest.*(?:not (?:disclosed|reported|declared)|undi...` |
| `whistleblower_retaliation` | critical | governance.whistleblower_retaliation | `(?i)(whistleblower|reporter|complainant)\s+(?:fired|dismissed|reassigned|demo...` |
| `no_grievance_mechanism` | high | governance.no_grievance_mechanism | `(?i)(no|absent|n[\.\/]a)\s+(?:grievance|complaint|whistleblower|reporting|eth...` |
| `board_independence_gap` | medium | governance.board_independence | `(?i)(no|zero|0)\s+independent\s+(?:director|board member)|board.*all (?:found...` |
| `audit_trail_gap` | high | governance.audit_trail | `(?i)(no|missing|not retained|destroyed|incomplete)\s+(?:audit trail|records|l...` |
| `tax_avoidance_transfer_pricing` | medium | governance.tax_planning | `(?i)(transfer pricing|royalty)\s+(?:dispute|aggressive|adjustment).*(?:>|over...` |
| `sanctions_listed_counterparty` | critical | governance.sanctions | `(?i)(ofac|un sanctions|eu sanctions|hmt sanctions|sdn list|consolidated list)...` |
| `pep_undisclosed` | high | governance.pep_screening | `(?i)(politically exposed person|pep)\s+(?:not (?:screened|disclosed)|undisclo...` |

