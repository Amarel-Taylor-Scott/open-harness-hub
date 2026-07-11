# Primitive Loop JSON Hook

Use this hook when an LLM needs to run the primitive foundry loops through a
deterministic, receipt-backed interface instead of arbitrary shell commands.

Runner:

```bash
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py \
  --request-json '{"action":"actions.list"}'
```

Request schema:

```text
_repos/shared-backend-components/schemas/primitive_loop_hook_request.schema.json
```

Rules:

- Only call allowlisted `action` names returned by `actions.list`.
- Use `dry_run: true` first for live/model actions.
- Do not pass shell fragments; the hook ignores shell strings and builds fixed
  `argv` arrays with `shell=false`.
- Generated rows are candidates only: `candidate=true`, `serves_truth=false`.
- Every call writes `request.json`, `response.json`, and a ledger row under:

```text
_repos/shared-backend-components/data/dev-intel/primitive_loop_json_hook/
```

Useful requests:

```json
{"action":"actions.list"}
```

```json
{"action":"status.snapshot","args":{"include_services":false}}
```

```json
{"action":"flywheel.run","args":{"iterations":1,"mode":"full","max_child_actions":10,"execute_live_model":false,"input_context_tokens":262144,"output_context_tokens":65536,"max_token_ceiling":65536}}
```

```json
{"action":"gemma_long.once","dry_run":true,"args":{"limit":1,"lane_dry_run":true}}
```

```json
{"action":"token_savings.run_small","args":{"n":100,"k":5,"seed":7,"intent_mode":"paraphrase"}}
```

```json
{"action":"session_benchmarks.run","args":{"sessions":12,"k":8,"components_per_turn":4,"scenario_mode":"mixed"}}
```

```json
{"action":"session_benchmarks.run","args":{"sessions":8,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle"}}
```

```json
{"action":"session_benchmarks.run","args":{"sessions":6,"k":8,"components_per_turn":4,"scenario_mode":"large_org"}}
```

```json
{"action":"billion_plan.run"}
```

```json
{"action":"twenty_million_goal.run","args":{"target":20000000,"horizon_days":60,"daily_working_target":100000,"daily_candidate_target":400000}}
```

```json
{"action":"twenty_million_cycle.run","args":{"seed_rows":100000,"compile_shards":2,"benchmark_n":300}}
```
