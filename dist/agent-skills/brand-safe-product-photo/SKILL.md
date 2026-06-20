---
name: brand-safe-product-photo
description: Given a product brief (name, category, brand tone, optional reference
  image), produce a cinematic product photo prompt + image that obeys brand-safety
  rules and produces verifiable lens physics.
when_to_use: 'Pipeline kind: generate_image.'
---

# Brand-Safe Product Photo

Image-generation pipeline that composes a cinematic-photography
persona, style-reference RAG, lens-physics RAG, GREP guard rules,
a tool call to a text-to-image model, and an output-safety review.
Demonstrates that image-gen is a normal citizen of the catalog: it
uses the same primitives as a text pipeline.

## Task

Given a product brief (name, category, brand tone, optional reference
image), produce a cinematic product photo prompt + image that obeys
brand-safety rules and produces verifiable lens physics.

## Steps

1. **guard_input** — `rule_pack` → `rule-pack/grep-prohibited-terms`
2. **retrieve_style** — `knowledge_pack` → `knowledge-pack/style-references-cinematic`
3. **retrieve_physics** — `knowledge_pack` → `knowledge-pack/lens-physics-primers`
4. **shape_prompt** — `harness` → `harness/text-safety-review`
5. **txt2img** — `tool` → `tool/txt2img-sdxl`
6. **review_output** — `rule_pack` → `rule-pack/grep-output-safety-image`

## Defaults

- **persona**: persona/cinematic-product-photographer
- **model_adapter**: adapter/sdxl-local

## Success criteria

- rubric `rubric/brand-safe-image-v1` threshold 0.8

## Provenance

- Hub artifact: `pipeline/brand-safe-product-photo` v0.1.0
- License: `MIT`
- Industry: creative, retail
- Full source manifest: see `references/manifest.yaml`
