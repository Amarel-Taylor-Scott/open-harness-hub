# TELEON — the intent-native, eval-gated, self-adaptive compute runtime (MASTER build prompt)

> **NAME (OWNER-DECIDED 2026-06-06 — domain `teleon.dev` owned).** Canonical naming + portfolio — single
> sources: `docs/strategy/teleon-naming-and-domain.md` + `docs/strategy/teleon-baltor-openharnesshub-portfolio.md`:
> - **Portfolio:** a HoldCo owns **Teleon** (this runtime SaaS, `teleon.dev`), **Baltor** (`baltor.ai`, the
>   applied product — a TENANT of Teleon), and **OpenHubForAI** (the open ecosystem + the open CapabilityTask
>   spec). Dependency law: Baltor → Teleon → OpenHarnessHub, never the reverse
>   (`architecture/portfolio_dependency_law.json`).
> - **Runtime product / SaaS:** **Teleon** — the purpose-driven, eval-gated, self-adaptive compute runtime.
> - **Open standard (neutral, stewarded by OpenHubForAI):** **Capability Task Specification (CTS)** / the
>   "Open CapabilityTask Spec"; the formal object/kind is **CapabilityTask**. *Teleon implements the spec.*
> - **Core object (product language):** **PurposeTask** (`PurposeTaskSpec`, shipped; an instance is
>   colloquially "a teleon") — Teleon is the reference implementation of CTS.
> - **Dashboards:** **Teleon Control Tower** (staff) · **Capability Assurance Portal** (customer).
> - **Domains:** `teleon.dev` (owned). Standard `capabilitytasks.org`/`.io` UNVERIFIED. **Caution:**
>   `teleon.ai` is an adjacent AI-agent-deployment platform — keep positioning crisp (CapabilityTask /
>   purpose-defined compute / evidence-gated promotion), avoid "deploy agents" language; trademark check before
>   public launch (see the naming doc).
> - **Superseded:** "Purpose Runtime" (my prior proposal) → **Teleon**; "Anneal" → superseded (survives only
>   as the internal metaphor for the capability compiler); "OCTS" → "CTS"; "Cairn" console sub-brand → retired.
> - **NOTE:** this master prompt predates the portfolio split; treat the portfolio + naming docs +
>   `prompts/teleon-build-kit.md` as canonical where they differ. Generic runtime concepts below are **Teleon**
>   (extracting from `src/baltor/` into `src/teleon/`), not Baltor internals.

> **One-sentence manifesto:** Cloud architecture should be organized around durable, measurable **capabilities**,
> not around static deployments of code.
> **Core invariant (top of the spec):** *A CapabilityTask may adapt its MEANS, but it may not autonomously
> change its ENDS.* Means (auto-adaptable): implementation · runtime class · prompt · parser · workflow · retry ·
> timeout · fallback order · model · tool sequence. Ends (human-gated): purpose · permissions · success criteria
> · data access · connected systems · risk class · approval requirements.

This is the SINGLE master prompt. Build as focused, proven increments (Agent subagents or direct edits); a
Workflow only on explicit owner opt-in. Never run two repo-mutating builds concurrently. Everything composes the
ALREADY-SHIPPED substrate (flywheel 318) — do not rebuild it. Sub-specs for depth:
`prompts/baltor-{purpose-driven-cloud-task-runtime,open-capability-task-standard,purpose-task-dashboard-and-standard,
path-improvement-and-skill-intake-factory,k8s-cloudfunction-template-factory}.md`; doctrine
`docs/standards/capability-task-architecture-doctrine.md`; vision `docs/architecture/purpose-task-self-adapting-execution.md`.

## TELEON CLAUSE (carry in the North Star loop)
CapabilityTask stays stable · Implementation evolves · Runtime changes · **Evidence decides** · **Policy gates
promotion** · **Humans approve boundary expansion.** A candidate is never promoted because it's new/cheap/an
agent likes it — only because it BEATS the incumbent on a scorecard, passes policy, and survives shadow+canary.
Agents are SCAFFOLDING (discover/repair/fallback), not the runtime; the **capability compiler** (the internal
"anneal" step) hardens the common path into cheap deterministic code as evidence accumulates. Self-adapt the
MEANS, never the ENDS without approval.

## Claim the lineage (signals rigor; inherit the safety results)
This is NOT invented from scratch — name and inherit the prior art (the research mandate):
- **Control loop = MAPE-K** (IBM autonomic computing, ~2003; Rainbow framework) — `Observe→Diagnose→Propose→
  Evaluate→Gate→Promote→Monitor→Rollback`. Inherit the formal-methods work on **interfering control loops**
  (critical once we have a graph of self-adapting capabilities that can oscillate/conflict).
- **Promotion = progressive delivery** (Argo Rollouts `AnalysisTemplate` / Flagger `Canary`): metric-gated
  auto-promote/auto-rollback, the `Degraded` state, multi-window canaries. Generalize the gated object from "a
  Deployment" to "a purpose contract with a portfolio of implementations," and let candidates be **generated**.
- **Intent plane = control-plane/desired-state** (Crossplane — an OAM evolution; **Kratix** calls its contracts
  "Promises" — a CapabilityTask IS a durable promise; study Kratix as substrate).
- **Eval plane = eval-driven development (EDD)** (Braintrust/MLflow/Promptfoo/LangSmith): capability-vs-regression
  eval split, version-pin every component, production regressions become test cases.
- **Standards to REUSE** (don't reinvent): JSON Schema/OpenAPI (interfaces) · CloudEvents/AsyncAPI (events) ·
  Serverless Workflow (sub-workflows) · **OpenTelemetry GenAI semconv** (agent/workflow/tool spans → extend with
  `capability.task.*`; still experimental → version-pin) · OCI (packaging) · **SLSA v1.2 + in-toto** (provenance
  on candidates/prompts/evals/bindings/promotions) · **xRegistry** (CNCF Sandbox; the capability/skill registry)
  · Score/OAM (workload description) · **OPA/Gatekeeper + Kyverno** (the policy-as-code substrate for the
  forbidden-changes / approval-required gates — name these, don't hand-wave the policy engine).

## The defensible wedge (lead with THIS, not the generic vision)
Everyone else (AWS DevOps Agent, Kiro, AgentCore, Itential, Vercel) bounds *an agent acting on existing infra*,
or treats the agent as the runtime. **Teleon's distinctive move: an implementation PORTFOLIO spanning
agentic→deterministic, plus a compiler that hardens discovered agentic behavior DOWN into cheap deterministic
execution as evidence accumulates.** Cascade: cache → deterministic parser → browser → OCR → LLM → agentic
investigation → human review; a mature task learns ~90% cheap-path / ~9% browser / <1% LLM / fraction human.
Agents at the edges (discover/repair/fallback); deterministic code on the common path. This is the **Determinism
Factory at the cloud layer** — the economic thesis competitors don't center on.

## Competitive positioning (AWS has the parts, stitched by humans — the seam is the wedge)
- **Amazon Q Developer** — codegen/IaC/pipeline scaffolding in the *dev loop*; not a self-managing runtime.
- **Kiro** — "spec is the unit of work" (closest to provision-by-purpose) but build-time **authoring** with human
  checkpoints; acceptance criteria are dev-time test gates, not runtime success criteria.
- **AWS DevOps Agent** (GA 2026, on Bedrock AgentCore) — reactive SRE teammate; its mitigation plans already say
  "success criteria and rollback," then hands specs to Kiro and **waits for human approval**. In Teleon's model
  DevOps Agent is exactly the *supervisor/investigator* role the architecture shrinks the DevOps agent into.
- **The empty column** (continuous eval against success criteria · eval-gated shadow→canary→promote · autonomous
  runtime re-binding · acting without a human-approved step *inside the box*) is Teleon. The "managed +
  ServiceNow" advantage erodes fast → win on the ABSTRACTION (the implementation portfolio + the compiler), not
  integrations.

## Object model (a small family, not one YAML)
`CapabilityTask` (stable contract — built: `PurposeTaskSpec`, CTS-0 conformant) · `CapabilityImplementation`
(candidate) · `CapabilityRuntimeBinding` (task/impl→runtime class) · `CapabilityEvalSuite` (golden/regression/
**adversarial**/shadow/human-rubric) · `CapabilityRun` (input/output hash · impl · runtime · cost · latency ·
policy status · trace · artifacts) · `CapabilityPromotion` (candidate vs incumbent · evidence · approvals ·
canary · rollback) · `CapabilityBoundaryChange` (human-approved end-change) · `TaskOrientation` (STRUCTURED,
auditable operational memory — failure modes · successful/rejected strategies · runtime/cost history — NOT chat).

## Three planes · lifecycle · adaptation ladder
- **Planes:** Intent (stable) · Execution (replaceable: function/container/job/KEDA/Knative/Temporal/browser/
  GPU/edge) · **Evidence (the learning layer that GOVERNS adaptation — the differentiator most platforms lack).**
- **Lifecycle:** Draft→Simulated→Validated→Shadow→Canary→Active→Degraded→Diagnosing→CandidateGenerated→
  Evaluating→(Promoting|Rejected)→(Active|RolledBack); regression → automatic rollback.
- **Adaptation ladder (risk-tiered gates):** L0 runtime tuning (auto-promote on metrics) · L1 runtime rebind
  (cost/latency/reliability evals) · L2 config repair (regression+shadow) · L3 implementation candidate (full
  eval+provenance+canary+rollback) · L4 capability decomposition (human approval) · L5 boundary expansion
  (ALWAYS human-approved). Never treat "raise memory limit" and "add Salesforce write access" as the same change.

## RISKS to design around (the research's critique pass — build these in, don't omit)
1. **Eval saturation / Goodhart** — auto-generated candidates can game a FROZEN eval suite (pass without
   generalizing). Mitigate: rotate hard examples, **holdout + adversarial sets first-class**, pull fresh cases
   from production, **calibrate LLM-as-judge against human labels (~75% agreement floor before trusting a gate).**
2. **The evidence plane isn't free** — continuous shadow + canary + judge machinery COSTS money; it must net
   *against* the "agents at the edges" savings, or the economic argument leaks. Meter + show it (the dashboard's
   cost-arbitrage card must include the cost of the gates).
3. **LLM-judge trust** — gating on an uncalibrated judge gates on noise; keep a human-labeled validation set.
4. **Interfering control loops** — a graph of self-adapting capabilities can oscillate/conflict; borrow the
   MAPE-K formal-methods results; the capability graph must detect cycles + conflicts.
5. **Differentiation erosion** — "task as the unit / spec-driven / three planes" are already marketed; lead with
   the portfolio + compiler.

## Build order (mapped to what's SHIPPED — build the next unbuilt rung)
SHIPPED (flywheel 318): `PurposeTaskSpec` (CTS-0) + runtime-class vocabulary + PurposeTask PoC (provision-by-
capability + drift→side-by-side→promote-if-wins, baseline kept) + Parallel-Path Engine (eval-gated promotion +
rollback) + execution-backend selector (cloud-agnostic) + numeric provider/preference graph + dashboard
redaction core (staff/customer projections, deny-by-default).
NEXT, in order, each a focused proven increment (schema/code/proof/docs together; flywheel stays green):
1. **Adaptation ladder as config + proof** — `architecture/capability_adaptation_ladder.json` (L0–L5 + auto-vs-
   human gate) + a proof that an L5 change can't take an L0 promotion path.
2. **CTS-1** — bind runtime classes → backends via the execution selector (proof: class→backend by policy;
   missing-cloud→local fallback).
3. **Eval harness depth** — golden/regression/adversarial suites + **judge calibration vs human labels** +
   capability-vs-regression split + holdout rotation (directly mitigates eval saturation).
4. **CapabilityRun / CapabilityPromotion / Evidence ledger** — contracts + the run record + the evidence ledger
   (incidents-become-tests); provenance (SLSA/in-toto) on candidates.
5. **The dual-audience dashboard** — remaining projections + `/api/purpose-tasks/*` + staff/customer UI (the
   redaction core is built) — `prompts/baltor-purpose-task-dashboard-and-standard.md`.
6. **Template Factory** (Workflow opt-in) → generated implementations + function↔K8s shape-switching.
7. **The capability compiler** (the wedge; research-grade) — harden a discovered agentic path into deterministic
   code, eval-gated, provenance-tracked. Build LAST; it's the novel + hard part.
8. **Policy-as-code** — wire OPA/Kyverno-style gates behind the promotion gate (forbidden-changes / approval-required).
9. **CTS spec package + conformance tests + registry** (xRegistry model) — for the open-standard/Line-B play.

## Acceptance (the runtime is real when)
CapabilityTask contracts + registry · local tasks run · runtime selection (CTS-1) · candidate side-by-side ·
eval scorecard (with calibrated judge + holdouts) · promotion gate blocks unsafe (and a faster-but-wrong or
contract-weakening candidate is rejected) · adaptation ladder enforced (L5 needs human) · boundary expansion
human-gated · TaskOrientation · staff + customer dashboards (no staff-only leak — proven) · evidence-plane cost
metered · interfering-loop detection on the graph · redteam fails safely · offline demo + flywheel GREEN.

*Warrant: clear owner intent (name + detail + a single agent-ready build prompt for the intent-native, eval-
gated, self-adaptive compute runtime; develop it as an independent product under the HoldCo portfolio). Name
**"Teleon"** is OWNER-DECIDED 2026-06-06 and **`teleon.dev` is owned** (supersedes my earlier "Purpose Runtime"/
"Anneal" proposals); `capabilitytasks.org/.io` still need clearance, and `teleon.ai` is an adjacent-space
caution (see the naming doc). Claims the MAPE-K/progressive-delivery/EDD/control-plane lineage; centers the
implementation-portfolio + compiler wedge; builds the risks (eval saturation · evidence-plane cost · judge
calibration · interfering loops · policy-as-code) in as first-class; composes the shipped substrate (no
rebuild), now extracting into `src/teleon/`. Standard stays neutral (CTS, stewarded by OpenHubForAI); Teleon =
reference impl. Self-adapt means, never ends.*
