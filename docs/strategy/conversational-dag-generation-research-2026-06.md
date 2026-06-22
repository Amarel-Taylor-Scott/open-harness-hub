# Conversational DAG generation — how n8n / Zapier / Dify / Flowise / Langflow do it, and how we compare

Research (2026-06-22) to confirm + guide our capability compiler (`scripts/compile_capability_live.py` +
`src/teleon/synthesis/*`). discovery≠trust — we learn-from, we don't adopt blindly.

## How the incumbents generate workflows from natural language
- **n8n AI Workflow Builder** — NL description → a complete, importable n8n **workflow JSON**, generated against n8n's
  node catalog; real-time feedback "phases"; you review required **credentials/params**; refine via follow-up prompts.
  (The whole graph is generated, then imported + reviewed.)
- **Zapier Copilot** — NL ("when X, do Y, then Z") → a **Zap outline** (trigger + actions); builds **step-by-step**,
  suggests apps/action-events/connected accounts, **asks confirmation before acting**. Known limits (load-bearing for us):
  it **mis-configures** steps and **cannot add paths/branching** — Zaps stay mostly LINEAR.
- **Dify / Flowise / Langflow** — visual **DAG** builders (conditional branches + loops in Dify); components map 1:1 to
  nodes; **Langflow FILTERS eligible components by the clicked port's type** — i.e. it CONSTRAINS the choices to what's
  valid at that point (a UX version of grounding the selection in the real catalog).

## The engineering pattern (from the research)
- **Schema-constrained generation** — compile a JSON Schema → an FSM / grammar; at each token only schema-valid tokens
  are allowed (constrained decoding). Native structured outputs: OpenAI/Anthropic/Gemini/Cohere/xAI; local via Ollama/
  vLLM/SGLang + Outlines / LM Format Enforcer. A *mathematical* guarantee of valid JSON, not statistical.
- **Validation + repair loop** — models still produce edge-case-malformed output; best practice = validate, then **one
  repair retry** with the errors fed back. (`collinwilkins`, `techsy`, `tetrate`.)
- **FlowMind** (arXiv 2602.11782) — "execute-summarize" for structured workflow generation from LLM reasoning.
- **Catalog grounding** — generate against the real node/app catalog; constrain selection to it (Langflow's port filter,
  n8n's node schemas).

## How OUR compiler maps — and where we LEAD
| pattern | them | us (today) |
|---|---|---|
| catalog grounding | n8n node schemas; Langflow port filter | `candidate_pool()` searches the 600+ component INDEX + registries for the intent → the LLM picks ONLY from real components |
| no-hallucination | constrained decoding / 1:1 nodes | `_validate()` REJECTS any invented component (never run) — the registry is the guardrail |
| DAG / branching | Dify yes; **Zapier NO (linear)** | real DAG: nodes + edges + **acyclicity check** |
| iterative refine | Zapier step-by-step; n8n re-prompt | the synthesis tree + **escape strategies** (sprout/reframe) — principled backtracking, not just re-prompt |
| **cost / determinism** | — (they just wire nodes) | **DETERMINISTIC-FIRST**: the descent compiles to the cheapest bounded path; model only for the residual — our wedge |
| **governance** | review credentials | provenance + verify gate + serves_truth + honest-MISSING (Baltor) |

**Our differentiators:** we don't just *build* a workflow — we **compile** it to the cheapest bounded, governed path, with
a real DAG (branching), a hallucination guardrail, and backtracking. Zapier's two weak spots (mis-config, no branching)
are exactly where we're strong (microsteps + per-component test + validation; real DAG edges).

## Concrete ADOPT (confirmed best practices we were missing)
1. **Validation + repair RETRY** — today we reject on parse-fail/hallucination/cycle; add ONE repair retry that feeds the
   errors back to the LLM (the universal best practice). *(implemented this pass.)*
2. **Schema-constrained / structured-output mode** — request native structured output from the lane (Ollama/vLLM grammar)
   so the DAG JSON can't be malformed — upgrade from parse-with-try/except. *(next; via the llm_port.)*
3. **Port/plane-typed candidate filtering** — Langflow-style: filter the candidate pool by what the previous node outputs
   (type-aware composition), not just intent-relevance.
4. **Review-before-run + config correctness** — Zapier's hard part; lean on our microsteps + the per-node test + a
   human/govern confirmation gate before a capability goes tenant-visible (the promotion boundary already does this).
