# LLM Endpoint Usage Policy

_Status: candidate operating policy for the provider-agnostic primitive-generation router
(`scripts/llm_capability_router.py`) and its quota guardrail (`scripts/llm_quota_manager.py`). serves_truth=false._

The router lets many primitive-generation jobs share a small set of free/keyed model lanes (Hy3 on OpenRouter,
NVIDIA Build, Ollama Cloud, Ollama local, OmniRoute). This policy is the **compliance contract** every call
runs under. The LLM **proposes**; the deterministic system (security gate, sandbox, fixture proof, promotion
gates) **disposes**. Nothing here promotes or serves truth.

## Hard rules (do NOT)

1. **Do NOT bypass, defeat, or "work around" a provider's rate limits.** A `429` / rate-limit / usage-pause is
   a signal to **back off**, not to retry faster. The router cools the lane (exponential backoff + jitter) and
   rotates to a *different provider* (a separate rate pool) — it never hammers a limited endpoint.
2. **Do NOT rotate API keys to evade a per-account limit.** Multiple keys exist to use *your own* legitimately
   provisioned capacity across concurrent workers, not to circumvent one account's cap. When every configured
   key is limited, the job is **queued**, not forced through on a fresh key.
3. **Use keys ONLY as configured.** Keys come from `.agent/openrouter_keys.txt` and the gitignored `.env` — never
   hard-coded, never committed, never logged. The tooling reports key **presence** (set / not set), never values.
4. **Do NOT send private material to a cloud lane.** Data classed `internal` / `sensitive` / `restricted` routes
   **LOCAL-first** (Ollama on localhost). A cloud lane may see such data **only** if its capability explicitly
   allows that class **and** a redactor passes first. By default no cloud lane allows anything above `synthetic`.
5. **Do NOT store raw prompt text or secrets in any receipt.** The usage ledger stores a prompt **hash** and safe
   metadata only. Raw bodies are dropped at the ledger boundary (allowlisted fields) and string fields are
   scrubbed of key-shaped tokens.
6. **Respect provider Terms of Service and robots/scraping policies.** This router calls model APIs you are
   entitled to use; it is not a scraper and must not be pointed at endpoints you are not authorized to call.

## Controls the tooling enforces

| Control | Where | Behavior |
|---|---|---|
| **Kill switch** | `.agent/STOP_LLM_GENERATION` | `touch` it to halt ALL router-driven generation instantly; delete it to resume. Checked before every call. |
| **Per-provider budgets** | `QuotaManager(budgets=…)` | `max_requests` / `max_tokens` / `max_cost` per provider; a lane over budget is skipped, not called. |
| **Per-campaign cost cap** | `QuotaManager(campaign_cost_cap=…)` | The tighter of provider budget vs campaign cap wins; an estimate that would exceed the cap is refused **before** the call. |
| **Cooldowns** | `QuotaManager.cooldown()` | Throttled lanes rest with exponential backoff + jitter; consecutive throttles escalate. |
| **Dry run** | `--dry-run` / `dry_run=True` | Route + estimate cost + record intent, **never** call the model. |
| **Estimated → actual cost** | `estimate_cost()` before; usage after | Estimated cost gates the budget; actual cost (when the provider returns usage) is charged and ledgered. |
| **Redacting usage ledger** | `artifacts/llm_usage/usage_ledger.jsonl` | One row per attempt: job/campaign/provider/model/prompt_hash/schema_hash/tokens/cost/latency/status/error_class/retry/fallback. No raw prompt, no key. |
| **Never-drop queue** | `artifacts/llm_usage/generation_queue.jsonl` | When all lanes are exhausted or generation is halted, the job is persisted (body hashed), never silently dropped. |

## Fallback ladder (never a silent drop)

`retry-same-lane-once → next lane (alt model / same family) → lower-cost degraded lane → QUEUE`.

Each rung is quota-gated and ledger-recorded. A throttle cools the lane before the router moves on, so a
rate-limited provider is given time to recover rather than being retried into the ground.

## Data classes

`public < synthetic < internal < sensitive < restricted`. A lane's `allowed_data_classes` in
`config/llm_provider_capabilities.yaml` is the gate. `internal` / `sensitive` / `restricted` force LOCAL-first
routing; redaction is mandatory before any such data may reach a lane that allows it above `synthetic`.

## Reviewing usage

`artifacts/llm_usage/usage_ledger.jsonl` is the audit trail — safe to read and share (hashes + metadata only).
`artifacts/llm_usage/generation_queue.jsonl` lists jobs awaiting capacity. Neither ever contains raw prompt
text or a credential.
