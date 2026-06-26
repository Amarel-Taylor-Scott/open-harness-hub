# Prompt ABI and token-efficient context

OpenHubForAI should treat repeated system prompts, tool schemas, output
contracts, and verified context-pack headers as runtime assets, not incidental
prompt text. The practical abstraction is a **Prompt ABI**: a canonical,
versioned prefix layout that lets compatible harnesses and pipelines reuse
prompt-prefix and KV-cache work safely.

This is a runtime optimization and a governance contract. It does not create a
new top-level component family. It describes how harnesses, logic packs, tool
schemas, and knowledge packs are compiled into a stable prefix before dynamic
tenant, user, or task data is appended.

Prompt ABI is downstream of the context control loop. A block should become
canonical and reusable only after it has been adversarially validated, checked
for freshness and reconciliation status, scoped for privacy/cache reuse, and
strengthened when a stronger component or verified global context feed exists. See
[[context-control-loop.md]].

## Why it matters

Many enterprise agents repeat the same long scaffolding on every request:

- system policy;
- harness instructions;
- tool schemas;
- output contracts;
- safety rules;
- citation/provenance rules;
- stable context-pack headers.

If those blocks are serialized identically for the same model/tokenizer target,
the serving layer can route requests by prefix hash and reuse prefill/KV work
instead of recomputing it. The logical input may still contain the same tokens,
but repeated prefill compute, time to first token, memory movement, and
provider-side cached-input cost can drop.

The core rule is:

```text
standardized prefix -> shared prefix hash -> safe cache lookup -> lower repeated prefill work
```

## Prefix layout

A token-efficient harness compiles prompts in three layers:

```text
[STATIC CANONICAL PREFIX]
- public harness template
- stable system policy
- stable output contract
- canonical tool schemas
- stable safety and citation rules
- verified context-pack header / corpus map

[ORG / TENANT PREFIX]
- organization policy
- tenant permissions
- approved internal context packs
- tenant-specific tool allowlists

[USER / SESSION / TASK CONTEXT]
- user memory
- current request
- retrieved private documents
- dynamic tool results
- current date and other volatile facts
```

The static layer is the strongest reuse target. The tenant layer can be reused
inside its own boundary. The user/session/task layer is usually private and
volatile, so it must not be globally shared.

## Manifest metadata

Harnesses and pipelines can declare optional `prompt_abi` metadata:

```yaml
prompt_abi:
  version: "ohh-agent-v1"
  canonical_prefix_hash: "sha256:..."
  tool_schema_hash: "sha256:..."
  policy_block_hash: "sha256:..."
  output_contract_hash: "sha256:..."
  context_pack_hashes:
    - "sha256:..."
  cache_scope: "public"
  cacheable_prefix_tokens: 6400
  dynamic_context_boundary: "tenant_context"
  model_targets: ["local_default", "frontier_judge"]
```

The hash should be computed from the canonical serialized blocks plus the
model/tokenizer-sensitive representation used by the runtime. A different model,
tokenizer, tool-schema serialization order, or hidden provider wrapper can
invalidate KV reuse even when the human-readable prompt text is unchanged.

## Cache scopes

Prefix reuse must respect the same privacy discipline as component execution.
The controlled values live in `vocabularies/cache-scopes.yaml`.

| Scope | Reuse boundary | Typical contents |
|---|---|---|
| `public` | Any compatible requester | public OHH templates, public tool schemas, public context-pack headers |
| `org` | One organization | internal policies, approved org-wide tools |
| `tenant` | One customer tenant | tenant rules, private corpus headers |
| `user` | One user/session family | personal memory and preferences |
| `private` | No shared reuse | secrets, raw private documents, sensitive tool results |

The runtime rule is:

```text
reuse allowed only when cache_scope is within requester permissions
```

Cross-user cache hits are valuable only when the cached prefix is intentionally
shareable. Timing and hit-rate side channels should be treated as part of the
privacy threat model.

## Runtime shape

The serving path should compile and route prompts like this:

```text
raw task + selected components
-> canonical prefix builder
-> prefix hash / scope label
-> cache router
-> model/runtime pool
-> trace cache hit rate, saved prefill, and safety decisions
```

Self-hosted deployments can route identical prefix hashes to warm pools with
hot KV state. Provider-backed deployments can still benefit from provider prompt
caching if the static prefix is exactly repeated.

## Measurement

Every token-efficient harness should report:

```text
cache_efficiency = (cacheable_prefix_tokens / total_input_tokens) * expected_reuse_rate

expected_savings =
  p(cache_hit) * saved_prefill_cost
  - canonicalization_cost
  - cache_lookup_cost
  - isolation_overhead
```

The component is worth cache-shaping when expected savings are positive and the
scope/isolation risk is below the deployment's threshold.

## Relationship to speculative execution

Speculative decoding accelerates future tokens. Prefix/KV reuse accelerates past
tokens. Prompt ABI makes repeated past context reusable across users, tenants,
and workloads where the governance boundary allows it.

Future inference hardware is likely to optimize the same substrate before it
hardwires one speculative algorithm:

- prefix hash lookup;
- paged KV movement;
- low-bit KV decode;
- tree/path verification kernels;
- small draft lanes;
- fallback controllers.

That means Prompt ABI is also a hardware-alignment strategy. If OHH components
standardize context layouts now, runtimes and later accelerators have stable
units to cache, route, verify, and meter.

## Product implication

Context Fidelity/Baltor packs should be **verified, current, reconciled,
modular, and token-efficient**:

```text
[stable pack header]
[stable provenance and source map]
[stable verification policy]
[dynamic freshness delta / tenant override]
```

The stable layers are cacheable. The dynamic layers are not. This lets OHH and
Baltor sell more than accurate context: they can sell context that is verified,
current, reconciled, agent-ready, modular across tools and context packs, and
efficient to serve repeatedly.
