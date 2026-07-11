# Agent Coordination — running Codex + Claude Code/Fable concurrently, without collision

> Owner (2026-07-09): "we have Codex working simultaneously to Claude Code, and calls to various endpoints — keep that
> in mind to maximize impact." Two (or more) agents share ONE working tree, ONE git branch, and the SAME key pools.
> Uncoordinated, that is collision + wasted quota, not impact. This is the protocol. Both agents commit as the same
> git user, so *file/lane separation* — not author — is how we avoid clobbering.

## 1. Lanes — own different FILES so edits never collide

Observed reality: Codex has been editing the experiment modules (`reuse_experiment_grid.py`, `edge_exposed_gapfill.py`,
`realistic_session_harness.py`, `primitive_reuse_prompt_matrix.py`, `run_large_project_ab.py` — e.g. the
retryable-error split) and running the grid. So:

| Lane | Owner | Paths (edit only these) |
|---|---|---|
| **Experiment spine** — reuse grid, prompt matrix, buildout genomes, harnesses, running the model zoo | **Codex** | `scripts/reuse_experiment_grid.py`, `scripts/primitive_reuse_prompt_matrix.py`, `scripts/run_large_project_ab.py`, `scripts/buildout_forge*.py`, `scripts/{edge_exposed_gapfill,realistic_session_harness,multi_step_task_ab,input_token_lever,search_rag_primitive_pack}.py`, `data/dev-intel/reuse_experiment_grid/` |
| **Cleanup · infra migration · docs · inventory** | **Claude Code / Fable** | `docs/*`, `.gitignore`, `db/postgres/*`, new `scripts/load_*`/`scripts/*inventory*`, `scripts/consolidate_keys.py`, `architecture/storage_tier_policy.json`, memory |
| **Shared (coordinate before editing)** | either, announce first | `CLAUDE.md`, `FOR_CODEX.MD`, `flywheel_proof_modules.py`, `db/postgres/schema.sql`, `BIBLE.md` |

**Rule:** do NOT edit a file in the other agent's lane. If you must, say so in your turn and make it one small atomic
commit. When you see a "modified by user or linter" note on a lane-Codex file, that's Codex — take it into account,
don't revert.

## 2. Endpoints — partition the pools so both run at full speed

The 29 OpenRouter keys + Mistral/SambaNova/etc. are shared; two agents hammering the same pool = mutual rate-limiting.

- **Partition convention:** an agent reads `.agent/key_partition.json` (if present) for its key slice; default split —
  **Codex → OpenRouter pool (the big 29-key rotation) + Mistral**; **Claude/Fable → SambaNova · Together · Groq ·
  Cerebras · NVIDIA + the openrouter tail keys (indices 24–28)**. If only ONE agent is making live calls, it may use
  all pools.
- **Gemma via CDP is SINGLE-SESSION** (one logged-in debug Chrome on :9222) — **only one agent uses it at a time**;
  announce before a gemma run. It returns clean error rows when busy/down, so it never fabricates.
- **Don't double-run the same job.** The reuse grid is Codex's — Claude/Fable does NOT run `reuse_experiment_grid.py
  --live` or its supervisor (this session's Claude supervisor was stopped to yield the lane). Check
  `pgrep -f "reuse_experiment_grid --live"` before launching anything that calls model endpoints.
- **Never kill the other agent's processes.** Leave `codex`/`codex-code-mode-host` procs alone; leave Claude's
  background jobs alone. Coordinate via lanes, not `pkill`.

## 3. Git discipline (shared branch, ~870 commits ahead of origin)
- **Small, frequent, single-purpose commits** — smaller blast radius if the trees diverge.
- **Only stage YOUR lane's files** (`git add <specific paths>`, never `git add -A`) — prevents grabbing the other
  agent's in-flight edits.
- **Before any push / history rewrite** (e.g. the P0 `.git` shrink): STOP and get explicit owner sign-off, and
  coordinate so the other agent isn't mid-commit. Irreversible + outward-facing.
- If you hit a merge/rebase conflict on a shared file, take the other agent's version for its lane and re-apply your
  change minimally.

## 4. Shared state / claim (lightweight)
- Optional `data/dev-intel/agent_coordination/claims.jsonl` (append-only): `{agent, lane, paths, task, started_at}`
  so each agent can see what the other is touching. (Note: `data/dev-intel/` is gitignored now — claims are local
  coordination, not committed.)
- The grid's incremental `grid.json` is the shared experiment state — **resumable + retryable-error-aware** (Codex's
  fix), so a single writer at a time is correct; a second writer would race it. One grid runner only.

## 5. Division of the 5M/40M plan (so both agents advance it in parallel)
Per `AIDEVOBSERVER-5M-40M-PLAN.md`:
- **Codex:** milestones 2/5/6 (retrieval benchmark, savings replay across lanes, consistency proof) — it owns the
  experiment harnesses that produce the receipts.
- **Claude/Fable:** milestones 1/7 + infra (the inventory scanner + status-ladder counts, the Postgres/pgvector/
  warehouse migration, object-storage for bodies, 40M-readiness sharding) + all docs/dashboards.
- **Shared:** the receipt schema + `/api/observer/primitive-corpus` contract (agree in `db/postgres/schema.sql` +
  a doc before either implements).

**Net:** Codex proves savings on the harnesses; Claude/Fable builds the substrate + inventory + migration + docs the
proofs run on. Different files, partitioned endpoints, one grid runner, atomic commits — that is how two agents
compound instead of collide.
