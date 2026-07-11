# Teleon Egress Graph And Route Broker

Teleon workers must treat every outbound search, fetch, API call, MCP tool call,
or registry lookup as evidence. The egress graph captures that evidence before a
worker can use it downstream.

## Contract

- Every outbound action starts as an egress intent and receives a route broker
  decision before transport.
- Every completed or blocked outbound action emits a
  `TeleonEgressObservation`.
- Observations are append-only and tenant-scoped.
- Secrets in URLs, headers, request summaries, and response summaries are
  redacted before storage.
- The graph projects observations into query, worker, tool, destination,
  egress-event, and response-digest nodes.
- Search is scoped by tenant and can filter by query text, query id, worker, or
  destination host.
- `serves_truth=false` always. The graph records what a worker touched; Baltor
  decides what can become served context.
- The append-only egress ledger is the source of record. The graph/search layer
  is a projection.

## Route Broker

The route broker sits before transport:

```text
Worker -> EgressIntent -> RoutePolicyDecision -> TransportAdapter
       -> AppendOnlyEgressLedger -> Graph/Search Projection
```

Route policies live in `_repos/shared-backend-components/architecture/egress_route_policy_taxonomy.json`.
Execution-surface defaults point at those policies from
`_repos/shared-backend-components/architecture/execution_environment_profiles.json`.

Supported route families are direct public internet, official API,
customer-private connector, approved proxy exit, approved VPN exit, browser pool,
and blocked/manual review. Proxy and VPN routes are for customer-approved
network paths, residency, secure tunnels, or allowlisted exits. They are never
used for ban evasion, captcha bypass, access-control bypass, or silent fallback
when authorization is unclear.

## Runtime Shape

The local correctness implementation is split by responsibility:

- `_repos/teleon/backend/src/teleon/egress/policy.py` mints `EgressIntent` and deterministic
  `EgressRouteDecision` records.
- `_repos/teleon/backend/src/teleon/egress/client.py` is the worker-facing egress API.
- `_repos/teleon/backend/src/teleon/egress/transports.py` is the only scoped module allowed to own raw
  HTTP transport calls.
- `_repos/teleon/backend/src/teleon/egress/ledger.py` stores append-only intent, decision, attempt,
  and payload-reference records.
- `_repos/teleon/backend/src/teleon/egress/traffic_graph.py` projects ledgered observations into the
  searchable graph:

```text
Query -> EgressEvent -> Destination
          |        |
          v        v
        Worker   ResponseDigest
          |
          v
         Tool
```

Production can replay the same observation stream into a graph database or
search index. Do not bypass the observation contract to write graph nodes
directly; the observation is the receipt.

The north-star production storage model is two-layered:

- append-only ledger tables for intents, route decisions, attempts, response
  digests, payload references, and blocked/manual-review decisions;
- graph/search projections derived from the ledger for tenant/query/worker/tool
  investigation.

## Why This Exists

This is the runtime analogue of code-knowledge graph augmentation tools such as
`pi-gitnexus`: instead of appending code-call context to file reads and searches,
Teleon records worker egress so later agents and reviewers can ask:

- Which sources did this query touch?
- Which worker/tool contacted which host?
- Which response digest was used?
- Which unavailable source produced a verification task?
- Which evidence was later promoted, held out, or ignored by Baltor?

## Proof

```bash
python3 _repos/shared-backend-components/scripts/check_teleon_egress_graph.py --self-test
python3 _repos/shared-backend-components/scripts/check_teleon_egress_enforcement.py --self-test
python3 _repos/shared-backend-components/scripts/check_teleon_execution_environment_taxonomy.py --self-test
```

The proof covers redaction, append-only behavior, tenant isolation, graph
projection, query search, worker/destination search, and the truth boundary.
The enforcement proof covers the runtime egress client, append-only route
decisions and attempts, approval-required route blocking, static no-raw-HTTP
guards for covered worker/inference modules, and raw HTTP isolation in the
approved transport adapter. The taxonomy proof covers route-policy coherence,
runtime profile coverage, pre-autotune defaults, and the no-truth egress
boundary.
