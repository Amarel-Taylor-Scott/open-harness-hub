# Service Connections — the standardized contract

How products and hubs authenticate to each other, and how users manage their own
keys and connections. One pattern everywhere; no bespoke auth per site.

## 1. Identity tiers

| Tier | Credential | Issued by | Example |
|---|---|---|---|
| **User** | JWT session (`/v1/auth/*`) | platform-core | a person signing into Baltor's console |
| **User API key** | `sk_live_…` | self-service (`/v1/keys`) | an agent calling the LLM plane with a user's key |
| **Service account** | `SERVICE_<ID>_SECRET` (env) | operator (.env / Terraform) | Baltor itself, Teleon itself, each hub |
| **Service key** | `sk_svc_…` | handshake (`/v1/service/handshake`) | Baltor → Teleon scoped key |

## 2. The handshake (Baltor needs a key from Teleon, and vice versa)

Standardized for every pair — products ↔ products, hubs ↔ products:

```
POST /api/v1/service/handshake
Authorization: Bearer $SERVICE_BALTOR_SECRET        # caller proves who it is
{ "from": "baltor", "to": "teleon", "scopes": ["llm:invoke", "events:write"] }

→ { "connection": {…}, "secret": "sk_svc_…", "receipt": "rcpt_…" }   # secret shown once
```

Rules:
- The caller authenticates with **its own** service secret; the issued key is scoped `from → to`.
- Every handshake emits a signed receipt; both sides list connections at `/v1/service/connections`.
- Revocation = revoke the key (same as user keys). Re-handshake to rotate.
- Admin bootstrap is just env: set `SERVICE_<ID>_SECRET` for each deployed service.
  Terraform generates and injects these (see `terraform/`).

## 3. User-managed connections (MCP servers, tools, webhooks)

Users open their own connections from any product portal:

```
POST /api/v1/connections        (user JWT)
{ "kind": "mcp", "name": "filesystem-mcp", "endpoint": "http://localhost:3920/sse", "scopes": ["read"] }
```

- `kind`: `mcp` | `tool` | `webhook`. List/delete via `/v1/connections`.
- The UI surface for this is the kit's `OhApiKeys`/`OhSettings` pattern — a shared
  "Connections" page is queued (Pass 2) so Baltor and Teleon render the same screen.

## 4. Scopes (initial vocabulary)

`llm:invoke` · `events:write` · `registry:read` · `registry:publish` · `serve:cited` ·
`verify:run` · `state:read` · `state:write`. Keep the list short; extend only when a
real call needs it.

## 5. Receipts

Every credential event (register, key create/revoke, handshake, LLM invocation) emits a
record signed by platform-core (HMAC). **Honest gap:** production receipts are
Sigstore/Rekor (see BACKEND-STACK.md); HMAC is the local stand-in. The record shape is
already compatible: `{ id, kind, at, body, sig }`.
