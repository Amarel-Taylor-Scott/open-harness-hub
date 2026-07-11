# Teleon Execution Environment Taxonomy

Teleon should not hard-code whether a worker is "a Kubernetes thing" or "a
cloud function thing." A worker declares an abstract runtime class, then policy
binds that class to a local, K8s, serverless, browser, GPU, or workflow backend.

The new profile layer lives in
`_repos/shared-backend-components/architecture/execution_environment_profiles.json`. It adds the missing
pre-autotune contract for every class in
`_repos/shared-backend-components/architecture/capability_runtime_classes.json`:

- shared characteristics: surface family, execution shape, state model, trigger
  model, scale-to-zero support, browser/GPU needs;
- requirements: minimum worker resource class, network-policy default, local
  correctness backend;
- policy preferences: lifecycle policy, SLA policy, egress route policy,
  identity mode, tenant-data default, secret-access default;
- pre-autotune defaults: sources for concurrency and timeout, scale-to-zero,
  minimum instances;
- autotuning boundary: allowed knobs and forbidden knobs;
- observability: required receipts and the no-truth runtime boundary.

## Runtime Binding

```text
CapabilityTask / PurposeTask
  -> worker bucket
  -> runtime_class
  -> ExecutionEnvironmentProfile
  -> RuntimeClassBinding
  -> ExecutionProviderDecision
  -> local/function/K8s/job/browser/GPU/workflow backend
```

The runtime class remains the portable authoring surface. The execution profile
is the pre-autotune policy card for that class. The backend selector can reorder
eligible providers, tune concurrency, tune keepalive, tune batch windows, and
move resource class upward when evidence supports it. It cannot change tenant
scope, trust boundary, secret policy, source authority, egress restrictions, or
truth authority.

> **Wiring status (2026-06-18):** these profiles are AUTHORED defaults + guardrails, validated by
> `check_teleon_execution_environment_taxonomy`. The live egress/route callers do NOT yet read
> `profile.policy_preferences.egress_route_policy_id` — they pass `route_policy_id` explicitly to
> `decide_route`. Consuming the profile's preferences during selection is a tracked follow-up; the
> profile is the authored target, not yet the runtime source.

## Egress routing (profile → policy; full contract in `teleon-egress-graph.md`)

Each execution profile carries an `egress_route_policy_id` preference (see the wiring-status note above);
outbound requests are governed by `_repos/shared-backend-components/architecture/egress_route_policy_taxonomy.json`. Today `decide_route`
selects/validates the route policy the caller REQUESTS (by `route_policy_id`), the destination URL scheme,
and whether an approval ref is present: an unknown policy, a `blocked`-kind policy, a non-http(s) scheme, or
a not-`default_allowed` route without an approval ref all resolve to `manual_review_blocked` instead of
silently rotating to another network path. Richer inputs (source policy, tenant policy, credential
availability, residency, destination risk, provider health) are PLANNED selection signals, not yet read by
the broker.

The route broker sits before transport and mints a typed decision record for every outbound request:

```text
Worker -> EgressIntent -> RoutePolicyDecision -> TransportAdapter -> AppendOnlyEgressLedger -> Graph/Search Projection
```

`decide_route` consumes the caller's `EgressIntent` and returns a `RoutePolicyDecision` (the chosen/validated
`route_policy_id`, the destination scheme, and the approval-ref check) that is appended to the ledger. The
**append-only egress ledger is the source of record; the graph/search layer is a projection** derived from it
(`serves_truth=false`, tenant-scoped) — never an authority.

The **full egress contract is the single source in [`teleon-egress-graph.md`](teleon-egress-graph.md)** and
is not duplicated here: the route broker, the append-only egress ledger as source of record, the graph/search
projection, the proxy/VPN route rules (customer-approved paths only — never ban evasion / captcha bypass /
access-control bypass), the north-star runtime path, and the local `_repos/teleon/backend/src/teleon/egress`
enforcement slice (`EgressClient` + the sole raw-HTTP transport adapter). `serves_truth=false` is invariant
across every egress decision, and Baltor decides what evidence can become served context.

## North Star

The runtime class remains the portable authoring surface; the execution profile is its pre-autotune policy
card. Kubernetes NetworkPolicy, service mesh egress gateways, workload identity, CloudEvents-style envelopes,
OpenTelemetry spans, and PROV/OpenLineage-style lineage are implementation choices **below** this contract —
they must not become the source of truth. The task ledger and egress ledger are the canonical runtime records.

## Proof

```bash
python3 _repos/shared-backend-components/scripts/check_teleon_execution_environment_taxonomy.py --self-test
```

The proof cross-checks the profiles against runtime classes, backend local
equivalents, worker resource classes, lifecycle policies, SLA policies, route
policies, schemas, and docs. The egress route-broker and its enforcement proof
(`_repos/shared-backend-components/scripts/check_teleon_egress_enforcement.py`) are covered in
[`teleon-egress-graph.md`](teleon-egress-graph.md).
