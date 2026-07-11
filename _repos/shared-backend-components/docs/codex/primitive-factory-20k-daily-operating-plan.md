# Primitive Factory 20k Daily Operating Plan

**Target:** 20,000+ usable primitive and primitive-group candidates per day.

Usable means accepted into the primitive database candidate layer with source
refs, visible input/output edges, proof obligations, dedupe keys, and
`candidate=true` / `serves_truth=false`. It does not mean 20,000 promoted truth
primitives per day.

## Current Position

The repo now has the minimum pieces needed for a high-throughput primitive
factory:

- 10 useful primitive-factory lanes in
  `catalog/knowledge-packs/data/primitive-factory-5k-lanes/lanes.jsonl`.
- 503 daily shard packets in
  `data/dev-intel/primitive_factory/daily_shards/2026-07-01/shards.jsonl`.
- 800 daily 20k-mode shard packets in
  `data/dev-intel/primitive_factory/daily_shards_20k/2026-07-01/shards.jsonl`.
- Open WebUI Gemma browser-context transport through Chrome DevTools Protocol.
- Ollama Cloud direct transport for `glm-5.2` and `kimi-k2.7-code`.
- Threaded coding benchmark with token-per-second accounting.
- Threaded primitive shard worker with token-per-second accounting.
- Multi-provider fleet planner that allocates disjoint provider windows:
  `scripts/plan_primitive_provider_fleet.py`.
- Candidate extractor that rejects rows missing required fields or truth
  boundary metadata.
- Partial-success batch handling: if some provider calls rate-limit, timeout,
  or use a wrong model id, successful model receipts are still extracted and
  failed receipts are written to `failed_model_outputs.jsonl`.
- Deterministic L3 verifier loop:
  `scripts/run_primitive_verification_loop.py --date 2026-07-01 --interval-seconds 45 --max-ticks 0`.
- Live dashboard:
  `python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --serve --port 9174`.
- Raw flywheel telemetry in the dashboard: call starts, finishes, active calls,
  retries, model-output receipts, model-output errors, recent raw results, and
  provider/model breakdowns.
- Source material telemetry in the dashboard: selected source rows, catalog JSONL
  rows, selected source files, and 20k shard counts.

Current live flywheel services:

```text
aidevobserver-primitive-fleet-glm-kimi-20260701.service
  -> GLM/Kimi generation loop, Gemma lane excluded while Open WebUI CDP is Cloudflare-blocked.

aidevobserver-primitive-verification-loop-20260701.service
  -> deterministic L3 candidate verifier loop.
```

Current 2026-07-01 live snapshot after verifier repairs:

```text
all_provider_accepted=4270
all_provider_total_tokens=1820798
raw_model_output_receipts=603
raw_model_output_errors=106
verified_l3=3827
source_rows_checked=5142
verified_ratio=0.744
selected_source_rows=74333
catalog_jsonl_rows=126625
daily_20k_shards=800
```

The source-material inventory is large enough for this phase. The active
bottlenecks are provider stability, row-shape quality, dedupe/verification
yield, and downstream L4 proof generation.

Observed Gemma CDP throughput:

| Workload | Workers | Unit Count | Errors | Completion TPS | Total TPS |
|---|---:|---:|---:|---:|---:|
| LeetCode prompts | 1 | 8 prompts | 0 | 144.761 | 168.717 |
| LeetCode prompts | 2 | 8 prompts | 0 | 234.804 | 274.968 |
| LeetCode prompts | 4 | 8 prompts | 0 | 248.216 | 292.546 |
| LeetCode prompts | 8 | 8 prompts | 0 | 230.488 | 271.339 |
| Primitive shards | 2 | 4 shards | 0 | 252.357 | 323.205 |
| Primitive shards | 4 | 8 shards | 0 | 246.319 | 311.909 |

The first extracted primitive run accepted 48 rows from 8 shards and rejected 2
rows for missing visible input/output edges. That is the right rejection shape:
bad model rows stay out of the candidate layer.

Observed high-ceiling primitive-factory provider evidence from 2026-07-01
manifests:

| Provider Lane | Batch Evidence | Accepted | Rejected | Accepted/Shards | Completion TPS | Total TPS | Accepted / 1k Total Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| Open WebUI `gemma-4-coding` CDP | `20k_openwebui_gemma-4-coding_cdp` | 30 | 0 | 10.000 | 214.864 | 264.918 | 4.520 |
| Ollama Cloud `glm-5.2` direct | `20k_ollama_glm-5-2_direct` | 99 | 10 | 14.143 | 208.330 | 225.769 | 3.017 |
| Ollama Cloud `kimi-k2.7-code` direct | `20k_ollama_kimi-k2-7-code_direct` | 35 | 0 | 17.500 | 152.202 | 155.416 | 0.981 |

Interpretation:

- Gemma is currently the cleanest efficient candidate writer per token.
- GLM is the best second high-yield lane and should also review contracts.
- Kimi produces many rows but spends more tokens; reserve it for long contract
  expansion, diversity passes, and critique unless backlog pressure warrants
  more candidate writing.

## Daily Quality Levels

Use levels so throughput is honest:

```text
L0 raw observation
L1 model draft row
L2 extracted schema-valid candidate row
L3 source-backed database candidate
L4 tested candidate with fixture/proof receipt
L5 promoted primitive
L6 preferred primitive group route
```

The daily 20k target should be:

```text
20,000 L2/L3 accepted database candidates/day
2,000 L4 proof-tested candidates/day
100-500 L5/L6 promoted or preferred rows/day
```

Trying to promote 20,000/day would dilute trust. The system should generate
aggressively, validate cheaply, review selectively, and promote slowly.

## Throughput Math

The current primitive run produced:

```text
48 accepted rows / 8 shards = 6 accepted rows per shard
12,540 total tokens / 48 accepted rows = 261 total tokens per accepted row
9,903 completion tokens / 48 accepted rows = 206 completion tokens per accepted row
```

At this observed density:

```text
20,000 accepted rows/day needs about 3,334 model shards/day
20,000 accepted rows/day needs about 5.2M total model tokens/day
```

The endpoint can theoretically supply far more than that if kept saturated, but
planning should use a large safety factor for browser session resets, malformed
rows, dedupe, source refreshes, and validator time.

Practical target:

```text
4,000 model shards/day
6 accepted rows/shard after extraction
24,000 accepted rows/day before dedupe
20,000 accepted rows/day after dedupe and rejection
```

To reduce model calls, improve prompt yield to 10 accepted rows per shard:

```text
2,400 model shards/day
10 accepted rows/shard after extraction
24,000 accepted rows/day before dedupe
20,000 accepted rows/day after dedupe and rejection
```

## Token Budget Rules

Keep most candidate-generation prompts small.

| Stage | Prompt Budget | Output Budget | Model Use |
|---|---:|---:|---|
| Shard candidate writing | 500-900 input tokens | high ceiling, default 65,536 | Gemma/Kimi/GLM |
| Group-card expansion | 700-1,200 input tokens | high ceiling, default 65,536 | Gemma/Kimi/GLM |
| Contract review | 400-900 input tokens | 600-1,200 output tokens | GLM/Gemma |
| Long contract expansion | 1,000-2,000 input tokens | high ceiling, default 65,536 | Gemma/Kimi/GLM |
| Code/test generation | 800-1,500 input tokens | 2,000-6,000 output tokens | Gemma/Codex |

Hard rules:

- Do not put the full brief in every prompt.
- Use prompt-version IDs instead of repeated policy prose.
- Give each shard 2-3 source refs, not the whole source map.
- Give base group IDs and visible edges, not full registry rows.
- Ask for JSONL only.
- Use the high-ceiling output budget by default. Small output caps are only for
  explicit smoke tests and should not be used for production primitive
  generation.
- Prefer 10 compact rows per shard over 1 verbose row.
- Expand contracts and proofs in a second pass only after extraction and dedupe.
- Store long schemas and proof details as artifact refs, not inline fields, until
  expansion is required.

## Context Budget Rules

Every layer needs a compact context representation:

```text
source_ref_card: source id, URL, authority, license/policy signal
lane_card: lane id, target, source ids, base group ids, rejection policy id
candidate_card: primitive id, visible edge, kind, source refs, proof blockers
group_card: visible edge, hidden member edge ids, blackbox, effects
proof_card: fixture ids, validators, pass/fail receipt
```

The model should usually see:

```text
system prompt version
one lane card
one shard card
2-3 source ref cards
2 base group cards
strict output schema
```

The model should not see:

```text
entire primitive database
entire source map
entire markdown brief
large raw API docs
previous daily outputs except compact dedupe hints
```

## Shard Strategy For 20k/day

The current 503 regular shards are enough for a 5k/day layer. The 20k mode
uses a separate shard set instead of overloading the 5k mode.

Current 20k config:

```text
daily_raw_candidate_target: 80,000
daily_useful_candidate_target: 20,000
daily_raw_candidate_target including lane rounding: 82,000
shard_useful_target: 25
daily_20k_shards: 800
```

Recommended lane expansion:

| Lane Family | Accepted/day |
|---|---:|
| OpenAPI operation groups | 2,500 |
| Schema/record import groups | 2,500 |
| Workflow automation templates | 2,000 |
| Package API surface groups | 2,000 |
| Public dataset ingest groups | 1,500 |
| Procurement/workforce/opportunity groups | 1,500 |
| Document extraction/export groups | 1,500 |
| Runtime wrappers and cloud jobs | 1,500 |
| CI/CD, repo, and DevOps groups | 1,500 |
| RAG, vector, and eval groups | 1,500 |
| Frontend/data app component groups | 1,000 |
| Safety, policy, memory, and audit groups | 1,000 |

The database should ingest accepted L2/L3 rows partitioned by day and lane.
Promotion should happen from a separate queue.

## Endpoint Use Plan

Use the provider fleet by role:

| Lane | Primary Role | Notes |
|---|---|---|
| Codex | Orchestrator, repo editor, deterministic validator | Owns patches, docs, schemas, extraction, and truth-boundary discipline. |
| Open WebUI Gemma | Efficient candidate writer and coding helper | Best observed accepted rows per token; use CDP when direct HTTP is blocked. |
| Ollama Cloud GLM | High-yield writer and contract/proof reviewer | Good direct lane; use for candidate generation and review passes. |
| Ollama Cloud Kimi | Long expansion and diversity review | Useful but verbose; use high ceiling and smaller windows. |

Plan disjoint provider windows before live calls:

```bash
python3 scripts/plan_primitive_provider_fleet.py \
  --date 2026-07-01 \
  --target-profile 20k \
  --scale 1
```

The planner writes a JSON plan and command file under:

```text
data/dev-intel/primitive_factory/fleet_runs/2026-07-01/
```

Use Gemma through Open WebUI for:

- high-volume candidate drafting;
- short coding/test generation;
- long primitive contract expansion after extraction;
- repair passes for rejected rows;
- fixture generation for proof gates.

Recommended worker defaults:

```text
short coding prompts: workers=4
primitive candidate shards: workers=2
long primitive expansion: workers=1 or workers=2
repair/retry passes: workers=2
```

Use CDP mode when Cloudflare blocks direct HTTP. If the Open WebUI browser has
a token but `/api/config`, `/api/models`, or `/api/chat/completions` return
Cloudflare HTML, exclude Gemma from the hot loop until the browser session is
refreshed:

```bash
python3 scripts/check_openwebui_gemma_endpoint.py --mode cdp --live
```

GLM/Kimi-only persistent loop:

```bash
systemd-run --user \
  --unit=aidevobserver-primitive-fleet-glm-kimi-20260701 \
  --working-directory=/home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing \
  python3 scripts/run_primitive_provider_fleet_loop.py \
    --date 2026-07-01 \
    --target-profile 20k \
    --scale 2 \
    --max-cycles 0 \
    --sleep-seconds 30 \
    --exclude-lane gemma_openwebui_cdp_candidate_writer
```

Verification loop:

```bash
systemd-run --user \
  --unit=aidevobserver-primitive-verification-loop-20260701 \
  --working-directory=/home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing \
  python3 scripts/run_primitive_verification_loop.py \
    --date 2026-07-01 \
    --interval-seconds 45 \
    --max-ticks 0
```

Run candidate generation in offset windows:

```bash
python3 scripts/run_primitive_factory_model_worker.py \
  --date 2026-07-01 \
  --provider openwebui \
  --mode cdp \
  --model gemma-4-coding \
  --offset 0 \
  --limit 100 \
  --workers 2 \
  --max-tokens 65536 \
  --timeout 240 \
  --out-dir data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_batch_000
```

Then extract:

```bash
python3 scripts/extract_primitive_model_candidates.py \
  --outputs data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_batch_000/model_outputs.jsonl \
  --out-dir data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_batch_000/extracted
```

Run many offset windows instead of one huge process. That makes retries cheap
and keeps browser/CDP failures isolated.

## Long Primitive Strategy

Long primitives should not be generated as one giant record in one pass.

Use a staged protocol:

```text
Pass 1: compact candidate skeleton
Pass 2: contract schema expansion
Pass 3: hidden member edge expansion
Pass 4: fixture and proof-plan generation
Pass 5: repair/review
```

Pass 1 output stays compact:

```json
{
  "primitive_id": "grp:...",
  "kind": "primitive_group",
  "input_edge": "...",
  "output_edge": "...",
  "hidden_member_edges": ["..."],
  "source_refs": ["..."],
  "proof_requirements": ["..."],
  "candidate": true,
  "serves_truth": false
}
```

Pass 2 expands only selected fields:

```json
{
  "primitive_id": "grp:...",
  "contract_schema": {...},
  "error_contract": {...},
  "artifact_refs": ["..."],
  "candidate": true,
  "serves_truth": false
}
```

Pass 3 expands only hidden routes:

```json
{
  "primitive_id": "grp:...",
  "hidden_member_edges": [
    {"edge_id": "...", "input_edge": "...", "output_edge": "..."}
  ],
  "route_hash": "...",
  "candidate": true,
  "serves_truth": false
}
```

This avoids feeding huge contracts back into every prompt. The database can join
the fragments by `primitive_id` and `source_output_id`.

## Validation Gates

A row cannot enter the candidate database unless it passes:

```text
json_parse_gate
candidate_boundary_gate
required_field_gate
visible_edge_gate
source_ref_gate
proof_requirement_gate
dedupe_key_gate
kind_gate
```

A row cannot become L3 unless it also passes:

```text
source_ref_resolution
source_authority_policy
license_policy_review
edge_contract_normalization
dedupe_cluster_check
group_hidden_edge_check
```

The verifier may perform deterministic candidate-shape repair before L3 gating:

```text
source_ref_alias_resolution_from_daily_shards
label_equals_url_source_ref_normalization
string_effect_wrapping
mutator_inference_with_promotion_blocker
proof_requirement_completion_with_promotion_blocker
group_contract_repair_from_top_level_hidden_edges
```

These repairs do not promote truth. They preserve `candidate=true` and
`serves_truth=false`, add normalization notes, and add promotion blockers when a
field is inferred.

A row cannot become L4 unless it passes:

```text
fixture_generation
schema_validation
golden_input_output_test
side_effect_receipt_test
error_case_test
runtime_profile_check
```

No row becomes `serves_truth=true` without a promotion receipt.

## Dedupe Strategy

Dedupe must run before expensive review.

Layered keys:

```text
primitive_id exact match
dedupe_key exact match
normalized visible edge hash
source_ref_id + input_edge + output_edge hash
group route hash
title + edge semantic cluster
proof plan similarity
```

Daily target accounting should distinguish:

```text
raw_model_rows
extracted_rows
schema_valid_rows
deduped_candidate_rows
source_backed_rows
reviewed_rows
tested_rows
promoted_rows
```

The 20k target should be measured at `deduped_candidate_rows` or
`source_backed_rows`, not raw model rows.

## Scheduler Design

Use small batch windows:

```text
batch size: plan with scripts/plan_primitive_provider_fleet.py
workers: 2 for current Gemma/GLM/Kimi primitive generation lanes
retry limit: 2
malformed-output repair: enabled
extract immediately after each batch
dedupe after each batch
ledger every batch
record partial failures as data, not command failure
```

Daily loop:

1. Build 20k shard plan.
2. Plan provider windows with `scripts/plan_primitive_provider_fleet.py`.
3. Run Gemma, GLM, and Kimi lanes from the plan in offset windows.
4. Extract model outputs.
5. Write `failed_model_outputs.jsonl` for bad model receipts and keep the
   successful receipts flowing.
6. Reject malformed and incomplete rows.
7. Dedupe accepted rows.
8. Run GLM/Gemma review on sampled and high-risk rows.
9. Generate proof tasks for accepted rows.
10. Write candidate database partitions.
11. Run L4 proof generation for top-ranked rows.
12. Produce daily throughput ledger and dashboard metrics.

## Metrics

Minimum daily metrics:

```text
model_provider
model
mode
worker_count
prompt_tokens
completion_tokens
total_tokens
completion_tps
total_tps
raw_model_rows
extracted_rows
accepted_rows
rejected_rows
duplicate_rows
source_backed_rows
group_ratio
average_hidden_edges_per_group
accepted_rows_per_1k_tokens
accepted_rows_per_shard
rejection_reason_counts
cost_or_token_budget_remaining
```

Useful efficiency metric from the first run:

```text
accepted_rows_per_1k_total_tokens = 48 / 12.540 = 3.83
```

To reach 20k/day at that efficiency:

```text
20,000 / 3.83 = about 5.22M total tokens/day
```

## Immediate Implementation Backlog

1. Add candidate database writer for verified L3 partitions.
2. Add dedupe ledger and route-hash generation beyond the verifier edge key.
3. Add rejection repair prompts for remaining missing source refs, missing
   effects, weak contracts, and groups with too few hidden member edges.
4. Add GLM review worker for high-risk candidate clusters.
5. Add long primitive expansion worker for selected group cards.
6. Add L4 fixture/proof generation for top-ranked L3 rows.
7. Add daily throughput dashboard Markdown summary.
8. Add direct bearer-token mode when a safe service-token path exists, keeping
   CDP as the fallback.
9. Add promotion queue that samples top candidates for tests and proof receipts.
10. Add provider-specific concurrency caps so Kimi uses lower concurrency and
    GLM can carry more hot-loop load.
11. Add automatic retry-queue consumption from `failed_model_outputs.jsonl`.
12. Add Gemma re-enable watchdog that probes CDP and launches Gemma lanes only
    after Cloudflare/API checks are healthy.

## Default Operating Recommendation

Run Gemma CDP in two modes:

```text
workers=2 for primitive candidate shards
workers=1-2 for long primitive expansion
workers=4 for coding/test generation
```

Treat 20,000/day as a database candidate ingestion target:

```text
candidate=true
serves_truth=false
source-backed
deduped
proof-planned
queryable by the AIDevObserver benchmark lab
```

Then let proof and promotion run slower. This gives AIDevObserver's benchmark
lab a large, usable primitive economy without weakening the truth boundary.

---

## Appendix — folded from Primitive Throughput Scale Plan (5k/day predecessor)

*Folded in 2026-07-03 from `primitive-throughput-scale-plan.md` (now archived). These are the sections this plan did not already carry: the factory scaling rule + proof gates, the machine-readable throughput/5k lane files and their checker, the high-volume lane table, the crisp verified/not-verified acceptance list, and the fast-candidate foundry-loop recipe. The Gemma worker and provider-fleet planner already live above in "Endpoint Use Plan"; the stale run snapshot stays in the archived predecessor.*

### Scaling Rule

Hand-authored primitives cannot reach 5,000/day.

The only realistic path is:

```text
verified factories -> parameterized primitive groups -> automatic proof receipts
```

A factory is verified once. Each emitted instance is verified only when its
parameters pass deterministic gates:

```text
source_evidence_gate
contract_schema_gate
deterministic_factory_gate
fixture_or_property_test_gate
candidate_boundary_gate
```

### Daily Capacity Plan

The machine-readable lane plan lives at:

```text
catalog/knowledge-packs/data/primitive-throughput-lanes/lanes.jsonl
```

It currently defines 12 lanes with planned capacity:

```text
20,000 verified primitive-group instances/day
```

Run:

```bash
python3 scripts/check_primitive_throughput_lanes.py
```

The checker validates:

- lane ids are unique;
- every lane declares source evidence;
- every lane declares a deterministic factory;
- every lane declares example group edges;
- every lane includes required proof gates;
- every lane preserves candidate/truth boundary language;
- planned capacity reaches the 20k/day stretch target.

### Lane Strategy

The throughput comes from high-volume families:

| Lane | Target/day |
|---|---:|
| Schema/record import groups | 2,500 |
| OpenAPI CRUD/policy groups | 2,500 |
| Workflow template groups | 2,000 |
| Package API surface groups | 2,000 |
| CI/CD and DevOps groups | 1,500 |
| K8s/cloud runtime groups | 1,500 |
| Public dataset ingest groups | 1,500 |
| Procurement/workforce groups | 1,000 |
| Document extraction groups | 1,500 |
| RAG/embedding/eval groups | 1,500 |
| Frontend component groups | 1,500 |
| Safety hook/memory groups | 1,000 |

### What Counts

Counts as verified:

- source-backed group card;
- visible input/output edge;
- hidden member edges;
- deterministic factory or implementation;
- passing generated fixture/property test;
- declared effects, cache/memory, runtime targets;
- candidate-only boundary preserved.

Does not count:

- raw search seed;
- source URL only;
- untested generated code;
- synthetic primitive with no source;
- edge card with no proof path;
- any row claiming `serves_truth=true` without promotion.

### Useful 5k/day Execution Layer

The practical daily target is now split into two machine-readable layers:

```text
catalog/knowledge-packs/data/primitive-factory-5k-lanes/lanes.jsonl
data/dev-intel/primitive_factory/daily_shards/<run-date>/shards.jsonl
```

The lane file defines useful accepted output, not raw volume. A row counts only
after source refs, visible edge contracts, hidden member edges or a single-step
contract, proof plan, dedupe key, and candidate boundary pass.

Run:

```bash
python3 scripts/check_primitive_factory_5k_lanes.py
python3 scripts/build_primitive_factory_5k_shards.py --date 2026-06-30
```

The shard builder creates parallel work packets. Each packet carries:

- raw and useful candidate targets;
- source refs and base primitive-group examples;
- Kimi candidate-writer prompt;
- GLM contract-reviewer prompt;
- deterministic validators and proof gates;
- `candidate=true` / `serves_truth=false` boundary.

Recommended execution split:

```text
Codex: orchestrate repo edits, run checkers, write accepted artifacts.
Kimi: draft candidate primitive/group JSONL for each shard.
GLM: review edge clarity, hidden member edges, proof gates, and duplicates.
Deterministic scripts: reject schema failures, missing source refs, weak edges, missing proof plans, and truth-boundary violations.
```

This keeps throughput parallel while preserving the promotion rule: models can
generate and critique candidates, but promotion requires deterministic proof and
review receipts.

### Fast Candidate Mode

Use fast candidate mode when the goal is generating more primitive candidates
and shard packets quickly, not refreshing every lifecycle/search/proof artifact
on every tick.

```bash
python3 scripts/global_primitive_foundry_loop.py \
  --fast-candidate-mode \
  --use-case-limit 50 \
  --surface-limit 1 \
  --microsurface-limit 1 \
  --local-repo-limit 1 \
  --search-scope-limit 1 \
  --naics-scope-limit 1 \
  --business-operation-scope-limit 1 \
  --skip-multilingual-search-scopes
```

Fast mode automatically:

- builds the 5k/day factory shard plan;
- uses the smaller fast shard target from `scripts/_config.py`;
- regenerates and checks the AIDevObserver benchmark-lab 10k task corpus;
- uses that corpus as public use-case seeds;
- skips lifecycle packaging, route fixtures, route verification, and runtime
  coverage for that tick.

For continuous operation, run candidate generation frequently and refresh the
heavier packaging/proof artifacts on a slower cadence:

```bash
python3 scripts/global_primitive_foundry_loop.py \
  --watch \
  --build-5k-shards \
  --build-aidevexplorer-task-corpus \
  --use-aidevexplorer-task-corpus \
  --shard-useful-target 10 \
  --lifecycle-every 6 \
  --route-fixture-every 6 \
  --route-verifier-every 12 \
  --runtime-coverage-every 12
```

This preserves the boundary:

```text
candidate=true
serves_truth=false
```

The fast path increases candidate throughput. It does not promote primitives
or replace proof gates.
