---
name: code-security-review
description: Given source code (string OR structured dict with multiple files), identify
  CWE-cited vulnerabilities + hardcoded secrets + license issues + propose fixes.
  Score against the rubric.
when_to_use: 'Pipeline kind: review.'
---

# Code security review (CWE-cite-first AppSec audit)

Review source code against `rubric/code-security-review-v1`. Uses
the SAME chain shape as ESG / radiology / contract review:
structured-to-prose → secrets-redact → GREP (vuln + secrets) → RAG
against OWASP / CWE → judge → audit.

Fourth vertical proving the architecture is industry-agnostic.

## Task

Given source code (string OR structured dict with multiple files),
identify CWE-cited vulnerabilities + hardcoded secrets + license
issues + propose fixes. Score against the rubric.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_vulnerabilities** — `rule_pack` → `rule-pack/grep-code-vulnerabilities`
4. **rag_against_owasp** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/security-engineer-cite-first
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-code-vulnerabilities`
- **knowledge_packs**: `knowledge-pack/owasp-top-10-llm`

## Success criteria

- deterministic `$.steps.grep_vulnerabilities.output.hit_count` <= `30`
- composite `OR` over 2 child criteria

## Provenance

- Hub component: `pipeline/code-security-review` v0.1.0
- License: `MIT`
- Industry: security, security.appsec, software, software.codereview
- Full source manifest: see `references/manifest.yaml`
