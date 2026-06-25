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

## Refinement (owner 2026-06-25): BOTH authoritative; git holds EVERYTHING; branches model promotion
Store every record/codeblock/component in **both** — they play different roles, and git is no longer gated on the
promotion boundary:
- **git = the durable, versioned source of truth for EVERYTHING** (candidate AND promoted). Promotion state is a
  **branch**, not an entry gate: candidates land on `candidates/*` (or a `staged` branch), variations on **feature
  branches**, and promotion = a reviewed **merge to `main`** (PRs · diff · blame · rollback for free). git already
  holds our ledgers (`data/dev-intel/*.jsonl` are tracked + auto-committed) — make it deliberate + structured
  (`records/<registry>/<id>.json`, `codeblocks/<id>.py`).
- **DB (pgvector) = the FAST, searchable MIRROR** of the same records — rebuildable from git, indexed for semantic +
  multi-attribute search. The DB is a **derived index**, not the source of truth (so it can be dropped + rebuilt).
- **Promotion boundary now governs TENANT-VISIBILITY** (what's *served*), **not git ENTRY** — everything is in git
  from the moment it's created; what's promoted is what's been merged to `main` + flagged servable in the DB.

Two honest caveats: (1) **third-party code is still a POINTER** — git holds OUR record + a handle to their repo,
never a copy (license + bloat). (2) **git is not a database at billions-scale** — the curated/promoted layer +
codeblocks + structured ledgers live in git (branchable, sharded if needed); the extreme-volume raw-candidate
firehose is mirrored in DB/object-store, not one-file-per-row in a single giant repo. "git holds everything" =
everything that benefits from versioning/branches/review.

## Scale to billions: multiple locations, kept consistent by content-addressing + CDC (owner 2026-06-25)
Storing in several places is fine — make them **consistent by design**, not by hope. **git is the dev-friendly
authoritative copy** (easy to read, branch, review); every other location is a **derived, rebuildable mirror**.
- **One canonical `content_hash` per record** = dedup + **idempotent sync** across all locations (git · pgvector ·
  object-store · leaf shards). Same hash → same record everywhere; a changed hash → a real change to propagate
  (`record_store.append` already takes an `idem_key`).
- **CDC log is the sync spine**: each create/update emits a CDC event (the repo's CDC + index-delta discipline); a
  sync worker propagates git ↔ pgvector ↔ object-store idempotently. **Truth flows git/CDC → mirrors**; never let a
  mirror diverge silently — reconcile on `content_hash`.
- **Leaf / sharded scale**: partition by `registry × hash-prefix × time` into **leaf shards** — pgvector shards
  (HNSW per shard), git sub-trees/branches, object-store key-prefixes. Billions of rows = many small leaves, each
  independently indexed + synced; queries **scatter/gather** across leaves. No single giant repo or index.
- **Tiered by access pattern**: hot (pgvector, promoted/recent) · warm (sqlite/JSONL staging) · cold (object-store
  Parquet, sharded). Which tier + which git branch a record sits in is governed by the promotion boundary
  (tenant-visibility), not by whether it exists.


