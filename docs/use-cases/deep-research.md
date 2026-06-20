# Use case 3 - Deep research with citations

> The "Perplexity / OpenAI deep research" pattern. Multi-source web search with verified citations.

## When to use

- Researcher answering open-ended questions across the open web
- Sales / market research synthesis
- Journalist source verification
- Litigation prep

## Primary pipeline

[`pipeline/deep-research-with-citations`](../catalog/pipeline_deep-research-with-citations.md)

## Primitives used

| Layer | Component | What it does |
|---|---|---|
| Redact | `harness/redact-pii-text` | Strip PII before external search |
| Expand | `knowledge-pack/common-abbreviations` | Domain abbreviations |
| Plan | `harness/text-safety-review` | Decompose into sub-questions |
| Online policy | `rule-pack/web-search-allowlist-default` | Allowlist + PII sanitize |
| Search | `tool/web-search` | Brave/Serper/DDG backend |
| Guard | `rule-pack/grep-prompt-injection-heuristics` | Block injection in retrieved content |
| Verify sources | `harness/text-safety-review` (verification mode) | Credibility / relevance / freshness |
| Synthesize | `harness/text-safety-review` (synthesis mode) | Cite-or-omit per claim |
| Verify | `processor/citation-coverage` | Every claim cited |

## Composition

```
query
  → redact-pii-text
  → common-abbreviations expand
  → plan_subqueries (LLM decompose)
  → web-search-allowlist-default sanitize
  → web-search (parallel per sub-Q)
  → grep-prompt-injection-heuristics guard
  → verify_sources (credibility + freshness + cross-reference)
  → synthesize (cited)
  → citation-coverage verify
  → synthesis_markdown, citations[], confidence_per_claim[]
```

## Sample inputs / outputs

```python
inputs = {
    "query": "How has EU AI Act compliance affected high-risk AI deployment in 2025-2026?",
    "max_sources": 15,
    "freshness_window_days": 180
}
# → synthesis_markdown:
#   "EU AI Act high-risk obligations entered into force in August 2026 [1].
#    Major deployers have published Annex IV dossiers (typical length
#    ~80 pages) [2]. Compliance cost estimates range from €52k to €380k
#    per high-risk system [3, citing FRA 2026 study]..."
# → citations: [
#     "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
#     "https://digital-strategy.ec.europa.eu/.../annex-iv",
#     "https://fra.europa.eu/.../ai-compliance-cost-2026"
#   ]
# → confidence_per_claim: [0.95, 0.82, 0.68]
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/open-harness-hub@dist-published
/deep-research-with-citations
```

### MCP host (Cursor / cline / Claude Desktop)

Add `dist/mcp/server.py` as an MCP server - `tool/web-search` becomes available as a model-callable tool, and you can compose the pipeline yourself.

## Customization knobs

- **Tighter allowlist**: edit `rule-pack/web-search-allowlist-default` to add/remove sources. Government sources only? Drop the news allowlist line.
- **Different search backend**: swap `tool/web-search` implementations (Brave, Serper, Tavily, Exa, Perplexity).
- **Stronger judge**: switch the synthesis harness's `model_target` to `frontier_judge` (Anthropic / OpenAI) for high-stakes outputs.
- **Cross-language search**: pair with `processor/audio-to-text-whisper` (for non-English audio sources) and `knowledge-pack/iso-country-codes` for jurisdiction-aware filtering.
- **Iterative refine**: add `processor/iterative-revise-loop` at the end with `verifier_refs: [citation-coverage, hallucination-scorer]` to auto-retry until convergence.
