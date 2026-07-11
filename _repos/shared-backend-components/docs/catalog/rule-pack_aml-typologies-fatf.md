# FATF AML typologies (sampled)

*rule-pack* · `rule-pack/aml-typologies-fatf` · v0.1.0 · experimental

Classifier rules for common FATF-aligned AML typologies. Each rule
is a labeled-example bundle the AML harness uses to score a
transaction sequence against known patterns (structuring / smurfing,
layering through shell entities, trade-based laundering, etc.).
Reference for educational use; institutions should layer
jurisdiction-specific red flags on top.

| axis | value |
|---|---|
| industry | finance, finance.aml |
| capability | classification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | dated |
| license | MIT |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `structuring_under_threshold` | high | fatf.placement | `` |
| `layering_via_shell` | high | fatf.layering | `` |
| `trade_based_value_mismatch` | medium | fatf.tbml | `` |
| `high_risk_corridor` | medium | fatf.geographic | `` |
| `rapid_in_rapid_out` | medium | fatf.layering | `` |
| `round_dollar_pattern` | low | fatf.placement | `` |

