---
name: blip-clip-image-to-prompt
description: Given a Stable-Diffusion-generated image, recover an approximate prompt
  + verify via embedding similarity.
when_to_use: 'Pipeline kind: extraction.'
---

# BLIP + CLIP Interrogator image-to-prompt

Generate a prompt that would re-create a given image. Combines:
(1) BLIP captioning model for high-level description, (2) CLIP
Interrogator for matching against curated artist / style / medium
vocabulary, (3) embeddings cosine-similarity to confirm prompt
fidelity to original image. The winning Kaggle shape for the
Stable Diffusion Image-to-Prompts competition.

Verified by Open Harness Hub mining: leonidkulyk LB 0.45836
BLIP+CLIP CLIP-Interrogator (732 votes), inversion Calculating
Stable Diffusion Prompt Embeddings (617 votes), burhanuddinlatsaheb
Text-to-Image Generation (570 votes — uses the same BLIP+CLIP
combo). Confirmed across 3 top kernels.

## Task

Given a Stable-Diffusion-generated image, recover an approximate prompt + verify via embedding similarity.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **caption_with_blip** — `processor` → `processor/embedder-minilm`
3. **clip_interrogate** — `processor` → `processor/cross-encoder-reranker`
4. **verify_cosine** — `processor` → `processor/multi-vector-fusion`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/bge-embeddings-local

## Provenance

- Hub component: `pipeline/blip-clip-image-to-prompt` v0.1.0
- License: `MIT`
- Industry: ai, creative, creative.image
- Full source manifest: see `references/manifest.yaml`
