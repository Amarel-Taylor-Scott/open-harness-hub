# Storage & hosting cost analysis (measured 2026-07-10)

> Answers: are we running out of disk? and how does the maximal multi-model/multi-representation design scale in
> hosting cost across object storage, Postgres, vector DBs, and git? Numbers are MEASURED locally + projected with
> stated assumptions. The reconciliation with "build out everything, don't prune": **never delete a representation —
> TIER it (hot RAM / cold quantized disk / on-demand). Build all; keep all; only the usage-hot subset lives in
> expensive hot storage.** That is what makes 100M+ affordable.

## 1. Local disk — YES, we are tight

`/` = **1.9 TB, 96% used, ~85 GB free.** The consumers (all **gitignored + regenerable from committed generators**):

| Path | Size | What |
|---|---|---|
| `dist/` (all) | **223 GB** | build artifacts (embedding stores, indexes) |
| ↳ `dist/primitive-facet-embeddings` | 44 GB | the 40M-vector facet store (model2vec 256d) |
| ↳ `dist/primitive-semantic-index` | 31 GB | lexical/semantic index |
| ↳ `dist/primitive-description-embedding-shards` | 16 GB | description embedding shards |
| ↳ `dist/primitive-model-stores` | 0.2 GB→ | the new per-model lanes (card-level, small) |
| `data/dev-intel/` (all) | **83 GB** | generated data (packs, receipts, factory) |
| ↳ `data/dev-intel/primitive_factory` | 54 GB | factory outputs |
| `.git` | 2.6 GB | code history (+ historically-committed data = CLEANUP-BACKLOG P0) |
| `~/.ollama` | 9.9 GB | downloaded LLM/embedding models |

**~306 GB is generated + gitignored + regenerable.** Implications:
- Do **NOT** materialize full multi-model FACET stores locally: each ≈ 44 GB (one model × 90 facets × 540K), so 5
  models = ~220 GB → fills the disk. The new per-model store is **card-level (1 vector/card)** = ~0.1–0.2 GB/model —
  safe. Keep bulk-facet builds to ONE cheap model (model2vec); strong models = card-level + rerank/on-demand.
- We can reclaim ~100–300 GB anytime by pruning superseded `dist/`/`data` artifacts (they rebuild from committed
  generators) — a local-hygiene action, not a data loss. (Ask before deleting; some are in-use.)

## 2. What the maximal design costs at scale (per-system)

Assumptions: ~74 embedded vectors/primitive today (90 facets, some empty) at 256d f32 ≈ 76 KB/primitive of vectors
(measured: 540K → 44 GB). Structured metadata (the 500+ columns, mostly scalars/hashes/tags) ≈ 5 KB/primitive.
Bodies ≈ 2 KB/primitive. Descriptions (300+ × 25 tok) ≈ 30 KB/primitive of text.

### 2A. Vector DB — the DOMINANT cost (Qdrant / pgvector / Milvus)
Raw vector bytes, ONE model's facet set:

| primitives | vectors (×74) | f32 | int8 (÷4) | binary (÷32) | PQ64 (÷~64) |
|---|---|---|---|---|---|
| 540K (now) | 40M | 44 GB | 11 GB | 1.4 GB | 0.7 GB |
| 5M | 370M | 380 GB | 95 GB | 12 GB | 6 GB |
| 40M | 3B | 3 TB | 760 GB | 95 GB | 48 GB |
| 100M | 7.4B | 7.6 TB | 1.9 TB | 240 GB | 120 GB |

× multiple models multiplies this (5 models × 100M f32 = **38 TB**; the 360-channel maximal = **55 TB** — the
research bundle's number). **This is why tiering + quantization is mandatory, not optional.** Levers (all KEEP the
representation): int8 (4×) · binary (32×) · PQ (~64×) · hot HNSW for the queried 5–10M only · cold DiskANN/on-disk
for the rest · **card-level (1 vector/primitive) for strong-model lanes** (74× smaller than facet-level) · compute
rare descriptions/models ON DEMAND.

**Monthly cost @ 100M, optimized (int8 + DiskANN cold + hot subset + card-level strong models):**
- **Managed (Qdrant Cloud / Pinecone / pgvector on RDS):** ~**$1,000–4,000/mo** (hot ~30–60 GB RAM + cold 1–3 TB SSD + replicas).
- **Self-hosted (one 128–256 GB-RAM box + 2–4 TB NVMe):** ~**$300–800/mo** (hardware amortized / cloud VM).
- **Naive all-hot f32 (55 TB in RAM): effectively impossible (~$100k+/mo)** — never do this.

### 2B. Postgres — registry / contracts / edges / receipts (MODERATE)
100M × 5 KB structured = **~500 GB** + edges (100M × ~10 × small ≈ 100–300 GB) + receipts (grow with usage).
- **DESCRIPTIONS and BODIES do NOT go in PG rows** — store handles/digests in PG, the 30 KB/primitive of text +
  2 KB bodies in object storage. Keeping descriptions in PG would add ~3 TB and wreck it.
- Managed (RDS/Cloud SQL, ~$0.10–0.15/GB/mo storage + instance): **~$300–1,000/mo** at 100M.

### 2C. Object storage (S3-compatible) — bodies / descriptions / raw (CHEAP)
- Bodies: 100M × 2 KB = 200 GB → ~$5/mo (S3 standard $0.023/GB).
- Descriptions (compressed): ~1–3 TB → ~$25–70/mo standard, less on infrequent-access.
- Raw mined source / snapshots (can be TBs): tier to cold (Glacier $0.004/GB) → cheap.
- **Total ~$50–200/mo.** This is the cheapest tier — push everything bulky here.

### 2D. Git — code, NOT data (NEGLIGIBLE if disciplined)
- Git holds only code + configs + the committed GENERATORS (minters/builders). **All generated data is gitignored +
  regenerable** — the pattern already followed (packs gitignored, minters committed). So git stays ~hundreds of MB.
- Cost: **~$0–50/mo** (GitHub / self-hosted Gitea). The only risk is BLOAT if generated data leaks into history —
  which is the CLEANUP-BACKLOG **P0** (`.git`=2.6 GB from ~55,606 historically-tracked files; untrack + optionally
  `git filter-repo` to shrink). Do this before it grows.

## 3. Headline

| System | @100M optimized (monthly) | Cost driver | Lever |
|---|---|---|---|
| **Vector DB** | **$1k–4k managed / $300–800 self-host** | embeddings (55 TB naive) | quantize (4–64×) + tier + card-level strong models |
| Postgres | $300–1,000 | structured metadata + edges | descriptions/bodies → S3, not PG |
| Object storage | $50–200 | bodies + descriptions + raw | cold tiers (Glacier) |
| Git | $0–50 | code only | keep generated data gitignored (P0 cleanup) |
| **Total serving** | **~$1.5k–5k managed / ~$0.5k–1.5k self-hosted** | | |

**Not** the $10k–100k of naive full materialization. The maximal "build out everything" design is affordable **only
via tiering by real-world usage** — build + keep every representation, but let the [usage ledger] decide which live in
hot RAM vs quantized-cold vs computed-on-demand. Locally we are near the wall (85 GB free): build strong-model lanes
**card-level**, keep bulk-facets to one cheap model, and reclaim regenerable artifacts as needed.
