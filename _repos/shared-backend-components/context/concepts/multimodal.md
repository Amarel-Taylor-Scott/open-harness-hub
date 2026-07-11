# Multimodal pipelines

Image, audio, music, video, document, and 3D pipelines compose the
**same** primitives as text pipelines. The hub does not split modalities
into separate trees.

A common image-gen pipeline:

```
[persona]   "Brand-safe product photographer"
[rule_pack] grep-prohibited-terms      ← guard input (celeb names, trademarks, NSFW)
[knowledge_pack] style-references      ← RAG of cinematic style descriptors
[knowledge_pack] lens-physics          ← RAG of physical priors (lens / aperture)
[harness]   prompt-shaper              ← compose final prompt from input + retrieved style + physics
[tool]      txt2img.sdxl               ← function-call to the image model
[rule_pack] grep-output-safety-image   ← NSFW / IP / watermark detectors on the output
```

Only two fields change vs. a text pipeline:

```yaml
modality: ["image"]
pipeline_kind: "generate_image"
```

## Recommended fields for generative pipelines

When a pipeline emits image / audio / music / video, the manifest should also
declare:

| Field | What |
|---|---|
| `output_safety_packs` | Rule packs that screen the generated component (NSFW, IP, watermark, prompt-injection-via-image). |
| `style_packs` | Knowledge packs of style references the prompt-shaper pulls from. |
| `physics_packs` | Knowledge packs encoding physical priors (lens optics, acoustic, motion). |
| `attribution` | Free text describing who / what the style references are drawn from, plus license. |

The hosted backend also needs media-aware services:

- asset storage for large outputs and previews.
- media captions, transcripts, thumbnails, waveforms, and perceptual hashes.
- cost models for resolution, duration, frame count, sample rate, GPU seconds, storage, and egress.
- safety screens for NSFW, IP, likeness, watermark, hidden text, malware, and policy violations.
- provenance for prompt, seed, model version, source assets, license, and safety report.

See [`pipeline/multimodal-generation-blueprint`](../catalog/pipeline_multimodal-generation-blueprint.md) for a generic media generation blueprint.

## Example in the catalog

See [`pipeline/brand-safe-product-photo`](../catalog/pipeline_brand-safe-product-photo.md).
