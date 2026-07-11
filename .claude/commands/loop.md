---
description: Run the real-world primitive foundry loop across repo files, Kaggle/LeetCode-style tasks, apps, papers, websites, and discussions
---

Adopt the **real-world primitive foundry operator** role and begin immediately.

Purpose: build new reusable primitives from real developer surfaces and real-world
problem shapes, not from abstract brainstorming. Treat every generated row as
candidate-only until promotion gates prove it.

## Hard Rules

- Do not store raw source bodies in generated primitive rows.
- Do not promote generated primitives directly. Keep `candidate=true` and `serves_truth=false`.
- Prefer source-backed decomposition: source object -> component breakdown -> rebuild plan -> primitive candidate -> variation candidate -> proof receipt.
- Use existing registries and primitives before generating new ones.
- Report hard gaps honestly, especially algorithm, competitive-programming, Kaggle, SWE-bench, WebArena/OSWorld, and agentic workflow gaps.
- If live network, credentials, or paid APIs are unavailable, use metadata descriptors, write the exact connector gap, and continue.

## Run This Loop

1. Orient from `AGENTS.md`, `README.md`, `_repos/_shared/taxonomy/SPEC.md`, and `_repos/shared-backend-components/docs/codex/baltor-always-in-memory-context.md`.
2. Run the hermetic proofs:

```bash
python3 _repos/shared-backend-components/scripts/source_to_primitive_foundry.py --self-test
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --self-test
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --self-test
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --self-test
```

3. Prefer deterministic JSON-hook calls for benchmark, 20M-cycle, and scheduler-friendly operations:

```bash
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"actions.list"}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":16,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"mixed","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":8,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":6,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"large_org","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_cycle.run","args":{"seed_rows":100000,"rows_per_shard":10000,"compile_shards":2,"start_shard":-1,"benchmark_n":300,"benchmark_k":5,"paraphrase":true}}'
```

4. Run one broad repo/source-to-primitive pass:

```bash
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --once --repo-root . --file-limit 0 --external-seed-count 1000 --max-components 5 --max-sources-per-partition 50
```

5. Run the governed continuous scrape/decompose/feed loop. Offline mode uses
metadata descriptors and synthetic real-world seeds. Live scraping and LLM calls
are opt-in so source policy, ToS, credentials, and rate limits stay explicit.

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --once --source-limit 100 --question-count 240 --max-components 5 --max-sources-per-partition 25
```

6. Run the deconstruction-plane definition pipeline. This builds the persistent
database of planes, layers, dimensions, question rows, question edges, and
definition-completeness rubric, then materializes fully-defined primitive
candidate records from the latest continuous-loop run.

```bash
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --run --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4
```

For continuous operation:

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --watch --interval 3600 --source-limit 500 --question-count 240 --max-ticks 0
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --watch --interval 3600 --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4 --max-ticks 0
```

Only after operator review, credentials, and source-policy approval:

```bash
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --watch --live --use-llm --provider ollama --source-limit 500 --question-count 240 --interval 3600
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --run --use-llm --provider openwebui --mode cdp --llm-refine-limit 25
```

7. Run focused evidence checks when time allows:

```bash
python3 _repos/shared-backend-components/scripts/run_primitive_consumption_benchmark.py --run --limit 10 --date 2026-07-07
python3 _repos/shared-backend-components/scripts/bench_composition_system.py --run --corpus 34123 --input-sample 4000 --target-sample 150 --token-sample 500
python3 _repos/shared-backend-components/scripts/run_token_savings_experiments.py --run --n 3000 --k 5 --seed 7 --intent-mode paraphrase
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 16 --turns-per-session 0 --scenario-mode mixed --include-supervised --compare-base
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 8 --turns-per-session 0 --scenario-mode ml_lifecycle --include-supervised --compare-base
python3 _repos/shared-backend-components/scripts/run_realistic_session_benchmarks.py --run --sessions 6 --turns-per-session 0 --scenario-mode large_org --include-supervised --compare-base
```

8. Read the receipts under:

- `_repos/shared-backend-components/data/dev-intel/source_to_primitive_foundry/real_world_loop/`
- `_repos/shared-backend-components/data/dev-intel/continuous_primitive_scrape_loop/`
- `_repos/shared-backend-components/data/dev-intel/primitive_deconstruction_plane_pipeline/`
- `_repos/shared-backend-components/catalog/knowledge-packs/data/primitive-deconstruction-plane-database/`
- `_repos/shared-backend-components/data/dev-intel/session_emulation/`
- `_repos/shared-backend-components/data/dev-intel/token_savings_experiments/`
- `_repos/shared-backend-components/data/dev-intel/primitive_lift_benchmark/`
- `_repos/shared-backend-components/data/dev-intel/realistic_session_benchmarks/`
- `_repos/shared-backend-components/data/dev-intel/primitive_factory/specialized_packs/`

## Loop Phases

`ORIENT -> INVENTORY -> SOURCE-SCAN -> DECOMPOSE -> REBUILD-PLAN -> GENERATE-CANDIDATES -> REMIX -> BENCHMARK -> GAP-QUEUE -> RECORD -> REPEAT`

Source families to cover every pass:

- repo files and code systems
- web pages and websites
- apps and workflow products
- Kaggle competitions, datasets, and notebooks
- news and product-release feeds
- Medium/blog articles and system-design writeups
- textbooks, course material, Google Scholar/citation clusters, and paper publication pages
- LeetCode/interview and competitive-programming problems
- papers and technical reports
- discussions, issues, forums, and Q&A

Output expected every pass:

- governed source queue and source-policy snapshots
- 200+ question bank over languages, design systems, architectures, tests, security, observability, cost, remix axes, and promotion gates
- persistent deconstruction planes, analysis layers, dimensions, question database, and completeness rubric
- question-answer/decomposition rows
- component breakdowns
- candidate rebuild plans
- primitive graphs
- primitive examples
- primitive database feed rows
- fully-defined primitive candidate rows with examples, graph refs, visible edges, proof requirements, benchmark hooks, promotion blockers, and `serves_truth=false`
- primitive candidates
- primitive variation candidates
- coverage and token proxy receipt
- explicit hard-gap list

$ARGUMENTS
