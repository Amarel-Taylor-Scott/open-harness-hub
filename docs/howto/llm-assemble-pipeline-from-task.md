# Getting started: assemble a pipeline from a task description

A common ask: "I have a task. The catalog has 500+ artifacts. Which ones do I need?"

The catalog ships a scaffolding script that takes a free-text task description, searches the catalog for relevant components, and emits a draft pipeline manifest. The script is meant for two audiences:

1. A developer poking around for the right components.
2. An LLM agent asked to assemble a pipeline from the catalog (give the agent the JSON output).

## Three search modes

| Flag | Mode | When to use |
|---|---|---|
| _(none)_ | **Lexical** — token overlap (default fallback). | Quick local lookup with no sidecar. Works out of the box. |
| `--semantic` | **Semantic** — cosine similarity against precomputed sentence-transformers embeddings. | When your task description doesn't share keywords with manifest descriptions (e.g. "find code that helps me triage UGC"  →  best hit is `pipeline/platform-content-triage`, no shared tokens). |
| `--hybrid` | **Hybrid** — `0.55 * semantic + 0.45 * lexical + edge-aware boost`. **Recommended.** Top-pipeline siblings get a `+0.10` boost so components that already ship together surface together. | The default for any non-trivial assembly. |

Semantic + hybrid require the embeddings sidecar to be built once:

```bash
pip install sentence-transformers
OH_BUILD_EMBEDDINGS=1 python3 scripts/build_catalog_db.py
```

Hybrid gracefully falls back to lexical if the sidecar isn't present, so the script is always usable.

## Quick start

```bash
python3 scripts/scaffold_pipeline_from_task.py --hybrid "Review a vendor invoice for fraud signals + extract line items"
```

Output (abridged):

```
Task: 'Review a vendor invoice for fraud signals + extract line items'

Found 24 relevant artifacts across 8 types.

== persona (3 hits) ==
  [0.61] persona/bureaucracy-translator-cite-first
         Bureaucracy translator (cite-first)
         matched: bill, document, extract, fraud

== rule-pack (4 hits) ==
  [0.72] rule-pack/grep-fake-inkasso-fraud-flags
         Fake-Inkasso fraud flags
         matched: extract, fraud, invoice, signals

== knowledge-pack (2 hits) ==
  [0.55] knowledge-pack/verbraucherzentrale-fake-inkasso-indicators
         Verbraucherzentrale fake-Inkasso 10-indicator taxonomy
         matched: fraud, signals

== rubric (2 hits) ==
  [0.49] rubric/bureaucracy-translation-quality-v1

== Draft pipeline (use --draft-yaml to emit YAML) ==
Steps: 6
  - structured_to_prose       processor/structured-to-prose
  - redact_pii                processor/redact-pii-text
  - grep_red_flags            rule-pack/grep-fake-inkasso-fraud-flags
  - rag                       rule-pack/hybrid-retrieval-policy
  - grade                     processor/llm-judge
  - audit                     processor/audit-trace-emitter
```

## Get the draft YAML

```bash
python3 scripts/scaffold_pipeline_from_task.py \
  "Triage user-generated content for illicit signals on a social platform" \
  --draft-yaml > /tmp/my-pipeline.yaml
```

Then refine the draft, validate it, and you have a working pipeline.

## Use it from an LLM agent

```bash
python3 scripts/scaffold_pipeline_from_task.py "..." --json > /tmp/catalog-hits.json
```

The JSON has the shape:

```json
{
  "task": "...",
  "hits_by_type": {
    "persona": [{ "id": "...", "score": 0.61, "matched_tokens": [...], "name": "...", "description": "...", "path": "..." }],
    "rule-pack": [...],
    "knowledge-pack": [...],
    "rubric": [...]
  },
  "draft_pipeline": { ... full pipeline manifest ... }
}
```

Feed it to your agent with a prompt like:

> Here is a task and a set of catalog hits. Compose a working pipeline.yaml using only artifacts that exist in `hits_by_type`. Refine the `draft_pipeline` if needed; never invent artifact IDs.

The "never invent artifact IDs" constraint is important. The script gives the agent a closed set of real IDs to compose from, which prevents fabricated references that would fail validation.

## Validation loop

```bash
# 1. Get the draft.
python3 scripts/scaffold_pipeline_from_task.py "..." --draft-yaml > catalog/pipelines/mine/draft.yaml

# 2. Edit it (rename, add real inputs/outputs, tag).
$EDITOR catalog/pipelines/mine/draft.yaml

# 3. Validate against schemas.
python3 scripts/validate.py

# 4. If it has clean+flagged samples, add them to scripts/bench_pipelines.py.
```

## Real example — human-trafficking UGC triage with Gemma 4

```bash
python3 scripts/scaffold_pipeline_from_task.py --hybrid \
  "Detect illicit social media posts related to human trafficking on user-generated content platforms with Gemma 4" \
  --draft-yaml
```

Output picks all the right pieces automatically:

- `persona/trust-and-safety-reviewer`
- `adapter/gemma-4-26b-vision` (multimodal — handles both post text and attached images)
- `rule-pack/grep-human-trafficking-ugc-flags` (18 GREP detectors from the Polaris + ILO taxonomies)
- `rule-pack/classifier-trafficking-signal` (10 Polaris-typology classifier slots, second-stage)
- `rule-pack/grep-platform-moderation-flags` (kept for the CSAM-route short-circuit)
- `pattern/two-stage-extract-then-judge`, `pattern/refuse-on-redacted`, `pattern/critical-tier-output-override`
- `rubric/platform-moderation-quality-v1`

The composer correctly slots the GREP pack as the early triage step and the classifier pack as the second-stage judge — different `family` values flow into different positions in the pipeline. See [Human-trafficking signal triage](../use-cases/human-trafficking-ugc-detection.md) for the full pipeline.

## Underneath: the catalog DB

The script reads from `dist/catalog.sqlite`, a derived SQLite database with three useful tables:

- `artifacts` — id, type, name, description, license, lifecycle, etc. (one row per manifest)
- `artifacts_fts` — FTS5 full-text index over name + description + tags + industry + capability
- `edges` — typed adjacency (`uses_rule_pack`, `uses_persona`, `step_ref`, etc.) used for the hybrid-mode edge-aware boost
- `embeddings` — optional, populated only when `OH_BUILD_EMBEDDINGS=1` is set

YAML stays the source of truth; the DB is a derived build artifact, regenerated from the YAML on every push.
