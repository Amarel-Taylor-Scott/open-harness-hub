# Baltor Free LLM Demo Routing

Date: 2026-06-04

This note documents how Baltor can use free or low-cost OpenAI-compatible LLM
routes for non-commercial demos without letting those routes become trusted
context infrastructure.

## Boundary

Free or unofficial model/API routes may be useful for:

- non-commercial demos
- local demo environments
- public-source summarization
- draft enhancement
- background candidate generation
- free-user slow queues

They must not be used for:

- commercial production workloads
- customer private data
- tenant or organization-scoped context
- regulated context
- source-handle expansion for sensitive sources
- final verification or adversarial validation
- policy decisions
- certified context receipts

The reason is simple: Baltor's product contract is verified, source-linked,
policy-aware context. A free/demo route can help produce draft material, but it
cannot be the authority that certifies context.

## ChatAnywhere / GPT_API_free

[chatanywhere/GPT_API_free](https://github.com/chatanywhere/GPT_API_free) is
an OpenAI-compatible gateway with free and paid access patterns. In Baltor it is
classified as:

```json
{
  "provider": "chatanywhere",
  "provider_tier": "non_commercial_demo",
  "commercial_use": "non_commercial_only",
  "trust_boundary": "hosted",
  "quality_tier": "demo_best_effort",
  "requires_reverification": true
}
```

This route is only eligible when the request declares both:

```json
{
  "model_policy": {
    "deployment_environment": "demo_noncommercial",
    "commercial_use": "non_commercial"
  },
  "data_policy": {
    "privacy_scope": "public"
  }
}
```

It is blocked for tenant/private/org scopes even when cloud use is allowed.

## Environment Wiring

The model gateway can load the route from environment variables:

```bash
export OH_LLM_ENABLE_CHATANYWHERE_DEMO=1
export CHATANYWHERE_API_KEY="..."
export OH_LLM_CHATANYWHERE_BASE_URL="https://api.chatanywhere.tech/v1"
export OH_LLM_CHATANYWHERE_MODEL="gpt-3.5-turbo"
```

Alternative key variable:

```bash
export OH_LLM_CHATANYWHERE_API_KEY="..."
```

The default route exposes only low-risk capabilities:

```text
draft_enhancement
background_summary
public_summary
demo_chat
summary
```

The default route blocks sensitive Baltor capabilities:

```text
verification
claim.verify
policy
audit_review
context.receipt
private_summary
source_handle.expand
```

## Request Example

Allowed non-commercial demo request:

```json
{
  "task": "context.demo.draft_enhancement",
  "model_policy": {
    "capability": "draft_enhancement",
    "allow_cloud": true,
    "deployment_environment": "demo_noncommercial",
    "commercial_use": "non_commercial"
  },
  "data_policy": {
    "privacy_scope": "public"
  }
}
```

Blocked private request:

```json
{
  "task": "context.demo.draft_enhancement",
  "model_policy": {
    "capability": "draft_enhancement",
    "allow_cloud": true,
    "deployment_environment": "demo_noncommercial",
    "commercial_use": "non_commercial"
  },
  "data_policy": {
    "privacy_scope": "tenant"
  }
}
```

The blocked private request should produce the reason:

```text
low_trust_route_not_allowed_for_private_scope
```

## Baltor Policy

Any output from a free/demo provider enters Baltor as draft context only. Before
promotion into a context pack, it must pass through:

```text
source-handle validation
policy check
prompt-injection scan, when source-derived
claim verification against trusted sources
human review, when risk is non-trivial
context receipt generation by a trusted route
```

This keeps free/non-commercial infrastructure useful for demos while preserving
Baltor's verified-context boundary.
