# AIDevObserver Primitive 2M Loop

Objective: run the primitive factory as an evergreen loop. The first milestone
is 2,000,000 aggregate verified L3 primitive/group candidates; after that,
continue into the next shard epochs, source families, task families, and
coverage targets instead of stopping. The milestone metric is the sum of
`verified_count` across:

```text
data/dev-intel/primitive_factory/verified_candidates/*/manifest.json
```

Do not soft-stop on roadblocks. If one surface fails, use the least resistant
working path: retry, recover sessions, restart services, reduce batch size,
increase timeout, switch providers, advance shard epochs, mine alternate source
surfaces, add deterministic fallbacks, or launch exploratory sprout lanes for
new domains/use cases.

## Primary Command

Start or repair the durable supervisor:

```bash
python3 scripts/start_primitive_2m_goal.py start --target-verified 2000000 --date-prefix 2026-07-01 --continue-after-target --no-honor-stop-file
```

Status:

```bash
python3 scripts/start_primitive_2m_goal.py status
python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --format text --no-cdp-check
```

Useful artifacts:

```text
data/dev-intel/primitive_factory/2m_goal/state.json
data/dev-intel/primitive_factory/2m_goal/latest_status.json
data/dev-intel/primitive_factory/2m_goal/goal_ledger.jsonl
data/dev-intel/primitive_factory/2m_goal/loop_manifest.json
data/dev-intel/primitive_factory/2m_goal/primitive-2m-goal.log
```

## Supervisor Duties

- Keep Gemma OpenWebUI CDP generation running through `gemma-recovered`.
- Keep GLM/Kimi Ollama generation running through `glm-kimi`.
- Keep deterministic verification running.
- Keep failed-shard retry running so provider timeouts, disconnected calls, and
  obsolete model names are retried through working fallbacks.
- Keep the source foundry running for public/local source material.
- Build new 20k shard epochs when a shard set is nearly exhausted.
- Prune stale per-epoch helper services; keep the active/recent epoch window hot
  and stop/reset old Gemma/Ollama/verify/retry units so they do not steal
  scheduler capacity.
- Reserve live shard windows from active batch processes before planning new
  work.
- Use high output ceilings unless explicitly running a smoke test.
- For Open WebUI Gemma, require a real CDP chat probe (`/api/chat/completions`
  status 200) before starting the Gemma generator. If CDP is challenged, stop
  active Gemma units and continue with Ollama while recovery retries.
- Send both `max_tokens` and `max_completion_tokens` to OpenAI-compatible
  Open WebUI calls; treat provider-side length stops as a routing/batching
  signal, not a reason to lower ceilings.
- Record every tick as candidate-only receipts.
- Continue after milestone counts; milestones are progress markers, not stop
  conditions.
- When blocked, try fallbacks in this order: recover provider session, restart
  service, lower per-batch shard count, increase timeout, switch provider,
  regenerate/advance shard epoch, mine a different source surface, add a
  deterministic parser/repair step, create a sprout lane for a fresh domain.
- Retry failed shard receipts through
  `scripts/run_primitive_failed_shard_retry_loop.py`, skipping shards that
  already have successful output receipts and keeping retry outputs in a
  separate candidate-only retry tree.

## Invariants

- No model output is promoted to truth.
- Primitive rows remain `candidate=true` and `serves_truth=false`.
- Prefer useful primitive groups with visible input/output edges and hidden
  member edges.
- Every candidate needs source refs, mutators, proof requirements, and promotion
  blockers.
- Dashboard/monitor must show raw calls, active workers, recent errors, tokens,
  source inventory, and verification counts.
- No stop condition should be embedded in the pasted goal command. Operators can
  still stop OS services manually if required, but the agent should treat the
  loop as perpetual.
