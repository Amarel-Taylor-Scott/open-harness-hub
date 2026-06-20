# Costed Blueprint Route Matrix

The sentence-to-pipeline product should not emit a single "best" pipeline.
It should emit a route matrix: cheap, balanced, quality-first, and local-first
options with explicit assumptions, cost drivers, trust boundaries, and model
swap points.

This is especially important for high-risk workflows such as human
exploitation triage, public-benefit eligibility, AML alert review, food and
water quality triage, and verified government fact propagation. The user needs
to see the safety gates and human review path before they see provider-specific
model choices.

## Route Shape

Each blueprint option should declare:

- requested task, modalities, and risk tier;
- required guardrails and review queues;
- candidate models or adapters by stage;
- estimated calls, tokens, media operations, cacheable prompt prefix, and
  expected cache hit rate;
- live pricing snapshot identifiers, or a clear simulated-pricing flag;
- deployment target such as local Python, Render, Cloud Run, or private VPC;
- data residency, privacy, and tenant boundary assumptions;
- verified-fact dependencies and refresh policy;
- eval kit, rubric, and A/B test arm.

The matrix is not a substitute for a real production estimate. It is a compact
decision object that lets a user compare tradeoffs before generating Terraform,
MCP setup, queue workers, and runtime configuration.

## Cost Controls

The cheapest credible route usually follows this order:

1. deterministic parsing, redaction, and routing;
2. cheap local or hosted embedding and retrieval;
3. small local or inexpensive model for labeling, reranking, and schema repair;
4. frontier or specialist model only for uncertain, high-risk, or appeal cases;
5. human review for regulated, safety-critical, or low-confidence outputs.

Standardized system prompts, schemas, and guardrail prefixes should be stable
enough to use provider prefix caching when available. The cacheable prefix
must not include tenant secrets, private user content, or volatile facts that
need fresh lookup.

## Million-Object Role

At scale, the route matrix becomes another object factory output. Each generated
blueprint can produce reusable objects:

- route templates;
- model-route records;
- prompt-prefix cache profiles;
- eval arms;
- deployment line items;
- verified-fact dependency records;
- review-ticket routing rules.

Those objects feed search, recommendations, telemetry, and cost optimization.
The platform can then answer questions like "show the cheapest reviewed
pipeline for image-plus-text exploitation triage that keeps images in-region"
or "swap this AML alert review pipeline from a frontier model to a local model
without losing required verification gates."
