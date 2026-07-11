# Service Auth And Consumption Model

Status: draft architecture brief  
Updated: 2026-06-09

This document answers the open handoff question: how do AI Done Right services
consume each other using API keys, authentication, service accounts, and scoped
authorization?

The short answer: **external clients get API keys or OAuth clients; internal
services get workload identities and short-lived scoped tokens; users get OIDC
sessions; every cross-service call is tenant-scoped and auditable.**

Machine-readable policy:

```text
architecture/service_auth_consumption_model.json
```

Focused proof:

```bash
python3 scripts/check_service_auth_consumption_model.py --self-test
```

The proof cross-checks the policy against `services/registry.yaml`, verifies
every declared service has a distinct service account, checks that
registry-declared communication edges have scoped internal auth coverage, and
rejects obvious raw secret literals.

## Research Anchors

- OWASP API Security Top 10 2023 keeps authorization and authentication risk at
  the center of API design, especially object-level and function-level access:
  <https://owasp.org/www-project-api-security/>
- NIST SP 800-207 frames zero trust around explicit authentication and
  authorization for users, assets, and resources, with no implicit network
  trust: <https://csrc.nist.gov/pubs/sp/800/207/final>
- OAuth 2.0 client credentials are for confidential clients acting as
  themselves, not as a user: <https://datatracker.ietf.org/doc/html/rfc6749#section-4.4>
- OAuth 2.0 mTLS binds client authentication and tokens to certificates:
  <https://www.rfc-editor.org/rfc/rfc8705>
- SPIFFE/SPIRE provides workload identity through SVIDs for service-to-service
  authentication in heterogeneous environments:
  <https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/>

## Principles

1. **Separate human identity from workload identity.**
   Users authenticate with OIDC/SSO/session auth. Services authenticate as
   service accounts/workloads.

2. **API keys are for external client access, not internal service trust.**
   Customer SDKs, CLI clients, and publisher integrations may use scoped API
   keys. Internal Baltor/Teleon/OpenHubForAI calls should use service identity plus
   short-lived tokens.

3. **No shared god token.**
   Each service has its own account, allowed callers, allowed callees, scopes,
   environments, and rotation policy.

4. **Tenant and object authorization happen before data access.**
   Authentication only proves who is calling. Authorization must check tenant,
   workspace, purpose, object, action, data class, and freshness/security policy.

5. **Candidate does not mean trusted.**
   OpenHubForAI registries expose discoverable metadata. Baltor and Teleon must
   still evaluate, verify, or gate artifacts before use.

6. **Every privileged call produces an audit event or receipt.**
   Cross-service requests should carry correlation IDs, actor/delegation
   context, tenant, scopes, data class, and policy decision.

## Identity Types

| Identity | Used by | Credential | Notes |
| --- | --- | --- | --- |
| Human user | Browser UI, console user | OIDC/session | Maps to tenant memberships and roles. |
| External API client | Customer SDK, CLI, webhook publisher | Scoped API key or OAuth client | Keys are hashed at rest; raw value shown once. |
| Service account | Baltor, Teleon, OpenHubForAI APIs, workers | Short-lived JWT/OAuth token, mTLS cert, or SPIFFE SVID | Internal service-to-service trust. |
| Worker identity | Ingestion, foundry, measurement, enrichment, retrieval, governance | Service account plus queue role | Least privilege per queue and datastore. |
| Publisher identity | Open registry submitters | OIDC + signing key or verified publisher account | Needed for provenance and promotion. |
| Break-glass identity | Human operator | Time-boxed approval + hardware/SSO MFA | Must emit high-severity audit events. |

## Consumption Matrix

| Caller -> callee | Auth default | Authorization checks | Receipt/audit |
| --- | --- | --- | --- |
| Browser -> product API | OIDC session cookie | tenant, role, route, object, CSRF | request audit |
| Customer SDK/CLI -> product API | scoped API key or OAuth client | tenant, key scope, quota, data class | API key usage audit |
| Baltor -> Teleon | service account + short-lived token; mTLS/SPIFFE in prod | tenant, `purpose_task:*` scopes, data minimization | PurposeTask receipt |
| Teleon -> Baltor | service account + delegated task token | read-only context-pack scope unless explicitly approved | context access receipt |
| Product API -> retrieval/enrichment | internal service token | tenant, data class, freshness, route purpose | platform access audit |
| Product API -> queue | service token + enqueue scope | tenant, job kind, budget, approval policy | queued job receipt |
| Worker -> datastore | workload identity / IAM role | table/bucket/secret least privilege | job trace + DB audit |
| OpenHubForAI -> registry backend | API key/OIDC for publishers; public read for public metadata | candidate status, publisher rights, private-first gate | registry audit |
| Private bench hub -> any backend | internal service identity only | status must remain private until owner flips to live | private access audit |
| Webhook source -> ingestion | signed webhook or connector OAuth | source tenant, connector grant, replay window | source event receipt |

## Token And Key Rules

API keys:

- Store only a hash plus a short prefix.
- Show the raw key once at creation.
- Attach tenant, workspace, scopes, created_by, created_at, expires_at,
  last_used_at, last_used_ip, revoked_at, and rotation state.
- Support per-key quotas and allowed origins/IPs when useful.
- Never put raw keys in screenshots, fixtures, docs, logs, or generated
  receipts.

Service tokens:

- Short-lived by default.
- Issued to a specific service account and environment.
- Carry audience, issuer, subject, tenant/delegation context, scopes, purpose,
  expiry, key ID, and correlation ID.
- Validate issuer, audience, expiry, signature, and certificate/workload binding.
- Prefer mTLS/SPIFFE or cloud workload identity in production.

Secrets:

- Use `secret_ref` / `vault://` / cloud secret names in config.
- Never hardcode vendor keys, OAuth secrets, signing keys, database passwords,
  or tunnel tokens in repo files.

## Minimum Data Model

Add or map these tables/records when moving from prototype to production:

- `identity_providers`
- `tenants`
- `users`
- `memberships`
- `roles`
- `api_keys`
- `oauth_clients`
- `service_accounts`
- `service_account_keys`
- `service_dependency_edges`
- `access_grants`
- `policy_decisions`
- `auth_receipts`
- `audit_events`

`service_dependency_edges` should be generated from `services/registry.yaml`
and checked against runtime traces so undocumented service calls are visible.
The draft policy file already models this as `service_edges`; the validator
requires coverage for registry-declared `sync_reads`, `enqueues`, `calls`,
`emits`, and datastore reads.

## Portfolio-Specific Rules

Baltor:

- Owns customer context truth, canonical facts, context responses,
  reconciliation decisions, receipts, and tenant policy.
- Can call Teleon for PurposeTask execution, candidate generation, evaluation,
  and runtime decisions.
- Must not give Teleon raw customer context unless the request is explicitly
  scoped, minimized, and recorded.

Teleon:

- Owns capability execution, scorecards, promotion gates, runtime choices, and
  evidence bundles.
- May request Baltor context packs through Baltor's policy gate.
- Must not write Baltor canonical facts or reconciliation decisions.

OpenHubForAI registries:

- Own public and private registry metadata.
- Public reads may be unauthenticated for live public entries.
- Publishing, private bench access, and promotion require authenticated
  publisher/service identities.
- Registry discovery is candidate intelligence, not trust.

AI Done Right parent:

- Owns brand, portfolio, research, investor, and Control Tower projection
  surfaces.
- Owns no customer runtime truth.

## Phased Implementation

Phase 0 - prototype honesty:

- Keep prototype account/API-key pages clearly simulated.
- Add no fake secrets.
- Keep private-first as a displayed status, not a claimed security boundary.

Phase 1 - local MVP:

- Add local signed dev tokens for service calls.
- Add API key records with hash-only storage for external clients.
- Add middleware that checks tenant, scopes, object, and route purpose.
- Emit audit events for API key use and cross-service calls.

Phase 1 status (2026-06-09): the **user-identity + API-key slice is implemented
locally** — per-product separate realms (`architecture/identity_realm_registry.json`)
served by `scripts/identity_local_service.py`: register/onboard/login/session,
hash-only API keys (raw shown once, session-gated mint/list/revoke, `verify` for
service callers), audit JSONL with `X-AIDR-Request-Id`. Proof:
`scripts/check_identity_local_service_runtime.py`. Still open in Phase 1:
service-to-service dev tokens and route-purpose middleware on the product APIs.

Phase 2 - production SaaS:

- Add OIDC/SSO for users.
- Add OAuth client credentials for service APIs.
- Add mTLS/SPIFFE or cloud workload identity for internal service calls.
- Move secrets to vault/cloud secret manager.
- Add per-service accounts for Baltor, Teleon, each registry backend, and each
  worker tier.

Phase 3 - enterprise:

- Support customer-managed IdP, SCIM, service-account lifecycle, audit export,
  private connectivity, tenant-specific keys, and BYO cloud identity.
- Add service-dependency drift checks against telemetry.

## Open Design Questions

- Which identity provider should be the first production implementation?
- Do OpenHubForAI publisher accounts live in one shared registry backend or per hub?
- Which service mesh/workload identity path is preferred for the first cloud?
- Should customer API keys be accepted directly by Baltor/Teleon or exchanged
  for short-lived access tokens at an API gateway?
- Which events become signed receipts versus ordinary audit logs?
