# Improving the primitive-system gaps: research + what shipped + the plan

> Owner ask (2026-07-10): *"Research all research agents, launch all of them, improve, etc."* — against the
> open-problems register (`primitive-open-problems-and-load-bearing-points.md`).

This is the companion to the honest gaps register: for each gap, the **prior-art technique** that addresses it,
the **repo asset to reuse** (reuse-first), a **concrete first step**, and its **status** — shipped this
session or planned. It was produced by a 7-agent research workflow (one grounded agent per gap) plus a
synthesis pass, and then *acted on*: five modules shipped, all self-test-gated and registered in proofs.

The synthesis's ordering principle governs everything: **build the scoreboard, then move the score.** Three of
the gaps are about *raising* how much value flows through robust, model-independent lanes; only the robust-lane
router lets you *measure* that fraction. The honest-ledger law forbids unquantified savings claims, so the
scoreboard is the instrument that makes the other fixes provable and rankable — build it first.

---

## Shipped this session (5 modules)

| Gap | Module | What it does | Result |
|---|---|---|---|
| 2.1 (verify) | `edge_alignment_gate.py` | Deterministic soundness gate: role (payload→payload only) / ambiguity / cycle + corpus enable-evidence. | Reproduces the hand-verified **4-accept/10-reject** decision exactly; admits are `candidate_for_review`, never auto-truth. `3ab7538a5` |
| 2.4 | `producer_edge_index.py` | One-pass inverted `producers[edge]`/`consumers[edge]`; a slot is a hash lookup + set intersect, not an O(N) scan. | **Proven equivalent** to the linear scan for every network; scales to 60k cards; `build_network(index=…)` bit-identical. `d24d92791` |
| 2.1 (propose) | `propose_edge_alignments.py` | Generates candidate alignments from dangling edges, **reusing `edge_type_matcher`** (6 tiers), gated + evidenced. | Re-derives the Officer family from the raw pack automatically; the semantic entity family awaits the matcher's embedding tier (honest). `675d9d8aa` |
| 2.2 (keystone) | `robust_lane_router.py` | Classifies each need into `deterministic_compose`/`package_import` (robust, 0-token) vs `partial_compose`/`generate_tail`; reports the robust fraction. | The honest scoreboard: **~54% robust** on the pack workload; a mutation gate proves it moves with real composability. `264e6223b` |

All five are pure composition/deterministic, `serves_truth=false`, and exposed on the agent API (`alignment.screen`,
`robust.coverage`, plus the earlier `deployment.*`/`scale.profile` — 27 actions).

The load-bearing win: **gap 2.1 (the #1 open problem) now has both halves** — propose (reusing the matcher) →
verify (the gate, reproducing the human decision) → evidence → a human promotes. Scaling alignment no longer
means scaling manual review of the clearly-unsound; only genuinely-semantic cases reach a person.

---

## The prioritized plan (from the synthesis)

### Move 1 — the robust-lane scoreboard · **SHIPPED** (`robust_lane_router.py`)
The keystone. "Route more to robust lanes" was unquantified; now it is ~54% on the pack workload, and every
other fix is scored against that number. Next: run it over `realistic_session_harness` working-set tasks (not
just the pack) for a real-workload figure, and add the `partial_compose` residual-tail measurement.

### Move 2 — the edge aligner · **SHIPPED** (`edge_alignment_gate.py` + `propose_edge_alignments.py`)
The #1 open problem. The synthesis confirmed the polarity/role check alone reproduces the 4/10 split (it does),
and that the propose half already exists as `edge_type_matcher.py` (it does — now reused). **Remaining:** the
emit loop — refactor `CANONICAL_EDGE_ALIGNMENTS`/`_edge_align_apply` to *load* `curated_seed ∪ promoted_candidate_rows`
instead of a hand-typed dict (no-magic-values), and turn on the matcher's **embedding tier** to catch the
semantically-related-but-lexically-dissimilar family the token tier misses.

### Move 3 — attestation for the import/vendor lanes · **planned** (`primitive_attestation.py`)
Depth-before-breadth: make the *strongest* token lane (package import) trustworthy enough to ship to a paying
consumer. `formalize_card` writes a plain `provenance` dict and the packaging pack *declares* "cosign-signed"
as prose — nothing recomputes the hash, checks revocation, or expires the copy. First step: `build_attestation`
(in-toto v1 Statement, `subject.digest.sha256 == artifact_hash`, SLSA-style predicate from the fields
`formalize_card` already emits) + `sign_attestation` (HMAC-local → ed25519 → cosign seam) + `verify_attestation`
(recompute digest from the shipped body → catch tampered/stale vendored copies; check signature, revoked-set,
and stapled `primitive_warranty` freshness). Mutation gate = four injected defects (flip a body byte, revoke,
advance the clock past expiry, corrupt the signature) each forcing `verified=False`. Reuses `primitive_warranty.py`
(the expiry engine already exists).

---

## Per-gap research (technique · reuse asset · first step · status)

**2.1 Cross-mint edge chaining ≈ 0** — *techniques:* COMA/COMA++ composite schema matching (the propose half),
LogMap/Alcomo **coherence repair** (propose→check-coherence→discard = our gate), **structural/record subtyping
& row polymorphism** (the "same-shape" check as decidable width-subtyping over contract fields), OAEI reference
alignments (the 4-kept/10-rejected set IS a scored reference), metamorphic testing (a sound alignment may only
ADD routes, never change an existing one). *Reuse:* `edge_type_matcher.py`, `build_canonical_edge_type_vocabulary.py`
(produced_by/consumed_by polarity), `check_primitive_composability.build_type_index`, `mint_unmet_edge_producers.py`
(the propose→govern pattern), `build_edge_type_retrofit.canonicalize_edge`. *Status:* **SHIPPED** (gate + propose);
emit-loop + embedding-tier remaining.

**2.2 Reuse-via-prompt not dependable** — *techniques:* the robust-lane cascade (deterministic-compose →
import → partial → generate), coverage measurement over mined sessions. *Reuse:* `hybrid_composer.plan`,
`saas_buildout_decomposer.certify_candidate`, `primitive_runtime.compose_route`, `realistic_session_harness`.
*Status:* **SHIPPED** (`robust_lane_router` scoreboard); partial-composition residual-tail is a longer bet
(needs live-model runs to prove the tail shrinks).

**2.3 Proving large primitives (oracle at scale)** — *techniques:* metamorphic + property-based testing,
consumer-driven **contract testing**, differential/**shadow testing**, an oracle-strength ladder. *Reuse:*
`primitive_verification_pipeline.py` (`LEVELS = candidate/structural/source/execution` — add `integration`),
the executed **buildout oracles** (`buildout_oracle_patterns.py`, `saas_buildout_decomposer`), the atlas
mutation catalogs. *First step:* extend `LEVELS` with an `integration` level that returns True iff a card
references a passing `buildout_run_receipt` — bridging the executed oracles to a formal verification level.
*Status:* **planned** (a clean extension of an existing module).

**2.4 Composition at corpus scale** — *techniques:* inverted index + set-intersection slot lookup, union-find
connectivity pruning before cartesian enumeration. *Reuse:* the persisted lexical index pattern
(`build_primitive_search_index`), pgvector. *Status:* **SHIPPED** (`producer_edge_index`, proven equivalent);
persisting it to disk + a bounded grid explorer are the follow-ons.

**2.5 Execution-backed scorer** — *techniques:* sandboxed runners, measured runtime/memory, a bakeoff harness.
*Reuse:* the harness-bakeoff lane, `saas_buildout_decomposer` execution. *First step:* replace the
`execution_efficiency` declared seam in the grid-search scorer zoo with a sandboxed measured run behind a
capability flag. *Status:* **planned** (the seam is already declared and named).

**2.6 Cross-environment trust** — *techniques:* **Sigstore/cosign**, **in-toto/SLSA** provenance, **TUF**,
content-hash binding, install-time verification tied to registry revocation. *Reuse:* `primitive_package_contract.formalize_card`
(the provenance dict + artifact_hash), `primitive_warranty.py` (expiry), `build_deployment_packaging_surface_pack`.
*Status:* **planned** — Move 3 above (the highest-value non-shipped item).

**3.3 Auto-decomposition of large primitives** — *techniques:* call-graph **community detection** (CNM/label
propagation), **clone detection** (MinHash-LSH), program slicing, interface/cut-edge extraction. *Reuse:*
`codegraph.py` (the AST is already parsed), `cluster_primitive_duplicates._minhash_signature/_lsh_blocking`,
`primitive_scale_and_containment.py` (the source-tree-reference `internal_components` field to populate).
*First step:* `primitive_subtree_partitioner.partition_symbol_graph(nodes, edges)` — partition the AST
call/import graph into candidate sub-primitives and derive each one's typed cut-edge interface. *Status:*
**planned**; the community-partitioner is the most speculative bet (modularity resolution limits, non-unique
optima) — mitigate with a directory-partition default + racing + the `saas_buildout_decomposer` execution gate.

---

## Quick deterministic wins vs long research bets

**Quick wins** (offline, stdlib, reuse existing engines, gold-set-provable): the aligner emit-loop; a
`sound_connectivity` metric on `edge_type_matcher.connectivity_report` (ship *after* the gate so the number
means something); attestation + verify (HMAC-local + content-hash binding is fully deterministic); the
clone-collapse pre-pass (reuse the existing MinHash-LSH) + directory-partition default.

**Long bets** (need live-model runs, ops, or have theoretical failure modes — sequence behind the wins,
candidate-only): partial-composition tail-shrink (live-model), the community-partitioner zoo (resolution limit
+ O(n²)), a content-addressed private index (real ops, sacrifices `pip install` reach), a Merkle/Rekor
transparency log (auditability, not the trust *fix*).

## Dependency ordering

`robust_lane_router` (SHIPPED — the scoreboard, no new deps) is the root: it scores and prioritizes the rest,
and reveals whether the import lane carries enough value to justify Move 3's attestation work. The aligner gate
(SHIPPED) unblocks the emit-loop and the embedding tier. `producer_edge_index` (SHIPPED) unblocks corpus-scale
everything. So the three shipped foundations already unblock the planned remainder; the next single thing to
build is **Move 3 (attestation)** — the highest-value planned item, self-contained and deterministic.

*Everything here is candidate work (`serves_truth=false`); the shipped modules are proven by self-test +
`run_proofs`, and the planned ones carry their mutation gate in the plan. Re-verify any number before relying
on it.*
