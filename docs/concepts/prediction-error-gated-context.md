# Context efficiency from model heuristics + consumer behavior — the design space

Open-ended question (owner, 2026-06-12): *can we make context compression and
serving more efficient by learning from model heuristics, consumer behavior,
etc.?* Short answer: **yes, strongly — and the repo already holds most of the
pieces.** This doc lays out the space so we can pick directions deliberately
rather than building one thing. The budgeted planner
(`scripts/processors/compression/usage_gated_compress.py`) is ONE worked point
in this space, not the whole answer.

## The premise (from the essay + the neuroscience)

A transformer is stateless: it re-pays the full prefill cost of every context
item on every turn. The brain doesn't — it carries a learned generative model
and spends expensive bits only where prediction FAILS (Raichle's "dark
energy"; Friston's free-energy principle). So the efficiency thesis is:
**stop paying full price to re-stream what the system can already predict; pay
full price only on surprise.** Three things can tell you what's predictable —
model heuristics, the content's own nature, and consumer behavior — and there
are four distinct levers to act on once you know.

## Axis 1 — the SIGNAL (what tells you what to keep)

| Signal | Source | Cost | Cross-turn? | In repo today |
|---|---|---|---|---|
| Attention scores (H2O) | model-internal | high (needs internals) | no (per pass) | — (decoding-phase; doesn't cut prefill) |
| Perplexity / info (LLMLingua) | small model | medium | no (per prompt) | `retrieval/llmlingua_compress` (deterministic proxy) |
| Query relevance (LongLLMLingua) | query+content | low | no | `retrieval/extractive_span_selector`, `mmr_diversity_select` |
| **Usage history** (cited / re-read / changed) | logs | **near-zero** | **yes (learns)** | `compression/usage_gated_compress` (new) |
| Content nature (volatility class, authority, governance tier) | metadata | zero | n/a | `retrieval/source_precedence_select`, `memory/memory_confidence_track` |
| **Consumer behavior** (cohort usage shape) | fleet logs | low | yes | — (gap; see Axis 3) |

The white space is the bottom two: nobody gates compression on **demonstrated
cross-turn usage** or **cohort behavior**. H2O uses attention (internal,
single pass); LLMLingua uses perplexity (internal, single prompt). Both are
blind to "this file gets re-read every turn but never actually cited." That's
the Friston prior, and it's the cheapest signal of all because it's already in
the logs.

## Axis 2 — the LEVER (where the saving comes from), cheapest first

1. **Don't re-send** — cache / KV reuse. The essay's 10× discount.
   *Repo:* `cache/cache_prompt_prefix` (mark the stable prefix), `cache/cache_kv_reuse` (LMCache-style prefix reuse), `cache/cache_exact`, `cache/cache_semantic`.
2. **Send less** — compress the text. Structural (code), learned (prose), extractive (spans).
   *Repo:* `compression/structural_compress`, `retrieval/llmlingua_compress`, `retrieval/extractive_span_selector`.
3. **Send by reference** — replace predictable context with a handle + gist, and **rehydrate only on a prediction miss** (the brain's move: pay full cost only when prediction fails). *Repo:* `compression/usage_gated_compress` (the planner) + `memory/memory_agentic_hierarchy` (the page in/out mechanics).
4. **Persist state** — distill stable context into a durable derived layer so it NEVER re-streams: a CLAUDE.md fragment, an llms.txt surface, or a compiled capability. This is the deepest lever and it IS the Teleon/Baltor thesis — the brain persists weights; we persist *governed derived layers*. *Repo:* `deliver/emit_claudemd_fragment`, `deliver/emit_llms_txt`, the Determinism Factory / compiled-unit registry.

Most of the value is in 1 and 4, not 2. Compression (lever 2) is the obvious
move and the smallest win; caching and persistence are where the order-of-
magnitude lives. The essay's own pricing proves it — the discount is on
*re-reads avoided*, not on *tokens shrunk*.

## Axis 3 — CONSUMER BEHAVIOR (the part the question names, and our gap)

The essay's key observation: the cache ratio is **not stable across users** —
developer-on-big-codebase ≈ 99% re-read, student-one-off ≈ 50/50, consultant
in between. That means the right compression policy is **cohort-dependent**:

- **Power-user / large-repo profile:** a huge stable substrate the model has
  already absorbed → compress the substrate hard (lever 3/4), keep only the
  active working set full. Biggest absolute saving.
- **One-off / fresh-context profile:** almost everything is genuinely new →
  *barely compress* (everything is surprise; the brain wouldn't compress what
  it hasn't seen). Aggressive compression here would *hurt*.
- **Iterating-on-deliverables profile:** a growing artifact + churning edits →
  gate on volatility (re-read what changed, page out what froze).

So the heuristic isn't one curve — it's **a policy selected by the cohort's
usage shape**, then personalized per tenant. Cold-start a new user from the
average prior of similar cohorts, then let their own prediction-miss feedback
specialize it. This is the genuinely new capability and it's a *gap* today —
the planner has the per-item prior but nothing yet learns the *cohort* shape.

## Axis 4 — the LEARNING LOOP (active inference, concretely)

A prediction MISS is the only expensive event: we compressed something away and
the model/user then needed it (re-opened the file, re-asked, cited the handle).
Each miss raises that item's retention; over turns the prior converges to the
user's true working set. Formally this is minimizing **expected free energy** =
(bits served) + (surprise of being wrong about what to keep). The planner
already implements the per-item version (`observe()` re-promotes a cited
handle); the cohort version is the open extension.

## The hard constraint — governance overrides usage for truth

Usage statistics MUST NOT be the only gate, and this is the line where a naive
"compress what's rarely used" policy becomes dangerous: a fact can be **rarely
cited but load-bearing when it is** — a safety constraint, a regulatory
deadline, a signed source of truth. Those are pinned by **governance**, not by
usage (`source_precedence_select`, `memory_confidence_track`, the
`serves_truth` discipline). The lossless law is why the mechanism is
*handle + rehydrate*, never *delete*: a paged-out fact is one reference away,
so a miss costs latency, never correctness. And per-tenant usage priors are
tenant-private lineage — never global (repo law). Compression decisions are
deterministic precisely so a receipt can prove what the model was shown.

## What exists vs. what's missing (so we can choose)

- **Have:** all four levers as individual processors; the per-item usage prior
  + prediction-miss loop (new, validated).
- **Missing / candidate next steps (pick deliberately, don't auto-build):**
  1. a **cohort policy selector** — classify a tenant's usage shape and pick the
     default compression curve (Axis 3);
  2. a **real usage-log miner** — produce the prior from actual Claude-Code-style
     cache/citation logs instead of a synthetic feed;
  3. **wire the planner into the live context-pack path** so handle-only items
     actually page in on a gateway miss (lever 3 end-to-end);
  4. a **persistence promoter** — detect context stable enough to distill into a
     CLAUDE.md/llms.txt layer (lever 4) so it leaves the re-read loop entirely.

Each is a separate, scoped piece. The prototype proves the gate is buildable
and governed; the bigger wins (cohort policies, persistence) are decisions, not
defaults.

## The worked example (one point in the space)

`processor/usage-gated-compress` (`compress.usage_gated`): given context items,
a usage prior, and a token budget, assign each item FULL / SUMMARY /
HANDLE_ONLY by `priority = 0.55·utility + 0.30·volatility + 0.15·recency`
(unseen items = cold-start FULL — novelty is high free energy). Lossless:
paged-out items return with a rehydratable `ctx://` handle; `observe()` folds a
turn's outcome into a new prior and a prediction miss re-promotes the item.
Deterministic, model-external, cross-turn, and it cuts *prefill* — the re-read
cost H2O explicitly can't touch. It is lever 3 with the Axis-1 usage signal;
it is NOT the whole answer.
