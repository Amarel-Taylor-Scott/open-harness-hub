<!-- Thanks for contributing! -->

## What this PR changes

<!-- One paragraph plain-language summary. -->

## Type

- [ ] New artifact (harness / pipeline / rule-pack / knowledge-pack / tool / processor / persona / adapter / rubric / dataset)
- [ ] Update to existing artifact
- [ ] Taxonomy / SPEC change
- [ ] Schema change
- [ ] Emitter / tooling change
- [ ] Documentation
- [ ] Other

## Checklist

- [ ] `python scripts/validate.py` passes
- [ ] `python scripts/build_catalog_index.py` runs without errors
- [ ] `python scripts/emit/all.py` runs without errors
- [ ] If this PR adds an artifact: it has a `license` from an SPDX-compatible list (MIT, Apache-2.0, CC-BY-4.0, CC0-1.0, BSD-3-Clause, …)
- [ ] If this PR adds an artifact: industry / capability / modality tags come from the controlled vocabularies in `vocabularies/`
- [ ] If this PR changes a harness or pipeline that touches health data: `data_protection.hipaa_safe_harbor_categories` is declared (when appropriate)
- [ ] If this PR adds a high-risk artifact: `eu_ai_act_risk: high_risk` is set so the Annex IV dossier is generated
- [ ] If sample data is included: it is synthetic / composite (no real PII)
- [ ] If promoting to `stable`: a sample run is committed under `samples/`

## Linked issues

<!-- Closes #123 / Related to #456 -->
