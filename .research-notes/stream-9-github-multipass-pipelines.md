# Stream 9 — Production multi-pass pipelines mined from GitHub

> All 20 codebases verified via authenticated `gh search` / `gh api`.

## 15 new pipelines to add

| # | pipeline_kind | slug | source repo |
|---|---|---|---|
| 1 | `research` | `deep-research-supervisor-worker` | langchain-ai/open_deep_research |
| 2 | `rag` | `self-rag-grade-and-revise` | AkariAsai/self-rag (+ LangGraph forks) |
| 3 | `rag` | `corrective-rag-tri-state` | CRAG (Nagi-ovo, aws-samples) |
| 4 | `rag` | `rag-fusion-rrf` | Raudaschl/rag-fusion + superlinear-ai/raglite |
| 5 | `rag` | `hyde-then-retrieve` | labdmitriy/llm-rag + yilane/rag-related |
| 6 | `rag` | `step-back-abstract-retrieve` | labdmitriy/llm-rag |
| 7 | `rag` | `graphrag-global-mapreduce` | microsoft/graphrag global_search |
| 8 | `rag` | `graphrag-drift-followup` | microsoft/graphrag drift_search |
| 9 | `reasoning` | `tree-of-thoughts-bfs` | princeton-nlp/tree-of-thought-llm |
| 10 | `reasoning` | `skeleton-of-thought-parallel` | imagination-research/sot |
| 11 | `reasoning` | `reflexion-verbal-memory` | noahshinn/reflexion |
| 12 | `code` | `swe-agent-sample-and-review` | princeton-nlp/SWE-agent |
| 13 | `code` | `code-act-jupyter-loop` | OpenInterpreter/open-interpreter |
| 14 | `writing` | `storm-persona-curation` | stanford-oval/storm |
| 15 | `router` | `semantic-route-dispatch` | aurelio-labs/semantic-router |

## 10 new processors to add

| # | Proposed slug | Source |
|---|---|---|
| 1 | `processor/context-window-packer` | ✅ already shipped this session — SWE-agent `history_processors.py` style |
| 2 | `processor/multi-vector-fusion` | Raudaschl/rag-fusion, superlinear-ai/raglite, GraphRAG |
| 3 | `processor/iterative-revise-loop` | ✅ already shipped this session — Reflexion / Self-RAG |
| 4 | `processor/retrieval-evaluator` | CRAG correct/incorrect/ambiguous classifier |
| 5 | `processor/document-grader` | Self-RAG per-doc relevance grader |
| 6 | `processor/hallucination-grader` | Self-RAG grounded-vs-generated check |
| 7 | `processor/persona-set-generator` | STORM multi-perspective persona spawner |
| 8 | `processor/skeleton-outliner` | SoT outline-then-parallel-expand splitter |
| 9 | `processor/action-sampler-multi-rollout` | SWE-agent `action_sampler.py` |
| 10 | `processor/runtime-tool-selector` | Toolformer / pydantic-ai `_tool_search.py` |

Near-misses worth slotting in next: `processor/budget-controller`, `processor/note-compressor`, `processor/trajectory-voter`, `processor/community-summary-mapreduce`, `processor/structured-output-validator-retry`.

## Mapped source codebases

| Repo | Key files | Pattern |
|---|---|---|
| langchain-ai/open_deep_research | `src/open_deep_research/deep_researcher.py` (~700 LOC), `prompts.py` | Supervisor + N parallel researchers + critic + final report writer |
| Alibaba-NLP/DeepResearch (Tongyi) | `inference/react_agent.py`, `run_multi_react.py` | Multi-trajectory ReAct + majority-vote across N rollouts |
| jina-ai/node-DeepResearch | `src/agent.ts` | Budget-bounded loop: search → read → reason → reflect → answer-or-continue; "beast mode" fallback |
| dzhng/deep-research | `src/deep-research.ts`, `feedback.ts` | Recursive depth-and-breadth tree, learning rollup |
| stanford-oval/storm | `knowledge_storm/storm_wiki/modules/{persona_generator,knowledge_curation,outline_generation,article_generation,article_polish}.py` | Persona-set → simulated dialogue → outline → section fanout → polish |
| AkariAsai/self-rag | `retrieval_lm/run_short_form.py` | Reflection tokens: retrieve → grade-docs → rewrite-query loop → generate → halluc + answer graders |
| Nagi-ovo/CRAG-Ollama-Chat | (CRAG impl) | retrieve → evaluator (correct/incorrect/ambiguous) → refine or web-fallback |
| Raudaschl/rag-fusion + superlinear-ai/raglite | `main.py`, `_search.py` | N query rewrites → N retrievals → RRF → answer |
| labdmitriy/llm-rag, yilane/rag-related | `step_back.py`, `06_langchain_StepBackPrompting.py` | Step-Back abstraction; HyDE doc synthesizer |
| microsoft/graphrag | `packages/graphrag/graphrag/query/structured_search/{local_search,global_search,drift_search}/` | Local (ego-network), Global (map-reduce over community summaries), DRIFT (primer-then-follow-up hybrid) |
| princeton-nlp/SWE-agent | `sweagent/agent/{agents,reviewer,history_processors,action_sampler}.py` | Multi-sample action rollouts + container exec + history-window-compressor + patch reviewer judge |
| noahshinn/reflexion | `programming_runs/reflexion.py`, `hotpotqa_runs/react.py` | Try → evaluator → verbal self-reflection → memory append → retry, bounded by max_iters |
| princeton-nlp/tree-of-thought-llm | (paper code) | Propose N thoughts → value/vote → BFS/DFS expand → backtrack |
| imagination-research/sot | (SoT) | Outline skeleton → parallel expand bullets → stitch |
| aurelio-labs/semantic-router | `semantic_router/routers/{semantic,hybrid}.py` | Encode utterance → semantic+BM25 hybrid route classifier → dispatch |
| pydantic/pydantic-ai | `_agent_graph.py`, `_output.py`, `_tool_search.py` | Structured-output validation with retry-on-fail; runtime tool selection from large catalogs |
| OpenInterpreter/open-interpreter | `interpreter/core/respond.py` | LLM-emit-code → render → exec-in-jupyter → observation-inject → loop |
| crewAIInc/crewAI | `lib/crewai/src/crewai/crew.py` (`kickoff`) | Sequential or hierarchical role-agents; task-output chained |
| geekan/MetaGPT | `metagpt/roles/` (architect, engineer, product_manager, qa_engineer) | SOP-driven assembly line; structured artifact handoff |
| microsoft/promptflow | (promptflow) | DAG of typed nodes (LLM / python / prompt) + bulk-eval + variants |
