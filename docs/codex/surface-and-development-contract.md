# Surface + Development Contract (rules that prevent reinvention / regression)

> Installed 2026-06-25 after an incident: the autonomous work tunneled the BASIC landing sites instead of the
> built-out surfaces, and an audit found a parallel search/populate stack was built in `scripts/` instead of using
> the designed ports. **Nothing was deleted** (0 surface commits; the 3.2 MB design bundle + `web/` apps are intact),
> but the pattern must not recur. These rules bind Claude Code, the autonomous loops, and contributors.

> **Update 2026-06-26 (reconcile — the rules below are unchanged):** the canonical BUILT-OUT, shipped surface is now
> the **standardized 5-surface server `scripts/surface_server.py`** — one config-driven renderer, one byte-identical
> light-theme stylesheet (accent + copy are the only per-surface variables), enforced by
> `scripts/check_surface_server.py`. Its full design reference is **`docs/DESIGN-BIBLE.md`**. The `web/` React apps and
> the `dist/sites/openharness-design/` bundle remain the protected, richer references (rule 1 still applies to them);
> the surface_server is the live floor a generator must never shadow with a basic regen. `serves_truth = false`.

## 1. Surface source-of-truth — serve the BUILT-OUT surface, never a basic replacement
- **Canonical, expensive, protected surfaces (NEVER remove, regress, or shadow with a basic regen):**
  `web/{teleon,baltor,harness-hub,context-is-everything}` (the functional React apps — logins, Control Towers,
  30+ guided demos), `dist/sites/openharness-design/` (the 3.2 MB high-fidelity design handoff), `FULLDESIGNDETAILS/`.
- `dist/portfolio-public/*` (the 8–32 KB landing pages from `build_portfolio_sites.py`) is a **secondary marketing
  landing layer**, NOT the product. When demoing/serving/tunneling, lead with the **built-out** surfaces + the app
  servers (`:8000/:8001/:8003`), not the landing sites.
- Any generator that writes a surface must NOT overwrite a richer hand-built/designed surface. If unsure which is
  richer, compare size + feature inventory first (`du -sh`, grep for login/dashboard/control-tower).

## 2. Reuse-first — do NOT build a new surface/engine when one exists (the highest-ROI rule)
Before building ANY new module, run the reuse check: `scripts/check_reinvention_guard.py`,
`scripts/codegraph.py --audit <area>`, `scripts/check_substrate_layers.py`. Search `src/teleon/**` for an existing
implementation. *"This already exists, don't rebuild it"* is the default. (Violated this session: a parallel
search stack `record_search/hybrid_search/scale_index` was built alongside the existing
`src/teleon/retrieval/search_port.py` + `synthesis/component_search.py` + `registry/port.py`.)

## 3. Port-first — implement against the agnostic ports, not parallel scripts
New capability code implements/extends the designed PORT (`record_store`, `retrieval/search_port`, `RegistryPort`,
execution-provider, LLM port), so backends swap by config. Do NOT write a parallel store/search on raw JSONL that
bypasses the port. (The scale work — sqlite incremental index, durable queue — must land BEHIND these ports.)

## 4. Proof-registration — every new seam is in the gate
Every new script/module with a `--self-test` MUST be registered in `scripts/flywheel_proof_modules.py` so
`run_proofs.py` runs it. A seam not in the gate is orphaned. (Violated: ~15 new scripts this session were not
registered.)

## 5. Move-not-delete + warrant (already law, restated)
Superseded code/docs are archived via `scripts/archive_legacy_docs.py` (never deleted, never untracked). Every
design/surface/strategy change carries a warrant (clear owner intent OR ≥2 sources OR a repo principle) per
`docs/codex/change-verification-contract.md` — NEVER a unilateral single-agent replacement of designed work.

## 6. Autonomous-loop guardrails (added)
- Loops NEVER `git reset --hard` the shared tree (use the isolated worktree). Loops touch only `data/dev-intel/`
  candidates, never `web/`, `templates/`, `dist/sites/`, or `architecture/*surface*`.
- Loops follow rules 1–4. A loop that would create a parallel surface/engine files a proposal instead.

Enforcement: a `check_surface_and_dev_contract.py` (TODO) asserts (a) the canonical surfaces exist + are non-empty,
(b) no loop commit touched `web/`/`dist/sites/`, (c) new `--self-test` scripts are registered. Until then, this
doc is the binding contract.
