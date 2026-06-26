# Leaf-convergence & content-addressed sync — systems-design research

**Date:** 2026-06-06. **Owner-supplied, verify-first** (GitHub repos cited below; none adopted as runtime —
all are *study references / candidates behind a port*). **Purpose:** map the design families behind a
**convergent, leaf/chunk/record comparison system** to concrete prior art, and to Baltor's **leaf-convergence
engine** — the scale unlock for comparing/converging billions–trillions of facts/leaves/fields without
all-pairs comparison (flagged in the YC/scale plan as a strategic subsystem).

> **The core pattern:** raw → canonicalize → split into **leaves** (records / fixed blocks / content-defined
> chunks) → `leaf_hash = H(canonical bytes)` → group into ranges → build a **Merkle/range tree** → **root
> hash = compact commitment** → compare roots between replicas → **descend only into mismatched ranges** →
> fetch differing leaves → **merge by conflict policy**. Three orthogonal jobs: **hash rings decide where
> data lives**, **Merkle/range trees decide whether two places match**, **content-defined chunking decides
> stable leaf boundaries**, and **CRDT/versioning decides how concurrent changes converge.**

## Design families → strongest prior art (study order)

| Design area | Strongest examples | Relevance to Baltor |
|---|---|---|
| **Direct leaf/range Merkle sync** | Scionic Merkle Tree (numbered leaves + LeafSync ranges) · transparency-dev/merkle (compact ranges) · Cassandra/Dynamo anti-entropy | The literal template: compare roots → descend to mismatched ranges → sync only the diff |
| **Merkle search tree (CRDT)** | domodwyer/merkle-search-tree · ipfs/go-ds-crdt · hoytech/quadrable (sparse Merkle DB + partial proofs) | Record-SET reconciliation that converges deterministically — closest to *fact* convergence |
| **Content-defined chunking** | google/cdc-file-transfer (FastCDC) · systemd/casync · folbricht/desync · rsync/librsync/Copia | Stable leaf boundaries so an insertion shifts only nearby chunks (not everything) |
| **Backup dedup CAS** | restic · BorgBackup · Kopia · bupstash · Bup | Mature chunk→hash→dedup→pack/index/snapshot engineering (compression, GC, cache) |
| **P2P content-addressed DAGs** | IPFS/UnixFS/IPLD · Hypercore · Iroh (blobs/docs/willow, BLAKE3) | Content-addressed chunks + verifiable sparse replication |
| **Record reconciliation / merge** | Dynamo · Cassandra · CR-SQLite (CRDT SQLite) · go-ds-crdt | How divergent records actually MERGE (not just where they differ) |
| **Routing / ownership** | Cassandra token ring (vnodes) · uhashring · rendezvous/HRW · jump hashing · memberlist/Serf | Assign leaves/ranges to owners with minimal remap on membership change |
| **Git-like object models** | Git (packfiles/deltas) · OSTree · Nix · OCI layout · Bazel CAS · lakeFS · Dolt | Content-addressed immutable object graphs + versioned snapshots/diff |

**Verdict (owner):** the architecture is real and well-supported, but **no single repo owns the whole design.**
Cleanest synthesis = **FastCDC-style leaves + Merkle/range commitments + hash-ring ownership + CRDT/versioned
merge + CAS chunk storage.** Closest single phrase-match to "convergent leaf comparison": **Scionic Merkle
Tree** (numbered leaves, LeafSync range requests, logarithmic branch size — a folder of 1M chunks needs ~21
leaves in a branch, not 1M sibling hashes).

## How it maps to Baltor (what we already have vs the gap)

| Layer of the pattern | Baltor today | Gap → leaf-convergence engine |
|---|---|---|
| Canonical record/leaf + content hash | content-hash discipline already in the repo (normalized-object/source/version hashes) | a **canonical leaf model** (record · field · chunk ordinal) with `leaf_hash` |
| Record ledger / ownership | **DurableFleetLedger** (atomic claim, leases) + supervisor **shard leases** (a coarse ownership ring already) | a **hash-ring / rendezvous** map of leaf-ranges → shards for range repair at scale |
| Range tree / commitment | — | a **Merkle search tree** (records) or **compact-range tree** (append-only) → `root_hash` per range |
| Compare & sync | conflict detection + reconciliation (CFPB invariant) operate on small sets | **root-compare → descend mismatched ranges** so we never do **all-pairs** comparison |
| Merge / conflict policy | **reconciliation authority** (authority-ranked, deterministic) + Lossless Distillation side-by-side | Merkle finds *where* differs; reconciliation already decides *who wins* — keep that split |
| Versioning / rollback | versioned derived layers + rehydration (Lossless law) | multi-version leaf store + **tombstones** for safe deletes across replicas |

**Why it's the scale unlock:** with leaves + range commitments, Baltor compares **pipeline v1 vs v2**, **source
update N vs N+1**, **fact convergence**, **context-pack diffs**, **runtime-config diffs**, and **side-by-side
provider output** (the Lossless Distillation pre-promotion compare) in `O(changed)` not `O(all)`. The same
primitive powers CDC freshness, dedupe, and the determinism-factory's before/after.

## Recommended architecture (copy this layering)

1. **Canonical leaf** — record/field/CDC-chunk; deterministic serialization; `leaf_hash = BLAKE3/SHA-256(bytes)`.
2. **Leaf index** — `{key, content_hash, byte_length, codec, schema_version, logical_path, chunk_index, tombstone, causal_version}`.
3. **Range tree** — Merkle search tree (mutable record sets) · compact-range Merkle (append-only logs) · Scionic numbered-leaf (file chunks). `root_hash` = state commitment.
4. **Ownership** — rendezvous/HRW for simple owner selection; Cassandra-style token ring + vnodes when **range repair** matters. (Reuse the supervisor's shard-lease model as the ring substrate.)
5. **Sync protocol** — exchange `root(range)`; equal → done; differ → exchange child summaries / compact ranges → descend to mismatched leaves → fetch by hash → verify → **merge by Baltor reconciliation policy** (NOT last-write-wins for truth-bearing facts).
6. **GC** — refs/snapshots, **tombstones** for deletes, compaction once safe.

## Three load-bearing caveats (govern them, don't ignore)

1. **Dedup/CDC can leak** — identical chunks → identical IDs; chunk-length patterns leak (2025 "Breaking & Fixing
   CDC" reports key-recovery on keyed CDC in backup systems). → tenant-scope leaf IDs; don't cross-tenant dedup
   truth-bearing content.
2. **Deletes are hard** — a removed leaf can be reintroduced by a replica without **tombstones / causal
   versions**. → keep tombstones + causal metadata long enough (matches the Lossless law: omitted ≠ deleted).
3. **Hash equality proves BYTES, not MEANING** — two equal-hash leaves are byte-identical; *semantic*
   convergence still needs canonical serialization + schema versions + **explicit conflict rules**. This is
   exactly why **Merkle finds differences but Baltor's reconciliation authority decides truth** — never let
   hash-convergence masquerade as verification.

## Baltor stance + next build (a focused increment, not a platform)

- **Adopt none as the runtime.** These are study references; if any code is adopted it sits behind a
  `LeafStoreProvider` / `RangeTreeProvider` port with a local stdlib equivalent first (cloud-defer discipline).
- **Build the local proof FIRST** (mirrors the strategy-paste acceptance): generate many leaves → change a tiny
  subset → **prove unchanged shards/ranges are skipped**, the changed leaf count is recovered, and **no
  all-pairs comparison occurs**. A deterministic, stdlib Merkle-search-tree + rendezvous-ownership prototype +
  `check_leaf_convergence_no_all_pairs` is the first slice — then range repair, then tombstones, then merge via
  the existing reconciliation authority.
- **Reuse, don't duplicate:** the DurableFleetLedger is the record/ownership substrate; the temporal fact graph
  + reconciliation are the merge authority; content hashes already exist. The leaf-convergence engine is the
  **range-commitment + descend-only-diff** layer on top — not a second store or a second truth authority.

## Repos to study first (verify-first; none installed)

Merkle range/chunk: **Scionic Merkle Tree**, transparency-dev/merkle, **domodwyer/merkle-search-tree**,
hoytech/quadrable. CDC: **google/cdc-file-transfer (FastCDC)**, casync/desync, buildbarn/go-cdc. Dedup CAS:
Borg/Kopia/restic/Bup. P2P: IPFS/UnixFS, Hypercore, Iroh, go-ds-crdt. Ownership: Cassandra token ring,
uhashring, rendezvous/jump hashing, memberlist/Serf. Versioned data: Git, lakeFS, Dolt, CR-SQLite.

*Warrant: owner-supplied systems-design research (verify-first; sources are the cited GitHub repos/papers). No
repo adopted or installed. Maps to the planned leaf-convergence engine; reuses the durable ledger +
reconciliation authority (Merkle finds diffs, Baltor decides truth); honors the Lossless Distillation law
(tombstones, multi-version, side-by-side compare).*
