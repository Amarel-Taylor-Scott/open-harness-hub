# Why registries feel semantic but aren't verifiable edge graphs — and the Open Primitive Format

> Owner (2026-07-10): "Why do GitHub / PyPI / other registries easily allow semantic search of packages and
> code with edge-based input/output descriptions? Are there agentic standards for edge-based search and use?
> People are rebuilding GitHub for the agentic era but I see no standards on code primitives and edges. Google
> shipped an Open Knowledge Format — has anyone published an Open Edge / Open Primitive Format? Are we in a
> position to implement an open edge + open graph standard supporting multiple/tunable embeddings, multiple
> weighted edges, search systems?" — and "will Teleon be able to query the primitive database … extensibility?"

Short answers, then the evidence: **registries feel semantic because they index names, text, symbols,
dependency graphs, popularity, and increasingly embeddings — but none maintain a machine-verifiable "this
output safely satisfies that input under these effects" graph.** That is a *precision* gap, not an indexing
gap: registry search may return plausible candidates a human inspects; automatic primitive composition must
**reject a false edge before code runs.** No published standard fills it — **there is no Open Edge / Open
Primitive Format** — and we are unusually well positioned to define one, because we already built the
*verification* layer registries lack. We shipped a first version (`open_primitive_format.py`, OPF v0) this
session, and its query interface is exactly the extensibility seam Teleon and future extensions use.

---

## 1. Why registries look semantic but are not verifiable edge graphs

| Registry | What it actually indexes | What it does NOT maintain |
|---|---|---|
| GitHub code search | trigrams + symbols + repo/path/lang facets; increasingly embeddings | a typed output→input compatibility graph; effects; safe-chaining |
| PyPI | project name, description, classifiers, dependencies, (now) attestations/SBOM/lock metadata | what a package's functions *consume/produce*; whether two packages compose |
| npm / crates / Maven | names, deps, download counts, README text | machine-checkable interface compatibility across packages |
| Sourcegraph / SCIP | language-agnostic symbols + references (a real code graph) | a *safety* verdict that output X satisfies input Y under effects |
| Vector code search | dense/hybrid retrieval over docstrings + code | precision-critical admission (retrieval returns neighbors, not proofs) |

The through-line: these are **retrieval systems**. Retrieval is *allowed* to return a plausible-but-wrong
candidate — a human reads it and decides. **Automatic composition has no human in the loop before execution**,
so a false edge means wrong code *runs*. That precision requirement — not embedding technology — is why
text/embedding search looks "solved" while cross-mint output→input compatibility is not. Our own benchmark
measures the exact failure: name-equality alone auto-authorizes a same-name/different-unit join (1 false
authorize); the contract-aware classifier catches it (0). Registries live on the name-only side of that line.

---

## 2. The agentic-standards landscape (surveyed) — all stop before typed edges + safe chaining

| Standard / draft | What it is | Where it stops |
|---|---|---|
| **MCP** (Model Context Protocol) | tools/resources/prompts a model can call over a server | tools are named + JSON-schema'd; no typed *primitive edges*, effects, or composition safety |
| **A2A** (Agent-to-Agent) | agent-to-agent messaging + task delegation | agent capabilities as cards; not a verifiable output→input graph |
| **AgentSkill objects** | packaged agent skills with metadata | discovery metadata; no cross-skill typed compatibility |
| **ARD** (Agentic Resource Discovery, draft 2026-05) | federated, search-first discovery across MCP/A2A/skills/APIs/workflows | **intentionally stops before invocation**; capabilities are *search metadata*, not typed edges + effects + safe chaining |
| **Google Open Knowledge Format** | portable knowledge-graph interchange | *knowledge* facts, not executable primitive *edges*/contracts |
| Schema/API registries (Buf/Apicurio, Protobuf/Avro/JSON-Schema) | per-format compatibility + lifecycle | single-format; not a cross-mint capability/edge/evidence graph |

The closest to "agentic search," ARD, explicitly leaves capabilities as *search metadata* and stops before
invocation. **None define typed primitive edges, effects, evidence, or safe chaining** — the invocation-safe
layer is the open gap.

---

## 3. Why we are positioned to define the missing standard

The standard nobody published needs a *verification* layer, and that is precisely what this session built:

- **Directional contracts + a proved adapter DSL** (`edge_contract_and_adapters`) — width subtyping, units,
  classified total-lossless/partial/lossy adapters. Registries have none of this.
- **A graded compatibility lattice** (`compatibility_lattice`) — names retrieve (`CLOSE_CANDIDATE`), contracts
  authorize. The invocation-safety verdict ARD stops before.
- **A capability/implementation zoo** (`capability_implementation_zoo`) — a capability is a family with an
  immutable Pareto set of implementations, not one package.
- **Claim-scoped, digest-bound evidence** (`primitive_attestation`) — the trust layer registries defer to
  provenance-only.
- **Multiple/tunable embeddings + multiple search systems** — already a zoo in the retrieval graph; OPF carries
  them as first-class descriptors.
- **A held-out adversarial benchmark** proving the safety invariant (0 false auto-authorizes).

A registry indexes; we *admit*. That verification layer is the moat and the reason an Open Primitive Format
from us would carry something the ecosystem lacks.

---

## 4. The Open Primitive Format (OPF v0) — shipped this session

`open_primitive_format.py` is the concrete artifact. An OPF record carries what a verifiable edge graph needs:

- **Multiple weighted directional ports** — `ports.consumes[]` / `ports.produces[]`, each `{edge, role, weight,
  required, contract_ref}` (a primitive is an *action* with many typed ports, not one input/one output).
- **Multiple tunable embeddings** — a list of `{model, dim, space, vector_ref, tunable}` (256-d model2vec,
  384-d BGE, 30000-d sparse SPLADE all coexist on one record; the search system is pluggable).
- **The capability/implementation split**, **evidence refs**, **delivery modes** (the matrix), and a **named
  compatibility authority** — an OPF edge *name retrieves; it never authorizes* (that's the lattice's job).
- **Governance** — `serves_truth=false` is a required field (the candidate/truth boundary travels with the
  record).

It validates and round-trips every corporate-pack card. It is **complementary to ARD/MCP**: ARD/MCP discover
*resources*; OPF is the invocation-safe *edge + contract + evidence* layer they stop before. The standards
stance (from the tradeoff analysis) holds — **do not build a universal super-IR**; keep native formats
(WIT/Protobuf/OpenAPI/Arrow) lossless and let OPF be the small Teleon-owned kernel + replaceable projections
over them, owning only the differentiating semantics (capability/implementation identity, effect contracts,
directional compatibility, adapter risk, evidence, admission, PlanLock, slicing, receipts).

---

## 5. Teleon can query the substrate — and so can future extensions

The same module answers the extensibility question. `OPFQuery` is a **stable, extensible query contract**:
`build_opf_index(records)` + `query(method, index, **args)` over a query-method **zoo** (`by_capability`,
`producers_of`, `consumers_of`, `by_delivery_mode`, `by_embedding_model`). The self-test proves a **Teleon-style
external consumer** — one holding only OPF + the query contract, *no internal card import* — resolves "what
produces this edge" and hydrates portable records. Adding a new query method / search system / embedding lane is
**one registered row**, and existing callers are unaffected — that is the extensibility guarantee.

This aligns with the portfolio dependency law: **products consume the substrate, never the reverse.** Teleon
queries the primitive database through OPF + the query seam (and the existing `/registry/` seam, MCP tools, and
the 27-action agent API); it does not import substrate internals. So: **yes, Teleon can query the primitive DB,
the infrastructure supports it, and the format + query zoo are built for future extensions** — a new consumer
or a new query capability is additive, not a breaking change.

---

## 6. The path to a published standard (if the owner wants to)

OPF v0 is a working internal format. To publish it as an *open* standard:

1. **Freeze the v0 schema** (this session's record shape) + a JSON-Schema for it; version it (`opf_version`).
2. **Adapter + compatibility spec** — publish the classified-adapter DSL and the compatibility lattice as the
   *admission* half ARD/MCP lack (the differentiator).
3. **Evidence predicate registry** — reuse in-toto/SLSA predicate types; add the Teleon-specific ones
   (contract-test, compatibility-verdict, execution-receipt) as named predicates.
4. **Bridges, not forks** — importers from WIT/Protobuf/OpenAPI/Arrow (lossless where possible, `UNKNOWN`
   where not) so OPF federates native formats instead of replacing them.
5. **A reference validator + query server** (the shipped `open_primitive_format` is the seed) so adopters get a
   conformance test, not just prose.

The naming space the owner explored (dontrebuild / reuse-first / deterministic-LLM-last / proof-aware-compiler)
maps cleanly: OPF is the **proof-aware capability graph** under the reuse-first thesis — the standard for a
verifiable, invocation-safe edge graph that the agentic-GitHub efforts are missing.

*Grounded in the session's shipped modules (all self-test + run_proofs green) and the surveyed standards; the
ARD draft and PyPI/PEP facts are as of 2026-07; re-verify any external claim before publishing.*
