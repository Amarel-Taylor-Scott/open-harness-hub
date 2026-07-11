# HANDOFF → GPT-5.6 agent — reuse/token-savings experiment workstream (session 2026-07-09)

> **For the whole-system picture** (every surface, the architecture, the primitive DB, the infrastructure/data-tier
> migration — flat-file/JSONL → databases/microservices, hosting on Fly.io, costs, separation of concerns) read
> **`SYSTEM-OVERVIEW.md`**. This handoff is the experiment-workstream detail.


> Written for a fresh agent taking over. Read this FIRST, then `context/blackbox.md` + the repo `CLAUDE.md`.
> Everything below is `candidate=true / serves_truth=false`. **The headline discipline of this workstream:
> never conclude from a single cell or a small run — report aggregates with sample sizes (MIN_N=8).**

## 0. The one reconciliation you must inherit

Earlier in this session an over-claim was made and then **refuted by more experiments**: *"prompt-injecting a
verified primitive always fails; only deterministic composition works."* That was an artifact of ONE prompt
(`signatures_only`) on ONE model (codestral). The corrected, executed picture:

- **Reuse-via-prompt is PROMPT-dependent and MODEL-dependent — not doomed.** In the 6-variant race,
  `full_source_asis` (show the FULL tested module + "use as-is, do NOT re-implement") reaches pass≈0.5–1.0 at
  ~68 median output tokens, vs `signatures_only` (~0.1 pass, model re-implements). But some models still fail
  `full_source_asis` → **needs the full 7-model grid before ANY universal claim.**
- **Deterministic composition is the reliable FLOOR:** all covered project types boot + pass their real hidden
  oracles at **0 model tokens**, model-independent (`multi_step_task_ab.deterministic_compose_run`,
  `edge_exposed_gapfill`).
- **Partial composition is the realistic model** (owner's framing): the DB solves the portions it covers, exposes
  typed edges, the LLM fills only the task-specific gap (`edge_exposed_gapfill.py`, coverage=0.75 demo).
- **Realistic senior-dev sessions are INPUT-token-dominated** — the growing conversation + re-read files are re-sent
  every turn, so a long session over a big codebase is millions–billions of *input* tokens; single-shot *output*
  savings are the rounding error. This is the biggest, least-explored savings lever
  (`realistic_session_harness.py`; even a 5-turn session is in:out ≈ 8:1).

Do **not** re-assert "reuse fails" or "5–7×" or "1.17M primitives" as settled fact anywhere. Those are unproven /
prompt-dependent / raw-count. Lead with executed, both-pass, n≥MIN_N aggregates only.

## 1. The 10 modules built this session (all `--self-test` green, under `_repos/shared-backend-components/`)

| # | Module (scripts/…) | Purpose | self-test | Role |
|---|---|---|---|---|
| 1 | `automation_directory_forge.py` | mine public workflow ecosystems → deterministic primitive candidates + molecules (offline) | `--self-test` | produces `make_webhook_worker` molecule |
| 2 | `buildout_forge_automation.py` | signed-webhook ingest-worker genome + hidden HMAC/idempotency/metrics oracle | `--self-test` | registers `webhook_ingest_worker__stdlib_http__v0` |
| 3 | `multi_step_task_ab.py` | `PrimitiveSessionManager` (inject-once) + multi-step compounding + **deterministic compose** | `--self-test` | compose lane engine |
| 4 | `search_rag_primitive_pack.py` | verified search/labeling/RAG primitives + 3 bootable molecules | `--self-test` | WITH-DB side of 3 families |
| 5 | `buildout_forge_search_rag.py` | 3 large project genomes (BM25 search, labeling, RAG) + hidden oracles | `--self-test` | registers those 3 families |
| 6 | `primitive_reuse_prompt_matrix.py` | race 6 prompt variants × model × project; records reimplementation flag | `--self-test` | defines the 6 `prompt:<variant>` lanes |
| 7 | `reuse_experiment_grid.py` | **THE grid**: 4-lane × model-zoo × family × repeats; resumable; aggregates-only; MIN_N=8 | `--self-test` | writes `grid.json` |
| 8 | `agent_instruction_compiler.py` | repo guidance → verified enforced automation (hooks/CI/policy). CANDIDATE product hypothesis | `--self-test` | not a grid lane |
| 9 | `edge_exposed_gapfill.py` | partial composition: cover hard infra + expose edge; LLM fills 1-function gap | `--self-test` | `edge_gapfill` lane (not yet in grid) |
| 10 | `realistic_session_harness.py` | multi-turn tool loop; full-session INPUT-dominated accounting; WITH/WITHOUT DB | `--self-test` | realistic-session lane (not yet in grid) |

Run all at once via the umbrella: the modules are registered in `scripts/flywheel_proof_modules.py` (→ `run_proofs`).

### 1b. Added after the initial handoff (same session — best-practice improvements)
- **`scripts/input_token_lever.py`** (`--self-test`) — quantifies the BIGGEST lever (ideation #20/#18/#22): replacing
  verified-module bodies with compact capability CARDS cuts the INPUT tokens that dominate long sessions.
  Structural proxy over real module sizes: a **50-turn session cuts input ~218,800→28,750 tokens (~87%)**, and the
  saving COMPOUNDS with turns × verified fraction. Live success under card context is what `realistic_session_harness`
  tests. **This is where "billions saved" actually comes from — not single-shot output.**
- **`scripts/run_reuse_grid_to_completion.sh`** — self-healing supervisor: re-invokes the RESUMABLE grid until all
  740 cells present or it stalls 3× (rate-limit / gemma session down). The grid process dies silently every ~75–110
  cells (not root-caused; resume covers it) — run the supervisor instead of babysitting restarts.
- **Grid aggregates now include** `median_in_tokens`, `input_output_ratio` (sessions are input-dominated),
  `tokens_per_pass` (cost-per-pass proxy = all tokens incl. failed attempts / passing run) — the ideation #22/#43/#44
  metrics. Prefer `tokens_per_pass` as the fair cross-lane comparator; report `by_lane_model` not pooled `by_lane`.

## 2. Current experiment state (evolving — read `data/dev-intel/reuse_experiment_grid/grid.json`)

`reuse_experiment_grid.py` is the spine. Lanes present in `grid.json`: `without`, `prompt:{signatures_only,
full_source_asis, import_minimal, usage_example, docstring, negative_guarded}`, `compose`. Aggregates roll up
`by_lane`, `by_lane_model`, `by_lane_family` — **trust `by_lane_model`/`by_lane_family` for any per-model claim;
pooled `by_lane` can hide a tiny per-cell n.**

**Reportable aggregate (6 models: codestral·deepseek·gpt-oss-120b·qwen·glm·gemma-4-coding; n≈56 per lane, well above
MIN_N):** `compose` pass **1.0 @ 0 tok** (deterministic floor, model-independent) · `full_source_asis` pass **0.625 @
108 med out-tok** · `without` pass **0.614 @ 1374 med out-tok** · `signatures_only` **0.089** (reimpl 0.45) · other
prompt variants ≈0. **Reconciled read: `full_source_asis` ≈ `without` on pass rate at ~13× fewer output tokens (reuse
DOES pay with the right presentation); `compose` is the only 1.0/0-token lane; the earlier "reuse fails" was a
prompt artifact of `signatures_only`.** The grid resumes + the retryable-error split (rate-limit ≠ failure) keeps it
honest. Remaining toward the full 740-cell target: llama-3.3-70b + more gemma/gpt-oss repeats — run
`bash scripts/run_reuse_grid_to_completion.sh` (survives the env SIGKILL of long background procs via resume).

## 3. Gemma-4-coding via iamretarded.net (working, session-dependent)

`gemma-4-coding` is reached through **browser-context CDP** (Cloudflare blocks raw HTTP). VERIFIED live this session
(built a real labeling service, oracle_pass=True, 159 out-tok). Path: model string `openwebui:gemma-4-coding` →
`reuse_experiment_grid._openwebui_agent` → `scripts/openwebui_cdp_bridge.cdp_chat`. Requirements:
1. A logged-in Chrome with `--remote-debugging-port=9222` at `https://ui.iamretarded.net` (isolated profile
   `/tmp/aidevobserver-gemma-profile`). Launch: `google-chrome --user-data-dir=/tmp/aidevobserver-gemma-profile
   --remote-debugging-port=9222 --new-window https://ui.iamretarded.net &` then sign in.
2. Verify: `python3 -c "import scripts.openwebui_cdp_bridge as b; print(b.cdp_chat('gemma-4-coding','','ping',timeout=60).get('ok'))"`
3. With no logged-in tab, `cdp_chat` returns a clean recorded error (never fabricates). Never touch a local Ollama
   gemma4 (overheat rule).

## 4. Open threads — do next (in order)

1. **Finish the grid across all 7 models** before concluding. Resumable:
   `python3 scripts/reuse_experiment_grid.py --live --models "openrouter:meta-llama/llama-3.3-70b-instruct,openrouter:openai/gpt-oss-120b,openwebui:gemma-4-coding,openrouter:z-ai/glm-4.6,openrouter:deepseek/deepseek-chat" --repeats 3`
   (The runner has been dying ~every 75–110 cells — cause not root-caused; resume covers it. Worth hardening.)
2. **Wire the two missing lanes into the grid** — `edge_gapfill` (partial composition) and `realistic_session`
   (input-dominated). These are the lanes most likely to show *real* savings; today they're standalone A/Bs.
3. **Go up in task scale** — the families are all small stdlib HTTP services. The owner repeatedly asked for
   senior-dev-scale, billion-token, long-context sessions. `realistic_session_harness.py` is the seed; extend it to
   large multi-file working sets + many turns and measure the INPUT-token save from compact verified references.
4. **Respect MIN_N=8; report `by_lane_model`.** Keep the no-proxy discipline (both-fail = inconclusive; headline only
   both-pass positive).
5. See `docs/RESEARCH_PATHS_AND_IDEATION.md` for the full catalog of paths to test.

## 5. This session's commits
`7c1b009b3 automation forge` → `f64636213 multi-step` → `6cd88afe3 compose` → `a3f01c179 search-rag` →
`21c9e4501/c21fbafee/730590da4 reuse-matrix` → `2f7de6fb8 agent-compiler` → `736ea401c grid` → `ff9119a5a resumable` →
`b6099b7e4 gapfill` → `d99b9e711 gemma` → `e45658b27 realistic-session`. Each maps 1:1 to a module above.
