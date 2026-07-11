# Local-first with cited answers

*pattern* · `pattern/local-first-with-cited-answers` · v0.1.0 · beta

Privacy-preserving RAG pattern: all PDF content + chunks + embeddings + chat history live on the user's machine; model inference goes through a local provider (e.g. Ollama) by default; every answer surfaces (page, span) citations. Cloud is opt-in via explicit API key. Generalizes from CiteMind (PDF research wiki) to any vertical where uploads to a hosted model are politically, legally, or culturally unacceptable.

| axis | value |
|---|---|
| industry | education, privacy, compliance, healthcare, defense, legal |
| capability | retrieval, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



