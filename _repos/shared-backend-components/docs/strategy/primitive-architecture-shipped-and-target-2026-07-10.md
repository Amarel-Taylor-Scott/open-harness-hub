# The primitive architecture: what shipped, and the target from external review

> Owner (2026-07-10): "use 100% of your power, just this once, and improve everything and create a new MD file,
> proceed with all planned" — plus an external deep-research review that reframes the architecture and corrects
> several claims in the open-problems register.

Two things happened this session: (1) every planned gap-improvement shipped as a tested module, and (2) an
external research review argued — correctly — that the deeper fix is not a learned edge aligner but a change of
ontology: **capabilities are not implementations; names are not contracts; tests are not truth; packages are
not the registry; large artifacts are not indivisible; optimization must never delete the implementation
zoo.** This doc reconciles the two: what is built, how it maps to the revised architecture, what claims were
corrected, and the phased program forward.

---

## Part A — What shipped this session (all self-test-gated + registered in proofs)

| Area | Module | One line |
|---|---|---|
| Composition | `primitive_groups_frameworks_and_remixers` | groups · frameworks · deterministic remixers · integrators over cards |
| Networks | `primitive_networks_and_grid_search` | task = edge-chain of slots; grid search, non-destructive Pareto rankings |
| Scale | `primitive_scale_and_containment` | atom→application ladder; large primitive = governed source-tree reference (never bytes) |
| Deployment | `primitive_deployment_profiler` | op-class → deps/substrate/resources; use-case → medium (K8s vs cloud-fn) + cost band |
| Gap 2.1 verify | `edge_alignment_gate` | deterministic soundness gate; reproduces the hand 4-accept/10-reject exactly |
| Gap 2.4 | `producer_edge_index` | corpus-scale inverted slot index, proven equivalent to the linear scan |
| Gap 2.1 propose | `propose_edge_alignments` | reuses `edge_type_matcher`; rediscovers the Officer family; embedding-tier gap noted |
| Gap 2.2 | `robust_lane_router` | the scoreboard: ~54% of pack needs route to robust (0-token) lanes |
| Gap 2.6 | `primitive_attestation` | in-toto/SLSA signed, **content-bound** attestation; recompute-digest verify catches tampering |
| Gap 2.3 | `primitive_verification_pipeline` (+`integration` level) | a large primitive earns a level via a passing executed run, not a unit test |
| Gap 2.5 | `execution_scorer` | real measured execution by **instruction count** (deterministic, not wall-clock) |
| Gap 2.1 emit | alignment table = `curated_seed ∪ promoted rows` | promote_alignment gates then appends; proposing ≠ promoting |
| Gap 3.3 | `primitive_subtree_partitioner` | auto-decompose a large primitive's call graph into sub-primitives + cut-edge interfaces |
| Deploy rung | `primitive_microservice_packager` | deterministically package a primitive as a runnable FastAPI/Flask service, body mounted verbatim |
| **Contract algebra** | `compatibility_lattice` | **graded, directional** edge compatibility — names retrieve, only structure/adapter/explicit authorize |

Plus docs: the storage-and-delivery model, the composition-representation explainer, the open-problems
register, and the gap-improvements plan. Every row `serves_truth=false`.

---

## Part B — The external review's reframing (adopted as the target architecture)

The review's load-bearing corrections, in priority order. These become the north star; the shipped modules are
early, honest increments toward them.

1. **Contracts, not names.** Replace edge-name equality with a directional contract-compatibility engine:
   multi-port `ActionSpec`s carrying schemas, semantics, units, errors, effects, state, security capabilities,
   and protocol. Names and embeddings *retrieve*; contracts + evidence + policy *authorize*. → **Shipped
   increment:** `compatibility_lattice` makes compatibility graded + directional, and enforces the invariant
   that names/embeddings cap at `CLOSE_CANDIDATE` (retrieval only). The full `ContractIR` (WIT/CUE/JSON-Schema
   importers) is the next build.

2. **Claim-scoped evidence, not a global `serves_truth`.** Truth is a *computed admission decision* over a
   claim-, digest-, environment-, workload-, policy-, and time-scoped evidence graph; when it must travel,
   emit a short-lived signed `AdmissionGrant` bound to the exact artifact digest (the in-toto pattern). →
   **Shipped increment:** `primitive_attestation` is exactly that digest-bound signed statement whose verify
   recomputes the content hash and checks revocation + freshness. The multidimensional evidence *graph* (build
   / interface / property / integration / security / performance / SLO, each digest-bound) is the next build.

3. **Capabilities ≠ implementations; keep an immutable zoo.** A logical capability retains a non-destructive
   Pareto set + diversity archive of implementations, versions, packages, services, source slices, and runtime
   forms. Ranking never deletes alternatives. → **Aligned:** the network grid search is already non-destructive
   (every path scored + kept, losers preserved). The formal `CapabilityFamily` / `ImplementationVariant` split
   (§B object model) is the next schema change.

4. **Hierarchical content-addressed artifacts.** Represent a repo as application → service → target → module →
   symbol → slice over shared CAS; static analysis / build graphs / symbols / tests / traces / licensing
   propose independently-buildable slices. → **Shipped increments:** `primitive_scale_and_containment` (the
   source-tree reference, never bytes) + `primitive_subtree_partitioner` (call-graph → sub-primitives + cut
   edges). The `SliceManifest` + independent-build qualification is the next build.

5. **PyPI is one carrier, not the registry** — and several of my claims were STALE (see Part C). Bundle fine
   primitives into governed *packs* with entry-point manifests; use WASI/OCI/service/SQL/source carriers for
   other shapes; front it all with a governed Simple-API gateway + a deterministic materializer (closure locks,
   build-once-test-those-bytes, TUF current-authorization, isolated execution, signed receipts).

6. **Reuse is a matrix, not a ladder.** Import / vendor / compose / execute / deploy / RPC / WASM / source
   integration trade coupling, autonomy, isolation, latency, install cost, security, licensing, portability,
   observability differently — deployment is not always "higher" than import. → **Correction:** my
   storage-and-delivery doc's "ladder" is superseded by this matrix (Part C).

7. **Multi-objective Pareto scoring over measured receipts.** Hard constraints (correctness/evidence/policy)
   first; then rank the remaining routes on a Pareto frontier from measured cold/warm execution receipts — no
   universal cost currency across a 20-line function and a deployed service. → **Shipped increments:** the grid
   search already computes a Pareto front; `execution_scorer` produces the first real measurement (instruction
   count). The full receipt factory (cold/warm/burst profiles, per-environment keys) is the next build.

8. **Decomposition is a governed multi-view candidate pipeline** (syntax + symbols + build + data-flow + tests
   + traces + history + licensing), not one algorithm. → **Shipped increment:** `primitive_subtree_partitioner`
   is the deterministic by-module/by-connectivity default; the multi-view fusion + independent qualification is
   the next build.

---

## Part C — Corrected claims (honest-ledger law)

The review corrected real errors. The following supersede the corresponding statements in
`primitive-open-problems-and-load-bearing-points.md` and `primitive-storage-and-delivery-model.md`:

- **PyPI is NOT an ungoverned byte bucket.** It now has index-hosted attestations (PEP 740), Trusted
  Publishing, file **yanking**, project **status markers** (PEP 792, incl. quarantine/deprecation), reproducible
  lock metadata (`pylock.toml`, PEP 751), and wheel **SBOM** locations (PEP 770). The design should *consume*
  these signals, not ignore them. PyPI's own docs correctly note that provenance establishes *origin*, not
  *trustworthiness* — so independent evidence + policy is still required, but the claim "no revocation, no
  provenance, no lifecycle" was stale.

- **A private index does not necessarily lose `pip install` reach.** A governed gateway can implement the same
  Simple API and stay pip/uv-compatible; it loses unauthenticated *public discovery*, not package-manager
  ergonomics. Governance vs installability is a gradient, not a binary.

- **The import lane is not inherently the weakest trust story.** `pip install <name>` is weak, but importing an
  *exact digest from a locked closure after provenance + admission + current-authorization checks* can be
  **stronger** than pasted or vendored source. Trust depends on artifact resolution + policy, not on the
  `import` statement.

- **"Reuse is a ladder" → reuse is a MATRIX.** Delivery modes trade coupling/isolation/latency/security/cost
  differently; deployment is not strictly "higher" than import. The ladder framing in the storage-and-delivery
  doc is superseded by the delivery matrix.

- **"Store handles, never bodies" needs a retrievability guarantee.** A digest verifies bytes but does not
  guarantee they remain *retrievable*, and one opaque tree digest blocks partial reuse — hence the hierarchical
  content-addressed capsules with subtree addressing (Part B §4).

- **The corpus denominators must be separated.** 112K / 1.17M / ~1.7M refer to *different* things (searchable
  cards vs all records vs vectorized components). The ledger must report distinct counts for source artifacts,
  parsed symbols, candidate implementations, capability families, contract ports, embedding rows, verified
  adapters, evidence-bearing implementations, and active/deprecated/quarantined/revoked releases — or coverage
  percentages are unreadable.

---

## Part D — The object model to migrate toward (review §3)

`PrimitiveCard` should become a *materialized view* over a normalized model: `CapabilityFamily` (the logical
outcome) · `ContractProfile` (immutable, revisioned) · `ImplementationVariant` (one way to satisfy it) ·
`ArtifactRelease` / `ArtifactManifest` (content-digested bytes/trees) · `AdapterCard` (directional, proved
like any implementation) · `EvidenceAttestation` (digest-bound, claim-scoped) · `EnvironmentProfile` ·
`ExecutionReceipt` · `SelectionPolicy` · `PlanLock`. The identity stack: `capability_id · implementation_id ·
release_version · artifact_digest · contract_digest · environment_digest · policy_digest`. "Version in metadata,
never in the name" remains a *naming* convention for the logical capability — it does not forbid versioned
release locators or immutable digests (that was a schema-modeling confusion, now resolved).

---

## Part E — The phased program (review §15) and where we are

- **Phase 0 — correct the ledger + object boundaries.** Separate denominators; make rows immutable candidates;
  keep `PrimitiveCard` as a view. → *Started:* claims corrected (Part C); non-destructive rankings already hold.
- **Phase 1 — contract registry + compatibility v1.** `PortContract`/`ContractIR`/`AlignmentAssertion`/
  `AdapterCard`; exact + family + structural matching; the 4-accept/10-reject set as directional assertions;
  a restricted lossless adapter DSL. → *Started:* `compatibility_lattice` (grades + directionality) +
  `edge_alignment_gate` (the 4/10 reference). Next: `ContractIR` + the adapter DSL.
- **Phase 2 — evidence graph + policy admission.** Digest-bound attestations; computed admission replaces the
  truth bit; risk-tiered policy; dependency-triggered invalidation. → *Started:* `primitive_attestation`. Next:
  the evidence DAG + `eligible(...)` decision.
- **Phase 3 — governed acquisition + packaging.** Packs + entry-point manifests; digest-locked per-plan envs;
  verify attestations/SBOM/license/vuln before activation; WASI/OCI carriers; offline mirror. → *Started:*
  `primitive_microservice_packager` (the deploy carrier) + the deployment profiler. Next: the materializer +
  gateway.
- **Phase 4 — hierarchical decomposition + slice qualification.** → *Started:* `primitive_subtree_partitioner`.
  Next: multi-view fusion + `SliceManifest` + independent build/differential qualification.
- **Phase 5 — corpus-scale retrieval + planning.** Postings/bitmap indexes; bounded action planning; Pareto
  pruning. → *Started:* `producer_edge_index`. Next: the compatibility/planning indexes + bounded planner.
- **Phase 6 — learned alignment (LAST).** A high-recall candidate generator feeding the `CLOSE_CANDIDATE` lane;
  never authorizes execution. → *Deferred, by design* — the report's key sequencing point.

---

## Revised load-bearing principles

1. Capabilities are logical families; implementations are an immutable zoo.
2. Stable IDs establish identity; contracts + evidence establish admissible compatibility.
3. Names, text, embeddings, and models retrieve candidates but **never** authorize execution.
4. Adapters are first-class, directional, versioned, and proved like any implementation.
5. Evidence is claim-, digest-, environment-, workload-, policy-, and time-scoped; admission is computed.
6. Catalog metadata is reference-oriented; artifacts live in a retrievable hierarchical CAS.
7. Delivery is federated (source · packages · components · containers · services · SQL · workflows · deploys).
8. Planning applies hard constraints before contextual Pareto ranking; every run yields a receipt.
9. Originals, alternatives, and derived slices are immutable; optimization changes ranking, not history.
10. **Abstention is a successful safety outcome** when compatibility or evidence is unknown.

> The current architecture no longer rests on globally-meaningful edge names or a universal truth bit. It rests
> on stable capability/implementation identities, directional multi-dimensional contracts, first-class verified
> adapters, hierarchical content-addressed artifacts, and claim-scoped evidence evaluated by policy — with
> retrieval finding candidates, deterministic checks admitting a safe subset, bounded planning selecting a
> Pareto route, and receipts improving ranking. This session shipped the first honest increments of exactly
> that; the rest is a measurable engineering program, not a set of vague blockers.

*Full external review archived in the session record (2026-07-10); every shipped module is proven by self-test
+ run_proofs; re-verify any number before relying on it.*
