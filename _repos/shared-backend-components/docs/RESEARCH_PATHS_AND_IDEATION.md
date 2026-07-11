# Research Paths & Ideation — token savings from a deterministic primitive database (2026-07-09)

> Companion to `HANDOFF-GPT-5.6.md`. A catalog of testable paths to prove and MAXIMIZE token savings, grounded in
> this session's executed findings and the harnesses already in `_repos/shared-backend-components/scripts/`. Each
> path: hypothesis · how to test · why it matters. `candidate=true / serves_truth=false`.

**Session findings this builds on:** (a) single-shot OUTPUT savings on common code are marginal; (b) "use this
primitive" prompt-injection often triggers re-implementation — but this is PROMPT- and MODEL-dependent
(`full_source_asis` "use as-is" works where `signatures_only` fails); (c) deterministic composition (manager emits
thin wiring, mounts verified module verbatim) passes hidden oracles at **0 model tokens** — the reliable floor;
(d) realistic senior-dev sessions are **INPUT-token-dominated** (growing conversation + re-read files re-sent every
turn) — the biggest, barely-explored lever; (e) **partial composition** (DB covers what it can, exposes typed edges,
LLM fills only the gap) is the most realistic model.

## ★ Top 8 by expected value (do these first)
1. **#22 Input/output token accounting harness** — meter the real split before optimizing anything (foundational).
2. **#20 Compact verified reference vs raw re-read** — the core input-token lever; attacks finding (d) directly.
3. **#33 Partial composition w/ typed-edge exposure + LLM gap-fill** — operationalizes (e), the realistic product model.
4. **#31 Deterministic-composition coverage scaling** — grow the template/edge registry so the 0-token floor covers more.
5. **#1 "Full tested source + use-as-is" presentation matrix** — cheapest high-signal test; turns (b) into a tuned knob.
6. **#25 Multi-turn session replay on a LARGE real codebase** — where millions–billions of input tokens actually live.
7. **#15 Retrieval precision@k, oracle-ceiling gated** — retrieval quality caps every downstream mechanism.
8. **#42 reimplementation_rate as first-class regression-tracked metric** — make the (b) failure mode a ratcheting KPI.

**Sequencing:** build #22 + #42 first (they instrument everything). Then #25 to escape toy-task regime. Then attack
the two biggest levers in parallel — input-token (#20, #23, #27) and composition coverage (#31, #33). Every lane
should carry the held-out-oracle guard (#34) and report `input_output_split · cost_per_pass · coverage_fraction ·
reimplementation_rate`. Route every candidate primitive through the two-axis lift×durability gate (#46).

## A. Prompt / presentation strategies for reuse
- **#1★ Presentation-format matrix** — verbatim-mount rate is dominated by HOW a primitive is shown; sweep ≥8 variants (signature-only → full source+test → import-stub → tool-call) through `real_buildout_ab_harness.py`; metric `reimplementation_rate`, `cost_per_pass`. One template change can flip reuse net-positive at zero infra cost.
- **#2 Import-stub-only** — bodies live behind a frozen import surface (never in context); compare pass-rate + tokens. The strongest presentation is no presentation — collapses input AND output tokens.
- **#3 Anti-primitive steering** — show a known-bad re-implementation (via `anti_primitive_store.py`) next to the verified one; measure reimplementation_rate drop on HMAC/idempotency tasks.
- **#4 Authority framing sweep** — "certified, hidden-oracle-passing, changing it fails CI" vs neutral; isolate a free lever, see how much models defer to stated verification.
- **#5 Contract-first vs code-first ordering** — lead with typed edges+contract then source; metric `edge_type_match_rate`.

## B. Model diversity
- **#6 Frontier vs code-specialist vs small-local mount-behavior map** — `model_lane_bakeoff.py`; reimplementation_rate × pass-rate × cost_per_pass by model class (small/local may mount more willingly).
- **#7 SLM-uplift on the covered portion** — mounting primitives lets a small model match a frontier model on the DB-covered fraction (`measured_lift_headtohead.py`). The DB as capability equalizer — a core economic claim.
- **#8 Cross-model amortization** — a primitive verified once serves N models; compute break-even reuse count. Justifies the factory; the moat is the verified asset.
- **#9 Model-invariance of the deterministic floor** — confirm compose passes at 0 tokens across all model lanes. Separates the guaranteed floor from the probabilistic reuse upside (honest pricing).

## C. Task-family diversity (beyond small HTTP services)
- **#10 Task-family × input:output-ratio census** — per-family token accounting (extends `task_layer_stack_framework.py` 28-role matrix); high input-dominance = biggest lever → targets the roadmap.
- **#11★ Refactor on a LARGE existing codebase** — refactors re-send big files across many turns (input 10–100×); inject compact verified digests of touched modules; highest-token real scenario, least explored.
- **#12 Bug-fix-from-failing-test** — oracle is the provided failing test (free verification); DB fix primitives cut `turns_to_pass`. Cleanest credible demo.
- **#13 Framework/library migration (A→B)** — capability-gap sweet spot (models get target-API wrong); measure pass-rate lift + reimplementation_rate. Structural durable lift.
- **#14 Data/ETL pipeline assembly** — highly compositional (read→normalize→dedupe→load); partial composition covers most, LLM fills schema transform; best-case for the 0-token floor.
- **#16 Infra-as-code (Terraform/K8s/CI YAML)** — template-dominated + typed params → possibly highest `coverage_fraction` of any family → strongest floor story.
- **#17 Auth/billing/webhook subsystems** — HMAC/idempotency/retry/Stripe: where models fail silently and the DB wins most; adversarial oracles (replay/dup/skew). The correctness-not-just-cost wedge.

## D. The input-token / context-engineering lever (the underexplored frontier)
- **#18 Re-read multiplier** — `re_read_multiplier = total_content_bytes_sent / unique_content_bytes`; a single number that quantifies the waste the DB removes (headline metric for the input thesis).
- **#19 Stable-prefix / prompt-cache economics** — verbatim-mount at a STABLE position → prompt-cache-eligible → those tokens cost ~10% across turns. Reframes verified primitives as *cheaper* tokens, not just *fewer* — a multiplicative axis.
- **#20★ Compact capability-card context vs raw file re-read** — replace re-read bodies with a card (name+typed edges+contract+hash+1-line behavior); metric `input_token_reduction` at held-constant pass-rate. Mechanizes finding (d).
- **#21 Context ladder (tiered compression sweep)** — full file → module digest → capability card → edge signature; plot pass-rate vs input tokens; find the knee (extends `context_lift_matrix.py`).
- **#22★ Input/output token accounting harness** — extend `run_realistic_session_benchmarks.py`/`agentic_session_savings_bench.py` to emit per-turn+cumulative input/output/cache-read/cache-write. Build FIRST; every other claim depends on it.
- **#23 Differential / delta context** — send only the diff since last turn + a stable digest of the rest; cuts input tokens with no pass-rate loss; stacks with capability cards.
- **#24 Re-derivation elimination** — inject a once-computed verified digest so the model stops re-deriving the same understanding each turn; measure the output-token drop (repair/re-derivation is "the token sink").
- **#25★ Multi-turn session replay on a real large codebase** — replay consented Claude Code logs DB-on vs DB-off; the credibility anchor for any pricing claim (converts thesis from synthetic to evidence).
- **#26 Cache-eligible-fraction analyzer** — classify per-turn context bytes stable vs changed; sizes the theoretical ceiling of the lever.
- **#27★-adj Frozen-substrate call surface** — expose all verified modules as a named typed call surface (MCP `capability_compose`) so bodies never enter context. The architectural end-state: DB as runtime, not context payload.

## E. Retrieval / routing of the right primitive per subtask
- **#15★ Retrieval precision@k, oracle-ceiling gated** — score `primitive_retrieval_bakeoff.py` against the oracle-best primitive (TinyRouter/TRINITY gate); a wrong retrieval poisons both reuse and composition.
- **#28 Decomposition-granularity sweep** — `query_decomposer.py` at several grains; maximize coverage_fraction × retrieval precision (find the right reuse unit — molecule/subsystem vs leaf).
- **#29 Intent-semantic vs lexical vs hybrid index** — `check_primitive_hybrid_search.py`; precision@k on held-out subtask→primitive labels; index design moves the savings ceiling.
- **#30 Compiled-route cache hit-rate over a session** — `compiled_route_store.py`; caching turns one-time composition into permanent 0-token reuse (the flywheel's compounding term).

## F. Verification / oracle strengthening
- **#31★ Deterministic-composition coverage scaling** — track `coverage_fraction` on a fixed suite as the template/edge registry grows (`validate_compose.py`/`check_registry_compose.py`); scales the one 0-token-proven mechanism.
- **#32 Mutation testing on the oracle** — mutate the verified primitive; require the oracle to catch it; report kill-rate. Prevents shipping primitives that "pass" only because the test is blind (protects trust).
- **#33★ Partial composition w/ typed-edge exposure + LLM gap-fill** — `hybrid_composer.py` end-to-end; metrics coverage_fraction, edge_type_match_rate, gap-fill tokens, oracle pass; the realistic architecture to optimize hardest.
- **#34 Hidden held-out oracle discipline** — enforce train/grade split everywhere (leakage guard); leakage is the #1 way these numbers lie.
- **#35 Adversarial oracle packs** — replay/duplicate/malformed/clock-skew per capability-gap primitive; value is correctness under adversity, invisible to happy-path oracles.

## G. Deterministic-composition scaling
- **#36 Edge-typed auto-wiring at scale** — verify every seam's `input_edge`/`output_edge` types match across N-primitive chains; auto-wire success vs chain length. What lets composition scale past hand-built templates.
- **#37 Template-registry growth loop** — `saas_buildout_decomposer.py` mines primitives FROM oracle-tested code; measure verified-templates/day + coverage contribution (the supply side of the flywheel).
- **#38 Config-driven thin-wiring generalization** — expand the config→wiring generator to ETL/IaC; fraction fully-declarative vs LLM-fill (more declarative = larger guaranteed floor).
- **#39 Composition depth vs reliability curve** — pass-rate vs chain depth; where composition must hand off to gap-fill.
- **#40 Compose-route as an MCP capability** — `capability_compose` over MCP; tokens saved per call + pass-rate of returned compositions (benchmark → callable product).

## H. Agent-instruction-compiler product direction
- **#41 Repo-guidance → enforced hooks/CI/policy compiler** — A/B prose-only vs compiled-hooks agent lanes; reimplementation_rate, turns_to_pass, session tokens. Sells "your agent follows your rules + reuses your verified code" as enforced, not suggested (this session's `agent_instruction_compiler.py`).
- **#41b Reinvention-guard live hook** — non-blocking PreToolUse "this exists as verified primitive X" (`find-reuse`); measure wrote-new vs adopted + token delta. Highest-ROI decision, measured at point of action.
- **#42★ reimplementation_rate as product telemetry** — per model/presentation/family time series; alert on regression; correlate with presentation+model. Can't improve reuse without owning this number.

## I. Metrics that matter
- **#43 cost_per_pass north-star** — $-weighted total tokens per hidden-oracle-passing solution; headline field in all receipts (prevents output-only cherry-picking).
- **#44 session_token_total vs single-shot** — report both; the 10–100× ratio corrects the framing that makes the DB look weak.
- **#45 executor_certified_per_MTok** — verified oracle-passing executors per MTok (`harness_bakeoff_spec.py`); keeps the factory honest about *verified* output, not raw rows.
- **#46 Two-axis lift×durability dashboard** — score every primitive via `durable_gap_harness.py`+`reason_codes.py`; prune transient wins; enforces the capability-gap admission law.

## J. Adversarial / failure-mode probes
- **#47 Stale-primitive silent-pass** — inject drift (dep bump/API change); check the oracle catches it; require digest+`verified_at` staleness gating. Stale reuse is worse than none (confidently wrong).
- **#48 Cross-cutting-concern reachability limit** — thread one concern (auth/logging/tracing) through N modules; where composition breaks + gap-fill takes over → reveals the next primitive shape (aspect primitives).
- **#49 "Model insists on re-implementing" as a gap signal** — classify refused mounts (presentation-fixable vs no-lift vs primitive-wrong); feed `gap_screen.py`. Turns the failure into feedback.
- **#50 Composition-vs-reuse interference** — hybrid lane pass-rate vs pure-composition/pure-generation; find families where edge-typing must be enforced harder.

## K. Economics / productization
- **#51 Pricing on % of MEASURED savings** — auditable meter (on #22/#43/#44) → per-customer savings receipt (held-out-oracle verified) → dry-run the invoice math. The monetization model depends on a meter customers trust.
- **#52 MCP delivery end-to-end** — agent with `primitive_search`+`capability_compose`+`find_reuse` vs without, real IDE loop; session_token_total, cost_per_pass, turns_to_pass. The shipping product is the MCP runtime.
- **#53 Private-repo scanning wedge** — mine a customer's repo (`saas_buildout_decomposer.py`) → offer their OWN primitives back; models defer to "your team's certified code" (sidesteps the rewrite problem). Defensible GTM wedge.
- **#54 Break-even / amortization P&L per primitive** — combine verification cost (#8) + per-use savings (#43); rank by realized ROI; focus the factory on the high-reuse head (depth-before-breadth).

## L. Cross-session learning & ground truth
- **#55 Consented-session corpus → primitive-demand ranking** — mine consented logs for recurring re-derived sub-solutions (consent = gate #0); rank by frequency×token-cost; feed `research_queue.py`. Aims the factory at demonstrated demand.
- **#56 Longitudinal flywheel** — fix a benchmark cohort; re-measure cost_per_pass + coverage_fraction across DB snapshots over weeks; proves the flywheel compounds vs plateaus (the investment thesis).
