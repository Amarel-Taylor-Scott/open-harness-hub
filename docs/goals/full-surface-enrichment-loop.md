# GOAL — Whole-surface enrichment loop (Baltor · Teleon · Hubs · Observer/Spotter · Discovery)

> Owner ask (2026-06-24): a loop to run for the **next ~3 days, iterating every ~30 minutes**, filling gaps and
> generating **records, metadata, embeddings, tools, descriptions, use-cases** for **all** aspects of the project —
> from Baltor, to Teleon, to the OpenHubForAI registries, to the new **Observer/Spotter** supervisor/monitor/session-review tool.

## The one command

```bash
./enrich            # start the 3-day loop (every 30 min), foreground
./enrich bg         # start it DETACHED (survives closing the terminal)
./enrich status     # read-only monitor (runs by surface + recent cycles + last gate)
./enrich stop       # clean stop after the current cycle (state preserved); ./enrich resume to re-enable
./enrich logs       # tail the loop log
./enrich run        # one cycle now (debug)
# pass-through flags:  ./enrich start --days 3 --interval-min 30 --gate-every 4 [--offline]
```

It is **separate from `./loop`** (the YC/sweep flywheel daemon) and uses its own stop flag
(`.agent/ENRICHMENT_STOP_REQUESTED`), so **both can run at once**. Body + scheduler:
`scripts/enrichment_loop.py` (`--self-test` proves the wiring). State:
`data/dev-intel/enrichment_loop_state.json`; log: `data/dev-intel/enrichment_loop.log`.

## What it does each cycle

A **cadence scheduler over the real worker scripts** (it does not reimplement them). Each cycle it picks the
**most-overdue** enrichment task by its own cadence, runs it as a subprocess, records the result, runs the **full proof
gate every 4th cycle** (~every 2h) to stay honest, and checkpoints state so a restart resumes. It never crashes on a
task error or a red gate — it records and continues for you to review. Tasks (interleaved by surface for a diverse
cold-start; steady state is cadence-driven):

| Surface | Task | Generates |
|---|---|---|
| **Teleon** | `registry_loop --run --with-population` | discover → dependency-graph → records **+ enrichment** (embeddings/descriptions/use-cases/labels/keywords) → MVP + population |
| **Teleon** | `build_million_records` | scaled candidate **records** via governed variation mutation (industry × geo × season × …) |
| **Teleon** | `distill_kaggle_kernels` | candidate registry **entries** distilled from mined Kaggle kernels (lossless, candidate-only) |
| **Teleon** | `build_capability_mvp` | the capability showcase, counts recomputed from the registries |
| **Hubs** | `build_hub_sites --all` | all 22 OpenHubForAI surfaces rebuilt from the registries |
| **Hubs** | `build_hub_browser` | the browse-everything hub table |
| **Observer** | `build_spotter_surface` | the Spotter surface (taxonomy + live review, computed counts) |
| **Observer** | `build_code_genome_index` | code-genome dogfood over `src/teleon` (candidate internal-reinvention) |
| **Baltor** | `baltor_flywheel --once` | one applied-context flywheel cycle |
| **Discovery** | `harvest_tools --run` *(network)* | new staged **tools** from the forges (honest rate-limit stop; skipped under `--offline`) |

## Updated context (state as of 2026-06-24 — read before driving deeper enrichment)

- **Proof gate is the source of truth:** `PYTHONPATH=. python3 scripts/run_proofs.py` (currently **669/669 green**).
  `scripts/flywheel_proof_modules.py` is only a registry list — running *it* is a NO-OP; run `run_proofs.py`.
- **Teleon federation:** **103 registries** in `architecture/registry_ontology.json` (schema-conformant, grounded on
  disk, 5 universes + static/discovery/meta kinds partitioned; `check_registry_ontology`). The universal menu is
  `src/teleon/registry/port.py`; population engines are `populate.py` / `enrich.py` (#84, the enrichment worker:
  embedding/description/long-description/use-cases/labels/keywords per record); search is `search.py`
  (BUILD/TROUBLESHOOT/IMPROVE). Records come from **population**, not hand-building.
- **Global Software Knowledge Graph** (`src/teleon/knowledge/`): `dependency_graph` (#101, transitive "this stack
  exists"), `product_distance` (#102, latent-space product overlap), `repo_similarity` (§2), `code_genome` (§9,
  signal + AST fork). Backing registries #99–103.
- **Observer/Spotter** (`src/teleon/observer/`): one **router** over an **11-module intervention taxonomy**
  (reinvention · stack_reinvention · product_reinvention · footgun[can-block] · adversarial · reinvention_cluster ·
  guidance · alternative · shortcut · oversized/duplicate-context) with a **global interruption budget** + graduated
  modes; `review == route_session("review_only")`; `capture.py` ingests Claude Code/Codex transcripts (proven on a
  real 2847-line session); `session_store.py` is the session schema + the accept/reject **outcome** loop (the moat).
  Patterns single-sourced in `architecture/behavioral_heuristics.json` (#103).
- **Hubs:** 22 OpenHubForAI registries; profiles in `architecture/hub_profiles.json` (`check_hub_profiles`); sites built by
  `build_hub_sites.py`. Counts are **computed** by `scripts/check_ai_done_right_surface_family.py` — never hand-typed.
- **Baltor / Teleon split (architectural law):** Baltor → Teleon → OpenHarnessHub, **never the reverse**
  (`check_portfolio_dependency_law.py`). Brand: product = **Teleon**; **AI Done Right** is the parent.

## Governance the loop (and any agent driving it) must hold

- **`serves_truth=false`** on every generated artifact; generated rows are **candidates** (discovery ≠ trust), never
  asserted as verified fact. High-volume rows **stream to the DB/pgvector**, not git.
- **No-magic-values:** counts are **computed** from the registries, never typed into prose.
- **Lossless distillation:** distillation/compression/promotion creates a *new versioned* layer; raw + held-out +
  rejected + lineage survive. Omitted ≠ deleted.
- **Warrant before change** (match the bar to blast radius); **move-not-delete** for superseded files
  (`archive/legacy/`); **no insurance** pipelines; **no real PII/secrets**; env-var **names** only.
- **Change a seam/count → update its asserting check in the same change.** Keep the gate green or record the red.

## When a task is blocked, switch paths (don't idle)

If a worker is slow/rate-limited/network-blocked (e.g. `harvest_tools` hits a 403), it fails **honest** and the loop
moves on — never stop the loop because one path is blocked. To deepen between cycles, an interactive agent launched via
`/goal follow the instructions in docs/goals/full-surface-enrichment-loop.md` should pick the **highest-leverage gap**:
fill a registry's thin records, add use-cases/descriptions to under-enriched entries, close an ontology `gap_to_close`,
add a missing Observer intervention type, or add a worker for a missing row family — then **gate it** and checkpoint.

## Run it

Owner-launched. Start with `./enrich bg` (detached) or `./enrich` (foreground). Monitor with `./enrich status`; halt
with `./enrich stop`. The 3-day window starts at first launch; it resumes cleanly if restarted.
