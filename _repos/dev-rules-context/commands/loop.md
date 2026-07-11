# /loop

Run the real-world primitive foundry loop.

Suggested proof commands:

```bash
python3 _repos/shared-backend-components/scripts/source_to_primitive_foundry.py --self-test
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --self-test
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --self-test
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --self-test
```

Deterministic JSON-hook operations:

```bash
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"actions.list"}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":16,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"mixed","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":8,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":6,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"large_org","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_cycle.run","args":{"seed_rows":100000,"rows_per_shard":10000,"compile_shards":2,"start_shard":-1,"benchmark_n":300,"benchmark_k":5,"paraphrase":true}}'
```

Suggested broad pass:

```bash
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --once --repo-root . --file-limit 0 --external-seed-count 1000 --max-components 5 --max-sources-per-partition 50
```

Suggested continuous scrape/decompose/feed pass:

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --once --source-limit 100 --question-count 240 --max-components 5 --max-sources-per-partition 25
```

Suggested deconstruction-plane definition pass:

```bash
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --run --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4
```

Suggested realistic session benchmarks:

```bash
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 16 --turns-per-session 0 --scenario-mode mixed --include-supervised --compare-base
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 8 --turns-per-session 0 --scenario-mode ml_lifecycle --include-supervised --compare-base
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 6 --turns-per-session 0 --scenario-mode large_org --include-supervised --compare-base
```

Continuous mode:

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --watch --interval 3600 --source-limit 500 --question-count 240 --max-ticks 0
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --watch --interval 3600 --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4 --max-ticks 0
```

Live scraping and LLM calls are opt-in and require source-policy review:

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --watch --live --use-llm --provider ollama --source-limit 500 --question-count 240 --interval 3600
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --run --use-llm --provider openwebui --mode cdp --llm-refine-limit 25
```

Expected output: repo-file and real-world source descriptors decomposed into
component breakdowns, rebuild plans, primitive candidates, variation candidates,
primitive graphs, examples, deconstruction planes/layers/dimensions/questions,
fully-defined primitive candidate rows, staged primitive database feed rows, and
receipts. Generated rows are candidates only and must keep `serves_truth=false`
until promotion. Raw source bodies are not stored; the loop persists handles,
digests, source-policy snapshots, generated decomposition rows, and proof
requirements.

Additional receipts now include realistic multi-prompt benchmark rows under
`_repos/shared-backend-components/data/dev-intel/realistic_session_benchmarks/`
and lifecycle/large-org specialized candidate cards under
`_repos/shared-backend-components/data/dev-intel/primitive_factory/specialized_packs/`.
