# Prompt-engineering repo catalog (the ideation spreadsheet)

A spreadsheet of prompt-engineering-heavy GitHub repos — prompt packs, prompt
optimizers, structured-generation libraries, agentic harnesses, eval/guardrail
frameworks, agent-config standards — to ideate component families from.

## Files

- **`prompt-engineering-repos.csv`** / `.jsonl` — **harvested**: real repos pulled
  from the GitHub Search API by `scripts/acquisition/github_repo_harvester.py`
  across a prompt-engineering query taxonomy. Every row is a repo the API
  returned, with GitHub's own stars / license / topics. Nothing fabricated.
- **`curated-marquee-repos.csv`** — **hand-annotated**: the marquee repos with a
  specific *lift hypothesis* per row (the analysis the raw API rows lack).
- **`summary.json`** — honest counts (total, by family, by camp, ingest-candidates
  vs do-not-ingest).

## Columns

`repo_full_name, url, family, camp, gate, stars, language, license, topics,
description, lift_hypothesis, source, harvested_at`

- **family** — optimizer · structured_generation · harness · eval · guardrail ·
  rag · agent_config · prompt_pack · system_prompt_collection · general_llm.
- **camp** — `engineering` (durable lift: optimizer / structured-gen / harness /
  eval / guardrail) vs `template` (prompt/system-prompt collections: pattern value,
  near-zero catalog lift).
- **gate** — `ingest-candidate` (permissive license) · `ideate · license-review`
  (NOASSERTION/unknown) · `ideate · copyleft-review` (GPL/AGPL) ·
  `reference-only · do-not-ingest (injection/jailbreak)`.

## The principle: mine the engineering, not the prompts

The durable capability-lift is **not** in the prompt text. It's in:
1. **Optimizer layer** — DSPy / GEPA / TextGrad auto-improve + benchmark a
   component; ship every cataloged component with an optimizer-improved, benchmarked variant.
2. **Structured-generation reliability** — Outlines / Instructor / Guidance /
   lm-format-enforcer: schema-aligned, constrained decoding (deterministic_guarantee lift).
3. **Harness architecture** — modular cache-aware system prompts, tool registries,
   approval gates, memory compaction, rollback (reusable patterns, not prompts).
4. **Eval rigs** — the instruments that MEASURE `pipeline_score − bare_model_score`.

Prompt-template packs are **Camp-1**: a useful pattern taxonomy, low as catalog content.

## Hard caveats (governance / safety)

- **Leaked / extracted system-prompt collections are licensing-gray** → `gate =
  reference-only`. Ideation reference, **not** an ingestion source.
- **Never ingest jailbreak / prompt-injection payloads** — they'd poison the catalog
  and create the exact harm the governance moat prevents. The harvester auto-tags
  these `do-not-ingest`. (A *"this component is injection-hardened"* tag is itself a
  candidate capability-lift feature — see `guardrail` family: Rebuff, NeMo-Guardrails.)

## Scaling to 2,000+ (and beyond)

Unauthenticated search is throttled (10/min, 1000 results/query cap). To reach
2,000+ quickly, set a token (30/min, 5000 core/hr) and re-run:

```bash
GH_TOKEN=ghp_xxx python3 -m scripts.acquisition.github_repo_harvester --target 5000 --max-pages 5
```

Add queries to `TOPIC_QUERIES` / `KEYWORD_QUERIES` in the harvester (with star-band
qualifiers like `stars:50..200` to break the 1000/query cap) to widen coverage.
Then score rows against the two-axis gate and feed `ingest-candidate × engineering`
rows into the acquisition queue (`scripts/acquisition/research_queue.py`).
