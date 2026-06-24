# GOAL — Claude Code whole-surface enrichment loop (the `/loop` command)

> Owner ask (2026-06-24): a **Claude Code loop** — a `/loop` command, **not** the `./enrich` Python daemon — to run
> for the **next ~3 days, iterating every ~30 minutes**, filling gaps and generating **records, metadata, embeddings,
> tools, descriptions, use-cases** for **every** surface: **Baltor · Teleon · the Open\*Hubs · the new
> Observer/Spotter supervisor·monitor·session-reply tool · Discovery**.

**This is the Claude Code driver. `./enrich` / `scripts/enrichment_loop.py` are the deterministic Python version — do
NOT start them.** The whole point of the Claude Code loop: *I* am the model each cycle, so the generative parts
(descriptions, long-descriptions, use-cases, new tool definitions, gap analysis, new intervention types) get real
model quality instead of the deterministic floor the Python scheduler drops to whenever the Ollama Cloud lane is
rate-limited (HTTP 429). I still drive the **bulk deterministic workers** for scaled record/embedding generation.

## The loop command

```
/loop 30m Run ONE cycle of the Claude Code whole-surface enrichment loop per docs/goals/claude-code-enrichment-loop.md.
```

- **Cadence:** ~30 minutes between cycles (`/loop 30m`). "Or so" is fine — a cycle that needs longer just runs longer.
- **Horizon:** 3 days. **Start 2026-06-24; STOP after 2026-06-27.** Each cycle, if `date +%F` is **after `2026-06-27`**,
  do nothing and **do not reschedule** (let the loop end).
- **Manual stop:** if `.agent/CLAUDE_LOOP_STOP_REQUESTED` exists, halt cleanly and do not reschedule.
  Create it with `: > .agent/CLAUDE_LOOP_STOP_REQUESTED`; clear it with `rm -f .agent/CLAUDE_LOOP_STOP_REQUESTED`.
- **Continuity across cycles:** state lives in `data/dev-intel/claude_loop_state.json` (the breadcrumb). Each cycle
  reads it to know what was done last and what to do next, and writes it back at the end. The session-summary between
  fires is lossy — **the breadcrumb, not memory, is the source of truth for "where am I."**
- This is a Claude Code session loop: it runs while this Claude Code session is alive. If you need it to survive the
  terminal closing for the full 3 days, the durable alternative is the `/schedule` cloud routine (same prompt, cron
  cadence) — but the owner asked for the `/loop` command, so that is the default.

## One cycle = this exact contract

1. **Guard.** If `.agent/CLAUDE_LOOP_STOP_REQUESTED` exists or `date +%F` > `2026-06-27`: stop, don't reschedule. Else continue.
2. **Read the breadcrumb** (`data/dev-intel/claude_loop_state.json`): `cycle`, `surface_cursor`, `last_gate_cycle`,
   per-surface `last_enriched`, and `notes`. This tells you the round-robin position and what is most overdue.
3. **Pick ONE highest-leverage gap.** Cold-start: round-robin the surfaces in order
   `[teleon, hubs, observer, baltor, discovery]` so every surface gets touched early. Steady state: pick the
   **most-overdue / thinnest** target — a registry with empty `description`/`use_cases`/`embedding`, an ontology
   `gap_to_close`, a hub profile missing fields, an Observer module with no behavioral-heuristic records, a thin plane
   with no real tool definitions. **Prefer the gap that lifts the most coverage per cycle.**
4. **Generate REAL output for that gap** — both halves:
   - **Bulk (run the deterministic worker):** invoke the matching script from the surface table below so scaled
     records/embeddings/sites regenerate from the registries (computed, not hand-typed).
   - **Model-quality (your added value):** write the real descriptions / long-descriptions / use-cases / new tool
     definitions / new intervention types / closed ontology gaps that the deterministic floor can't. This is *why*
     it's a Claude Code loop.
5. **Validate.** Run the narrow checks for what you touched (e.g. `python3 scripts/validate.py <paths>`,
   the relevant `check_*` / `--self-test`). Fix what you broke **in the same cycle** (change a seam/count → update its
   asserting check).
6. **Gate on cadence.** Every **4th cycle** (≈ every 2 h) run the full proof gate:
   `PYTHONPATH=. python3 scripts/run_proofs.py`. Keep it green, or **record the red** in the breadcrumb `notes` and
   keep going (never silently leave a red; never fake green).
7. **Commit** on `feat/scale-goals-and-hygiene` (or the current working branch) with a clear message, e.g.
   `enrich(teleon): use-cases + embeddings for N registry records [claude-loop cycle K]`. High-volume rows **stream to
   JSONL/DB staging**, not thousands of new git files.
8. **Update the breadcrumb**: bump `cycle`, advance `surface_cursor`, set the surface's `last_enriched`, record the
   gate result if run, and a one-line `notes` entry on what to pick up next.
9. **Reschedule** the next cycle (~30 min) unless step 1 said stop.

## Surfaces, what to enrich, and the worker to drive

| Surface | What "enrich" means here | Bulk worker to run | Your model-quality layer |
|---|---|---|---|
| **Teleon** (registry federation, ~100+ registries in `architecture/registry_ontology.json`; menu `src/teleon/registry/port.py`) | per-record embeddings · descriptions · long-descriptions · use-cases · labels · keywords; new records via population; close ontology `gap_to_close` | `python3 scripts/registry_loop.py --run --with-population` (drives `src/teleon/registry/{populate,enrich}.py`); `python3 scripts/build_million_records.py`; `python3 scripts/distill_kaggle_kernels.py` | write real use-cases/descriptions for thin entries; add a missing registry entry or close a `gap_to_close` with a correct shape |
| **Hubs** (22 Open\*Hubs; profiles `architecture/hub_profiles.json`) | hub profile fields, computed counts, rebuilt surfaces | `python3 scripts/build_hub_sites.py --all` | fill a hub profile's missing wedge/description/use-case fields with real copy |
| **Observer / Spotter** — the **supervisor·monitor·session-reply** tool (`src/teleon/observer/{router,capture,review,session_store}.py`; patterns in `architecture/behavioral_heuristics.json`) | new intervention types, behavioral-heuristic records, session-outcome examples (the accept/reject moat loop), descriptions/use-cases per module | `python3 scripts/build_spotter_surface.py`; `python3 scripts/build_code_genome_index.py` | add a real behavioral heuristic (pattern → intervention), a new intervention type, or labeled session-outcome examples |
| **Baltor** (applied context product) | one applied-context flywheel cycle; context records/metadata | `PYTHONPATH=. python3 scripts/baltor_flywheel.py --once` | enrich a context-record's metadata/use-cases where thin |
| **Discovery** (tool harvest) | new staged candidate tools from the forges | `python3 scripts/harvest_tools.py --run` *(network; honest rate-limit stop — skip if 403)* | classify/label a freshly harvested batch; promote nothing without license + dedupe |

If a worker is slow / rate-limited / network-blocked, it fails **honest** — record it and switch to a different
surface's gap. **Never stop the loop because one path is blocked.**

## Governance every cycle must hold (non-negotiable)

- **`serves_truth=false`** on every generated artifact; generated rows are **candidates** (discovery ≠ trust), never
  asserted as verified fact.
- **No magic values:** counts/totals are **computed** from the registries (`check_*` scripts), **never typed into prose**.
- **Lossless distillation:** any distillation/compression/promotion makes a **new versioned** layer; raw + held-out +
  rejected + lineage survive. Omitted ≠ deleted.
- **Warrant before change**, matched to blast radius. Brand / strategy / vocabulary / pricing / product-structure
  changes need **clear owner intent** — not a unilateral loop call. Record the warrant.
- **Move, not delete** for superseded files (`archive/legacy/<original-path>` + manifest).
- **No insurance** pipelines. **No real PII / secrets** — synthetic or public metadata only; env-var **names** only.
- **Change a seam/count → update its asserting check in the same cycle.** Keep the gate green or **record the red**.

## Breadcrumb schema (`data/dev-intel/claude_loop_state.json`)

```json
{
  "loop": "claude-code-enrichment",
  "start_date": "2026-06-24",
  "stop_after": "2026-06-27",
  "cycle": 0,
  "surface_cursor": 0,
  "surfaces": ["teleon", "hubs", "observer", "baltor", "discovery"],
  "last_gate_cycle": 0,
  "last_gate_result": "",
  "last_enriched": {"teleon": null, "hubs": null, "observer": null, "baltor": null, "discovery": null},
  "notes": ["initialized 2026-06-24 — first cycle: teleon"]
}
```
