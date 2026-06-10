# Stream 3 — Tool & eval standards (research notes)

## Headline recommendations — TOOL
1. **JSON Schema Draft 2020-12 as canonical `parameters` / `returns`**; one emitter file produces OpenAI / Anthropic / MCP / Gemini variants. Use `litellm` as reference normalizer.
2. **MCP as the primary publish target** — generate `tools/list` JSON-RPC responses; cross-vendor coverage via clients.
3. **OpenAPI ingestion** — `tool.implementations[].openapi` should auto-derive `parameters` from the linked Operation.

## Headline recommendations — EVAL
1. **`benchmark/* → lm-evaluation-harness YAML` emitter** — strongest OSS momentum; academic credibility. Map `dataset`→`dataset_path`, `rubric`→`metric_list`, `pipeline`→`doc_to_text`.
2. **`benchmark/* → promptfoo config` emitter** — application-dev audience; near-1:1 mapping (`providers`/`tests`/`assert`).
3. **Adopt Ragas + garak metric names as referenceable `rubric/*` identifiers** (`ragas.faithfulness`, `garak.probes.dan`).

## Tool schemas — emission map

```
manifest.parameters/returns (JSON Schema 2020-12)
    → OpenAI:    tools[].function.parameters
    → Anthropic: tools[].input_schema
    → MCP:       tools[].inputSchema / outputSchema
    → Gemini:    tools[].functionDeclarations[].parameters  (OpenAPI-3.0 subset; lossy down-convert)
```

Reference: `litellm.utils.function_to_dict` already normalizes across providers.

## Tool standards table

| Standard | URL | Adoption | Decision |
|---|---|---|---|
| OpenAI function calling | platform.openai.com/docs/guides/function-calling | de facto | trivial emit |
| Anthropic tool use | docs.anthropic.com/en/docs/agents-and-tools/tool-use | very high | trivial emit |
| Google Gemini function calling | ai.google.dev/gemini-api/docs/function-calling | high | emit with down-convert (no $ref, limited anyOf) |
| MCP | modelcontextprotocol.io (rev 2025-11-25) | very high — cross-vendor | **primary publish target** |
| OpenAPI Operations | spec.openapis.org/oas/latest | universal for HTTP | **ingest** to auto-derive tool manifests |
| LangChain BaseTool | python.langchain.com/docs/concepts/tools | high | generate adapter; don't import |
| LlamaIndex FunctionTool | docs.llamaindex.ai | medium | generate adapter |
| Toolformer / Gorilla / APIBench | gorilla.cs.berkeley.edu | research | cite as eval datasets |

## Eval standards table

| Standard | URL | Adoption | Decision |
|---|---|---|---|
| HELM (Stanford CRFM) | crfm.stanford.edu/helm | academia | mirror vocab; no direct emit |
| BIG-Bench (Google) | github.com/google/BIG-bench | declining/frozen | support import as dataset source |
| EleutherAI lm-evaluation-harness | github.com/EleutherAI/lm-evaluation-harness | OSS industry standard | **first-class emit target** |
| OpenAI Evals | github.com/openai/evals | declining vs lm-eval | secondary emit |
| MLPerf | mlcommons.org/benchmarks/inference-llm | hardware | out of scope unless measuring perf |
| garak | github.com/NVIDIA/garak | leading LLM-security scanner | reference probes by name |
| promptfoo | promptfoo.dev/docs | high among app devs | **second-class emit target** (near-1:1) |
| DeepEval | docs.confident-ai.com | medium-high | generate pytest files |
| Ragas | docs.ragas.io | high for RAG | metric-library reference |
| TruLens | trulens.org | medium | feedback-library reference |
