# Draft manifest YAML emitter + validator-loop

*processor* · `processor/draft-manifest-yaml-emitter` · v0.1.0 · experimental

Takes a draft manifest (as a Python dict or JSON object emitted by
`harness/draft-manifest-author`), writes it to
`catalog/_inbox/{type}/{slug}.yaml` with stable YAML formatting,
and runs `scripts/validate.py` against the single file.

Behavior:
 - On validation pass: file written; returns success + file path.
 - On validation fail: file written to `catalog/_inbox/_failed/{type}/{slug}.yaml`
   with a sibling `.errors.json` listing every validation error,
   PLUS a structured error report so `harness/draft-manifest-author`
   can revise and retry.
 - Slug-collision check: if a file already exists at the target
   path OR the id collides with an existing live catalog entry,
   emit fails and the structured report includes the conflict
   details.

Idempotent + deterministic when the input dict is identical
(modulo YAML key ordering, which the emitter normalizes).

Hard rule: NEVER writes to live `catalog/{type}/` directly. Only
`catalog/_inbox/` (and the `_failed/` subdir on validation failure).
Curator promotes from `_inbox/` to live after review.

| axis | value |
|---|---|
| industry | software, software.docs, ai, cross_industry |
| capability | format_conversion, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



