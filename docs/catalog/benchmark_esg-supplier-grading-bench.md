# ESG supplier-grading benchmark v1

*benchmark* · `benchmark/esg-supplier-grading-bench` · v0.1.0 · experimental

Runs `pipeline/supplier-policy-grading` against the synthetic
supplier disclosure pack test set (3 representative cases: a well-
disclosed T1 tech supplier; a T3 textile supplier in Mae Sot with
forced-labor + corridor red flags; a T2 Paraguay soy supplier with
mixed signals — strong S, weak E around deforestation).

Scores under `rubric/esg-supplier-compliance-v1` and reports per-
dimension breakdown so reviewers can see WHERE a model arm
succeeds vs fails (E vs S vs G vs cross-cutting), not just the
headline weighted-sum.

Used as a regression gate for the ESG vertical: any change to
rule-pack/grep-esg-* or the persona must keep headline metric
within ±0.05 of baseline.

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



