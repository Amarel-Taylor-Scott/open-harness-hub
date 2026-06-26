"""OpenHubForAI — response/prompt cache processors (Baltor consumption tier).

This package holds the deterministic implementations behind the
`catalog/processors/cache/` manifests — the cache lane of the context layer
(see `docs/strategy/context-layer-pmf.md`).

Each manifest's `implementations[].path` resolves to a `run(...)` callable here.

Modules:
  cache_exact          — backs processor/cache-exact (process_kind cache.exact_hash):
                         exact-hash response cache keyed by canonical
                         (task, components, inputs); identical runs hit instantly.
  cache_semantic       — backs processor/cache-semantic (process_kind cache.semantic):
                         GPTCache-style paraphrase cache over a deterministic
                         bag-of-words cosine; personalized entries NEVER hit.
  cache_kv_reuse       — backs processor/cache-kv-reuse (process_kind cache.kv_reuse):
                         LMCache-style KV-prefix reuse plan for self-hosted
                         inference (longest shared token prefix).
  cache_prompt_prefix  — backs processor/cache-prompt-prefix (process_kind
                         cache.prompt_prefix): mark the stable prompt prefix for
                         provider prompt caching (Anthropic cache_control /
                         OpenAI automatic >1,024-token prefix).
"""
