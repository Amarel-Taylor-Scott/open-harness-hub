# Primitive Factory Fable 5 Handoff

Use this when Fable 5 / Claude Code picks up the 20k/day primitive factory
work from Codex.

## Read First

1. `README.md`
2. `taxonomy/SPEC.md`
3. `CLAUDE.md`
4. `docs/codex/no-magic-values.md`
5. `docs/codex/primitive-factory-20k-daily-operating-plan.md`

## Current State

The primitive factory now has:

- 20k-mode daily shards:
  `data/dev-intel/primitive_factory/daily_shards_20k/2026-07-01/shards.jsonl`
- 10,000 real-world build-task use cases for AIDevObserver benchmark-lab testing:
  `catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl`
- Open WebUI Gemma CDP transport:
  `scripts/openwebui_cdp_client.py`
- Ollama Cloud direct transport through the shared OpenAI-compatible client:
  `scripts/_llm_client.py`
- Batch runner with extraction:
  `scripts/run_primitive_factory_batch_loop.py`
- Multi-provider planner:
  `scripts/plan_primitive_provider_fleet.py`

Every generated row remains:

```text
candidate=true
serves_truth=false
```

No model output is truth until promotion receipts exist.

## Token Policy

For primitive generation, use the high-ceiling default:

```text
max output tokens: 65,536
```

Do not lower this for real primitive batches. Small caps are only for explicit
smoke tests. The user rejected conservative caps because they caused truncated
JSONL and weak yield.

## Provider Roles

| Lane | Role | Current Judgment |
|---|---|---|
| Codex | Orchestrator, patcher, validator, documentation owner | Owns repo changes and truth-boundary discipline. |
| Open WebUI `gemma-4-coding` | Efficient candidate writer and coding helper | Best observed accepted rows per token. |
| Ollama Cloud `glm-5.2` | High-yield candidate writer and reviewer | Good direct lane for candidates and contract/proof review. |
| Ollama Cloud `kimi-k2.7-code` | Long expansion, diversity, critique | Useful but verbose; run smaller windows. |

## Observed Run Evidence

Read the manifests before trusting these numbers:

```text
data/dev-intel/primitive_factory/batch_runs/2026-07-01/20k_openwebui_gemma-4-coding_cdp/manifest.json
data/dev-intel/primitive_factory/batch_runs/2026-07-01/20k_ollama_glm-5-2_direct/manifest.json
data/dev-intel/primitive_factory/batch_runs/2026-07-01/20k_ollama_kimi-k2-7-code_direct/manifest.json
```

Snapshot from those manifests:

| Lane | Accepted | Rejected | Accepted/Shards | Completion TPS | Total TPS | Accepted / 1k Total Tokens |
|---|---:|---:|---:|---:|---:|---:|
| Gemma CDP | 30 | 0 | 10.000 | 214.864 | 264.918 | 4.520 |
| GLM direct | 99 | 10 | 14.143 | 208.330 | 225.769 | 3.017 |
| Kimi direct | 35 | 0 | 17.500 | 152.202 | 155.416 | 0.981 |

## Resume Commands

Check the Open WebUI browser-context endpoint:

```bash
python3 scripts/check_openwebui_gemma_endpoint.py \
  --mode cdp \
  --live \
  --prompt "Print exactly: Open WebUI browser-context integration OK"
```

Build or refresh the 20k shard plan:

```bash
python3 scripts/build_primitive_factory_5k_shards.py \
  --target-profile 20k \
  --date 2026-07-01 \
  --shard-useful-target 10
```

Plan disjoint provider windows:

```bash
python3 scripts/plan_primitive_provider_fleet.py \
  --date 2026-07-01 \
  --target-profile 20k \
  --scale 1
```

Inspect the generated commands:

```bash
python3 -m json.tool \
  data/dev-intel/primitive_factory/fleet_runs/2026-07-01/20k_provider_fleet_plan.json
```

The command file is:

```text
data/dev-intel/primitive_factory/fleet_runs/2026-07-01/20k_provider_fleet_commands.sh
```

The current generated plan assigns:

| Lane | Offset Window | Shards |
|---|---:|---:|
| Gemma CDP | 47-72 | 25 |
| GLM direct | 25-35 | 10 |
| Kimi direct | 35-39 | 4 |

Run one lane at a time at first. After one clean scale-1 cycle, increase
`--scale` and compare accepted rows per 1k total tokens.

## Do Not

- Do not commit tokens, cookies, browser storage, Cloudflare clearance, or
  passwords.
- Do not mark generated rows `serves_truth=true`.
- Do not use low output caps for real primitive generation.
- Do not report raw model lines as promoted primitives.
- Do not create thousands of static component files for high-volume rows; use
  JSONL staging and database load paths.

## Next Steps

1. Run the provider fleet planner and execute one scale-1 batch per lane.
2. Compare accepted rows per shard, accepted rows per 1k total tokens, and
   rejection reasons.
3. Route Gemma and GLM to the highest-yield candidate lanes; reserve Kimi for
   expansion/review unless its efficiency improves.
4. Add dedupe/load planning for accepted L2 rows into the candidate database.
5. Use the 10,000-task corpus as the real-world evaluation feed for
   AIDevObserver benchmark-lab build speed, pitfall avoidance, and primitive reuse.
6. Add a daily ledger that distinguishes raw model rows, extracted candidates,
   deduped candidates, source-backed candidates, tested candidates, and
   promoted rows.
