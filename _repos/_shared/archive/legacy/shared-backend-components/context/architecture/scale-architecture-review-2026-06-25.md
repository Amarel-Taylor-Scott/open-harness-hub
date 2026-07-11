# Scale architecture review — is this the best for the planned scale?

> Critical review, 2026-06-25. Planned scale (per north-stars): **billions→trillions** of records, internet-scale
> registry, high write throughput (autonomous loops), semantic search at scale, multi-tenant. **Bias warning: most
> of the current implementation was built this session — this review is deliberately hard on it.** serves_truth=false.

## Verdict (one line)
**The principles are right; the current implementation is a single-node PROTOTYPE that will not pass ~low millions,
and one framing ("git = authoritative store of EVERYTHING") is wrong for the planned scale.** It proves the loop;
it is not the scale architecture. The gap between the two is large but the path is clear.

## What's RIGHT (keep — these are scale-correct)
- **Content-addressing (`content_hash`)** — the essential primitive for dedup + idempotent sync. ✓
- **Tiered storage** (hot/warm/cold) + **pointer-not-copy** for third-party code (license + bloat). ✓
- **CDC as the sync spine** + reconcile-on-hash; truth flows one direction. ✓ (right pattern, not yet built)
- **Deterministic-first descent** (LLM last) — the only way cost survives at scale. ✓ (thesis right; loops violate it — see #5)
- **Leaf sharding / scatter-gather** + **registry-as-pointer, records-from-population**. ✓
- **serves_truth=false + promotion boundary + proof gate + SEHA boundary** — governance is sound. ✓

## What WON'T scale (ranked by severity)
1. **The operational substrate is JSONL files appended by Python daemons, re-read whole each cycle.** `hybrid_search`
   rebuilds the index by reading ALL records; `populate`/`enrich` scan from a cursor but the files are single growing
   blobs. This is **O(n) per cycle → quadratic over a run**. Dead at low-millions, impossible at billions. **This is
   the #1 blocker.** Production needs a real DB + **incremental, CDC-driven indexing**, never whole-file rebuilds.
2. **"git = authoritative source of truth for EVERYTHING" does not hold at billions/trillions.** Git is not a
   database; multi-GB single JSONL files + auto-commits are pathological (Microsoft needed GVFS/Scalar at ~millions
   of files). **Fix the framing:** the data-plane source of truth is an **append-only event log + object-store
   (content-addressed)**; **git is a curated, human-facing PROJECTION of the promoted + code subset** — not the
   firehose store. (Dev-ergonomics is a real reason to keep git for code/curated artifacts; it is not a reason to
   put a trillion rows in it.)
3. **Search "vectors" are deterministic LEXICAL hashes + O(n) Python cosine.** They capture spelling, not meaning,
   and scanning every record per query is dead past ~100k. Production needs **learned embeddings** (nomic/e5/etc.)
   in an **ANN index** (pgvector HNSW sharded, or a dedicated vector DB — Qdrant/Milvus/Vespa/LanceDB). (Queued #16,
   but it's not a "later polish" — it's load-bearing.)
4. **Single-process daemons, no queue/backpressure/horizontal scaling.** Can't safely run N swarms (dup writes; I
   already hit a file-deletion race this session). Production = a **durable queue + stateless idempotent workers**
   (Temporal/Kafka+consumers/SQS), scaled horizontally, content-hash-idempotent. The current model is single-node.
5. **Eager LLM enrichment per record breaks cost at scale.** Billions × hundreds of tokens of GLM/Kimi = millions of
   dollars + years of wall-clock. Must be **lazy/triaged**: deterministic for the firehose; LLM only on the searched/
   high-value subset, on demand. (The repo's gap-screen/capability-valley thesis says exactly this — the loops as
   built enrich indiscriminately, violating it.)
6. **Consistency + schema evolution are under-specified.** Conflict resolution (two loops, different enrichment for
   one record), CDC ordering across shards, exactly-once vs at-least-once, and **schema migration** (the
   universal_object_schema grew mid-session) + backfill/reprocessing of billions are unaddressed.

## Target architecture for the planned scale
- **Source of truth = append-only event log (Kafka/Redpanda) + content-addressed object-store.** Everything is an
  immutable, hashed event; the log is replayable; mirrors are rebuildable from it.
- **Operational = sharded pgvector (or dedicated vector DB) with LEARNED embeddings + ANN**, indexed **incrementally
  from the CDC stream** — never whole-file rebuilds. Postgres for structured metadata + relationships.
- **Compute = durable queue + stateless horizontal workers** (the loops become consumers). Idempotent via
  content-hash. Backpressure + retries + DLQ.
- **git = curated projection** of the promoted + code + schema subset (dev-facing, versioned, branch=promotion).
- **Enrichment = deterministic-first + lazy LLM** (on-demand / high-value subset only).
- **Cold = object-store Parquet, sharded; leaf scatter-gather** for analytics + rebuild.
- **Schema = versioned + backfill via the queue.**

## Prototype → production path (what to swap, in order)
1. **Move the operational tier off whole-file JSONL** → Postgres (+ pgvector) via the existing `record_store` port
   (`PostgresRecordStore` is already stubbed); index incrementally. *(Biggest scale win; #16/#19.)*
2. **Real embeddings + ANN** (nomic via `embeddings.Embedder` → pgvector HNSW). *(#16.)*
3. **CDC sync engine** as the spine; git becomes a projection. *(#20 — reframe git's role.)*
4. **Loops → queue+workers** (durable, horizontal, idempotent). *(new — the autonomy model's scale form.)*
5. **Triage LLM enrichment** (lazy/high-value only). *(tune the enrich loop.)*

## Honest bottom line
What's running now is an excellent **proof of the flywheel** — it produces governed, hashed, enriched, searchable
records end-to-end. But it is **single-node prototype-grade**; the planned scale needs the substrate swap above. The
good news: the **principles, governance, and data model are scale-correct**, so this is a substrate migration
(JSONL→log+DB, daemons→workers, lexical→learned-ANN, git-everything→git-projection), **not a redesign**.
