# ADR 0005 — Accountability: who owns the outcome when the agent acts

## Status
Accepted (2026-07-04). Supersedes nothing; superseded by nothing.

## Context
The external "regulate agentic AI / accountability designed before deployment" concern asks a question our
schemas did not answer: **who owns the OUTCOME when a capability acts in production?** We already model the
point-in-time gate — `governance/HumanApprovalReceipt` (a human approves a *boundary-expanding change*),
`steward-review-*`, and `PromotionRecord.receipt_id` (the warrant for a promotion). But a grep of the running-
task model found **no owner / escalation / on-failure** binding for a *running* capability. Approval of a change
is not the same as ongoing ownership of what the capability does after it ships. That gap is real.

## Decision
Adopt `schemas/governance/AccountabilityBinding.schema.json` — it binds a running capability (a PurposeTask /
promoted `artifact_key`) to an `accountable_owner`, the `authority` to act before something breaks
(pause / rollback / suspend_autonomy / revoke), an ordered `escalation_path`, an `autonomy_ceiling` (the
adaptation-ladder level it may run at without a fresh approval), and an `on_failure` action. It **reuses**
the `approver_role` vocabulary and the L0–L5 ladder, and **references** (never duplicates) `HumanApprovalReceipt`
+ `PromotionRecord`. Candidate-first per the truth boundary: required for any capability at autonomy ≥ L3 or
serving a paying customer; ratchets to enforced.

## Consequences
"Who owns the outcome" becomes a first-class, enforceable contract — it strengthens the Capability Assurance
Portal and the governance moat, and it is buyer-legible for the exact enterprise concern the market is voicing.
The schema is additive (new file, `governance/` is glob-discovered, no manifest) so there is no blast radius.

## Enforcement / links
Future check: a served capability above its `autonomy_ceiling` without an `active` binding fails. Ties to the
BoundaryApproval / adaptation-ladder invariants in teleon and `HumanApprovalReceipt`.
