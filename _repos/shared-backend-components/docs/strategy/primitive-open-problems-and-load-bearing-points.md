# Primitives: load-bearing points, capability gaps, and the hard parts

> **SUPERSEDED 2026-07-10 by `primitive-open-problems-v2-2026-07-10.md`** — after the external review + a build
> session, the load-bearing points MOVED (names → contracts) and several claims here were corrected. This v1
> is kept for lineage; read v2 for the current state. (v1's §3.2 PyPI claims are already corrected in-place.)

> Owner ask (2026-07-10): *"a new MD file of load-bearing points, areas of lack of capability, difficulty when
> thinking about packaged primitives, PyPI primitives, advanced multi-file multi-line primitives, etc."*

This is the honest register, written to the repo's honest-ledger law: what the whole design *rests on*, where
it is genuinely *weak or unproven*, and the specific *hard parts* of the packaged / PyPI / multi-file
directions. It is not a roadmap of promises — it is a map of load-bearing walls and known cracks. Every claim
is grounded in something measured this session or in the reconciled savings ledger
(`docs/REAL_SAVINGS_NUMBERS.md`).

---

## Part 1 — Load-bearing points (if one of these is wrong, a lot falls)

1. **Typed edges are the composition substrate.** Every representation — chains, groups, networks,
   integrators — resolves by matching `output_edge` to the next `input_edge`. Composition is *name matching on
   a graph*, and it only works because names are globally unique and meaning-bearing. **Load-bearing
   consequence:** if the edge vocabulary fragments, composition silently fails. Measured: `codegraph.py`
   already drops ~6k ambiguous call edges; independently-minted primitive edges chain **exactly 0 times**
   across mints (see §2.1). Edges are the foundation *and* the fault line.

2. **The candidate/truth boundary.** Nothing serves as truth by generation, assertion, or a green test —
   only after source review + an executed passing proof + the gates. Every row this session is
   `serves_truth=false`. **Load-bearing consequence:** the product's trust story *is* this boundary; any code
   path that flips the bit without proof breaks the whole value proposition, not just one row.

3. **Governance/provenance is the moat — not the capability gap.** The durable advantage is signed sources,
   lineage, CDC/revocation, and receipts, because model capability is a rising tide that erases raw
   capability advantages. **Load-bearing consequence:** work that improves grounding beats work that improves
   raw generation.

4. **Deterministic composition is the only robust 0-token win.** Reuse-via-prompt is prompt- and
   model-dependent (§2.2); deterministic composition (mount the verified module verbatim, emit thin wiring)
   passes hidden oracles model-independently. **Load-bearing consequence:** the network/grid layer and the
   integrator are built around this because it is the one lane that does not degrade with the next model.

5. **Store handles + digests, never bodies.** A primitive row carries a reference (handle, content digest,
   counts, components), not source bytes. **Load-bearing consequence:** this is precisely what lets a
   primitive be a 100K-line application (§scale) without the corpus exploding — and it is why "millions of
   primitives in GitHub" is the wrong shape (`docs/architecture/primitive-storage-and-delivery-model.md`).

6. **Reuse is a ladder, not a mechanism.** Reference → source → import → vendor → deterministic-compose →
   deploy, trading coupling for autonomy. **Load-bearing consequence:** there is no single "how you use a
   primitive" — the granularity of the primitive (§scale) picks the viable rungs, and a design that assumes
   one rung breaks for the others.

---

## Part 2 — Areas of genuine capability gaps (the honest weak spots)

### 2.1 Cross-mint edge chaining is ≈ 0 — alignment is a hand-curated lever
The central limiter of the whole composition layer. Independently-minted primitives almost never share an
exact edge name, so a raw composite request usually *refuses* (measured across the 112K corpus: exact
cross-card joins = 0; measured this session on the corporate pack: the raw pack refuses both integration
demos). The fix — `CANONICAL_EDGE_ALIGNMENTS` — is **curated by hand and by judgment**: this session a
9-agent workflow proposed 14 alignments and independent verification **kept 4, rejected 10** as unsound
(input-contract→payload aliases that would fabricate chains). That rejection was *manual reasoning*, not an
automated check. **Gap:** there is no learned-and-verified aligner; scaling alignment past a pilot table
needs one, and an unsound auto-alignment silently fabricates capability. This is the #1 open problem.

### 2.2 Reuse-via-prompt does not reliably save tokens
The honest ledger: showing a model the *full verified source* with "use as-is" can pass (~0.6 @ ~108 output
tokens) but showing *signatures only* makes models re-implement and fail; single-shot OUTPUT savings on
common code are marginal. **Gap:** "retrieve the primitive into the prompt and it'll reuse it" is *not* a
dependable win — only deterministic-compose (§1.4) and package-import (0-token, code never in the prompt) are
robust. Much of the value narrative has to route through those two, not through prompt injection.

### 2.3 The oracle problem at scale — how do you *prove* a large primitive?
A 20-line function has a cheap executable oracle. A 100K-line, multi-service application does not — its
"contract" is an SLA over a running system, not a unit test. This session minted 2 bridge primitives and
proved a 5-step chain, but every step was small. **Gap:** there is no method yet for *promoting* a
service/application-tier primitive to `serves_truth=true` — held-out oracles, contract tests, and shadow runs
exist for small primitives; the equivalent for a whole app (integration environments, SLO conformance) is
unbuilt. Until then, large primitives are honest **candidates** you *reference and deploy*, never *verified
truth*.

### 2.4 The composition layer is proven on a pack, not the full corpus
Networks, groups, grid search, and the deployment/scale profiles all run and are tested — on the **57-card
corporate pack** (+ remixes). **Gap:** slot computation is currently a linear scan over a card list; running
it over the **112K-card** searchable corpus (let alone 1.17M) needs an inverted `output_edge → producers`
index and a bounded grid explorer. The math holds; the scale plumbing is untested. (The grid explorer already
strides past a 10k-path cap — the corpus-scale *slot index* is the missing piece.)

### 2.5 Resource/deployment numbers are DRAFT rubrics, not measured
The deployment profiler decides medium and sizes vCPU/memory from tables, and `execution_efficiency` in the
grid-search scorer zoo is a **declared seam, never run**. **Gap:** "most efficient path" and "this needs 8 GB"
are *planning bands*, not observations. A real harness-backed execution scorer (the Harbor/bakeoff lane)
would replace the proxy — until it does, efficiency claims are labeled estimates.

### 2.6 Cross-environment trust of imported/vendored primitives
The vendor and import rungs move code into someone else's runtime. **Gap:** SLSA-style provenance, signing,
and revocation are *modeled* (the delivery doc names them) but not enforced end-to-end — a vendored primitive
today carries its proof status as data, not as a verifiable signature the consumer's toolchain checks.

---

## Part 3 — The specific hard parts of packaged / PyPI / multi-file primitives

### 3.1 Packaged primitives
- **Governance has to travel with the package.** A `pip`-installed primitive is just code once installed —
  its `candidate/serves_truth` status, lineage, and revocation state live in the registry, not the wheel. The
  hard part: keeping the consumer's *installed* copy tied to the registry's *current* truth/revocation state
  (a stale import can outlive a revoked primitive).
- **Version discipline vs the "version in metadata, never in the name" law.** Python packaging wants
  `==1.2.3`; our naming law forbids version in ids/names (`schema_version` is metadata). Reconciling
  pip's version pinning with metadata-versioned identity is unsolved plumbing.
- **Dependency conflict at the union.** The deployment profiler already computes *union dependencies* across a
  network's steps — that union is exactly where a real environment breaks (two primitives wanting incompatible
  `lxml`/`numpy`). At scale, "install every primitive you might reuse" is not viable; you need per-route
  virtualenvs or a resolver, which nobody has built here.

### 3.2 PyPI primitives specifically
> **Corrected 2026-07-10** (external review; see `primitive-architecture-shipped-and-target-2026-07-10.md`
> Part C). Two claims below were STALE: PyPI now HAS index-hosted attestations (PEP 740), file yanking, project
> status markers (PEP 792), lock metadata (PEP 751), and wheel SBOMs (PEP 770) — it is not an ungoverned byte
> bucket; consume those signals. And a private/governed index can implement the same Simple API and stay
> pip/uv-compatible — it loses public *discovery*, not `pip install` ergonomics (governance vs installability
> is a gradient). The import lane, done as *digest-from-a-locked-closure after admission + current-auth checks*,
> can be STRONGER than pasted/vendored source, not weaker.

- **Public PyPI cannot enforce our invariants by itself.** It has no *Teleon-specific* candidate/truth bit and
  accepts only a limited attestation-predicate set, so proof/admission/revocation stay in the governed control
  plane. But it is namespace-squattable and its own docs note provenance establishes origin, not
  trustworthiness — so independent evidence + policy is required. The hard trade is governance depth, not a
  binary reach-vs-governance choice.
- **Supply-chain trust runs the wrong direction.** Our whole thesis is "don't trust generated code — verify
  it." Publishing to an index and having agents `pip install` it reintroduces exactly the supply-chain trust
  problem (typosquats, dependency confusion) that governance was supposed to remove. The import lane is the
  strongest token win *and* the weakest trust story simultaneously.
- **Chicken-and-egg with retrieval.** Import is 0-token only if the package is *already installed*. Retrieval
  (MCP) tells you *which* primitive to use; something still has to install it before the import lane pays off.
  Bridging "discovered via MCP" → "installed and importable" is unbuilt.

### 3.3 Advanced multi-file / multi-line primitives
- **Representation is solved; decomposition is not.** A large primitive is a source-tree *reference* (§scale,
  shipped) — good. But *finding the sub-primitive boundaries* inside someone else's 100K lines (which
  functions/modules are reusable primitives, what their edges are) is an unsolved extraction problem. We can
  *hold* a large primitive; we cannot yet *automatically decompose* an arbitrary one into governed atoms.
- **Composition granularity mismatch.** The grid-search cost model assumes atomic step-primitives scored in
  *tokens*. A step that is itself a service/application is scored in *deploy cost and latency*, not tokens —
  the scorer zoo has no unit that spans "read this 90-line function" and "stand up this 100K-line service."
  The two ends of the scale ladder do not share a cost currency.
- **Partial reuse of a large primitive.** Calling one function of a 100K-line app vs deploying the whole thing
  are different reuse acts, but the card has one external contract. Modeling "reuse a *part* of a large
  primitive" (a sub-tree reference that is itself addressable) is only half-built (internal components are
  listed, but not independently retrievable/deployable yet).
- **Proving it (again §2.3).** The larger the primitive, the more its correctness is an integration/SLO
  property and the less a unit oracle can certify it. Large primitives will sit at `serves_truth=false` longer
  than small ones — possibly indefinitely — and the product has to be honest that "verified" means different
  things at different scales.

---

## The one-paragraph version

The design rests on **typed edges + governance + deterministic composition + reference-not-body storage**, and
those are solid. The genuine gaps are all downstream of two facts: **independently-minted things don't chain
without curated alignment**, and **you can't cheaply prove big things**. Packaging and PyPI are real delivery
rungs but reintroduce supply-chain trust and version/governance-drift problems; multi-file primitives are
*representable* today but not yet *auto-decomposable*, *partially-reusable*, or *provable at scale*, and they
break the token-based cost model. None of this is fatal — it is the honest edge of what is built — and the
highest-leverage next moves are a **learned-and-verified edge aligner**, an **execution-backed scorer/oracle
that scales with primitive size**, and a **governed index with signing** for the import/vendor rungs.

*Written candid on purpose. Everything above is the state as of 2026-07-10; re-verify before relying on any
specific number.*
