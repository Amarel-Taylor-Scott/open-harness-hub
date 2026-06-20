# The model-query template (canonical)

A model query is **not** a string assembled once at the end — it is a **structured template of
named slots** that pipeline steps write into **at any stage**, and that a final render step
serializes into the prompt the model actually sees. This is why "place context in the prompt"
is *not* a single step at the end of polishing: context (and persona, instructions, examples,
schema, tools) is added into slots throughout **Model query enrichment** and **polishing**; the
last step only **renders** the populated template per a placement policy.

See `scripts/showcase/builder.py::harness_recipe` ("Render the model-query template") and
[`retrieval-and-prompt-taxonomy.md`](retrieval-and-prompt-taxonomy.md) (R0–R6 + P1–P5).

## The template (JSON shape)

```jsonc
{
  "persona":            "string|null",        // role/expertise only — NO facts (P1)
  "system_instructions":"string",             // the task contract (P2)
  "constraints":        ["string"],           // hard rules: cite-or-abstain, refusal policy, format
  "citation_policy":    "every_claim|key_claims|none",
  "context_blocks":     [                      // the retrieved/added knowledge — appended by ANY step
    { "id":"c1", "content":"string", "source":"corpus-id#locator",
      "retrieved_by":"bm25|dense|hybrid|exact-id|tool|web",
      "rank":1, "score":0.0, "placement":"head|tail|mid|auto" }
  ],
  "examples":           [ { "input":"…", "output":"…", "kind":"static|knn|cot" } ],  // P3 few-shot
  "tools":              [ { "name":"…", "schema":{} } ],                              // available tool calls
  "user_input":         "string",             // the runtime artifact (the Input ⌖)
  "output_schema":      { },                  // the typed envelope the response is verified against (P4)
  "render":             {                      // the PLACEMENT POLICY (how slots serialize)
    "context_placement":"edge|prepend|append|mid",   // edge ⇒ most-relevant first AND last
    "block_format":"delimited_source_tagged|markdown|plain",
    "instructions_position":"last|first",
    "token_budget": 8000, "dedupe": true, "order":"relevance|chronological"
  },
  "provenance":         [ { "block":"c1", "source":"…", "license":"…", "valid_through":"…" } ]
}
```

## The law: any step can write any slot, at any stage

| Step (phase) | Writes slot(s) |
|---|---|
| Add persona *(enrichment)* | `persona` |
| Build the system prompt *(enrichment)* | `system_instructions`, `constraints`, `citation_policy` |
| Query transform *(enrichment)* | (rewrites the query used for retrieval; may add a `context_block`) |
| Retrieve · Rerank/fuse · online-facts *(enrichment)* | append `context_blocks[]` (+ `provenance[]`) |
| Few-shot *(enrichment)* | `examples[]` |
| Output schema *(enrichment)* | `output_schema` |
| Summarize/compress *(polishing)* | rewrite `context_blocks[].content` (shorter, cited spans kept) |
| Select · order · de-conflict *(polishing)* | prune/reorder `context_blocks[]`, set `render.order`, flag conflicts |
| **Render the model-query template** *(polishing)* | reads the whole template + `render` policy → the final prompt string |

So **context is added wherever it is discovered** (a tool call mid-flow, a corrective re-retrieval
in the loop, an enrichment step) by appending a `context_block` — *not* only at a terminal
"place context" step. Placement is a **property of each block + a global render policy**, applied
once at render time. Edge placement (most-relevant first AND last) + instructions-last is the
default because models attend unevenly across long context ("lost in the middle").

## Why a template, not a string

- **Add anywhere:** any step appends/edits a slot; the corrective loop can inject a fresh
  `context_block` and re-render without rebuilding the prompt by hand.
- **Governed:** every `context_block` carries `source` + `provenance` → per-claim citation and the
  freezable/cited output the product promises (value-prop 2).
- **Swappable render:** the placement policy is a component option (edge / structured / instructions-last),
  not hard-coded — so a bundle can change *how* the same populated template serializes.
- **Verifiable:** `output_schema` is the contract the post-call **Model response verification** checks
  against (Check output → Verify JSON → Re-verify), and the **Model response post-processing** composes
  the typed decision + cited indicators + the full runtime object from it.

## Templated bundles ship a pre-filled template

Each bundle in the taxonomy (Standard hybrid RAG, High-precision legal, …) is, concretely, a
**default model-query template + render policy** with its slots wired to specific components — the
off-the-shelf starting point an engineer then tweaks slot-by-slot. A future schema
(`schemas/model-query-template.schema.json`) will validate these.
