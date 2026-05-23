# Image-output safety checks

*rule-pack* · `rule-pack/grep-output-safety-image` · v0.1.0 · experimental

Post-generation safety check pack for image outputs. Pairs of
(detector-call, threshold) plus a watermark presence check. Designed
to be called by an image-gen pipeline AFTER the txt2img tool returns.

| axis | value |
|---|---|
| industry | creative, media |
| capability | safety_gating |
| modality | image |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



**family:** `heuristic`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `nsfw_classifier_threshold` | critical | — | `nsfw_classifier(image) < 0.10` |
| `celebrity_face_match` | high | — | `celebrity_face_match(image, registry='public_celebrities') == false` |
| `watermark_present` | medium | — | `watermark_detector(image, brand=$.context.brand) == true` |

