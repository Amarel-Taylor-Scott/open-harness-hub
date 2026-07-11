"""OpenHubForAI — clinical decision-SUPPORT processors (DEFENSIVE only).

This package holds the implementations behind the `_repos/shared-backend-components/catalog/processors/clinical/`
manifests. Shared, non-negotiable stance (each module enforces it structurally):

  * decision SUPPORT, never autonomous action — every output proposes, flags
    or ESCALATES to a clinician; ``disposition: proposed`` and
    ``serves_truth: False`` are pinned in every envelope;
  * the clinical knowledge (interaction tables, dose ranges, reference
    ranges, terminology) is an INJECTED governed corpus — never facts
    hardcoded in this package; the code is the mechanism, the corpus is the
    data, and every hit carries the corpus citation;
  * missing data → ABSTAIN with the reason, never a guess;
  * deterministic; on_error=raise.

Self-test fixtures use small SYNTHETIC demo corpora — they exist to prove the
mechanism and are not clinical reference data.
"""
