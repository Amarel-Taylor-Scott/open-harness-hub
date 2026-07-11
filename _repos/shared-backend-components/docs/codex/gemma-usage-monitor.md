# Gemma 4 Primitive Factory Usage Monitor

The Gemma monitor reports local Open WebUI/Gemma primitive-factory usage from
candidate-generation artifacts. It is evidence-only: snapshots keep
`candidate=true` and `serves_truth=false`.

## Commands

Text snapshot:

```bash
python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --format text
```

JSON snapshot:

```bash
python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --format json
```

Write the static dashboard:

```bash
python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --write-dashboard
```

Serve the live dashboard:

```bash
python3 scripts/gemma_usage_monitor.py --date 2026-07-01 --serve --port 9174
```

Open:

```text
http://127.0.0.1:9174/
```

The server also exposes:

```text
http://127.0.0.1:9174/snapshot.json
```

## What It Shows

- Gemma/OpenWebUI accepted candidate count.
- Prompt, completion, and total token counts.
- Aggregate completion TPS and total TPS.
- Worker errors and dry-run labels.
- Live SVG charts for accepted candidates, Gemma tokens, and throughput.
- Provider-lane bars for Gemma, GLM, and Kimi.
- Live model-call events from `call_events.jsonl` when the worker is
  instrumented.
- Raw flywheel totals: calls started, calls finished, active calls, retry
  events, model-output receipts, output errors, and failed model receipts.
- Raw flywheel by provider/model so accepted rows are not the only visible
  signal.
- Active raw calls and recent raw results with shard ids, status, token usage,
  durations, and error summaries.
- Source material inventory with selected source-file counts, source rows,
  catalog JSONL rows, and daily 20k shard counts.
- A browser console stream fed by `/api/events`.
- Recent Gemma worker batches.
- Latest provider-fleet lane status for Gemma, GLM, and Kimi.
- Local Chrome DevTools/Open WebUI target status.
- Process visibility and whether the monitor is running in a sandbox-limited
  PID namespace.

## Live Endpoints

The served dashboard is no longer a static meta-refresh page. It polls and
subscribes to:

```text
http://127.0.0.1:9174/snapshot.json
http://127.0.0.1:9174/api/snapshot
http://127.0.0.1:9174/api/console
http://127.0.0.1:9174/api/events
```

`/api/events` is a Server-Sent Events stream with `snapshot` and `console`
events. The browser falls back to JSON polling if EventSource is unavailable.

## Model Call Events

`scripts/run_primitive_factory_model_worker.py` emits per-call JSONL records:

```text
batch_*/model/call_events.jsonl
```

Each call gets a `call_started` row and a `call_finished` row with provider,
model, shard id, duration, token usage, status, and error summary. These rows
are candidate telemetry only; they do not promote any primitive.

The monitor also reads `model_outputs.jsonl` receipts directly. This matters
when a provider returns errors: accepted-count charts can look stable while raw
calls are failing. Use the Raw Flywheel tables for throughput and failure
debugging, then use accepted/L3 counts for database-yield accounting.

## Source Material Inventory

The monitor verifies that the factory has enough source material before judging
candidate quality. For the 2026-07-01 20k profile, the live inventory includes:

```text
catalog_jsonl_files=299
catalog_rows=126625
selected_source_rows=74333
daily_20k_shards=800
selected_source_files=20/20
```

Those numbers indicate the current bottleneck is not source-material volume.
The live bottlenecks are provider stability, row-shape quality, dedupe, and L3
verification yield.

## Verification Yield

The deterministic verifier normalizes common model drift while preserving the
candidate boundary. Current repairs include:

- `primitive-group` kind normalization to `primitive_group`.
- string `contract` wrapping into a contract object.
- `label=https://...` source-ref normalization.
- source-ref alias resolution from daily shard source maps.
- string effects wrapped into effect objects.
- missing mutators inferred from candidate shape, with a promotion blocker.
- one-item proof plans completed with candidate-boundary/source/contract gates,
  with a promotion blocker.
- primitive-group contracts repaired from top-level hidden member edges when
  the model placed hidden edges outside `group_contract`.

Rows repaired this way remain `candidate=true` and `serves_truth=false`; the
repair is not promotion. Inferred fields receive normalization notes and
promotion blockers so tests or human review can focus on them.

## Running Productive Lanes While Gemma Is Blocked

If Open WebUI/Gemma is Cloudflare-challenged but Ollama Cloud lanes are working,
keep GLM and Kimi running and exclude the Gemma lane:

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

Create this file to stop the continuous loop cleanly:

```text
data/dev-intel/primitive_factory/STOP
```

## Open WebUI CDP Probe

Use the redacted CDP probe when the Chrome target exists but model calls fail:

```bash
python3 scripts/openwebui_cdp_client.py --probe --timeout 60
```

The probe reports page URL/title, whether an Open WebUI token is present, and
whether `/api/config`, `/api/models`, and `/api/chat/completions` return JSON or
Cloudflare HTML. It does not export tokens, cookies, or clearance values.

Observed failure mode:

```text
title=Open WebUI
token_present=true
/api/config -> 403 text/html Cloudflare "Just a moment..."
/api/models -> 403 text/html Cloudflare "Just a moment..."
/api/chat/completions -> 403 text/html Cloudflare "Just a moment..."
```

When this happens, the browser profile needs a Cloudflare/session refresh before
Gemma can be used productively again.

## Operational Notes

When run inside Codex's normal sandbox, process and CDP visibility may be
limited. For host-process and Chrome DevTools visibility, run the monitor
outside the sandbox or grant the command explicit approval.

The monitor never reads or writes Open WebUI tokens, cookies, localStorage, or
Cloudflare clearance values. It only checks the CDP target list and local
primitive-factory artifacts.
