# NudeNet NSFW image filter

*tool* · `tool/nudenet-nsfw-image-filter` · v0.1.0 · experimental

Classifies a generated image for explicit/illicit content and returns
per-class scores + a pass/block decision against a threshold. Wraps the
open-source NudeNet detector.

Capability lift: a diffusion model has no built-in content gate; this tool is
the post-generation safety filter that blocks illicit output before it
reaches a user. Source-governed — verify and propagate the upstream license of
the version you bundle.

| axis | value |
|---|---|
| industry | media, security, cross_industry |
| capability | classification, safety_gating, safety |
| modality | image |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



