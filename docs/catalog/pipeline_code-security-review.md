# Code security review (CWE-cite-first AppSec audit)

*pipeline* · `pipeline/code-security-review` · v0.1.0 · experimental

Review source code against `rubric/code-security-review-v1`. Uses
the SAME chain shape as ESG / radiology / contract review:
structured-to-prose → secrets-redact → GREP (vuln + secrets) → RAG
against OWASP / CWE → judge → audit.

Fourth vertical proving the architecture is industry-agnostic.

| axis | value |
|---|---|
| industry | security, security.appsec, software, software.codereview |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given source code (string OR structured dict with multiple files),
identify CWE-cited vulnerabilities + hardcoded secrets + license
issues + propose fixes. Score against the rubric.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_vulnerabilities` | rule_pack | `rule-pack/grep-code-vulnerabilities` | — |
| 4 | `rag_against_owasp` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

