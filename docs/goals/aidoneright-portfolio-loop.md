# AI Done Right - Portfolio Improvement Goal

Use this file as the long goal for Codex / Claude Code Max. The `/goal`
command should only point here, for example:

```text
/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md
```

## Mission

Improve and polish all aspects of the AI Done Right portfolio:

- AI Done Right parent / portfolio site
- Baltor governed-context product
- Teleon purpose-defined capability runtime
- all live Open*Hub registry sites
- all private bench hubs
- the full Baltor method spine:
  - OpenReconciliationHub
  - OpenHardeningHub
  - OpenEnrichmentHub
  - OpenOptimizationHub
  - OpenVerificationHub
- Demo Control Tower
- Shared Inference Gateway
- Shared Template Registry
- Teleon PurposeTask Control Tower
- README / HANDOFF / CLAUDE / START-HERE docs
- production-readiness docs
- service-to-service auth, API keys, service accounts, secret refs, and access boundaries

Work one useful, proof-backed increment per cycle. Do not end a cycle on
diagnosis only.

## Product Positioning Law

AI Done Right is the parent/platform brand.

Baltor governs context: source handles, reconciliation, verification, freshness,
hardening, enrichment, optimization, safe consumption, receipts, provenance, and
truth governance.

Teleon runs capabilities: CapabilityTask / PurposeTask, runtime selection,
execution backends, candidate paths, scorecards, evidence ledgers, promotion
gates, rollback, local emulators, provider adapters, and boundary approvals.

Open*Hubs are registries and discovery surfaces: discovery is not trust,
candidate is not active, benchmark result is not promotion authority, and
Open*Hubs are not truth authorities.

Shared internal surfaces are projection/control surfaces: Shared Inference
Gateway, Shared Template Registry, Demo Control Tower, Teleon PurposeTask
Control Tower, and future service-auth/control-plane surfaces.

Dependency law:

- Baltor may depend on Teleon.
- Teleon may consume Open*Hub resources.
- Open*Hubs do not depend on Baltor truth.
- Baltor governs truth.
- Teleon runs capabilities.
- Dashboards are projection-only.

## Non-Negotiable Guardrails

Do not:

- commit
- push
- pip install
- npm install that mutates dependency state
- deploy real cloud
- use paid providers
- use production secrets
- call network LLMs unless explicitly authorized
- run live third-party diagnostics unless explicitly authorized
- make public accusations
- create fake URLs
- put raw API keys in config, HTML, logs, receipts, screenshots, docs, or prototypes
- let dashboards write truth
- make Open*Hubs truth authorities
- let LLM output become truth
- let agent output become truth
- let benchmark result promote a candidate
- create a second durable ledger
- create a second event bus
- create a second LLM wrapper
- create a second worker framework
- use broad `pkill`

If a real provider, SDK, key, service account, cloud backend, container, or owner
authorization is missing:

- build or document the local equivalent
- mark the real provider as candidate or HELD
- prove graceful degradation where possible
- continue with safe work

## Reading Order

Read these first if present:

- README.md
- START-HERE-CLAUDE-CODE.md
- HANDOFF.md
- CLAUDE.md
- CLAUDE-CODE.md
- MARKETING.md
- POSITIONING-AUDIT.md
- BACKEND-STACK.md
- UX-BACKLOG.md
- EXPERIMENTS.md
- products.js

Then inspect shared design/system files if present:

- shared/oh-tokens.css
- shared/oh-components.css
- shared/oh-site.css
- shared/oh-site.jsx
- shared/oh-hub.jsx
- shared/oh-experiments.js

Then inspect internal surfaces if present:

- context-is-everything/Demo Control Tower.html
- inference-gateway/Shared Inference Gateway.html
- teleon/Teleon PurposeTask Control Tower.html
- template-registry/Shared Template Registry.html

Then inspect every hub folder README and prototype page.

Create or update:

- `.agent/aidoneright-current-state-verification.json`

Record:

- verified surfaces
- missing surfaces
- stale docs
- stale counts
- dead links
- old brand references
- public/private status mismatches
- product-boundary violations
- design-system violations
- service-auth gaps
- production-readiness gaps
- next target

## Priority Ladder

Pick the highest-value incomplete target.

P0 - Fix stale counts, dead links, stale brand references, missing hub entries, or
surface inventory mismatch.

P1 - Create or improve service-to-service consumption docs and architecture:

- service_consumption_matrix
- service_identity_catalog
- service_account_policy
- api_key_policy
- secret_ref_policy
- authn_authz_model
- public_private_visibility_matrix
- product_service_boundaries

P2 - Add checks/proofs for:

- no raw secrets in prototypes
- Open*Hub projection-only access
- product boundary preservation
- no stale parent-brand hardcodes

P3 - Polish and verify the Baltor method spine:

- Reconcile
- Harden
- Enhance
- Optimize
- Verify

P4 - Update production-readiness docs:

- prototype-to-production plan
- backend service map
- datastore plan
- auth plan
- API plan
- observability plan
- security review
- handoff to Claude Code Max

P5 - Research candidate production stack:

- auth providers
- API gateways
- secret management
- service accounts
- service mesh / workload identity
- search and registry backends
- billing/metering
- observability
- MCP/agent security

P6 - Demo Control Tower polish:

- every surface card opens
- statuses are honest
- private bench is grouped correctly
- no fake production claims

P7 - Handoff bundle freshness:

- docs reflect current surface counts
- screenshots index is current
- handoff manifest exists

P8 - Design polish:

- no overflow
- no clipping
- no broken links
- shared tokens only
- private preview banners correct

## Service-To-Service Consumption Model

Define how every service consumes every other service.

Required human actors:

- anonymous visitor
- demo reviewer
- logged-in user
- org admin
- product operator
- support/admin staff
- owner/developer

Required machine actors:

- baltor_service
- teleon_service
- openhub_projection_service
- inference_gateway_service
- template_registry_service
- demo_control_tower_service
- agent_gateway_service
- crawler_worker
- registry_ingest_worker
- benchmark_runner
- harness_runner
- receipt_writer
- state_store_worker
- sandbox_runner

Allowed credential classes:

- public_read_projection
- anonymous_demo_read
- demo_token
- user_session_oidc
- org_user_session
- org_scoped_api_key
- service_account_jwt
- workload_identity
- oauth2_client_credentials
- short_lived_api_key
- mtls_service_identity
- signed_request
- secret_ref
- human_approval_receipt

Forbidden:

- raw long-lived keys in browser prototypes
- raw keys in HTML
- raw keys in logs
- shared organization keys in agent sandboxes
- Open*Hub public pages executing gated tools
- cross-tenant reads
- direct provider SDK calls from product/business code
- free/prototype LLM endpoints handling sensitive data by default

Standard headers:

- `Authorization: Bearer <token>`
- `X-AIDR-Tenant`
- `X-AIDR-Org`
- `X-AIDR-Request-Id`
- `X-AIDR-Idempotency-Key`
- `X-AIDR-Actor`
- `X-AIDR-Service`
- `X-AIDR-Data-Class`
- `X-AIDR-Receipt-Required`

Never show real secret values. Use examples like:

- `sk_demo_redacted`
- `svc_baltor_redacted`
- `secret_ref://prod/openai/main`
- `receipt://example`

## Required Service Matrix Shape

Create entries like:

```json
{
  "consumer": "baltor",
  "provider": "teleon",
  "interface": "PurposeTaskProviderPort",
  "purpose": "Run bounded capabilities such as source fetch, fragile fact refresh, decomposition assistance, and context optimization.",
  "auth_mode": "service_account_jwt",
  "secret_policy": "secret_ref_only",
  "data_classes": ["tenant_private", "regulated_context"],
  "allowed_actions": ["run_capability", "get_receipt", "get_status"],
  "forbidden_actions": ["promote_candidate_without_policy", "expand_boundary", "read_other_tenants"],
  "receipt_required": true,
  "projection_only": false,
  "status": "design_required"
}
```

And:

```json
{
  "consumer": "opencontext_hub_public_site",
  "provider": "openhub_projection_api",
  "interface": "GET /api/opencontext/search",
  "auth_mode": "public_read_projection",
  "secret_policy": "no_secrets",
  "data_classes": ["public_metadata"],
  "allowed_actions": ["read_public_metadata"],
  "forbidden_actions": ["read_private_payload", "serve_context_as_truth", "write_registry"],
  "receipt_required": false,
  "projection_only": true
}
```

## Proof / Check Targets

Create or update checks when relevant:

- `scripts/check_portfolio_surface_inventory.py`
- `scripts/check_products_js_source_of_truth.py`
- `scripts/check_control_tower_surface_links.py`
- `scripts/check_private_bench_hub_status.py`
- `scripts/check_method_spine_hubs_complete.py`
- `scripts/check_hub_footers_parent_brand.py`
- `scripts/check_no_stale_parent_brand_names.py`
- `scripts/check_service_consumption_matrix.py`
- `scripts/check_service_identity_catalog.py`
- `scripts/check_api_key_policy.py`
- `scripts/check_secret_ref_policy.py`
- `scripts/check_no_raw_secrets_in_prototypes.py`
- `scripts/check_openhub_projection_only_access.py`
- `scripts/check_service_auth_boundaries.py`
- `scripts/check_handoff_docs_freshness.py`
- `scripts/check_surface_counts_in_docs.py`
- `scripts/check_handoff_bundle_manifest.py`

If this repo is design/prototype-only and backend flywheel is not applicable:

- do not fake backend green
- mark backend proof as `NOT_APPLICABLE_DESIGN_REPO`
- run static/design checks instead

## Method-Spine Requirements

Verify these private bench hubs:

| Hub | Stage | Hero | Methods |
| --- | --- | --- | --- |
| OpenReconciliationHub | Reconcile | Cluster alignment. | dedupe; link evidence; surface conflicts |
| OpenHardeningHub | Harden | Robust object hardening. | detect fragile values; create objects; refresh over time |
| OpenEnrichmentHub | Enhance | Context enrichment. | add metadata; connect objects; increase robustness |
| OpenOptimizationHub | Optimize | Pack shaping. | summarize; structure; rank |
| OpenVerificationHub | Verify | Cited and provable. | source support; receipt/provenance; verification gates |

Each must have:

- private preview banner
- correct muted accent
- launch accent ready
- open standards section
- provenance/trust section
- account console
- README
- Control Tower link
- parent bench card
- no overclaiming

## Handoff Freshness

Create or update:

- `docs/handoff/handoff-freshness.md`
- `docs/handoff/claude-code-max-transfer.md`
- `docs/handoff/codex-transfer.md`
- `docs/handoff/openhub-surface-counts.md`

Required handoff contents:

- README.md
- START-HERE-CLAUDE-CODE.md
- HANDOFF.md
- CLAUDE.md / CLAUDE-CODE.md
- MARKETING.md
- POSITIONING-AUDIT.md
- BACKEND-STACK.md
- UX-BACKLOG.md
- products.js
- screenshots/screens index
- Control Tower
- parent site
- Baltor
- Teleon
- all live hubs
- all private bench hubs
- method-spine docs
- service-auth docs
- production-readiness gap
- next loop prompt

## Browser E2E + Local Service Emulation Gate (owner add-on, 2026-06-09 — MANDATORY)

The repo's surfaces are high-fidelity prototypes (HTML + React/Babel, mock data,
`products.js` as the owning registry). The loop must therefore build and maintain a
**local production-shaped harness around the prototypes**: start local services, expose
them through reverse proxies / TryCloudflare, crawl every path, click every button, test
registration/API-key flows against local emulators, capture screenshots/HTML, and FAIL
when anything breaks. **This gate is required before claiming a surface or flow works.**

### Core rule

UI interaction is a CONTRACT, not a screenshot. Do not rely on visual inspection. Every
page, route, button, link, tab, form, CTA, console action, account page, API-key action,
registration path, and product flow must be either: tested by Playwright (or equivalent),
explicitly marked HELD with a visible reason (`data-held="true"` +
`data-held-reason="…"` or a visible HELD/preview label), or excluded by a documented
rule. **No silent dead buttons.** Do not mark a flow green if the backing service is a
dead button; do not hide failing buttons by removing them.

### Do not

No real production secrets · no paid cloud · no live LLMs unless explicitly authorized ·
no real external account registration · no live third-party diagnostics · no real
customer-data mutation · **no fake URLs** · public pages never write truth · dashboards
never become truth · raw API keys never appear in screenshots, HTML, logs, events, local
storage, or receipts (`aidr_demo_sk_redacted_…` / `secret_ref://local/demo/user-key`
example forms only).

### Local service emulation target

`architecture/local_service_registry.json` is the registry — a lightweight
Cloud-Run-like / service-mesh preview. Every entry carries: service_id, display_name,
owner, port, start_command, health_url, ready_url, public_routes, private_routes,
env_file, allowed_consumers, auth_mode, data_classes, logs_path, screenshot_required,
trycloudflare_required, status. Target services: parent/Baltor/Teleon/hub sites, Demo
Control Tower, shared inference gateway, shared template registry, Teleon PurposeTask
Control Tower, local auth/api-key/service-account services, event tracker, A/B engine,
analytics projection, OpenHub projection API, MCP connection emulator, LLM-plane stub
(deterministic unless live LLM explicitly authorized), receipt service, state service.
Required emulator behaviors: auth (register/login/logout/session/org-switch), API keys
(create/list/revoke/test; hash-or-redacted at rest; never reveal after creation), service
accounts (identity/token/scopes/rotation), events (page_view, button_click, form_submit,
api_key_created, api_key_tested, experiment_exposed, …), deterministic seeded A/B
variants, analytics aggregation, projection-only public metadata, MCP connection
add/list/test/revoke without executing dangerous tools, receipts for important flows,
state that is never truth authority. Cloud-Run-like discipline per service: own port,
`/healthz` `/readyz` `/version` `/metrics/local` `/api/status` where practical,
structured logs, env config, idempotent startup, graceful shutdown, registry entry,
container/Terraform plan later.

### Playwright crawler + every-button testing

Discover pages from `products.js`, Control Tower cards, hub route definitions, nav/footer
links, and the standard route set (/dashboard /installed /publish /keys /team /audit
/notifications /billing /usage /settings /docs /pricing /cases /about /status /changelog
/terms /privacy + product/private-bench/method-spine routes). For every page: load local
URL (and tunnel URL when available), wait for stable DOM, capture 1440/1280/390px
screenshots + HTML snapshot + console logs + network failures; verify no horizontal
overflow, no uncaught JS errors, no dead links, no broken assets, no raw secrets, honest
status labels, projection-only disclaimers, private-preview banners, public/private route
boundaries. Enumerate and activate every interactive element (button, a[href],
[role=button], submit, .oh-btn, tabs, segments, summary, selects, checks, radios,
command-palette actions, CTAs, console/key/account buttons); for each: record
selector/text/role, activate, verify the expected result (route change, modal, tab, form
submit, event tracked, API call, disabled/HELD display, or safe error), no console error,
no crash, no secret, no forbidden mutation from public pages. Artifacts:
`artifacts/e2e/{screenshots,html,console,network,reports}/`.

### Required flows

- **Registration/account:** parent → sign-up CTA → register `demo+<ts>@aidoneright.dev`
  (generated local passphrase) → local/demo email-verification state → login → dashboard
  → create org/workspace → switch org → billing/usage/settings/team/audit → logout →
  login → session restored → events tracked (local outbox emulator; no real email).
- **API keys:** /keys → create (shown once) → redacted afterward → test via
  `GET /api/local/key-test` (scoped success) → revoke → test fails → key absent from
  screenshots/HTML/console/events/receipts except redacted/ref form.
- **Service accounts:** create local service account → scoped token/ref → Baltor calls
  Teleon local API with it → Teleon calls OpenHub projection API → OpenHub PUBLIC page
  cannot use a service token → scope violations and revoked tokens fail closed → tokens
  only redacted in UI/logs.
- **Baltor ↔ Teleon:** register → org → Baltor portal → connect to Teleon via service
  account → run a context-governance demo → Baltor requests a Teleon CapabilityTask →
  Teleon returns deterministic local result + receipt → Baltor serves the governed answer
  with receipt/source handles → held-out warnings stay separate → Teleon output is
  evidence/candidate, never truth.
- **Teleon agent capability:** list CapabilityTasks → run local deterministic capability
  → view receipt → forbidden boundary expansion requires human approval → LLM fallback
  while disabled fails closed or uses the local stub → no raw secrets → events tracked.
- **Open*Hub:** landing → search/browse → entry detail → provenance/trust rail →
  dashboard → publish/submit local fixture → lands in review queue (never public-active)
  → "discovery is not trust" present → no execution from public listings → private hubs
  show the private-preview banner.
- **A/B + analytics:** every page load + meaningful interaction emits a LOCAL event
  (page_view, experiment_exposed, cta_clicked, button_clicked, form_started,
  form_submitted, registration_completed, login_completed, api_key_created/tested/revoked,
  service_account_created, mcp_connection_created/tested, capability_run_started/
  completed, receipt_viewed, held_item_viewed) carrying event_id, timestamp, session_id,
  anon_or_user_id, org_id?, surface_id, route, event_type, target_text_or_id,
  experiment_variant?, data_class, no_raw_secret. Never send analytics externally.

### TryCloudflare / reverse-proxy

Support local-only, reverse-proxy, and TryCloudflare URLs. Maintain
`dist/cloudflare-urls.md`, `dist/local-service-urls.md`, `dist/e2e-url-map.json` with
local_url, tunnel_url?, status, last_checked, screenshot, notes per service/page. If
cloudflared is unavailable: mark HELD/PARTIAL, never fake a URL, still run local E2E.

### Deliverables

Docs: `docs/production/{local-service-emulation,e2e-browser-test-plan,cloud-run-like-service-contract,playwright-qa-gate,trycloudflare-review,prototype-to-deployable-services}.md`.
Registries: `architecture/{local_service_registry,e2e_surface_registry,e2e_action_registry,local_emulator_registry}.json`.
Scripts: `scripts/{start_local_services,stop_local_services,check_local_services_health,check_trycloudflare_urls,check_reverse_proxy_urls,check_e2e_surface_registry,check_no_raw_secrets_in_e2e_artifacts,check_local_auth_emulator,check_local_api_key_flow,check_service_account_flow,check_analytics_event_flow,check_ab_test_flow,check_baltor_teleon_connection_flow,check_openhub_projection_flows,check_e2e_full_stack}.py`.
Playwright: `e2e/{crawl_all_surfaces,click_everything,register_login_portal,api_keys_flow,service_accounts_flow,baltor_teleon_flow,openhub_flows,analytics_ab_flow,capture_all_screenshots,no_overflow_check}.mjs`.
If Playwright is not installed and installs are forbidden: create scripts + docs, add the
HELD note ("Playwright dependency not installed; browser E2E gate ready but not runnable
in this environment"), run fallback static checks, never claim Playwright green. If
Playwright IS installed: run the suite.

### Acceptance criteria (a cycle is not green unless)

Local service registry exists · services start locally or are HELD · health checks pass
for available services · every surface is in the E2E surface registry · every route
resolves or is HELD · every button/action is tested or HELD · registration/login works
locally · API key create/test/revoke works locally · service-account flow works locally ·
Baltor↔Teleon local connection works or is partially implemented with a clear HELD item ·
OpenHub public pages remain projection-only · analytics events recorded locally · A/B
variants exposed + tracked locally · screenshots + HTML snapshots captured · no raw
secrets in artifacts · TryCloudflare URLs checked when available · no fake URLs · docs
updated · proof/check results recorded.

### Gate loop commands

```text
/loop 1200 /goal follow docs/goals/aidoneright-portfolio-loop.md and add the Browser E2E + Local Service Emulation Gate as mandatory: use Playwright or equivalent to crawl every surface from products.js and Control Tower, test every route/link/button/form/tab/CTA/account-console action, attempt local registration/login/org/API-key/service-account/MCP flows, verify Baltor↔Teleon service consumption, verify Open*Hub projection-only behavior, record local analytics/A-B events, capture desktop/mobile screenshots and HTML snapshots, check console/network/no-overflow/no-raw-secrets, start all services from a local service registry with health/ready endpoints, expose/check TryCloudflare or reverse-proxy URLs when available, emulate Cloud-Run-like services locally, and complete one proof-backed increment per cycle. No fake URLs, no real secrets, no paid cloud, no direct provider bypass, no overclaims.
```

Parser-safe short form:

```text
/goal add a mandatory Playwright E2E + local Cloud-Run-like service emulation gate: start local services from a registry, health-check them, expose/check TryCloudflare/reverse-proxy URLs, crawl every products.js/Control Tower surface, test every route/button/form/account action, run local registration/login/API-key/service-account/MCP flows, verify Baltor↔Teleon and OpenHub projection-only behavior, record local analytics/A-B events, capture screenshots/HTML/console/network, check no overflow/no raw secrets/no fake URLs, document HELD items, and complete one proof-backed increment per pass.
```

## Short Goal Command

Use this in Codex/Claude Code:

```text
/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md. Work one proof-backed increment only. First verify current state from README.md, HANDOFF.md, products.js, Control Tower, and hub READMEs. Prioritize stale surface counts, dead links, parent-brand consistency, method-spine completeness, and the new service-to-service auth model: service consumption matrix, service identities, API key policy, secret refs, public/private projection boundaries. Preserve product positioning: AI Done Right parent; Baltor governs truth/context; Teleon runs capabilities; Open*Hubs are registries only; discovery is not trust; output is not truth; dashboards are projection-only. No raw secrets, no fake URLs, no cloud, no network LLM, no installs, no overclaims. If backend flywheel is not applicable, mark NOT_APPLICABLE_DESIGN_REPO and run static/design checks instead. Return files changed, checks run, honest gaps, and next target.
```

## Loop Command

If the environment asks for `/loop interval prompt`, use:

```text
/loop 1200 /goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md. Work one proof-backed increment per cycle. Start with current-state verification, then repair the highest-priority mismatch. Prioritize service-to-service auth, API keys, service accounts, secret refs, projection-only Open*Hub boundaries, method-spine docs, Control Tower links, stale counts, and handoff freshness. Stop only if STOP_REQUESTED exists.
```

## Emergency Short Goal

```text
/goal follow docs/goals/aidoneright-portfolio-loop.md. Verify reality, fix one highest-priority issue, run checks, update receipt/docs. Preserve AI Done Right/Baltor/Teleon/Open*Hub boundaries. Build service-auth docs/matrix if no higher-priority breakage exists. No secrets, no fake URLs, no installs, no cloud, no overclaims.
```

## Final Response Format

Return only after a real increment:

1. Cycle status: GREEN / PARTIAL / RED
2. Target selected and why
3. Current-state corrections
4. New increment completed
5. Service-auth progress
6. Portfolio/product boundary check
7. Method-spine status
8. Proofs/checks run with exact commands
9. Files changed
10. Honest gaps / HELD items
11. Next target
