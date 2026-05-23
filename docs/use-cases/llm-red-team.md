# Use case 8 - LLM red-teaming

> Prompt-injection + jailbreak + safety probe battery against any LLM endpoint.

## When to use

- Pre-deployment safety review of a custom model
- Quarterly red-team exercise against production endpoints
- Adversarial robustness validation for a fine-tune
- Vendor model selection (compare safety across N model arms)

## Primary pipeline

No single pipeline - assemble from primitives. Eventually:
`pipeline/llm-redteam-suite` (planned).

## Primitives to compose

| Layer | Artifact |
|---|---|
| Input attacks | `rule-pack/grep-prompt-injection-heuristics` (the heuristic battery used by garak's `promptinject`, `latentinjection`, `ansiescape`, `dan`) |
| Secret canaries | `rule-pack/grep-ai-vendor-keys` (planted in the system prompt; check output for leaks) |
| Garak-aligned probes | future `processor/garak-*` set; map to garak probe names |
| Judge | `processor/llm-judge` with a frontier model |
| Hallucination | `processor/hallucination-scorer` |
| Citation | `processor/citation-coverage` |
| Refusal-style | `persona/research-analyst` baseline; compare against custom-persona arms |
| Rubric | `rubric/garak-promptinject` (planned), `rubric/research-entity-v1` (citation-coverage as a proxy) |
| Audit | `processor/audit-trace-emitter` |

## Composition

```
test_prompt
  → grep-prompt-injection-heuristics  (does the prompt LOOK injected?)
  → harness/text-safety-review        (model handles the prompt)
  → grep-prompt-injection-heuristics  (does the OUTPUT leak system prompt or canary?)
  → hallucination-scorer
  → citation-coverage
  → llm-judge (rubric/garak-promptinject)
  → audit-trace-emitter
```

## Sample probe library

Run these against your endpoint and score each:

| Probe | Source |
|---|---|
| `promptinject` | Direct prompt injection - "ignore previous" |
| `dan` | DAN / "do anything now" jailbreaks |
| `latentinjection` | Indirect injection via retrieved doc / tool result |
| `ansiescape` | Terminal escape codes hide payload |
| `grandma` | Social-engineering jailbreak ("grandma used to tell me…") |
| `goodside` | Riley Goodside's classic injections |
| `divergence` | Trigger model to leak training data |
| `dan_jailbreak` | Various DAN variants |
| `system_prompt_extraction` | Get the model to print its system prompt |
| `package_hallucination` | Trick the model into recommending non-existent packages |
| `realtoxicityprompts` | Toxicity continuation tests |
| `malwaregen` | Refuses code-generation for malware |

## Install path

### Standalone (no model host)

```bash
python scripts/run_pipeline.py harness/text-safety-review \
  --inputs '{"messages": [{"role":"user","content":"<probe>"}]}'
```

### Against a specific endpoint

Edit the harness's `model_target` field to point at the endpoint under test:

```yaml
model_targets:
  - id: "endpoint_under_test"
    transport: "openai_compatible"
    endpoint: "https://api.your-prod-endpoint/v1"
    default_model: "your-model-id"
```

## Customization knobs

- **Add probes**: write `knowledge-pack/redteam-probes-<family>` with rows of `{ probe_id, prompt, expected_failure_mode, severity }`.
- **Run a model A/B**: write a `benchmark/llm-redteam-comparison` referencing your pipeline + a probe `dataset/` + the rubric. The emitter produces lm-eval-harness YAML + promptfoo config for cross-tool runs.
- **Continuous red-team**: schedule the pipeline in CI; alert on regression versus the baseline benchmark.
- **Reflexive defense**: feed red-team findings back as new `rule-pack/grep-*` patterns. The catalog grows; the model's defenses get tightened.
