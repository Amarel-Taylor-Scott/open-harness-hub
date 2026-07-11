# Primitives, v2: load-bearing points, capability gaps, and the hard parts (post-review, post-build)

> Owner (2026-07-10): "a new MD file of load-bearing points, areas of lack of capability, difficulty when
> thinking about packaged primitives, PyPI primitives, advanced multi-file multi-line primitives, etc."

This supersedes the first register (`primitive-open-problems-and-load-bearing-points.md`). It is written after
an external deep-research review reframed the architecture *and* after a session that shipped the first
increments of that reframing. Same honest-ledger law: what the design rests on, where it is genuinely weak, and
the specific hard parts — but now the load-bearing points have MOVED (from names to contracts), several old
claims are corrected, and some old gaps are half-closed. Every module named below is self-test-gated + in
`run_proofs`.

---

## Part 1 — Load-bearing points (v2 — these MOVED)

The single biggest change: **names are no longer load-bearing for authorization.** They retrieve candidates;
contracts and evidence authorize. The register's #1 old wall ("typed edges are the substrate because names are
globally unique") is now a *retrieval* mechanism, not a *safety* mechanism.

1. **Contracts, not names, authorize composition.** `compatibility_lattice` grades a join
   (IDENTICAL / FAMILY_COMPATIBLE / SAFE_STRUCTURAL / VERIFIED_ADAPTER / LOSSY_OR_PARTIAL / CLOSE_CANDIDATE /
   UNKNOWN / INCOMPATIBLE), and only the first four auto-authorize; name/embedding similarity caps at
   `CLOSE_CANDIDATE` (retrieval only). Backed by real structure: `edge_contract_and_adapters` decides
   directional **width subtyping** over `PortContract` fields (types + units + required), and the
   `compatibility_benchmark` proves the payoff — **name-only makes a false auto-authorize (same-name/different-unit),
   contract-aware makes zero.** *Load-bearing consequence:* if a code path lets a name authorize execution, the
   same-name/different-unit (or different-security, or different-effect) bug is back. Abstention on UNKNOWN is a
   *success*, not a failure.

2. **Truth is a computed, claim-scoped decision — not a stored bit.** `serves_truth=false` remains the default
   stamp, but admissibility should be *computed* over a claim-, digest-, environment-, workload-, policy-, and
   time-scoped evidence graph, and travel as a short-lived signed grant bound to the exact artifact digest
   (`primitive_attestation` is that digest-bound signed statement; the full evidence graph is the next build,
   §2.2). *Load-bearing consequence:* a passing test proves a *claim in a context*, not universal truth; a
   dependency or environment change invalidates only the reachable claims.

3. **A capability is an immutable zoo of implementations; optimization changes ranking, not history.**
   `capability_implementation_zoo` keeps an append-only Pareto set + diversity archive — incomparable variants
   (faster vs leaner, permissive-license vs higher-accuracy) both survive, revoked ≠ deleted, and ranking is a
   query-time view. *Load-bearing consequence:* no ingestion/optimization pass may destructively replace an
   alternative; the accumulated zoo (with negative evidence) is the durable asset.

4. **Deterministic composition + reference-not-body storage remain the robust spine.** Deterministic
   composition is still the one model-independent 0-token win (`robust_lane_router` measures ~54% of the pack
   workload routing to robust lanes); large primitives are governed source-tree references, never bodies
   (`primitive_scale_and_containment`). These held up under review.

5. **Governance is infrastructure; the defensible asset is the evidence network.** The review sharpened this:
   SLSA/in-toto/Sigstore/PyPI-attestations can be adopted by anyone; the hard-to-copy asset is the accumulated
   contract mappings, verified adapters, execution receipts, *negative* evidence, and outcome data.

---

## Part 2 — Capability gaps (v2 — what is STILL weak after this session)

### 2.1 The contract algebra is a seed, not a system
`edge_contract_and_adapters` does width subtyping + a restricted adapter DSL (rename/widen/unit_convert/
project/enum_map), and `compatibility_lattice` grades names. **Gap:** there is no `ContractIR` with importers
from WIT / CUE / JSON-Schema / Protobuf / OpenAPI, so most pack cards have no structured contract yet — the
lattice still falls back to names for them. The adapter DSL is deterministic but small; general adapter
*synthesis* is unbuilt. Closing this is the bulk of Phase 1.

### 2.2 Evidence is a leaf, not a graph
`primitive_attestation` binds one signed statement to one artifact digest and checks revocation + freshness.
**Gap:** there is no multidimensional evidence *DAG* (build / interface / property / integration / security /
performance / SLO, each digest-bound with parent links) and no computed `eligible(subject, claim, env, policy,
now)` decision — so admission is still effectively a per-artifact check, not a claim-scoped graph query. A
dependency change cannot yet invalidate *only* the reachable claims. This is Phase 2's centerpiece and the next
build.

### 2.3 Cross-mint chaining is still ≈0 without curated/promoted alignment
The aligner now has both halves (propose → gate → evidence → promote → served, `edge_alignment_gate` +
`propose_edge_alignments` + the emit-loop) and the gate reproduces the human 4/10 decision. **Gap:** the
*propose* half is still lexical (token) by default — the semantic entity family needs the matcher's embedding
tier turned on, and there is still no learned-and-verified aligner (deferred to Phase 6 *by design* — it feeds
the CLOSE_CANDIDATE lane only, never authorizes).

### 2.4 Proving large primitives: a level exists, the matrix does not
`primitive_verification_pipeline` now has an `integration` level earned by a passing `buildout_run_receipt`.
**Gap:** a large application has *distinct* functional / interface / state / security / performance / SLO
claims, and one passing integration run does not certify all of them. The per-dimension evidence matrix
(§2.2's graph) is required before a service/application-tier primitive can be honestly admitted for a specific
claim.

### 2.5 Measured execution is one scalar, not a receipt factory
`execution_scorer` measures real executed-instruction count (deterministic). **Gap:** there is no receipt
factory keyed by environment/workload/hardware with cold/warm/burst profiles, quantiles, and variance — so
"most efficient" is still a single deterministic proxy, not a portable multi-environment observation. Planning
should rank on a measured Pareto frontier; today it ranks on token proxies + this one instruction-count lane.

### 2.6 Corpus-scale composition: the index exists, the planner does not
`producer_edge_index` makes slot lookup a hash+intersect (proven equivalent to the linear scan, scales to 60k).
**Gap:** there is no compatibility/semantic/effect postings index over 1M–100M records and no *bounded action
planner* (constrained A*/beam with dominance pruning + cycle/effect control). The grid explorer strides past a
10k cap but the corpus-scale planner is unbuilt.

### 2.7 Auto-decomposition proposes, it does not qualify
`primitive_subtree_partitioner` partitions a call graph into candidate sub-primitives + cut-edge interfaces
(deterministic by-module/by-connectivity). **Gap:** the multi-view fusion (symbols + build + data-flow + tests
+ traces + history + licensing), the `SliceManifest`, and *independent build + differential qualification* of an
extracted slice are unbuilt — so a decomposed piece is a candidate boundary, not a proven standalone primitive.

---

## Part 3 — The hard parts, corrected + updated

### 3.1 Packaged primitives
- **Now shippable, deterministically.** `primitive_microservice_packager` emits a runnable FastAPI/Flask
  service with the verified body mounted verbatim (0-token) + a Dockerfile + resources from the deployment
  profiler. So "package a primitive as a service" is no longer a hard part for the single-primitive case.
- **Still hard:** governance must travel with the artifact (a stale installed copy outliving a revocation);
  the deterministic *materializer* — exact closure locks, build-once-test-those-bytes, TUF current-authorization,
  isolated execution, signed receipts — is unbuilt (Phase 3). Dependency conflict at the union is real: the
  deployment profiler computes union deps, but per-route isolated environments (venv / WASI / container) chosen
  by measured warm-cache cost are unbuilt.

### 3.2 PyPI primitives (claims CORRECTED)
The original register was wrong that PyPI is an ungoverned bucket. **PyPI now has:** index-hosted attestations
(PEP 740), Trusted Publishing, file **yanking**, project **status markers** (PEP 792), reproducible lock
metadata (PEP 751 `pylock.toml`), and wheel **SBOMs** (PEP 770). The design should *consume* these.
- **Still true:** PyPI accepts a limited attestation-predicate set, so Teleon-specific proof/admission/revocation
  stay in the governed control plane; and its own docs note provenance establishes *origin*, not
  *trustworthiness*, so independent evidence + policy is still required.
- **Corrected:** a private governed index can implement the same Simple API and stay `pip`/`uv`-compatible — it
  loses public *discovery*, not install ergonomics. And a *digest-from-a-locked-closure import after admission +
  current-auth checks* can be a **stronger** trust story than pasted/vendored source, not weaker.
- **Hard part that remains:** bundling fine primitives into governed *packs* with static entry-point manifests
  (never importing untrusted package code to discover what it provides) + the governed gateway/materializer.

### 3.3 Advanced multi-file / multi-line primitives
- **Representation solved; contracts + partial reuse advancing.** A large primitive is a governed source-tree
  reference (`primitive_scale_and_containment`), decomposable into sub-primitives with cut-edge interfaces
  (`primitive_subtree_partitioner`).
- **Still hard:** the token-vs-deploy *cost-currency mismatch* is unresolved (a 20-line function scored in
  tokens vs a 100K-line service scored in deploy cost/latency) — the review's answer is a vector-valued cost
  model + Pareto ranking, not one scalar (unbuilt). Partial reuse of *part* of a large primitive needs the
  sub-tree to be independently addressable + deployable (half-built: components are listed, not independently
  buildable). And proof-at-scale is the §2.4 evidence-matrix problem.

---

## Part 4 — The one-paragraph version (v2)

The architecture no longer rests on globally-meaningful edge names or a universal truth bit. It rests on
**directional contracts + first-class classified adapters** (names retrieve, contracts authorize — measured:
0 false auto-authorizes on the adversarial set), an **immutable capability/implementation zoo** (optimization
changes ranking, not history), **claim-scoped evidence bound to exact digests**, and **reference-not-body
hierarchical storage**. This session shipped the first honest increments of each. The genuine remaining gaps
are downstream and now precise: a full ContractIR + adapter synthesis (Phase 1), the evidence DAG + computed
admission (Phase 2), the governed materializer (Phase 3), independent slice qualification (Phase 4), the
corpus-scale planner (Phase 5), and only then a learned aligner (Phase 6, feeding candidates it may never
authorize). None are vague blockers; each is a measurable program with a named first module already built.

*Full external review + this session's ~17 shipped modules are in the session record (2026-07-10); re-verify
any number before relying on it.*
