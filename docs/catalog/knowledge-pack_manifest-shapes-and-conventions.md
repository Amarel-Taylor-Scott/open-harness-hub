# Open Harness Hub manifest shapes, schemas & conventions reference

*knowledge-pack* · `knowledge-pack/manifest-shapes-and-conventions` · v0.1.0 · experimental

In-catalog reference pack distilling the OHH manifest shapes for
use by `persona/manifest-author` and `harness/draft-manifest-
author` when generating draft manifests from external knowledge
trees.

Contents:
 - **Schema summaries**: one-page distillation of each of the 14
   component schemas under `schemas/*.schema.json` — required
   fields, optional fields, validation gotchas.
 - **Envelope conventions**: id format, slug rules, semver,
   license defaults, lifecycle progression, attribution.
 - **Vocabularies in-context**: industries (52+ top-level with
   sub-industries), capabilities (~25), modalities (7), leaf-
   types (40+), lifecycle (4), lifecycle-position (12+).
 - **Pattern library**: 20+ "canonical example" snippets — one
   well-formed harness, pipeline, rule-pack (each family), tool,
   rubric, etc. — to ground few-shot generation.
 - **Hard rules from AGENTS.md + SPEC.md §5**:
   · Pipeline never wires raw rule packs to a model.
   · Volatile facts go in tools/knowledge packs, not personas.
   · Every harness declares model_targets (even if `none`).
   · Privacy boundaries travel with the component.
   · Reproducibility is first-class.
   · Industry-specific concepts as leaf instances, not top-level.
 - **Curator-review etiquette**: drafts go to `catalog/_inbox/`;
   curator promotes to live `catalog/{type}/` after review.
 - **Anti-patterns to avoid**: slug-collision, attribution-
   stripping, vocabulary-explosion, missing-required-field,
   placeholder text ("TODO", "FIXME", "lorem ipsum") in shipped
   manifests.

Intended consumers:
 - `harness/draft-manifest-author` (in-context schema reference)
 - `persona/manifest-author` (system-prompt grounding)
 - Human contributors (browsable doc page)

This pack must be REGENERATED whenever schemas/ or vocabularies/
change. The CI workflow `validate.yml` should add a check that
this pack's version matches schemas/*.schema.json + vocabularies/
hashes (TODO; tracked in repo issues).

| axis | value |
|---|---|
| industry | software, software.docs, ai, cross_industry |
| capability | retrieval, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



