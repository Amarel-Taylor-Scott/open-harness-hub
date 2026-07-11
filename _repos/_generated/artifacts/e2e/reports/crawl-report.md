# Crawl report — 2026-06-09T20:06:11.008Z

Crawled 16 running surfaces; 16 passed.

| surface | http | overflow | page errors | dead links | video | screenshots |
|---|---|---|---|---|---|---|
| portfolio_hub | 200 | no | 0 | 0 | videos/crawl-portfolio_hub.mp4 | portfolio_hub-1440px.png<br>portfolio_hub-1280px.png<br>portfolio_hub-390px.png |
| parent_site | 200 | no | 0 | 0 | videos/crawl-parent_site.mp4 | parent_site-1440px.png<br>parent_site-1280px.png<br>parent_site-390px.png |
| teleon_site | 200 | no | 0 | 0 | videos/crawl-teleon_site.mp4 | teleon_site-1440px.png<br>teleon_site-1280px.png<br>teleon_site-390px.png |
| baltor_site | 200 | no | 0 | 0 | videos/crawl-baltor_site.mp4 | baltor_site-1440px.png<br>baltor_site-1280px.png<br>baltor_site-390px.png |
| openharnesshub_site | 200 | no | 0 | 0 | videos/crawl-openharnesshub_site.mp4 | openharnesshub_site-1440px.png<br>openharnesshub_site-1280px.png<br>openharnesshub_site-390px.png |
| opencontexthub_site | 200 | no | 0 | 0 | videos/crawl-opencontexthub_site.mp4 | opencontexthub_site-1440px.png<br>opencontexthub_site-1280px.png<br>opencontexthub_site-390px.png |
| openskillshub_site | 200 | no | 0 | 0 | videos/crawl-openskillshub_site.mp4 | openskillshub_site-1440px.png<br>openskillshub_site-1280px.png<br>openskillshub_site-390px.png |
| opentoolshub_site | 200 | no | 0 | 0 | videos/crawl-opentoolshub_site.mp4 | opentoolshub_site-1440px.png<br>opentoolshub_site-1280px.png<br>opentoolshub_site-390px.png |
| harness_hub_app | 200 | no | 0 | 0 | videos/crawl-harness_hub_app.mp4 | harness_hub_app-1440px.png<br>harness_hub_app-1280px.png<br>harness_hub_app-390px.png |
| baltor_app | 200 | no | 0 | 0 | videos/crawl-baltor_app.mp4 | baltor_app-1440px.png<br>baltor_app-1280px.png<br>baltor_app-390px.png |
| context_is_everything_app | 200 | no | 0 | 0 | videos/crawl-context_is_everything_app.mp4 | context_is_everything_app-1440px.png<br>context_is_everything_app-1280px.png<br>context_is_everything_app-390px.png |
| demo_control_tower | 200 | no | 0 | 0 | videos/crawl-demo_control_tower.mp4 | demo_control_tower-1440px.png<br>demo_control_tower-1280px.png<br>demo_control_tower-390px.png |
| design_bundle_preview | 200 | no | 0 | 0 | videos/crawl-design_bundle_preview.mp4 | design_bundle_preview-1440px.png<br>design_bundle_preview-1280px.png<br>design_bundle_preview-390px.png |
| shared_inference_gateway_surface | 200 | no | 0 | 0 | videos/crawl-shared_inference_gateway_surface.mp4 | shared_inference_gateway_surface-1440px.png<br>shared_inference_gateway_surface-1280px.png<br>shared_inference_gateway_surface-390px.png |
| shared_template_registry_surface | 200 | no | 0 | 0 | videos/crawl-shared_template_registry_surface.mp4 | shared_template_registry_surface-1440px.png<br>shared_template_registry_surface-1280px.png<br>shared_template_registry_surface-390px.png |
| teleon_purpose_task_control_tower_surface | 200 | no | 0 | 0 | videos/crawl-teleon_purpose_task_control_tower_surface.mp4 | teleon_purpose_task_control_tower_surface-1440px.png<br>teleon_purpose_task_control_tower_surface-1280px.png<br>teleon_purpose_task_control_tower_surface-390px.png |

_Review videos: native continuous recording (webm) + mp4 renders via the md5-verified static ffmpeg (owner-authorized download)._

## Skipped (held/planned — honest, not faked)
- **local_event_tracking_service** (planned): gate-specified emulator not yet built; projection/evidence only — NOT the platform event bus and never truth
- **local_ab_test_service** (planned): gate-specified emulator not yet built (note: the design bundle already has client-side A/B in shared/oh-experiments.js — wire, don't duplicate)
- **local_service_account_emulator** (planned): Phase-1 remainder of the service-auth model (scoped local dev tokens; scope violations and revoked tokens fail closed)
- **local_openhub_projection_api** (planned): gate-specified; submissions land in a review queue, never the public-active registry; discovery is not trust
- **local_mcp_registry_service** (planned): gate-specified; add/list/test/revoke MCP connection METADATA without executing tools (Teleon agent_gateway MCP projection exists in src/teleon/agent_gateway — wire, don't duplicate)
- **local_llm_plane_emulator** (planned): src/teleon/inference (OIPS router + receipts) exists as the canonical plane — expose a local deterministic-stub HTTP surface from it; network LLMs stay owner-gated
- **local_receipt_service** (planned): gate-specified; ModelInvocationReceipt + evidence-ledger machinery exists in src/teleon — project it behind a local HTTP surface, don't duplicate
- **local_state_service** (planned): gate-specified; src/teleon/blackboard (local SQLite, append-only) is the candidate substrate — wire, don't duplicate; never truth