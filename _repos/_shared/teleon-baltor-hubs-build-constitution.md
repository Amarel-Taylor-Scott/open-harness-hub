# TELEON + BALTOR + OPEN HUBS + OBSERVER

## Master Build Constitution — Universal Computational Intelligence Infrastructure

**Version:** 1.0 · **Updated:** 2026-06-24 · **Status:** canonical build directive

> Feed this file to any coding agent (Claude Code / Anthropic API, Cursor, OpenAI Platform agents, internal
> builders) before it touches this repository. It is a **constitution**, not a feature list: it sets the mission,
> the four systems, the universal interfaces, the non-negotiable laws, and the bar for "done." It exists to force
> **build-out discipline** — real infrastructure over toys, honest candidates over fake placeholders, and
> continuous expansion of the real architecture that already exists in this repo rather than a parallel reinvention
> beside it.
>
> **This prompt is grounded, not generic.** Every system below names the real modules it extends. Building a
> "clean" parallel version instead of extending these is itself the #1 anti-pattern this system was built to detect
> (see *Observer / Spotter*). Extend what exists.

---

## 0. How to use this document

1. **Read the law before you write.** The hard constraints in §11 are enforced by `scripts/run_proofs.py`
   (the proof gate) and by named `check_*` scripts. Green is necessary, never sufficient — every change also
   carries a **warrant** (§11).
2. **The canonical references this prompt compresses** (read when a section is load-bearing for your task):
   `docs/strategy/teleon-baltor-openhubforai-portfolio.md` (portfolio architecture),
   `docs/strategy/teleon-naming-and-domain.md` (brand/naming law),
   `docs/strategy/north-stars.md` + `docs/concepts/capability-valleys.md` (what to build for),
   `docs/codex/no-magic-values.md`, `docs/codex/lossless-distillation.md`,
   `docs/codex/change-verification-contract.md` (the codified laws),
   `prompts/teleon-build-kit.md` (Teleon control-plane greenfield kit),
   `architecture/portfolio_dependency_law.json` (the dependency invariant).
3. **When this prompt and a code-enforced law disagree, the law wins** — and you fix the contradiction in the same
   change (no orphaned contradictions). When this prompt and your instinct to "simplify by rebuilding" disagree,
   this prompt wins.

---

## 1. Core directive

You are not building an agent framework. You are not building workflow automation. You are not building prompt
tooling. You are building the **foundational infrastructure layer for universal machine-executable computation**.

> **Mission:** Build a universal computational compiler that turns ambiguous human-or-agent intent into globally
> optimized, **verified** execution graphs over all machine-executable capability that exists — and that
> continuously **removes intelligence** from those graphs as cheaper, deterministic, more reliable paths are found.

The forever-question every layer asks: **Can intelligence be removed?**

The system is one holding architecture (**AI Done Right**, `aidoneright.dev`, "AI, done right.") over four
tightly-integrated macro-systems. Two answer different questions and must never be collapsed:

- **Teleon answers:** *How should the machine do the thing?* (efficiency, compilation, optimization)
- **Baltor answers:** *Did the machine do the correct thing?* (truth, verification, governance)

---

## 2. The four systems (extend these — do not reinvent them)

### SYSTEM 1 — TELEON · the universal compiler & runtime
`teleon.dev` · the purpose-driven, eval-gated, self-adaptive **compute runtime SaaS**.

Teleon accepts ambiguous intent, compiles it into an executable graph, searches globally across known capability,
builds a working brute-force solution **immediately**, then descends: observes waste → measures it → substitutes
deterministic computation → routes to the cheapest *sufficient and reliable* model → caches → parallelizes →
benchmarks alternatives → permanently records the better path. **Intelligence should continuously disappear**; if a
workflow can eventually avoid an LLM entirely, the compiler must force that transition.

- Object: **PurposeTask** (formal/spec synonym **CapabilityTask**). Staff plane: **Teleon Control Tower**.
  Customer plane: **Capability Assurance Portal**.
- Real homes already in-repo: `_repos/teleon/backend/src/teleon/synthesis/` (intent→DAG, synthesis tree with backtracking),
  `_repos/teleon/backend/src/teleon/economics/` (live cost model, routing, simulator), `_repos/teleon/backend/src/teleon/inference/` (model lanes/ports),
  `_repos/teleon/backend/src/teleon/components/` (uniform `Component.invoke`, `lower_to_dag`, `verify_buildable_dag`),
  `architecture/capability_ladders.json` (cost-ordered deterministic-first descent ladders).

### SYSTEM 2 — BALTOR · the truth, governance & verification product
`baltor.ai` · the applied, customer-facing **context product**, powered by Teleon (a tenant of the runtime).

Baltor is everything that asks *did the machine do the correct thing?* — AI auditing, execution verification,
benchmarking, hallucination detection, security/vulnerability scanning, regression and adversarial testing, schema
and API-contract validation, magic-number auditing, reproducibility & trust scoring, compliance, observability,
red-team, model comparison, deterministic verification. **Never trust a model output automatically. Everything is
validated.** Baltor's `serves_truth=true` outputs are the few that have passed the gates; everything else is a
candidate.

- This is the deliberately **under-built moat** — the Verification universe is where the durable advantage is. Bias
  new effort here. Real homes: `_repos/baltor/backend/src/baltor/` (being incrementally extracted to `_repos/teleon/backend/src/teleon/` for generic runtime
  pieces — lossless; see `architecture/portfolio_dependency_law.json` → `migration_status`), the proof gate
  `scripts/run_proofs.py`, and the `check_*` family.

### SYSTEM 3 — OPEN HUB FEDERATION · the machine's world model
The **OpenHubForAI** ecosystem + the open **CapabilityTask spec (CTS)**. A machine-readable global registry
layer where, eventually, **every executable capability in existence is represented**. This is the machine's world
model and the open funnel.

- Real homes: `architecture/registry_ontology.json` (the federation index — a registry-of-registries),
  `_repos/teleon/backend/src/teleon/registry/port.py` (the universal menu: `list/lookup/search/explain`),
  `architecture/hub_profiles.json` (the OpenHubForAI surfaces). **Counts are computed** by
  `scripts/check_ai_done_right_surface_family.py` — never hand-type the number of hubs or registries.

### SYSTEM 4 — OBSERVER / SPOTTER · the coding-session review, supervisor & assistant
The AI-usage review & **real-time intervention** surface — it watches how humans and agents actually use AI and
challenges waste *before* it happens. It is Baltor's verification ethos and Teleon's "remove intelligence" descent,
applied to the **act of building with AI**: the supervisor that says "you're reinventing OAuth — `authlib` exists,"
"there's an official API, don't scrape," "check the embedded text layer before OCR."

- Real homes: `_repos/teleon/backend/src/teleon/observer/{router,capture,review,session_store}.py` (one router over a typed intervention
  taxonomy + a global interruption budget + graduated modes; `capture.py` ingests Claude Code / Cursor / Codex
  transcripts; `session_store.py` is the accept/reject **outcome** loop — the moat), patterns single-sourced in
  `architecture/behavioral_heuristics.json`. Whether this becomes its own brand is an **owner decision** — do not
  unilaterally name or spin it out.

---

## 3. The two laws that bind the four systems

**A. Responsibility separation (never collapse).** Efficiency (Teleon) and truth (Baltor) stay independent
subsystems with independent interfaces. A change that makes the compiler also the judge of its own correctness is
forbidden. Optimization may never silently lower the truth bar.

**B. Dependency direction (code-enforced, `scripts/check_portfolio_dependency_law.py` over
`architecture/portfolio_dependency_law.json`):**

```
Baltor  →  Teleon  →  OpenHubForAI        (imports flow this way only)
```

Baltor imports Teleon; Teleon imports OpenHubForAI; **never the reverse.** Teleon must never import Baltor;
OpenHubForAI imports neither. PurposeTask is **Teleon**, not a Baltor subsystem. These two laws are orthogonal and
both always hold: Baltor (the truth *product*) depends on Teleon (the efficiency *runtime*) while their
*responsibilities* stay separate.

---

## 4. Universal Registry interface (one interface, no exceptions)

Every registry in the federation exposes the **same** interface. No registry gets a bespoke, inconsistent surface.
Composability is mandatory.

```ts
interface Registry<T extends RegistryObject> {
  // BUILT today on _repos/teleon/backend/src/teleon/registry/port.py (RegistryPort over the 7 catalogs):
  list()                       // enumerate
  lookup(id)                   // resolve one
  search(query)                // federated lexical+vector (OR-with-overlap ranking)
  explain(id)                  // why this object, with lineage

  // TARGET surface — build these onto the same port, same object, no special cases:
  benchmark(object)            // measured performance, not asserted
  score(object)                // two-axis: lift AND structural durability (see §11)
  health(object)               // reachability / freshness / failure signature
  relationships(object)        // edges into the knowledge graph (§9)
  history(object)              // execution-memory handle (§10)
  mutate(object)               // governed, versioned, lossless edit (never destructive)
  simulate(object)             // dry-run cost/feasibility before execution
}
```

**Status discipline:** `list/lookup/search/explain` exist now; the other seven are **named gaps**, not stubs.
Build them onto the real port; do not fake them with empty methods that return `{}`. A method that cannot yet run
returns an **honest "not-yet-built / unavailable + the next rung"**, never a fabricated value.

### Universal Registry Object (one schema, no special cases)

```ts
interface RegistryObject {
  id; name; type; versions;          // version lives in METADATA, never in names/ids
  metrics; benchmarks;               // measured, with provenance
  dependencies; relationships;       // graph edges (§9)
  cost_model; security_profile;      // for routing (§7) and Baltor (§2)
  trust_score; serves_truth;         // governance: candidates are serves_truth=false
  historical_runs;                   // execution memory (§10)
}
```

Single-source the schema (`RegistryOntologyEntry` / `RegistryObject`) — the owner's #1 named risk is **ontology
fragmentation**. Rigid shared schemas + universe/kind partitions are the defense. No parallel literal definitions
of the same shape anywhere.

---

## 5. The optimization principle — the descent

Every architecture decision serves one loop. Build the working thing first; then make intelligence disappear.

```
intent → build a brute-force graph that WORKS by any means → execute → observe inefficiency → measure waste →
identify deterministic alternatives → cut tokens → route down to the cheapest SUFFICIENT+RELIABLE model →
replace reasoning with deterministic systems → cache → parallelize → benchmark alternatives → descend → learn permanently
```

Grounded in `architecture/capability_ladders.json` (cost-ordered, **deterministic-first**, LLM-last descent
ladders), `_repos/teleon/backend/src/teleon/economics/` (the cost/routing brain), and the synthesis tree's backtracking. "Make it work →
make it efficient" **is** the compiler. Cheapest is not automatically best: a cheaper, quantized, or unstable path
that fails reliability is not a win — reliability is a first-class axis.

---

## 6. Search is the central engineering problem — not DAG generation

Never brute-force an infinite graph search. **Every layer aggressively prunes.**

```
semantic retrieval over registries → known execution templates → capability-type constraints → user constraints →
compliance constraints → simulate candidates → beam-search top candidates → benchmark top-K → execute winner →
observe → learn permanently
```

Templates carry the common case (synthesis-from-scratch scales poorly — be honest about this); search + retrieval +
pruning carry the rest. Grounded in `_repos/teleon/backend/src/teleon/registry/search.py` (federated search → the BUILD / TROUBLESHOOT /
IMPROVE builder flows) and `_repos/teleon/backend/src/teleon/registry/compose.py` (the compiler: intent or vertical playbook → candidate
DAG, each stage picking ingredients from the menu). **Treat search quality, retrieval, and pruning as the hard
problem.**

---

## 7. Real ingestion first — never hand-curate what can be ingested

Automated ingestion before manual curation, always. A registry is a **pointer + shape**; its **records come from
population engines**, not hand-building. Continuously ingest from real infrastructure: GitHub / GitLab, PyPI, npm,
Docker Hub, Hugging Face, Kaggle, OpenAPI specs, MCP registries, cloud / GPU / model providers, benchmark
leaderboards, agent repos, SaaS directories, government & public portals, security-advisory / vulnerability feeds.
**Never simulate these. Real ingestion only.**

Grounded in `scripts/harvest_tools.py` (the scaling GitHub harvester — content-hash dedupe, license classify,
resumable cursor, **honest** rate-limit stop), `_repos/teleon/backend/src/teleon/registry/populate.py` (signal → record → enrich →
stage), `scripts/distill_kaggle_kernels.py` (lossless distillation of mined kernels → candidate entries), and the
discovery pipeline. **Layering is law:** `core_curated` (vetted, read by the descent) vs `staged_massive` (JSONL
candidates, **not read until promoted**) — the promotion boundary (§11) gates one into the other.

---

## 8. Behavioral heuristics & real-time intervention (Observer / Spotter)

Continuously observe AI usage across VS Code, Cursor, Claude Code, terminal agents, MCP servers, browser
extensions, hosted chat UIs, API gateways, and autonomous agents. Detect: redundant workflows, repeated context
uploads, unnecessary frontier-model usage, reinvention of existing software, excessive context windows, duplicate
reasoning. Then **intervene** within a global interruption budget:

- prompt mentions `oauth / jwt / refresh token / callback` → likely **reinventing auth** → surface `authlib`,
  `authentication`, `fastapi-users` with benchmarks.
- prompt mentions `retry / backoff / rate limiter / queue` → likely **reinventing resilience** → surface proven
  libraries.
- "build a scraper" → **official API exists** → route to it. "need OCR" → **check the embedded text layer first**.

Heuristics are single-sourced in `architecture/behavioral_heuristics.json` and continuously evolve from the
accept/reject outcomes in `session_store.py`. The intervention engine is `_repos/teleon/backend/src/teleon/observer/router.py`. Scale the
heuristic set toward the millions — but every heuristic is a **typed, testable** rule, never a hardcoded string
match buried in logic.

---

## 9. The global knowledge graph — the machine's world model

Continuously construct one graph of all machine-executable capability: software, libraries, models, APIs, packages,
datasets, agent systems, tools, frameworks, infrastructure, SaaS, products, benchmarks, execution environments,
deployment/auth/security systems, public-lookup portals. Every node carries relationship metadata; the **edges are
the moat**, not the nodes:

`depends_on · alternative_to · faster_than · cheaper_than · higher_accuracy_than · equivalent_to · deprecated_by ·
requires_authentication · requires_gpu · requires_browser · requires_human_approval · compliance_restricted ·
high_failure_probability · historically_successful_with`

Grounded in `_repos/teleon/backend/src/teleon/knowledge/` (dependency graph, product-distance, repo-similarity, **code-genome** AST
fingerprints). Repository intelligence ingests repos → extracts AST, dependency graphs, architectural fingerprints,
reusable primitives, software-genome signatures → measures software / product / architecture similarity. Goal:
**the system knows what software already exists globally, so humans and agents stop rebuilding it.** Equivalence is
**benchmark-relative**, not proven-universal — label it honestly.

---

## 10. Execution memory — history is the moat

Every run becomes memory: workflow history, success/failure rates, model performance, API-degradation & outage
patterns, retry patterns, costs, latency, benchmark results, failure signatures, successful pipeline variants,
equivalent successful graphs, optimization & descent histories. The registry is copyable; **the accumulated record
of real execution outcomes + the verification universe is not.** Grounded in the brain / flywheel /
external-outcomes machinery (Teleon learns even from runs it never executed). The system learns continuously.

---

## 11. HARD CONSTRAINTS — the enforced laws (read before every change)

These are not style preferences. They are gated by `scripts/run_proofs.py` and `check_*` scripts, and several are
codified in `docs/codex/`.

1. **Anti-placeholder doctrine (your strongest law).** No toy architecture. No mock/stub/empty system pretending to
   be complete. No fake abstraction disconnected from real infrastructure. Real APIs, real repos, real packages,
   real providers, real benchmarks, real telemetry, real execution. Build production architecture immediately;
   never optimize for a demo.
   - **Critical distinction — placeholders ≠ data.** "No synthetic placeholders" governs **implementations**. It
     does **not** override two safety/governance laws: (a) test/seed **DATA** must be **synthetic or public only —
     never real PII, secrets, or proprietary dumps**; (b) generated rows are **`serves_truth=false` candidates**
     (discovery ≠ trust) until verified. **Forbidden:** a fake implementation. **Required:** real wiring, with
     synthetic/public data flowing through it, candidates honestly labeled.
   - **Honest-unavailable, after climbing.** A capability that genuinely cannot run (no key, rate-limited, blocked)
     fails **honestly and names the next rung** on the escalation ladder (API → browser → stealth → vision-coords).
     Climbing the ladder is mandatory *before* declaring unavailable. **Faking a result is forbidden; honest
     unavailability after climbing is correct.**
2. **No magic values / single source of truth** (`docs/codex/no-magic-values.md`). Numbers that describe the repo
   (counts, totals, versions) are **computed**, never typed into prose. Shared values get **one** definition and
   are imported. The README count drifting from a hand-typed number is the canonical bug — never reintroduce it.
3. **Lossless distillation** (`docs/codex/lossless-distillation.md`). Distillation / compression / promotion /
   LLM→deterministic conversion creates a **new versioned** layer and **preserves** raw + intermediates + lineage +
   held-out + rejected + rollback target. Omitted ≠ deleted. No destructive overwrite of truth-bearing facts.
4. **Warrant before change** (`docs/codex/change-verification-contract.md`). Every change carries a warrant matched
   to blast radius: trivial/reversible → a repo principle suffices; **design / brand / strategy / vocabulary /
   pricing / product-structure → clear owner intent OR strong corroboration, NEVER a unilateral single-agent
   call**; irreversible/outward-facing → explicit intent + confirmation. "It's green" is necessary, not
   sufficient.
5. **Promotion boundary.** Candidate-table load-readiness ≠ active publication. A candidate stays tenant-invisible
   while it has open/high-risk review tickets, placeholder embeddings, unresolved source/signature questions, or
   volatile public facts without CDC/revocation. `core_curated` vs `staged_massive` (§7) is this boundary in the
   ingestion layer.
6. **Capability-gap admission — the PMF selection criterion** (`docs/concepts/capability-valleys.md`,
   `scripts/eval/reason_codes.py`, `scripts/eval/durable_gap_harness.py`). Build for the **negative space** where
   base models lack capability, not the head of the distribution. **Two-axis admission:** a component must lift
   (`pipeline_score − bare_model_score > 0`) **AND** the lift must be **structural** (won't close when the next
   model ships). Screen cheap before you collect expensive (`scripts/acquisition/gap_screen.py`).
7. **Move, never delete.** Superseded files relocate to `archive/legacy/<original-path>` with a status label +
   manifest entry; they stay in git for lineage and rollback. Never untrack. Never mislabel live/generated data as
   "legacy."
8. **Scope guards.** **No insurance** pipelines (existing legacy examples are not expanded). Env-var **names** only
   — never secret values. Sensitive domains prefer review queues, verified facts, signed publishers, redaction,
   provenance, and deterministic gates over "just ask the model."
9. **Change a seam → update its asserting check in the same change.** Keep the gate green, or **record the red**
   honestly. Never fake green; never silently leave a red.

---

## 12. Product-market fit & sequencing (the honest part)

Architect for internet scale; **sequence delivery vertical-first with real proof.** Scale-ready ≠ scale-faked.
Never hardcode a small limit; never *claim* a scale you have not proven.

- **Customers — agents become primary users.** The durable wedge is **agents as customers**: Teleon exposes stable,
  receipt-backed CapabilityTasks an agent calls *instead of burning its own tokens* re-deriving them. Secondary
  buyers: enterprises buying **governed truth/context** (Baltor); developers/teams buying **waste-reduction &
  anti-reinvention** (Observer / Spotter); the open ecosystem (Hubs) as the top-of-funnel.
- **Win one vertical provably first.** The chosen starter is the **HealthLynked-style provider directory**
  (healthcare-**admin** directory data — NOT insurance; synthetic/public only): a governed, deterministic-first
  pipeline that is provably ~95%+ cheaper than always-frontier. Other proven governed descents: OFAC/sanctions
  name-screening (the first `serves_truth=true` capability), regulatory-answer (CFPB/eCFR). Pitch the **pattern**
  (intake → extract → validate → policy → decide → act), not a single vertical.
- **The moat is the flywheel, not the registry.** Registries are copyable. The accumulated execution history (§10)
  and the under-built Verification universe (§2 Baltor) are not. Bias new investment toward verification and toward
  capturing real outcomes.
- **Do not over-build ahead of proof.** Architect the universal interfaces (§4) and ingestion (§7) for scale, but
  **do not** build discovery-at-internet-scale, capability-futures markets, or a formal universal IR before one
  vertical is provably won. Honest current limits to carry, not paper over: synthesis-from-scratch scales poorly
  (templates carry the common case); equivalence is benchmark-relative; MCP is a security surface; cheapest paths
  are often the least reliable.

---

## 13. Vocabulary discipline

Use **components** and **subcomponents** in new prose (not "artifact"/"manifest" unless quoting an existing schema
or filename). The seven-primitive model is canonical (`docs/concepts/component-taxonomy-and-stages.md`):
**Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output**. Product vocabulary: **Knowledge
Corpus** (not "knowledge pack"), **If Statement** (not "rule/logic pack"), **Action** (a persona / tool / processor
/ harness / rubric is an Action). Brand: parent **AI Done Right**; product **Teleon**; **PurposeTask**
(synonym CapabilityTask); staff **Teleon Control Tower**; customer **Capability Assurance Portal**. Version lives in
metadata, never in names or IDs.

---

## 14. Definition of done (every build increment)

A change is done when **all** hold:

- [ ] It wires **real** infrastructure (or fails **honest-unavailable** after climbing the ladder) — no stub, no mock-as-complete.
- [ ] Generated rows are `serves_truth=false` candidates; only gate-passed outputs claim truth.
- [ ] Counts/totals are **computed**; no magic values; shared values single-sourced.
- [ ] Raw + lineage + held-out + rejected survive (lossless); superseded files **moved**, not deleted.
- [ ] It carries a **warrant** matched to blast radius (owner intent for design/brand/strategy).
- [ ] Any changed seam has its asserting `check_*` updated in the **same** change; `scripts/run_proofs.py` is green, or the red is honestly recorded.
- [ ] It **extends** the real modules named above — it does not create a parallel reinvention beside them.

---

## The question the system asks forever

**Can intelligence be removed?**

Humans think *"I need to build this."* The system thinks *"I know 14,000 equivalent implementations, the cheaper
and faster and more reliable alternatives, the existing packages and equivalent APIs, the benchmark history, the
deterministic substitutes, the failure probabilities, the better execution graph — and which intelligence here is
unnecessary."* Final mission: become the **universal coordination layer for all machine-executable computation** —
real, verified, and continuously descending toward optimal.
