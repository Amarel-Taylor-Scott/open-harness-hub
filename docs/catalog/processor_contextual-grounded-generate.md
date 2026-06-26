# Contextual AI Grounded Generate adapter (GLM — grounded LLM with inline attributions)

*processor* · `processor/contextual-grounded-generate` · v0.1.0 · experimental

GOVERNED ADAPTER that WRAPS Contextual AI's hosted Grounded Language
Model (`POST /v1/generate`) as an OpenHubForAI processor component.
This is a thin wrapper over a third-party best-of-breed engine — OHH
does NOT rebuild it. The GLM takes `messages[]` plus a `knowledge[]`
array, prioritizes the supplied retrievals over its parametric memory,
emits inline attributions, and supports `avoid_commentary`. It scores
88% on Google's FACTS grounding benchmark (vs Gemini 2.0 Flash 84.6%,
Claude 3.5 Sonnet 79.4%, GPT-4o 78.8%) — a strong grounded-generation
engine.

WRAP, NOT REPLACE — and a precise distinction OHH leads with:
grounding != lift. Contextual's GLM produces answers FAITHFUL to the
retrieved documents (grounding). It does NOT measure, and does not
claim, the accuracy LIFT a component-over-a-corpus adds versus the same
bare model. What OHH adds ON TOP of the external engine:
  - PROVENANCE: the `knowledge[]` this adapter is fed comes from a
    GOVERNED corpus (signed publisher / verified source / freshness-
    tracked), so "grounded" means grounded in provenance-carrying
    content — not merely faithful to whatever was ingested.
  - MEASURED-LIFT ADMISSION: admitted only when paired measurement
    (`scripts/foundry/measure.py`) shows a positive, STRUCTURAL lift
    (`scripts/eval/reason_codes.py`) from a SEPARATE evaluator — never
    by the vendor's model-vs-model factuality number alone.
  - COMPOSITION: slots into the seven-primitive grammar as an API-stage
    Action, interchangeable at the schema boundary with OHH's
    deterministic anti-hallucination pre-pass + governed-source path.

DETERMINISTIC / LOCAL FALLBACK: when no Contextual credentials are
configured, the pipeline falls back to
`processor/faithful-extract-before-model` — OHH's deterministic
extract-before-model anti-hallucination pre-pass that injects
machine-readable facts verbatim before any local model call. The hosted
GLM is a stronger grounded generator; the local path guarantees zero
hallucination on extractable fields offline.

Hosted engine, external trust boundary, external_call side effect:
routed to the external-metered worker pool (see
docs/architecture/component-execution-and-runtime-routing.md). Requires
a Contextual AI API key. Cost (Contextual list pricing, 2026): $3 per M
input tokens / $15 per M output tokens — metered per call.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | generation, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | proprietary-saas-wrapped |



