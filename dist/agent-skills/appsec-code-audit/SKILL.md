---
name: appsec-code-audit
description: CWE-cite-first AppSec audit harness for source-code review. Detects secrets-in-code
  + injection + crypto/auth weaknesses + describes attack vectors + proposes fixes.
when_to_use: Use when the user needs evaluation. Use when the user needs extraction.
  Use when the user needs verification. Use when the user needs reasoning. Particularly
  relevant for security. Particularly relevant for security.appsec. Particularly relevant
  for software.
---

# AppSec Code Audit harness

CWE-cite-first AppSec audit harness for source-code review. Detects
secrets-in-code + injection + crypto/auth weaknesses + describes
attack vectors + proposes fixes.

## Applied layers

- `persona`
- `privacy`
- `grep`
- `rag`
- `tools`

## code bundle → secrets+vuln GREP → CWE/OWASP citations → grade + fixes

*model_call:* `required`

**Steps**

1. structured-to-prose
2. PII / secrets redact
3. code-vulnerabilities GREP (29 CWE-cited rules)
4. RAG against OWASP Top 10 LLM + MITRE ATT&CK
5. judge against code-security-review rubric
6. propose concrete fixes (parameterized query, version bump, alternative library)
7. audit trace

**Verification**

- every finding cites CWE-ID + OWASP category + CVE (if applicable)
- attack vector + impact described (no 'looks unsafe')
- concrete proposed fix provided
- code smells separated from real vulnerabilities

## Privacy boundaries

- **raw_input**: stays local; production secrets must be redacted upstream
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/appsec-code-audit` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
