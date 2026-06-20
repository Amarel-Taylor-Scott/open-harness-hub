# Retrieval & Prompt-Engineering Taxonomy (canonical)

The decision-useful menu of **retrieval** and **prompt-engineering** components,
turned into the product's two-layer offer:

- a **FLEXIBLE component menu** — every atomic step is a swappable component with
  options, a one-line pro/con per option, and a recommended default; and
- **RECOMMENDED templated bundles** — off-the-shelf compositions of those atomic
  components ("Standard hybrid RAG", "High-precision legal RAG", "Cheap
  keyword-first", "Agentic/CRAG") that lock in defaults so an engineer can start
  from a working stack and only swap what their domain demands.

This is the single reference for *which retrieval/prompt component to pick and
why*. It is **aligned with the existing product model**, not a parallel one:

- Vocabulary is the canonical product vocabulary — **components / subcomponents**,
  **Knowledge Corpus**, **Conditional**, **Action** (see
  [`component-taxonomy-and-stages.md`](component-taxonomy-and-stages.md) for the
  seven primitives, and [`../design/value-propositions.md`](../design/value-propositions.md)
  for the words). Retrieval-research source names like "If Statement", "rule
  pack", "knowledge pack" are NOT used here.
- The atomic ordering mirrors the canonical governed-model-call recipe
  (`harness_recipe` in `scripts/showcase/builder.py`) exactly — these are the
  **THEN steps that run once the Trigger gate admits an input**, not a new flow.
- **Lift is pipeline-level.** No single retrieval or prompt component carries a
  lift number; the assembled pipeline shows `▲ +Δ` over the bare model. A
  component here shows *where it fits* and its evidence/sources, per
  value-prop 1. Most of these steps are deterministic and **freezable** (Conditionals,
  keyword/regex retrieval, chunking, fusion, compression, injection checks,
  output verification) — they cost no model tokens — which is exactly why the
  bundles below "add lift without adding cost" (value-prop 3).

Research basis: **356 retrieval + prompt-engineering techniques** cataloged across
ten domains (lexical & fuzzy retrieval; semantic & hybrid retrieval; query
transformation; chunking strategies; reranking & fusion; summarization & context
compression; context assembly & placement; agentic & LLM-assisted RAG; prompt
engineering techniques; RAG evaluation & tool landscape). The atomic steps and
bundles below are the decision-useful distillation; representative citations are
attached per option.

---

## How to read this document

The retrieval sub-pipeline is a chain of **ordered atomic steps**. Each step is
**optional and swappable**: a step is a *slot*, and each method below is a
*component* that fills it. You assemble a pipeline by choosing one (or none) per
slot. The bundles in §2 are pre-filled chains.

```
                ┌─────────────────────── the RETRIEVAL sub-pipeline ───────────────────────┐
Input ─▶ [R0 Query transform] ─▶ [R1 Retrieve (method)] ─▶ [R2 Chunk*] ─▶ [R3 Rerank/Fuse]
       ─▶ [R4 Summarize/Compress] ─▶ [R5 Select · order · de-conflict] ─▶ [R6 Place in prompt] ─┐
                                                                                                 │
       ┌──────────────────────── the PROMPT-ENGINEERING steps ───────────────────────────┐     │
       │ [P1 Persona] ─▶ [P2 System prompt] ─▶ [P3 Few-shot] ─▶ [P4 Output schema]         │ ◀───┘
       │ ─▶ [P5 Injection defense] ─▶ ▶▶ the Action (model call) ▶▶                         │
       └───────────────────────────────────────────────────────────────────────────────────┘
* Chunking (R2) is an INDEX-TIME decision in most stacks (it shapes what R1 can
  return) but is placed here because it is co-designed with retrieval. See R2.
```

Every step's **primitive** and its **slot in `harness_recipe`** are in the §3
mapping table.

---

## 1. The atomic steps (the flexible component menu)

For each step: the swappable method options, a one-line pro / con per major
option, the recommended **DEFAULT** and why, and representative citations.

### R0 — Query transform *(Action; optional, model-assisted or deterministic)*

Reshape the user/runtime query before it hits the retriever, to close the
query-document gap. Maps to `harness_recipe` as a pre-call **Action** that runs
before knowledge retrieval (a query-side companion to "Build the system prompt").

| Option | Pro | Con |
|---|---|---|
| **None (raw query)** | Zero latency/cost; no drift | Vocabulary/format mismatch unaddressed |
| **Synonym / ontology expansion** (WordNet, UMLS, MeSH) | Auditable, zero-inference, high precision in controlled vocab | Word-sense errors on short queries; ontology curation cost |
| **Pseudo-Relevance Feedback** (Rocchio / RM3) | Fully automatic recall lift; no labels | Topic-drift if first pass is bad; +1 retrieval round |
| **Query2Doc** (LLM pseudo-doc, concat to query) | +3–15% BM25 on MS-MARCO/TREC, no fine-tune | One LLM call; single-shot hallucination risk |
| **HyDE** (hypothetical-doc embedding centroid) | Strong zero-shot dense; bridges short-query↔long-doc | Hallucinated hypotheticals add noise; +1 LLM call |
| **Multi-Query / RAG-Fusion** (N rephrasings → union or RRF) | Covers multiple phrasings; recall lift; RRF de-dupes | N× retrieval; noisy variants survive a single high rank |
| **Step-Back** (abstract the over-specific query) | ~21.6% error cut on specific→general tasks; cheap | Counterproductive on already-broad queries |
| **Query decomposition / sub-questions** | Essential for multi-hop/comparative; +MRR, +F1 | Many LLM + retrieval rounds; overkill for single-hop |
| **Self-Query / metadata-filter extraction** | Pre-filters by hard constraints before similarity | Needs a populated, queryable metadata schema |
| **Conversational decontextualization** (resolve anaphora) | Mandatory for multi-turn; any retriever | Long history inflates cost; over/under-specify risk |

**DEFAULT: None for single-turn factual lookups; add HyDE *or* Query2Doc for
short/conversational queries against long technical corpora; add conversational
decontextualization whenever the surface is multi-turn.** Rationale: query
transforms are the cheapest way to lift recall without re-indexing, but each adds
an LLM call and drift risk — so apply them only where the query↔doc gap is real.
Multi-Query/RAG-Fusion is the recall escalation when a single transform is
insufficient; decomposition is reserved for genuinely multi-hop questions.

Citations: HyDE — <https://arxiv.org/html/2509.07794>,
<https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde>;
Query2Doc — <https://arxiv.org/abs/2303.07678>,
<https://aclanthology.org/2023.emnlp-main.585/>; Step-Back —
<https://www.dmflow.chat/en/blog/rag-query-transformation-guide-6-advanced-architectures>;
Decomposition — <https://arxiv.org/pdf/2507.00355>; Self-Query —
<https://towardsdatascience.com/how-to-build-a-rag-system-with-a-self-querying-retriever-in-langchain-16b4fa23e9ad/>;
Conversational rewrite — <https://arxiv.org/pdf/2305.15645>.

### R1 — Retrieve (method) *(Knowledge Corpus, typed by `retrieval`; ≥1 leg)*

Pull candidate facts from a **Knowledge Corpus**. The method *is* the corpus's
`retrieval` trigger (keyword / regex / exact-id / rag_vector / classifier /
graph). One or more legs run in parallel.

| Method (≈ `retrieval`) | Pro | Con |
|---|---|---|
| **BM25 / lexical** (`keyword`) | ~94% recall on exact-match queries; zero inference; interpretable; exact rare-term/code/ID match | Vocabulary mismatch ("heart attack"≠"cardiac arrest"); no semantics |
| **BM25F (field-weighted)** (`keyword`) | Title/heading boosted without extra passes; index-time structure | Field-weight tuning is critical; needs structured docs |
| **Trigram / `pg_trgm`, edit/phonetic** (`regex`/fuzzy) | Substring/typo/name matching in-DB; language-agnostic | Character-level only; not a semantic ranker |
| **Exact-id lookup** (`exact_id`) | Deterministic hit on CVE/NDC/FIPS/K-number/SKU | Only fires when the identifier is present |
| **Dense bi-encoder + ANN** (`rag_vector`) | Sub-ms semantic recall; paraphrase/synonymy | Single-vector bottleneck; weak on exact tokens; re-index on model change |
| **SPLADE / learned sparse** (`rag_vector`+`keyword`) | Semantic *and* inverted-index-compatible; beats BM25 on BEIR | Neural inference at index/query; English-tokenizer bound |
| **ColBERT late-interaction** (`rag_vector`) | Best out-of-domain generalization; token-level match | 10–100× storage; needs PLAID, not stock ANN |
| **BGE-M3 (dense+sparse+ColBERT, one model)** | One model → hybrid; strong multilingual | ~560M params; not top on English-only MTEB |
| **Classifier / graph** (`classifier`/`graph`) | Recordability/abstention gates; multi-hop relations | Needs trained classifier / KG coverage |

ANN index choice (within a dense/sparse leg): **HNSW** (best recall/speed ≤~100M
vectors) · **IVF / IVF-PQ** (memory-constrained, filtered, or billion-scale) ·
**ScaNN / DiskANN** (100M–1B). Compression: **scalar int8** (default, ~4×, <3%
nDCG drop) → **binary + rescore** (32×, cost-sensitive 250M+). **Matryoshka
(MRL)** truncation tunes cost↔quality at query time.

**DEFAULT: a hybrid of one lexical leg (BM25) + one dense leg (bi-encoder on
HNSW, scalar-quantized).** Rationale: BM25 is non-negotiable as the leg that
*guarantees* exact surface-form matching for rare terms, codes, identifiers and
named entities — exactly the cases where embeddings generalize too broadly and
fabricate — while the dense leg covers paraphrase/synonymy. SPLADE is the
recommended evolution when BM25 recall is the bottleneck but full dense infra
isn't yet in place; ColBERT/BGE-M3 when out-of-domain generalization or
multilingual coverage dominates over storage/latency.

Citations: BM25 — <https://en.wikipedia.org/wiki/Okapi_BM25>,
<https://www.lancedb.com/blog/hybrid-search-combining-bm25-and-semantic-search-for-better-results-with-lan-1358038fe7e6>;
Dense/HNSW — <https://oneuptime.com/blog/post/2026-01-30-dense-retrieval/view>,
<https://qdrant.tech/course/essentials/day-2/what-is-hnsw/>; SPLADE —
<https://qdrant.tech/articles/modern-sparse-neural-retrieval/>,
<https://arxiv.org/abs/2109.10086>; ColBERT — <https://arxiv.org/abs/2511.00444>;
BGE-M3 — <https://huggingface.co/BAAI/bge-m3>; quantization —
<https://huggingface.co/blog/embedding-quantization>; MRL —
<https://arxiv.org/abs/2205.13147>; `pg_trgm` —
<https://www.postgresql.org/docs/current/pgtrgm.html>.

### R2 — Chunk *(Action: Transform; index-time, co-designed with R1)*

Split corpus documents into retrievable units. This is **mostly an index-time
decision** (it shapes what R1 can return) but is co-designed with retrieval, so
it lives in the retrieval sub-pipeline. In `harness_recipe` the *read-time* half
of multi-granularity strategies (parent/window expansion) rides inside Knowledge
retrieval.

| Option | Pro | Con |
|---|---|---|
| **Fixed-size + overlap** | Trivial, predictable | Splits mid-thought; ignores structure |
| **Recursive character** (separator hierarchy) | Respects paragraph/sentence boundaries; library default | Still size-driven, not meaning-driven |
| **Page/structure-aware** (headings, tables, page anchors) | Preserves citable anchors; clean tables | Needs structured source (PDF/HTML) |
| **Parent-child / hierarchical** | Small-chunk precision + large-chunk context | Two storage layers; doubled tuning |
| **Sentence-window** | Sentence-precision match, read-time expansion | Fails on tabular/scattered facts |
| **Semantic chunking** (embedding-boundary) | Coherent units | Embedding cost at index time |

**DEFAULT: recursive-character chunking (~256–512 tokens, ~10–15% overlap) with
page/structure-aware boundaries when the source has them; switch to parent-child
when retrieved passages feel too short for generation.** Rationale: recursive is
the robust general default; parent-child resolves the precision↔context tension
that single-granularity chunking forces, and is standard for long-form PDFs and
manuals.

Citations: Parent-child —
<https://medium.com/@seahorse.technologies.sl/parent-child-chunking-in-langchain-for-advanced-rag-e7c37171995a>,
<https://kuriko-iwai.com/research/rag-chunking-strategies-technical-guide>;
Sentence-window — <https://pixion.co/blog/rag-strategies-baltor>.
(Catalog components implementing this step: `processor/recursive-character-chunker`,
`processor/page-aware-chunker`.)

### R3 — Rerank / Fuse *(Action: rerank, and/or Conditional fusion policy)*

Two distinct jobs, often both present: **fuse** multiple retrieval legs into one
list, then **rerank** the merged top-k with a high-precision model. In
`harness_recipe` this is the "Knowledge ranking" step.

**Fusion** (combine legs — choose by whether you have labels):

| Option | Pro | Con |
|---|---|---|
| **Reciprocal Rank Fusion (RRF, k≈60)** | No score normalization; robust; native in OpenSearch/Qdrant/Elastic | Discards score magnitude; k-sensitive |
| **Convex combination (weighted, tuned α)** | Beats RRF when ≥50 labeled pairs exist; keeps magnitude | Needs labeled data; α may not generalize across query types |
| **Distribution-Based Score Fusion (DBSF)** | Handles incompatible/unbounded score distributions | Needs stable per-retriever distribution; less benchmarked |
| **Weighted RRF** | RRF robustness + retriever prioritization, no labels | Still magnitude-blind; manual weights |

**Rerank** (rescore merged top-k — a cross-encoder jointly reads query+doc):

| Option | Pro | Con |
|---|---|---|
| **No rerank** | Lowest latency/cost | Misses the largest single precision lift |
| **Cross-encoder (hosted: Cohere Rerank 4 Pro / Voyage Rerank 2.5)** | ~40%+ recall@k / MRR lift; SOTA | API cost + 200–500ms/batch; license traps (some non-commercial) |
| **Cross-encoder (open-weight: BGE-reranker-v2-m3, Apache-2.0)** | Self-hostable, commercial-safe | GPU to serve |
| **ColBERT late-interaction rerank** | Token-level precision, OOD-robust | Storage/infra overhead |
| **LLM-as-reranker** | Strongest reasoning over relevance | Highest cost/latency |

**DEFAULT: RRF for fusion (switch to convex combination once you have ≥50
labeled query-doc pairs), followed by a cross-encoder reranker on the fused
top-50→100 → keep top-5.** Rationale: RRF needs no calibration data and safely
mixes BM25 scores with cosine similarities; the cross-encoder rerank is the
single highest-precision lever in the pipeline and its cost is bounded by
candidate count, not corpus size. Skip rerank only when the candidate pool is
already ≤5.

Citations: RRF —
<https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/>,
<https://arxiv.org/abs/2210.11934>; convex combination —
<https://arxiv.org/abs/2210.11934>,
<https://app.ailog.fr/en/blog/guides/hybrid-retrieval-fusion>; DBSF —
<https://qdrant.tech/blog/qdrant-1.11.x/>; cross-encoder rerankers —
<https://www.bestaiweb.ai/how-to-add-reranking-to-your-rag-pipeline-with-cohere-rerank-4-pro-voyage-rerank-2-5-and-zerank-2-in-2026/>,
<https://docs.cohere.com/docs/rerank>,
<https://bigdataboutique.com/blog/rag-reranking-improving-retrieval-quality-with-cross-encoders>.
(Catalog: `processor/cross-encoder-reranker`, `processor/gemma-reranker`,
`rule-pack/hybrid-retrieval-policy`.)

### R4 — Summarize / Compress *(Action: Transform; optional)*

Reduce the reranked context to the salient cited spans before it enters the
prompt — cut tokens, cost, and "lost-in-the-middle" dilution. In `harness_recipe`
this is the "Knowledge summarizing" step.

| Option | Pro | Con |
|---|---|---|
| **None (pass full chunks)** | No information loss; no extra call | Most tokens, most dilution |
| **Extractive span selection** (deterministic) | Cheap, faithful, keeps exact citable text | Coarser than abstractive |
| **Contextual compression** (LLM extracts query-relevant spans) | Strong token cut; keeps relevance | +1 model call; can drop nuance |
| **Abstractive summary** (small model rewrites) | Densest; fluent | Paraphrase weakens citation; hallucination risk |

**DEFAULT: none for small contexts; extractive span selection (then optional
small-model compression with `gemma`-class models) when the reranked context
exceeds the budget.** Rationale: compression is freezable-friendly when
extractive (no model tokens) and preserves the exact spans citations point at;
reserve abstractive summarization for when token budget genuinely forces it,
because paraphrase erodes the provenance the product depends on.

Citations: baltor/compression —
<https://pixion.co/blog/rag-strategies-baltor>; reranking-as-compression
context —
<https://bigdataboutique.com/blog/rag-reranking-improving-retrieval-quality-with-cross-encoders>.

### R5 — Select · order · de-conflict *(Action: Transform; deterministic)*

Choose the final set, order it, and resolve contradictions before placement.
Distinct from R3: rerank scores *relevance*; this step enforces *budget,
diversity, recency, and consistency*. Folds into `harness_recipe`'s "Token
reduction — format · prioritize · compress" step.

| Option | Pro | Con |
|---|---|---|
| **Top-k by score** | Simple | Redundant near-duplicates; no recency/diversity logic |
| **MMR (diversity-aware)** | Cuts redundancy; broader coverage | λ tuning; can drop a relevant duplicate |
| **De-duplicate (SimHash/LSH + exact hash)** | Removes near-copies that waste budget | Threshold tuning |
| **Recency / authority weighting** | Surfaces fresh, signed, primary sources | Needs metadata + a policy |
| **Conflict resolution / source precedence** | One coherent context; flags contradictions | Needs a precedence policy |

**DEFAULT: top-k after rerank, then de-duplicate, then apply
source-precedence/recency weighting when the corpus has authority or freshness
metadata.** Rationale: this is where governance shows up at read time — primary,
signed, valid-through sources should win ties, and contradictions should be
flagged rather than silently averaged. Deterministic and freezable.

Citations: SimHash/LSH dedupe —
<https://sumonbis.github.io/academic-project/simhash/>,
<https://cse.msu.edu/~torng/Research/Pubs/ICDE2011.pdf>; placement/dilution
motivation (see R6).

### R6 — Place in prompt *(Action: Transform; deterministic)*

Where the selected context, the instructions, and the query sit in the final
prompt. Ordering matters because models attend unevenly across a long context
("lost in the middle"). Part of `harness_recipe`'s pre-call assembly feeding "Call
the right-sized model".

| Option | Pro | Con |
|---|---|---|
| **Naive concat (context → query)** | Simple | Mid-context evidence under-attended |
| **Edge placement** (most-relevant first AND last) | Counters lost-in-the-middle | Needs relevance ordering from R3/R5 |
| **Structured/delimited blocks** (XML/markdown sections, per-chunk source tags) | Clear boundaries; enables per-claim citation; aids injection defense | Slight token overhead |
| **Instructions-last** (context, then task + schema) | Recency bias favors the instruction | Long context can still bury it |

**DEFAULT: structured/delimited context blocks with explicit per-chunk source
tags, most-relevant evidence at the edges, task instructions + output schema
last.** Rationale: delimited source-tagged blocks are what make per-claim
citation and provenance possible (value-prop 2), and edge placement +
instructions-last directly mitigate the well-documented mid-context attention
drop.

Citations: assembly/placement is treated across the hybrid + baltor
sources — <https://app.ailog.fr/en/blog/guides/hybrid-retrieval-fusion>,
<https://pixion.co/blog/rag-strategies-baltor>.

---

### Prompt-engineering steps (P1–P5)

These are the prompt-construction Actions that wrap the model call. They map
1:1 onto `harness_recipe`'s "Add persona", "Build the system prompt", and
"Prompt-injection check" steps (few-shot and the output schema are part of the
system-prompt build).

#### P1 — Persona *(Action: Add Persona; role only, no facts)*

| Option | Pro | Con |
|---|---|---|
| **No persona** | Neutral; fewest tokens | No stance/expertise framing |
| **Role/expertise persona** ("cite-first counsel", "ESG auditor") | Sets stance & voice; improves task fit | Over-strong persona can bias against the rubric |

**DEFAULT: a minimal role persona matched to the task; hold *no* volatile facts
in it.** Rationale: persona sets stance only — facts belong in the Knowledge
Corpus where they carry provenance. (This is the canonical `persona` Action.)

Citation: persona/role framing is a standard prompt-engineering lever in the
prompt-engineering domain of the findings.

#### P2 — System prompt *(Action: Transform; the instruction contract)*

Task instructions, constraints, refusal/abstention policy, and the
citation/grounding requirement — **separate from the persona**. Options range
from terse instruction → structured instruction with explicit constraints and a
"cite every claim or abstain" clause.

**DEFAULT: a structured system prompt that states the task, the hard
constraints, the grounding/citation requirement, and an explicit abstention
policy ("if the corpus does not support it, say so").** Rationale: the abstention
+ cite-or-refuse contract is what converts retrieval into *governed* output and
is load-bearing for the negative-space domains the product targets.

#### P3 — Few-shot exemplars *(Action: Transform; part of the prompt build)*

| Option | Pro | Con |
|---|---|---|
| **Zero-shot** | Cheapest; no exemplar curation | Weaker format adherence on hard tasks |
| **Static few-shot** (k curated examples) | Reliable format/behavior; auditable | Token cost; manual curation; can over-fit |
| **Dynamic/retrieved few-shot** (kNN exemplars) | Examples matched to the input | Needs an exemplar store; retrieval cost |
| **Chain-of-Thought exemplars** | Lifts multi-step reasoning | Verbose; not needed for lookups |

**DEFAULT: zero-shot for simple extract/detect/classify; add 2–4 static
exemplars (or CoT exemplars for multi-step reasoning) only when format adherence
or reasoning quality measurably needs it.** Rationale: few-shot is a token cost
that should be paid only where it earns pipeline-level lift.

Citation: few-shot / CoT prompting are core prompt-engineering-domain techniques;
CoT-for-expansion evidence — <https://arxiv.org/pdf/2305.03653>.

#### P4 — Output schema *(Action: Transform; the typed envelope)*

| Option | Pro | Con |
|---|---|---|
| **Free text** | Flexible | Not machine-parseable; no contract |
| **JSON schema in prompt** | Parseable; pairs with post-verify | Models still emit malformed JSON |
| **Constrained/grammar decoding** | Guaranteed-valid structure | Needs white-box model support |

**DEFAULT: an explicit JSON output schema in the prompt, paired with the
post-call "Verify JSON (recover if malformed)" step.** Rationale: the typed
envelope is what the post-process and evaluate stages contract against; recovery
is handled deterministically downstream (§3).

#### P5 — Injection defense *(Conditional / Stop-End; a guard before the call)*

| Option | Pro | Con |
|---|---|---|
| **None** | No overhead | Untrusted input can override the system prompt / exfiltrate it |
| **Delimiting + role separation** | Cheap; reduces instruction confusion | Not sufficient alone against strong attacks |
| **Heuristic/classifier injection screen** (Conditional) | Blocks "ignore previous instructions" / prompt-extraction patterns | False positives; pattern upkeep |
| **Sanitize/strip retrieved content** | Neutralizes injection riding in corpus chunks | Can remove legitimate content |

**DEFAULT: delimit + role-separate (from R6) AND run a heuristic/classifier
injection screen that short-circuits the call if the input tries to extract or
override the system prompt.** Rationale: this is the canonical "Prompt-injection
check" Stop-End guard in `harness_recipe`; for governed pipelines the safe action
on detection is to halt and route to review, not to proceed.

Citation: injection defense is a core technique in the prompt-engineering domain
of the findings (defense-in-depth: delimiting + screening + sanitizing retrieved
context).

---

## 2. Recommended templated bundles (off-the-shelf compositions)

Each bundle is a pre-filled chain of the atomic components above. Pick a bundle,
then swap individual slots only where your domain demands. Lift is measured at
the **pipeline level** once assembled (value-prop 1); the freezable share is
noted because it's the cost story (value-prop 3).

### Bundle A — **Standard hybrid RAG** *(the default for most tasks)*
- **R0** none (or conversational decontextualization if multi-turn) · **R1** BM25
  + dense bi-encoder (HNSW, int8) · **R2** recursive-character chunks · **R3** RRF
  fuse → cross-encoder rerank (top-5) · **R4** none · **R5** top-k + dedupe ·
  **R6** delimited, source-tagged, edge-placed · **P1** minimal persona · **P2**
  structured + cite-or-abstain · **P3** zero-shot · **P4** JSON schema · **P5**
  delimit + injection screen.
- **When:** general semantic QA / detection / extraction over a mixed corpus where
  both paraphrase and exact terms matter. The safe starting point.
- **Freezable:** everything except the one reranker call (if hosted) and the one
  model Action — and the reranker can be the open-weight self-hosted option.

### Bundle B — **High-precision legal / regulated RAG**
- **R0** query decomposition (multi-issue questions) · **R1** BM25F (field-weighted:
  citation/heading boosted) + dense + **exact-id** leg for statute/section numbers
  · **R2** page/structure-aware (preserve citable anchors) · **R3** RRF →
  cross-encoder rerank · **R4** extractive span selection · **R5** top-k + dedupe +
  **source-precedence** (controlling authority wins, contradictions flagged) ·
  **R6** delimited, per-claim source tags, instructions-last · **P1** "cite-first
  counsel" persona · **P2** strict cite-every-claim-or-abstain · **P3** static
  exemplars · **P4** JSON with per-claim citations · **P5** injection screen +
  sanitize retrieved content.
- **When:** legal, compliance, clinical, or any domain where a wrong-but-fluent
  answer is unacceptable and every claim must trace to a primary source.
- **Why these locks:** exact-id + BM25F guarantee citation/section matching that
  embeddings blur; source-precedence + cite-or-abstain make the output governed.

### Bundle C — **Cheap keyword-first** *(cost floor)*
- **R0** none · **R1** BM25 only (optionally trigram/`pg_trgm` fuzzy fallback when
  hits < threshold) · **R2** recursive-character · **R3** no rerank (or BM25F
  field boosts) · **R4** none · **R5** top-k + dedupe · **R6** simple delimited
  concat · **P1** none/minimal · **P2** terse + abstain · **P3** zero-shot · **P4**
  JSON schema · **P5** delimit (+ light screen).
- **When:** exact-match-dominant lookups (technical reference, code/SKU/identifier
  search), tight latency/cost budgets, or no GPU/embedding infra. Also the
  Postgres-native stack (BM25/tsvector + `pg_trgm`).
- **Freezable:** ~everything except the single model Action — near-zero recurring
  cost.

### Bundle D — **Agentic / CRAG (corrective, self-correcting)**
- **R0** Self-RAG / Rewrite-Retrieve-Read or FLARE-style on-demand retrieval ·
  **R1** hybrid BM25 + dense · **R2** recursive/parent-child · **R3** RRF →
  rerank · **R4** contextual compression · **R5** select + dedupe + **a
  Conditional that grades retrieval quality** (corrective gate: if retrieved
  evidence is weak → re-query / decompose / web-search; if good → proceed) · **R6**
  delimited, edge-placed · **P1** persona · **P2** structured + abstain · **P3**
  zero-shot/CoT · **P4** JSON · **P5** injection screen · plus **iterate** (the
  `harness_recipe` retry loop) until the rubric passes.
- **When:** multi-hop / open-ended / long-form questions where a single retrieval
  pass is unreliable and you can afford extra LLM rounds for higher faithfulness.
- **Why these locks:** the corrective Conditional + iterate loop are what make it
  "agentic" — retrieval quality is *checked* and *repaired*, not assumed. Costs
  more model rounds; reserve for the questions that need it.

### Bundle E — **Multilingual / out-of-domain unified**
- **R1** BGE-M3 single model emitting dense + sparse + ColBERT heads (or
  ColBERT + BM25) · **R3** RRF or DBSF across the heads → optional rerank · all
  other slots as Bundle A.
- **When:** corpora spanning many languages or strong domain shift, where one
  unified model beats maintaining separate embedding/sparse models.

### Bundle F — **Cost-optimized large-scale (100M–1B vectors)**
- **R1** dense bi-encoder with MRL-truncated dims + binary quantization on
  ScaNN/DiskANN (or IVF-PQ), with BM25 as the exact-match safety net · **R3**
  binary ANN candidate set → **float32 rescore** → RRF → rerank · other slots as
  Bundle A.
- **When:** the corpus exceeds RAM budget and cost-per-query dominates; always
  pair binary candidates with a float32 rescore.

> Bundles are starting points, not cages. The product's job is to let an engineer
> begin from one of these and swap a single component (e.g. drop in `exact-id`,
> upgrade BM25→SPLADE, add a corrective Conditional) without rewiring the flow —
> because every slot is an independently swappable component.

---

## 3. Mapping: atomic step → primitive → slot in `harness_recipe`

How each atomic step maps to one of the **seven primitives** and where it slots
into the canonical governed-model-call recipe
(`scripts/showcase/builder.py::harness_recipe`). Most steps are **Action** (the
THEN) or **Knowledge Corpus** (the fact store) or **Conditional** (the IF / gate).
This is the contract that keeps the retrieval/prompt menu inside the
seven-primitive model — there is no new primitive here.

| Atomic step | Primitive | Schema `type`(s) | `harness_recipe` slot (phase) |
|---|---|---|---|
| **R0** Query transform | **Action** (Transform / Model-Call) — or **Conditional** for self-query filter extraction | `processor`, `harness`; `rule-pack`/`logic-pack` for self-query | pre — companion to *Build the system prompt* (query-side); decomposition/Self-RAG also drive the *retry loop* |
| **R1** Retrieve (method) | **Knowledge Corpus** (typed by `retrieval`) | `knowledge-pack`, `dataset` | pre — *Knowledge retrieval — keyword match* (`keyword`/`exact_id`), *— regex* (`regex`/fuzzy), *— RAG (vector)* (`rag_vector`/sparse/late-interaction) |
| **R2** Chunk | **Action: Transform** (index-time) | `processor` | (index build); read-time parent/window expansion rides inside *Knowledge retrieval* |
| **R3** Rerank | **Action: Transform** (rerank) | `processor` (cross-encoder/ColBERT/Gemma reranker) | pre — *Knowledge ranking* |
| **R3** Fuse | **Conditional** (retrieval/fusion policy) | `rule-pack` (e.g. `hybrid-retrieval-policy`) | pre — governs how the *Knowledge retrieval* legs merge (RRF/CC/DBSF) before *Knowledge ranking* |
| **R4** Summarize / Compress | **Action: Transform** | `processor` (extractive); `harness` (abstractive small-model) | pre — *Knowledge summarizing* |
| **R5** Select · order · de-conflict | **Action: Transform** (+ a **Conditional** for source-precedence/recency policy) | `processor`; `rule-pack` for the precedence policy | pre — *Token reduction — format · prioritize · compress* |
| **R6** Place in prompt | **Action: Transform** | `processor` (`envelope.*`/`format.*`) | pre — assembly feeding *Call the right-sized model* |
| **P1** Persona | **Action: Add Persona** | `persona` | pre — *Add persona* |
| **P2** System prompt | **Action: Transform** | `processor`/`logic-pack` (conditional prompt policy) | pre — *Build the system prompt* |
| **P3** Few-shot | **Action: Transform** | `processor` (part of prompt build) | pre — within *Build the system prompt* |
| **P4** Output schema | **Action: Transform** | `processor`/`logic-pack` | pre — within *Build the system prompt*; verified post-call (below) |
| **P5** Injection defense | **Stop / End** guard (+ **Conditional** screen) | `rule-pack`/`logic-pack`; `processor` to sanitize | pre — *Prompt-injection check* (short-circuits the call) |
| — the model call — | **Action: Model Call** (behind a trust boundary; adapter swaps transport) | `harness`, `adapter` | call — *Call the right-sized model* |
| Output verify/recover | **Conditional** | (deterministic built-in) | post — *Check output*, *Verify JSON (recover if malformed)* |
| Re-verify / score | **Action: Evaluate** | `rubric`, `benchmark` | post — *Re-verify* |
| Iterate / corrective loop | **Loop** | `pattern`, `pipeline` | post — *If not OK → retry with changes (≤3)* (the agentic/CRAG corrective loop) |
| Trigger gate (admit input) | **Conditional** (qualify) + **Stop / End** (disqualify) | `rule-pack`/`logic-pack` | gate — *Trigger gate*, *Pattern packs — qualify*, *Anti-pattern packs — disqualify* |

**Reading the table for assembly:** the retrieval sub-pipeline (R0–R6) populates
the **pre** phase of one governed model call; the prompt-engineering steps (P1–P5)
also live in **pre**; the model call is the single **call**; and verification +
the corrective loop live in **post**. A bundle from §2 is just a specific choice
of components for these slots — and because R1–R6 + P5 + the verify steps are
deterministic and freezable, the bundle adds pipeline-level lift while the only
recurring model cost is the one **Action: Model Call** (value-prop 3).

---

## See also
- [`component-taxonomy-and-stages.md`](component-taxonomy-and-stages.md) — the
  seven primitives, the stages, and the Knowledge Corpus `retrieval` triggers.
- [`../design/value-propositions.md`](../design/value-propositions.md) — the
  words and the four load-bearing claims (lift is pipeline-level; freezable;
  governed; open-core).
- `scripts/showcase/builder.py::harness_recipe` — the canonical ordered THEN
  steps these atomic steps map onto.
- Catalog components that already implement steps here:
  `processor/hybrid-bm25-vector-retrieve` (R1+R3 fuse),
  `processor/cross-encoder-reranker` & `processor/gemma-reranker` (R3 rerank),
  `rule-pack/hybrid-retrieval-policy` (R3 fusion policy),
  `processor/recursive-character-chunker` & `processor/page-aware-chunker` (R2),
  `processor/hyde-query-expander` & `pattern/hyde` (R0 HyDE),
  `pattern/rag-fusion` (R0 multi-query + RRF),
  `pattern/step-back-prompting` (R0 step-back),
  `pattern/two-stage-retrieve-rerank` (Bundle A skeleton),
  `processor/wikidata-query-walker` (R1 `graph`).
