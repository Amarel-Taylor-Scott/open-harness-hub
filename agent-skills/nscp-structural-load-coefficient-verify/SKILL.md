---
name: nscp-structural-load-coefficient-verify
description: Verify the edition-specific load-combination equations and load / phi
  / seismic-zone coefficients cited in a structural design submittal against the authoritative
  structural-design-code-constants corpus, by exact-id lookup, and flag any coefficient
  that does not match the claimed code edition — with a citation to the published
  table.
when_to_use: 'Pipeline kind: verify_data.'
---

# NSCP / ASCE 7 structural load-coefficient verifier

Verify the edition-specific numeric coefficients in a structural design
submittal (load-combination equations, importance / seismic-zone factors,
strength-reduction phi factors, allowable-stress increases) against an
authoritative constants corpus rather than the model's memory. Base models
confidently misquote these life-safety numbers because they blend
ASCE 7 / AISC 360 / ACI 318 / Eurocode / NSCP editions — a confident-wrong
failure that is deterministically checkable against the published tables.

This is a Cheap exact-id / keyword-first bundle (Bundle C) with a verify
spine: the structural-design-code-constants Knowledge Corpus is queried by
exact_id (e.g. "ASCE 7-22 load combo 2", "ACI 318 phi flexure", "NSCP 2015
seismic zone 4 Z"), every cited coefficient is checked for citation
coverage, and a deterministic gate requires that the submittal's numbers
match the edition the design claims. The pipeline does NOT perform the
structural-adequacy assessment itself — that is a tier-5 licensed-engineer
on-site act; it flags coefficient mismatches and routes them. Detection and
citation only; no PII.

## Task

Verify the edition-specific load-combination equations and load / phi / seismic-zone coefficients cited in a structural design submittal against the authoritative structural-design-code-constants corpus, by exact-id lookup, and flag any coefficient that does not match the claimed code edition — with a citation to the published table.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **injection_gate** — `processor` → `processor/prompt-injection-detector`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-building-code-inspection-flags`
4. **lookup_constants** — `processor` → `processor/two-time-retrieval`
5. **verify_sources** — `processor` → `processor/official-sources-checker`
6. **compare_harness** — `harness` → `harness/building-code-inspection-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **citation_coverage** — `processor` → `processor/citation-coverage`
10. **grade** — `processor` → `processor/llm-judge`
11. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/building-code-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/structural-design-code-constants`
- **rule_packs**: `rule-pack/grep-building-code-inspection-flags`

## Success criteria

- rubric `rubric/building-code-inspection-quality-v1` threshold 0.66
- deterministic `$.steps.injection_gate.output.allow` == `True`
- deterministic `$.steps.citation_coverage.output.passes` == `True`

## Provenance

- Hub component: `pipeline/nscp-structural-load-coefficient-verify` v0.1.0
- License: `MIT`
- Industry: construction.permitting, infrastructure, manufacturing
- Full source manifest: see `references/manifest.yaml`
