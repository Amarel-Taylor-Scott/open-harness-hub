# Recommended stack (cost-aware) + the cloud decision

The single recommended technology set for the shared backend, each layer with **the pick**, **the
alternatives**, and **the cost note** — plus the Cloudflare Vectorize verdict and the cloud split.
Grounds [[two-services-shared-infrastructure.md]] and [[context-enrichment-service.md]] in concrete
tech. Picks favor cost-awareness and avoiding lock-in; swap freely as scale dictates.

## The stack, start to finish

### Document pipeline
| Layer | Pick | Alternatives | Cost note |
|---|---|---|---|
| **Raw / source-of-truth store** | **Cloudflare R2** | S3 (Object Lock, FedRAMP/HIPAA, deep AWS); Backblaze B2 (~60% cheaper at rest, loses the edge story) | $0 egress is decisive for a serve-and-download product |
| **Retrieval index** | **pgvector first → Qdrant when you outgrow it** | object-storage-native (Turbopuffer / Mixpeek-on-R2) past ~100M vectors | pgvector cheapest if you already run Postgres, competitive <~50–100M vectors + hybrid in one engine; Qdrant ~4ms p50; bills run **2.5–4× the pricing page**; 1M docs @3072-dim ≈ 12GB raw |
| **Compressed tier** | **Repomix (code) · LLMLingua-2 (prose)** | gitingest, code2prompt, selective-context | Repomix ~70% (strip bodies, keep signatures), MCP + Claude Code plugin; LLMLingua-2 3–6× faster than v1 at 2–5×; general 5–20× |

### Cross-cutting
| Layer | Pick | Alternatives | Cost note |
|---|---|---|---|
| **Sync / freshness (CDC)** | **native connector sync + a queue** (Rovo MCP, GitLab MCP → Cloudflare Queues/SQS + scheduled re-embed) | **Onyx** (batteries-included OSS ingestion+sync, 40+ connectors, self-host) | build vs. buy; Onyx if you'd rather not own the plumbing |
| **Adversarial / security** | **promptfoo** (red-team: injection, PII leak, guardrails; 500+ vectors) | Lakera, Rebuff, NeMo Guardrails | **non-negotiable** for a service ingesting other people's content |
| **Verification / measurement** | **Braintrust** (or **Langfuse** OSS) **+ lm-eval-harness** | — | this IS the lift/fidelity engine — **wrap it, don't rebuild it**; Langfuse self-hostable (20k+★) |

### Runtime
| Layer | Pick | Alternatives | Cost note |
|---|---|---|---|
| **Inference + serving** | **vLLM on Kubernetes; MCP as the protocol** | LlamaIndex (retrieval), LangGraph/CrewAI (agents) | vLLM serves embeddings *and* generation; MCP is the convergence point for feeding agents |
| **Caching** | **provider prompt cache → semantic cache; LiteLLM gateway** | GPTCache, Redis LangCache, LMCache | prompt cache ~90% off input + context engine 40–60% — **free before you build anything** |
| **Hyper-efficient / memory** | **Mem0 (distilled) + token-efficient packaging** | Hindsight (recall-network), Zep/Graphiti (temporal) | value compounds when the dense artifact lands on a cacheable prefix |

**Substrate:** Kubernetes + Karpenter (autoscaling GPU nodes) · Ray (distributed embed/generate) ·
Postgres doubling as pgvector.

## The Cloudflare Vectorize verdict

**Interesting, but not the primary store.** Two hard problems: (1) **no hybrid search** — and BM25+vector
is the mature middle for any serious retrieval product; (2) pricing is **per queried + stored vector
dimension**, which scales unpredictably with dimension count and query volume. It fits **one** case:
already all-in on Cloudflare *and* retrieval is pure-semantic (its 50,000 namespaces × 5M-vector cap
suits a tenant model). **Verdict:** run pgvector/Qdrant as the system of record; keep Vectorize as an
optional **edge cache for hot, semantic-only lookups**.

## Cloud: split by egress, not by brand

For a host-and-serve product the deciding cost is **egress**, and it's lopsided: **R2 $0.00/GB** vs
**S3 $0.09 · GCP $0.12 · Azure $0.087** (verified Apr 2026). 10TB/mo serving ≈ **$15 on R2 vs ~$891 in
S3 egress alone**. But R2 can't carry everything — request fees remain (Class A $4.50/M, B $0.36/M),
S3 still wins for FedRAMP/HIPAA + complex lifecycle + multi-region (the regulated wedge), and Workers
AI runs Cloudflare's catalog, **not arbitrary vLLM GPU at scale**.

**The answer is a data-gravity-aware hybrid:**
- **Edge / storage / serving** (the CDN-like Baltor surface) → **Cloudflare R2 + Workers + free CDN.**
  Zero egress on every download and MCP serve.
- **Heavy GPU** (vLLM, embedding at scale, the foundry, measurement) → a **GPU cloud co-located with
  its data** — a hyperscaler if the wedge needs FedRAMP/HIPAA, or a specialized GPU provider (Modal,
  RunPod, Lambda, CoreWeave) for cost. Keep vectors + Postgres **next to the GPU** (no egress between
  inference and storage); serve only finished artifacts from R2.
- **Break-even:** the split pays off above ~$400/mo in S3 egress — which a serving product clears
  immediately.

## The SaaS — two faces of one product

The two phrasings are two faces, not two products:
- **Compression / efficiency face** — sells token-efficiency. The raw capability is **commoditizing**
  (Repomix free, prompt caching free), so "we compressed your docs" alone is thin. The defensible
  version sells what the free tools don't: **measured fidelity per tier, hosting + freshness, and
  multi-format delivery** (MCP · skill · packed file · llms.txt).
- **Context-layer face** — sells **governed context products**: corpora turned into retrievable,
  provenance-bearing, freshness-tracked context for open agents. The gap is explicit: no RAG platform
  solves the upstream **data-governance** problem; **MCP moves context, it does not produce it**
  (Gartner: 60% of MCP-only agentic projects fail by 2028 without a consistent layer beneath). Baltor
  *produces* that layer for the open-agent world — the part nobody hosts.

**Pricing boundary (falls out of the architecture):** raw + compressed are **freezable** (download,
one-time/storage); **hyper-efficient served live = recurring** (a static download can't stay current —
the CDC/freshness moat). The metered middle (per source scanned, per token compressed/embedded) funds
the foundry. Buyer pool is **broader than OHH's** — anyone running Claude Code / open agents at scale
who wants governed, cheap, fresh context without building a bounded pipeline.

**The one thread:** the whole SaaS rests on the same guarantee as OHH's lift gate — **measured
tier-fidelity**. That's why one backend, two doors isn't just infra economy — it's *the same moat sold
through two doors*.
