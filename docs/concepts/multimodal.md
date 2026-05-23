# Multimodal pipelines

Image, audio, and video pipelines compose the **same** primitives as
text pipelines. The hub does not split modalities into separate trees.

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

When a pipeline emits image / audio / video, the manifest should also
declare:

| Field | What |
|---|---|
| `output_safety_packs` | Rule packs that screen the generated artifact (NSFW, IP, watermark, prompt-injection-via-image). |
| `style_packs` | Knowledge packs of style references the prompt-shaper pulls from. |
| `physics_packs` | Knowledge packs encoding physical priors (lens optics, acoustic, motion). |
| `attribution` | Free text describing who / what the style references are drawn from, plus license. |

## Example in the catalog

See [`pipeline/brand-safe-product-photo`](../catalog/pipeline_brand-safe-product-photo.md).
