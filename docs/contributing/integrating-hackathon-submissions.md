# Integrating hackathon submissions as verified-evidence pipelines

This guide explains how to port any Hugging Face Space, Kaggle kernel,
or hackathon submission into the Open Harness Hub catalog as a
verified-evidence pipeline + reusable design patterns. Designed for
contributors and authors who want their work in the registry.

## Why port your submission?

- **Visibility**: every `oh-hub search <topic>` and `oh-hub describe`
  command surfaces matching artifacts to anyone using the catalog
- **Standards-format publication**: one YAML manifest emits to
  Croissant, MCP, Agent Skills, HF model+dataset cards, lm-eval-
  harness, promptfoo, CycloneDX-ML, OpenLineage, C2PA, EU AI Act
  Annex IV, SPDX 3.0 - all 13 emitters work on the same manifest
- **Cross-vertical reuse**: design patterns extracted from one
  submission travel into other verticals (e.g. the
  Two-Stage-Extract-Then-Judge pattern from Bill_info AI now
  references ESG, radiology, contract review, AppSec, and the
  MedLabel medicine-safety pipeline)
- **Citation graph**: every artifact carries an `attribution` block
  with your name + URL + license - discovery and credit are linked

## The 7-step integration recipe

Use Sviatoslav Grabovsky's Bill_info AI integration as the canonical
worked example. It became:

1. `persona/bureaucracy-translator-cite-first` - the action-first,
   cite-first persona with hard rules
2. `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` -
   the 10-criterion fraud taxonomy that grounds the LLM judgment
3. `rule-pack/grep-fake-inkasso-fraud-flags` - deterministic GREP
   detectors for the 10 indicators (first-pass before LLM)
4. `rubric/bureaucracy-translation-quality-v1` - 9-dim grading
   anchored in the published eval (96% extraction / 100% redacted
   refusal)
5. `pipeline/bill-info-extract-fraud-detect-recommend` - the full
   2-stage chain with deterministic validation + critical-tier
   override
6. `dataset/bill-info-test-documents` - reference to the 28-doc
   eval set
7. `adapter/gemma-4-26b-vision` - the multimodal adapter

Plus 3 reusable design patterns extracted from the work:
`pattern/two-stage-extract-then-judge`,
`pattern/critical-tier-output-override`,
`pattern/refuse-on-redacted`.

## Step-by-step

### 1. Persona (1 YAML, ~50 lines)

The persona captures HOW the model should behave for your use case.
Include hard rules - what it ALWAYS does, what it NEVER does, what
it refuses on. Cite the authoritative source for each rule.

```yaml
id: "persona/<your-persona-name>"
type: persona
version: "0.1.0"
name: "..."
description: "..."
system_prompt: |
  You are a <role>. Hard rules:
   - You ALWAYS cite ...
   - You NEVER ...
   - You ALWAYS refuse if ...
role: "..."
domain: ["..."]
```

### 2. Knowledge pack (1 YAML + 1 JSONL data file)

The knowledge pack is the citation backbone. Whether it's
Verbraucherzentrale fraud indicators, ACR Appropriateness Criteria,
MITRE ATT&CK techniques, or drug-interaction references - the rule
is **every authoritative claim cites a knowledge pack entry**.

JSONL format: one line per entry with `id`, `tier` or `severity`, `text`.

### 3. Rule pack (1 YAML, ~12 GREP detectors)

GREP rules are the FIRST PASS - deterministic, fast, transparent.
They fire BEFORE the LLM call. Each rule has:

```yaml
- id: "<rule_id>"
  pattern: "(?i)<regex>"
  severity: "critical" | "high" | "medium" | "low"
  category: "<your_domain>.<failure_mode>"
```

Aim for 10-15 detectors. Critical-tier should be reserved for
findings that should block downstream action.

### 4. Rubric (1 YAML, ~7-10 dimensions)

The rubric is your grading contract. Each dimension has:
- `id`, `label` (human readable)
- `weight` (0-1, sum to 1.0)
- `scale` (typically "0..1")
- `evidence_required` (what the grader looks for)

Anchor dimensions in published eval metrics if you have them.

### 5. Pipeline (1 YAML)

The pipeline chains everything. The canonical 6-step shape:

```yaml
steps:
  - id: "structured_to_prose"
    kind: "processor"
    ref: "processor/structured-to-prose"
  - id: "redact_pii"
    kind: "processor"
    ref: "processor/redact-pii-text"
  - id: "grep_red_flags"
    kind: "rule_pack"
    ref: "rule-pack/<your-grep-pack>"
  - id: "rag_against_authority"
    kind: "rule_pack"
    ref: "rule-pack/hybrid-retrieval-policy"
    inputs:
      corpus: "knowledge-pack/<your-knowledge-pack>"
  - id: "grade"
    kind: "processor"
    ref: "processor/llm-judge"
    inputs:
      rubric_ref: "rubric/<your-rubric>"
  - id: "audit"
    kind: "processor"
    ref: "processor/audit-trace-emitter"
```

### 6. Dataset (1 YAML)

References your eval set. Even if the eval is "small" (Bill_info AI
shipped on 28 documents), publish the dataset shape + provenance.

```yaml
id: "dataset/<your-dataset>"
type: dataset
splits:
  test:
    rows: <N>
    path: "external://github.com/<you>/<repo>/eval/docs/"
record_schema: "schemas/<your-schema>.schema.json"
provenance:
  origin: "..."
  collected_by: "<you>"
  license: "..."
```

### 7. Adapter (1 YAML, optional)

If you use a specific model and other catalog pipelines could benefit
from it, ship an adapter manifest. See `adapter/gemma-4-26b-vision`
for the template.

## Bonus: extract reusable design patterns

If your submission has an architectural insight that generalizes
beyond the specific use case, ship it as a `pattern/` artifact. The
3 patterns Bill_info AI shipped:

- **Two-Stage Extract-Then-Judge** - separate extraction + judgment
  calls because focused criteria don't compete with extraction for
  the model's attention
- **Critical-Tier Output Override** - on critical-tier finding, every
  UI component is FORCED into one consistent message
- **Refuse-on-Redacted** - null over hallucination on missing /
  redacted fields

A good pattern manifest has:
- Structural shape (pseudocode)
- When-to-use vs when-NOT-to-use
- Variants
- Counter-patterns
- Implementing pipelines (which catalog pipelines instantiate this)
- Tradeoffs table (latency / cost / quality / complexity /
  explainability)

## Attribution

Every manifest you contribute carries an `attribution` block:

```yaml
attribution:
  source_url:  "https://huggingface.co/spaces/<you>/<space>"
  source_kind: "huggingface"
  author:      "<Your Name> (<Hackathon>, <Track>)"
  license:     "<Your license>"
```

Authors should list themselves in `authors:` at the top of each
manifest. Open Harness Hub contributors are listed as a SECOND
author for the catalog port specifically.

## How to submit

1. Fork [github.com/Amarel-Taylor-Scott/open-harness-hub](https://github.com/Amarel-Taylor-Scott/open-harness-hub)
2. Create your artifacts in `catalog/personas/...`, `catalog/pipelines/...`, etc.
3. Run `python scripts/validate.py` - must report `all manifests valid`
4. Run `python scripts/build_index_page.py` to refresh `docs/INDEX.md`
5. Open a PR - Taylor + the contributors review for: schema validity,
   attribution correctness, design-pattern reusability, vocabulary
   additions

## Known integrations

- **Bill_info AI** (Sviatoslav Grabovsky, Gemma 4 Good Hackathon -
  Impact Track: Digital Equity & Inclusivity) - refugee bureaucracy
  translation with Verbraucherzentrale-grounded fraud detection.
  Demo: https://huggingface.co/spaces/Svityk/bill-info-ai
- **MedLabel** (Gemma 4 Good Hackathon 2026) - offline-first
  multilingual medicine-safety AI; reads medicine labels and detects
  dangerous drug interactions. The catalog port `pipeline/medlabel-
  photo-to-warning` is a reference shape; author attribution + repo
  URL confirmation pending.

The catalog is intentionally open-author: if your project belongs
here, open a PR.
