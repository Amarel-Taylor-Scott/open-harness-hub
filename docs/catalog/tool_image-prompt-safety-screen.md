# Image prompt safety screen

*tool* · `tool/image-prompt-safety-screen` · v0.1.0 · experimental

Pre-generation guard: screens an image prompt for prohibited content/intent
(CSAM, non-consensual, targeted real individuals, weapons-making, etc.),
returns allow/block + the matched policy categories, and optionally a
sanitized rewrite. The deterministic gate that runs BEFORE any GPU cost.

Capability lift: blocks disallowed requests before generation, cutting both
risk and wasted compute — the generator has no policy of its own.

| axis | value |
|---|---|
| industry | media, security, cross_industry |
| capability | safety_gating, governance, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



