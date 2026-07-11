# AppSec Code Audit harness

*harness* · `harness/appsec-code-audit` · v0.1.0 · beta

CWE-cite-first AppSec audit harness for source-code review. Detects
secrets-in-code + injection + crypto/auth weaknesses + describes
attack vectors + proposes fixes.

| axis | value |
|---|---|
| industry | security, security.appsec, software |
| capability | evaluation, extraction, verification, reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/code-security-review`, `pipeline/full-vendor-due-diligence`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### code bundle → secrets+vuln GREP → CWE/OWASP citations → grade + fixes  
*model_call: `required`*

1. structured-to-prose
1. PII / secrets redact
1. code-vulnerabilities GREP (29 CWE-cited rules)
1. RAG against OWASP Top 10 LLM + MITRE ATT&CK
1. judge against code-security-review rubric
1. propose concrete fixes (parameterized query, version bump, alternative library)
1. audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`

**verification:** every finding cites CWE-ID + OWASP category + CVE (if applicable), attack vector + impact described (no 'looks unsafe'), concrete proposed fix provided, code smells separated from real vulnerabilities



## Privacy boundaries

- **raw_input**: stays local; production secrets must be redacted upstream
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

