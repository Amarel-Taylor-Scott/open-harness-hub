---
name: codegraph-assisted-code-review
description: From the changed symbols in a pull request, retrieve their dependents
  from a local code graph and persist the review context to durable memory keyed by
  the PR.
when_to_use: 'Pipeline kind: devops.code_review_assist.'
---

# CodeGraph-assisted code review (DevOps)

Seed pipeline for the DevOps section. Given the changed symbols in a pull
request, pull their dependents from a local code knowledge graph (so the
reviewer/agent sees blast radius without reading the whole repo), then persist
that review context to durable memory keyed by the PR so it survives across
commits and sessions.

Composes two catalogued open-source tools — tool/codegraph-code-graph-query
and tool/agentmemory-persistent-memory — and is intentionally minimal: extend
it with a review harness (LLM risk summary) and a rubric/benchmark. Token-
efficient by construction (pairs with pattern/input-token-compression and
pattern/twelve-factor-agent).

## Task

From the changed symbols in a pull request, retrieve their dependents from a local code graph and persist the review context to durable memory keyed by the PR.

## Steps

1. **retrieve-impacted-symbols** — `tool` → `tool/codegraph-code-graph-query`
2. **persist-review-context** — `tool` → `tool/agentmemory-persistent-memory`

## Success criteria

- deterministic `$.retrieve-impacted-symbols.results` is_truthy `True`
- semantic must_cover ['review context', 'persisted', 'pull request'] against `$.persist-review-context`

## Provenance

- Hub component: `pipeline/codegraph-assisted-code-review` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
