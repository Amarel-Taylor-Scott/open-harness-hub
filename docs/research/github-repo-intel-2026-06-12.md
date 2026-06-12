# GitHub repo intel — 2026-06-12 intake batch

Eleven repos run through the governed intake engine (`scripts/repo_intel/engine.py`;
snapshots in `.agent/repo-intel/snapshots.jsonl`, facts `api_verified` via the GitHub
API except revfactory/harness which is `webfetch_github_page`). **Discovery ≠ trust:
every decision below is candidate-grade; nothing becomes active without the full
proof-to-promote ladder** (classification → duplicate check → license review →
provenance → sandbox → eval → red-team → promotion decision).

Lanes used below — *inspiration* (read the design, build our own), *template*
(structure/content we instantiate), *wrap* (run behind a port as a swappable backend;
output never truth), *integrate* (full integration candidate behind the gates).

## The batch

| Repo | Stars | License | Intake decision | Lane | Maps to (ours) |
|---|---|---|---|---|---|
| revfactory/harness | 6.8k | Apache-2.0 | intake_as_skill_candidate | template + inspiration | OpenSkillsHub / OpenHarnessHub — generates domain agent teams + skills from 6 architecture patterns (Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical Delegation). Companion paper claims +60% avg quality, n=15 author-measured — treat as unverified-until-reproduced. |
| revfactory/harness-100 | 945 | Apache-2.0 | watch | template | ~200 ready-made harness configs; thin description so the classifier saw nothing — re-classify after a content crawl. Natural follow-up to harness once it clears eval. |
| obra/superpowers | 224.9k | MIT | intake_as_skill_candidate | template + inspiration | OpenSkillsHub — the largest skills framework + methodology; mine its skill-shape conventions for our skill digestion pipeline (`shared-sandbox-and-skill-digestion`). |
| anthropics/skills | 149.5k | none/custom | **quarantine (no_license)** | template (pending) | OpenSkillsHub — official Agent Skills repo; the engine refused intake because the license is custom/unrecognized. Owner license review required before anything is copied. |
| mem0ai/mem0 | 58.4k | Apache-2.0 | intake_as_tool_candidate | wrap | `memory_distilled_write` is our deterministic core of its selective-extraction idea; mem0 itself = swappable memory backend behind ports (already tracked: competitor/complement — differentiate on governance/provability). |
| getzep/graphiti | 27.3k | Apache-2.0 | intake_as_tool_candidate | wrap | `memory_temporal_graph` implements the validity-interval semantics deterministically; Graphiti = live temporal-KG backend candidate for the same `run()` seam. |
| letta-ai/letta | 23.3k | Apache-2.0 | intake_as_tool_candidate | wrap + inspiration | `memory_agentic_hierarchy` is the deterministic page-in/page-out core of the MemGPT idea; Letta = bounded-agent runtime candidate behind ports (agents propose, never serve truth). |
| microsoft/graphrag | 33.7k | MIT | intake_as_tool_candidate | inspiration | `graphrag_retrieve` (catalog manifest; implementation queued) — follow its community/global-sensemaking split; heavy build cost, adopt the algorithm shape not the stack. |
| LMCache/LMCache | 8.5k | Apache-2.0 | watch | integrate (serving layer) | `cache_kv_reuse` is our deterministic reuse PLANNER and cites LMCache's ~7x TTFT ceiling; LMCache itself is the live KV layer when we run self-hosted inference on the Teleon plane. Thin topics → classifier saw little; re-classify when the inference plane goes live. |
| zilliztech/GPTCache | 8.1k | MIT | intake_as_tool_candidate | wrap | `cache_semantic` is the governed deterministic core (personalized-never-served, tenant-scoped); GPTCache = learned-embedding cache backend candidate behind the same `run()`. Last push 2025-07 — check maintenance before integration. |
| microsoft/LLMLingua | 6.3k | MIT | intake_as_tool_candidate | wrap | `llmlingua_compress` implements the budgeting contract with an honest deterministic scorer; LLMLingua = the learned perplexity scorer swapped behind the same seam. |

## Standing rules this batch re-confirmed

- **The engine's honesty held:** the highest-star repo in the batch (anthropics/skills)
  was quarantined on license grounds — stars are not proof, and no_license blocks intake
  regardless of provenance.
- **Pattern worth repeating:** our deterministic processors (cache/memory/retrieval
  packages, 2026-06-12 commit b9c8260f) each cite their reference repo; the reference
  repo then enters intake as the LIVE backend candidate behind the same `run()` seam.
  Deterministic core ours, learned backend theirs, one contract.
- **Re-classify thin repos after a crawl:** harness-100 and LMCache landed `watch`
  purely because their API descriptions are thin — the classifier needs content, not
  prestige.

## How to add the next repo

```bash
# facts (api_verified) → snapshot → classify → decision; never hand-write a decision
python3 - <<'PY'
from scripts.repo_intel import engine as E
repo = {"full_name": "owner/name", "description": "...", "topics": [...],
        "license": "SPDX-ID", "stars_count": 0, "forks_count": 0, "archived": False}
E.append_snapshot(repo, now="<iso8601>", source_method="github_api", source_confidence="api_verified")
cls = E.classify(repo)
print(E.intake_decision(repo, cls, E.compute_trend(repo), E.risk(repo), now="<iso8601>"))
PY
```

## Batch 2 (same session) — ingestion / parsing / routing / serving lanes

| Repo | Stars | License | Intake decision | Lane | Maps to (ours) |
|---|---|---|---|---|---|
| microsoft/markitdown | 151.8k | MIT | intake_as_tool_candidate | wrap | `doc_to_markdown_rag_ingest` (catalog) — the any-format→Markdown converter behind the same seam; pairs with native-format-preservation sidecars. |
| docling-project/docling | 61.4k | MIT | intake_as_tool_candidate | wrap | the live `DoclingParser` backend our `scripts/ingest/parser_provider.py` seam already names — wiring it = installing the optional dep, the seam exists. |
| vllm-project/vllm | 82.7k | Apache-2.0 | intake_as_tool_candidate | integrate (serving) | the self-hosted inference engine the Teleon plane would run; pairs with LMCache for the KV layer `cache_kv_reuse` plans for. |
| infiniflow/ragflow | 82.6k | Apache-2.0 | intake_as_tool_candidate | inspiration + foil | full RAG platform — compare their chunk/citation UX against our governed retrieval family; we differentiate on verification + receipts. |
| tesseract-ocr/tesseract | 74.6k | Apache-2.0 | intake_as_tool_candidate | wrap | the OCR engine behind `on_device_ocr_prepass` (catalog) — engine injected, prompt-block contract ours. |
| unclecode/crawl4ai | 68.3k | Apache-2.0 | watch | wrap (pending) | LLM-friendly crawler for the acquisition lane; thin API description → re-classify after a content crawl. |
| BerriAI/litellm | 50.2k | NOASSERTION | **quarantine (no_license)** | wrap (pending) | unified model routing — overlaps our OIPS gateway; SPDX shows NOASSERTION (mixed MIT + enterprise dirs) so the engine refuses until owner license review. |
| firecrawl/firecrawl | 131.8k | AGPL-3.0 | **quarantine (restrictive)** | inspiration only | scrape→LLM-ready markdown; AGPL is incompatible with our open-core commercial layer — read the design, never vendor the code. |

Governance note: two more high-star quarantines (litellm NOASSERTION, firecrawl AGPL) —
the license gate is doing exactly its job on the most popular repos in the batch.

## Batch 3 (the "100% power" sweep) — 70 repos across 4 capability-lane clusters

Four discovery scouts proposed real repos from knowledge (no live API — rate-limit-safe);
all 70 unique repos run through `repo_intel.engine` in one deterministic pass. **These are
`knowledge_proposed_unverified` — API fact-verification is the engine's own
`proof_to_promote` step**, so every row is candidate-grade and nothing is treated as a
committed number. Snapshots appended to `.agent/repo-intel/snapshots.jsonl`.

**Decision distribution (70 unique):** 19 `intake_as_tool_candidate` · 10
`propose_teleon_integration` · 8 `intake_as_harness_candidate` · 4 `intake_as_skill_candidate`
· 1 `intake_as_context_candidate` · 23 `watch` (thin signals) · **5 `quarantine`**.

**Quarantined by the license gate (the governance working — stars are not proof):**
marker (GPL-3.0), surya (GPL-3.0), MinerU (AGPL-3.0) — copyleft, inspiration-only never
vendor; Arize/phoenix (Elastic-2.0) — source-available, wrap-behind-port-only; pgvector
(PostgreSQL license) — permissive but not in the OSI-permissive allowlist, routed to human
license review (conservative, correct).

**Lane → our-seam map (the integration thesis):**

| Cluster | Representative repos | Maps to our seam | Lane |
|---|---|---|---|
| Vector stores | qdrant, weaviate, milvus, chroma, lancedb, marqo, vespa | `dense-vector-retrieve` / `hybrid-retrieve-fuse` backend | wrap |
| RAG frameworks | llama_index, haystack, R2R, llmware, txtai, Verba | `doc-to-markdown-rag-ingest`, retrieval family | inspiration/template |
| Rerankers | FlagEmbedding (bge), rerankers | `cross-encoder-reranker` scorer seam | wrap |
| Chunkers | chonkie, semchunk | `page-aware-chunker` / `recursive-character-chunker` | wrap |
| Agent frameworks | langgraph, autogen, crewai, smolagents, metagpt, autogpt, swarms | bounded-agent runtime (propose-never-truth, sandboxed) | wrap/foil |
| Prompt-opt | dspy | `system-prompt-builder` under the lossless law | integrate |
| Eval | ragas, deepeval, promptfoo, giskard, uptrain | the verification gate (scorers feed receipts) | wrap — VALIDATES thesis |
| Observability | langfuse, phoenix, openllmetry, helicone | the receipts plane (assurance-vs-logging) | complement |
| Guardrails | guardrails-ai, nemo-guardrails, llm-guard, rebuff | `prompt-injection-screen`, `clinical-abstention-gate` | wrap — VALIDATES thesis |
| PII / red-team | presidio, garak | redaction at intake / injection-screen hardening | wrap/inspiration |
| Doc parsing / OCR | unstructured, nougat, PaddleOCR (+ quarantined marker/surya/MinerU) | `doc-to-markdown-rag-ingest`, `on-device-ocr-prepass` | wrap |
| Inference serving | sglang, vllm/aibrix, TGI, TensorRT-LLM, llama.cpp, ollama | the inference gateway / `smart-router` | integrate |
| Memory | cognee, memobase | the `memory-*` family backends | wrap |
| Fine-tuning | LLaMA-Factory, unsloth, axolotl | the inference gateway (training jobs) | integrate |

**The standing finding, reconfirmed at scale:** the eval + guardrails clusters
**VALIDATE** our verification thesis (their pass/fail verdicts ARE the shape of our gates),
the observability cluster is **complement not foil** (it logs what happened, makes no
truth/promotion decision — assurance-vs-logging is the differentiator), and the
self-evolving agent-swarm cluster is **the foil, never our runtime** (sandbox-only, never
pip-install/execute). No single repo does verification + receipts + governed truth
promotion — the white space holds at 70-repo scale.
