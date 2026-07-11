# Numeric preference graph for adapter selection (non-fragile)

**Date:** 2026-06-06. **Owner direction:** "I have hard-coded roles like candidate and fallback; it would be
better to have some sort of graph representation of prioritizations and fallbacks and alternatives, that are
numeric in nature ... numeric and non-fragile."

## The problem (it bit us twice on 2026-06-06)

Adapter selection in the External Capability Catalog was gated on **hard-coded role strings**
(`primary`/`fallback`/`stub`) and **exact provider-name matches**. Both are fragile magic values
(`_repos/shared-backend-components/docs/codex/no-magic-values.md`):

1. Setting an adapter's `role` to `"candidate"` was rejected — `candidate` is a *status*, not one of the
   five legal role strings. The role/status string vocabularies are easy to confuse and brittle to extend.
2. Enriching a provider string from `"LLMLingua"` to `"LLMLingua / LLMLingua-2"` broke
   `check_optimization_harness`, which matched the name **exactly**.

Selection should not hinge on whether two strings are byte-identical.

## The model — numbers, not strings

`_repos/baltor/backend/src/baltor/runtime/registry/preference_graph.py` makes selection **numeric**:

- Each adapter carries a numeric **`priority`** (higher = more preferred).
- **Order = priority descending**, then healthy-first, then a stable `adapter_id` tie-break. No role-string
  gating, no exact-name match — only the numbers (plus optional availability/health) decide.
- **Graph view:** adapters are **nodes**; consecutive nodes are joined by an edge that is `falls_back_to`
  when the priority gap exceeds `TIE_BAND` (5), or `alternative_of` when they're within it (interchangeable).
  The edge **weight** is the numeric priority delta. The order is monotone-non-increasing in priority, so the
  graph is **acyclic by construction**. `primary` = the top node; `alternatives` = each tie-band group.

```
nodes:  headroom(78) ──falls_back_to(8)──► llmlingua(70) ──falls_back_to(50)──► stub(20)
order:  [compression.headroom@v1, compression.llmlingua@v1, compression.stub@v1]
```

## Why it's non-fragile (proven by `check_preference_graph_numeric`)

- **Renaming a provider string does not reorder anything** — order depends on numbers, not names (the exact
  failure above can't recur).
- **An unknown or missing role never raises** — it derives priority `0` and sinks to the bottom.
- **Explicit numbers override coarse role labels** — e.g. the reversible **Headroom** compressor (role
  `fallback`, `priority: 78`) correctly ranks **above** LLMLingua (role `primary`, `priority: 70`), because
  reversible compression is the better lossless-law fit. The role label no longer dictates preference.
- **Gradual migration / backward-compatible** — roles remain *advisory* labels. When an adapter declares no
  `priority`, one is derived from its role (`ROLE_DEFAULT_PRIORITY`: primary 80 · fallback 50 · stub 20 ·
  foil/reference 0). So existing slots keep working unchanged; add explicit numbers only where the
  role-derived default is wrong.

## API

```python
reg = CapabilityRegistry()
reg.preference_order("compression")          # adapters, numeric desc (optionally health/available-filtered)
reg.preference_graph("compression")          # {nodes, edges, order, primary, alternatives, acyclic}
```

Consistent with the **execution-backend selector**, which already ranks backends by a numeric **pricebook**
(cheapest wins) rather than by labels — same principle, one mental model: *prefer by number, fall back by
number, treat near-equals as alternatives.*

## Migration path (tracked, not done in one big bang)

- ✅ Numeric layer + graph + proof (additive; nothing removed).
- ✅ First slot annotated with explicit priorities: `compression`.
- ◻ Annotate the other adoptable slots with explicit `priority` where role-derived defaults are wrong.
- ◻ Move `replacement_candidates` and any role-string gating onto `preference_order` (keep roles as labels).
- ◻ Project the preference graph on `/fleet` (or a `/providers` panel) so the numeric prioritization is visible.

*Warrant: clear owner intent (numeric, non-fragile). Additive + capability-encapsulated; the legacy role
fields and all existing proofs stay green (307/307). No magic-string selection on the new path.*
