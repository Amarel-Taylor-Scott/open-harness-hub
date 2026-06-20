---
name: saas-launch-review
description: Wraps the SaaS launch review flow as a reusable harness. Reviews landing-page
  copy + tagline + pricing + demo materials against corpus norms and anti-pattern
  rules; produces per-aspect findings with severity, observation, corpus norm, and
  suggested rewrite.
when_to_use: Use when the user needs evaluation. Use when the user needs extraction.
  Use when the user needs reasoning. Particularly relevant for software. Particularly
  relevant for creative.
---

# SaaS launch landing-page review harness

Wraps the SaaS launch review flow as a reusable harness. Reviews
landing-page copy + tagline + pricing + demo materials against
corpus norms and anti-pattern rules; produces per-aspect findings
with severity, observation, corpus norm, and suggested rewrite.

## Applied layers

- `persona`
- `grep`
- `rag`
- `tools`

## landing page → anti-pattern flags → corpus-norm RAG → per-aspect grade + rewrites

*model_call:* `required`

**Steps**

1. extract tagline + ICP + feature list + pricing + demo info
2. fire SaaS-launch anti-pattern GREP pack
3. RAG against SaaS launch best-practices pack per aspect
4. judge per saas-launch-quality-v1 rubric
5. propose per-finding rewrites
6. emit audit trace

**Verification**

- every finding has aspect + severity + suggested rewrite
- every rewrite is at most 1 sentence longer than the original
- launch-day-blocker findings explicitly flagged

## Privacy boundaries

- **raw_input**: stays local; landing-page text is public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/saas-launch-review` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
