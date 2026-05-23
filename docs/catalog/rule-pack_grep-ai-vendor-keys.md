# AI vendor API key detectors

*rule-pack* · `rule-pack/grep-ai-vendor-keys` · v0.1.0 · beta

Detection patterns for API keys issued by major LLM / AI vendors —
Anthropic, OpenAI, Hugging Face, Cohere, Replicate, Mistral, Groq,
Together, fal, Perplexity, Voyage, NVIDIA NIM. The highest-current-risk
category given how many AI projects accidentally commit these keys.

Treat every hit as critical and run a key-revocation step
immediately. Most vendors also have programmatic revocation endpoints
(Anthropic `/v1/admin/api-keys/{id}`, OpenAI `/v1/api-keys/{id}`).

| axis | value |
|---|---|
| industry | security, ai |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `anthropic_api_key` | critical | secret.anthropic | `\bsk-ant-api03-[A-Za-z0-9_\-]{95}\b` |
| `anthropic_admin_key` | critical | secret.anthropic | `\bsk-ant-admin01-[A-Za-z0-9_\-]{95}\b` |
| `openai_api_key_legacy` | critical | secret.openai | `\bsk-[A-Za-z0-9]{48}\b` |
| `openai_project_key` | critical | secret.openai | `\bsk-proj-[A-Za-z0-9_\-]{60,}\b` |
| `openai_admin_key` | critical | secret.openai | `\bsk-admin-[A-Za-z0-9_\-]{60,}\b` |
| `huggingface_token` | critical | secret.huggingface | `\bhf_[A-Za-z]{34}\b` |
| `cohere_api_key` | low | secret.cohere | `\b[A-Za-z0-9]{40}\b` |
| `replicate_api_token` | critical | secret.replicate | `\br8_[A-Za-z0-9]{37}\b` |
| `groq_api_key` | critical | secret.groq | `\bgsk_[A-Za-z0-9]{52}\b` |
| `together_api_key` | high | secret.together | `\btogether_[A-Za-z0-9]{40,}\b` |
| `fal_key` | critical | secret.fal | `\bfal-[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]...` |
| `perplexity_key` | critical | secret.perplexity | `\bpplx-[A-Za-z0-9]{48,}\b` |
| `voyage_key` | critical | secret.voyage | `\bpa-[A-Za-z0-9_\-]{43}\b` |
| `nvidia_nim_key` | critical | secret.nvidia | `\bnvapi-[A-Za-z0-9_\-]{60,}\b` |
| `mistral_key` | high | secret.mistral | `(?i)mistral(.{0,12})?[A-Za-z0-9]{32}` |

