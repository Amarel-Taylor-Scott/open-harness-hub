# Candidate Primitive Promotion Scoring

Object factories should not promote every generated object. A candidate primitive needs enough usefulness, demand, verifiability, deployment value, and capability-gap value to justify curation. It also needs acceptable privacy, license, dedupe, and review risk.

Promotion scoring turns high-volume candidate JSONL into reviewable decisions:

```text
candidate normalized objects
-> promotion score
-> quality index record
-> review ticket or promotion queue
-> curated manifest or retained JSONL candidate
```

## Criteria

The default score follows the project priority formula:

```text
usefulness
x demand
x complexity
x time_savings
x frequency_of_deployment
x not_solved_by_out_of_box_llms
x cost_savings
x deployment_management_value
x model_swap_value
```

It also accounts for capability-gap signals:

```text
verifiability x training_attention_gap x data_coverage_gap x economic_value
```

## Promotion Decisions

- `promote_candidate`: strong score with no blocking review reason.
- `review_before_promotion`: useful candidate with privacy, license, dedupe, or domain review needs.
- `hold`: weak or incomplete candidate that may improve with more evidence.
- `reject`: low-value or high-risk candidate.

Marketplace-derived, job-derived, regulatory, medical, financial, child-safety, security, and automated-deployment candidates should usually route to review even when their score is high.

## Outputs

Promotion scoring should emit:

- `promotion-decision` records;
- quality/facet index records;
- review tickets;
- recommended downstream outputs such as pipeline candidates, rubric candidates, tool/harness candidates, or cost-model candidates.

This keeps the one-million-object path useful: high-volume generation can continue, but curation attention moves to the candidates most likely to become reliable reusable primitives.
