# Primitive Model Scheduler

Candidate-only operating schedule for primitive discovery, decomposition,
generation, benchmark, and agentic improvement lanes.

All lanes write receipts with `serves_truth=false`. Generated outputs are
candidate artifacts until a separate promotion gate accepts them.

## Active Runtime Timers

These user-level `systemd-run` timers are active on this machine.

| Unit | Cadence | First delay | Lane |
|---|---:|---:|---|
| `primitive-loop-json-flywheel.timer` | 30 min | 30 min | Full primitive flywheel: source collect, deconstruction, token-savings benchmark, Gemma lane supervision |
| `primitive-20m-goal-plan.timer` | 360 min | 90 min | Refresh the 20M advanced generator control plane |
| `primitive-20m-supervised-cycle.timer` | 120 min | 75 min | Supervised 20M cycle: deterministic seed slice, shard verification, card packaging, before/after token-savings benchmark |
| `primitive-realistic-session-benchmark.timer` | 180 min | 95 min | Multi-prompt app, warehouse, agent, compliance, and platform-session token-savings benchmark |
| `primitive-ml-lifecycle-session-benchmark.timer` | 180 min | 115 min | Production ML lifecycle benchmark across product, data, modeling, serving, reliability, security, governance, and support roles |
| `primitive-large-org-session-benchmark.timer` | 180 min | 135 min | Google-scale organization benchmark across business units, platforms, infra, AI, trust, GTM, and governance |
| `primitive-ollama-local-gemma4-smoke.timer` | 60 min | 60 min | Local Ollama `gemma4:latest` smoke receipt |
| `primitive-ollama-compat.timer` | 60 min | 61 min | Shared LLM plane Ollama/free-limited compatibility proof |
| `primitive-context-foundry.timer` | 60 min | 70 min | AIDevObserver context/session/source foundry tick |
| `primitive-multimodel-improvement.timer` | 120 min | 120 min | Kimi + GLM improvement sweep over architecture, modules, and research targets |
| `primitive-shard-builder-20k.timer` | 24 hr | 24 hr | Build the next 20k primitive factory shard file |
| `primitive-provider-fleet-ollama.timer` | 180 min after first run | 24 hr | Ollama Cloud provider fleet with GLM + Kimi lanes |
| `primitive-codex-gap.timer` | 360 min | 60 min | One bounded Codex north-star gap closure cycle |

## Active Continuous Services

These services are also running under the user systemd manager. They use their
own `--watch` loops rather than external timers.

| Unit | Internal cadence | Lane |
|---|---:|---|
| `primitive-live-source-collector.service` | 30 min | Live source scrape from `data/research-queue/seed_sources.jsonl`, source limit 20, question count 720 |
| `primitive-deconstruction-live-loop.service` | 30 min | Deconstruction plane pipeline, question count 720, atlas limit 250, overlays per primitive 48 |
| `primitive-gemma-long-multistep-loop.service` | 15 min | Open WebUI `gemma-4-coding` long multistep primitive generation |

## Max Budgets

- Open WebUI Gemma lane: `--max-tokens 65536`, `--timeout 600`,
  `--min-hidden-edges 10`, `--min-examples 4`.
- Primitive JSON flywheel context policy:
  `input_context_tokens=262144`, `output_context_tokens=65536`,
  `max_token_ceiling=65536`, `auto_reduce_on_issue=true`.
- Provider fleet GLM/Kimi lanes: `--max-tokens 65536`.
- 20M goal plan:
  `target_working_primitives=20000000`, `daily_working_target=100000`,
  `daily_candidate_target=400000`, `horizon_days=60`.
- 20M supervised cycle:
  `seed_rows=100000`, `rows_per_shard=10000`, `compile_shards=2`,
  `start_shard=-1` (auto next unused), `benchmark_n=300`,
  `benchmark_k=5`, `paraphrase=true`.
- Realistic session benchmark:
  `sessions=16`, `turns_per_session=0`, `k=8`,
  `components_per_turn=4`, `context_window=262144`,
  `compare_base=true`, `include_supervised=true`.
- ML lifecycle session benchmark:
  `sessions=8`, `turns_per_session=0`, `k=8`,
  `components_per_turn=4`, `scenario_mode=ml_lifecycle`,
  `context_window=262144`, `compare_base=true`,
  `include_supervised=true`.
- Large-organization session benchmark:
  `sessions=6`, `turns_per_session=0`, `k=8`,
  `components_per_turn=4`, `scenario_mode=large_org`,
  `context_window=262144`, `compare_base=true`,
  `include_supervised=true`.

## Temporary Provider Pause

Ollama Cloud returned `429 weekly usage limit` on 2026-07-07. The scheduler
recorded `_repos/shared-backend-components/data/dev-intel/primitive_factory/OLLAMA_PAUSE.json`
with `expires_at_utc=2026-07-08T22:05:30Z`. The multimodel improvement timer
now records `ollama_usage_pause_active` rows instead of burning long timeouts.
The provider-fleet timer is deferred for 24 hours. Local Ollama and Open WebUI
Gemma lanes remain active.

## Verification Commands

```bash
systemctl --user list-timers 'primitive-*' --all
systemctl --user status primitive-loop-json-flywheel.timer
systemctl --user status primitive-20m-goal-plan.timer
systemctl --user status primitive-20m-supervised-cycle.timer
systemctl --user status primitive-realistic-session-benchmark.timer
systemctl --user status primitive-ml-lifecycle-session-benchmark.timer
systemctl --user status primitive-large-org-session-benchmark.timer
systemctl --user status primitive-gemma-long-multistep-loop.service
systemctl --user status primitive-ollama-local-gemma4-smoke.timer
systemctl --user status primitive-multimodel-improvement.timer
systemctl --user status primitive-shard-builder-20k.timer
systemctl --user status primitive-provider-fleet-ollama.timer
systemctl --user status primitive-codex-gap.timer
```

## Stop Commands

```bash
systemctl --user stop primitive-loop-json-flywheel.timer
systemctl --user stop primitive-20m-goal-plan.timer
systemctl --user stop primitive-20m-supervised-cycle.timer
systemctl --user stop primitive-realistic-session-benchmark.timer
systemctl --user stop primitive-ml-lifecycle-session-benchmark.timer
systemctl --user stop primitive-large-org-session-benchmark.timer
systemctl --user stop primitive-gemma-long-multistep-loop.service
systemctl --user stop primitive-ollama-local-gemma4-smoke.timer
systemctl --user stop primitive-ollama-compat.timer
systemctl --user stop primitive-context-foundry.timer
systemctl --user stop primitive-multimodel-improvement.timer
systemctl --user stop primitive-shard-builder-20k.timer
systemctl --user stop primitive-provider-fleet-ollama.timer
systemctl --user stop primitive-codex-gap.timer
```

## Cron Equivalents

Use these only on hosts where user systemd timers are not available. Keep the
same `PYTHONPATH` so moved `_repos/` imports resolve.

```cron
PYTHONPATH=/home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/shared-backend-components:/home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/teleon/backend:/home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/baltor/backend

*/30 * * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"flywheel.run","request_id":"cron-full-flywheel-max-budget","args":{"iterations":1,"mode":"full","max_child_actions":10,"execute_live_model":false,"auto_reduce_on_issue":true,"run_token_benchmark":true,"token_n":300,"token_k":5,"token_intent_mode":"paraphrase","source_limit":36,"source_question_count":1200,"source_max_components":12,"deconstruction_question_count":1800,"deconstruction_overlays_per_primitive":10,"deconstruction_max_base_primitives":0,"gemma_limit":1,"input_context_tokens":262144,"output_context_tokens":65536,"max_token_ceiling":65536,"gemma_min_hidden_edges":10,"gemma_min_examples":4}}'
15 */6 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_goal.run","request_id":"cron-20m-goal-plan","args":{"target":20000000,"horizon_days":60,"daily_working_target":100000,"daily_candidate_target":400000}}'
45 */2 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_cycle.run","request_id":"cron-20m-supervised-cycle","args":{"seed_rows":100000,"rows_per_shard":10000,"compile_shards":2,"start_shard":-1,"benchmark_n":300,"benchmark_k":5,"benchmark_seed":23,"paraphrase":true}}'
35 */3 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","request_id":"cron-realistic-session-benchmark","args":{"sessions":16,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"mixed","include_supervised":true,"compare_base":true,"context_window":262144}}'
55 */3 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","request_id":"cron-ml-lifecycle-session-benchmark","args":{"sessions":8,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle","include_supervised":true,"compare_base":true,"context_window":262144}}'
15 */3 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","request_id":"cron-large-org-session-benchmark","args":{"sessions":6,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"large_org","include_supervised":true,"compare_base":true,"context_window":262144}}'
0 * * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/ollama_local_model_smoke.py --model gemma4:latest --timeout 180 --num-predict 24
5 * * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/check_ollama_free_limited_compatibility.py --self-test
10 * * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --once --surface-limit 10 --use-case-limit 20 --microsurface-limit 20 --source-discovery-seed-limit 20 --search-scope-limit 20 --naics-scope-limit 20 --business-operation-scope-limit 20 --include-local-claude --derive-local-reviews --max-local-sessions 20 --local-repo-root /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing --local-repo-limit 120
20 */2 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/multi_model_improvement_loop.py --run --limit 2 --kinds architecture,module,research --target-workers 1
10 18 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/build_primitive_factory_5k_shards.py --target-profile 20k
30 */3 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && /usr/bin/python3 _repos/shared-backend-components/scripts/run_primitive_provider_fleet_loop.py --max-cycles 1 --scale 1 --max-tokens 65536 --only-lane glm_ollama_direct_candidate_writer --only-lane kimi_ollama_direct_long_expander --run-label scheduled-ollama-glm-kimi
0 */6 * * * cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing && MAX_CYCLES=1 CYCLE_TIMEOUT=14400 CODEX_MODEL=gpt-5.6-sol CODEX_REASONING_EFFORT=ultra /usr/bin/bash _repos/shared-backend-components/scripts/run_codex_north_star_gap_loop.sh --once
```
