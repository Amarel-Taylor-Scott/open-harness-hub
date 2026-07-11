# OpenHubForAI Surface Counts

Updated: 2026-06-09

This page records the current AI Done Right OpenHubForAI design-family counts. Do
not use it as the source of truth; recompute from
`dist/sites/aidoneright-design/shared/products.js` with
`python3 scripts/check_ai_done_right_surface_family.py --self-test`.

## Summary

| Group | Count | Source |
| --- | ---: | --- |
| Parent | 1 | AI Done Right |
| Products | 2 | Baltor, Teleon |
| Live OpenHubForAI registries | 9 | `products.js` layer `open` |
| Private bench hubs | 12 | `products.js` layer `candidate` |
| OpenHubForAI prototype surfaces | 21 | live + private bench |
| Total design-family surfaces | 24 | parent + products + OpenHubForAI registries |
| Operational Demo Control Tower registry surfaces | 20 | `architecture/demo_surface_registry.json` |
| Static launch sites | 7 | `scripts/portfolio_lib.py` |

## Live OpenHubForAI registries

- OpenContextHub
- OpenSkillsHub
- OpenToolsHub
- OpenSkillToTool
- OpenMCPHub
- OpenCompressionHub
- OpenBenchmarkHub
- OpenReviewHub
- OpenHubForAI

## Private Bench Hubs

- OpenTemplatesHub
- OpenEndpointHub
- OpenEnvironmentHub
- OpenSandboxHub
- OpenAgentHub
- OpenReceiptHub
- OpenStateHub
- OpenReconciliationHub
- OpenHardeningHub
- OpenEnrichmentHub
- OpenOptimizationHub
- OpenVerificationHub

## Baltor Method Spine

| Hub | Stage | Hero | Methods |
| --- | --- | --- | --- |
| OpenReconciliationHub | Reconcile | Cluster alignment. | dedupe; link evidence; surface conflicts |
| OpenHardeningHub | Harden | Robust object hardening. | detect fragile values; create objects; refresh over time |
| OpenEnrichmentHub | Enhance | Context enrichment. | add metadata; connect objects; increase robustness |
| OpenOptimizationHub | Optimize | Pack shaping. | summarize; structure; rank |
| OpenVerificationHub | Verify | Cited and provable. | source support; receipt/provenance; verification gates |

Each method-spine hub stays private-first until its `products.js` status flips
to `live`. The private preview banner, muted accent, launch accent, open
standards section, provenance/trust section, account console, README, Control
Tower link, and parent bench card remain required.

## Boundary Reminder

OpenHubForAI registries are discovery surfaces. They do not serve Baltor truth,
do not promote Teleon candidates, and do not execute gated tools from public
pages. Discovery is not trust; benchmark result is not promotion authority.
