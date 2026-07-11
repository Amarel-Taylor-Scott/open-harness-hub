# Read the Edges, Not the Code

**Edge-first composition: how AI coding agents can do the same work with orders of magnitude less context**

> **⚠ STATUS 2026-07-09 (DRAFT — do not publish as-is).** The "read only the edges → identical output / 486×" claim is
> a CONTEXT-BYTE reduction measurement, not proven end-to-end token savings, and it is PROMPT/MODEL-dependent: the
> 2026-07-09 executed experiments found signatures/edges-only presentation often makes models RE-IMPLEMENT and FAIL,
> whereas full tested source + "use as-is" works better. Keep as a structural-measurement draft; reconcile against
> `../HANDOFF-GPT-5.6.md` before any external use.

*AI Done Right · AIDevObserver — whitepaper DRAFT v0.95, 2026-07-01. Status: evidence reconciled against a
111-agent adversarial verification pass (3-vote refutation per claim). Every number carries its measurement
basis and review status; two motivational narratives (sustainability figures; pre-LLM component-economy
history) produced ZERO surviving verified claims and are explicitly held out of the argument until dedicated
research passes ground them. Every generated artifact in our system is candidate-only until it passes a
proof gate.*

---

## Abstract

When a human senior engineer uses a library, they read its interface: what goes in, what comes out, what it
promises. When today's AI coding agents use a library, they routinely read the *implementation* — whole
packages, full documentation pages, thousands of lines of code — because nothing in their environment tells
them the interface is enough. We show that for a large class of programming work, an agent that reads only
**edge contracts** (typed input/output summaries of black-box components) and orders those components into a
runnable graph produces **identical output** to an agent-style pass over full implementations, at a context
cost **hundreds of times smaller**. In our first controlled measurement, full-implementation context of
617,791 bytes collapsed to 1,270 bytes of edge cards — a **486x reduction** — with byte-identical results
verified by canonical output hashing. We describe the architecture that makes this workable where forty years
of component-reuse attempts failed, the benchmark program that will test it adversarially, and the honest
limits of the approach.

## 1. The problem: agents buy context they don't need

An AI coding agent asked to "import this CSV, validate it, dedupe it, and load it" will typically open the
CSV helper, read it, open the validation module, read it, scan the models file, read the docs page — spending
tens or hundreds of thousands of tokens acquiring knowledge it uses only to conclude *how to call three
functions*. The tokens are paid again next session, by every developer, on every team, forever. The same
pattern applies beyond code: agents re-read workflow definitions, ticket histories, and infrastructure
configs when a contract-level summary would carry the decision.

Three costs compound:

- **Model context** — implementation text crowds out task-relevant context and degrades attention.
- **Money and latency** — context tokens dominate agent bills; re-reads are pure waste.
- **Energy and water** — at industry scale, redundant context is redundant inference. We deliberately defer
  quantified sustainability claims to the evidence section below; the direction is not controversial, the
  magnitude deserves citations.

**The verified evidence** *(adversarial 3-vote verification, 2026-07-01; review status labeled per row)*:

| Signal | Finding | Status |
|---|---|---|
| Reading dominates agent spend | File-read operations consume **67.5–76.1% of all agent tokens** on SWE-bench Verified; input tokens, not output, drive agentic coding cost (the 76.1% figure comes from one bash-only scaffold — our cross-scaffold replication is queued) | 2026 preprints; replication planned |
| Most of it is waste | **23–82% of agent context can be pruned or compressed with no performance loss**; verified compression magnitudes run 5.6x–24x (LongCodeZip, ASE 2025; SWE-Pruner preprint) | peer-reviewed + preprint |
| Interface-only works for location | 12 frontier models locate issues at **94.5–97.3% success from a name-only skeleton at 18–24:1 compression** (location only, vendor preprint — our executed-fix replication is the upgrade) | single-vendor preprint; replication planned |
| Edges-over-implementations works end-to-end in one domain | **ComfyGPT wires 6,362 registered black-box nodes into runnable graphs from I/O type specifications alone**; LLM-assembles-graphs is established research (AFlow, WorfBench — ICLR 2025) | peer-reviewed |
| The philosophy is already shipping piecemeal | Aider's tree-sitter repo map is explicitly signature-only ("the LLM doesn't need to see the entire implementation"); Serena's LSP symbol tools are the closest adopted on-demand form | shipping OSS |
| Adoption/trust backdrop | 84% adoption, 51% daily use, 29% trust (Stack Overflow 2025); METR RCT: 19% *slower* on familiar repos | reported; not independently re-verified by our pass |

Honesty about magnitude: externally verified end-to-end savings are **one order of magnitude** (5.6x–24x),
not "orders of magnitude." Our own 486x figure measures something narrower and structural — agent-context
*bytes for route assembly* on a composition task at output equivalence — and the two must never be
conflated. Regime-dependence is also verified in both directions: LSP-style symbol tools ran ~4x costlier
for simple read-only exploration, and compression degrades on deep issue-resolution work — which is exactly
why our benchmark splits favorable and adverse regimes.

The research field is converging on "agent quality depends on context retrieval" — but it still retrieves
**snippets, files, docs, issues**. The gap this paper names is one level higher: retrieve **capability
records and composition routes**. In the surveyed set, no system combines a typed-contract registry,
tool-call contract search, deterministic receipted execution, and session-review reuse coaching —
**receipts/proofs and reuse coaching are entirely unoccupied**. The whitespace is the combination.

## 2. Why component reuse failed before, and what changed

Reusable software components are one of the oldest dreams in the field (McIlroy proposed a components
subindustry in 1968). Component economies kept failing at the same four bottlenecks: **discovery** (you
can't reuse what you can't find), **fit** (the component is almost right), **adaptation** (the glue between
components is the real work), and **trust** (nobody debugs a black box they didn't choose). Where those four
were bounded by the platform — Canva's canvas, n8n's workflow nodes, spreadsheets, LabVIEW — primitive
composition won decisively. General programming never got a bounded world.

The idea itself is software engineering's oldest good idea. Parnas's *information hiding* (1972) said
modules should hide implementation decisions behind stable interfaces; Meyer's *Design by Contract* made
the interface a checkable promise — preconditions, postconditions, effects, error behavior. Edge cards are
design-by-contract turned into a retrieval substrate. And plan-then-execute systems (Gorilla's
retrieval-grounded API calling, LLMCompiler's planner/executor split, LLM+P's formal-planner handoff,
"Compiled AI" deterministic post-compilation execution) have already shown that separating LLM planning
from deterministic execution beats agent loops in bounded settings.

What changed is not a better catalog format. It is that **an LLM with tool calls is a compiler of intent**:
it can map "import this CSV and dedupe it" onto a registry query, compare typed edges, select components,
and emit an ordered graph — the discovery and fit bottlenecks — while **deterministic machinery** handles
adaptation and trust: contract validation, adapter insertion, execution, and receipts. The LLM proposes;
the runtime proves. Neither alone was ever enough.

### Why hasn't someone already done this?

Because none of the hard parts is the search index. Multi-column hybrid retrieval over typed cards is
commodity engineering; what killed every prior component economy is what happens *after* retrieval — and a
market-structure quirk keeps today's incumbents from caring:

1. **Semantic types, not type labels.** Two teams' `CustomerRecord` are different shapes. Every universal
   vocabulary attempt (CORBA IDL, WSDL/UDDI, schema.org) hit ontology fragmentation. The new mitigations:
   LLMs judge semantic compatibility cheaply (the fuzzy matcher that never existed), and contracts travel
   with examples + fixtures so a dry-run catches label lies before execution does.
2. **Cards lie.** Signatures extract deterministically; *effects* (side effects, state paths, error
   behavior) are not statically decidable in dynamic languages. A wrong effects field composes a graph that
   corrupts data. Answer: cards stay candidate until proofs pass, and runtime receipts feed *observed*
   behavior back into the card — the registry converges on reality instead of trusting extraction.
3. **Cold-start economics.** The value appears only after tens of thousands of quality cards + templates +
   the mutation layer exist together; each alone is unrewarding. Code-tool vendors took the immediately
   monetizable path (better retrieval over raw code) instead of owning a registry.
4. **Incentive inversion.** Agent vendors bill per token — the sellers of AI coding have weak incentives
   to cut context consumption 100x. Context efficiency is structurally the *customer's* problem, which is
   why the reuse-and-routing layer is naturally a third-party product, not a feature the incumbents ship.
5. **The escape-hatch cliff.** Low-code dies at the first task it can't express. Here primitives live in
   normal codebases, source escalation is native and counted, and the novel 20% an agent must still write
   enters the registry as tomorrow's candidate primitive instead of leaving the paradigm.

## 3. The architecture of edge-first composition

The unit is a **primitive**: a small, typed, black-box capability with a visible contract.

```json
{
  "label": "primitives.groups.normalize_field_name",
  "contract": {"input": "RawFieldLabel", "output": "SnakeCaseAsciiFieldName"},
  "blackbox": "Normalize an external field label to snake_case ASCII.",
  "effects": [], "runtime_targets": ["local.python"],
  "candidate": true, "serves_truth": false
}
```

A primitive can be a function, an API endpoint, a queue worker, a cron job, a workflow step, a Kubernetes
job, a dashboard — the **contract is the primitive; the runtime shape is how it's exposed**. Groups hide
member edges behind one visible edge (a whole billing-reconciliation service can be one card), with
drill-down on demand.

The pipeline an agent actually runs:

1. **Search** — hybrid retrieval over edge cards: lexical token match, typed edge match
   (`requested_input → requested_output`), vector similarity (fuzzy embedding compatibility for
   near-synonym edges), and graph adjacency (what usually composes with what). At scale, **blocking** does
   the heavy lifting — hash/tag/type-family blocks prune millions of candidate pairs to hundreds before
   any fine-grained compatibility check runs, the same discipline entity resolution uses. **Templates rank
   above primitives** in retrieval: a known-good chain (`discover → fetch → extract → validate → emit`)
   answers in one hit what dozens of card lookups approximate. The agent's query costs a tool call, not a
   file read.
2. **Ordering** — candidate components are ordered into a data-flow graph by edge compatibility. The
   model's answer is not code: it is a **few-token route plan** (template choice, slot bindings, requested
   mutations, declared gaps — JSON on the order of hundreds of tokens). A deterministic verifier checks the
   graph is acyclic, type-sound, and satisfiable, dry-runs it on synthetic typed data, and deterministic
   wiring does the rest — before anything real executes.
3. **Deterministic adjustment** — when edges almost fit, registered **mutation operators** adapt them
   without touching internals: scalar→sequence lifting, field renames, output wrappers, schema-validator
   insertion, retry/idempotency/cache wrappers, runtime-shape wrappers (function→endpoint→worker→job). Each
   mutation carries preconditions and proof obligations. This is the glue-code layer, made explicit,
   reusable, and verified. When a mutation must touch a primitive's own surface (rename an input, reshape
   an output schema), **globally-unique object naming makes the surgery text-precise**: every definition's
   name is unique across the codebase, so a deterministic codemod can retarget every reference by exact
   string match — no AST ambiguity, no missed call sites. The naming discipline is not cosmetics; it is
   the enabling infrastructure for mechanical primitive editing at scale.
4. **Execution with receipts** — the graph runs under a runtime that emits a per-node receipt: cost,
   duration, inputs digest, output digest. Composability is paid for in receipts, not in trust.
5. **Troubleshooting** — when a run fails, the receipt names the node; drill-down opens that node's hidden
   member edges, then — only if needed — its source. The escape hatch to code is always there; it is simply
   no longer the default. Black boxes are debuggable because every box logs its boundary.
6. **Evolution ("genetic" mutation) and repair** — primitives are not static. When nothing fits out of the
   box, the ladder escalates: deterministic remixers first; then a tiered **repair agent** (light → heavy →
   SOTA model) makes the *smallest* adjustment that closes the gap — and the result is never a throwaway
   patch: it enters the registry as a NEW candidate primitive with full lineage to its parent. Variation
   operators generate competing variants (mutation stacks, cheaper substitutions, batched shapes); variants
   compete on proofs and receipts; winners earn promotion review, losers are kept as negative memory,
   never deleted. Selection pressure is measured lift, not model opinion.
7. **Promotion boundary** — everything generated is `candidate=true, serves_truth=false` until a proof gate
   passes: fixture tests, contract tests, side-effect audits, and human review where risk warrants. A model
   can propose a primitive; only evidence promotes one.

Two doctrines govern the pipeline itself. **Compatibility is routed, not declared**: the registry stores
routes (`A reaches slot B via map_sequence, with these proof obligations, with this receipt history`)
rather than static booleans — the system learns and proves paths instead of trusting an ontology. And
**the pipeline measures itself**: each stage (search, mutation, linking, model preprocessing) is a
cost-ordered ladder with receipts; the system continuously descends to the cheapest path that still passes,
keeps backup paths warm, and — when stakes or ambiguity warrant — runs two or three paths at once and
checks agreement before proceeding. Efficiency is not a configuration; it is a measured, monitored,
self-correcting property.

### The context-tier ladder

Context, like compute, is spent at the cheapest sufficient tier. An agent escalates only with a named
reason:

| Tier | Content | Typical spend |
|---|---|---|
| 0 | alias only | a few tokens |
| 1 | signature | ~10s of tokens |
| 2 | **compact primitive card** (contract + blackbox + effects) | ~100 tokens |
| 3 | evidence/proof view (fixtures, receipts, known-good chains) | ~100s |
| 4 | canonical registry record | ~1k |
| 5 | source snippet | ~1k–10k |
| 6 | full source | 10k+ |

Most route assembly happens at Tiers 2–3. Tiers 5–6 are reserved for five legitimate escalations:
modifying the primitive itself, debugging a failed proof, auditing security-sensitive behavior, extracting
missing metadata, or resolving a contradiction between contract and observed behavior. **Interface first;
source only on escalation** — and every escalation is counted, because escalation rate is the honest
measure of whether the cards are good enough.

### The compute-tier ladder

Every stage runs at the cheapest sufficient tier, and descends over time:

| Tier | Used for | Examples |
|---|---|---|
| **Deterministic** (default) | edge matching, graph validation, mutation application, execution, receipts, dedupe, digests | the entire hot path |
| **Light models** | query expansion, candidate rerank, card summarization, triage | small local/batch models |
| **Heavy models** | route synthesis when no template fits, contract drafting from messy sources | mid-tier coding models |
| **SOTA models** | novel decomposition, adjudicating conflicting contracts, reviewing promotion evidence | frontier models, sparingly |

The system's economics improve monotonically: every route that succeeds twice becomes a template; every
template hardens toward the deterministic tier; SOTA spend concentrates on the genuinely novel.

## 4. Beyond code: the same shape everywhere

The contract-not-implementation insight is not code-specific. The identical machinery covers:

- **Workflow automation** — nodes already are primitives; edge-first search chooses them.
- **Data engineering** — extract/normalize/validate/load routes with provenance receipts.
- **Project management** — tickets and plans as typed edges (`BugReport → TriagedTicket`,
  `Epic → OrderedTaskGraph`); an agent plans by composing summaries, not re-reading histories.
- **Infrastructure** — modules with typed variables/outputs are contract-first by construction.
- **Media and documents** — extraction cascades, rendering pipelines, review gates.

Industries follow from runtime shapes, not from new architecture: the same registry discipline serves
fintech reconciliation, healthcare-administration directories, procurement-opportunity ingestion, and
e-commerce integration — domains where auditability (receipts, provenance, promotion) is the buying reason,
not an afterthought.

**Filling the universe.** The registry grows by *decomposition*, not hand-authoring: ingestion foundries
break projects, packages, websites, workflow exports, process documents, and textbooks into candidate
primitives and — more importantly — into candidate **templates**, the recurring chains those artifacts
embody. Every ingested candidate arrives with a source handle, a compatibility contract, and
`candidate/serves_truth=false` stamps; the promotion gate, not the ingester, decides what agents ever see.
Our foundries have produced 70k+ edge-level candidates from first-party sources alone; the architecture is
source-family-agnostic by construction.

## 5. First measurements — and their honest limits

Our internal Benchmark Lab ran the first controlled A/B (2026-07-01): the same
normalize/validate/dedupe/digest task over 20,000 records, executed twice in isolated subprocesses —

| Measure (basis labeled) | Run A: rebuild from full source | Run B: compose primitives by edges |
|---|---|---|
| Agent context (simulated read) | 617,791 B | **1,270 B (486x less)** |
| Tokens (deterministic proxy, chars/4) | ~154,447 | **~317** |
| Output (canonical hash) | identical | identical (6,666 records) |
| Peak process memory | 59.3 MB | 67.3 MB (+8 MB receipt/runtime tax) |
| Wall time | 1.18 s | 1.78 s |

Read the last two rows as carefully as the first two: the graph runtime **costs** machine memory and time at
this scale — receipts and composability are not free. The claim we defend is precise: **agent-side context
and tokens collapse by orders of magnitude at equivalence of output**, while machine-side overhead stays
modest and fixed. This v0 is deterministic-arm-only, single task family, with context measured as simulated
agent reads; the benchmark plan below scales it to live model arms, 10,000-task corpora, and adversarial
grading before we publish headline numbers.

## 6. The benchmark program

The companion document (`docs/benchmarks/edge-first-composition-benchmark-plan.md`) specifies the full
program: baseline-vs-primitive-first arms across model tiers, a resource envelope covering tokens, context
bytes, machine memory, CPU/wall, and model calls (every estimate basis-labeled), runtime-shape reuse tests,
mutation tournaments, troubleshooting drills, and negative controls. Everything ships candidate-only with
receipts; a winning scorecard is promotion *evidence*, never automatic promotion.

## 7. What could still kill this (we test these, not hide them)

None of these is a research wall; each is an engineering budget with a named mechanism — and a metric that
tells us if the budget is blowing up:

- **Contract drift** — an edge card that lies is worse than no card. Mitigation: cards are generated from
  source, hashed against it, and re-verified on change; *effects* are never merely asserted — primitives
  run in an observed sandbox and the card records what the code actually did. Drift fails a gate, not a
  user.
- **Dynamic typing and long-tail semantics** — many real contracts are informal, and two teams'
  `CustomerRecord` differ. Mitigation: don't force one universal ontology — let primitives **multiply into
  proven variants** (children/sibling remixes per schema shape, each with fixtures), and let selection
  prune. The residual cost is index hygiene: variant explosion is managed by blocking, canonical-hash
  dedupe, and receipt-weighted ranking (used-and-proven variants rise; losers sink into lineage). The
  metric that guards it: retrieval precision at growing registry size (benchmark phase P1).
- **Contract-fit vs intent-fit** — the honest boundary of the checklist: everything a contract *states* is
  mechanically checkable (schema match, edge match, dry-run, observed effects), but two type-identical
  routes can differ in intent (keep-first vs keep-last dedupe both type-check). Fixtures encode intent —
  which is why the proof library, not the card count, is the compounding asset — and human
  accept/reuse/dismiss triage covers the remainder.
- **Debugging trust** — developers reject what they can't inspect. Mitigation: per-node receipts,
  drill-down member edges, and source on demand. Trust is earned by observability, not asserted.
- **The CodeAct result (the strongest verified counterargument)** — ICML 2024 showed free-form *code
  actions* beating constrained tool-schema composition by up to 20%: fixed contracts limit composition.
  Our answer is structural, not rhetorical: the graph formalism **escape-hatches into code** — an agent may
  always write free code where composition falls short, that code is itself a primitive shape, and it
  enters the registry with lineage. Contract-first and code-first are rungs on one ladder, selected by
  receipts, not ideology. If the escape-hatch rate stays high on composition-dominant tasks, the thesis is
  wrong — and the benchmark measures exactly that.
- **Novelty tail** — genuinely new algorithms have no primitive. Mitigation: the ladder — SOTA models write
  the novel 5%, and their output enters the registry as tomorrow's candidate primitive.
- **The catalog-quality trap** — a registry of junk cards recreates the UDDI failure. Mitigation: the
  promotion boundary, measured-lift admission, and negative memory from dismissed suggestions.

## 8. Conclusion

Component reuse never lacked components; it lacked a compiler of intent and a trust machine. LLM tool-calling
supplies the first, deterministic contracts/receipts/proofs supply the second, and the context economics —
hundreds-fold reductions at output equivalence — supply the reason to move now. Agents should read the edges,
not the code. The code should still be there when they need it — as the exception that proves the rule.

---

*Evidence appendix (external citations from the adversarially-verified research pass) and reproduction
instructions accompany the final v1.0. All benchmark receipts are published with basis labels;
`candidate=true / serves_truth=false` until independently reproduced.*
