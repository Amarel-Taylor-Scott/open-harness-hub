# Malformed anatomy detector (extra fingers / limbs / faces)

*tool* · `tool/malformed-anatomy-detector` · v0.1.0 · experimental

Flags the characteristic anatomical distortions of diffusion output: wrong
finger counts, extra/merged limbs, duplicated or warped faces. Returns the
detected defects and a pass/fail so the pipeline can reject or regenerate.

Capability lift: the generator itself does not know its hands are wrong; this
post-generation check (hand/pose landmark counting + an anomaly classifier)
catches the most common quality failure that makes generated images unusable.

| axis | value |
|---|---|
| industry | media, cross_industry |
| capability | classification, verification |
| modality | image |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



