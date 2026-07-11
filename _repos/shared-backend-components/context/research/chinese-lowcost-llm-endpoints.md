# Cheaper Chinese / China-adjacent LLM endpoints — a GOVERNED LOW-COST PAID lane

Status: research + governed catalog. Companion registry:
[`architecture/lowcost_llm_endpoint_registry.json`](../../architecture/lowcost_llm_endpoint_registry.json).
Enforced by [`scripts/check_lowcost_llm_endpoint_registry.py`](../../scripts/check_lowcost_llm_endpoint_registry.py)
(`--self-test`, deterministic, stdlib-only). Pricing web-verified ~2026-06; figures are approximate list
prices (pre-promo, excluding cache/batch discounts) — reconfirm against official provider docs before spend.

This is a **distinct lane** from the FREE registry
([`architecture/free_limited_llm_endpoint_registry.json`](../../architecture/free_limited_llm_endpoint_registry.json),
which is untouched). Everything below is **low-cost PAID**, billed per token — not a free tier.

## Verdict

There is a real, durable price valley below the US frontier providers, and it is dominated by Chinese
labs and China-adjacent aggregators that ship **OpenAI-compatible** APIs (swap `base_url` + key and existing
OpenAI-SDK code works). For **public / internal-non-sensitive** bulk work — classification, extraction,
drafting, long-document passes, agent inner loops — these routes cut cost 5–50x versus US frontier APIs at
competitive quality.

The catch is **jurisdiction, not capability**. Almost every cheap route is China-mainland resident (PRC data
jurisdiction). That is acceptable for public/internal-non-sensitive data and **unacceptable** for customer,
regulated, secrets, confidential, or PII data — which must route to a paid-enterprise-ZDR provider in an
acceptable jurisdiction, or to self-hosted/private inference. So the catalog is **policy-first**: price and
OpenAI-compatibility get a provider *admitted*; data-class + jurisdiction decides *what may flow through it*.

Recommendation by tier:

- **admit_first** (verified cheap, clean compatibility, run as candidates first): **DeepSeek direct**,
  **Qwen Model Studio International (Singapore)**, **SiliconFlow**, **Z.AI / GLM**, **MiniMax**.
- **probation / watchlist** (cheap but SDK-first, intl-onboarding friction, or higher output cost):
  **Moonshot/Kimi**, **StepFun**, **Baidu Qianfan/ERNIE**, **Tencent Hunyuan**, **Volcengine Ark/Doubao**.
- **exclude** from this catalog: **Together AI** — US-based (good jurisdiction) but **not free** (no free
  trial, $5 minimum purchase) and not China-adjacent, so it belongs in neither this lane nor the free
  registry as "free".

## Cheapest verified routes (the headline)

| Route | ~$/Mtok in | ~$/Mtok out | Note |
|---|---|---|---|
| Volcengine Doubao Seed 1.6 Flash | **$0.022** | $0.219 | Cheapest verified — but China-Beijing + real-name/Chinese-phone barrier (watchlist) |
| Qwen-Flash (International / Singapore) | **$0.05** | $0.20 | Cheapest **safe-region** route (data in Singapore, not PRC) — admit_first |
| Z.AI GLM-4.7-Flash | $0.06 | $0.40 | Cheapest current GLM flash — admit_first |
| Tencent Hunyuan HY3 Preview | $0.063 | $0.210 | SDK-first → watchlist |
| StepFun Step 3.5 Flash | $0.09 | $0.30 | 256K ctx, agent-positioned → probation |
| SiliconFlow (DeepSeek route) | $0.13 | $0.28 | Aggregator, OpenAI-compat — admit_first |
| **DeepSeek V4 Flash (direct)** | **$0.14** | **$0.28** | **1M ctx, JSON+function-calling, cache-hit $0.0028** — admit_first |

## Per-provider table

| Provider | Route (`base_url`) | ~$/Mtok (in/out) | OpenAI-compat | Capabilities | Region / residency | Data-use posture | Admit tier |
|---|---|---|---|---|---|---|---|
| **DeepSeek** (direct) | `https://api.deepseek.com` | $0.14 / $0.28 (cache-hit $0.0028) | Yes (swap base_url+key); JSON mode + function calling (strict) | chat, reasoning, code, 1M long-ctx, tool-use | China (PRC) | Paid usage; China jurisdiction → public/internal only | admit_first |
| **Alibaba Qwen / Model Studio** (International) | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | $0.05 / $0.20 (qwen-flash); $0.40/$1.20 (qwen-plus) | Yes | chat, multimodal, code, long-ctx, tool-use | **Intl: data in Singapore**, inference global ex-PRC-mainland; modes US/EU/SG/China | Cleanest safe-region cheap route | admit_first |
| **SiliconFlow** (aggregator) | `https://api.siliconflow.com/v1` (`.cn` = China) | $0.13/$0.28 (DeepSeek); $0.26/$2.08 (Qwen) | Yes (fully OpenAI-compatible MaaS) | 200+ models, embeddings, rerank, tool-use | `.com` intl / `.cn` China — verify upstream per model | Aggregator: confirm upstream + residency per model | admit_first |
| **Z.AI / GLM** (BigModel) | `https://api.z.ai/api/paas/v4` | $0.06/$0.40 (GLM-4.7-Flash); $0.43/$1.74 (GLM-4.6, 200K) | Yes | chat, reasoning, code, agentic, tool-use | China (PRC) origin; intl platform exists | China jurisdiction → public/internal only | admit_first |
| **MiniMax** (M-series) | `https://api.minimax.io/v1` | $0.255 / $1.00 (M2) | Yes (OpenAI SDK / Anthropic SDK / HTTP) | chat, ~204K long-ctx, agentic, tool-use | China (PRC) origin; intl platform | China jurisdiction → public/internal only | admit_first |
| **Moonshot / Kimi** | `https://api.moonshot.ai/v1` | $0.60/$3.00 (K2.5, cache $0.10); $0.95/$4.00 (K2.6) | Yes | chat, 262K long-ctx, agentic, code, tool-use | China (PRC) origin; intl | China jurisdiction → public/internal only | probation |
| **StepFun** (Step series) | `https://api.stepfun.com/v1` | $0.09/$0.30 (Step 3.5 Flash, 256K); $0.20/$1.15 (3.7 Flash) | Yes | chat, multimodal, agentic, code, tool-use | China (PRC) | Newer intl track record | probation |
| **Baidu Qianfan / ERNIE** | `https://qianfan.baidubce.com/v2` | $0.55/$2.20 (ERNIE 4.5); $0.59/$2.65 (5.1) | Yes (documented OpenAI-compat request format, Bearer) | chat, reasoning, code, tool-use | China (PRC), hosted-only on Qianfan | China platform + intl onboarding friction | probation |
| **Tencent Hunyuan** | `https://api.hunyuan.cloud.tencent.com/v1` | $0.063/$0.210 (HY3 Preview); $0.14/$0.57 (A13B) | Partial (Tencent SDK is the preferred/full path) | chat, multimodal, reasoning, code, tool-use | China (PRC), Tencent Cloud | SDK-first → watchlist | watchlist |
| **Volcengine Ark / Doubao** (ByteDance) | `https://ark.cn-beijing.volces.com/api/v3` | **$0.022/$0.219** (Seed 1.6 Flash); $0.514/$2.57 (Seed 2.0 Pro) | Yes (OpenAI-SDK-compat) | chat, multimodal, reasoning, code, tool-use | China-Beijing (PRC); real-name + Chinese-phone barrier | Cheapest, but access barrier → watchlist | watchlist |
| **Together AI** (boundary marker) | `https://api.together.xyz/v1` | per-model (see together.ai/pricing) | Yes | 200+ open models, aggregator, tool-use | US (non-China) | **Not free** ($5 min, no trial); not China-adjacent | **exclude** |

## Lane taxonomy

The catalog defines and the checker enforces a lane taxonomy spanning all four families:

- **`free/*`** — no-cost / rate-limited tier (GitHub Models, Groq, Gemini free). Lives in the **FREE
  registry** (`free_limited_llm_endpoint_registry.json`), *not* this file. Prototype-only; free-tier data may
  train the vendor; never customer-sensitive.
- **`lowcost/global-cheap`** — low-cost **PAID** with a clean international/non-China residency option (Qwen
  International @ Singapore, SiliconFlow `.com`). The cheapest *safe-region* routes for public/internal bulk.
- **`lowcost/china-cheap`** — low-cost **PAID** whose primary jurisdiction is China-mainland (DeepSeek direct,
  Baidu, Tencent, Volcengine/Doubao, StepFun, MiniMax CN). Often cheapest per token; China jurisdiction →
  **public / internal-non-sensitive only**.
- **`lowcost/code-agent`** — low-cost PAID tuned for coding / tool-use / agentic loops (DeepSeek V4, Z.AI GLM,
  StepFun agent, Kimi). Same data-class caps as their jurisdiction.
- **`lowcost/long-context`** — low-cost PAID with very large context (DeepSeek 1M, MiniMax ~204K, Kimi 262K,
  StepFun 256K). For large-document/codebase passes; same caps as jurisdiction.
- **`paid/safe`** — paid **enterprise** providers with strong privacy/ZDR + acceptable jurisdiction. The
  **only** lane allowed to carry customer / regulated / confidential / PII. (Separate enterprise registry.)
- **`selfhost/private`** — self-hosted / private inference (local Ollama/vLLM, VPC). The most-private lane and
  the fallback for any data that cannot leave the boundary. (See the free registry's self-hosted rows +
  Teleon Sandbox.)

## Data-class → lane routing table (the load-bearing rule)

Price and OpenAI-compatibility decide *admission*; **data-class + jurisdiction decides routing**.

| Data class | May route to | NEVER route to |
|---|---|---|
| `public` | any lane (cheapest acceptable wins) | — |
| `internal_non_sensitive` | `lowcost/*` (incl. China-cheap), `paid/safe`, `selfhost/private` | — |
| `customer` | `paid/safe` (ZDR) **or** `selfhost/private` only | `free/*`, `lowcost/*` |
| `regulated` | `paid/safe` (ZDR, jurisdiction-checked) **or** `selfhost/private` | `free/*`, `lowcost/*` |
| `confidential` | `paid/safe` (ZDR) **or** `selfhost/private` | `free/*`, `lowcost/*` |
| `secrets` | `selfhost/private` only (prefer: never send secrets to any LLM) | everything else |
| `pii` | `paid/safe` (ZDR + DPA) **or** `selfhost/private` | `free/*`, `lowcost/*` |

A China-mainland jurisdiction caps `allowed_data_classes` to `public` / `internal_non_sensitive`
**regardless of price**. The checker fails if any low-cost entry lists a forbidden class.

## Cost-aware + region-aware + policy-first routing notes

- **Policy first, then price.** The router resolves the **data class** of a task before it looks at price. If
  the data class forbids the low-cost lanes, price is irrelevant — it goes to `paid/safe` or `selfhost`.
- **Region-aware within the lane.** For public/internal work, prefer the cheapest acceptable *region* —
  `lowcost/global-cheap` (Qwen International @ Singapore) is preferable to `china-cheap` when residency
  matters even for non-sensitive data, because it keeps data out of PRC jurisdiction entirely.
- **Cost-aware within the region.** Among equally-acceptable routes, sort by *blended* expected cost
  (weight input vs output by your traffic mix; account for cache-hit and batch discounts — DeepSeek's
  cache-hit at $0.0028 and Qwen/Alibaba batch at 50% are large levers).
- **Numeric, not name-based.** Following the repo's no-magic-values rule, the live router should branch on
  numeric provider IDs / priorities / weights from config, never on display strings; this catalog is the
  human-readable source those numbers derive from.
- **Candidate, never auto-active.** Admission to this catalog is *candidate*. Promotion to live use requires
  the standard ladder (local conformance → dev-only spend-capped key → candidate/shadow → approved
  non-sensitive), official paid/ZDR terms where data class demands it, a `ModelInvocationReceipt`, and a
  governed fallback. **Output is never truth** — it is gated through the Teleon Inference Gateway.

## Rules of the road (operational governance)

These are non-negotiable for any low-cost-lane use:

1. **No fake accounts.** Use legitimately registered company accounts under real terms. Do not fabricate
   identity to dodge a provider's verification (e.g. Volcengine's real-name requirement → that provider stays
   watchlist until access is legitimately available).
2. **No shared / leaked / pooled keys.** Never use a key that is not the company's own. Shared-key and
   "unlimited"/"bypass" repos are quarantine in the free registry and have **no place** here.
3. **No reverse-engineered or unofficial endpoints.** Only official, documented APIs. No scraped chatbot
   backends, no unofficial proxies to a consumer app.
4. **Company-owned, scoped, rotated, spend-capped keys.** Each provider key is owned by the company, scoped to
   the minimum needed, rotated on a schedule, and capped with hard provider-side spend limits. Keys live in a
   vault; the registry stores only `vault://`-style `secret_ref`s — **never raw key literals** (the checker
   greps for `sk-`/`AKIA`/`gsk-` and fails on any).
5. **Products identify themselves on every request.** Send an honest identifying `User-Agent` / app header so
   the provider can attribute traffic; never impersonate another client.
6. **Right data in the right lane.** Enforce the data-class routing table above. Customer/regulated/secrets/
   confidential/PII never touch a low-cost or China-region lane — full stop.
7. **Unpaid-usage-trains-the-vendor caution (Gemini-style).** Where a provider's *free/unpaid* tier may be
   used to train the vendor, that lives in the **free** registry's notes. This catalog is **paid** usage,
   which generally carries stronger retention terms — but verify the retention/training stance per provider
   before sending even internal-non-sensitive data, and record it in `data_use_note`.

## Sources

- [DeepSeek Models & Pricing (official API docs)](https://api-docs.deepseek.com/quick_start/pricing)
- [DeepSeek JSON Output (official)](https://api-docs.deepseek.com/guides/json_mode)
- [DeepSeek Function Calling / Tool Calls (official)](https://api-docs.deepseek.com/guides/function_calling)
- [DeepSeek pricing 2026 (CloudZero)](https://www.cloudzero.com/blog/deepseek-pricing/)
- [Alibaba Cloud Model Studio model pricing (official)](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- [Call Qwen via OpenAI-Compatible API (official)](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)
- [Qwen pricing in 2026 (eesel AI)](https://www.eesel.ai/blog/qwen-pricing)
- [SiliconFlow pricing](https://www.siliconflow.com/pricing)
- [SiliconFlow Chat Completions API (docs)](https://docs.siliconflow.com/en/api-reference/chat-completions/chat-completions)
- [Z.AI Developer pricing (official)](https://docs.z.ai/guides/overview/pricing)
- [GLM-4.7-Flash pricing (OpenRouter)](https://openrouter.ai/z-ai/glm-4.7-flash)
- [MiniMax API Overview / Models (official)](https://platform.minimax.io/docs/api-reference/api-overview)
- [MiniMax M2 pricing (OpenRouter)](https://openrouter.ai/minimax/minimax-m2)
- [Moonshot Kimi K2 pricing 2026 (TokenMix)](https://tokenmix.ai/blog/kimi-k2-api-pricing)
- [Kimi K2.5 (OpenRouter)](https://openrouter.ai/moonshotai/kimi-k2.5)
- [StepFun Step 3.5 Flash (OpenRouter)](https://openrouter.ai/stepfun/step-3.5-flash)
- [StepFun pricing (pricepertoken)](https://pricepertoken.com/pricing-page/provider/stepfun-ai)
- [Baidu Qianfan ERNIE pricing (DataCamp)](https://www.datacamp.com/blog/ernie-4-5-x1)
- [Baidu ERNIE undercuts DeepSeek/OpenAI (VentureBeat)](https://venturebeat.com/ai/baidu-delivers-new-llms-ernie-4-5-and-ernie-x1-undercutting-deepseek-openai-on-cost-but-theyre-not-open-source-yet)
- [Tencent Hunyuan via AI Gateway (Tencent Cloud docs)](https://www.tencentcloud.com/document/product/1290/79463?lang=en)
- [Tencent Hunyuan pricing (pricepertoken)](https://pricepertoken.com/pricing-page/provider/tencent)
- [Volcengine Doubao API setup + pricing (DEV)](https://dev.to/tokenmixai/doubao-api-setup-2026-19-bytedance-models-0022m-floor-python-in-5-min-2akn)
- [Together AI billing / credits (official)](https://docs.together.ai/docs/billing-credits)
- [Together AI free tier / $5 minimum (Price Per Token)](https://pricepertoken.com/endpoints/together/free)
