---
name: code-review-with-risk-score
description: 'Given a diff (or file contents), produce: (1) a per-finding code-review
  comment list with file:line, (2) a numeric risk score 0-10 per finding, (3) cited
  rule (OWASP / CWE / MITRE) for each finding, (4) an overall diff verdict (approve
  / request-changes / block).'
when_to_use: 'Pipeline kind: review_code.'
---

# Code review with risk score

Full layered code-review pipeline. Composes:
  persona (senior engineer) →
  grep (secret-leak guards on the diff) →
  classifier (clinical-style red-flag screen for OWASP categories) →
  knowledge-pack (OWASP Top 10 for LLM Apps + MITRE ATT&CK as RAG) →
  tool (lint runner) →
  harness (text-safety-review with citation requirements) →
  rubric (per-claim severity scoring).

## Task

Given a diff (or file contents), produce: (1) a per-finding code-review
comment list with file:line, (2) a numeric risk score 0-10 per finding,
(3) cited rule (OWASP / CWE / MITRE) for each finding, (4) an overall
diff verdict (approve / request-changes / block).

## Steps

1. **grep_secrets_cloud** — `rule_pack` → `rule-pack/grep-cloud-secrets`
2. **grep_secrets_ai** — `rule_pack` → `rule-pack/grep-ai-vendor-keys`
3. **grep_secrets_vcs** — `rule_pack` → `rule-pack/grep-vcs-platform-pats`
4. **grep_private_keys** — `rule_pack` → `rule-pack/grep-private-key-blocks`
5. **retrieve_owasp_context** — `knowledge_pack` → `knowledge-pack/owasp-top-10-llm`
6. **retrieve_attack_context** — `knowledge_pack` → `knowledge-pack/mitre-attack-sample`
7. **review** — `harness` → `harness/text-safety-review`
8. **verify_citations** — `processor` → `processor/citation-coverage`

## Defaults

- **persona**: persona/code-consultant
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/owasp-top-10-llm`, `knowledge-pack/mitre-attack-sample`
- **rule_packs**: `rule-pack/grep-cloud-secrets`, `rule-pack/grep-ai-vendor-keys`, `rule-pack/grep-vcs-platform-pats`, `rule-pack/grep-private-key-blocks`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/clinical-grounded-response-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/code-review-with-risk-score` v0.1.0
- License: `MIT`
- Industry: software, software.codereview, security
- Full source manifest: see `references/manifest.yaml`
