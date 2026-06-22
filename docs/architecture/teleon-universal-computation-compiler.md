# Teleon as a universal computation compiler — one loop, seven seams

A deep architecture for the reframe: **Teleon is not an agent framework, a workflow builder, or "NL → pipelines." It is a
universal compiler/runtime that transforms ambiguous capability requests into globally optimized, verified executable
graphs over an internet-scale registry of computational primitives.** This is the already-ratified *cognitive-work
compiler* thesis (`docs/strategy/teleon-cognitive-compiler-2026-06.md`), taken to its full conclusion.

The north star, stated sharply: **the future is not models getting smarter — it is systems getting better at deciding when
intelligence is unnecessary.** Teleon's job is to *remove unnecessary intelligence from computation* — to compile a request
down to the cheapest deterministic path that provably works, and call a model only for the irreducible residual. That is
exactly the **descent** (`src/teleon/evolution/descent.py`): make it work, then make it efficient.

**Scale is the goal, not a constraint — and not something to hedge.** The target is to be the routing/compilation layer
that *every* agent goes through to get computation done: **billions, then trillions, of components**, and the default
substrate for autonomous work. If agents route to us, a data flywheel takes over — more agents → more traffic → better
measured metadata → better routing → more agents — and that flywheel at internet scale is the **Google-of-computation**
position. Bigger than any single product. Every system below is engineered to *reach and operate at that scale*; nothing
here caps it. The "pruner" architecture and the interface/implementation split that follow are precisely *how* you make
billions-to-trillions of components searchable, composable, and safe — they are the scaling mechanism, not a ceiling.

---

## The architecture is SMALL — one loop, seven seams (grounded)
A system *count* is the failure mode, not the goal. The architecture is **one loop** —
`specify → retrieve → compose → verify → optimize → execute → measure → learn` — where **every stage is a pruner**, held
together by **seven abstraction seams** that keep components, providers, front-ends, and runtimes swappable. Get the seams
right and everything below is implementation detail. (The detailed "systems" later in this doc are the *implementation* of
these seams + the loop — read them as the seams in depth, never as a headline count.)

| Seam | What stays swappable | Built / where |
|---|---|---|
| **Front-end agnostic** | NL · declarative spec · visual DAG · agent API → one IR | compiler intent→DAG (`compile_capability_live`) |
| **Component agnostic** | python · docker · OpenAPI · MCP · CLI · SQL · browser · remote inference | **built** — `src/teleon/components/` (uniform `invoke`) |
| **Provider agnostic** | same logical model, many vendors/regions, chosen at runtime | **built** — `economics/{economic_graph,routing_engine}` |
| **Representation agnostic** | jpeg/png = image; html→markdown auto-coerced | **built** — `synthesis/type_system.py` (lattice + coercion) |
| **Objective agnostic** | one compiler, user weights → cheap-/accuracy-/privacy-mode | **built** — `PreferenceProfile` + `economics/cost_model` |
| **Runtime agnostic** | dev local; prod Temporal/Dagster — nothing above the IR changes | `dag/pipeline_dag` + `runtime/execution_providers` |
| **Trust agnostic** | curated/community/discovered/experimental under graded sandbox | trust tiers (curated today; sandbox = next) |

This is **the fusion of three mature research areas** — standing on them means the hard parts are *known* hard parts:
- **Type-directed component-based program synthesis** — SyPeT (typed library as a Petri net, compose by reachability),
  TYGAR (polymorphism), **APIphany** (PLDI 2022: *semantic* types specify intent + direct search, and **simulated
  execution** scores candidates without real calls — exactly our analytic simulator, already built).
- **LLM cascades / model routing** — **FrugalGPT** (router + answer-scorer + stop-judger; up to ~98% cost cut at equal
  quality) and *agreement-based cascading* (escalate on ensemble disagreement, training-free). This is the descent.
- **Provider routing / inference economics** — **OpenRouter** (~100T tokens/mo across 80+ providers), LiteLLM, Portkey.

### What the research changes (honest findings — adopt these)
1. **Synthesis scales poorly with library size** (a known result; it's why graph/Petri-net methods exist). MCTS/beam do
   **not** dissolve the blowup — **templates carry the common case** (retrieve-and-mutate), synthesis is the long-tail
   fallback, and we accept *"first valid candidate over the cost threshold,"* not global optimality. Retrieval recall is
   imperfect (Gorilla) → plan for misses (family fallbacks, graceful degradation).
2. **Reliability is a first-class objective from day one.** OpenRouter's lesson: the same model's price spans 3–10× across
   providers, the cheapest endpoint is often a *quantized/degraded* one, and naive cheapest-routing is **unstable** (the
   cheapest provider saturates first, degrades first, recovers slowest). Their fix: skip recently-failing providers and
   weight survivors by the **inverse square of price**. → Our cost model folds availability+success into effective cost;
   the next refinement is explicit reliability weighting + skip-failing in `routing_engine`.
3. **The moat is the flywheel, not the registry.** Quality is the one objective term you **cannot buy** — only earn by
   running things and measuring (the telemetry write-back). Anyone can crawl PyPI; nobody else has *your measured quality*.
4. **"Equivalence" is empirical, not proven.** General program equivalence is undecidable; two pipelines are equivalent
   *only to within your benchmark corpus* (the agreement signal). Treat equivalence classes as **learned, benchmark-
   relative artifacts**, never theorems.
5. **MCP is one adapter type + a real security surface** (~97M monthly SDK downloads, Linux Foundation — but 30+ CVEs in
   early 2026, a cross-tenant leak, tool-poisoning). It sits *above* function-calling (overhead on latency-critical
   paths). → Treat MCP as one adapter factory among several; the **trust/sandbox tier is load-bearing, not someday**.

### Build order — and what NOT to build yet
**Build (each unblocks the next):** (1) close the **metadata write-back loop** [**done** — `economics/observation_store`
+ `provider_intel.record_measured_run`]; (2) the **analytic simulator** [**done** — `economics/simulator`, APIphany-style];
(3) **template library + retrieve-and-mutate** [next — biggest lever]; (4) **beam composition + the type lattice/coercion**
[lattice **done**; beam next]; (5) **PassManager + cost model** [cost model **done**; passes next]; (6) **sandbox +
trust-tier execution**, then **adapter factories** (OpenAPI/Docker/MCP), then discovery + canonicalization.
**Do NOT build yet** (destinations, not Monday's work): self-expanding discovery at internet scale; "capability futures"
/ a 10-billion-component registry / billions-of-DAGs search; a *formal* IR + verifier (start with the typed-DAG data
structure + pass functions we already have). **Win one vertical first** — document/invoice extraction (PyMuPDF→regex→
schema-validate, LLM only as fallback) or LLM-routing for one high-volume workload — *provably 10× cheaper at equal
quality, with the telemetry to prove it.* Scale is the destination; a measurably-cheaper vertical is the proof you earned it.

---

## The central problem — and why every layer is a *pruner*
The hard part is not DAG generation. It is **searching an effectively infinite universe of computational possibilities.**
The resolution is the single most important architectural principle here:

> **We never enumerate the universe. Every layer is a pruner that shrinks the search before the next layer sees it.**

```
millions of components ──(retrieval: lexical+vector+graph+constraints)──▶ dozens
       dozens ──(templates: don't synthesize from scratch; mutate a known-good skeleton)──▶ a few skeletons
   a few skeletons ──(type system: reject every type-invalid wiring)──▶ valid candidates only
 valid candidates ──(simulation: analytic cost/quality from metadata, no execution)──▶ top-k
        top-k ──(benchmark: run only these on real data)──▶ 1 winner
       1 winner ──(optimization passes: LLVM-style rewrites)──▶ the cheapest bounded graph
```

This is **program synthesis**, and synthesis only works when the space is aggressively pruned by **types, priors
(templates + learning), and cheap scoring (simulation)** — so the expensive steps (benchmark, execute) run on a handful
of candidates, never the universe.

---

## Honest map — what already exists vs. the gap
| # | System | Status | The real artifact today |
|---|---|---|---|
| 1 | Universal Capability Representation | **partial** | `tool_planes.json`, `plane_io_contracts.json`, `capability_taxonomy.json`, `capability_ladders.json`, `evolution/capability_graph.py` (capability→runners) |
| 2 | Registry (millions/billions) | **partial** | `registry_layers.json`, `tool_registry.json`, `tool_registry_staging.jsonl`, `harvest_tools.py`, `storage_tier_policy.json`, promotion boundary |
| 3 | Universal Adapter | **built (v1)** | `src/teleon/components/` (`invoke`/`lower`/`conformance`) + agnostic ports + `runtime/execution_providers/` |
| 4 | Retrieval Engine | **partial** | `synthesis/component_search.py`, `retrieval/hybrid.py` (RRF), ladders (families), `evolution/capability_graph.py` |
| 5 | DAG Composition | **partial** | `compile_capability_live.py`, `synthesis/synthesis_tree.py` (backtracking), `strategist.py`, `evolution/impl_finder.py` |
| 6 | Type System + Contracts | **partial** | `plane_io_contracts.json`, `io_contracts.py`, `dag_contract.py` |
| 7 | Verification | **partial** | `dag_contract.verify_buildable_dag`, `components/conformance.py`, `run_proofs.py` |
| 8 | Optimization Passes | **partial** | `optimization_passes.json`, `pipeline_dag.choose` (descent), `evolution/{descent,token_reduction,distiller,substrate_selector}.py`, `inefficient_pipeline_archetypes.json` |
| 9 | Execution Runtime | **partial** | `dag/pipeline_dag.py`, `components/lowering.run_compiled`, `runtime/execution_providers/`, `workers/function_emulator.py` |
| 10 | Telemetry + Observability | **partial** | `synthesis/synthesis_trace.py`, `evolution/{descent_attempt_store,descent_measurement}.py`, receipts, OpenLineage adoption |
| 11 | Learning Engine | **partial** | `evolution/{meta_learner,external_outcomes,auto_tuning,rule_generator,self_optimizing_unit}.py`, the brain |
| 12 | Benchmarking + Simulation | **partial (bench yes / sim no)** | `evolution/ab_harness.py`, `live_eval.py`, eval datasets, `eval/durable_gap_harness.py` |
| 13 | Self-Expanding Discovery | **partial** | `discovery_pipeline`, `harvest_tools.py`, `research/source_search.py`, `research_queue` |
| 14 | **Template Library + Mutation** | **seed only** | `module_bundles.json` (8 recipes) → needs to become a 10⁴–10⁵ template library |

Read that as: the *skeleton of all 14 exists*; the work is **depth, scale, and three missing pieces** (simulation,
canonicalization, sandboxed discovery).

---

## Six refinements — how to make internet-scale actually work (scale is the goal)
1. **A bounded capability ontology is what lets the implementations be UNBOUNDED.** A capability is an **interface**
   (`extract_text_from_image: image → structured_text`); a component is an **implementation** of it (paddleocr, tesseract,
   a vision-LLM, and a million others). We already split this (`capability_graph.py`: a capability → its evolving
   *runners*). This is **not a cap on scale — it is the index that makes billions-to-trillions of components searchable**,
   exactly as a bounded query grammar makes Google's billions of pages searchable. So: capabilities = the interface layer
   (a curated **ontology**, ~10³–10⁴); components = the implementations (**unbounded — 10⁸, 10¹², and up**). The *more*
   implementations per capability, the better — more fallbacks, more competition, more data for the flywheel. The capability
   is the type; the component is the value; the value space is meant to be effectively infinite.
2. **At this scale the registry IS the moat — and it compounds the bigger it gets.** Being the substrate every agent
   routes through is a **network-effect + data-flywheel** moat, like Google's index: the components themselves may be
   public, but the **scale**, the **measured** metadata harvested from all the traffic (cost/latency/quality/failure on
   real workloads), the **learned** winning compositions, and the **governed** provenance (Baltor) all compound with every
   request — more agents → more traffic → better metadata → better routing → more agents. "paddleocr exists" is free to
   anyone; *"across billions of runs, for invoices, paddleocr is dominated by surya at $0.002/210ms/0.94"* exists only here,
   and only because of the scale. Scale is not separate from the moat — **scale is what makes the flywheel turn**, and the
   flywheel is the moat.
3. **Don't benchmark every candidate — *simulate* first.** Benchmarking on a 500-doc set per candidate makes the
   benchmark engine the bottleneck. Add an **analytic simulator** that scores a candidate DAG's cost/latency/quality from
   component metadata *without executing it*, prune to the top-k, then benchmark only those. Simulation is what makes the
   search tractable; it's the biggest missing piece in §12.
4. **Equivalence & canonicalization is the unlisted hard problem.** Knowing paddleocr ≈ easyocr ≈ tesseract ≈ vision-LLM
   for `extract_text` is what makes fallbacks, ladders, dedupe, and learning *generalize*. Without it, 100M components is
   100M unrelated rows and the model can't transfer a lesson from one to another. This deserves its own system (§15).
5. **RL over pipelines is the wrong starting point.** Cold-start (no data on day one), credit assignment (which node
   caused the win?), and non-stationarity (the registry changes under you) make deep RL brittle here. Start with
   **contextual bandits + template mining from winning traces + supervised priors**, and only graduate to RL where the
   signal is dense. Be honest about the cold-start: templates + simulation + transfer carry you until telemetry exists.
6. **Auto-discovery is a security surface, not just a metadata surface.** Tiers C/D (auto-discovered / user-uploaded) are
   *arbitrary code*. The trust tier must gate **execution** (hard sandbox: gVisor/Firecracker/WASM, egress control,
   resource caps), not merely visibility. This is exactly our `discovery ≠ trust` law made executable (§17).

---

## The seams in detail (the "systems" are their implementation — not a headline count)
*The enumeration below is the implementation depth behind the seven seams + the loop above. It is a reference for the
contracts, the prior art, and the hard parts of each piece — read it that way, never as "build 22 systems."*

### 1. Universal Capability Representation Layer
**Purpose.** Make every computational primitive machine-understandable as a *capability object* — a transformation, not a
function. **Have.** Planes (`tool_planes.json`), typed I/O per plane (`plane_io_contracts.json`), a capability hierarchy
(`capability_taxonomy.json`), cost-ordered fallback ladders (`capability_ladders.json`), and the capability→runners
evolution graph (`capability_graph.py`). **Hard problem.** A single schema rich enough to drive retrieval, typing,
composition, simulation, and learning — without 10M ad-hoc classes. **Architecture.** Two-level model: a **CapabilityID**
(the interface: typed input→output contract + a node in the ontology) and **ComponentRecords** (implementations) carrying
`{input_contract, output_contract, cost_per_call, p50/p95_latency, deterministic, quality_score, failure_modes,
fallbacks, dependencies, trust_tier, measured_from}`. `fallbacks` is *already* the ladder; `quality/latency/cost` are
*measured*, written back by telemetry (§10) — the object is a living record, not a static manifest. Capabilities and
components both get embeddings (for §4). **Build next.** Promote the component schema to this full object; back-fill
`cost/latency/quality` from `descent_measurement.py`; make `CapabilityID` a first-class row distinct from components.

### 2. Registry Layer (the substrate, not the moat)
**Purpose.** Hold 10⁸ components with trust + provenance. **Have.** The layered model (`registry_layers.json`: curated
core / staged-massive / feeds), the GitHub harvester (`harvest_tools.py`, content-hash dedupe + license classify),
staging JSONL → Postgres+pgvector, the promotion boundary. **Hard problem.** Trust at scale + dedupe at the *capability*
level, not just content hash. **Architecture.** Four **trust tiers** as an admission/execution gate: **A** trusted-curated
(hand-verified; may run unsandboxed) · **B** community-verified (crowd + benchmark score) · **C** auto-discovered
(crawler; sandbox-only until benchmarked) · **D** experimental/user-uploaded (sandbox-only, never global). Each tier has
explicit promotion criteria (source, dedupe, content-hash, license, **security_score**, **reliability**, benchmark
results). Sources to add beyond GitHub/PyPI/RapidAPI: **npm, Docker Hub, Hugging Face**. **Build next.** Add the
`trust_tier` + `security_score` + `reliability` fields and make them gate execution (§7/§17); wire npm/HF/Docker harvesters.

### 3. Universal Adapter Layer (built — v1)
**Purpose.** Erase bespoke integrations: everything is `invoke(inputs) → outputs`. **Have.** `src/teleon/components/`
(`Component.invoke` over bespoke ports, `register_component_invoker` drop-in, `assert_conforms` gate, `lower_to_dag` +
`run_compiled`) + the agnostic ports (llm/embedding/reranker/search/ocr/browser) + `runtime/execution_providers/`
(docker/k8s/serverless/cloudflare/byo). **Hard problem.** Auto-generating a conformant adapter for *any* external surface.
**Architecture.** An **adapter factory** per surface kind that emits a `Component`: **OpenAPI/Swagger** spec → typed
component; **Docker image** → component (run container, map stdin/stdout to typed I/O); **MCP server** → component (we have
the MCP gateway); **CLI** → component (argv/stdin/stdout schema); **SQL** → component (parameterized query); **remote
inference** (vLLM/Together/Replicate) → component; **Python callable** → component (introspect signature). Each generated
adapter must pass `assert_conforms` before entering the registry. **Build next.** Ship the OpenAPI and Docker adapter
factories first (highest fan-out: they turn whole ecosystems into components automatically).

### 4. Retrieval Engine (millions → dozens, as a *subgraph*)
**Purpose.** Find the right few components from millions. **Have.** Lexical+vector search (`component_search.py`), RRF
hybrid (`retrieval/hybrid.py`), ladders as capability families, access-policy filtering, and `capability_graph.py` as a
graph substrate. **Hard problem.** Retrieving a **composable subgraph**, not a bag of individually-relevant components.
**Architecture.** A hierarchical funnel: **(1)** lexical BM25 → **(2)** vector over capability embeddings → **(3)** graph
retrieval over a **component compatibility graph** (edges = type-compatible *and* historically-co-occurring, from §10
telemetry) so you pull components that *connect* → **(4)** capability families (the ladder gives you the fallback set for
free) → **(5)** constraint pushdown (local-only / cheap-only / low-latency / gpu / privacy-safe). Tools at scale: Qdrant/
FAISS for vectors, a graph store for (3). **Build next.** Build the compatibility graph from execution traces and add
constraint pushdown; this is what turns retrieval from "relevant" into "composable."

### 5. DAG Composition Engine (program synthesis, not single-shot)
**Purpose.** Turn the candidate pool into candidate DAGs. **Have.** LLM-orchestrated composition (`compile_capability_live`:
candidate pool → LLM picks real components → validate + repair + type-aware grounding), backtracking
(`synthesis_tree.py`), escape strategies (`strategist.py`), implementation search (`impl_finder.py`). **Hard problem.** It
currently produces *one* DAG; synthesis needs *many* scored candidates. **Architecture.** Treat the LLM as the **proposal
distribution** and the registry+types as the **constraint**; search with **beam search** (keep top-N partial DAGs) or
**MCTS** over the composition tree, seeded by **templates** (§14) so most requests are *mutations of a known-good skeleton*
rather than from-scratch synthesis. Score partials with the **simulator** (§12). **Build next.** Add beam search returning
k candidate DAGs (it already validates each); feed them to simulation→benchmark instead of committing to the first.

### 6. Type System + Contracts Engine (LLVM-style)
**Purpose.** Reject invalid wirings at compile time. **Have.** Typed plane I/O (`plane_io_contracts.json`),
`edge_compatible`, type-level satisfiability in `dag_contract.py`. **Hard problem.** Flat types are too coarse — `jpeg`,
`png`, `webp` are all `image`; `html` can become `markdown` via a converter. **Architecture.** A **type lattice**
(subtyping: `jpeg <: image`), so a producer of `jpeg` satisfies a consumer of `image`; and a **coercion graph** (types as
nodes, converter components as edges) so when an edge *doesn't* type-check, the compiler searches for a shortest coercion
path and **auto-inserts a converter** (this is a compiler optimization pass too, §8). Contracts become richer than types:
pre/post-conditions, units, PII flags. **Build next.** Add the subtyping lattice + the coercion graph with auto-insert;
this single feature massively widens what composes.

### 7. Verification Engine (never trust the planner *or* the component)
**Purpose.** Prove a DAG is safe and working before it runs. **Have.** `verify_buildable_dag` (acyclic + type-compatible
+ satisfiable inputs + terminal output + dry-run), `assert_conforms`, 613 proofs. **Hard problem.** Verifying *untrusted*
components and *real* behavior, not just structure. **Architecture.** A **verification ladder** (cheapest first):
static (acyclic/types/satisfiable) → dry-run (synthetic typed data through the real executor) → **sandbox execution**
(Tier C/D in gVisor/Firecracker/WASM with egress + resource caps) → **synthetic-data test** (run on a few held-out
examples, check the output contract holds) → **security audit** (unsafe endpoints/secrets/egress) → benchmark (§12). A DAG
is promotable only at the rung its trust tier requires. **Build next.** Sandbox execution + synthetic-data testing — the
two rungs that make auto-discovered components safe to run.

### 8. Optimization Pass Engine (LLVM for cognition — our core IP)
**Purpose.** Rewrite a valid DAG into the cheapest equivalent one. **Have.** `optimization_passes.json` (10 passes), the
descent (`pipeline_dag.choose` cheapest-viable; `evolution/descent.py`, `descent_axes.py`), and concrete passes already in
code: `token_reduction.py`, `distiller.py` (LLM→deterministic rule), `substrate_selector.py` (cheapest backend),
`inefficient_pipeline_archetypes.json`. **Hard problem.** Scaling to *hundreds* of passes with correct ordering and a
cost model. **Architecture.** A **PassManager** like LLVM: **analysis passes** (cost/latency/criticality estimate) feed
**transform passes**, run to a **fixpoint**, each pass **legality-checked** to preserve the verified contract (a pass may
never break §7). The catalog grows well past 10: token reduction · model downgrade (frontier→small) · **deterministic
replacement** (LLM→regex/parser) · parallelization · cache insertion · **browser→direct-API** · retrieval reduction
(20 chunks→3) · API fusion · request batching · precomputation · coercion-insert (§6) · dead-branch elimination ·
common-subgraph elimination (§18 memoization). **Build next.** A real PassManager + cost model; migrate the JSON passes
into legality-checked transforms; this is where "remove unnecessary intelligence" literally happens.

### 9. Execution Runtime (production-grade, distributed)
**Purpose.** Run the graph reliably. **Have.** `pipeline_dag.DAG.run` (data-flow order, If/Loop/choice/merge, receipt),
`run_compiled`, the execution-provider port (docker/k8s/serverless/cloudflare/byo), a durable function emulator. **Hard
problem.** Distribution + durability at scale. **Architecture.** Data-flow execution where each node's output is a
**content-addressed artifact** (enables checkpoint/resume, memoization §18, and references-not-blobs); the
**execution-provider port** places nodes on the right backend (local/serverless/gpu/byo via `substrate_selector.py`); add
retry/backoff, **rate-limit handling**, **streaming** between nodes, partial rollback, and resource allocation. Reference
designs: Temporal (durability) and Dagster (asset graph). **Build next.** Content-addressed artifacts + checkpoint/resume
and rate-limit-aware scheduling — the two that make long internet-scale graphs survivable.

### 10. Telemetry + Observability Engine (the data that *is* the moat)
**Purpose.** Capture every execution forever. **Have.** Per-step traces (`synthesis_trace.py`), the descent attempt store
+ measurement (`descent_attempt_store.py`, `descent_measurement.py`), receipts, OpenLineage adoption. **Hard problem.** A
unified, queryable trace at internet scale that *closes the loop* into capability metadata and learning. **Architecture.**
Every run emits an **OpenLineage-shaped event** (Job/Run/Dataset + facets): `{pipeline_id, capability, per-node
{component, cost, latency, tokens, success}, failure_points, total}`. Land it in the **history tier** (warehouse). Two
write-backs make it the moat: (a) update each component's **measured** cost/latency/quality (§1), (b) reinforce the
**compatibility graph** (§4) and **template** stats (§14). **Build next.** The OpenLineage event + the two write-backs —
without them, telemetry is logs; with them, it's a self-improving registry.

### 11. Learning Engine (bandits + mining first, RL later)
**Purpose.** Get better at composing over time. **Have.** `meta_learner.py`, `external_outcomes.py` (learn from runs we
never ran), `auto_tuning.py`, `rule_generator.py` (LLM→deterministic rule), `self_optimizing_unit.py`, the brain. **Hard
problem.** Cold-start, credit assignment, non-stationarity. **Architecture.** Five learning targets, easiest signal first:
(1) **measured metadata** (just averaging telemetry — trivial, do first); (2) **retrieval ranking** (which components/
subgraphs win → a bandit over candidates); (3) **template mining** (cluster winning traces → new templates, §14);
(4) **composition priors** (fine-tune the proposal distribution / few-shot from winners); (5) **pass selection** (when does
each optimization pass pay off). Keep losers (lossless law) to avoid re-exploring dead ends. **Build next.** (1) + (3) —
measured write-back and template mining — before any RL; they carry the cold-start.

### 12. Benchmarking + Simulation Engine (simulate, *then* benchmark)
**Purpose.** Pick the best candidate DAG before deploying. **Have.** A/B harness (`ab_harness.py`), `live_eval.py`,
ground-truth eval datasets, the durable gap harness. **Missing.** The **simulator**. **Architecture.** Two stages:
**Simulate** — an analytic model that, from component metadata (§1), estimates a candidate DAG's cost/latency/quality and
**probability of success** *without executing it*, so beam search (§5) can rank k candidates cheaply. **Benchmark** — run
only the top-k against a **per-capability benchmark dataset** (e.g. 500 invoices with ground truth), measure
accuracy/latency/cost, pick the winner; then **shadow** it before promotion. **Build next.** The simulator (it unblocks
real multi-candidate search) + a benchmark-dataset registry keyed by capability.

### 13. Self-Expanding Discovery Engine
**Purpose.** Continuously grow the registry from the open world. **Have.** The discovery pipeline (scrape→classify→ideate→
govern), `harvest_tools.py`, `source_search.py`, the research queue. **Hard problem.** Inferring a *capability + types*
from a repo and proving it's safe/useful. **Architecture.** crawl (GitHub/PyPI/npm/HF/Docker) → read README/code → **LLM
infers capability + input/output contracts** (proposes; never trusted) → **sandbox test** (§7) → **benchmark** (§12) →
**assign trust tier** (§2) + **measured metadata** (§1) → register. discovery ≠ trust is the law: an inferred capability is
a candidate until the sandbox+benchmark confirm it. **Build next.** README→capability/type inference + the sandbox+
benchmark gate that auto-sets the trust tier; this is the loop that takes the registry from hundreds to millions.

---

## 14. Template Library + Mutation Engine (your "missing thing" — strongly agree)
**Most requests are not novel.** Synthesizing from scratch every time is the expensive path; **mutating a known-good
skeleton** is cheap and reliable. **Have.** `module_bundles.json` (8 recipes) — the seed. **Architecture.** A library of
**canonical templates** (Document-Extraction, Web-Research, Browser-Automation, Enrichment, RAG-QA, ETL, …) each a typed
parameterized DAG skeleton with named slots; composition (§5) first **retrieves a matching template** and the LLM
**fills/mutates slots** (swap the OCR rung, add a validation step) rather than building from zero. Templates are **mined**
from winning traces (§11) and ranked by §10 telemetry, so the library *grows itself*. Target: 10⁴–10⁵ templates. **Why it
matters.** It collapses the search space (§5) for the common case and is the single biggest efficiency lever after the
descent. **Build next.** A template schema + "retrieve-and-mutate" mode in the compiler + a miner that promotes recurring
winning subgraphs into templates.

---

## Systems you're underweighting (15–19)
- **15. Capability Equivalence & Canonicalization.** The unlisted hard problem (refinement #4). Cluster components that
  realize the same `CapabilityID`; assign canonical capability identities; dedupe at the *capability* level. Without it,
  fallbacks/ladders/learning can't generalize across the registry. Signals: shared I/O contract + benchmark-output
  agreement on a probe set + embedding proximity.
- **16. Cost & Economics Model.** The objective the whole compiler optimizes is multi-dimensional: **$ · latency · tokens
  · quality · privacy/risk · carbon**. Make it one explicit, **user-weighted** function — we already have a
  `PreferenceProfile` ("efficient" = the user's trade-off). Every pass (§8) and the simulator (§12) consult it. Without a
  single cost model, "most efficient" is undefined. **→ Expanded into the full economic/market layer below (§20–22): the
  registry is a *market*, and the cost model must run over LIVE provider economics, not static metadata.**
- **17. Security & Sandboxing / Trust (cross-cutting).** Executing Tier C/D components safely: gVisor/Firecracker/WASM
  isolation, egress allow-lists, resource caps, secret scoping (`SecretRef`), and the trust tier gating *execution*. This
  is `discovery ≠ trust` made operational, and it's a prerequisite for §13 at scale.
- **18. Caching & Memoization substrate.** Content-addressed artifacts (§9) → **memoize sub-DAGs**: identical (component,
  inputs) returns the cached output; common-subgraph elimination across pipelines (§8). We have a trajectory-fragment
  cache; generalize it. Often the single biggest cost win on repeated traffic.
- **19. Governance & Provenance = Baltor (the truth authority).** The compiler optimizes *efficiency*; it must never
  decide *truth*. Every compute output is `serves_truth=false` — a candidate — and **Baltor** dispositions truth-bearing
  outputs with provenance, verification, and CDC. This separation (Teleon = efficiency, Baltor = truth) is what lets the
  system be both aggressive about cost and trustworthy about results.

---

## The registry is a MARKET — the economic layer (Systems 20–22)
**The biggest expansion after the reframe (owner + external review):** a registry of *callable components* is too narrow.
**The real abstraction is a registry of executable ECONOMIC OPPORTUNITIES.** The same capability is realized by many
implementations; the same model is served by many providers (official *and* secondary) at different prices, latencies, and
availabilities; and those economics **change continuously**. So Teleon must think in **markets, not a static catalog**: a
real-time **exchange** that knows the price, capability, latency, quality, trust, and availability of *all computation* — a
**Bloomberg Terminal for computation**. At agent scale this is not a feature, it is the **most valuable layer**, and it
*compounds the data-flywheel moat*: you own live price/latency/availability across every provider, not just quality.

### Distinct entity types — ONE joined economic graph
The right model is several distinct **entity types** that **join into one graph**, so the router traverses
`capability → component → model → provider → endpoint → live-economics` in a single path (you cannot route if the price
data is siloed from the implementations). We already have the seed of exactly this: `model_provider_graph.json`
(model⇄provider nodes + edges). The entity types, mapped to what exists vs. the gap:

| # | Registry (entity type) | Have today | Gap |
|---|---|---|---|
| 1 | Capability (interface) | `capability_taxonomy.json`, `evolution/capability_graph.py` | full CapabilityID rows |
| 2 | Component (implementation) | `tool_registry.json`, staged JSONL, search index | scale + measured metadata |
| 3 | **API Endpoint** | `capability_endpoint_registry.json` (cost_units), `external_api_registry.json` | per-endpoint rate-limit/batch/latency at scale; secondary providers |
| 4 | **Model** | `model_index.json`, `ml_model_registry.json`, `model_quality_tier_codes.json`, `model_specialization_codes.json` | continuous benchmark dims (reasoning/OCR/JSON/hallucination) |
| 5 | **Provider** | `model_provider_graph.json`, `competitive_provider_mappings.json`, `ocr/search_provider_registry.json`, provider status codes | the model×provider economic edges, populated + LIVE |
| 6 | **Infrastructure** | `execution_backend_pricebook.json`, sandbox/blackboard/swarm/compression provider catalogs | vector-db / browser / GPU providers at scale |
| 7 | Workflow Template | `module_bundles.json` (seed) | the 10⁴–10⁵ library (§14) |
| 8 | **Economic** | `execution_backend_pricebook.json` (request/duration cost + `last_reviewed_at` + source + confidence), `inference_lane_profiles.json` (cost/latency/egress), free/lowcost endpoint registries | **LIVE** facets across all of the above |

The skeleton of all 8 exists. The work is **scale + the JOIN + making the economic facets LIVE**.

### System 20 — Provider Intelligence Engine (make the economics LIVE)
Prices/latency/availability change daily; static cost metadata rots. A **pricing + latency crawler** monitors **official**
providers (OpenAI/Anthropic/Google) and **secondary** providers (OpenRouter/Together/Groq/Fireworks/Replicate, and
self-hosted vLLM/k8s) → emits **CDC events** → updates the economic facets. We already have the CDC/freshness machinery
(`evolution/freshness_runtime.py`, `evolution/source_poller.py`) and the pricebook already carries `last_reviewed_at` +
`source` + `confidence`. **Build:** point the crawler at provider pricing and stream economic-CDC.

### System 21 — Computational Economics Engine (one objective function)
"Most efficient" must be **one explicit, user-weighted multi-objective function** over **$ · latency · energy ·
privacy/risk · hallucination-risk · failure-rate · availability**. The pieces exist — `PreferenceProfile` (the user's
trade-off, already built), `inference/model_efficiency.py`, the pricebook, the lane profiles — but not ONE engine the
simulator (§12), the optimization passes (§8), and the router (§22) all consult. **Build:** a single
`cost_model(candidate, profile) → score` every layer calls. (This subsumes and replaces §16.)

### System 22 — Dynamic Routing Engine (BGP for computation)
Like internet routing: when a provider degrades or a cheaper/faster route appears, **re-route and recompile** the affected
pipelines automatically. We have *selection* (`inference/lane_selection.py`, `inference/implementation_selector.py`,
`evolution/substrate_selector.py`) + the descent; the gap is the **live loop**: economic-CDC (§20) → re-score (§21) →
reroute + recompile (the optimization engine §8). **Secondary-provider arbitrage** is first-class: the same model on Groq
vs Together vs OpenAI vs self-hosted is four routes with different economics; the router picks per the live cost model over
the `model_provider_graph`. **Build:** the reroute-on-CDC loop + arbitrage traversal.

### Capability futures — recompile on discovery
When discovery (§13) + the benchmark swarm (§12) find a component that dominates (a new OCR repo at 0.95 quality /
$0.0003), the system **re-scores and recompiles** the thousands of pipelines whose best route just changed — a
forward-looking "the best pipeline for X just changed" signal. Discovery + learning + routing, closing the loop.

### The phases (where we are)
1. Registry of **tools** — *done*. 2. Registry of **computational primitives** — *mostly done* (planes, ladders, ML
models, endpoints). 3. Registry of **computational markets** — *the current frontier* (the 8 entity types exist; the JOIN
+ LIVE economics is the work). 4. **Global routing layer for machine intelligence** — the exchange every agent routes
through (the scale goal; §22 at internet scale, the Google/Bloomberg-of-computation position).

---

## The compile loop (your first-principles loop, refined with the pruners)
```
Human intent
  → Capability representation            (§1: interface, not implementation)
  → Retrieve a composable subgraph        (§4: millions → dozens, PRUNE)
  → Retrieve / mutate a template          (§14: skeleton, not scratch, PRUNE)
  → Compose k candidate DAGs (beam/MCTS)  (§5: LLM proposes under type+template constraints)
  → Type-verify + auto-coerce             (§6: reject invalid wirings, PRUNE)
  → Simulate → rank → benchmark top-k      (§12: cheap score first, run few, PRUNE)
  → Verify (static→dry-run→sandbox→test)   (§7: never trust planner or component)
  → Optimization passes (PassManager)      (§8: rewrite to cheapest equivalent)
  → Execute cheapest viable graph          (§9: durable, distributed, memoized §18)
  → Observe execution trace                (§10: OpenLineage, store forever)
  → Learn: metadata, templates, ranking    (§11: write back to §1/§4/§14)
  → Govern truth                           (§19: Baltor dispositions; serves_truth=false)
```
The loop is a **funnel of pruners** wrapped in a **learning cycle**: each pass narrows the space, telemetry feeds the next
request's priors, and Baltor keeps truth separable from efficiency.

---

## Sequencing — what to build, in order (honest priorities)
1. **Close the metadata loop** (§10 write-back → §1 measured cost/latency/quality) **and join + make LIVE the economic
   registries** (§20: point the existing freshness/CDC machinery at the `execution_backend_pricebook` + provider prices).
   Cheap; turns logs + prices into the moat — this *is* the data flywheel.
2. **The simulator** (§12) **over the unified cost model** (§21). Unblocks real multi-candidate search + live routing;
   everything downstream depends on cheap economic scoring.
3. **Template library + retrieve-and-mutate** (§14). Biggest efficiency lever for the common case.
4. **Beam search composition** (§5) + **type lattice & coercion** (§6). Multi-candidate, wider composability.
5. **PassManager + cost model** (§8 + §16). Scale the optimization that is the core IP.
6. **Sandbox + trust-tier execution** (§17/§7) → unlocks **discovery at scale** (§13) and the move to millions.
7. **Adapter factories** (§3: OpenAPI, Docker) and **equivalence/canonicalization** (§15) in parallel — they make the
   registry both *grow* and *generalize*.
8. **Dynamic Routing Engine** (§22) — once live economics (§20) + the cost model (§21) exist, close the reroute-on-CDC +
   recompile loop and exploit secondary-provider arbitrage over the `model_provider_graph`. This is the exchange layer —
   the global routing position every agent flows through, and the endgame of the scale thesis.

## The thesis
Models will keep getting smarter; that is not our bet. **Our bet is that the larger, more durable value is a system that
decides when intelligence is unnecessary** — that compiles an ambiguous request down to the cheapest deterministic graph
that provably works, calling a model only for the irreducible residual, and that learns to need the model less over time.
That is a new **systems architecture layer for computation**, not a product feature. Teleon is the compiler; Baltor is the
truth authority; the registry is the substrate; the descent is the optimizer; and *removing unnecessary intelligence* is
the objective function.
