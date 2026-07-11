# Parallel Paths & Path Tracking Operating Manual

How every pipeline step (scrape, build, test, benchmark, generate, search, verify, compile, deploy, repair) runs a
PORTFOLIO of interchangeable paths, tracks every attempt with receipts, and lets metrics — never a hardcoded choice
— decide the winner. Last reconciled 2026-07-02. Companion to `docs/OPERATIONS-BIBLE.md` and
`docs/handoff/primitive-generation-verification-and-upload-manual.md`.

**Principle (the non-commitment law):** no step commits to one way of doing its job. Each step declares an ordered
escalation ladder of paths; the engine runs baseline + challengers; the tracking ledger records which won, which
lost (preserved as training negatives), and why. "Unlimited paths per step" is literal — adding a path is one row.

---

## 1. The spine (already built — reuse it, do not rebuild)

| layer | canonical home | what it gives you |
| --- | --- | --- |
| **Path engine** | `src.teleon.experiments.parallel_paths.run_parallel(capability_slot, input_snapshot, baseline_path, candidate_paths, *, runner, now)` | runs a baseline + ANY number of candidate paths; returns the served output + per-path result; a candidate is NEVER served as truth |
| **Engine modes** | `SERVABLE_MODES=(baseline, fallback)`, `CHALLENGER_MODES=(candidate, shadow, canary, fallback)` | baseline=champion, candidate=challenger to serve, shadow=runs-but-not-served, canary=small live slice, fallback=escalation |
| **Promotion gate** | `src.teleon.experiments.path_promotion` (`PathPromotionDecision`) | a candidate is promoted ONLY through a passing decision; baseline is always the `rollback_target` |
| **Cost / compare / rollback** | `path_costing`, `path_comparator`, `path_rollback` | rank paths by cost/quality; revert safely |
| **Tracking ledger** | `src.teleon.evolution.descent_attempt_store.DescentAttempt(unit_id, strategy, before, after, outcome, losers, rollback_target, raw_ref, substrate_ref)` | append-only "brain": every attempt, losers kept as negatives, rollback preserved |
| **Path portfolio catalog** | `catalog/knowledge-packs/data/step-path-portfolios/` (builder `scripts/build_step_path_portfolio_pack.py`) | the machine-readable list of paths per step + receipt fields (this manual's companion pack) |
| **Redteam** | `scripts/check_parallel_path_redteam.py` | every attack fails safely |

Already wired to the engine/ledger: `src/teleon/hub_freshness.py` (scraper tool descent), `src/teleon/enrichment/search_enrich.py`, `src/teleon/extraction/document_extraction_cascade.py`, the benchmark-seeds pack. The work is EXTENDING this to the remaining factory scrapers/builders/testers, not inventing a new mechanism.

---

## 2. The step-path portfolio catalog (`step-path-portfolios` pack)

`catalog/knowledge-packs/data/step-path-portfolios/step_path_portfolios.jsonl` — one row per step, each with an
ordered `paths[]` (cheapest/most-deterministic first). 9 steps, 52 tracked paths today. Each path declares:

```text
path_id           a stable name (e.g. structured_api, deterministic_table_row, skill_behavior_test)
engine_mode       one of baseline|candidate|shadow|canary|fallback (single-sourced from the engine — never retyped)
escalation_order  0..n-1 (the ladder order)
when_wins         the condition under which this path is the right one
how_fails         its failure mode (why you escalate off it)
receipt_fields    what the tracking ledger records for this path
```

The nine steps and the shape of their ladders (see the pack for the full paths):

- **scrape**: cached_snapshot → structured_api → html_fetch_parse → headless_browser → stealth_browser → vision_extraction → human_review. *(escalate-before-unavailable: only climb when the cheaper path fails its receipt gate.)*
- **build**: deterministic_table_row → schema_driven_codegen → template_slot_fill → deterministic_remix → model_bounded_generation → source_fallback_codegen. *(generate only the missing edge.)*
- **test**: schema_gate → deterministic_fixture → contract_test → skill_behavior_test → differential_test → human_review. *(match rigor to risk.)*
- **benchmark**: paired_arm_run (A0..A8) → offline_replay → shadow_production → canary_slice → uplift_matrix (SLM-vs-SOTA). *(no claim is truth without adapter receipts.)*
- **search**: exact_edge → blocking_lexical → dense_vector → hybrid_rrf → graph_route → negative_memory_suppress → source_fallback.
- **verify_bridge**: registry_bridge_load → operational_load → dedupe_collapse. *(a primitive is not made until searchable.)*
- **compile**: deterministic_template_fill → typed_graph_lowering → grammar_constrained_gen → model_bounded_function → manual_approval_lock.
- **deploy_package**: dry_run_plan → oci_image_build → iac_module_emit → helm_operator_emit → marketplace_listing → human_approval_publish. *(receipts-first; outward publish is approval-gated.)*
- **repair**: read_failure_receipt → negative_memory_lookup → deterministic_mutator → alternate_route → context_ladder_escalate → model_micro_repair → gap_queue_new_primitive.

---

## 3. Add an unlimited number of paths to any step

Two moves, both cheap:

1. **Declare the path** — append a tuple to `STEPS['<step>']['paths']` in `scripts/build_step_path_portfolio_pack.py`
   (`path_id, engine_mode, when_wins, how_fails, extra_receipt_fields`) and run `--write`. The checker
   (`scripts/check_step_path_portfolio_pack.py --self-test`) enforces: mode is a real engine mode, exactly one
   baseline, ladder orders contiguous, refs resolve, boundary held. A brand-new STEP is a new key in `STEPS`.
2. **Wire the path to the engine** — implement a `Runner` branch that executes the path and pass it in
   `candidate_paths` to `run_parallel(...)`. The engine already accepts any number of candidates; you never touch
   engine code to add a path.

---

## 4. Track every path (the receipt ledger)

Every path execution records a receipt so nothing is a silent choice. Standard fields (`path_receipt_fields.jsonl`):

```text
step, path_id, engine_mode, input_hash, output_hash, outcome (improved|no_change|regressed|failed),
cost, latency_ms, tokens_in, tokens_out, source_read_depth, proof_status,
winner_reason, losers, rollback_target, negative_memory_ref
```

Write it via `DescentAttempt` (the append-only brain) — same call the hub-freshness scraper uses:

```python
from src.teleon.evolution.descent_attempt_store import DescentAttempt
brain.append(DescentAttempt(
    unit_id=f"{step}:{capability_slot}", strategy=path_id,
    before={...baseline metrics...}, after={...winning-path metrics...},
    outcome="improved" if won else "no_change",
    losers=tuple(other_path_ids), rollback_target="baseline",
    raw_ref="scripts/<the step's script>.py", substrate_ref=f"{step}:{path_id}"))
```

Losers are preserved as training negatives; the rollback target is always the baseline. This is what turns "we ran
a path" into "we know which path is best for this task family, with evidence."

---

## 5. Improve a scraper / builder / tester / benchmark (the recipe)

```text
1. Find its step in the portfolio pack; confirm the paths it SHOULD have vs the one it hardcodes today.
2. Refactor its single code path into a Runner with a branch per path_id.
3. Call run_parallel(baseline_path, candidate_paths, runner=...) instead of the one hardcoded call.
4. On each run, append a DescentAttempt receipt (§4).
5. Add any missing path to the portfolio pack (§3) so the catalog stays the source of truth.
6. Gate: the step's own check_*.py --self-test + check_step_path_portfolio_pack.py + check_parallel_path_full_stack.py.
```

Highest-leverage subsystems to wire next (currently single-path): the factory **scrapers/harvesters** (CKAN/Socrata/
ArcGIS/HRSA/NPPES ingesters — give them the scrape ladder), the **build lanes** (the Ollama/Fable/deterministic
generators — give them the build ladder so a lane that stalls escalates instead of failing), and the **testers**
(realize the declared `proof_requirements` as the test ladder). Each becomes a portfolio + receipts without new
engine code.

---

## 6. Definition of done for a path improvement

```text
[ ] the step's paths are in step-path-portfolios (build_step_path_portfolio_pack.py --write ; checker PASS)
[ ] the subsystem calls run_parallel with >=2 candidate paths (not a hardcoded single call)
[ ] every run appends a DescentAttempt receipt with losers + rollback_target
[ ] a candidate is served ONLY through a passing PathPromotionDecision (baseline = rollback_target)
[ ] check_parallel_path_full_stack.py --self-test still green
[ ] no path is promoted to truth without receipts ; every row candidate=true / serves_truth=false
```
