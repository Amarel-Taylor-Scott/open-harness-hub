# Descent method catalog — how to accomplish each dimension (generated)

> GENERATED from `architecture/descent_method_catalog.json` by `scripts/check_descent_method_catalog.py` — do not hand-edit. Updated 2026-06-20.

For each improvement DIMENSION (descent axis), the concrete METHODS to accomplish it, each grounded in a VARIETY of real candidate modules found by research (5 parallel reviewer agents, 2026-06-20). Discovery is NOT trust: every module is a candidate (license-flagged; copyleft/source-available/unstated/unverified are non-vendorable, adopt-behind-a-port only) that must pass its own intake + measured-lift before promotion. Extends architecture/descent_strategy_registry.json (the built strategies) with the broader method/module landscape.

Each module is a **candidate** (discovery ≠ trust). `[v]` = vendorable (clean permissive); `[port]` = copyleft/source-available/unstated/unverified → adopt behind a port, verify before use.

## `tokens_in` (5 methods)

- **prompt/context compression** — small-LM scores token salience, drops low-information tokens
  - [v] `microsoft/LLMLingua` — coarse-to-fine prompt+KV compression up to ~20x — MIT
  - [v] `3DAgentWorld/Toolkit-for-Prompt-Compression` — toolkit wrapping 5 compressors — MIT
  - [v] `liyucheng09/Selective_Context` — drops low-self-information units — MIT
- **prompt distillation (gist tokens)** — train the model to pack a prompt into few reusable cached tokens
  - [v] `jayelm/gisting` — compress prompts into reusable gist tokens (~26x) — Apache-2.0
  - [v] `microsoft/LLMLingua` — data-distilled small token-classifier compressor (LLMLingua-2) — MIT
- **KV/prefix cache reuse** — cache & reuse prefill KV blocks so repeated context isn't recomputed
  - [v] `LMCache/LMCache` — tiered KV-cache offload+reuse (CacheBlend) — Apache-2.0
  - [v] `vllm-project/vllm` — Automatic Prefix Caching — Apache-2.0
  - [v] `sgl-project/sglang` — RadixAttention prefix sharing — Apache-2.0
- **retrieval-instead-of-stuffing (RAG)** — retrieve only relevant chunks rather than stuffing the full corpus
  - [v] `run-llama/llama_index` — indexing + retrievers/routers — MIT
  - [port] `deepset-ai/haystack` — modular hybrid-search RAG — Apache-2.0 (unverified)
- **redundant-text dedupe** — strip near-duplicate text before it enters context
  - [port] `ekzhu/datasketch` — MinHash+LSH near-duplicate detection — MIT (unverified)

## `tokens_out` (4 methods)

- **grammar/schema constrained decoding** — mask logits each step so only schema-valid tokens emit
  - [v] `dottxt-ai/outlines` — structured generation (JSON Schema/regex/CFG) — Apache-2.0
  - [v] `mlc-ai/xgrammar` — near-zero-overhead CFG/JSON engine (vLLM/SGLang default) — Apache-2.0
  - [v] `guidance-ai/llguidance` — fast CFG constrained decoding (~50us/token) — MIT
- **typed/validated structured output** — define a schema, parse into a type, re-ask on failure
  - [v] `567-labs/instructor` — Pydantic-typed JSON, auto-validate+retry — MIT
  - [v] `BoundaryML/baml` — DSL for typed LLM functions, schema-aligned parsing — Apache-2.0
- **schema-filling wrappers** — wrapper writes the structural tokens, model generates only values
  - [v] `1rgs/jsonformer` — fills fixed JSON tokens, model fills values — MIT
- **native provider structured output** — provider enforces JSON Schema server-side
  - [port] `openai structured-outputs` — response_format json_schema strict — proprietary

## `cost` (4 methods)

- **model downgrade / cascade** — cheap model first, escalate only on a failed quality check (FrugalGPT)
  - [v] `lm-sys/RouteLLM` — strong-vs-weak cascade routers; ~85% cost cut — Apache-2.0
  - [port] `stanford-futuredata/FrugalGPT` — reference cascade impl — unverified
- **semantic/exact response caching** — return a stored answer for an identical or similar prompt
  - [v] `zilliztech/GPTCache` — embedding-based semantic cache — MIT
  - [v] `aurelio-labs/semantic-router` — embedding decision layer to gate cache-or-call — MIT
- **LLM gateway cost controls** — one OpenAI-compatible endpoint adds cost tracking, caching, budgets
  - [v] `BerriAI/litellm` — SDK+proxy to 100+ APIs, cost/budgets — MIT (enterprise/ separate)
  - [v] `Portkey-AI/gateway` — fast gateway, retries/fallbacks/caching — MIT
- **batch inference** — async submission for ~50% discount or self-host batching
  - [v] `vllm-project/vllm` — continuous batching + chunked prefill — Apache-2.0
  - [port] `openai batch API` — flat 50% discount, 24h SLA — proprietary

## `latency` (6 methods)

- **response/semantic caching** — return a stored answer for an identical or near-duplicate prompt, skipping inference
  - [v] `zilliztech/GPTCache` — semantic cache (~100x on hits) — MIT
  - [v] `BerriAI/litellm` — gateway response+semantic caching — MIT
- **prefix-cache / KV reuse** — cache KV of shared prefixes; recompute only the unique suffix -> big TTFT drop
  - [port] `LMCache/LMCache` — tiered KV-cache cross-request reuse — Apache-2.0 (unverified)
  - [v] `sgl-project/sglang` — RadixAttention longest-common-prefix reuse — Apache-2.0
- **speculative decoding** — a cheap draft proposes tokens; the target verifies in parallel -> fewer sequential passes
  - [port] `SafeAILab/EAGLE` — EAGLE-1/2/3 speculative decoding (~3x) — unverified
  - [port] `FasterDecoding/Medusa` — draft-free multi-head decoding — Apache-2.0 (unverified)
- **smaller/faster model routing** — route simple queries to a small/cheap model, reserve the big model for hard ones
  - [port] `lm-sys/RouteLLM` — strong-vs-weak routing at fixed quality — Apache-2.0 (unverified)
  - [v] `aurelio-labs/semantic-router` — embedding routing without an LLM call — MIT
- **continuous/dynamic batching** — interleave many in-flight sequences at token granularity to amortize weight loads
  - [v] `vllm-project/vllm` — continuous batching + PagedAttention — Apache-2.0
  - [v] `huggingface/text-generation-inference` — production serving + continuous batching — Apache-2.0 (old tags HFOIL, flag)
- **streaming** — emit tokens incrementally over SSE so perceived latency (TTFT) drops
  - [port] `vercel/ai` — streamText/SSE provider-agnostic helpers — Apache-2.0 (unverified)

## `llm_usage` (4 methods)

- **deterministic rule replacement** — compile/distill LLM decisions into rules or a small model
  - [v] `stanfordnlp/dspy` — compile modular LM programs into optimized prompts/weights — MIT
  - [v] `aurelio-labs/semantic-router` — swap LLM decision calls for vector-space matching — MIT
  - [v] `arcee-ai/DistillKit` — distill a large teacher into a small student — Apache-2.0
- **memoize/cache** — cache results so repeated asks don't re-call
  - [v] `zilliztech/GPTCache` — semantic cache (similarity hits) — MIT
  - [port] `langchain-ai/langchain` — set_llm_cache exact-match call cache — MIT (unverified)
- **fewer agent hops** — compile/optimize agent graphs; parallelize round-trips
  - [port] `langchain-ai/langgraph` — graph runtime with fan-out/fan-in — MIT (unverified)
  - [v] `zou-group/textgrad` — textual-gradient prompt optimization → leaner program — MIT
- **tool-use instead of generation** — call a tool/function for a fact rather than generating it
  - [v] `BerriAI/litellm` — native function/tool calling + parallel_tool_calls — MIT

## `determinism` (4 methods)

- **LLM->rule / source-bound extraction** — LLM proposes structure, code disposes; bind every field to a source span
  - [v] `google/langextract` — structured extraction mapped to exact source char-span — Apache-2.0
- **grammar/schema constrained decoding** — only grammar-valid tokens emit → 100% structural correctness
  - [v] `mlc-ai/xgrammar` — CFG/JSON/regex constrained generation — Apache-2.0
  - [v] `guidance-ai/guidance` — interleave control + constrained gen — MIT
- **formal verification** — discharge proof obligations on LLM output via a solver
  - [port] `Z3Prover/z3` — SMT solver — MIT (unverified)
  - [port] `leanprover/lean4` — formal proof assistant — Apache-2.0 (unverified)
- **finite-state/DSL compilation** — compile NL intent into a deterministic state machine
  - [port] `statelyai/xstate` — statecharts for predictable logic — MIT (unverified)

## `verifiability` (4 methods)

- **lineage/provenance** — emit run->job->dataset lineage in a portable standard
  - [v] `OpenLineage/OpenLineage` — open lineage standard + collectors — Apache-2.0
- **cryptographic receipts/attestation** — sign artifact+context; land proof on a transparency log
  - [port] `sigstore/cosign` — keyless signing + transparency log — Apache-2.0 (unverified)
  - [port] `in-toto/in-toto` — supply-chain attestation framework — Apache-2.0 (unverified)
- **grounding/hallucination detection** — check each claim against evidence; flag unsupported spans
  - [v] `amazon-science/RefChecker` — knowledge-triplet hallucination checks — Apache-2.0
- **cross-source corroboration** — retrieve from multiple independent sources, aggregate agreement
  - [port] `Cartus/Automated-Fact-Checking-Resources` — graph-based evidence aggregation (GEAR) — unverified

## `reliability` (4 methods)

- **multi-provider failover gateway** — one unified API; auto-reroute on provider failure
  - [v] `BerriAI/litellm` — Router retry/fallback/load-balancing — MIT
  - [v] `Portkey-AI/gateway` — failover/load-balancing/retries — MIT
- **retries with backoff** — re-issue transient-failed calls with exponential backoff + jitter
  - [v] `jd/tenacity` — general-purpose Python retry — Apache-2.0
- **circuit breakers** — stop calling a failing dependency after a threshold; probe to re-close
  - [port] `danielfm/pybreaker` — Python circuit breaker — BSD-3 (unverified)
  - [v] `resilience4j/resilience4j` — JVM breaker/retry/bulkhead — Apache-2.0
- **fallback chains** — ordered providers tried until one succeeds
  - [port] `langchain-ai/langchain` — Runnable.with_fallbacks() — MIT (unverified)

## `resilience` (3 methods)

- **durable execution / checkpoint-resume** — checkpoint each step; auto-resume from last completed on crash
  - [v] `temporalio/temporal` — durable workflows, auto retry/resume — MIT
  - [port] `dbos-inc/dbos-transact-py` — Postgres-checkpointed durable workflows — MIT (unverified)
- **self-healing supervisor/restart** — a supervisor watches processes and restarts with backoff
  - [port] `Supervisor/supervisor` — process control/restart — BSD-derived (unverified)
- **graceful degradation** — on partial failure return a reduced useful answer (cached/smaller/partial)
  - [port] `langchain-ai/langchain` — with_fallbacks to cached/smaller model — MIT (unverified)

## `locality` (3 methods)

- **local inference runtime** — run the model on owned hardware behind a stable API
  - [v] `ollama/ollama` — pull/run GGUF models locally + REST — MIT
  - [v] `ggml-org/llama.cpp` — C/C++ CPU/Metal/CUDA inference — MIT
  - [v] `vllm-project/vllm` — high-throughput GPU serving — Apache-2.0
- **edge/on-device models** — compile the model to run on phone/embedded/browser
  - [v] `mlc-ai/mlc-llm` — TVM-compiled universal deployment — Apache-2.0
  - [v] `pytorch/executorch` — ~50KB on-device PyTorch runtime — BSD
- **no-egress network policy** — default-deny egress so a workload cannot call out
  - [port] `cilium/cilium` — eBPF egress policy default-deny — Apache-2.0 (eBPF GPL/BSD split)

## `privacy` (4 methods)

- **PII detection + redaction** — NLP+regex find entities, then mask before the LLM sees them
  - [v] `microsoft/presidio` — PII detect/redact/anonymize — MIT
  - [v] `guardrails-ai/guardrails_pii` — Presidio-backed PII validator — Apache-2.0
- **tokenization/pseudonymization** — replace identifiers with reversible tokens or k-anon generalizations
  - [v] `arx-deidentifier/arx` — k-anonymity/l-diversity/t-closeness/DP — Apache-2.0
- **differential privacy** — calibrated noise bounds per-record influence
  - [v] `google/differential-privacy` — DP building blocks — Apache-2.0
  - [v] `meta-pytorch/opacus` — DP-SGD training with budget tracking — Apache-2.0
- **synthetic data** — model that reproduces statistical shape without real records
  - [port] `sdv-dev/SDV` — tabular synthetic data — BSL (source-available, flag)
  - [v] `joke2k/faker` — rule-based fake values — MIT

## `safety` (3 methods)

- **sandboxing (microVM/userspace-kernel)** — virtualize/intercept syscalls so untrusted code can't reach the host
  - [v] `google/gvisor` — userspace kernel runsc OCI runtime — Apache-2.0
  - [v] `firecracker-microvm/firecracker` — microVM VMM ~125ms boot — Apache-2.0
  - [v] `google/nsjail` — namespaces/cgroups/seccomp-bpf — Apache-2.0
- **policy engines** — decisions evaluated against declarative policy, separate from app code
  - [v] `open-policy-agent/opa` — Rego policy engine — Apache-2.0
  - [port] `cedar-policy/cedar` — formally-verified authz language — Apache-2.0 (unverified)
- **LLM guardrails (I/O rails)** — filter/transform prompts before + responses after by rules/classifiers
  - [v] `NVIDIA-NeMo/Guardrails` — programmable I/O/topical rails — Apache-2.0
  - [v] `guardrails-ai/guardrails` — 65+ validators into I/O guards — Apache-2.0

## `specialization` (4 methods)

- **LoRA/PEFT/QLoRA fine-tuning** — attach low-rank adapters; train a tiny delta on consumer GPUs
  - [v] `huggingface/peft` — canonical LoRA/QLoRA library — Apache-2.0
  - [v] `unslothai/unsloth` — fused kernels for ~2x faster LoRA/QLoRA — Apache-2.0
  - [v] `huggingface/trl` — SFT/DPO/RLHF trainers — Apache-2.0
- **knowledge distillation** — transfer teacher capability into a smaller student
  - [v] `arcee-ai/DistillKit` — production KD toolkit — Apache-2.0
- **few-shot classifier heads** — fine-tune embeddings + a light head, no prompts
  - [v] `huggingface/setfit` — prompt-free few-shot classification — Apache-2.0
- **rerankers/embedding models** — swap a frontier call for a cross-encoder reranker on top-k
  - [v] `huggingface/sentence-transformers` — embedding + reranker models — Apache-2.0
  - [port] `FlagOpen/FlagEmbedding` — BGE embeddings + rerankers — MIT (unverified)

## `portability` (3 methods)

- **open context/skill/agent formats** — represent knowledge & tools in a vendor-neutral spec
  - [v] `GoogleCloudPlatform/knowledge-catalog` — OKF v0.1 (markdown+YAML) — Apache-2.0
  - [port] `modelcontextprotocol/modelcontextprotocol` — MCP tool/data interface — MIT (unverified)
  - [port] `opensanctions/followthemoney` — FtM entity data model — MIT (unverified)
- **standard data/provenance schemas** — emit lineage/metadata in interoperable standards
  - [v] `OpenLineage/OpenLineage` — open lineage standard — Apache-2.0
  - [port] `mlcommons/croissant` — ML dataset metadata on schema.org/JSON-LD — Apache-2.0 (unverified)
- **OpenAI-compatible abstraction** — one interface for 100+ providers; swap vendors freely
  - [v] `BerriAI/litellm` — 100+ APIs in OpenAI format — MIT
  - [v] `ollama/ollama` — local runner w/ OpenAI-compatible API — MIT

## `freshness` (4 methods)

- **change-data-capture (CDC)** — stream row-level DB changes as events to keep derived data current
  - [port] `debezium/debezium` — CDC for Postgres/MySQL/Mongo — Apache-2.0 (unverified)
- **source polling / scheduled re-sync** — pull from authoritative APIs on a schedule via standard taps
  - [v] `meltano/sdk` — Singer SDK for taps/targets — Apache-2.0
  - [port] `airbytehq/airbyte` — 250+ ELT connectors — ELv2 (source-available, flag)
- **cache invalidation on source change** — evict/refresh caches the moment the source mutates
  - [port] `janbjorge/PGCacheWatch` — Postgres LISTEN/NOTIFY -> cache invalidation — unverified
- **webhooks / event triggers** — push notifications from the source the instant data changes
  - [v] `svix/svix-webhooks` — open-source webhook send/receive service — MIT

## `reproducibility` (3 methods)

- **data/experiment + version pinning** — tie data+model+params to a commit so a run is re-derivable
  - [port] `iterative/dvc` — data/model versioning tied to Git — Apache-2.0 (unverified)
  - [port] `mlflow/mlflow` — experiment tracking into repeatable runs — Apache-2.0 (unverified)
- **record/replay logs** — capture real LLM/HTTP calls once, replay deterministically in tests
  - [port] `vcr/vcr` — cassette record/replay of HTTP — MIT (unverified)
- **content-addressed hashing** — hash content -> CID; identity changes iff bytes change
  - [port] `ipfs/kubo` — content-addressed Merkle-DAG store — MIT/Apache (unverified)

## `energy` (3 methods)

- **quantization** — reduce weight precision (INT8/INT4/FP8) -> less memory+compute per token
  - [v] `ggml-org/llama.cpp` — GGUF 2-8 bit quant, CPU — MIT
  - [port] `bitsandbytes-foundation/bitsandbytes` — 8/4-bit (NF4) quant for QLoRA — MIT (unverified)
- **small models on CPU** — run 1-7B Q4 models on CPU/edge instead of GPU
  - [v] `ggml-org/llama.cpp` — CPU/ARM/Apple-Silicon inference — MIT
  - [port] `ml-explore/mlx` — Apple-Silicon inference — MIT (unverified)
- **green-compute / carbon-aware scheduling** — shift jobs to lowest grid carbon intensity; measure footprint
  - [port] `Green-Software-Foundation/carbon-aware-sdk` — carbon-aware time/region scheduling — MIT (unverified)
  - [port] `mlco2/codecarbon` — measure energy + regional CO2 — MIT (unverified)

