# How primitives are stored, delivered, and integrated

> Owner questions (2026-07-10): *"how primitives can be stored, used, and integrated — are MCP tools just
> downloading files? are primitives packaged into PyPI and imported? are primitives copied into files using
> command-like tools that can edit files?"* and *"does GitHub allow that many small files … in a way where we
> can track lineage, remixing, and other metadata?"*

Short answers: **storage** is three tiers (git holds *generators + schemas*, a database holds the *operational
corpus + lineage*, object storage holds *bulk payloads*) — millions of primitives are **not** individual git
files. **Delivery** is not one mechanism but a **ladder of five**, each a different level of reuse coupling;
MCP retrieval, PyPI-style import, and CLI file-copy are all real rungs on it, chosen per situation. Every
mechanism below already exists in this repo as a script or table.

---

## Part 1 — Storage: three tiers, not a pile of files

Measured today (2026-07-10): the repo tracks **37,007 files** with a **2.6 GB** `.git`. The **~1.17M
primitive records** and all generated composition/deployment data are **gitignored** — the git tree holds the
*deterministic generators*, schemas, and curated seeds, not the generated rows. That split is deliberate and
correct.

### Why not "millions of small files in git"

Git and GitHub degrade badly on that shape, and it buys nothing:

- **Git itself:** every file is an index entry; `status`, `checkout`, `clone`, and diff all go superlinear
  past ~100k files. A working tree of a million tiny JSON files makes ordinary commands take minutes and bloats
  the pack. We already feel this at 37k files + a 2.6 GB history — the cleanup backlog's P0 is *reducing*
  tracked generated data, not adding more.
- **GitHub limits:** 100 MB hard per-file cap, ~1–5 GB recommended repo size, API rate limits that make
  per-file operations impractical at scale, and no query surface — you cannot ask GitHub "give me every
  primitive that produces `OfficerRowBatch`."
- **Lineage/remix/metadata is a *query*, not a *path*.** "What remixes descend from this card," "what's the
  provenance chain of this served fact," "which primitives fill this slot" are **relational/graph queries**.
  A filesystem answers them with `grep`; a database answers them with an index and a foreign key. Storing
  lineage as file paths is the anti-pattern the whole naming/edge system exists to avoid.

### The three tiers (each already stubbed here)

| Tier | Holds | Where | In git? |
|---|---|---|---|
| **Source of truth (git)** | generators, schemas, vocabularies, curated seeds, the *code* of every primitive family | this repo | yes — small, reviewable |
| **Operational store** | the queryable corpus + embeddings + **lineage/remix/metadata as columns + FKs** | Postgres + **pgvector** (`db/postgres/schema.sql` `object_embedding`, and the tiered `record_store`) | no |
| **Bulk / cold** | full payloads, JSONL shards, held-out + rejected candidates (lossless history) | object storage (S3 / the `cloud_provisioning` S3-Vectors plan) | no |

Lineage and remix edges live in the operational store as first-class rows (the composition layer already emits
`lineage: {parent_card_id, transform_id}` on every remix, and provenance-chain records on served facts) — so
"track lineage, remixing, and other metadata" is a **schema** question, answered by columns and indexes, and
git stays the home of the *code that produces and governs* those rows, not the rows themselves.

---

## Part 2 — Delivery + integration: a ladder of five reuse modes

"Used and integrated" is not one thing. A primitive can be reused at five increasing levels of coupling, and
the right rung depends on the situation (governance needs, offline needs, token budget, and whether the
consumer's runtime is trusted). All five exist in the repo today.

### Rung 1 — Retrieve **by reference** (the MCP default) · lowest coupling, 0 files
`primitive_get` / `primitive_search` return the primitive's **typed edges + proof status + governance state**,
**not its body** (the full source is behind an explicit `include_payload=true` switch). The agent composes by
**name and edge**, not by copying code. *This is the answer to "are MCP tools just downloading files?" — **no**:
by default nothing is downloaded; the agent gets a reference and the reinvention-guard verdict.* Lowest
coupling, always current, fully governed.

### Rung 2 — Retrieve **the verified source** (MCP `include_payload=true`) · the prompt-inject lane
The tool returns the tested body with "use this as-is, do not re-implement." Reuse happens **in the prompt**.
Measured reality (the honest ledger): this is **prompt- and model-dependent** — showing the *full tested
source* can pass (~0.6 @ ~108 output tokens) while showing *signatures only* makes models re-implement and
fail. So it works, but it is not a universal win, and it is retrieval-of-content, still not a "download."

### Rung 3 — **Package import** (PyPI-style) · 0-token reuse, strongest single-shot win
`primitive_package_contract.py` + `package_linkable_primitive_cards.py`: verified primitives are packaged so a
consumer does `from verified_primitives.<x> import <fn>` and the model **imports** rather than regenerates —
the code never enters the prompt (0 output tokens for the reused part). *This is the answer to "are primitives
packaged into PyPI and imported?" — **yes**, that's this rung.* Caveat: to preserve governance we distribute
through a **private/governed index** (not necessarily public PyPI), and the import requires the package
installed in the consumer's environment — which is exactly what the **deployment profiler** (`deployment.estimate`)
sizes: the deps, substrate, and resources that lane needs.

### Rung 4 — **Vendor / file-copy** (CLI edit-tool) · highest coupling, offline + auditable
`demo_vendor_onboarding.py`: the verified primitive is **copied into the consumer's repo** (they then track and
own it) — the `go vendor` / "copy the snippet in" model, via a command-line/edit tool. *This is the answer to
"are primitives copied into files using command-like tools that edit files?" — **yes**, that's this rung.* Best
when the consumer needs offline builds, a frozen version, or a full audit trail in their own VCS; the cost is
that updates no longer flow automatically (they re-vendor).

### Rung 5 — **Deterministic composition** (the 0-token floor) · model-independent
A manager emits thin wiring from declared config and **mounts the verified module verbatim** into a runnable
route (the integrator / `compose_route`). This passes hidden oracles with **no model call for the reused
logic** and is model-independent — the most robust win, and the one the network/grid-search layer is built to
find.

### And for running a primitive *as a service*
`build_deployment_packaging_surface_pack.py` packages primitives/routes as **deployables** — OCI images,
Terraform modules, Helm charts, marketplace bundles — with digest pinning and SBOM policy. The deployment
profiler decides *which* medium (K8s vs cloud function vs …) and *how big*.

---

## The through-line

> **Refined 2026-07-10** (external review; see `../strategy/primitive-architecture-shipped-and-target-2026-07-10.md`
> Part C). The "ladder" is better modeled as a **delivery MATRIX**: the modes trade coupling, isolation,
> latency, install cost, security, licensing, portability, and observability *differently* — deployment is NOT
> strictly "higher" than import, and a sandboxed WASI component can be more isolated than a vendored source
> copy. Also: importing a *digest from a locked closure after admission checks* can be a STRONGER trust story
> than pasted/vendored source, not a weaker one. Read the rungs below as points in that matrix, not a total
> order.

- **Storage:** git = the code that generates and governs; a database = the corpus + lineage/remix/metadata as
  queryable rows; object storage = bulk payloads (with a retrievability guarantee + subtree addressing, so one
  opaque tree digest never blocks partial reuse). Millions of primitives are rows, not files.
- **Delivery:** a matrix over *retrieve-by-reference · retrieve-source · import · vendor · deterministic
  compose · WASI · container/RPC · deploy* — each a different coupling/isolation/latency/cost trade. MCP is
  retrieval; PyPI-style import, file-copy vendoring, and service/deploy are distinct points chosen per
  situation (autonomy, security, latency, licensing, observability).
- The two connect: retrieval (MCP) hands you the *reference*; the import/vendor/deploy rungs are how that
  reference becomes *running code*, and the deployment profiler tells you what each rung costs to run.

*Everything here is governed: retrieval returns candidates (`serves_truth=false`) until promotion; a copied or
imported primitive carries its proof status and lineage with it.*
