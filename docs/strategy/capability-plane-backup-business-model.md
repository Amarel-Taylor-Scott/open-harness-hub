# Capability Plane — the second business line (backup to the context engine), on one shared substrate

**Date:** 2026-06-06. **Status:** strategy / positioning (owner direction). **Owner intent:** build out the
CapabilityTask/OCTS/PurposeTask architecture far enough that, **if Baltor's context-enhancement engine doesn't
win, the purpose-driven cloud architecture can stand alone as a backup business model.** Doctrine + spec are
captured: `docs/standards/{open-capability-task-specification,capability-task-architecture-doctrine}.md`;
reference runtime: `docs/architecture/purpose-task-self-adapting-execution.md` (PurposeTask, CTS-0 shipped).

## The two-line thesis (NOT a fork — "one substrate, multiple doors")
This extends the existing [[two-services-ohh-and-ceaas]] pattern to a THIRD door on the SAME backend:
- **Line A (primary): the governed Context Engine** — Baltor.ai (Verify · Corpus · Compress): verified, current,
  provable context for AI agents. The current bet.
- **Line B (backup/optionality): the Capability Plane** — *intent-native, eval-gated, self-adaptive compute*: the
  reference runtime (PurposeTask) of the open **OCTS** standard. "Declare a capability; the platform finds/builds
  the implementation, picks the runtime, measures success, repairs drift, proves promotions, asks humans only at
  boundaries." A genuinely new cloud layer between static serverless/K8s and unbounded agents.
- **The crux: the work is NOT wasted whichever line wins, because they share one substrate** (see below). Line B
  is *optionality*, not a pivot — a hedge that compounds the primary, not a competing team.

## Why the backup is a real standalone business (the category gap)
Hyperscalers have the PARTS (functions · jobs · workflows · runbooks · ops-copilots · spec→code) but **none
exposes a long-lived capability object that owns success-criteria + cross-backend selection + evidence-gated
self-evolution + fallback preservation** (see the OCTS competitive analysis). The category is **Capability-
Oriented Cloud Runtime / Intent-Native Compute / Eval-Gated Serverless.** Demand is real: every team running
agents/serverless hits the "my deployment no longer matches my purpose" problem; the alternative today is
unbounded agents (expensive/unpredictable) or slow manual CI/CD. The economic breakthrough (the **capability
compiler**: agent discovers → hardens common path into cheap deterministic code → router moves to cheaper
compute → agent only for diagnosis/repair/fallback) is a token-cost reducer that sells itself.

## The shared substrate (why building B strengthens A)
Both lines run on the SAME governed substrate already shipped/being built — so every increment serves both:
| Substrate (built/queued) | Serves Line A (Context Engine) | Serves Line B (Capability Plane) |
|---|---|---|
| Governance spine (no-truth-bypass · receipts · lineage · promotion boundary) | served context is provable | promotions are auditable |
| **Eval harness / measured-lift gate** (the real moat) | which context lifts | which implementation wins |
| **Parallel-Path Engine** (side-by-side + promotion + rollback) | A/B context packs | A/B implementations |
| **Execution-backend selector** (cloud-agnostic, numeric) | where context work runs | runtime arbitrage |
| Provider / skill graphs (numeric, non-fragile) | context providers | implementation/skill providers |
| Determinism Factory | LLM→deterministic context rules | agent→deterministic-code compiler |
| FleetLedger / durable workers | context jobs | CapabilityTask execution units |
**Conclusion:** the eval harness + parallel-path + governance + execution selector are the joint moat. Build
them for A; they ARE B. That's what makes the backup credible rather than a distraction.

## Commoditization play (how it becomes a category, not a feature)
1. **Open the standard, neutral** — OCTS (`capabilitytasks.io`), built on CNCF/LF standards (CloudEvents/OpenAPI/
   AsyncAPI/Serverless-Workflow/OTel/OCI/SLSA/xRegistry/Score/OAM). The standard is NOT named after Baltor.
2. **Be the best reference implementation** — PurposeTask / the Baltor Capability Plane. Adoption of the spec
   pulls workloads toward the best conformant runtime (the OTel/OCI playbook).
3. **Conformance + adapters** — CTS-0..6 tiers + adapters (K8s Job/KEDA/Knative/Cloud Run/Lambda/Temporal/
   browser). Commodity = portable tasks that run anywhere; Baltor wins on the **control plane + eval harness +
   registry + compiler**, not on lock-in.
4. **Registry network effects** — a registry of CapabilityTasks/skills/eval-packs/runtime-classes (xRegistry
   model) is the durable asset; the more tasks + evals, the better the compiler + arbitrage.

## Monetization (Line B, consumption-shaped — drafts, ⟦DECISION⟧)
- **Per CapabilityTask under management** (the governed object) · **per run** (metered execution) · **per
  promotion / eval-gated change** (the value event) · **runtime-class-hours** (arbitrage margin) · **eval-harness
  / conformance** (enterprise) · **private control plane / registry** (enterprise/on-prem). The **eval harness +
  the arbitrage savings** are the willingness-to-pay anchors (cost reduction is measurable). Open spec/SDK +
  freezable task packages = the free funnel; the live governed control plane + compiler = the paid product.

## The honest risk (the #1 startup killer is focus dilution)
**Two business models pre-PMF is dangerous.** The discipline that makes this a hedge and not a death-by-two-fronts:
- **One team, one substrate, two doors.** Do NOT fork the team or build B-only infrastructure pre-proof. Only
  build what serves BOTH lines (the table above) until a proof point justifies the standalone GTM.
- **Sequence the standalone Capability-Plane GTM BEHIND the context-engine proof points** (a paid pilot, a
  consumed package — see the GTM/fundraising plan). B is *captured + ready + substrate-built*, not *sold-in-
  parallel*, until A either proves out (B becomes an expansion) or stalls (B becomes the pivot).
- **The reference impl, not the committee.** A standard with no conformant runtime + registry + adapters is a PDF;
  lead with the working PurposeTask runtime. Standardization is a multi-year effort — treat it as a long arc, not
  a quarter.
- **The compiler is the novel + hard part** (agent→deterministic-code with provenance); it's also the economic
  payoff. Invest there, but it's a research-grade bet — don't promise it before it's proven.

## ⟦DECISION⟧ for the owner
1. **Which line leads the narrative now** — context engine (current) with Capability Plane as captured
   optionality (recommended), or elevate the Capability Plane to co-equal? (Affects the YC story + the raise.)
2. **Spin the standard out as a neutral foundation** (capabilitytasks.io / CNCF Sandbox) vs keep it Baltor-led
   for now? (Neutrality wins adoption but slows control.)
3. **Pricing + raise implications** of a two-line story (does B change the TAM slide / use-of-funds?).
None of these should be decided unilaterally — flagged per the change-verification contract.

## Build-out path (continues via the loop, focused increments — no premature B-only fork)
Shipped: PurposeTask PoC + `PurposeTaskSpec.v1` (CTS-0) + runtime-class vocabulary + parallel-path promotion +
execution selector. Next (each serves BOTH lines): adaptation-ladder config + proof · OCTS CTS-1 (runtime-class
→ backend binding) · the eval harness depth · the Template Factory (Workflow opt-in) → the capability compiler ·
the CapabilityRun/Promotion/Evidence ledger · the registry. Capstone: the full PurposeTask runtime
(`prompts/baltor-purpose-driven-cloud-task-runtime.md`).

*Warrant: clear owner intent (build the purpose-driven cloud architecture out as a commoditizable backup
business model). Framed as optionality on a SHARED substrate (not a fork), sequenced behind the primary's proof
points, honest about focus-dilution risk. Brand-consistent (Context is Everything parent; Baltor.ai = Line A;
Capability Plane = Line B, OCTS reference runtime). Decisions flagged ⟦DECISION⟧. Related:
[[two-services-ohh-and-ceaas]], [[cloud-task-self-adapting-execution]], [[context-layer-pmf]].*
