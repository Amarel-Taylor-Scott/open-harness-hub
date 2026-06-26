# Registry build-out — roadblocks & slowdowns log (2026-06-23)

Honest log of issues hit while wiring every registry to embeddings / records / pgvector / search, what I resolved
myself, and what's genuinely blocked on a credential / external resource. Status: **resolved** (fixed it) ·
**floor** (works at a deterministic floor; a key upgrades it) · **owner-gated** (needs a credential / provisioning).

| # | Issue | Impact | Status | Resolution / what's needed |
|---|---|---|---|---|
| 1 | **Only 14 of the catalogs were searchable** (hand-listed `CATALOGS`) | federated search / guardrail / MVP grounded against 14, not the corpus | **resolved** | `discover_catalogs()` auto-scans `architecture/*.json`, validates (list + id-field + lookup round-trip), registers them → **147 catalogs** searchable. `check_registry_discover` proves it. |
| 2 | **~33 registries are NOT catalog-shaped** (policy / runtime / derived — e.g. `compliance`, `human_approval`, `failure_recovery`, `registry_dependency_graph`) | can't be record-searched | **by design** | They surface via their **backing module** (a policy engine / runtime), not the search menu. The facets honestly list them as "relevant, not on the menu." Not a bug — not everything is a record list. |
| 3 | **Embedding is a 64-dim lexical hash** (deterministic floor) | vector search ranks real records first but is **not semantic** | **resolved (local, no key)** | **LOCAL Ollama `nomic-embed-text`** (already installed) gives 768-dim SEMANTIC embeddings — pdf 0.74 > object-detection 0.39, **no API key**, private. Wired via `embedding_port.best_embedder()` (`check_local_embedder`). The cloud key was a reflex, not a requirement (see [local-first-decision-rigor](../codex/local-first-decision-rigor.md)). Lexical is the offline fallback. |
| 4 | **No Postgres+pgvector provisioned here** | loading 147k records into a server vector DB | **resolved for dev (local)** | Vector search runs **locally with no server**: the in-memory cosine already works; `sqlite-vec` / FAISS are local/keyless next rungs. pgvector (DDL + plan ready) is the **scale** option, not a requirement. |
| 5 | **Records are mostly synthetic** (2,317 real + 144,683 flagged synthetic to hit 1000/registry) | the 1000/registry is scale-proof, not all real | **floor / population** | Real volume accrues via the **population engine** (`populate`, `distill_kaggle_kernels`, the standing harvest) against real sources — over time + cadence, not one turn. Synthetic is flagged `synthetic:true`, never claimed real (repo law). |
| 6 | **LLM Tier-1 (distill/guardrail)** | runs the deterministic floor, not a model judge | **resolved (local, no key)** | **LOCAL Ollama** (`gemma4-e2b` already installed, localhost, keyless) serves the cheap Tier-1 lane — the cascade's cheap gate is *supposed* to be a local model. The cloud `OH_LLM_API_KEY` is for frontier/scale only, not required. |
| 7 | **MetaKaggle full pull is 11 GB** (+198 GB code) | can't distill "millions" of kernels here | **owner-gated** | Mined a **bounded 94-kernel sample** (proven). Full pull runs against the Kaggle credential (authenticated) on a machine with the disk. |
| 8 | **FB pages not directly scrapeable** (ToS) | can't auto-harvest theaiempire / DeepRepo | **floor** | Governed path: owner-paste OR `fb_page_scrape` (`RAPIDAPI_KEY` / `APIFY_TOKEN`). `ingest_fb_page_links.py` extracts + cleans the GitHub links from pasted/fetched post text. |

## Slowdowns (performance notes)
- **Auto-discovery scans ~180 JSON files** on first use → **cached** (`_DISCOVER_CACHE`), so it's a one-time cost per process. If it ever dominates, precompute the catalog index to a file in the loop.
- **Record generation is in-memory-fast** (147k enriched records build in seconds), but the real cost is the **DB load** (the pgvector COPY), which is the materialization step, not the build.
- **`build_records(reg, 1000)`** recomputes embeddings each call; for the real DB load, embed once and store (the pgvector table caches them).

## The loop (automation)
`scripts/registry_loop.py` is the refresh **loop body** (discover → dependency-graph → records → MVP; + credential-gated population). Run it on a cadence: `watch -n 900 'PYTHONPATH=. python3 scripts/registry_loop.py --run'`, cron, or wire it as a flywheel under `./loop`. Everything downstream of the registries is **computed**, so one pass keeps the graph, the records, and the public showcase current as registries grow.

## What's genuinely blocked vs resolved (after local-first review)
- **Resolved myself, NO key:** menu coverage (1), catalog adapters, records pipeline, **semantic embeddings (local Ollama nomic, 3)**, **local vector search (4)**, **local LLM Tier-1 (6)**, the loop, the guardrail/MVP grounding.
- **Truly external (and even these mostly have keyless paths):** full MetaKaggle pull = *disk*, not a key (Kaggle CLI already authenticated); FB *automated* harvest = `RAPIDAPI_KEY` **or** the keyless owner-paste path. A cloud key is now only ever the *scale* option, never the requirement.
- **Inherent (not a bug):** policy/runtime registries aren't searchable record-catalogs; real record volume is a population process, not a fabrication.

> Correction (local-first rigor, see [local-first-decision-rigor](../codex/local-first-decision-rigor.md)): rows 3/4/6
> were wrongly framed as "needs a cloud key." All three run **locally, free, open-source, keyless** — and embeddings
> are *better* local (semantic) than the floor. The cloud keys are the exception (scale), not the default.
