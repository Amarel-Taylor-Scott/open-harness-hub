# Use case 1 - Internal Q&A on documents

> Upload PDFs, ask questions, get cited answers.

## When to use

- Internal knowledge base lookups (HR policies, runbooks, contracts)
- Customer-facing chat-with-docs widgets
- Researcher answering questions over a paper corpus
- Compliance team querying regulatory PDFs

## Primary pipeline

[`pipeline/chat-with-pdf-citations`](../catalog/pipeline_chat-with-pdf-citations.md)

## Primitives used

| Layer | Component | What it does |
|---|---|---|
| Format conversion | `processor/pdf-to-text` | OCR + extract layer → plain text |
| Chunking | `processor/recursive-character-chunker` | Split with overlap on paragraph/sentence boundaries |
| Embedding | `processor/embedder-minilm` | 384-dim text embeddings (local, no API key) |
| Retrieval | `rule-pack/hybrid-retrieval-policy` | BM25 + dense + RRF + min-score floor |
| Reranking | `processor/cross-encoder-reranker` | Top-20 → top-5 via cross-encoder |
| Safety | `rule-pack/grep-prompt-injection-heuristics` | Block injection in retrieved chunks |
| Privacy | `rule-pack/privacy-pii-text-en` | Redact PII in retrieved chunks |
| Persona | `persona/research-analyst` | Citation-first answer style |
| Harness | `harness/text-safety-review` | Compose persona + RAG + verify |
| Verification | `processor/citation-coverage` | Every claim cited or "no evidence" |

## Composition

```
pdf_bytes + question
  → pdf-to-text
  → recursive-character-chunker
  → embedder-minilm (over chunks)
  → embedder-minilm (over query)
  → hybrid-retrieval-policy
  → cross-encoder-reranker
  → grep-prompt-injection-heuristics
  → privacy-pii-text-en (redact chunks)
  → text-safety-review (persona/research-analyst)
  → citation-coverage
  → answer_markdown, citations[]
```

## Sample inputs / outputs

```python
inputs = {
    "pdf_bytes": open("hr_handbook.pdf", "rb").read(),
    "question":  "What's the parental leave policy for non-birthing parents?"
}
# → answer_markdown:
#   "Non-birthing parents receive 12 weeks of paid leave [1] within
#    the first year of the child's arrival [2]..."
# → citations: ["chunk_4", "chunk_12"]
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/open-harness-hub@dist-published
/chat-with-pdf-citations
```

### Cursor / OpenHands / any Agent Skills tool

```bash
git clone --branch dist-published https://github.com/Amarel-Taylor-Scott/open-harness-hub.git oh
cp -r oh/agent-skills/chat-with-pdf-citations ~/.cursor/skills/
```

### Direct Python (no harness host)

```bash
python scripts/run_pipeline.py pipeline/chat-with-pdf-citations \
  --inputs inputs.json
```

## Customization knobs

- **Bigger corpus**: swap `embedder-minilm` (384-dim) for `adapter/openai-embeddings` (`text-embedding-3-large`, 3072-dim) for higher recall.
- **Better reranker**: swap default BGE-base for Cohere Rerank by setting `processor/cross-encoder-reranker` `model_target` to `cohere_rerank`.
- **Domain knowledge**: add a domain `knowledge-pack/*` and prepend it as a fixed retrieval prefix.
- **Citation format**: edit `persona/research-analyst` to match your citation style (numeric `[1]`, footnote `[smith-2026]`, etc.).
