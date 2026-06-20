---
name: sdg-alignment-assessment
description: Given a policy / program / project / investment description and optional
  geography + time-horizon hints, produce a per-claim SDG alignment assessment with
  target/indicator citations, counter- target risks, additionality discussion, and
  a rubric grade against `rubric/sdg-alignment-v1`.
when_to_use: 'Pipeline kind: grading.'
---

# UN SDG alignment-claim assessment

End-to-end pipeline that takes a policy / program / project /
investment description and produces a per-claim SDG alignment
assessment with target + indicator citations, counter-target
risks, additionality discussion, and a quality grade.

Use cases:
 - Corporate CSRD ESRS optional SDG mapping disclosure review
 - GRI SDG-mapping disclosure review
 - Impact-investor (IFC, GIIN, Acumen, BlueOrchard) due diligence
 - NGO theory-of-change review against SDG framework
 - Government budget tagging audit
 - Foundation grant-proposal SDG-alignment claim review

Output:
 - per-claim findings with SDG goal + target + indicator codes
 - alignment type (direct / indirect / enabling / symbolic /
   counter / misaligned)
 - counter-target risks
 - geographic + temporal fit assessment
 - additionality assessment
 - SDG-washing markers list
 - rubric score (rubric/sdg-alignment-v1)

## Task

Given a policy / program / project / investment description and
optional geography + time-horizon hints, produce a per-claim SDG
alignment assessment with target/indicator citations, counter-
target risks, additionality discussion, and a rubric grade
against `rubric/sdg-alignment-v1`.

## Steps

1. **normalize** — `processor` → `processor/structured-to-prose`
2. **classify_candidate_sdgs** — `rule_pack` → `rule-pack/classifier-sdg-mapping`
3. **rag_sdg_drilldown** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
4. **review** — `harness` → `harness/sdg-alignment-review`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/sdg-alignment-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/classifier-sdg-mapping`

## Success criteria

- rubric `rubric/sdg-alignment-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/sdg-alignment-assessment` v0.1.0
- License: `MIT`
- Industry: esg, sustainability, nonprofit, government, humanitarian
- Full source manifest: see `references/manifest.yaml`
