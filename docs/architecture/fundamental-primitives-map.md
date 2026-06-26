# Fundamental primitives — code/file map (generated)

> GENERATED from `architecture/fundamental_primitives_taxonomy.json` by `scripts/check_fundamental_primitives_taxonomy.py` — do not hand-edit. Updated 2026-06-20.

**Principle.** One canonical map of the fundamental primitives, organized by layer, each pointing to the REAL artifact that implements it. Assurance is first-class (the PMF wedge), not an afterthought. Non-destructive: this INDEXES the code; it does not move it.

**PMF alignment.** DATA + STANDARD + RUNTIME are the substrate we share with every platform; ASSURANCE (verification/freshness/source-authority/receipts/governance) is where we differentiate — 'they standardize where context lives; Baltor governs whether it's true'.

## Layer: `data` (5 primitives)

### `data.unit` — The typed atomic unit of data that flows through the system, with governance attached.
- **implemented by:** `src/teleon/io/governed_record.py`, `src/teleon/resources/resource_ref.py`, `schemas/io`, `schemas/shared`
- **standards:** JSON-Schema, JSON-LD @context
- **PMF role:** Every unit carries serves_truth + provenance — assurance rides on the unit, not bolted on.

### `data.medium` — The FORMAT/medium a unit travels in (native shape, envelope, open knowledge/entity format).
- **implemented by:** `src/baltor/native/native_format_preserver.py`, `src/baltor/native/okf_adapter.py`, `src/baltor/native/ftm_adapter.py`, `schemas/native`, `schemas/envelopes`
- **standards:** OKF, FollowTheMoney, native JSON/CSV/Markdown
- **PMF role:** Same-format-in/out + open-format interop = the on-ramp; we govern the contents above the medium.

### `data.storage` — Where units rest: state log, memory, vector store, object/staging store.
- **implemented by:** `schemas/memory`, `schemas/runtime`, `db`, `data/capability-candidates`
- **standards:** pgvector, SQLite-WAL
- **PMF role:** Candidate≠promoted is enforced at the storage/promotion boundary.

### `data.transfer` — How units MOVE: event bus, work I/O, governed egress.
- **implemented by:** `src/teleon/io/event_io.py`, `src/teleon/io/work_io.py`, `src/teleon/egress`, `architecture/egress_route_policy_taxonomy.json`, `schemas/egress`
- **standards:** CDC events, CloudEvents-shaped
- **PMF role:** Egress is policy-bounded; transfer carries receipts, not raw trust.

### `data.computation` — How units are TRANSFORMED: execution providers, workers, inference lanes.
- **implemented by:** `src/teleon/runtime/execution_provider.py`, `src/teleon/workers`, `src/teleon/inference`, `src/teleon/io/inference_io.py`
- **standards:** OpenAI-compatible inference
- **PMF role:** LLM output is never truth — computation proposes, the assurance rail disposes.

## Layer: `standard` (3 primitives)

### `standard.interop` — Open standards we adopt at the edges (single source of what we ingest/emit).
- **implemented by:** `architecture/standards_interop_manifest.json`, `src/baltor/observability/projections/standards.py`
- **standards:** OKF, FollowTheMoney, PROV-JSON, OpenLineage, Web-Annotation, JSON-Patch, MCP
- **PMF role:** Format isn't the moat; we consume the open formats and add assurance.

### `standard.context` — Context-grounding standards: the governed context object + its grammar.
- **implemented by:** `schemas/context`, `schemas/context-object.schema.json`, `schemas/contextops`, `taxonomy/SPEC.md`
- **standards:** OKF, JSON-LD, DCAT/SKOS
- **PMF role:** They standardize where context lives; we govern whether it's true.

### `standard.skill` — Skill/capability standards: CapabilityTask + digested skills + the seed framework.
- **implemented by:** `src/teleon/purpose_tasks/purpose_task.py`, `src/teleon/digestion`, `src/teleon/seeds`, `schemas/purpose_tasks`
- **standards:** SKILL.md, CapabilityTask spec (CTS)
- **PMF role:** SKILL.md won the format war → adopt it as candidate import/export; the moat is governed lift.

## Layer: `runtime` (4 primitives)

### `runtime.execution` — Compute backend selection by policy/telemetry (local/docker/k8s/cloud-fn behind one port).
- **implemented by:** `src/teleon/runtime/execution_backend_selector.py`, `src/teleon/runtime/execution_providers`, `architecture/execution_backend_policy_matrix.json`
- **standards:** ExecutionProviderPort
- **PMF role:** Backends interchangeable behind a port; the FleetLedger stays truth.

### `runtime.k8s` — Kubernetes primitives (Job/Deployment-worker) with a built local equivalent (defer gate).
- **implemented by:** `src/teleon/workers/execution_providers/local_job_emulator.py`, `architecture/execution_backend_policy_matrix.json`, `scripts/check_real_execution_candidates_have_emulators.py`
- **standards:** K8s Job/Deployment
- **PMF role:** Cloud may be candidate; the local equivalent can never be missing.

### `runtime.cloud_function` — FaaS primitives (Cloud Run / Lambda / Azure Function) each with a local emulator.
- **implemented by:** `src/teleon/runtime/execution_providers/gcp_cloud_run_function_candidate.py`, `local_emulators/model_emulator.py`, `local_emulators/source_of_truth_emulator.py`, `scripts/check_local_function_emulator.py`
- **standards:** Cloud Run, AWS Lambda, Azure Function
- **PMF role:** Every live seam has a built local emulator → local_go_live_ready=True while cloud stays honest.

### `runtime.environment` — The execution-environment profile + provisioning (the medium compute runs IN).
- **implemented by:** `src/teleon/environments`, `architecture/execution_environment_profiles.json`, `schemas/environments`, `schemas/runtime`
- **standards:** ExecutionEnvironmentProfile
- **PMF role:** Environment is a typed, policy-bounded profile, not ad-hoc.

## Layer: `capability` (1 primitives)

### `capability.seven_primitives` — The seven-primitive grammar: Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output.
- **implemented by:** `taxonomy/SPEC.md`, `taxonomy`
- **standards:** seven-primitive model
- **PMF role:** The shared vocabulary every component decomposes into — version lives in metadata, never names.

## Layer: `assurance` (5 primitives)

### `assurance.verification` — Measured lift + verification: does the component do what the model can't, provably?
- **implemented by:** `src/teleon/lift`, `scripts/eval/reason_codes.py`, `scripts/eval/durable_gap_harness.py`
- **standards:** RuleArena, measured-lift
- **PMF role:** The internal selection bar: admit on lift AND structural durability.

### `assurance.freshness` — Freshness/CDC currency: stale facts are held out, never served, until re-synced.
- **implemented by:** `src/teleon/evolution/freshness_runtime.py`, `src/teleon/self_healing`, `local_emulators/source_of_truth_emulator.py`
- **standards:** CDC 'changed' events
- **PMF role:** The wedge provers concede + gateways disclaim — answer currency.

### `assurance.source_authority` — Earned source-authority + multi-source corroboration (not a fixture).
- **implemented by:** `architecture/source_authority_registry.json`, `scripts/artifact_graph/authority_corroboration.py`
- **standards:** provenance, independent corroboration
- **PMF role:** 'Independent authorities AGREE' — earned from provenance, the #1 differentiator.

### `assurance.receipt` — Portable receipts: every governed action emits a verifiable, backend-portable record.
- **implemented by:** `schemas/observability`, `src/baltor/observability/projections/standards.py`, `scripts/check_live_ofac_receipt.py`
- **standards:** PROV-JSON, OpenLineage, ModelInvocationReceipt
- **PMF role:** Portable cross-vendor receipts — what data-gravity platforms don't emit.

### `assurance.governance` — Policy + promotion + org guardrails bounding what the AI may do/heal/promote.
- **implemented by:** `src/teleon/governance/org_policy.py`, `architecture/org_guardrail_policies.json`, `architecture/portfolio_dependency_law.json`
- **standards:** org guardrail policy, promotion boundary
- **PMF role:** The AI fixes only within the org's confines; candidate never auto-promotes.

## Owner-requested family coverage

- **data storage** → `data.storage`
- **data transfer** → `data.transfer`
- **data computation** → `data.computation`
- **units** → `data.unit`
- **mediums** → `data.medium`
- **standards** → `standard.interop`
- **context standards** → `standard.context`
- **skill standards** → `standard.skill`
- **K8 primitives** → `runtime.k8s`
- **cloud function primitives** → `runtime.cloud_function`

