# Where code + components actually live (storage routing)

> Decision note, 2026-06-25. Grounded in `architecture/storage_tier_policy.json` (which already defines the tiers)
> + `src/teleon/storage/record_store.py`. **Not either/or — both, by DATA TYPE.** The law: *a DB is never the code
> store; git is.* pgvector stores the **record** (metadata + vector + pointer); git stores the **code**.

## The routing
| Data | Lives in | Tier | Why |
|---|---|---|---|
| Registry pointers/shapes (`architecture/*.json`) | **git** (`json_file` — "git IS the store, never a DB") | config | small, reviewed, versioned, diffable |
| Record **metadata + embeddings + hybrid search + graph** | **Postgres + pgvector** (`PostgresRecordStore`) | operational | millions of indexed rows; semantic + multi-attribute search |
| **Raw code** — our generated/promoted components + codeblock templates | **git** (`code-templates/ · templates/ · pipelines/ · catalog/`) → **GitHub/GitLab** to publish | config/code | code wants diff · blame · branches · PRs · signing · install — git is built for this; a DB is not |
| **Ingested third-party code** | **pointer only** — the record carries `provenance.url` + `content_hash`; fetch by handle | operational (the *record*) | license + bloat + provenance; never copy upstream code into our DB |
| Cold / history / CDC / lineage | **object-store Parquet** | history | trillions; lineage |

## The principle (content-addressed pointer)
A record in pgvector = `{ metadata, embedding, searchability columns, content_hash, source_handle }`, where
`source_handle` points at where the raw code lives (a git remote + ref + path + commit-sha, or an object-store key).
**Never inline raw code blobs in the vector store** — you'd lose versioning/review and bloat the index. Our records
already do this: `provenance = { url, content_hash, source_seed }`.

## Our generated codeblocks (scripts/codeblock_enrich.py)
Tiny templates may sit **in the DB record** (they're small) AND be **promoted to git** (`code-templates/`) once stable
— the **promotion boundary** decides: a staged candidate lives in the operational DB; a promoted, reviewed component
is committed to git (versioned, signed, installable, indexed back into pgvector by handle).

## The one production gap (queued #16)
The operational tier is currently `LocalRecordStore` (sqlite/JSONL staging — the canonical first tier). Wiring
`PostgresRecordStore` + pgvector is the scale move for metadata+vectors. **Code stays in git regardless.**
