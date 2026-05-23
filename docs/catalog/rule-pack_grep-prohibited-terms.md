# Prohibited Terms (image-gen guard rails)

*rule-pack* · `rule-pack/grep-prohibited-terms` · v0.1.0 · beta

GREP guard rail for image-generation pipelines. Blocks prompts that
reference real celebrities by name, real trademarks, hate slurs, or
explicit sexual content. Severity drives the pipeline's refusal vs
rewrite branch.

| axis | value |
|---|---|
| industry | creative, media |
| capability | safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `celebrity_name_marker` | high | ip.celebrity_likeness | `(?i)in the (style|likeness) of [A-Z][a-z]+ [A-Z][a-z]+` |
| `trademark_logo` | high | ip.trademark | `(?i)\b(nike|adidas|coca[- ]cola|disney|marvel|apple|google)\b.*\b(logo|swoosh...` |
| `explicit_sexual` | critical | content.sexual | `(?i)\b(nude|naked|nsfw|porn|explicit sexual)\b` |
| `hate_slur_placeholder` | critical | content.hate | `(?i)\b(<hate-slur-placeholder>)\b` |

