# Stream 2 — AI-specific standards (research notes)

## Headline recommendations
1. **Croissant emitter for `dataset` / `knowledge-pack`** — highest external interop (HF/Kaggle/Google Dataset Search index it automatically). Renderer `dataset.yaml → croissant.json`.
2. **MCP server stubs from `tool` / `processor` + the hub itself as an MCP server.** Strategic moat — makes the catalog a runtime contract Claude / OpenAI MCP clients can consume directly.
3. **HF model-card / dataset-card / Space renderer trio.** Three small renderers; reuses existing fields; gives every artifact a publishable README.

## Standard-by-standard

| Standard | URL | Adoption | Hub mapping | Decision |
|---|---|---|---|---|
| Model Cards (Mitchell et al.) | arxiv 1810.03993 + HF spec | de facto (HF variant) | `harness`, `adapter` | emit MODEL_CARD.md alongside |
| Datasheets for Datasets (Gebru et al.) | arxiv 1803.09010 | mostly academic | `dataset`, `knowledge-pack` | encode as `datasheet:` block + render |
| Croissant (MLCommons) | mlcommons/croissant; docs.mlcommons.org/croissant | official; adopted by HF/Kaggle/Google Dataset Search | `dataset`, `knowledge-pack` | **emit alongside** (highest ROI) |
| Model Context Protocol (MCP) | modelcontextprotocol.io (spec rev 2025-11-25) | very high (Anthropic, OpenAI, Google, MS) | `tool`, `processor`, `persona`, `knowledge-pack` | **full adopt as export surface**; hub publishes its own MCP server too |
| AIBOM (CycloneDX 1.6 modelCard) | cyclonedx.org/capabilities/mlbom, /docs/1.6/json | official OWASP/ECMA | cross-cuts `harness`+`adapter`+`dataset` per release | emit on releases |
| NIST AI RMF / AI 600-1 | nist.gov/itl/ai-risk-management-framework | US-gov voluntary | `rubric` (Measure), `harness.risks` (Map) | tag with controls; coverage report |
| ISO/IEC 42001 | iso.org/standard/81230 | enterprise cert | org-level governance | compliance/iso42001-mapping.yaml |
| EU AI Act Annex IV | eur-lex Regulation 2024/1689 | law (phased 2026-2027) | aggregate over harness+dataset+rubric | generate Annex-IV dossier |
| ONNX metadata | onnx.ai, onnx/onnx.proto | de facto interchange | `adapter` | optional `adapter.onnx:` block |
| HF frontmatter (model/dataset/Space cards) | hub-docs modelcard/datasetcard; spaces-config | de facto for OSS | `harness`→model README; `dataset`→dataset README; deploy→Space (already present) | three renderers |
| Kaggle | kaggle.com/docs/api, /docs/models | platform-specific | `harness` (notebook variant), `dataset` | ignore unless publishing to Kaggle |

## Emit pattern
- Source of truth stays **YAML manifest in `catalog/`**.
- Renderers under `scripts/emit/` produce: croissant.json, model_card.md, dataset_card.md, hf_space_readme.md, cyclonedx-aibom.json, mcp-server.{ts,py}, eu-ai-act-annex-iv.md.
- Renderers are idempotent and CI-checked.
