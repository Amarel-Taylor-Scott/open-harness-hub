# Image aesthetic & technical quality scorer

*tool* · `tool/image-aesthetic-quality-scorer` · v0.1.0 · experimental

Scores a generated image for aesthetic quality and flags technical defects
(blur, JPEG/compression artifacts, low contrast, watermark/text bleed) so a
pipeline can keep only the best of N candidates.

Capability lift: turns "generate and hope" into "generate N, keep the best" —
a measurable selection gate the generator cannot apply to itself.

| axis | value |
|---|---|
| industry | media, cross_industry |
| capability | classification, evaluation |
| modality | image |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



