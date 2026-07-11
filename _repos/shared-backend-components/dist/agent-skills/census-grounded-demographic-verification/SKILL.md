---
name: census-grounded-demographic-verification
description: Given a demographic/economic claim about a US place (and optionally an
  address), resolve the geography, fetch the authoritative ACS figure, and return
  supports/contradicts/no-evidence with the figure and a citation.
when_to_use: 'Pipeline kind: verification.'
---

# Census-grounded demographic verification

Verifies a natural-language demographic/economic claim about a US place
against authoritative Census ACS data and returns supports / contradicts /
no-evidence with the exact figure and a citation.

Worked example of the public-data-grounding pattern: deterministic
standardization (address/place → FIPS) and an authoritative API call run
BEFORE the model; the model only judges the claim against the fetched figure.
Capability lift over a bare LLM: the answer carries a real, current,
cited number instead of a hallucinated one.

## Task

Given a demographic/economic claim about a US place (and optionally an
address), resolve the geography, fetch the authoritative ACS figure, and
return supports/contradicts/no-evidence with the figure and a citation.

## Steps

1. **geocode** — `tool` → `tool/us-census-geocoder-api` (when `$.inputs.place_or_address contains a street address`)
2. **resolve_geo** — `processor` → `processor/geo-fips-normalizer`
3. **fetch_acs** — `tool` → `tool/us-census-acs-api`
4. **judge_claim** — `processor` → `processor/llm-judge`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_pack**: knowledge-pack/us-census-api-reference

## Success criteria

- rubric `rubric/census-grounded-answer-quality` threshold 0.8

## Provenance

- Hub component: `pipeline/census-grounded-demographic-verification` v0.1.0
- License: `MIT`
- Industry: government, finance, cross_industry
- Full source manifest: see `references/manifest.yaml`
