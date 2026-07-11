# Capability Binding & Infrastructure-from-Code Landscape

**Question this answers:** *Are there tools that do purpose / capability / contract-defined programming that completely abstracts out cloud-function and K8s-worker programming?* — i.e. the **infrastructure-from-code / workload-spec / platform-capability-API / serverless-runtime** category.

**Verdict (short):** **No tool does the full Teleon thesis.** These tools abstract **deployment / workloads / platform resources**, not the capability **lifecycle**. The closest (Kratix, Radius, Score, Nitric) abstract *where and how a workload deploys* or *capability-as-a-self-service-API for provisioning a resource* — none of them declares a purpose-defined capability whose **implementation** is selected from candidates on **evidence**, gated for promotion, kept with a reversible rollback, and bounded by human approval. They are **CapabilityTask binding targets / execution adapters** behind a `CapabilityTaskBindingProvider`; **Teleon is the capability-lifecycle control plane *above* them**, and the **local reference binding stays the stable first path**.

**Distinct from existing catalogs — do not duplicate.** Durable-workflow + agent runtimes are cataloged separately:
- [`_repos/shared-backend-components/architecture/teleon_runtime_landscape.json`](../../architecture/teleon_runtime_landscape.json) — Temporal, DBOS, Dapr, Hatchet, Inngest, Trigger.dev, ARK, kagent, AgentScope, agent-sandbox.
- [`_repos/shared-backend-components/architecture/teleon_adjacent_extended.json`](../../architecture/teleon_adjacent_extended.json) — Restate, Prefect, Kestra, Windmill, Flyte, Ray, Modal, Cloudflare Workflows/Agents, Letta, LangGraph, Bedrock AgentCore, Vertex Agent Engine.

This catalog is the **NEW** infrastructure-from-code / workload-spec / platform-capability-API / serverless-runtime category. Machine-readable companion: [`_repos/shared-backend-components/architecture/capability_binding_landscape.json`](../../architecture/capability_binding_landscape.json); proof: `_repos/shared-backend-components/scripts/check_capability_binding_landscape.py --self-test`.

**Governance carried throughout:** discovery ≠ trust; candidate ≠ active (status is never `active`); a workload spec / compile target ≠ truth; every entry carries a `teleon_local_equivalent` (the local reference binding) and a `do_not_adopt_as_primary`; no raw keys. License flags are honest (`license_confidence` = `verified` / `unverified`).

---

## The three sub-families (so we never blur them)

1. **Infrastructure-from-code** — *Nitric, Wing, Encore, Klotho.* You write application code; the tool **infers and provisions cloud infrastructure** (functions, queues, storage, DBs). Abstracts *cloud-function/worker plumbing from code*.
2. **Workload / app / platform spec** — *Score, OAM + KubeVela, Radius, Kratix, Crossplane.* You **declare a desired workload / resource / capability shape**; a platform fulfils it. Abstracts *the deployment target / resource graph / self-service API*.
3. **Serverless / scaler runtime** — *Knative, KEDA, Serverless Framework.* **Runs and autoscales** functions/containers (incl. scale-to-zero). Abstracts *the run/route/scale plumbing*.

What every one of them **lacks vs Teleon's lifecycle**: a stable **purpose/capability contract** above evolving implementations · **side-by-side candidate implementations** · a **scorecard** · **eval-gated promotion** (evidence decides, never the spec/benchmark itself) · a **reversible rollback object** · **human boundary-expansion approval** · a Baltor-style **truth boundary**.

---

## Closest matches (ranking table)

`closeness_rank` 1 = closest to the *capability-contract* idea. Per the brief, Kratix / Radius / Score / Nitric rank highest.

| Rank | Tool | Sub-family | What it abstracts | The lifecycle gap | Binding role | Validation risk |
|---|---|---|---|---|---|---|
| **1** | [Kratix](https://www.kratix.io/) | platform-capability-API | A platform capability packaged as a **Promise** = a self-service, governed K8s API (deps + request API + provisioning workflows + destination rules) | Provisions a resource on request; no candidate-vs-baseline, no scorecard, no eval-gated promotion, no rollback object, no truth boundary | platform_capability_api | positioning_threat |
| **1** | [Radius](https://radapp.io/) | resource-composition | App + dependencies definition; platform engineers define **Resource Types** implemented by **Recipes** (Terraform/Bicep) per Environment | Recipe is *how to provision*; no candidate comparison / evidence / promotion / rollback / boundary | platform_capability_api | thesis_strengthening |
| **1** | [Score](https://score.dev/) | portable-workload-spec | One YAML **workload spec** → translated to Compose / K8s / Helm / Cloud Run / Fly.io | A portable *deployment description*; no purpose, candidate, scorecard, promotion, rollback | workload_spec_export | thesis_strengthening |
| **2** | [Nitric](https://nitric.io/) | infrastructure-from-code | Code declares resource needs → **infers + provisions** AWS/GCP/Azure/K8s (no hand-written Terraform) | Abstracts *where code deploys*, not whether a candidate capability is promoted | capability_compile_target | thesis_strengthening |
| **2** | [Crossplane](https://www.crossplane.io/) | resource-composition | **XRD** defines a platform API schema; **Composition** maps it to managed resources; consumers create a **claim** | A control plane for *resources*, reconciling to desired state; no capability candidate/evidence/promotion/rollback | platform_capability_api | positioning_threat |
| **3** | [Encore](https://encore.dev/) | backend-infra-from-code | Declare infra in code (services/DBs/Pub-Sub/cron) → provisions in your AWS/GCP; full local dev | Backend framework, not capability lifecycle | capability_compile_target | safe_to_wrap |
| **3** | [Wing](https://www.winglang.io/) | cloud-oriented-language | Unifies infra (preflight) + runtime (inflight) in one language; **local cloud simulator** | A language for cloud apps; pre-release; no capability lifecycle | capability_compile_target | thesis_strengthening |
| **3** | [OAM + KubeVela](https://oam.dev/) | app-delivery-model | App-centric model (components/traits/policies/workflow) delivered across environments | App delivery, not capability lifecycle | workload_spec_export | thesis_strengthening |
| **4** | [Knative](https://knative.dev/) | k8s-serverless-runtime | Run/autoscale serverless workloads on K8s (scale-to-zero, revisions, routing) | Runs + routes; revisions/traffic-split are deployment routing, **not** eval-gated promotion | execution_adapter | safe_to_wrap |
| **4** | [Klotho](https://klo.dev/) | infrastructure-from-code | Annotated code → generated IaC via the Klotho Engine | Same IfC gap **and archived** — not a live target | capability_compile_target | thesis_strengthening |
| **5** | [KEDA](https://keda.sh/) | event-driven-scaler | Scale any K8s container to/from zero on event-source metrics (ScaledObject) | Only decides *how many replicas*; narrowest slice | scaler | safe_to_wrap |
| **5** | [Serverless Framework](https://www.serverless.com/) | serverless-framework | Package/deploy functions + resources from `serverless.yml` (mainly AWS Lambda) | Deploys functions; **v4+ proprietary/license-key** constrains it | capability_compile_target | positioning_threat |

---

## Per-tool detail

### Infrastructure-from-code

#### Nitric — `closeness_rank 2`, candidate, Apache-2.0 (verified)
- **Abstracts:** multi-language IfC — application code declares APIs/queues/topics/key-value/storage/schedules; Nitric infers and provisions cloud infrastructure, deploying the same code to AWS (Lambda/API Gateway/SQS/SNS/DynamoDB), GCP, Azure, or your own Kubernetes cluster (pre-built providers run Pulumi or Terraform). Sources: [nitric.io](https://nitric.io/), [github.com/nitrictech/nitric](https://github.com/nitrictech/nitric), [docs/providers](https://nitric.io/docs/providers).
- **Lacks vs Teleon lifecycle:** no purpose/capability contract decoupled from implementation, no candidate comparison, no scorecard, no eval-gated promotion, no rollback object, no boundary approval, no truth boundary.
- **Binding:** `capability_compile_target`. A CapabilityTask whose runtime selection lands on a cloud function can **compile to Nitric**; the local function binding (`teleon.local_function@v1`) stays the stable first path.

#### Encore — `closeness_rank 3`, candidate, MPL-2.0 (verified)
- **Abstracts:** backend IfC — declare infra (services/DBs/Pub-Sub/cron) directly in TypeScript/Go code; Encore parses it and provisions per-environment into your own **AWS/GCP** account with no Terraform/Pulumi; runs the whole backend locally with real services/DBs/Pub-Sub via one command. The OSS framework/parser/compiler/runtime/CLI are MPL-2.0 and self-hostable; **Encore Cloud** is a separate commercial managed plane. Sources: [encore.dev](https://encore.dev/), [github.com/encoredev/encore](https://github.com/encoredev/encore), [docs/infra](https://encore.dev/docs/platform/infrastructure/infra).
- **Lacks vs Teleon lifecycle:** backend service/infra provisioning, not capability lifecycle (no contract/candidate/scorecard/promotion/rollback/boundary/truth).
- **Binding:** `capability_compile_target`; its strong local-dev story aligns with our local-first stance, but Teleon's contract + evidence + promotion sit above its provisioning.

#### Wing (Winglang) — `closeness_rank 3`, research, MIT (verified)
- **Abstracts:** a cloud-oriented language unifying infrastructure (preflight) and runtime (inflight) code; compiles to Terraform/CloudFormation and **runs locally in a full cloud simulator** (functions/queues/buckets). **Still pre-release in 2026** — AWS fully supported (Terraform engine), GCP/Azure partial. Sources: [winglang.io](https://www.winglang.io/), [github.com/winglang/wing](https://github.com/winglang/wing), [LICENSE](https://github.com/winglang/wing/blob/main/LICENSE.md), [supported clouds](https://www.winglang.io/docs/faq/supported-clouds-services-and-engines/supported-clouds).
- **Lacks vs Teleon lifecycle:** a language for cloud apps; no capability lifecycle. Pre-release maturity is an adoption caution → status `research`.
- **Binding:** `capability_compile_target`. The **local cloud simulator** is the most interesting signal — it validates a local-equivalent path for cloud primitives, exactly the `teleon.local_function` pattern.

#### Klotho — `closeness_rank 4`, **research_archived**, Apache-2.0 (**unverified** — re-check archived repo)
- **Abstracts:** IfC that took annotated application code and generated cloud IaC via the open-source **Klotho Engine**. Sources: [klo.dev](https://klo.dev/), [InfraCopilot announcement](https://klo.dev/announcing-infracopilot/), [github.com/klothoplatform/infracopilot](https://github.com/klothoplatform/infracopilot).
- **Status:** **No longer actively developed — the repo is archived;** the vendor pivoted to **InfraCopilot** (a conversational IaC editor on the same engine). Cannot be a live binding target. Its existence-then-archival is evidence the IfC category churns — owning the capability *lifecycle* (not the codegen) is the durable position.
- **Binding:** `capability_compile_target` for reference only. Re-verify license against the archived repo before quoting it.

### Workload / app / platform spec

#### Kratix — `closeness_rank 1` (closest), candidate, Apache-2.0 (verified)
- **Abstracts:** platform engineers package a capability (database, CI/CD pipeline, K8s cluster, VM, third-party service) as a **Promise** — a **self-service, governed Kubernetes API**: declared dependencies + an API for how consumers request it + provisioning workflows + destination rules. This is the **single closest match to "capability as a self-service API contract."** Sources: [kratix.io](https://www.kratix.io/), [Promise reference](https://docs.kratix.io/main/reference/promises/intro), [CNCF blog](https://www.cncf.io/blog/2025/08/08/from-terraform-modules-to-platform-services-simplify-infrastructure-management-with-the-kratix-cli/). Core Apache-2.0 (Syntasso); **Syntasso Kratix Enterprise** is a separate commercial product.
- **Lacks vs Teleon lifecycle:** a Promise **provisions a resource** when requested; it does **not** declare a purpose whose *implementation* evolves while the contract stays stable. No side-by-side candidates, no scorecard, no eval-gated promotion, no rollback object, no boundary approval, no truth boundary. It answers "give me a database," not "is this candidate way of fulfilling the capability good enough to promote?"
- **Binding:** `platform_capability_api`. A CapabilityTask binds **down** onto a Promise; Teleon keeps the contract + candidate comparison + eval-gated promotion + rollback **above** it. `teleon.local_capability_api@v1` stays the stable first path. Marked `positioning_threat` because it markets near the "capability self-service API" surface.

#### Radius — `closeness_rank 1`, candidate, Apache-2.0 (verified), CNCF Sandbox
- **Abstracts:** a cloud-agnostic application platform; developers describe an app + dependencies, platform engineers define org-specific **Resource Types** implemented by **Recipes** (Terraform configs or Bicep) per **Environment**, so the same app maps to dev vs prod infra. CNCF Sandbox (accepted 2024-04-16; IP owned by CNCF; Microsoft-originated). Sources: [github.com/radius-project/radius](https://github.com/radius-project/radius), [CNCF project page](https://www.cncf.io/projects/radius/), [Resource Types blog](https://opensource.microsoft.com/blog/2025/06/30/expanding-platform-engineering-capabilities-with-radius-resource-types/).
- **Lacks vs Teleon lifecycle:** Resource Types + Recipes select *which infrastructure fulfils a declared resource*; no candidate-implementation comparison, no scorecard, no eval-gated promotion, no rollback object, no boundary, no truth boundary.
- **Binding:** `platform_capability_api`. The **Resource-Type-with-Recipes** split is external **confirmation** that a stable contract above swappable implementations is the right shape; Teleon's evidence + promotion decide *whether* the candidate ships.

#### Crossplane — `closeness_rank 2`, candidate, Apache-2.0 (verified), CNCF **Graduated** (Oct 2025)
- **Abstracts:** build **custom control planes** on Kubernetes — an **XRD** (CompositeResourceDefinition) defines a platform API schema, a **Composition** maps it to a graph of managed resources, consumers create a **claim**. Sources: [crossplane.io](https://www.crossplane.io/), [github.com/crossplane/crossplane](https://github.com/crossplane/crossplane), [CNCF project page](https://www.cncf.io/projects/crossplane/).
- **Lacks vs Teleon lifecycle:** XRD/Composition/claim **provision and reconcile resources** toward desired state; no purpose/capability selected from candidates on evidence, no scorecard, no eval-gated promotion, no rollback-as-object, no boundary, no truth boundary. Its "custom control plane" is a **resource** control plane, not a **capability-lifecycle** control plane — hence `positioning_threat`.
- **Binding:** `platform_capability_api`; "publish your own API" validates contract-above-implementation, but Teleon adds the candidate/evidence/promotion/rollback/truth layer.

#### Score — `closeness_rank 1`, candidate, Apache-2.0 (verified), CNCF Sandbox
- **Abstracts:** a platform-agnostic, container-based **workload specification** — define a workload once in one YAML file, then a Score Implementation CLI translates it to **Docker Compose** (`score-compose`), **Kubernetes** (`score-k8s`), **Helm**, **Google Cloud Run**, **Fly.io**. Eliminates per-platform config drift. Sources: [score.dev](https://score.dev/), [docs.score.dev](https://docs.score.dev/docs/), [github.com/score-spec/spec](https://github.com/score-spec/spec), [CNCF blog](https://www.cncf.io/blog/2023/11/13/decoding-workload-specification-for-effective-platform-engineering/).
- **Lacks vs Teleon lifecycle:** describes a single workload's resources/ports/dependencies for translation; no purpose, candidates, scorecard, promotion, rollback, boundary, or truth boundary. A portable **deployment** description.
- **Binding:** `workload_spec_export`. Teleon **exports** a CapabilityTask's selected implementation to a Score spec; the contract is exported *to* Score, never replaced *by* it. `teleon.capabilitytask_spec@v1` stays the source of truth. "Define once, translate to many targets" directly validates runtime-neutral binding.

#### OAM + KubeVela — `closeness_rank 3`, candidate, Apache-2.0 (verified), CNCF Incubating
- **Abstracts:** the **Open Application Model** is a higher-level, app-centric abstraction (components + traits + policies + workflow) across hybrid/multi-cloud; **KubeVela** implements it as an application delivery platform that hides Kubernetes behind a simple app definition + delivery workflow. Sources: [oam.dev](https://oam.dev/), [github.com/kubevela/kubevela](https://github.com/kubevela/kubevela), [CNCF project page](https://www.cncf.io/projects/kubevela/), [core concepts](https://kubevela.io/docs/getting-started/core-concept/).
- **Lacks vs Teleon lifecycle:** models and **delivers** an application across environments; no purpose-defined capability selected from candidates on evidence, no scorecard, no eval-gated promotion, no rollback-as-object, no boundary, no truth boundary.
- **Binding:** `workload_spec_export`. Teleon can export a CapabilityTask's chosen implementation to an OAM/KubeVela definition; the components/traits separation validates app-centric abstraction.

### Serverless / scaler runtime

#### Knative — `closeness_rank 4`, candidate, Apache-2.0 (verified), CNCF **Graduated** (Sep 2025)
- **Abstracts:** a Kubernetes-native serverless runtime — deploy/run serverless + event-driven workloads with request-driven autoscaling (incl. **scale-to-zero**), revisions, and traffic routing. Sources: [knative.dev](https://knative.dev/), [CNCF project page](https://www.cncf.io/projects/knative/), [graduation announcement](https://www.cncf.io/announcements/2025/10/08/cloud-native-computing-foundation-announces-knatives-graduation/).
- **Lacks vs Teleon lifecycle:** **runs and autoscales** a service; its revisions/traffic-split are **deployment routing, not** evidence-gated capability promotion; no capability contract, candidate comparison, scorecard, rollback-as-capability-object, boundary, or truth boundary.
- **Binding:** `execution_adapter`. A CapabilityTask whose runtime selection picks K8s-serverless binds to a Knative Service; the local function binding stays the stable first path.

#### KEDA — `closeness_rank 5`, candidate, Apache-2.0 (verified), CNCF **Graduated** (2023)
- **Abstracts:** Kubernetes event-driven autoscaling — scale any container **to/from zero** based on event-source metrics (queues/streams/DBs/telemetry; 70+ scalers) via a **ScaledObject**; acts as a K8s metrics server. Sources: [keda.sh](https://keda.sh/), [github.com/kedacore/keda](https://github.com/kedacore/keda).
- **Lacks vs Teleon lifecycle:** only decides **how many replicas** of a worker run; the narrowest slice here. No capability contract/candidate/scorecard/promotion/rollback/boundary/truth.
- **Binding:** `scaler`. A CapabilityTask bound to a K8s worker can attach KEDA as the scaler; `teleon.local_worker_pool@v1` stays the stable first path.

#### Serverless Framework — `closeness_rank 5`, **reference**, license: **proprietary (v4+) / MIT (v3 and earlier)** (verified)
- **Abstracts:** a YAML-config framework that packages and deploys serverless functions + managed-service resources (mainly **AWS Lambda**) — abstracts packaging/deploy/IAM/event-wiring behind a `serverless.yml`. Sources: [serverless.com](https://www.serverless.com/), [github.com/serverless/serverless](https://github.com/serverless/serverless), [V4 license model](https://www.serverless.com/blog/serverless-framework-v4-a-new-model).
- **License flag:** **CLI v4+ is proprietary and requires login / a license key** (free for orgs under $2M annual revenue; paid above); v3 and earlier remain MIT. This makes it a **constrained** target — prefer Apache/MIT targets (Score/Nitric) for actual binding.
- **Lacks vs Teleon lifecycle:** deploys functions + resources from a config; no capability contract/candidate/scorecard/promotion/rollback/boundary/truth.
- **Binding:** `capability_compile_target`, kept as the incumbent **reference** that defines the "deploy functions from a spec" surface Teleon binds above.

---

## CapabilityTask binding map

A Teleon **CapabilityTask** (stable, purpose-defined) binds **down** onto a target via a `CapabilityTaskBindingProvider`. The contract, runtime selection, candidates, evidence/scorecards, eval-gated promotion, rollback, and boundary approval stay **above** the binding. Targets marked **[xref]** live in the existing catalogs and are *not* re-added here.

| CapabilityTask binding | Target | Sub-family | Catalog |
|---|---|---|---|
| compile-to-Nitric | Nitric (AWS/GCP/Azure/K8s) | infrastructure-from-code | this catalog |
| compile-to-Encore | Encore (AWS/GCP) | backend-infra-from-code | this catalog |
| compile-to-Wing | Wing simulator / Terraform | cloud-oriented-language | this catalog |
| export-Score | Score → Compose/K8s/Helm/Cloud Run/Fly.io | portable-workload-spec | this catalog |
| export-OAM | OAM/KubeVela app definition | app-delivery-model | this catalog |
| Kratix-Promise | Kratix Promise (self-service API) | platform-capability-API | this catalog |
| Radius-Recipe | Radius Resource Type + Recipe | resource-composition | this catalog |
| Crossplane-claim | Crossplane XRD/Composition/claim | resource-composition | this catalog |
| Knative-service | Knative Service (scale-to-zero) | k8s-serverless-runtime | this catalog |
| KEDA-worker | KEDA ScaledObject on a worker | event-driven-scaler | this catalog |
| Serverless-deploy | Serverless Framework (`serverless.yml`) | serverless-framework | this catalog (reference) |
| Temporal-workflow **[xref]** | Temporal | durable-workflow | `teleon_runtime_landscape.json` |
| Modal-function **[xref]** | Modal | compute-backend | `teleon_adjacent_extended.json` |
| Local default (stable first path) | `teleon.local_function@v1` / `teleon.local_worker_pool@v1` | local reference binding | Teleon |

`teleon_local_equivalent` per slot: `teleon.local_function@v1` (cloud-function targets), `teleon.local_worker_pool@v1` (K8s/serverless workers + scalers), `teleon.capabilitytask_spec@v1` (workload-spec / app-delivery exports), `teleon.local_capability_api@v1` (platform-capability-API / resource-composition targets).

---

## Verdict & local-first stance

- **None of these tools does the full thesis:** purpose → contract → runtime-selection → implementation-candidate → scorecard → eval-gated promotion → rollback → human-boundary-approval. They abstract **deployment / workloads / platform resources**, **not** the capability **lifecycle**.
- **Kratix Promises** and **Crossplane XRDs/claims** come closest to "capability as a self-service API contract," and **Radius Resource Types + Recipes** and **Score workload specs** validate "stable contract above swappable implementations" — but all four stop at **provisioning / deploying a resource**. There is no candidate-vs-baseline scorecard, no eval-gated promotion, no rollback object, and no truth boundary in any of them.
- **Teleon is the capability-lifecycle control plane *above* these binding targets.** Each tool is **one switchable peer** behind a `CapabilityTaskBindingProvider`, with a governed local-equivalent fallback. The **local reference binding** (`teleon.local_function` / `teleon.local_worker_pool` / `teleon.capabilitytask_spec` / `teleon.local_capability_api`) **stays the stable first path**; no external target becomes a second control plane or a second capability registry.
- **Honest license flags:** Serverless Framework v4+ is proprietary/license-key (prefer Apache/MIT targets); Klotho is **archived** (reference only, license unverified pending re-check); Encore is MPL-2.0 (OSS framework, commercial cloud); the CNCF entries (Score/Radius/Crossplane/KubeVela/Knative/KEDA) and Kratix/Nitric core are Apache-2.0, Wing is MIT.
