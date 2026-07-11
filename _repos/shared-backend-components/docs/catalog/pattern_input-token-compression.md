# Input-token compression (prune / dedupe / compress context before the model)

*pattern* · `pattern/input-token-compression` · v0.1.0 · beta

Shrink what the model has to read before the call, so the same task costs
fewer input tokens (and often runs faster and more accurately, because the
model sees less noise).

The context that reaches an LLM is usually far larger than it needs to be:
retrieved RAG chunks overlap, system prompts repeat, few-shot examples are
verbose, and long documents carry boilerplate. This pattern inserts a
deterministic-or-cheap compression stage between context assembly and the
expensive model call.

Compression levers (compose as needed):
 1. **redundancy dedupe** — drop near-duplicate retrieved chunks
    (SimHash / embedding cosine) before they hit the prompt.
 2. **extractive pre-summarization** — keep only sentences/spans that
    answer the query; discard the rest.
 3. **prompt compression** — LLMLingua-style token dropping on low-
    information tokens, with a target compression ratio.
 4. **schema-aware field selection** — for structured inputs, send only
    the fields the task uses.
 5. **token budgeter** — cap assembled context to a hard token / cost
    ceiling, evicting lowest-scoring chunks first.

Every compression step declares the tokens-in saved and is paired with a
quality check so the pipeline can detect when compression hurts the answer.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | summarization, retrieval, routing |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



