# IOC extraction GREP pack (file hashes / domains / IPs / URLs)

*rule-pack* · `rule-pack/grep-ioc-extraction` · v0.1.0 · beta

Extracts indicators-of-compromise from threat-intel reports,
incident write-ups, sandbox outputs. Output IOCs feed into
`pipeline/threat-intel-ioc-review` for verification + ATT&CK
TTP mapping.

| axis | value |
|---|---|
| industry | security, threat_intelligence |
| capability | extraction, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `md5_hash` | medium | ioc.hash.md5 | `\b[a-fA-F0-9]{32}\b` |
| `sha1_hash` | medium | ioc.hash.sha1 | `\b[a-fA-F0-9]{40}\b` |
| `sha256_hash` | high | ioc.hash.sha256 | `\b[a-fA-F0-9]{64}\b` |
| `ipv4_address` | medium | ioc.network.ipv4 | `(?<!\d)(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9...` |
| `defanged_ipv4` | medium | ioc.network.ipv4.defanged | `(?<!\w)(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\[\.\]){3}(?:25[0-5]|2[0-4]...` |
| `domain_with_tld` | medium | ioc.network.domain | `\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|net|org|io|co|ru...` |
| `defanged_domain` | medium | ioc.network.domain.defanged | `\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\[\.\][a-zA-Z0-9-]+)+\b` |
| `url_http` | medium | ioc.network.url | `https?://[^\s"<>]+` |
| `defanged_url` | medium | ioc.network.url.defanged | `hxxps?://[^\s"<>]+|https?\[://\]` |
| `registry_key` | medium | ioc.host.registry_key | `(?i)HK(LM|CU|CR|U|CC)\\[^\s"'<>]+` |
| `windows_mutex` | medium | ioc.host.mutex | `(?i)\bGlobal\\[a-zA-Z0-9_-]{8,}\b|\bLocal\\[a-zA-Z0-9_-]{8,}\b` |
| `cve_id` | high | ioc.vuln.cve | `CVE-(?:1999|2[0-9]{3})-\d{4,7}` |
| `mitre_technique_id` | medium | ioc.mitre.technique | `\bT\d{4}(?:\.\d{3})?\b` |
| `yara_rule_header` | medium | ioc.detection.yara | `(?i)\brule\s+[A-Za-z0-9_]+\s*\{` |
| `bitcoin_address` | medium | ioc.payment.btc_address | `\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b` |

