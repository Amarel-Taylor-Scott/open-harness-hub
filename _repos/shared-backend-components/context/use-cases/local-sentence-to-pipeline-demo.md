# Local Sentence-To-Pipeline Demo

The simplest demo should be a downloadable local Python app.

The user types a sentence such as:

> Build me an LLM pipeline that intakes a photo plus description and processes
> it in the cheapest way possible to classify whether it may relate to human
> exploitation.

The app returns a blueprint, not a generic answer.

## Demo Flow

1. Parse the sentence into task, modality, risk, budget, hosting, and review
   constraints.
2. Search the local registry for harnesses, tools, rule packs, guardrails,
   evals, and deployment patterns.
3. Generate cheap, balanced, and quality-first pipeline options.
4. Estimate model, embedding, search, storage, and human-review costs.
5. Attach safety gates, eval kits, A/B test plans, and review tickets.
6. Export `pipeline.yaml`, `runtime.yaml`, `cost-estimate.json`,
   `eval-plan.yaml`, and optional Terraform/MCP setup files.
7. Emit tenant-private normalized records for model routes, prompt-prefix cache
   profiles, pricing stubs, eval arms, verified-fact dependencies, and review
   rules.

The demo should run in simulate mode without API keys. With user-provided keys
or local model endpoints, it can execute selected stages.

## Guardrail Registry

The demo should treat guardrails and eval kits as first-class components:

- restricted-content gates;
- PII and sensitive-data screening;
- source-governance rules;
- citation checks;
- human-review routing;
- false-positive and false-negative eval sets;
- cost and latency A/B tests.

For high-risk classes such as exploitation or abuse detection, the pipeline
should classify risk and route to review without generating explicit harmful
content, descriptions, or transformations.

## Verified Fact Updates

Some pipelines depend on volatile facts. For example, if the Philippines
government changes employment agency fee rules, every dependent pipeline should
know that the relevant fact object changed.

The platform needs:

- verified publisher intake;
- signed or attested fact objects;
- effective dates and jurisdiction;
- dependency edges from pipelines to fact objects;
- impact analysis when a fact changes;
- automatic review tickets for affected pipelines;
- optional redeployment or bundle regeneration.

The local app can show this in simulate mode: ingest a signed government fact
update, find dependent pipelines, and produce an update plan.

## Output Records

Every simulated run should be able to produce records that later become
searchable primitives. The public catalog should store only synthetic examples
or curated components; private prompts stay tenant-private and are represented by
hashes, route metadata, guardrails, and review state.

The record path is described in
[`local-blueprint-record-persistence.md`](../architecture/local-blueprint-record-persistence.md)
(which absorbed the local-blueprint-output-records plan).

## Why This Is Useful

The value is not only pipeline generation. It is the ability to combine:

- a local/private registry;
- cost-aware model routing;
- guardrails and eval kits;
- signed facts and source updates;
- deployable runtime blueprints;
- repeatable A/B testing of cost and quality.

This is the product wedge: users can start locally, then move to hosted search,
private registries, managed workers, verified publishers, and deployment
automation.
