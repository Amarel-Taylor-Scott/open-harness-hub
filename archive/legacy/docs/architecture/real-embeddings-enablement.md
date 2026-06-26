# Real Embeddings Enablement

This document covers how to move the Open Harness Hub vector store from the
offline placeholder (hash-bow-v1) to a real, promotable semantic embedding.
It is the companion to [vector-readiness-audit.md](vector-readiness-audit.md)
and [local-embedding-worker-contract.md](local-embedding-worker-contract.md).

---

## 1  Why Placeholder Vectors Block Promotion

`scripts/db/build_vector_store.py` maintains a strict boundary between
placeholder and real embeddings via `is_placeholder`:

```python
HASH_MODEL = "hash-bow-v1"   # deterministic feature-hash, dim=256 — placeholder
REAL_MODEL  = "all-MiniLM-L6-v2"   # sentence-transformers, dim=384 — promotable
```

The function `is_placeholder(model)` returns `True` for `HASH_MODEL` and
`False` for everything else. Every row in `object_embedding` stores the flag
as an integer column. The promotion pipeline reads it:

- `is_placeholder = 1` → the object **cannot** become tenant-visible via
  semantic search and will fail any promotion-readiness check.
- `is_placeholder = 0` → the embedding was produced by a real model and may
  proceed through the standard promotion gates (review tickets, CDC, index
  records, etc.).

The hash embedder is intentionally kept as the offline default so the build
succeeds with zero external dependencies, but its vectors must never be
surfaced as real search results.

---

## 2  Local Enablement — sentence-transformers + all-MiniLM-L6-v2 (384 dim)

### 2a  Prerequisites

```bash
pip install sentence-transformers      # pulls torch, transformers, huggingface_hub
```

Python 3.9 / 3.10 / 3.11 are all supported. NumPy must be `<2` when using
torch wheels compiled against NumPy 1.x (which is most PyPI wheels as of
mid-2026). If `import sentence_transformers` raises a NumPy ABI error, pin:

```bash
pip install "numpy<2"
pip install sentence-transformers
```

The model weights (~90 MB) are downloaded from Hugging Face on first use and
cached in `~/.cache/huggingface/hub`. An internet connection is required once;
subsequent runs are fully offline.

### 2b  Building a real-vector store

```bash
python3 -m scripts.db.build_vector_store build \
  --model all-MiniLM-L6-v2 \
  --limit 200 \
  --store dist/vector-store/real-sample.sqlite
```

The embedder selection logic in `get_embedder()` detects the installed
`SentenceTransformer` and sets `dim=384`, `is_placeholder=0`:

```python
def get_embedder(model: str) -> tuple[Callable[[str], list[float]], int]:
    if model == REAL_MODEL:
        try:
            from sentence_transformers import SentenceTransformer
            st = SentenceTransformer(model)
            dim = int(st.get_sentence_embedding_dimension())
            return (lambda t: [...st.encode(t, normalize_embeddings=True)...], dim)
        except Exception:
            return (hash_embed, HASH_DIM)   # graceful offline fallback
    return (hash_embed, HASH_DIM)
```

### 2c  Qualitative comparison with the hash embedder

The hash embedder (hash-bow-v1, 256 dim) has two known deficiencies observed
in live catalog searches:

1. **Score saturation / ties.** Multiple unrelated components receive identical
   cosine scores (e.g. five `adapter/scale-gemini-multimodal-arm-*` entries
   all score `0.2085` on the query "semantic similarity embedding retrieval").
   This happens because hash collisions blur token boundaries at small dim=256.
2. **Low raw scores.** Typical top-5 scores are 0.06–0.21. The hash vectors
   are signed ±1 unit-features; query–doc overlap is sparse, so cosine values
   are naturally low even for good matches.
3. **No synonymy.** "cost optimization" and "token budget" share no hash bins;
   conceptually synonymous documents score near zero.

A real sentence-transformer model (`all-MiniLM-L6-v2`, 384 dim) addresses all
three:

- Trained cosine similarity between semantically similar sentences is typically
  0.7–0.95 for close matches.
- Synonymy and paraphrase are captured; "cost reduction" matches "budget
  constraint" without keyword overlap.
- Tie rates drop sharply because 384-float dense vectors have far more
  distinguishing capacity than 256-bin hash bags.

The net effect is meaningful ranked retrieval: the right component appears in
position 1–3 for a natural-language query rather than being indistinguishable
from noise.

---

## 3  Hosted-Route Enablement (Provider-Neutral)

For production scale or when GPU/CPU resources are constrained, the store
supports any embedding provider that returns a normalized float vector. The
model registry in `scripts/_config.py` is the canonical single source of truth
for model IDs and their output dimensions:

```python
EMBEDDING_MODELS: dict[str, int] = {
    "all-MiniLM-L6-v2":     384,   # sentence-transformers, local default
    "bge-small-en-v1.5":    384,   # local alternative, same dim
    "text-embedding-3-small": 1536, # OpenAI-compatible hosted route
    "text-embedding-ada-002": 1536, # legacy OpenAI-compatible route
}
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSIONS: int = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]
```

Adding a new model requires only:

1. Add a row to `EMBEDDING_MODELS` in `scripts/_config.py`.
2. Wire a provider-neutral embedding function in `get_embedder()` (or a thin
   worker that POSTs text to a REST endpoint and returns `list[float]`).
3. The store schema is multi-dim by design — `dim` is stored per row, so a
   384-dim and a 1536-dim model can coexist for the same objects.

### 3a  text-embedding-3-small (1536 dim)

Typical hosted-route wiring (provider-neutral, no SDK hard-dependency):

```python
import os, httpx

def openai_compat_embed(text: str, model: str = "text-embedding-3-small") -> list[float]:
    resp = httpx.post(
        os.environ["EMBEDDING_API_BASE"] + "/embeddings",
        headers={"Authorization": f"Bearer {os.environ['EMBEDDING_API_KEY']}",
                 "Content-Type": "application/json"},
        json={"model": model, "input": text, "encoding_format": "float"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]   # already normalized by this API
```

Set `EMBEDDING_API_BASE` and `EMBEDDING_API_KEY` in the worker environment.
The base URL can point at OpenAI, Azure OpenAI, or any compatible local server
(e.g. Ollama with nomic-embed-text serving the same REST shape). The store is
unaware of which backend is used; it only sees the returned float list and the
model string.

### 3b  pgvector column sizing

Always derive the column type from `scripts/_config.pgvector_type()` — do not
hard-code `vector(384)` or `vector(1536)` in SQL files:

```python
from scripts._config import pgvector_type, EMBEDDING_MODELS
col = pgvector_type(EMBEDDING_MODELS["text-embedding-3-small"])  # → "vector(1536)"
```

---

## 4  Promotion Rule

**Only non-placeholder vectors may be promoted to tenant-visible search.**

The rule applies at two levels:

### 4a  Build-level flag

Every `object_embedding` row stores `is_placeholder INTEGER`. A promotion
check must verify `is_placeholder = 0` before the object can transition from
staged to active.

### 4b  Re-embed on model change

When the default model changes (e.g. from `all-MiniLM-L6-v2` to a fine-tuned
variant), existing stored vectors become stale:

1. A migration creates new `object_embedding` rows keyed by the new
   `embedding_model` string. Old rows remain; the store is multi-model by
   design.
2. New `index_record` rows are emitted for the new model's vectors.
3. The old model's vectors may be soft-deleted or left in place for A/B
   comparison; they do not block promotion of the new vectors.
4. `scripts.db.daily_promotion_readiness_plan` should be rerun after any
   model-change migration to confirm that all active objects have a
   non-placeholder vector under the current model.

**Model-version drift check:** the `text_hash` column ensures that if the
source text of a component changes, the embedding is invalidated and must be
recomputed even if the model did not change. Hash mismatches surface in the
vector readiness audit as `text_hash_mismatch_rows`.

---

## 5  Cost and Throughput Notes

| Model | Dim | Infra | Throughput | Cost |
|---|---|---|---|---|
| hash-bow-v1 (placeholder) | 256 | pure-stdlib, zero deps | >500k/s | $0 — but not promotable |
| all-MiniLM-L6-v2 | 384 | CPU (sentence-transformers) | ~1k–5k docs/min on M-series | $0 compute, model weights ~90 MB |
| all-MiniLM-L6-v2 | 384 | GPU (CUDA/MPS) | ~10k–50k docs/min | $0 compute beyond hardware |
| text-embedding-3-small | 1536 | OpenAI-compatible API | rate-limited, ~1M tokens/min tier-2 | ~$0.02 / 1M tokens (2026 list) |
| text-embedding-ada-002 | 1536 | OpenAI-compatible API | same | ~$0.10 / 1M tokens (legacy list) |

For a 5,000-component daily batch (typical factory run):

- Local CPU: ~2–5 minutes, $0.
- Hosted API at $0.02/1M tokens: estimated ~$0.01–$0.02 total (short texts).

At 1M+ components (billion-scale goal), budget for ~$20–$50/run for hosted
embedding if you want 1536-dim vectors. Local models at 384-dim are the
cost-dominant choice for that scale. Use the `embedding-model-profiles.json`
emitted by the daily embedding execution planner for per-model cost snapshots.

---

## 6  Quick-Start Checklist

```
[ ] pip install sentence-transformers  (or pin numpy<2 if ABI error)
[ ] python3 -c "import sentence_transformers; print('ok')"
[ ] python3 -m scripts.db.build_vector_store build \
      --model all-MiniLM-L6-v2 \
      --store dist/vector-store/real-sample.sqlite \
      --limit 500
[ ] python3 -m scripts.db.build_vector_store search \
      "semantic similarity retrieval" \
      --store dist/vector-store/real-sample.sqlite \
      --model all-MiniLM-L6-v2
[ ] Confirm is_placeholder=false in build output JSON
[ ] Rerun scripts.db.daily_promotion_readiness_plan after full build
```
