# Context Compression Tools — research for the Baltor **Compress** module

**Date:** 2026-06-06. **Owner request:** "research compression tools like Headroom; we have not done
sufficient research on compression tools for the compression functionality." **Verify-first:** every tool
below was web-confirmed (sources at the bottom); anything not hard-confirmed is marked **⚠ verify before
adoption**. **Maps to:** Baltor.ai **Compress** module · the `compression` capability slot
(`_repos/shared-backend-components/architecture/external_capability_catalog.json`) · `CompressionProviderPort` · the Optimization stage.

> **Governing law — compression is never lossy of truth.** Per `_repos/shared-backend-components/docs/codex/lossless-distillation.md`,
> compression may shrink the *text surface* ONLY if answer-critical facts + source handles + held-out
> warnings survive, and a rollback/rehydration target exists. So we split the landscape into **reversible**
> (originals preserved, rehydratable — law-compliant by construction) vs **lossy/pruning** (must be gated by
> `compression-fidelity-check` + keep the raw layer). This distinction is the most important filter, not the
> compression ratio.

---

## 1. What we already have (don't duplicate)

- **`compression` capability slot** — `compression.stub@v1` (active; the shipped stdlib
  whitespace/structure-preserving compressor, lossless of words + source handles) + `compression.llmlingua@v1`
  (candidate primary, MIT).
- **Components:** `_repos/shared-backend-components/catalog/processors/compress/llmlingua-context.yaml`,
  `_repos/shared-backend-components/catalog/processors/compression/structural-compress.yaml`,
  `_repos/shared-backend-components/catalog/processors/retrieval/contextual-compressor.yaml`,
  `_repos/shared-backend-components/catalog/processors/retrieval/llmlingua-compress.yaml`,
  `_repos/shared-backend-components/catalog/processors/verify/compression-fidelity-check.yaml` (the fidelity gate),
  `_repos/shared-backend-components/catalog/patterns/input-token-compression.yaml`. Deterministic compression runs in
  `_repos/shared-backend-components/scripts/context_compress.py`.
- **The gap (why this doc exists):** the catalog references LLMLingua, but there was **no landscape survey** —
  no reversible-vs-lossy taxonomy, no comparison to the 2025–2026 tools (Headroom, EXIT, LLMLingua-2), and no
  decision on which become candidate adapters behind `CompressionProviderPort`.

---

## 2. Taxonomy of compression techniques (so we choose by mechanism, not hype)

| Technique | What it does | Lossless of truth? | Baltor fit |
|---|---|---|---|
| **Reversible / CCR** (compress-cache-retrieve) | Store originals locally; serve a compressed view; LLM/tool fetches the full item on demand | **Yes** (originals never deleted) | **Best fit** — matches the lossless law by construction |
| **Extractive** (sentence/span selection) | Keep the most query-relevant sentences/spans, drop the rest | Lossy but **citation-preserving** if spans carry handles | Strong fit, gate with fidelity check |
| **Token-pruning / perplexity** (LLMLingua family) | A small model drops low-information tokens | **Lossy** (token-level), can drop facts | Candidate, MUST gate + keep raw |
| **Abstractive / synthesis** (summarize) | Rewrite shorter | **Lossy + hallucination risk** | Avoid for truth-bearing facts; OK for non-critical prose |
| **Structural / AST** (JSON/code aware) | Compress structured payloads without losing structure | Mostly lossless of structure | Good for tool outputs / logs / code context |
| **KV-cache / prefix stabilization** | Stabilize prefixes for provider cache hits; compress the KV cache | Lossless (caching, not dropping) | Cost lever, complementary |
| **Provider-native prompt caching** (Anthropic/OpenAI/Gemini) | Cache repeated prefixes at the API | Lossless | Complementary, near-zero effort |
| **Semantic dedup** | Remove near-duplicate chunks | Lossy of duplicates only | Safe pre-pass |

**Implication for Baltor:** lead with **reversible + extractive (citation-preserving)**; treat token-pruning
as a gated candidate; never use abstractive on truth-bearing facts; layer KV/provider caching for cost.

---

## 3. The landscape (verified)

| Tool | Technique | License | Model dep | Lossless? | Maturity | Verdict for Baltor |
|---|---|---|---|---|---|---|
| **Headroom** (chopratejas/headroom) | Multi-algorithm: structural (JSON), AST (code), learned text model (Kompress-base), **CCR reversible**, KV-cache aligner, image router | **Apache-2.0** | Kompress-base HF model (GPU recommended, not required); calls **no external LLM** at compress time | **Yes (CCR)** + retrieval tool | **High** — 15.6k★, v0.23.0 (Jun 2026), MCP/proxy/lib/CLI | **Adopt as candidate primary.** Reversible design = native lossless-law fit; agentic-trace focus (tool outputs/logs/RAG) matches our worker context. Quality: GSM8K ±0.000, SQuAD v2 97%@19%, BFCL 97%@32% |
| **LLMLingua / LongLLMLingua / LLMLingua-2** (microsoft) | Token-pruning (small LM perplexity); LLMLingua-2 = task-agnostic token classification distilled from GPT-4; up to 20× | **MIT** | small LM (GPT2-small/LLaMA) or BERT-class classifier (LLMLingua-2, faster) | **No** (lossy token drop) | **High**, EMNLP'23 / ACL'24, widely used | **Keep candidate (LLMLingua-2 preferred).** Gate hard with `compression-fidelity-check`; keep raw layer. Good for long prose, not for fact lists |
| **EXIT** (ThisIsHwang/EXIT) | Context-aware **extractive** for RAG; classifies sentences preserving context deps; parallelizable | ⚠ verify (research code) | classifier model | Lossy but **extractive** (spans keep provenance) | Research / paper (arXiv 2412.12559) | **Candidate** — extractive + citation-preserving is the right shape; verify license + prod-readiness |
| **AdaComp** (arXiv 2409.01579) | **Adaptive** extractive — picks compression rate from query complexity + retrieval quality | ⚠ verify | predictor model | Lossy/extractive | Research paper | **Watch** — the adaptive-rate idea is worth borrowing into our selector |
| **BRIEF-Pro** (arXiv 2510.13799) | Universal context compression, short-to-long synthesis, multi-hop | ⚠ verify | model | Abstractive-leaning | Research paper (Oct 2025) | **Watch** — multi-hop reasoning compression; abstractive → truth-risk, study before use |
| **context-compressor** (Huzaifa785) | Library: extractive/abstractive/semantic/hybrid; 50–60% reduction | ⚠ verify (MIT-likely) | optional embeddings | Mixed (mode-dependent) | Small OSS lib | **Watch** — convenient multi-strategy API; lower maturity than Headroom/LLMLingua |
| **Compresr** (YC W26) | Commercial prompt/context compression | proprietary | n/a | n/a | YC-backed startup | **Competitor signal**, not a dependency — validates the market; do not adopt |
| **Provider-native prompt caching** (Anthropic/OpenAI/Gemini) | Prefix cache at the API | n/a (API feature) | none | Lossless | GA | **Use now** — complementary cost lever via canonical prompts (already in our pricing doc) |

---

## 4. Recommendation — what to wire, in what order

All behind **`CompressionProviderPort`** (a `CapabilityTask`-stable seam; cloud-defer-only-after-local-equivalent):

1. **Keep `compression.stub@v1` (active, local default).** Deterministic, lossless of words + handles — the
   offline correctness invariant. Never removed.
2. **Add `compression.headroom@v1` as the candidate *primary*.** Reversible CCR is the cleanest match to the
   lossless law (originals preserved + retrieval). Apache-2.0, mature, Python-first, no LLM at compress time.
   ⚠ Has a Rust component + a HF model (Kompress-base) → treat exactly like any external dep: contract test +
   local fallback (the stub) before it lands; do not import its SDK outside an approved adapter path.
3. **Keep `compression.llmlingua@v1` (prefer LLMLingua-2) as a gated candidate.** Token-pruning is lossy →
   every use MUST pass `compression-fidelity-check` (answer-critical facts + citations survive) and the raw
   layer is retained for rehydration.
4. **Catalog EXIT / AdaComp as extractive candidates** (citation-preserving). Borrow AdaComp's *adaptive
   compression rate* idea into our optimizer regardless of whether we adopt the code.
5. **Layer provider-native prompt caching + a KV/prefix stabilizer** (Headroom's CacheAligner does this) as a
   cost lever — lossless, low effort, big margin impact (matches `baltor-cloud-cost-pricing-pro-forma.md`).

**The Baltor differentiator (the pitch line):** competitors compress to save tokens. Baltor compresses
**under governance** — every compression emits a **fidelity delta + receipt**, preserves **source handles**,
keeps a **rehydratable raw layer**, and refuses to drop answer-critical facts. *Lean context, with proof.*
(Brand pillars: Verified · Current · **Efficient** · Provable — "Efficient", never "compression", as the
headline word, per `brand-architecture.md`.)

---

## 5. Adoption gate (every candidate, before it touches the served path)

```
CompressionProviderPort
  → compression.stub@v1            (local default, lossless, always available)
  → compression.headroom@v1        (candidate primary; reversible/CCR)
  → compression.llmlingua@v1       (candidate; lossy → fidelity-gated + raw retained)
  → ProviderUnavailableResult      (unconfigured → fall back to stub; never block)
```

Must hold (mirrors the execution-backend cloud-defer discipline): contract test exists · local equivalent
(the stub) exists · cataloged as candidate · `compression-fidelity-check` passes (answer-critical facts +
citations survive; fidelity delta recorded) · raw layer preserved + rehydration proven · no direct SDK import
outside the adapter · flywheel stays green.

---

## 6. Sources

- Headroom — https://github.com/chopratejas/headroom (Apache-2.0; reversible CCR; benchmarks)
- LLMLingua — https://github.com/microsoft/LLMLingua · https://www.microsoft.com/en-us/research/project/llmlingua/
- LongLLMLingua — https://arxiv.org/abs/2310.06839 · LLMLingua-2 (task-agnostic token classification)
- EXIT — https://github.com/ThisIsHwang/EXIT · https://arxiv.org/abs/2412.12559
- AdaComp — https://arxiv.org/abs/2409.01579 · BRIEF-Pro — https://arxiv.org/pdf/2510.13799
- context-compressor — https://github.com/Huzaifa785/context-compressor
- Compresr (YC W26, market signal) — https://yctierlist.com/w26/compresr/
- Context-engineering landscape — https://techsy.io/en/blog/best-context-engineering-tools

*Warrant: owner request (research compression tools) + ≥2 independent sources per adopted tool. No code adopted
in this pass — this is the research + the catalog decision. Honors the Lossless Distillation law and the
LOCKED brand ("Efficient", not "compression", as the headline pillar).*
