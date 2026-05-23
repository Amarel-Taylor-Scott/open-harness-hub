# Threat-intel IOC + TTP review (MITRE ATT&CK aligned)

*pipeline* · `pipeline/threat-intel-ioc-review` · v0.1.0 · experimental

Ingest a CTI report or incident write-up, extract IOCs + TTPs,
validate against MITRE ATT&CK, rate confidence, surface
attribution risk. Seventh vertical proving industry-agnosticism.

| axis | value |
|---|---|
| industry | security, threat_intelligence |
| capability | extraction, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a CTI report (text + sandbox output), extract IOCs by type,
map TTPs to ATT&CK techniques, rate confidence, flag attribution
concerns.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_iocs` | rule_pack | `rule-pack/grep-ioc-extraction` | — |
| 4 | `rag_against_attack` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

