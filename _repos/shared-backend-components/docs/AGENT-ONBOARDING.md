# Agent Onboarding — any system opening this repo

> System-agnostic entry point for **any** agent/model working here (Claude Code · **Claude Fable** · Codex/GPT-5.6 ·
> Cursor · Aider · Cline · MCP clients). Read the file for YOUR system, then the current-state + laws below. This repo
> is `_repos/shared-backend-components` (the substrate) inside the `_repos/`-migrated monorepo. Everything the
> substrate returns is `serves_truth=false` — pointers and shapes, never truth.

## 1. Read the file for your system first

| System | Read first | Then |
|---|---|---|
| **Claude Code / Claude Fable** | root `CLAUDE.md` + `_repos/shared-backend-components/CLAUDE.md` (the "Active handoff → GPT-5.6 (2026-07-09)" block is current) | `docs/HANDOFF-GPT-5.6.md`, `docs/CLEANUP-BACKLOG.md` |
| **Codex / GPT-5.6** | `_repos/dev-rules-context/FOR_CODEX.MD` (the review brief; its 2026-07-09 banner is current) | `docs/HANDOFF-GPT-5.6.md`, `docs/RESEARCH_PATHS_AND_IDEATION.md` |
| **Cursor / Aider / Cline / other coding agents** | this file + root `CLAUDE.md` | `docs/SYSTEM-OVERVIEW.md` for the whole picture |
| **MCP clients** | the MCP tool schemas (`capability-retrieval`, `baltor-context-gateway`, `teleon-capability-gateway`, `aidevobserver`) | `docs/INTEGRATION-BIBLE.md` (seams) |

**The one health command:** `PYTHONPATH=. python3 scripts/run_proofs.py` (runs every `--self-test`; 1,051 modules
registered). If a module you touch isn't in `scripts/flywheel_proof_modules.py`, register it.

## 2. Current state (2026-07-09) — the reconciled truth, do not overwrite with older framing

The active workstream is **executed token-savings experiments** (does the primitive DB save tokens on real coding
tasks?). Definitive so far, at real sample size (6-model grid, n≈56/lane, MIN_N=8):
- **Deterministic composition** (`compose` lane) is the only robust **0-token, 1.0-pass** win — model-independent.
- **Prompt-based reuse is PROMPT- and MODEL-dependent:** `full_source_asis` ("show the full tested module + use
  as-is") reaches ~0.625 pass at ~108 out-tok ≈ `without` (0.614 pass @ 1374 out-tok) → **~13× fewer output tokens
  when the presentation is right**. `signatures_only`/edges-only makes models **re-implement and FAIL** (~0.09).
- **Realistic sessions are INPUT-token-dominated** — compact capability-cards vs raw file re-reads cut ~**87% of
  input** on a 50-turn session (`input_token_lever.py`); this is where session-scale ("billions") savings live.
- **Partial composition** (DB covers portions + exposes typed edges + LLM fills the gap, `edge_exposed_gapfill.py`)
  is the realistic product model.
- **Do NOT re-assert** "47.5%", "4.7-5.9×", "486×", or "1.17M primitives" as proven token savings — those are
  projection / context-byte reduction / raw-count. Honest ledger: `docs/REAL_SAVINGS_NUMBERS.md`.

## 3. The laws you inherit (do not weaken; full text `_repos/dev-rules-context/standards/`)
1. **Multi-path** — a design choice is a portfolio of contract-substitutable paths behind one selector, raced by
   receipts; never hardwire one strategy.
2. **Globally-unique naming** — code = `py_<kind>__<file>__<scope>__<name>` (pyprefix); data ids = `canonical_id`
   only; version in metadata, never a name/id.
3. **Candidate/truth boundary** — born `candidate=true, serves_truth=false`; generation ≠ promotion; keep the six
   funnel counts distinct.
4. **Change verification** — every change carries a warrant (user-intent / corroboration / principle) matched to blast
   radius; design/brand/strategy is never a unilateral single-agent call.
5. **Verify the verifier** — mutation gate + determinism gate + quality ratchet on every checker.
6. **No magic values** — repo-state numbers computed, never typed; one definition, many readers.
7. **Lossless distillation** — distillation is never replacement; preserve raw + lineage + rollback.
8. **Archival** — move never delete; never untrack; status-labeled under `archive/legacy/`.

## 4. How to be productive here
- **Reuse-first.** Before building anything, check it doesn't exist: `src/teleon/registry/reinvention_guard.py`,
  `scripts/check_substrate_layers.py`, `scripts/codegraph.py --audit <target>`. *"This already exists, don't rebuild
  it"* is the highest-ROI decision.
- **Fast path, not full rebuilds:** `validate.py <changed paths>` → `build_component_id_index.py --update` →
  `build_catalog_pages.py --paths` → `run_proofs`. Full gates only on schema/vocabulary/broad-ref changes.
- **Codegraph before + after** editing a `.py`: `PYTHONPATH=. python3 scripts/codegraph.py --audit <file|symbol>` —
  update load-bearing neighbors in the SAME change.
- **New decision point = a portfolio, not an `if`. New id = one `canonical_id` call. New frontend↔backend = a
  service-plane service + a seam + `fetch('/api/<x>/...')`, never a static stub over a rich app.**
- **Every serious turn improves at least one durable thing.** If one path is blocked, switch paths — don't stop.

## 5. What to work on now → `docs/CLEANUP-BACKLOG.md`
Prioritized: **P0** untrack the 68 GB of generated data from git (55,606 tracked files, `.git`=2.6 GB) · **P1** the
JSONL→Postgres/pgvector/warehouse migration · **P2** finish the doc reconciliation · **P3** complete the reuse grid +
wire the partial-composition + realistic-session lanes · **P4** code/context hygiene. Confirm before any git-history
rewrite / force-push.

## 6. Document map (which doc for what)
- **`SYSTEM-OVERVIEW.md`** — the whole system (surfaces · architecture · primitive DB · infra/data-tier · savings ·
  hosting/Fly.io · costs · laws). Start here for the big picture.
- **`HANDOFF-GPT-5.6.md`** — the experiment workstream detail + open threads.
- **`RESEARCH_PATHS_AND_IDEATION.md`** — 56 ranked paths to test.
- **`CLEANUP-BACKLOG.md`** — what to clean up, P0→P4.
- **`REAL_SAVINGS_NUMBERS.md`** — the honest savings ledger.
- **`BIBLE.md`** — the north star (wins over everything if they disagree). **`INTEGRATION-BIBLE.md`** — frontend↔backend
  + local/cloud. **`DESIGN-BIBLE.md`** — the design system. **`strategy/primitive-system-end-to-end-briefing.md`** §4
  — the sober savings reconciliation other docs defer to.
