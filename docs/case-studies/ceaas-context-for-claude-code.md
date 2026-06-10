# Case study: serving this repo's context to Claude Code (Baltor dogfood)

**Subject:** Open Harness Hub's own documentation and governed corpora.
**Consumer:** the Claude Code (and MCP-client) agents that build this very repo — including the
subagent that wrote this file.
**Service:** Baltor ([[../strategy/context-enrichment-service.md]]) — the
content/corpus refinery, not the pipeline builder.

This is the cleanest dogfood we have: the platform that compresses and governs context for *other*
people's agents has, sitting inside it, a large doc tree that its *own* agents already struggle to
carry. If Baltor works, the first beneficiary is us.

> **Honest framing up front.** This case study describes a *target* delivery, not a shipped metering
> dashboard. What is built today: the governed component **definitions** for every tier and surface
> below (six catalog entries, confirmed on disk). What is planned: the tier *pipeline*, the four
> *emitters*, the MCP *serving endpoint*, and the fidelity *meter* — the `enrichment` service is
> `status: planned` in [`services/registry.yaml`](../../services/registry.yaml). Numbers describing the
> repo are computed below; nothing here invents a fidelity or token figure for the pipeline. See
> [Status](#status-built-vs-planned).

---

## 1. The problem (measured, on our own tree)

An agent opening this repo cannot read it. The documentation tree alone is large:

| Surface | Count (computed `2026-05-29`) |
|---|---|
| Markdown files under `docs/` | 4,553 |
| Words under `docs/` | ~1.28M |

That excludes the catalog YAMLs, the `scripts/` libraries, the seed modules, and the research notes.
No context window holds it, and feeding even a fraction raw is the failure mode every
context-engineering guide warns about: you bury the desk and the model's reasoning degrades
([[../concepts/context-layer-and-the-desk.md]] — the analyst's desk is small and easily buried).

Today the agents working this repo cope the way every Claude Code user copes: a hand-maintained
`CLAUDE.md`, ad-hoc `grep`/`Read` loops, and a CodeGraph index for structural queries. That works, but
it is exactly the *scattered, single-shot, local, ungoverned* state Baltor exists to replace
([[../strategy/context-enrichment-service.md]] — "the tooling exists... but only as scattered,
single-shot, local CLIs"). It has no provenance trail, no freshness contract, no measured guarantee
that the compressed view preserved what the agent needed, and no reuse: every agent rebuilds the same
view of the same tree.

## 2. The Baltor move: render the tree into tiers, serve the tiers

Baltor treats this repo's docs + corpora as **one governed corpus** and renders it into the three
token-efficiency tiers — each a *different mechanism*, which is why they are separate SKUs
([[../strategy/context-enrichment-service.md]]):

| Tier | Mechanism (shared-backend component) | What the agent gets |
|---|---|---|
| **Raw** | object store + source registry + connectors | full fidelity; the source of truth, freezable as an export |
| **Compressed — structural** | `compress.structural` ([`structural-compress`](../../catalog/processors/compression/structural-compress.yaml)) | bodies stripped, signatures + structure kept (~70% on code, structure-lossless) |
| **Compressed — learned** | `summarize.llmlingua` (LLMLingua-2) | token-classification compression of prose (general 5–20×) |
| **Hyper-efficient** | `memory/*` distilled facts + `cache/*` cache-shaping | extracted conventions/glossary packaged onto a **cacheable prefix** so the provider cache (~90% off input at a high hit rate) carries the recurring cost |

The hyper-efficient tier is where value compounds for an agent that opens this repo dozens of times a
day: the distilled "what an OHH contributor must know" is a near-static prefix, so after the first
load it is almost free. That is the same logic the desk explainer calls *swap* in the OS-memory
hierarchy ([[../concepts/context-layer-and-the-desk.md]]) — keep the cheap-to-resident pages on the
desk, pay the expensive model call only once.

## 3. The four surfaces — meet our agents where they ingest

Baltor's output "isn't an answer — it's a governed corpus rendered into whichever of [the] four shapes
the user's agent consumes" ([[../strategy/context-enrichment-service.md]]). For Claude Code working
*this* repo, all four map to a real ingestion path, and each is a seeded component:

1. **MCP server** — [`serve-mcp-corpus`](../../catalog/processors/deliver/serve-mcp-corpus.yaml)
   (`deliver.mcp_serve`). The default surface. The agent gets a live, tier-negotiated, CDC-fresh,
   cited handle on the docs + corpora instead of carrying the tree. This is the same convergence point
   the repo's own CodeGraph MCP server already proves valuable for *structural* queries; Baltor is the
   *content/corpus* analogue — "where is the lift bar defined and what does it actually say, cited."
2. **Packed file / llms.txt** —
   [`emit-llms-txt`](../../catalog/processors/deliver/emit-llms-txt.yaml) (`deliver.llms_txt`). Download
   or paste the compressed tier into any agent, no integration. The freezable surface — works on any
   subscription. (There is no `llms.txt` checked into the repo today; this is the planned emitter, not
   a shipped file.)
3. **Claude Code skill / plugin** —
   [`package-agent-skill`](../../catalog/processors/deliver/package-agent-skill.yaml)
   (`deliver.skill_package`). The corpus + its tools distributed as one installable, versioned,
   governed unit — the same shape the repo's existing skills (`/goal`, `/evolve`, `/polish`) take.
4. **CLAUDE.md fragment** —
   [`emit-claudemd-fragment`](../../catalog/processors/deliver/emit-claudemd-fragment.yaml)
   (`deliver.claudemd`). The distilled, always-loaded, near-zero-token tier for the stable knowledge
   that **must survive compaction**: the canonical vocabulary (Knowledge Corpus / Conditional /
   Action), the no-magic-values rule, the two-axis lift gate, the promotion boundary. This repo's
   `CLAUDE.md` is hand-maintained today; the CLAUDE.md fragment is the generated, governed, freshness-
   tracked version of exactly that file — and it is the surface this case study most directly improves.

The same governed corpus, four shapes, one provenance trail — the "one object, two doors" join applied
to a single product's internal use ([[../strategy/two-services-shared-infrastructure.md]]).

## 4. The guarantee: measured fidelity per tier (why an agent can trust the compressed view)

Compression is only safe if you can prove the tier preserved enough; over-compression "destroy[s] the
model's ability to reason" ([[../strategy/context-enrichment-service.md]]). So every tier we serve our
own agents ships a **published quality delta**, scored by a *separate* evaluator —
[`compression-fidelity-check`](../../catalog/processors/verify/compression-fidelity-check.yaml)
(`verify.compression_fidelity`), never self-graded.

This matters acutely for the dogfood: the compressed CLAUDE.md fragment must not silently drop, say,
the promotion-boundary rule or the "Conditional not rule-pack" vocabulary. The fidelity check is what
turns "we compressed your conventions" into a contract — and it is the **same measurement engine and
the same moat as OHH's capability-lift gate** ([[../design/value-propositions.md]] — "measured, never
asserted"), extended from "does the pipeline lift?" to "did the tier preserve?". An agent consuming a
Baltor tier reads a fidelity score the way an OHH builder reads a `▲ +Δ` lift number: governance, not a
vendor claim.

## 5. Why governance is the point even for our own agents

This repo's own rules say a doc must carry a warrant, a fact must carry provenance, and a volatile fact
must carry CDC/freshness ([[../codex/change-verification-contract.md]]). A raw `grep` of the tree gives
an agent text with none of that. Baltor serves the *governed* corpus: each served slice keeps its
source link, its lifecycle, and — for the live/hyper-efficient tier — a freshness contract, so an agent
acting on "the lift bar is two-axis" can cite `scripts/eval/reason_codes.py` as the single source
rather than paraphrasing from memory. That provenance trail is the external moat
([[../design/value-propositions.md]]); here it is also the thing that keeps an autonomous build loop
from acting on a stale or hallucinated convention.

## 6. The pricing line (consistent with the rest of the product)

Pricing falls out of freezable-vs-recurring ([[../strategy/context-enrichment-service.md]]):

- **Raw + compressed** tiers are downloadable → **freezable**: a static `llms.txt` or skill bundle of
  the docs is yours forever (one-time / storage-priced).
- **Hyper-efficient, live-served and kept fresh** against this constantly-changing repo →
  **recurring**, because a static download *cannot stay current* with a tree that changes every commit.
  The CDC/freshness obligation is the recurring-revenue moat.

For the dogfood specifically, the live MCP surface is the recurring one: the repo changes daily, so a
frozen `llms.txt` goes stale, while the served corpus tracks `main`.

## 7. Built on the shared backend (no fork)

Baltor adds no new engine for this — it is a surface + a meter + the four emitters over the same
substrate OHH already runs ([[../strategy/two-services-shared-infrastructure.md]]): the
compression/memory/cache components, the governed corpora, the connectors, the lift/fidelity harness,
the vector store, the workers. The `enrichment` async service in
[`services/registry.yaml`](../../services/registry.yaml) already declares ownership of
`scripts/processors/{compression,memory,cache,retrieval}` and `calls: [measurement]` — i.e. it reuses
OHH's measurement service to score fidelity. A better compressor or a fresher corpus shipped for OHH is
instantly a better Baltor tier for our agents.

## Status (built vs planned)

Honest, and consistent with the spec's own status section
([[../strategy/context-enrichment-service.md]]) and [`services/registry.yaml`](../../services/registry.yaml):

**Built (governed component definitions, confirmed on disk `2026-05-29`):**

- `processor/structural-compress` — `catalog/processors/compression/structural-compress.yaml`
- `processor/serve-mcp-corpus` — `catalog/processors/deliver/serve-mcp-corpus.yaml`
- `processor/emit-llms-txt` — `catalog/processors/deliver/emit-llms-txt.yaml`
- `processor/package-agent-skill` — `catalog/processors/deliver/package-agent-skill.yaml`
- `processor/emit-claudemd-fragment` — `catalog/processors/deliver/emit-claudemd-fragment.yaml`
- `processor/compression-fidelity-check` — `catalog/processors/verify/compression-fidelity-check.yaml`

(Seeded by `scripts/seed/baltor_components.py`; lifecycle `experimental`.)

**Planned (no entrypoint yet — boundary defined, code path declared in `services/registry.yaml`):**

- the tier *pipeline* (raw → compressed → hyper-efficient) on the shared workers — the
  `enrichment` service is `status: planned`;
- the four *emitter implementations* — the YAMLs above point to
  `scripts.processors.deliver.*` / `scripts.processors.compression.*` paths that do **not** exist on
  disk yet;
- the MCP *serving endpoint* that drops the governed corpus into a Claude Code session;
- the token-efficiency + *fidelity meter* that publishes the per-tier quality delta.

No tier-fidelity number, token-savings ratio, or cache hit rate for *this* corpus is reported here,
because none has been measured — the meter is planned. When it ships, the figures it produces (e.g.
`token_savings_ratio`, `fidelity_delta`) are `dimension-record` attributes both services read, never a
per-service column ([[../codex/schema-extensibility.md]]).

---

**WARRANT.** User intent — the owner asked for "full docs + dogfood + use cases/case studies," and for
Baltor positioning tied to the four consumption surfaces and the measured-fidelity guarantee; this is
that dogfood case study. Corroboration — the Baltor spec
([[../strategy/context-enrichment-service.md]]), the two-services decision record
([[../strategy/two-services-shared-infrastructure.md]]),
[`services/registry.yaml`](../../services/registry.yaml), and the seeded catalog YAMLs all agree on the
tiers, the four surfaces, the fidelity moat, and the `planned` status. Established principle —
honest built-vs-planned reporting and warranted claims ([[../codex/change-verification-contract.md]]),
canonical vocabulary and measured-not-asserted lift ([[../design/value-propositions.md]]). Repo-fact
claims (4,553 files, ~1.28M words) are computed, not invented; pipeline fidelity/token figures are
explicitly withheld as unmeasured.
