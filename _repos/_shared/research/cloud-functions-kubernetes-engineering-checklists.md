# Cloud Functions And Kubernetes Engineering Checklists

**Date:** 2026-06-29  
**Status:** research note, candidate-only  
**Truth boundary:** source-backed checklist material for primitive generation; `serves_truth=false` until converted into records, tested, and promoted.

## Purpose

This note distills how programmers, platform engineers, and architects commonly develop cloud functions and Kubernetes systems. The goal is to turn official-provider guidance into AIDevObserver examples, review findings, source-backed primitive opportunities, CandidateBundle routes, and benchmark fixtures.

The target use case:

```text
AI coding session mentions Lambda / Cloud Functions / Azure Functions / Knative / Kubernetes
  -> AIDevObserver recognizes the workload shape
  -> searches registry and local repo for existing routes, templates, manifests, and proof checks
  -> flags missing checklist items and reinvention
  -> proposes reusable primitive/template routes
```

This is not a security-only checklist. It is primarily a developer-speed and architecture-reuse checklist. The high-value finding is usually:

```text
The agent is rebuilding a cloud function or Kubernetes deployment from scratch,
but the primitive database already has a handler template, deployment template,
resource policy, probe policy, rollout plan, or platform checklist.
```

## Source Base

Primary sources reviewed:

| Area | Source |
| --- | --- |
| AWS Lambda function practice | https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html |
| AWS serverless architecture review | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html |
| Google Cloud Run functions | https://docs.cloud.google.com/run/docs/tips/functions-best-practices |
| Google Cloud architecture pillars | https://docs.cloud.google.com/architecture/framework |
| Azure Functions best practices | https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices |
| Azure Functions Well-Architected service guide | https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-functions |
| Kubernetes security checklist | https://kubernetes.io/docs/concepts/security/security-checklist/ |
| Kubernetes application security checklist | https://kubernetes.io/docs/concepts/security/application-security-checklist/ |
| Kubernetes probes | https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ |
| Kubernetes resource management | https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ |
| Kubernetes Deployments | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ |
| Kubernetes Horizontal Pod Autoscaling | https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ |
| Kubernetes NetworkPolicies | https://kubernetes.io/docs/concepts/services-networking/network-policies/ |
| Kubernetes Pod Security Standards | https://kubernetes.io/docs/concepts/security/pod-security-standards/ |
| Knative functions and serving | https://knative.dev/docs/functions/ and https://knative.dev/docs/serving/ |

## Unifying Workload Model

Most cloud function and Kubernetes work can be mapped into a small set of reusable objects:

```text
intent
  -> trigger / ingress contract
  -> handler or container contract
  -> dependency and configuration surface
  -> secret and identity surface
  -> runtime limits and scaling policy
  -> retry / idempotency / delivery semantics
  -> observability and ledger surface
  -> deploy / rollout / rollback surface
  -> cost and reliability guardrails
  -> proof checks
```

AIDevObserver should recognize those objects in coding sessions instead of only matching file names.

## Programmer Checklist

Programmers usually own the handler, container, tests, and local behavior.

### Cloud Function Programmer Checklist

- Define the event or HTTP request contract before writing the handler.
- Keep the handler idempotent so duplicate events or retries produce safe results.
- Return or signal completion explicitly; do not leave background work running after function termination.
- Keep per-invocation user state out of reused execution environments.
- Move reusable clients, SDKs, connection pools, and expensive static initialization outside the handler when safe.
- Use environment variables or config references for operational parameters, not hard-coded bucket names, queue names, table names, or endpoints.
- Pin the function framework/runtime dependency when the platform supports it.
- Keep dependencies minimal to reduce cold-start and deploy latency.
- Delete or stream temporary files instead of accumulating temporary data.
- Write local unit tests for handler behavior and contract validation.
- Write integration tests for trigger shape, permissions, retries, and downstream dependency behavior.
- Add structured logging with request id, event id, correlation id, and output digest.
- Avoid manually terminating the process from function code.
- Avoid recursive self-invocation unless it is a deliberately bounded workflow.

### Kubernetes Programmer Checklist

- Choose the right workload object: Deployment, StatefulSet, Job, CronJob, DaemonSet, or Knative Service.
- Define a container entrypoint that starts predictably and handles termination.
- Add readiness, liveness, and startup probes where appropriate.
- Set CPU and memory requests; set memory limits; use CPU limits only when the workload needs them.
- Externalize config through ConfigMaps or provider-specific config systems.
- Use Secret references or external secret providers; do not bake secrets into images or manifests.
- Make application logs structured and stdout/stderr friendly.
- Expose only the container ports required by the Service or Gateway.
- Build and tag images reproducibly.
- Scan image dependencies and track the base image.
- Write a local or test-cluster run path for the workload.
- Add smoke tests for startup, health, request path, and shutdown.

## Platform Engineer Checklist

Engineers usually own the deployment route, runtime policy, CI/CD, observability, scaling, and operations.

### Cloud Function Engineering Checklist

- Select the hosting plan based on latency, traffic pattern, networking needs, and cost profile.
- Configure timeout, memory, CPU, concurrency, and max instances/reserved concurrency based on load tests.
- Define retry, backoff, and dead-letter behavior for event-driven functions.
- Confirm queue visibility timeout and function timeout are compatible where applicable.
- Configure least-privilege execution identity.
- Put secrets in a managed secret store or managed identity path.
- Add CI/CD with reproducible package/build artifacts.
- Configure staging or deployment slots when supported.
- Add logs, metrics, traces, alerts, and dashboards.
- Load test upstream and downstream throughput constraints, not only function runtime.
- Configure throttling or concurrency limits where downstream services cannot absorb spikes.
- Confirm cold-start behavior is acceptable for the product SLA.
- Add runbook steps for stuck retries, poison messages, cost spikes, and dependency outages.
- Verify no function app grouping creates unwanted shared scaling, shared config, or shared deploy blast radius.

### Kubernetes Engineering Checklist

- Use declarative manifests, Helm, Kustomize, GitOps, or IaC as the deploy source of truth.
- Validate manifests before deployment.
- Enforce labels, selectors, namespace, owner, app, version, environment, and component metadata.
- Do not hand-manage ReplicaSets owned by Deployments.
- Use rollout status checks and rollback plans.
- Set `revisionHistoryLimit` high enough to preserve rollback ability.
- Avoid setting fixed replica counts when HPA owns scaling.
- Add HPA or autoscaling policy only after metrics and resource requests are valid.
- Configure PodDisruptionBudget for workloads that require availability during drains or upgrades.
- Define Service, Ingress, Gateway, DNS, TLS, and route policy explicitly.
- Add NetworkPolicy where namespace isolation or service-to-service boundaries matter.
- Use per-workload ServiceAccounts; avoid default ServiceAccount access.
- Disable service account token automount unless the workload needs Kubernetes API access.
- Enforce Pod Security Standards at namespace or admission level.
- Set non-root security context and disallow privilege escalation where possible.
- Add resource quotas and limit ranges at namespace level.
- Configure central logs, metrics, traces, events, and audit trails.
- Verify image pull secrets, private registry policy, and image provenance.
- Add safe database migration or side-effect sequencing when deploy changes data.

## Architect Checklist

Architects usually own the service boundary, platform choice, tenancy, resilience, security model, and cost posture.

### Cloud Function Architecture Checklist

- Confirm the workload is actually a function fit: event-driven, bounded duration, stateless, and scalable.
- Choose between function, container service, Kubernetes service, workflow engine, or managed batch based on runtime duration, statefulness, networking, latency, and control needs.
- Define trigger semantics: HTTP, timer, queue, event bus, object storage, stream, webhook, or workflow step.
- Define idempotency strategy and idempotency key ownership.
- Define consistency expectations and duplicate-event handling.
- Define durable orchestration when the workflow is long-running or multi-step.
- Define identity, secrets, private network access, and data residency.
- Define availability target, cold-start tolerance, retry budget, and failure mode.
- Define cost guardrails: max instances, reserved concurrency, budgets, alerts, and cost anomaly detection.
- Define observability minimums: traces, logs, metrics, correlation IDs, synthetic tests, SLO dashboards.
- Define deployment strategy: staging slot, traffic split, canary, rollback, or blue/green.
- Define compliance and privacy boundaries for logs and payloads.

### Kubernetes Architecture Checklist

- Decide whether the workload belongs on Kubernetes, serverless functions, managed Cloud Run-style container runtime, batch, or a workflow system.
- Define cluster tenancy model: shared cluster, per-team namespace, per-env cluster, or dedicated regulated cluster.
- Define namespace, RBAC, NetworkPolicy, Pod Security, quota, and secret boundaries.
- Define ingress/egress architecture: Gateway, Ingress, service mesh, private endpoint, or internal-only service.
- Define failure-domain model: zones, regions, node pools, disruption budgets, topology spread, and cluster upgrade windows.
- Define service-to-service identity and authorization.
- Define deployment strategy and rollback standard.
- Define autoscaling model: HPA, KEDA, Knative, VPA, cluster autoscaler, or provider autoscaling.
- Define observability standard: logs, metrics, traces, service-level dashboards, runbooks, and incident ownership.
- Define workload portability boundaries: raw Kubernetes, Helm, Kustomize, Operators, Knative Services, or managed provider abstractions.
- Define cost model: request/limit hygiene, overprovisioning tolerance, idle capacity, autoscaler settings, and namespace/showback.

## Checklist Families To Turn Into Primitives

These should become source-backed primitive opportunities first. Promote only after fixture coverage and proof.

### Cloud Function Primitive Opportunities

| Primitive slug | Input | Output | Purpose |
| --- | --- | --- | --- |
| `serverless.detect_function_workload` | SessionEventSet | WorkloadIntent | Detect Lambda/Cloud Functions/Azure Functions/Knative function work |
| `serverless.define_event_contract` | Intent + SourceRefs | EventContract | Normalize trigger, payload, response, and error contract |
| `serverless.validate_idempotency` | FunctionCode + EventContract | IdempotencyFindingSet | Find missing duplicate-event handling |
| `serverless.validate_completion` | FunctionCode | CompletionFindingSet | Detect missing HTTP response, background work, or manual exit |
| `serverless.validate_runtime_config` | FunctionConfig | RuntimeConfigReport | Check timeout, memory, concurrency, max instances, and quotas |
| `serverless.validate_retry_dlq` | FunctionConfig + TriggerContract | DeliveryPolicyReport | Check retry, backoff, DLQ, poison-message behavior |
| `serverless.validate_identity_secrets` | IaC + FunctionConfig | IdentitySecretReport | Check managed identity, least privilege, secret store references |
| `serverless.validate_cold_start` | FunctionPackage + RuntimeConfig | ColdStartRiskReport | Flag dependency bloat, large package, and low-concurrency choices |
| `serverless.validate_observability` | FunctionCode + IaC | ObservabilityReport | Check logs, metrics, tracing, correlation ids, alerts |
| `serverless.generate_review_bundle` | SessionEventSet + SourceRefs | ReviewFindingSet | Emit AIDevObserver findings for serverless reinvention/missing checks |

### Kubernetes Primitive Opportunities

| Primitive slug | Input | Output | Purpose |
| --- | --- | --- | --- |
| `k8s.detect_workload_shape` | SessionEventSet | WorkloadShape | Detect Deployment/Job/CronJob/StatefulSet/Knative/service work |
| `k8s.validate_manifest_schema` | ManifestSet | ManifestValidationReport | Parse and validate Kubernetes YAML |
| `k8s.validate_deployment_basics` | DeploymentManifest | DeploymentFindingSet | Check labels, selectors, pod template, strategy, revision history |
| `k8s.validate_probes` | PodTemplate | ProbeFindingSet | Check readiness, liveness, startup probe suitability |
| `k8s.validate_resources` | PodTemplate | ResourcePolicyReport | Check requests/limits and namespace policy fit |
| `k8s.validate_service_account` | ManifestSet | ServiceAccountReport | Detect default SA use and token automount issues |
| `k8s.validate_rbac_least_privilege` | RBACManifestSet | RBACFindingSet | Flag broad role bindings and cluster-admin shortcuts |
| `k8s.validate_network_policy` | ManifestSet | NetworkPolicyReport | Check whether pod/network boundaries are explicit |
| `k8s.validate_pod_security` | PodTemplate | PodSecurityReport | Map workload to Baseline/Restricted expectations |
| `k8s.validate_autoscaling` | Workload + HPAManifest | AutoscalingReport | Check metrics, requests, min/max, and fixed replicas conflict |
| `k8s.validate_rollout_plan` | DeploymentManifest + CIConfig | RolloutPlanReport | Check rollout status, rollback, canary/traffic split support |
| `k8s.validate_observability` | ManifestSet + AppConfig | ObservabilityReport | Check logs, metrics, traces, alerts, dashboards |
| `k8s.generate_review_bundle` | SessionEventSet + SourceRefs | ReviewFindingSet | Emit AIDevObserver findings for Kubernetes reinvention/missing checks |

### Knative / Kubernetes-Native Function Opportunities

| Primitive slug | Input | Output | Purpose |
| --- | --- | --- | --- |
| `knative.detect_function_project` | RepoSnapshot | KnativeFunctionCandidate | Detect `func`/`kn func` function projects |
| `knative.validate_service_contract` | KnativeService | KnativeServiceReport | Check Service, Route, Configuration, Revision assumptions |
| `knative.validate_traffic_split` | KnativeRoute | TrafficSplitReport | Check gradual rollout, pinned revision, canary behavior |
| `knative.validate_scale_to_zero` | KnativeService | ScalePolicyReport | Check cold-start, min-scale, concurrency, RPS target choices |
| `knative.validate_cloudevent_contract` | FunctionCode + Config | CloudEventContractReport | Check event type, source, schema, and sink behavior |

## AIDevObserver Finding Types

These are the likely high-value findings in real AI coding sessions.

### Reinvention Findings

- Agent writes a new Lambda handler scaffolder while repo already has a handler template.
- Agent writes custom Kubernetes Deployment YAML while repo already has Helm/Kustomize templates.
- Agent writes custom health endpoints while repo has a standard health-check module.
- Agent writes retry/backoff helpers while repo has a shared delivery-policy library.
- Agent creates bespoke IAM/RBAC policy while platform registry has least-privilege templates.
- Agent writes a custom queue consumer loop when the platform has a serverless-trigger template.
- Agent writes a new manifest linter while a kubeconform/kube-linter/OPA/policy path already exists.

### Missing Checklist Findings

- Cloud function lacks idempotency handling for duplicate events.
- Function timeout exceeds queue visibility timeout or has no timeout reasoning.
- Function makes outbound calls without retry/backoff/jitter or throttle tolerance.
- Function stores request/user data in global execution environment.
- Function writes temporary files without cleanup.
- Function app groups unrelated functions that should have separate scaling or deployment blast radius.
- Kubernetes Deployment lacks readiness/liveness/startup probes.
- Kubernetes Pod lacks resource requests/limits.
- Kubernetes workload uses the default ServiceAccount unnecessarily.
- Kubernetes manifest gives broad RBAC or cluster-admin shortcuts.
- Pod security context allows root/privilege escalation without justification.
- Workload exposes a service without NetworkPolicy in a segmented namespace.
- Deployment managed by HPA also pins replicas in Git without clear ownership.
- Side-effecting deploy step lacks rollback/compensation.

### Token-Waste Findings

- Agent reads whole Kubernetes docs or generated YAML instead of applying a checklist primitive.
- Agent scans every manifest manually instead of calling `k8s.validate_manifest_schema`.
- Agent asks the model to reason over a full Terraform plan when a small IaC summary is enough.
- Agent repeatedly patches YAML formatting instead of using existing Helm/Kustomize route.
- Agent asks for provider-agnostic cloud function code while the actual trigger/provider is already known.

## Demo Session Candidates

### Demo: Cloud Function Missing Idempotency

```text
User: Build an SQS-triggered Lambda to process invoice events.
Agent: Writes handler and database write path.
Observer finding: missing idempotency and queue visibility/timeout check.
Registry route: serverless.define_event_contract -> serverless.validate_idempotency -> serverless.validate_retry_dlq -> serverless.validate_observability.
```

Expected PlanDelta candidate:

```json
{"v":1,"p":"dense","t":0,"b":[0,0,0,0],"r":[],"g":[]}
```

### Demo: Kubernetes Deployment Missing Probes And Resources

```text
User: Containerize and deploy this FastAPI service to Kubernetes.
Agent: Writes Deployment and Service from scratch.
Observer finding: existing app deployment template found; generated manifest lacks probes, resources, non-root security context, rollout checks.
Registry route: k8s.validate_manifest_schema -> k8s.validate_deployment_basics -> k8s.validate_probes -> k8s.validate_resources -> k8s.validate_pod_security.
```

### Demo: Overbroad RBAC

```text
User: Give this controller permissions so it can update jobs.
Agent: Creates ClusterRoleBinding with broad permissions.
Observer finding: broad RBAC reinvention; route to least-privilege Role template and proof check.
Registry route: k8s.validate_rbac_least_privilege -> k8s.generate_review_bundle.
```

### Demo: Knative Function From Kubernetes Workload

```text
User: Make this event handler run on Kubernetes but scale to zero.
Agent: Starts writing raw Deployment, HPA, and Ingress.
Observer finding: Knative function/service route likely cheaper and more appropriate.
Registry route: knative.detect_function_project -> knative.validate_service_contract -> knative.validate_scale_to_zero -> knative.validate_traffic_split.
```

## CandidateBundle Sketch

```text
Q deploy_fastapi_to_kubernetes
O K8sDeploymentReviewReport
T0 k8s_workload_review

S0 detect SessionEventSet>WorkloadShape req:session allow:-
S1 parse ManifestSet>ManifestValidationReport req:yaml allow:-
S2 deployment DeploymentManifest>DeploymentFindingSet req:workload allow:-
S3 probes PodTemplate>ProbeFindingSet req:readiness,liveness allow:-
S4 resources PodTemplate>ResourcePolicyReport req:req_limit allow:-
S5 security PodTemplate>PodSecurityReport req:nonroot,leastpriv allow:-
S6 emit FindingSet>K8sDeploymentReviewReport req:review allow:wrap

C0.0 k8s_detect_workload SessionEventSet>WorkloadShape fx:0 mem:i c:h tools:- tr:C r:R3
C1.0 k8s_validate_manifest ManifestSet>ManifestValidationReport fx:0 mem:i c:h tools:- tr:C r:R3
C2.0 k8s_validate_deployment DeploymentManifest>DeploymentFindingSet fx:0 mem:i c:h tools:- tr:C r:R3
C3.0 k8s_validate_probes PodTemplate>ProbeFindingSet fx:0 mem:i c:h tools:- tr:C r:R3
C4.0 k8s_validate_resources PodTemplate>ResourcePolicyReport fx:0 mem:i c:h tools:- tr:C r:R3
C5.0 k8s_validate_pod_security PodTemplate>PodSecurityReport fx:0 mem:i c:h tools:- tr:C r:R3
C6.0 finding_emit_review FindingSet>K8sDeploymentReviewReport fx:0 mem:i c:h tools:wrap tr:C r:R3
```

Expected dense PlanDelta:

```json
{"v":1,"p":"dense","t":0,"b":[0,0,0,0,0,0,0],"r":[],"g":[]}
```

## Surfaces To Ingest For Real Primitive Evidence

Prioritize source surfaces that are likely to contain real repeated patterns:

- official provider quickstarts and best-practice docs;
- repo-local Terraform modules;
- Helm charts;
- Kustomize overlays;
- Kubernetes manifests under `deploy/`, `infra/`, `k8s/`, `.github/`, and `charts/`;
- serverless framework configs;
- AWS SAM templates;
- CloudFormation templates;
- Terraform `aws_lambda_function`, `google_cloudfunctions_function`, `azurerm_linux_function_app`, and Kubernetes provider resources;
- Pulumi components;
- CDK constructs;
- GitHub Actions deployment workflows;
- Argo CD / Flux manifests;
- Skaffold, Tilt, Garden, and devspace configs;
- OPA/Rego, Kyverno, Gatekeeper, kube-linter, kube-score, conftest policy packs;
- incident runbooks and postmortems for deploy failure, cold starts, overbroad permissions, and scaling failures.

## Benchmark Fixtures To Generate

Initial fixture families:

- `lambda_queue_idempotency_missing`
- `lambda_recursive_invocation_cost_spike`
- `cloud_run_function_background_activity`
- `cloud_run_function_temp_file_leak`
- `azure_function_wrong_hosting_plan`
- `azure_function_missing_app_insights`
- `k8s_deployment_missing_probes`
- `k8s_deployment_missing_resources`
- `k8s_default_service_account_used`
- `k8s_cluster_admin_shortcut`
- `k8s_no_network_policy`
- `k8s_hpa_without_requests`
- `knative_raw_deployment_reinvented`
- `knative_missing_traffic_split`

Each fixture should include:

```text
session transcript
repo/file evidence summary
existing template/helper/source_ref
expected findings
expected false-positive traps
privacy/redaction expectations
candidate-only primitive opportunities
```

## Readiness Path

Use readiness levels rather than treating every checklist item as production truth.

```text
R0 observed checklist item
R1 linked to official source
R2 expressed as primitive opportunity
R3 fixture-backed candidate primitive
R4 parser/checker implemented
R5 source-ref precision tested
R6 local repo integration tested
R7 benchmark pass
R8 auto-review eligible
R9 promoted production primitive
```

For now, every primitive in this note is a `primitive_opportunity`, not a promoted primitive.

## Next Steps

- Add a `cloud_functions_k8s` source-surface family to the context-foundry loop.
- Generate smoke fixtures from the demo session candidates above.
- Add a local manifest detector for Kubernetes YAML, Helm, Kustomize, Terraform, SAM, and Serverless Framework files.
- Add review findings for missing probes, missing resources, default ServiceAccount, broad RBAC, missing idempotency, and function temp-file leaks.
- Connect findings to source refs rather than generic advice.
- Keep safety as a manager lens, but lead product copy with speed, reuse, and token savings.

