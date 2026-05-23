# Use case 7 - Brand-safe image generation

> Style-RAG + lens-physics + guard rules + output-safety screened image generation.

## When to use

- Marketing / e-commerce product photography
- Editorial illustration with brand-safety constraints
- Internal mockup generation with IP guardrails
- A/B-testing image variants

## Primary pipeline

[`pipeline/brand-safe-product-photo`](../catalog/pipeline_brand-safe-product-photo.md)

## Primitives used

| Layer | Artifact |
|---|---|
| Input guard | `rule-pack/grep-prohibited-terms` (celebs, trademarks, NSFW) |
| Style RAG | `knowledge-pack/style-references-cinematic` |
| Physics RAG | `knowledge-pack/lens-physics-primers` |
| Persona | `persona/cinematic-product-photographer` |
| Prompt-shape | `harness/text-safety-review` |
| Tool | `tool/txt2img-sdxl` (or `adapter/sdxl-local`) |
| Output safety | `rule-pack/grep-output-safety-image` (NSFW classifier, celebrity-face match, watermark check) |
| Provenance | `scripts/emit/c2pa.py` → C2PA manifest with `c2pa.actions = trainedAlgorithmicMedia` |

## Composition

```
brief
  → grep-prohibited-terms (block celeb names, trademarks, NSFW)
  → style-references-cinematic retrieval (top-4 by brand_tone)
  → lens-physics-primers retrieval (top-2 by shot_type)
  → text-safety-review (persona/cinematic-product-photographer)
     → shaped prompt (lens, lighting, palette, composition, mood)
  → txt2img-sdxl
  → grep-output-safety-image (nsfw / celeb-face / watermark)
  → c2pa.manifest.json (provenance assertion)
  → final_prompt, image_url, safety_report
```

## Sample inputs / outputs

```python
inputs = {
  "brief": {
    "name":        "Ceramic mug",
    "category":    "tabletop",
    "brand_tone":  "moody noir",
    "shot_type":   "portrait-85mm",
    "description": "studio shot of a navy ceramic mug, no logos"
  }
}
# → final_prompt:
#   "studio product photograph of a navy ceramic mug. 85mm lens, f/2.0,
#    ISO 200. Single hard key light at 45° from upper right; subtle fill
#    from soft bounce on left. Monochrome palette with a single navy
#    accent. Deep shadows in lower third. Subject distance 2.5m.
#    Composition: rule-of-thirds, mug centered on right third.
#    Atmosphere: tense, contemplative."
# → image_url: "https://.../mug-noir.png"
# → safety_report: { nsfw: 0.01, watermark_present: false, celebrity_match: false }
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/open-harness-hub@dist-published
/brand-safe-product-photo
```

### Direct via tool

Add `dist/mcp/server.py` to Claude Desktop → the `txt2img-sdxl` tool becomes available, and Claude can compose this pipeline ad-hoc.

## Customization knobs

- **New style packs**: write `knowledge-pack/style-references-editorial`, `knowledge-pack/style-references-90s-grunge`, etc.
- **New backends**: change `adapter/sdxl-local` to a hosted target (`fal.ai`, `Replicate`, `OpenAI gpt-image-1`).
- **Stricter brand-safety**: add a `rule-pack/grep-output-safety-image` with rules specific to your brand (e.g. require a logo-corner watermark, ban competitor branding).
- **Multi-prompt A/B**: wrap the pipeline in a `processor/parallel.fan_out` to generate N variants for the marketing team to pick from.
- **C2PA signing**: install `c2patool` and sign the output manifest with your brand's code-signing certificate.
