# Guarded image generation (screen → generate → filter → select)

*pipeline* · `pipeline/guarded-image-generation` · v0.1.0 · experimental

End-to-end image generation with safety and quality guards composed from
existing components — the multi-component shape a registry can propose that a
blank-canvas builder cannot: screen the prompt, generate with a local model,
filter illicit content, reject anatomical distortions (6 fingers, extra
limbs), and keep only images above an aesthetic/technical bar.

Capability lift: a raw text-to-image model has no prompt policy, no content
filter, and no distortion check. This pipeline adds all three around it, so
the delivered image is safe, anatomically sane, and the best of N candidates.
Swap the generator via the adapter (Flux/SDXL/hosted) without changing the guards.

| axis | value |
|---|---|
| industry | media, security, cross_industry |
| capability | image_synthesis, safety_gating, evaluation |
| modality | image, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given an image prompt (and optional style/rules), generate candidate images,
block illicit prompts/outputs, reject anatomically distorted results, and
return the highest-quality safe image with a safety/quality trace.

**pipeline_kind:** `generate_image`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `screen_prompt` | tool | `tool/image-prompt-safety-screen` | - |
| 2 | `generate` | adapter | `adapter/flux-1-schnell-local` | $.steps.screen_prompt.output.allow == true |
| 3 | `filter_nsfw` | tool | `tool/nudenet-nsfw-image-filter` | - |
| 4 | `filter_anatomy` | tool | `tool/malformed-anatomy-detector` | - |
| 5 | `select_best` | tool | `tool/image-aesthetic-quality-scorer` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

