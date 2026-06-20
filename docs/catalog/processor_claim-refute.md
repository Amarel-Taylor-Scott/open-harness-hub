# Claim refute (adversarially try to refute a claim; default to refuted-if-uncertain)

*processor* · `processor/claim-refute` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. The SKEPTIC: instead of asking "can I find support
for this claim", it adversarially tries to REFUTE the claim, and DEFAULTS TO
refuted-if-uncertain. The burden of proof sits on the claim, not on the doubter.
This encodes the contract rule that no agent grades its own work
(docs/codex/change-verification-contract.md, "the verifier's duty"): the
refuter is a distinct adversarial step, separate from whatever produced the
claim.

WHY THIS AXIS: a confirmation-seeking verifier rewards plausible-sounding
output and is exactly how confident-but-wrong answers survive review. Inverting
the objective — actively search the governed evidence for a reason the claim is
FALSE, stale, or unsupported, and treat "no decisive support found" as a
refutation rather than a pass — is the structural defense a faithfulness check
does not provide.

Procedure (deterministic over governed inputs):
  1. Enumerate refutation grounds against the claim, each backed by a
     source_record (see schemas/source-record.schema.json):
       - direct_contradiction — an authority asserts the opposite;
       - superseded — a later authoritative version replaced the basis;
       - unsupported — no governed source actually supports the claim;
       - out_of_scope — the cited source does not cover the asserted field.
  2. Apply the burden-of-proof rule: the claim is UPHELD only when governed
     evidence affirmatively supports it AND no refutation ground stands. If
     support is absent, weak, or uncertain, the verdict is REFUTED — the
     default is not "benefit of the doubt".
  3. Emit a verdict: upheld | refuted | refuted_uncertain, with the warrant
     (the strongest refutation ground and its source, or the affirmative
     support that survived). A refuted or refuted_uncertain verdict on a
     gating field opens a review_ticket / blocks promotion rather than serving
     the claim.

This processor adjudicates over evidence already gathered (e.g. by
processor/web-search-verify and processor/authority-fetch-diff) and is itself a
local, read-only, deterministic decision — it makes no external calls.

GOVERNANCE (honest framing): this is a governed DEFINITION of an adversarial
refutation policy, not a measured-lift claim. It describes the refutation
grounds, the refuted-if-uncertain default, and the deterministic warrant per
verdict. It does NOT assert a populated refutation or error-catch number, and
it does NOT manufacture grounds it cannot tie to a governed source.

| axis | value |
|---|---|
| industry | cross_industry, ai, government.regulatory, legal.compliance |
| capability | verification, safety, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| freshness | volatile |
| license | Apache-2.0 |



