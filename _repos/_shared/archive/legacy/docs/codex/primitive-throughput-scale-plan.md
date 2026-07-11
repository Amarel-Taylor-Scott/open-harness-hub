# Primitive Throughput Scale Plan

**Target:** 5,000 to 20,000 reusable, verified primitive or primitive-group candidates per day.

For the current 20,000/day operating model, including token budgets, context
rules, long primitive generation, and Open WebUI Gemma worker settings, see
[`primitive-factory-20k-daily-operating-plan.md`](primitive-factory-20k-daily-operating-plan.md).

## Current Reality

The current local state is structurally correct but not yet scaled:

```text
Current verified curated groups: 4
Generated candidate edge cards: 72,192
Fully promoted serves_truth=true primitives: 0
```

The generated edge cards are useful search candidates, but they do not count as
fully verified working primitives. A verified primitive or group must have an
implementation or deterministic factory, a source-backed contract, proof gates,
and candidate/truth boundary metadata.

## Scaling Rule

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

## Daily Capacity Plan

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

## Lane Strategy

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

## What Counts

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

## Next Implementation Step

Build one factory lane at a time.

Recommended order:

1. Schema/record import factory.
2. OpenAPI operation group factory.
3. Workflow template group factory.
4. Dataset ingest group factory.
5. Runtime wrapper factory.

Each factory must emit:

```text
group card JSONL
fixture file
proof receipt
registry search card
throughput ledger row
```

The north-star metric is not raw rows/day. It is:

```text
verified_group_instances_per_day
```

The second metric is:

```text
average_hidden_edges_per_group
```

This keeps the system focused on reducing LLM context, not inflating primitive
counts.

## Useful 5k/day Execution Layer

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

## Fast Candidate Mode

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

## Open WebUI Gemma Worker

The primitive factory can use the Open WebUI-hosted Gemma coding model as the
current efficient high-throughput candidate writer. Kimi and GLM stay in the
fleet, but the role assignment should follow measured output, not old labels:

```text
Codex: orchestration, repo edits, deterministic validation, docs, handoff
Gemma via Open WebUI: efficient candidate writer and coding helper
GLM via Ollama Cloud: high-yield candidate writer plus contract/proof reviewer
Kimi via Ollama Cloud: long expansion, diversity review, and critique
```

Configure direct mode through environment variables when a safe bearer-token
path exists:

```bash
export OPENWEBUI_BASE_URL="https://ui.iamretarded.net"
export OPENWEBUI_MODEL="gemma-4-coding"
export OPENWEBUI_TOKEN="<redacted bearer token>"
```

Check offline wiring:

```bash
python3 scripts/check_openwebui_gemma_endpoint.py
```

Run a live direct smoke only when `OPENWEBUI_TOKEN` is configured:

```bash
python3 scripts/check_openwebui_gemma_endpoint.py --live
```

For the browser-context path, start Chrome with DevTools enabled and log in
through the isolated profile. The wrapper keeps cookies, Cloudflare clearance,
and the Open WebUI token inside the browser context.

```bash
google-chrome \
  --user-data-dir=/tmp/aidevobserver-gemma-profile \
  --profile-directory=Default \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --remote-allow-origins='*' \
  --no-first-run \
  --disable-first-run-ui \
  --no-default-browser-check \
  --disable-gpu \
  --disable-dev-shm-usage \
  --no-sandbox \
  --new-window https://ui.iamretarded.net
```

Then smoke-test browser-context mode:

```bash
python3 scripts/check_openwebui_gemma_endpoint.py \
  --mode cdp \
  --live \
  --prompt "Print exactly: Open WebUI browser-context integration OK"
```

Run LeetCode-style throughput checks:

```bash
python3 scripts/run_gemma_coding_benchmark.py \
  --mode cdp \
  --limit 8 \
  --workers 4 \
  --max-tokens 65536 \
  --out generated/gemma_leetcode_coding_benchmark_w4.json
```

Observed quick sweep on 2026-07-01:

| Workers | Tasks | Errors | Completion TPS | Total TPS |
|---:|---:|---:|---:|---:|
| 1 | 8 | 0 | 144.761 | 168.717 |
| 2 | 8 | 0 | 234.804 | 274.968 |
| 4 | 8 | 0 | 248.216 | 292.546 |
| 8 | 8 | 0 | 230.488 | 271.339 |

The local knee for short coding prompts was 2-4 workers. Eight workers stayed
error-free but underperformed four workers.

Dry-run shard scheduling without model calls:

```bash
python3 scripts/run_primitive_factory_model_worker.py \
  --provider openwebui \
  --model gemma-4-coding \
  --limit 25 \
  --workers 8 \
  --dry-run
```

Run live Gemma shard generation after a shard plan exists:

```bash
python3 scripts/run_primitive_factory_model_worker.py \
  --provider openwebui \
  --model gemma-4-coding \
  --limit 25 \
  --workers 8
```

For browser-context mode, use `--mode cdp`:

```bash
python3 scripts/run_primitive_factory_model_worker.py \
  --date 2026-07-01 \
  --provider openwebui \
  --mode cdp \
  --model gemma-4-coding \
  --limit 8 \
  --workers 4 \
  --max-tokens 65536 \
  --timeout 240 \
  --out-dir data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_w4_tps
```

Observed primitive-worker run on 2026-07-01:

| Workers | Shards | Errors | Completion Tokens | Completion TPS | Total TPS |
|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 0 | 4,684 | 252.357 | 323.205 |
| 4 | 8 | 0 | 9,903 | 246.319 | 311.909 |

For longer primitive prompts, two workers was slightly faster in this sample.
Use 2 as the measured default and 4 when backlog latency matters more than
peak token efficiency. Keep the default output budget high-ceiling
(`--max-tokens 65536`) for primitive generation; small caps are only for
explicit smoke tests.

Extract model text into candidate-only JSONL before any registry use:

```bash
python3 scripts/extract_primitive_model_candidates.py \
  --outputs data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_w4_tps/model_outputs.jsonl \
  --out-dir data/dev-intel/primitive_factory/model_outputs/2026-07-01/openwebui_gemma_cdp_w4_tps/extracted
```

The extractor rejects rows missing required fields such as visible input and
output edges, and all extracted rows remain `candidate=true` and
`serves_truth=false`.

Or fold it into a fast global tick:

```bash
python3 scripts/global_primitive_foundry_loop.py \
  --fast-candidate-mode \
  --run-gemma-shard-worker \
  --gemma-shard-limit 25 \
  --gemma-workers 8
```

For scheduler testing without live calls:

```bash
python3 scripts/global_primitive_foundry_loop.py \
  --fast-candidate-mode \
  --run-gemma-shard-worker \
  --gemma-worker-dry-run \
  --gemma-shard-limit 25
```

Model outputs land as candidate-only receipts under:

```text
data/dev-intel/primitive_factory/model_outputs/<date>/openwebui/
```

Do not commit bearer tokens, cookies, browser storage dumps, or password
material. Browser-context mode is an operational transport that keeps session
secrets in Chrome, not in repo artifacts.

## Multi-Provider Fleet Planning

Use the provider-fleet planner before running live batches so Gemma, GLM, and
Kimi consume disjoint shard windows:

```bash
python3 scripts/plan_primitive_provider_fleet.py \
  --date 2026-07-01 \
  --target-profile 20k \
  --scale 1
```

The planner reads existing batch ledgers under
`data/dev-intel/primitive_factory/batch_runs/<date>/`, writes a plan and shell
command file under `data/dev-intel/primitive_factory/fleet_runs/<date>/`, and
keeps every planned lane `candidate=true` / `serves_truth=false`.
