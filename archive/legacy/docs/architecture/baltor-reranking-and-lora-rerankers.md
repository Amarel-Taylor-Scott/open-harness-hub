# Baltor Reranking And LoRA Rerankers

Baltor treats reranking as a separate control surface from model routing.

Model routing decides which worker or reviewer should handle a task. Reranking
decides which retrieved candidates should enter a context pack, in what order,
and with which source-handled evidence.

The durable rule:

```text
Do not rank by embedding similarity alone.
Rank by source-aware usefulness for the task.
```

## Reranking Ladder

```text
0 deterministic filters
  -> ACL, source policy, dedupe, exact handles, date gates

1 lexical rankers
  -> BM25, issue keys, source IDs, paths, symbols, headings

2 vector rankers
  -> dense, sparse, hybrid, multivector recall

3 cross-encoder rerankers
  -> query/candidate pair scoring for top-candidate precision

4 LoRA/domain rerankers
  -> eval-approved tenant/domain/task adapters over known corpora

5 LLM judge rerankers
  -> conflict-aware, source-precedence, high-risk evidence ordering

6 human review
  -> unresolved high-stakes or regulated ranking decisions
```

Cross-encoders are useful after a broad retriever has produced a candidate
pool. Sentence Transformers describes cross-encoders as pair scorers/rerankers:
the query and candidate are evaluated together, which is slower than embedding
similarity but usually better for top-candidate precision.

LoRA rerankers are not a new source of truth. They are adapter profiles:

```text
base reranker
  + tenant/domain/task LoRA adapter
  + eval gate
  + lineage
  + source handles
```

PEFT/LoRA is useful because the adapter can specialize a reranker or judge for a
domain without retraining the whole model. Baltor should only promote a LoRA
reranker when it beats the base reranker on the tenant's evaluation set and does
not regress source recall, citation coverage, or safety policy.

## Scoring Signals

The reranking score should combine:

```text
lexical_match
semantic_similarity
source_authority
freshness
verifiability
relationship_proximity
task_fit
low_prompt_injection_risk
human_verified
```

Example policy:

```text
0.12 * lexical_match
+ 0.16 * semantic_similarity
+ 0.16 * source_authority
+ 0.12 * freshness
+ 0.16 * verifiability
+ 0.10 * relationship_proximity
+ 0.10 * task_fit
+ 0.05 * low_prompt_injection_risk
+ 0.03 * human_verified
```

The exact weights can change per pack type. The contract should not.

## Product Contract

Baltor exposes:

```text
GET/POST /api/context-gateway/reranking
MCP tool: context_reranking
Schema kind: baltor.context-reranker-profile.v1
Schema kind: baltor.context-reranking-policy.v1
```

The endpoint returns:

```text
reranker_profiles
reranking_policy
sample_rerank_decision
```

Reranker profiles are provider-neutral. They may mention examples such as BGE,
SentenceTransformers CrossEncoder, ColBERT-style late interaction, PEFT LoRA,
QLoRA, or LLM judges, but ranking policy must remain task/risk/corpus driven.

## Acceptance Criteria

Every reranked context pack should preserve:

```text
source handles
ACL and policy filters
ranking signals
reranker profile ID
adapter ID when used
eval version for promoted LoRA adapters
lineage for reranking decisions
raw candidate count and final candidate count
```

LoRA/domain adapters must additionally preserve:

```text
base model or reranker ID
adapter ID
training data source handles
eval case set
promotion decision
rollback path
known failure modes
```

The practical order for Baltor is:

```text
lexical + source-handle filters first
hybrid vector recall second
cross-encoder rerank third
LoRA/domain rerank only after eval
LLM judge only when risk justifies latency
human review for unresolved high-stakes ordering
```
