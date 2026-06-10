---
name: deep-research-with-citations
description: 'Given a user query, produce a one-page sourced synthesis: (1) decompose
  into sub-questions, (2) PII-sanitize each sub-query, (3) search across allowlisted
  sources, (4) verify each source''s relevance + credibility, (5) compose a cited
  answer with confidence intervals per claim.'
when_to_use: 'Pipeline kind: research_web.'
---

# Deep research with citations

The "deep research" pattern popularized by Perplexity and the
Anthropic orchestrator-workers cookbook. Fully layered:
  redact (PII out before external search) →
  persona (research analyst) →
  plan (LLM decomposes into sub-queries) →
  online-search rule pack (allowlist + sanitize) →
  tool (web-search) →
  rule pack (post-search verification — relevance + credibility) →
  harness (text-safety-review composes cited synthesis) →
  processor (citation-coverage verifier on output).

## Task

Given a user query, produce a one-page sourced synthesis: (1) decompose
into sub-questions, (2) PII-sanitize each sub-query, (3) search across
allowlisted sources, (4) verify each source's relevance + credibility,
(5) compose a cited answer with confidence intervals per claim.

## Steps

1. **redact_query** — `harness` → `harness/redact-pii-text`
2. **expand_abbreviations** — `knowledge_pack` → `knowledge-pack/common-abbreviations`
3. **plan_subqueries** — `harness` → `harness/text-safety-review`
4. **sanitize_search_queries** — `rule_pack` → `rule-pack/web-search-allowlist-default`
5. **search_sources** — `tool` → `tool/web-search`
6. **guard_retrieved_content** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
7. **verify_sources** — `harness` → `harness/text-safety-review`
8. **synthesize** — `harness` → `harness/text-safety-review`
9. **verify_citation_coverage** — `processor` → `processor/citation-coverage`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/common-abbreviations`, `knowledge-pack/iso-country-codes`
- **rule_packs**: `rule-pack/privacy-pii-text-en`, `rule-pack/web-search-allowlist-default`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.75

## Provenance

- Hub artifact: `pipeline/deep-research-with-citations` v0.1.0
- License: `MIT`
- Industry: cross_industry, media
- Full source manifest: see `references/manifest.yaml`
