# Cleanup Backlog — prioritized, actionable (for Claude Fable / any agent doing cleanup)

> The concrete cleanup work outstanding as of 2026-07-09, ranked P0→P4, each with **What · Why · How · Where ·
> Done-means**. Obey the repo laws: **move never delete** (archival), **lossless distillation** (preserve raw +
> lineage), **warrant before change**, and **confirm before anything irreversible/outward-facing** (git history
> rewrites, pushes, deletions). `candidate=true / serves_truth=false` for anything generated. Companion:
> `SYSTEM-OVERVIEW.md` (§5 infra), `HANDOFF-GPT-5.6.md` (experiment state).

---

## P0 — Git repo bloat: 68 GB of generated data is TRACKED in git (`.git` = 2.6 GB, 55,606 tracked data files)

- **What:** `_repos/shared-backend-components/data/dev-intel/` (generated candidate rows, receipts, 38,880 JSONL
  files, incl. a 2,070-file `economic_observations-*.jsonl` one-record-per-file anti-pattern and multi-GB monolith
  JSONLs) is **committed to git**, not gitignored. `.git` is 2.6 GB and growing.
- **Why:** Generated `candidate=true` data is NOT source — it belongs in a database / warehouse / object storage
  (SYSTEM-OVERVIEW §5), never in git history. It bloats every clone, slows every operation, and will only grow.
- **How (careful, staged — confirm with owner before the history rewrite):**
  1. Add `data/dev-intel/` (and other generated dirs: `dist/`, large `catalog/knowledge-packs/data/`) to
     `.gitignore` going forward.
  2. `git rm -r --cached _repos/shared-backend-components/data/dev-intel` — **untracks without deleting the files on
     disk** (they stay for the running experiments). Commit the untrack.
  3. Verify `run_proofs` + the experiment harnesses still find their data by path (they read the working tree, not
     git) — they should be unaffected.
  4. **Only after owner confirmation** (irreversible): shrink history with `git filter-repo --path
     _repos/shared-backend-components/data/dev-intel --invert-paths` on a clone, verify, then coordinate the
     force-push (outward-facing — needs explicit approval; the branch is 871 commits ahead of origin).
- **Where:** `.gitignore` (repo root + `_repos/shared-backend-components/`), `data/dev-intel/`.
- **Done-means:** `git check-ignore data/dev-intel/...` returns ignored; `git ls-files data/dev-intel | wc -l` == 0;
  files still present on disk; harnesses green; `.git` shrunk (post history-rewrite, if approved).
- **STATUS 2026-07-09 (commit 6f3c321e9): steps 1–3 DONE + verified** — `data/dev-intel/` ignored, 55,606 files
  untracked (0 tracked now), files intact on disk, harnesses green, git-status noise gone. **Step 4 (history rewrite
  to shrink `.git`=2.6GB) DEFERRED — needs explicit owner approval** (irreversible; branch is ~870 commits ahead of
  origin, so rewriting BEFORE the next push is far cheaper than after). Follow-up candidates needing per-subdir
  review (contain curated/published paths — do NOT blind-untrack): `dist/` (15,623 tracked), `_repos/_generated`
  (6,027 tracked).

---

## P1 — Data-tier migration: JSONL monoliths → Postgres / pgvector / warehouse / object storage

- **What:** Primitive cards + indexes live in flat JSONL; the Postgres schema (`db/postgres/schema.sql`) exists but
  cards were never loaded, the pgvector `object_embedding` HNSW index is commented out + unpopulated.
- **Why:** No indexed query, whole-file re-reads, no transactional promotion, no ANN search at scale. The tiered
  policy (`architecture/storage_tier_policy.json`: config=JSON / operational=Postgres+pgvector / history=warehouse)
  is designed but not realized.
- **How:** Follow the migration table in `SYSTEM-OVERVIEW.md` §5. Concretely, smallest-first:
  1. Write a **loader** `scripts/load_primitive_cards_to_postgres.py` (candidate → `component`/`component_version`),
     idempotent + dedupe-at-load, `--dry-run` first. Keep the JSONL as the raw layer (lossless).
  2. Populate `object_embedding` for `subject_type='primitive'` + **enable the pgvector HNSW index**; wire
     `intent_query`/`capability_retrieval` to read it (a `VECTOR_INDEX_PROFILES` entry).
  3. Collapse the 2,070 `economic_observations-*.jsonl` into **one warehouse table** (history tier), partitioned by
     time; stream large monolith JSONLs (candidates, breakdowns, Q&A) → staging table + CDC.
  4. Big blobs (raw source snapshots) → object storage with handles in the DB.
- **Where:** `db/postgres/schema.sql`, `architecture/storage_tier_policy.json`, new `scripts/load_*` loaders.
- **Done-means:** cards queryable from Postgres; ANN search served from pgvector HNSW; `economic_observations` is one
  partitioned table; a rehydration test proves JSONL↔DB losslessness; local→cloud swap stays config-only.

---

## P2 — Documentation reconciliation (finish what the 2026-07-09 audit started)

- **What:** The first-read path was reconciled for the top docs (both CLAUDE.md, FOR_CODEX.MD, REAL_SAVINGS_NUMBERS,
  the per-seat + 486× banners). **Remaining stale/overclaiming docs** the audit flagged but that were left:
  `docs/strategy/portfolio-pmf-solidification-2026-07-01.md` (carries "486× context reduction" as shipped),
  `docs/benchmarks/edge-first-composition-benchmark-plan.md`, `docs/NORTHSTAR.md` (reconcile date + savings pointer),
  the 11 `docs/codex/*.md` topic handoffs (superseded by `strategy/primitive-system-end-to-end-briefing.md`),
  `docs/CURRENT-STATE.md` (06-09 snapshot — consider archiving).
- **Why:** A fresh agent must not re-adopt "486×/47.5%/1.17M as proven savings"; contradictory path counts
  (26,880 vs 76,800) and stale "current" labels mislead.
- **How:** Add a superseded/caveat banner (as done for the top docs) OR `archive/legacy/`-move the ones fully
  superseded (move never delete; record in the manifest). Add the honest-savings pointer to `NORTHSTAR.md` + bump its
  reconcile date. Run `scripts/check_handoff_docs_freshness.py` after (don't break the verbatim-phrase gate).
- **Where:** `docs/strategy/`, `docs/benchmarks/`, `docs/codex/`, `docs/NORTHSTAR.md`, `archive/legacy/`.
- **Done-means:** no first-read-path doc asserts an unproven savings multiplier as fact; superseded docs are
  banner-marked or archived; freshness gate green.

---

## P3 — Experiment completion (the reuse grid + the two missing lanes)

- **What:** The comprehensive grid (`reuse_experiment_grid.py`) is at ~365 completed cells of a 740 target across
  6 of 7 models; `edge_exposed_gapfill` (partial composition) and `realistic_session_harness` (input-dominated)
  define their own lanes but are **not yet wired into the grid**; the live realistic session was `both_fail`
  (glm-4.6 couldn't finish the task in 15 turns).
- **Why:** These two lanes are the ones most likely to show *real* savings (partial composition; input-dominated
  sessions); the grid needs all 7 models × MIN_N to be definitive.
- **How:** (1) `bash scripts/run_reuse_grid_to_completion.sh` — resumable supervisor; survives the env SIGKILL of
  long background procs. (2) Add `edge_gapfill` + `realistic_session` as grid lanes (own tasks, per-model). (3) Tune
  the realistic session: more turns (25–40) / a slightly easier feature / a stronger model to land a both-pass
  session-scale number.
- **Where:** `scripts/reuse_experiment_grid.py`, `scripts/run_reuse_grid_to_completion.sh`,
  `scripts/{edge_exposed_gapfill,realistic_session_harness}.py`.
- **Done-means:** grid at 740 cells / 7 models; both extra lanes in the aggregate; ≥1 clean both-pass session-scale
  A/B; report by `by_lane_model` with `tokens_per_pass`.

---

## P4 — Code & context hygiene

- **What / How:**
  - **MEMORY.md** rides near its 24.4 KB read limit (recompact to <17 KB periodically; move detail to topic files —
    the compaction routine is well-exercised this session).
  - **Env SIGKILL of long background procs (exit 144)** — root-cause (likely fd/process exhaustion from the many
    subprocess oracles, or a harness wall-clock limit) OR make the grid checkpoint-and-exit cleanly under a resource
    watchdog. Until then the supervisor's resume is the mitigation.
  - **Gemma CDP session** is fragile (needs a logged-in debug Chrome on :9222) — add a pre-flight
    `openwebui_cdp_bridge --probe` gate + auto-skip-with-clean-error when down (already returns error rows).
  - **Naming/graph:** run `scripts/codegraph.py --audit` before/after edits; keep the two naming planes (pyprefix /
    canonical_id) conformant (ratchet-gated).
  - **`run_proofs`** has 1,051 registered modules — keep every new module registered (this session's 11 are) and
    green; it's the real gate.
- **Done-means:** MEMORY under limit; grid completes unattended; gemma auto-skips when down; codegraph audit clean;
  `run_proofs` green.

---

### Sequencing for a cleanup pass
**P0 first** (untrack the data — biggest, safest win: `git rm --cached` is non-destructive to disk), then **P2**
(doc reconciliation — fast, high-signal), then **P1** (the real infra migration — the durable investment), with
**P3** running in the background (supervised grid) and **P4** as you touch each area. Confirm before any git history
rewrite / force-push (irreversible + outward-facing).
