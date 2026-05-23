# MITRE ATT&CK technique mapper

*tool* · `tool/mitre-attack-mapper` · v0.1.0 · stable

Map free-text TTPs to MITRE ATT&CK technique IDs (T1234.xxx).
Returns the matched technique + tactic + sub-techniques + KEV
status if any associated CVE is on the CISA Known Exploited
Vulnerabilities catalog.

Uses the latest ATT&CK Enterprise matrix snapshot bundled at
knowledge-pack/mitre-attack-sample. For live ATT&CK STIX feed,
configure `mitre_navigator_endpoint` env var.

| axis | value |
|---|---|
| industry | security, threat_intelligence, threat_intelligence.ttp |
| capability | verification, extraction |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



