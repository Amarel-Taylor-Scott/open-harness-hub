# Ollama as the default brain — GLM-5.2 / Kimi-k2.7-code (2026-06-20)

The cheap Ollama lane is positioned as the **default LLM brain** — the orchestrator, reviewer, and
distiller-judge that drive a capability from unbounded+inefficient toward most-bounded+most-efficient —
escalating to a frontier model only when a confidence/quality bar fails. The descent applied to the brain itself.

## Auth (env-ref only — value never tracked)
- The Ollama key is referenced by the env name **`OLLAMA_API_KEY`**. The raw value lives **only in the
  gitignored `.env`** (and is never written to any tracked file — secret-hygiene law, enforced by
  `scripts/check_llm_secret_hygiene.py`). To use it elsewhere: `export OLLAMA_API_KEY=...` or rely on `.env`.

## Models registered (architecture/model_index.json, freshness-governed)
- **`glm-5.2`** — Zhipu via Ollama Cloud; `frontier`/general; `auth_env_ref: OLLAMA_API_KEY`.
- **`kimi-k2.7-code`** — Moonshot via Ollama Cloud; `high`/coding; `auth_env_ref: OLLAMA_API_KEY`.
- Endpoint: the Ollama OpenAI-compatible `…/v1/chat/completions`. Costs are candidate-until-verified
  (the model index holds stale facts out until re-synced).

## Default brain policy (architecture/default_brain_policy.json)
| role | cheap default (Ollama) | escalates to (frontier) | escalate when |
|---|---|---|---|
| orchestrator | `glm-5.2` | `claude-sonnet-4-6` | a multi-step plan fails validation / low planning confidence |
| reviewer | `kimi-k2.7-code` | `claude-opus-4-8` | high review uncertainty / high-blast-radius change |
| distiller-judge | `glm-5.2` | `gpt-o3` | eval judges disagree / borderline lift |

`src/teleon/inference/default_brain.brain_for(role, available_keys, force_frontier)` selects the cheap default
when `OLLAMA_API_KEY` is present, escalates only when forced or when the default is unreachable. The default is
**verifiably cheaper** than its escalation (cross-checked against the model index). Proof:
`scripts/check_default_brain_policy.py`. The brain PROPOSES; the eval/policy gates DISPOSE — `serves_truth=false`.
