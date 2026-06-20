# Teleon Execution Environment Taxonomy

Teleon should not hard-code whether a worker is "a Kubernetes thing" or "a
cloud function thing." A worker declares an abstract runtime class, then policy
binds that class to a local, K8s, serverless, browser, GPU, or workflow backend.

The new profile layer lives in
`architecture/execution_environment_profiles.json`. It adds the missing
pre-autotune contract for every class in
`architecture/capability_runtime_classes.json`:

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
  -> ExecutionEnvironmentProfile.v1
  -> RuntimeClassBinding.v1
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

## Egress Routing

Outbound requests are governed by
`architecture/egress_route_policy_taxonomy.json`. Today `decide_route` selects/validates the route
policy the caller REQUESTS (by `route_policy_id`), the destination URL scheme, and whether an approval
ref is present: an unknown policy, a `blocked`-kind policy, a non-http(s) scheme, or a
not-`default_allowed` route without an approval ref all resolve to `manual_review_blocked` instead of
silently rotating to another network path. Richer inputs (source policy, tenant policy, credential
availability, residency, destination risk, provider health) are PLANNED selection signals, not yet
read by the broker.

The important split is:

- The append-only egress ledger is the source of record.
- The graph/search layer is a projection.
- Route decisions and observations are evidence only.
- `serves_truth=false` is invariant.

Proxy and VPN routes exist for customer-approved routing, data residency,
allowlisted egress IPs, secure tunnels, and source-approved access paths. They
are never used for ban evasion, captcha bypass, or access-control bypass. If a
source cannot be reached safely, Teleon emits a blocked/manual-review route
decision and a verification task.

## North Star

The north-star runtime path is:

```text
Worker
  -> EgressIntent
  -> RoutePolicyDecision
  -> TransportAdapter
  -> AppendOnlyEgressLedger
  -> Graph/Search Projection
  -> Baltor verification and source-precedence gates
```

Kubernetes NetworkPolicy, service mesh egress gateways, workload identity,
CloudEvents-style envelopes, OpenTelemetry spans, and PROV/OpenLineage-style
lineage are implementation choices below this contract. They must not become
the source of truth. The task ledger and egress ledger are the canonical runtime
records; Baltor decides what evidence can become served context.

The first local enforcement slice is implemented by `src/teleon/egress`:
covered context workers and live inference adapters call `EgressClient`, which
records the intent, route decision, attempt, and graph observation before a
response is consumed. Raw HTTP is isolated to the approved transport adapter so
new worker code cannot silently bypass the route broker in the covered path.

## Proof

```bash
python3 scripts/check_teleon_egress_enforcement.py --self-test
python3 scripts/check_teleon_execution_environment_taxonomy.py --self-test
```

The proof cross-checks the profiles against runtime classes, backend local
equivalents, worker resource classes, lifecycle policies, SLA policies, route
policies, schemas, and docs. The egress enforcement proof adds the executable
runtime guard for covered workers and live inference.
