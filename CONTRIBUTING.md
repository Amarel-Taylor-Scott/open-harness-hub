# Contributing to Open Harness Hub

Welcome! The hub grows by contributions. There are two ingest paths
(see [SPEC §12](taxonomy/SPEC.md#12-ingest-paths)):

1. **Direct PR** — write a manifest by hand.
2. **Reference port** — generalize a pattern from an existing
   permissively-licensed harness repo into a hub manifest, with full
   upstream attribution.

## Direct PR workflow

```bash
# 1. Scaffold.
python scripts/new.py harness my-new-thing

# 2. Edit the YAML — fill in description, model targets, privacy
#    boundaries, applied layers, packs consumed/emitted.
$EDITOR catalog/harnesses/my-new-thing.yaml

# 3. Validate.
python scripts/validate.py

# 4. Rebuild catalog docs.
python scripts/build_catalog_pages.py

# 5. Smoke test locally.
mkdocs serve   # http://127.0.0.1:8000
python scripts/run_pipeline.py pipeline/your-pipeline --simulate

# 6. Open a PR.
```

CI runs `scripts/validate.py` on every PR. PRs that fail validation
cannot merge.

## Lifecycle promotion

- An artifact enters at `experimental`.
- To promote to `beta`: external review + at least one sample run
  committed alongside the manifest.
- To promote to `stable`: at least one benchmark referencing the
  artifact, and the manifest must be semver-stable.
- To deprecate: declare `superseded_by` + `deprecated_on`.

## Style guide

- Be concrete in the description. "Classifies recruitment-fraud risk
  level for migrant job offers" is better than "Safety classifier."
- Always declare an explicit privacy boundary, even when it's local.
- Always declare at least one model target, even if `transport: none`.
- For multimodal pipelines, declare `output_safety_packs`,
  `style_packs`, `physics_packs` as appropriate.

## Industry-agnostic by default

The hub stays generic. Industry-specific concepts go in via:

- A `corridor_profile` style fact pack is a kind of `entity_signal`.
- A `medication_interaction` rule is a kind of `classifier_rule`.
- A `cve_signature` is a kind of `grep_rule`.

If a new top-level concept is genuinely needed, open an issue with
the proposal before opening a PR.
