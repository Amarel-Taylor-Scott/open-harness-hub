# Stream 5 — RAG framework patterns (LangChain / LlamaIndex / Haystack / DSPy / others)

> Source: parallel research agent. Web tools were denied; relied on
> training-data knowledge through Jan 2026. URLs are canonical paths
> but unverified for this session — re-check before publishing.

## Headline: top 10 artifacts to add

| # | Already in catalog? | Proposed artifact id | Notes |
|---|---|---|---|
| 1 | ✅ rule-pack/hybrid-retrieval-policy | hybrid-retrieval-rrf | BM25 + dense + RRF — landed |
| 2 | ✅ processor/recursive-character-chunker | recursive-character-chunker | landed |
| 3 | **NEW** | processor/semantic-chunker | LC `SemanticChunker`, LI `SemanticSplitterNodeParser` |
| 4 | **NEW** | pipeline/parent-document-retrieval | small-to-big retrieval; LC `ParentDocumentRetriever`, LI `AutoMergingRetriever` |
| 5 | **NEW** | pipeline/multi-query-expansion | LLM fans out N rewrites; LC `MultiQueryRetriever` |
| 6 | ✅ processor/cross-encoder-reranker | cross-encoder rerank | landed |
| 7 | **NEW** | processor/self-query-filter | NL → metadata-filter extraction; LC `SelfQueryRetriever`, LI `AutoRetriever` |
| 8 | **NEW** | rubric/rag-faithfulness-relevance-v1 | faithfulness / answer-relevance / context-precision / context-recall (RAGAS-style) |
| 9 | ✅ processor/hyde-query-expander | HyDE | landed |
| 10 | **NEW** | pipeline/router-query-engine | LLM picks {vector, SQL, KG, web} sub-engine |

## Framework primitive map (full)

### LangChain (langchain-ai/langchain)
- Retrievers under `libs/langchain/langchain/retrievers/`: BM25, MultiQuery,
  ContextualCompression, ParentDocument, SelfQuery, Ensemble (RRF),
  MultiVector, TimeWeighted.
- Splitters under `libs/text-splitters/langchain_text_splitters/`:
  RecursiveCharacter, MarkdownHeader, SemanticChunker (experimental).
- Chains: RetrievalQA, ConversationalRetrievalChain, MapReduceDocumentsChain.
- Eval: RAGAS integration + LangSmith eval datasets.

### LlamaIndex (run-llama/llama_index)
- Schemas in `llama-index-core/llama_index/core/schema.py`: Document,
  TextNode, IndexNode.
- Node parsers: SentenceSplitter, TokenTextSplitter, SentenceWindowNodeParser,
  HierarchicalNodeParser, SemanticSplitterNodeParser.
- Retrievers: VectorIndexRetriever, KeywordTableSimpleRetriever,
  KnowledgeGraphRAGRetriever, AutoMergingRetriever, RecursiveRetriever.
- Query engines: SubQuestionQueryEngine, RouterQueryEngine,
  SQLAutoVectorQueryEngine.
- Synthesizers: TreeSummarize, Refine, CompactAndRefine, Accumulate.
- Rerankers: LLMRerank, SentenceTransformerRerank, CohereRerank.
- Evaluators: RetrieverEvaluator, FaithfulnessEvaluator, RelevancyEvaluator.

### Haystack 2 (deepset-ai/haystack)
- `components/retrievers/in_memory/`: InMemoryBM25Retriever,
  InMemoryEmbeddingRetriever.
- `components/joiners/document_joiner.py`: DocumentJoiner (concat / RRF / merge).
- `components/rankers/`: MetaFieldRanker, LostInTheMiddleRanker,
  TransformersSimilarityRanker, SentenceTransformersDiversityRanker.
- `components/preprocessors/`: DocumentSplitter, DocumentCleaner.
- `components/builders/`: PromptBuilder, AnswerBuilder.

### DSPy (stanfordnlp/dspy)
- Signatures (declarative I/O contract) — `dspy/signatures/signature.py`.
- Modules under `dspy/predict/`: Predict, ChainOfThought, ProgramOfThought,
  ReAct, MultiChainComparison.
- Teleprompters under `dspy/teleprompt/`: BootstrapFewShot, MIPROv2, COPRO,
  BootstrapFinetune — optimizers for prompts.
- Retrievers under `dspy/retrieve/`: ColBERTv2, ChromadbRM, PineconeRM,
  QdrantRM, WeaviateRM.
- Assertions: `dspy/primitives/assertions.py` — `Assert`, `Suggest`.

### Others
- **RAGFlow** (infiniflow/ragflow) — DeepDoc layout parser; chunk templates
  for Q&A / Manual / Laws / Paper; GraphRAG; KG extraction.
- **Cognita** (truefoundry/cognita) — modular DataSource / Parser /
  Embedder / VectorDB / Retriever / QueryController.
- **llmware** (llmware-ai/llmware) — Library / Parser / Retrieval / Prompt /
  Agents + RAG-Instruct SLMs (BLING/DRAGON).
- **Outlines** (dottxt-ai/outlines) — `generate.json`, `generate.regex`,
  `generate.choice` — constrained decoding, maps to **rule-pack** as
  output contracts.
- **Marvin** (PrefectHQ/marvin) — `@fn`, `cast`, `extract`, `classify`.
- **Mirascope** (Mirascope/mirascope) — `@llm.call`, `response_model`,
  prompt-as-function.

## What's notably MISSING from these frameworks (gap the hub fills)
- Standard JSON-LD addressability (only LlamaHub has anything like a
  registry; nothing publishes Croissant).
- Cross-tool emit (these frameworks lock into their own API; the hub's
  emit/ scripts produce MCP / Agent Skills / HF cards from the same source).
- Lifecycle-position labeling (none of them classify primitives as
  pre_api / api / post_api).
- Multi-modal pipelines (all four frameworks are text-centric).
- Built-in EU AI Act / DPV / HIPAA compliance metadata.

## Word count
~ 980.
