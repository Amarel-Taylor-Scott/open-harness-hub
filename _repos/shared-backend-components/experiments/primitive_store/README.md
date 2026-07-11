# primitive_store — git-like, content-addressed, scoped primitive storage + a generic executor

Reference implementation (CANDIDATE, `experiments/`) of how we store primitives — ours **and** external —
across a **database**, a **git-like environment** (forks / parallel versions / merges), and **buckets**, plus
the **one generic stateless executor** that runs any primitive by reference. Stdlib-only, offline,
`--self-test`-able (18 checks). Run: `python3 primitive_store.py --self-test`.

## Three planes, joined by the content hash

| Plane | Holds | Class |
|---|---|---|
| **Content** (`ContentBucket`) | the primitive's body/code, content-addressed (dedup + integrity) | long bodies never bloat git or the DB |
| **Lineage** (`LineageGraph`) | the git-like DAG: **fork** (new primitive), **branch** (parallel version), **merge** (remix, two parents), **supersede** (new version, prior KEPT) | the provenance/versioning plane |
| **Query** (`Index`) | a scope-tagged search projection | rebuildable — not the source of truth |

Source of truth = content + lineage; the index is a derived projection. The canonical hash is the join.

## The rules that matter

- **Scope — our code is a secret primitive.** Every primitive is `PUBLIC` (externally available: searchable +
  runnable) or `INTERNAL` (our own code: stored/versioned/forked *exactly* like a primitive, but **never
  returned by a public search and never run for a public caller**). Mirrors `LineageBundle.scope`'s
  "tenant_private never enters a global_public bundle" law. So **every one of our repos is a `system` of
  internal primitives** — same machinery as the public catalog, walled off from public search/use.
- **Candidate/truth.** Every write is born `candidate`; `promote()` is a pointer move that **requires a
  rollback target** (the `PromotionRecord` discipline). Prod execution runs **only promoted** versions.
- **Multi-path.** One `PrimitiveStorePort` with a `LocalPrimitiveStore` (this reference / bake-off baseline)
  **and** an `OmnigraphPrimitiveStore` adapter, chosen by `select_primitive_store(...)`. Omnigraph is a
  *selectable backend to race*, never a hardwired dependency.

## The generic executor (the "fetch the code by ref" idea)

`GenericExecutor.execute(version_id, inputs, caller_scope, mode)` is **one stateless runner for all
primitives**: it resolves the primitive, enforces **scope** (a public caller cannot run internal code) and
**promotion state** (prod runs only promoted), fetches the code from the bucket **by content ref** (cached by
hash — the cold-start mitigation), runs it through a **pluggable sandbox runner**, validates I/O against the
primitive's contracts, and returns outputs + a **receipt**. One generic image; the primitive is fetched
per-launch. This is the hosting plan's *"place workloads, don't rewrite them"* taken to its endpoint, and it
maps a stateless Cloud Run / K8s Job / Fly Machine to `(inputs, output-contract, code_ref) → outputs`.

## Production wiring (what changes when this leaves `experiments/`)

- `canonical_hash` → `src.teleon.experiments.ids.canonical_id` (the single-source authority).
- `ContentBucket` → S3/R2/MinIO behind the credential-plane (env-name indirection), or Omnigraph's Lance store.
- `GenericExecutor.runner` (demo `exec`) → the real shared sandbox (gVisor/Firecracker + Cedar policy).
- `OmnigraphPrimitiveStore._client` → a real HTTP/MCP client to an Omnigraph instance; then **bake it off**
  against `LocalPrimitiveStore` on measured receipts (multi-path law) before adopting it for the moat layer.
- Wire `--self-test` into `run_proofs`; pyprefix pass before promotion into `src/`.
