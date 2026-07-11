# Contextual AI LMUnit adapter (natural-language unit-test judge → 1-5 score)

*processor* · `processor/contextual-lmunit-judge` · v0.1.0 · experimental

GOVERNED ADAPTER that WRAPS Contextual AI's LMUnit evaluation model
(`POST /lmunit`) as an OpenHubForAI processor component, selectable
as the judge model behind OHH's `processor/llm-judge` and the rubric
tree. This is a thin wrapper over a third-party best-of-breed engine —
OHH does NOT rebuild it. LMUnit takes {query, response, unit_test}
(<=7000 tokens) and returns a continuous 1-5 score for that natural-
language unit test. It beats GPT-4o / Claude 3.5 as a judge on scoring
unit tests (RewardBench2 82.1% top-2, RewardBench 93.5% top-5, SOTA on
FLASK / BigGenBench) and is the highest-value wrap of the four:
Contextual open-sourced it in Jul 2025 (`ContextualAI/LMUnit`;
`LMUnit-llama3.1-70b`, `LMUnit-qwen2.5-72b` on Hugging Face;
arXiv:2412.13091), so it can run hosted OR self-hosted.

WRAP, NOT REPLACE — and the distinction OHH leads with: LMUnit grades
ANSWER QUALITY (it is the judge); it does NOT measure the LIFT a
pipeline-over-a-corpus adds versus the same bare model, and it carries
no will-it-survive-the-next-model durability axis. What OHH adds ON TOP:
  - LMUnit is the JUDGE MODEL, not the gate. OHH's two-axis admission
    gate (`scripts/foundry/measure.py` paired pipeline-vs-bare +
    `scripts/eval/reason_codes.py` durability_class) sits ABOVE it; the
    judge's 1-5 score is an input to that gate, not a substitute for it.
  - PER-DOMAIN RUBRICS: OHH's ~230 scored rubrics + verify family supply
    the domain-specific unit tests LMUnit scores; LMUnit is one general
    judge, the rubrics are the governed criteria.
  - PROVENANCE & COMPOSITION: scores attach to the governed pipeline run
    and slot into the seven-primitive grammar as a post-API evaluation
    Action.

DETERMINISTIC / LOCAL FALLBACK: when no Contextual credentials are
configured, the pipeline falls back to `processor/llm-judge` (generic
LLM-as-judge over local/frontier model targets, with deterministic
fallback). LMUnit is a stronger judge engine; the local judge keeps
evaluation runnable offline.

Hosted engine, external trust boundary, external_call side effect:
routed to the external-metered worker pool (see
context/backend/architecture/component-execution-and-runtime-routing.md). Requires
a Contextual AI API key for the hosted path (the open weights can run
on the local model tier). Cost (Contextual list pricing, 2026): $3 per
M input tokens — metered per call.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | proprietary-saas-wrapped |



