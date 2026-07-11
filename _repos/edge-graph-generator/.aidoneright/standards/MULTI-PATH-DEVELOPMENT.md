# Multi-Path Development

> **Portable standard.** Applies to any AI Done Right project. The reference implementation is the
> `ai_harness_and_knowledge_facts_and_logic_website_sharing` repository; every mechanism below is grounded
> in a file you can read there (paths cited inline).

## Thesis (owner framing)

> "Instead of making decisions on how to do something, build out all possible and reasonable paths and
> then benchmark and choose and fallback."

A design choice — which canonicalizer, which retriever, which embedder, which compose strategy — is not a
line of code you argue about and hardwire. It is a **portfolio of contract-substitutable paths** that
compete on the same input, measured by receipts, with a disclosed winner and the losers kept as
fallbacks. You do not decide; you enumerate, race, and let the receipts decide — then re-race to re-adapt.

---

## 1. The Non-Commitment Law

**Never hardwire one strategy where several are viable. A decision point is a PORTFOLIO of
contract-substitutable paths, not an `if`.**

- Wherever code would branch on a design opinion ("use lexical search", "cast then rename", "promote on
  pass"), express that point as a **named set of paths sharing one uniform contract**, selected by a
  configurable key — not a hardcoded call.
- The current production behavior is **one selectable path among the set** (`ACTIVE_DEFAULT`), never the
  only path. Selecting the default must reproduce today's behavior *exactly* — so adopting the portfolio
  replaces nothing.
- Adding a strategy is a **new row + a resolver entry**, never a rewrite. Removing a strategy is deleting
  a row, not unpicking an `if`.

Reference implementation — `scripts/primitive_paths_config.py` makes five runtime decision points
(`edge_canonicalizer`, `search_method`, `composer`, `reranker`, `proof_policy`) into portfolios: **15
paths across 5 decision points, 12 wired, behind ONE selector**, plus 5 tunable parameters. Its module
docstring states the law directly: *"every runtime decision point is a PORTFOLIO of contract-substitutable
paths … not an `if` baked into the code."* `ACTIVE_DEFAULT` (lines 111–119) "reproduces TODAY's behavior —
selecting it replaces nothing."

The same law at the infrastructure layer — `scripts/build_retrieval_backend_portfolio.py` (docstring):
after a red-team found four disjoint embedding dimensions, *"The fix is NOT 'hardcode one embedder' — it
is a PORTFOLIO with a single active default and a hard dim-compatibility rule … New backends are rows
here; flipping the active default is one field; everything else plugs in."*

---

## 2. Vocabulary (use these words)

| Term | Meaning | Reference |
| --- | --- | --- |
| **Decision point** | A place where several reasonable strategies exist. Holds a list of paths. | `DECISION_POINTS` — `scripts/primitive_paths_config.py:53` |
| **Path** | One named strategy at a decision point, satisfying that point's uniform contract. | path rows, same file |
| **Portfolio** | The full set of paths at a decision point. | — |
| **Uniform contract** | The single call signature every path at a decision point must satisfy, so any path is substitutable for any other. | docstring, `scripts/primitive_paths_config.py:16` |
| **`ACTIVE_DEFAULT`** | The one path per decision point that runs in production today. Reproduces current behavior exactly. | `scripts/primitive_paths_config.py:111` |
| **Fallback** | Any non-default path in the portfolio, kept live and selectable. | — |
| **Status** | `wired` (runs today) · `optional` (runs if a dep/daemon is present) · `planned` (declared, not built). The active default MUST be `wired`. | `scripts/build_retrieval_backend_portfolio.py:14` |
| **Receipt** | The recorded, hashable evidence of a run or a choice — never an opinion. | `DecisionReceipt` (`decision_receipt`, `scripts/primitive_paths_config.py:176`); `ParallelPathRun` (below) |

---

## 3. The Lifecycle

Run every decision point through these seven steps. Each maps to a real module in the reference repo.

1. **Enumerate all reasonable paths.** List every strategy a competent engineer might defend — including
   the current one and the "old" one you plan to replace. Keep the foil in the race; a path that wins
   nothing is a *result*, not waste.
   *Ref: `DECISION_POINTS` enumerates 3–4 paths per decision point, including legacy `linear_lexical`
   kept "not deleted" (`scripts/primitive_paths_config.py:65`).*

2. **Implement each behind ONE uniform contract.** Every path at a decision point takes the same inputs
   and returns the same shape, so the selector can swap them blind. A new path only has to satisfy the
   contract to plug in.
   *Ref: the five contracts (`CANONICALIZE`/`SEARCH`/`COMPOSE`/`RERANK`/`PROOF_POLICY`) declared at
   `scripts/primitive_paths_config.py:16`; resolvers return contract-shaped callables (`search_path`,
   `composer`, `reranker`, …).*

3. **Benchmark them on the SAME input via `run_parallel` (receipts, not opinion).** Execute the baseline
   and every candidate on one identical input snapshot; record a per-path receipt (output, cost,
   latency, error, contract-validation, source-handle coverage). Never compare a strategy on inputs it
   got to choose.
   *Ref: `src/teleon/experiments/parallel_paths.py` — see §4.*

4. **Choose an `ACTIVE_DEFAULT` by MEASURED receipts.** The winner is picked from the recorded metrics
   (cost + accuracy/composability + budget), with the ranking **disclosed, never silent**. Match the
   selection bar to the blast radius (§6 guardrail).
   *Ref: `_aggregate_class` ranks by measured `mean_composability`, then `contract_pass_rate`, then
   `median_tokens`, then `p50_latency_ms`, then path id — `scripts/run_path_bakeoff.py:679`.*

5. **Keep the rest as FALLBACKS with `wired|optional|planned` status.** Losers stay in the portfolio,
   selectable and honestly labelled. A per-task router returns the winner **plus ordered fallbacks** — a
   portfolio decision, never a lock-in.
   *Ref: `select_path` returns `{winner, fallbacks, ranked_path_ids}` and routes unknown inputs to a safe
   deterministic baseline — `scripts/path_selection_policy.py:355`.*

6. **Adding a new path is DATA (a new row), never a rewrite.** Extend the portfolio by appending a row and
   a resolver entry. The graph, the router, and the benchmark pick it up automatically.
   *Ref: adding an embedder/index/reranker/search-method = one tuple in `EMBEDDERS`/`INDEXES`/… —
   `scripts/build_retrieval_backend_portfolio.py:35`.*

7. **Re-benchmark to re-adapt.** When a model ships, a corpus grows, or a cost changes, re-run the
   bake-off; the routing table (and every future decision) updates automatically. "Find what makes the
   most sense" is durable *and* adaptive, not a one-time verdict.
   *Ref: `scripts/path_selection_policy.py` docstring — "As the bake-off re-runs, the routing table … updates automatically".*

---

## 4. The fair comparator — `run_parallel`

`src/teleon/experiments/parallel_paths.py::run_parallel` is the engine that makes step 3 trustworthy. It
is the non-negotiable center of this standard.

**What it guarantees:**

- **Identical input, provable.** It computes `input_snapshot_hash = sha256(canonical_bytes(input))` and
  feeds the same snapshot to the baseline and every candidate. Each per-path receipt carries that hash —
  the proof every path saw the same input (`run_parallel`, lines 113–140). A runner that *attests* it ran
  on a different hash is **refused at the input**, never inferred from output divergence (`_result_record`,
  lines 80–86).
- **Per-path receipts, not opinions.** Each path records `output`, `output_contract`, `cost`,
  `latency_ms`, `error`, `source_handle_coverage` (vs the baseline's grounding set), `contract_validation`,
  and `source_handles` (lines 87–100).
- **A candidate is NEVER served as truth.** `served_path_id` is *always* the baseline's id and
  `candidate_served` is *always* `False` (lines 170–173). `served_output()` structurally returns the
  baseline result — there is no code path that returns a candidate's output to a consumer (lines 183–189).
  Candidate outputs live only in `candidate_results` for the comparator to judge.
- **Modes are enum-bounded.** The served result must be a servable mode (`SERVABLE_MODES = ("baseline",
  "fallback")`); a challenger carries a challenger mode (`"candidate", "shadow", "canary", "fallback"`)
  (lines 37–41). The schema enforces it.
- **Pure and deterministic.** Execution is delegated to a caller-supplied `runner`; `now` is injected; ids
  are content hashes. No wall-clock, RNG, or network in the engine.

This is the line that separates measurement from wishful thinking: **you may race any strategy, but the
race can never promote a candidate.** Promotion is a separate, warranted decision (§6).

---

## 5. The bake-off and the routing table (worked machinery)

Two modules turn `run_parallel` into a repeatable decision procedure:

- **`scripts/run_path_bakeoff.py`** — races N strategies on a task set through `run_parallel`, then
  aggregates a **per-task-class leaderboard**. The winner per class is the highest measured composability
  *within a token/latency budget* (`TOKEN_BUDGET`/`LATENCY_BUDGET_MS = 400`), ties broken by
  contract-pass-rate, then fewer tokens, then latency, then id (`_aggregate_class`, line 679). Its
  headline finding: *"different task-classes elect different winners — no single path dominates."* Every
  emitted row is `candidate=true / serves_truth=false`.
- **`scripts/path_selection_policy.py`** — reads the leaderboard and derives a routing table
  `{task_class → ranked_path_ids}`. `select_path(task_features)` classifies a task and returns the
  winner **plus ordered fallbacks** (a portfolio, never a lock-in), records the decision to a ledger, and
  routes anything unclassifiable to the **safe deterministic baseline**. It re-derives automatically when
  the bake-off re-runs, and falls back to a clearly-labelled synthetic table when no leaderboard exists.

---

## 6. The guardrail — the benchmark that chooses must itself be trustworthy

A portfolio is only as honest as the benchmark that ranks it. **No self-graded metrics; no unmeasured
claims.** Before you trust a winner, verify the verifier.

**Checklist — the race is admissible only if:**

- [ ] **The judge is shared and canonical across all paths** — every path is scored by the *same*
      independent scorer, regardless of how it built its result. *Ref: `judge_route` in
      `scripts/run_path_bakeoff.py:410` is "the shared, canonical, fair scorer applied to EVERY path's
      route regardless of how it was built."*
- [ ] **No path grades itself.** A path never reports its own success metric; the comparator does. A
      candidate's output is data for the judge, never a truth claim (`candidate_served = False`).
- [ ] **Every path proved it ran on the same input** — the `input_snapshot_hash` matches; a divergent
      attestation is refused (`parallel_paths.py:80`).
- [ ] **The metrics are measured, not asserted** — cost/latency come from work done, contract-validation
      from an executed check, "proven" from an executed proof — never a hand-set flag. *Ref: `PROVEN` is
      computed by the real executed-proof runner — `scripts/run_path_bakeoff.py:311`.*
- [ ] **The ranking is disclosed** — the winner, the full order, and any non-wired selections are written
      down. *Ref: `decision_receipt` discloses `non_wired_selected` and a deterministic `config_hash` —
      `scripts/primitive_paths_config.py:176`.*
- [ ] **The choice carries a warrant proportional to blast radius.** "It's green" is necessary, not
      sufficient. Changing the `ACTIVE_DEFAULT` for a design/strategy-bearing decision needs clear intent
      or ≥2 independent agreeing sources, not a unilateral single-agent call.

See the companion standards: **`VERIFY-THE-VERIFIER.md`** (how to prove a scorer is trustworthy) and
`docs/codex/change-verification-contract.md` in the reference repo (warrant-before-change; "It's green is
necessary, not sufficient").

---

## 7. Worked example — the "how do we retrieve/compose?" decision point

A concrete pass through the full lifecycle, using real values from the reference repo's on-disk leaderboard
(`data/dev-intel/path_bakeoff/`).

**Step 1 — Enumerate the portfolio.** How do we turn a task intent into a composed primitive route? Five
reasonable strategies:

| Path | Strategy | Role |
| --- | --- | --- |
| `P0` | `deterministic_table_row` — zero-token pre-baked lookup (solved head only) | baseline |
| `P1` | `lexical_search` — old registry path: token overlap + RAW-string edge chaining | candidate (foil) |
| `P2` | `edge_typed_compose` — retrieval + chaining on CANONICAL edge types | candidate |
| `P3` | `hybrid_rrf` — dense+lexical fusion, surfaces what lexical-only misses | candidate |
| `P4` | `llm_assisted_peelback` — peel deeper layers only when a shallow compose stalls (costly) | candidate |

**Step 2 — One uniform contract.** Every path is a `run_parallel`-compatible runner:
`runner(path, input_snapshot) → {output, cost, latency_ms, error, source_handles, contract_validation}`
(`make_runner`, `scripts/run_path_bakeoff.py:589`). P0 is the baseline (a servable mode); P1–P4 are
candidates.

**Step 3 — Race on the same input.** For each of ~24 tasks across 5 task-classes,
`run_parallel(baseline=P0, candidates=[P1..P4])` runs all five on the identical `input_snapshot`, pins one
`input_snapshot_hash`, and records five receipts. No candidate is served.

**Step 4 — Choose the `ACTIVE_DEFAULT` per class, by measured receipts.** The leaderboard elects different
winners per class — the whole point:

| Task class | Winner | Measured cost | Runner-up fallbacks (ordered) |
| --- | --- | --- | --- |
| `string_transform` | **`P0`** deterministic_table_row | 0 tok / 1 ms | P2, P3, P4, P1 |
| `data_pipeline` | **`P2`** edge_typed_compose | 54 tok / 21 ms | P3, P4, P1, P0 |
| `algorithm` | **`P3`** hybrid_rrf | 70 tok / 29 ms | P4, P2, P1, P0 |
| `extraction` | **`P4`** llm_assisted_peelback | 246 tok / 110 ms | P3, P2, P1, P0 |
| `agentic` | **`P2`** edge_typed_compose | 54 tok / 21 ms | P3, P4, P1, P0 |
| `unknown` | **`P0`** (safe baseline) | 0 tok / 1 ms | P2, P3, P4, P1 |

The finding: **no single path dominates.** The cheap deterministic table wins the solved head; typed
compose wins the mid-complexity pipelines; fusion wins algorithms; the expensive peel-back is only worth
its 246 tokens where nothing shallower reaches. `P1` (the old raw-string chaining) **wins nothing** — a
measured foil, exactly what keeping it in the race is for.

**Step 5 — Keep the rest as fallbacks.** Each class carries an ordered fallback list; `select_path`
returns winner + fallbacks so a runtime failure or budget change degrades gracefully to the next-best
measured path, and an unclassifiable task routes to the safe deterministic baseline.

**Step 6 — Adding P5 is data.** A new strategy (say a learned cross-encoder rerank) is a row in the path
metadata + a strategy entry; the bake-off and router pick it up with no rewrite.

**Step 7 — Re-benchmark to re-adapt.** When a cheaper embedder or a stronger model ships, re-run the
bake-off; if `P4`'s peel-back is no longer worth 246 tokens for `extraction`, the routing table demotes it
automatically. The decision stays live.

**Guardrail applied here.** Every path was scored by the one shared `judge_route`; "proven" came from an
executed proof, not a flag; all five saw the same `input_snapshot_hash`; the leaderboard is
`candidate=true / serves_truth=false`; promoting any winner to a production default is a separate,
warranted change.

---

## 8. Adoption checklist

- [ ] Name the decision point and enumerate every reasonable path — include the incumbent and the foil.
- [ ] Define ONE uniform contract for the point; make each path satisfy it.
- [ ] Mark each path `wired` / `optional` / `planned`; the `ACTIVE_DEFAULT` must be `wired` and must
      reproduce current behavior exactly.
- [ ] Race the portfolio on identical input through `run_parallel` (or the same guarantees); never let a
      path run on inputs it chose.
- [ ] Rank by measured receipts (cost + accuracy/composability + budget); disclose the full order.
- [ ] Emit a `DecisionReceipt` (resolved config + hash + non-wired disclosure); mark it
      `candidate=true / serves_truth=false`.
- [ ] Return winner **plus ordered fallbacks**; route the unclassifiable to a safe deterministic baseline.
- [ ] Verify the verifier before trusting the winner (§6); carry a warrant proportional to blast radius.
- [ ] Add new paths as rows; re-benchmark on model/corpus/cost change so the choice re-adapts.

---

## Sources cited (reference implementation)

- `src/teleon/experiments/parallel_paths.py` — `run_parallel`: baseline + candidates on identical input;
  per-path receipts; `input_snapshot_hash` proof; candidate is never served (`served_path_id`/`served_output`).
- `scripts/primitive_paths_config.py` — 15 paths / 5 decision points / 12 wired behind one selector; the
  five uniform contracts; `ACTIVE_DEFAULT` reproduces current behavior; tunable `PARAMETERS`;
  `decision_receipt` (`DecisionReceipt`); `PathNotWired` for planned paths.
- `scripts/run_path_bakeoff.py` — races P0–P4 on ~24 tasks / 5 classes through `run_parallel`; shared
  `judge_route`; per-class winner by measured metrics within budget; "no single path dominates"; P1 foil.
- `scripts/path_selection_policy.py` — leaderboard → routing table; `select_path` returns winner + ordered
  fallbacks (portfolio, never lock-in); safe baseline for unknown; re-derives when the bake-off re-runs.
- `scripts/build_retrieval_backend_portfolio.py` — `wired|optional|planned` statuses; single-source
  `ACTIVE_DEFAULT` per kind; "the fix is a PORTFOLIO, not one hardcoded backend"; active default must be wired.
- `data/dev-intel/path_bakeoff/bakeoff_leaderboard_2026-07-03.json` + `data/dev-intel/path_selection_policy/routing_table.md`
  — the on-disk leaderboard and routing table used for the worked example's real per-class winners.
- `docs/codex/change-verification-contract.md` — warrant-before-change; "It's green is necessary, not
  sufficient"; ≥2 independent agreeing sources for design-bearing changes.
- Companion standard: `_repos/dev-rules-context/standards/VERIFY-THE-VERIFIER.md`.
