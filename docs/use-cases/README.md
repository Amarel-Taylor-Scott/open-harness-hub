# Use cases — where the capability-lift bar actually bites

This is the **strategy-level index** to the use-case library: who buys, what
breaks in a bare model, which product lifts it, and the **shape of the claim**
that proves the lift. For the recipe-level "what you can build today" catalog —
the eight one-page composition recipes with install paths — see [[index.md]].
This page sits above those: it ties each use case to the
[capability-lift bar](../concepts/capability-valleys.md) and shows how the *same*
governed object is consumed through **two doors**.

Two products ride one shared backend ([[../strategy/two-services-shared-infrastructure.md]]):

- **OpenHubForAI (OHH)** — assemble and monitor a *bounded* governed
  pipeline, with rules around input and output. Sells governed **pipelines**.
- **Baltor / Baltor** — refine content into token-efficiency tiers
  (raw → compressed → hyper-efficient) and serve governed corpora + tools into
  whatever *open-ended* agent you already run. Sells governed **fuel**.
  ([[../strategy/context-enrichment-service.md]].)

A Knowledge Corpus or Action is minted **once**, with one provenance trail and
one lift/fidelity score, then wired into an OHH pipeline **or** served by Baltor.
Same object, two consumption models — that is the "join."

## The admission bar these use cases share

Nothing earns a place because it is *nice to have*. The
[capability-lift bar](../concepts/capability-valleys.md) is a **hard floor**, on
two axes ([[../codex/master-goal.md]], [[../strategy/two-services-shared-infrastructure.md]]):

1. **It must lift** — `pipeline_score − bare_model_score > 0` on a real,
   held-out task. If a frontier model already does the task zero-shot, it does
   not belong here.
2. **The lift must be durable** — *structural*, won't close when the next model
   ships. The single source of the taxonomy (lift_reason → durability_class,
   mechanisms, retrievability tiers) is `scripts/eval/reason_codes.py`; the sorter
   is `scripts/eval/durable_gap_harness.py`. Do not re-derive those enums here.

Two honesty rules govern every claim below:

- **Lift is pipeline-level and measured paired** — bare model vs. the assembled
  pipeline on the user's data, scored by a *separate* evaluator, never
  self-graded ([[../design/value-propositions.md]],
  [[../concepts/context-layer-and-the-desk.md]]). A single *component* shows
  "where it fits," not a number.
- **Baltor's analogue is fidelity-per-tier** — every refined tier ships a
  published quality delta (raw → compressed → hyper-efficient) from a separate
  evaluator. Same measurement engine as OHH's lift gate, extended from "does the
  pipeline lift?" to "did the tier preserve enough?" ([[../strategy/context-enrichment-service.md]].)

Below, the "**claim shape**" column is the *form* of the proof — not an invented
number. Where a real measured result exists in this repo, it is cited and
labelled as such; everything else states the metric that *would* be reported,
not a fabricated value.

## The six index entries

| # | Use case | Product | Bare-model gap (why it fails) | Durable-gap reason code |
|---|---|---|---|---|
| 1 | Anti-trafficking recruitment screening | OHH | Code-words mutate to stay out-of-distribution; confident-wrong is catastrophic | `adversarial_concealment` |
| 2 | EUDR / deep-tier supply-chain due diligence | OHH | Volatile multi-jurisdiction law + non-English red-flags below the fluent surface | `unaddressable_source`, `sparse_data` |
| 3 | Clinical differential support | OHH | Needs an accountable licensed signer; coded vocabulary (ICD-10) | `accountability_license`, `coded_vocabulary` |
| 4 | Refugee-bureaucracy translation | OHH | Forms/circulars in closed channels; controlled output the model paraphrases away | `closed_channel_access`, `anti_fluency` |
| 5 | Governed code-context served into Claude Code | Baltor | Raw repo blows the window; un-governed compression destroys reasoning | fidelity-per-tier (enrichment wedge) |
| 6 | Live-fresh regulatory corpus served to any agent | Baltor | A static download can't stay current; freshness is the recurring obligation | freshness / CDC (management surround) |

Entries 1–4 are OHH (bounded pipelines); 5–6 are Baltor (governed fuel into open
agents). The detail recipes for the OHH cases live next to this file; the Baltor
cases are specified against [[../strategy/context-enrichment-service.md]] (status
below).

---

### 1 · Anti-trafficking recruitment screening (OHH)

**The task.** Review user-generated content (job posts, classifieds,
escort/massage directories, forums, dating-app messages) for human-trafficking
*recruitment* and *solicitation* signals; escalate flagged posts to a trained
human moderator with extracted indicators and a structured statement of reasons.
Defensive only — the catalog refuses attack tooling, evasion guides, and
content-generation flows useful to traffickers.

**Why a bare model fails.** This is the `adversarial_concealment` valley
([[../concepts/capability-valleys.md]]): the target *actively mutates* to stay
out-of-distribution, so a model trained on yesterday's wording confabulates a
plausible answer with nothing behind it — and the failure presents *identically
to a confident correct answer*. Detection is bidirectionally biased: a model can
miss a real victim *and* manufacture a false one (over-flagging marginalized
people) in the same breath. Confident-wrong here is catastrophic.

**The governed pipeline.** `pipeline/gemma4-trafficking-ugc-triage`
([recipe](human-trafficking-ugc-detection.md)) redacts PII before any inference,
runs deterministic GREP Conditionals in order (CSAM-route first, so suspected
CSAM short-circuits to an NCMEC packet *before* the model ever classifies it),
extracts indicators in a two-stage extract-then-judge Action, scores against the
Polaris typology, and emits decision + severity + evidence-cited reasons. The
governance — citation per escalation, ≥2 co-occurring indicators before
escalation, refuse-on-redacted, NCMEC route without classification — *is* the
product; it is what a bigger model cannot copy.

**Claim shape.** Pipeline-level recall *and* false-positive (over-flagging)
rate, measured paired against the bare Gemma-4 model on a held-out labeled set —
**both** directions, because recall alone hides the manufactured-victim failure.
Thresholds ship conservative (`threshold: 0.55`) and are calibrated per platform
via `scripts/bench_pipelines.py` on the operator's own labeled data. No headline
lift number is asserted here — the metric is the operator's to measure, and the
audit trace makes the result inspectable.

### 2 · EUDR / deep-tier supply-chain due diligence (OHH)

**The task.** Audit deep-tier supplier networks (tier 3, tier 4+) for forced
labor, **deforestation / environmental harm** (EUDR, ESRS E1–E5), and governance
gaps across 12 jurisdictions — and share rogue-broker / rogue-corridor signals
with peer orgs *without* leaking confidential supply-chain data.

**Why a bare model fails.** Two stacked durable gaps. The authoritative material
is volatile, multi-jurisdiction regulation plus red-flags expressed in 13
languages *below* the fluent English surface (`sparse_data`); and the ground
truth at deep tiers is often `unaddressable_source` — most factories subcontract
through informal labor agencies whose books never surface in any registry. A
base model fluently summarizes Western-shaped compliance and silently misses the
Mae-Sot-textile-workshop reality.

**The governed pipeline.** The ESG family
([recipe](esg-supply-chain-due-diligence.md)) flattens structured disclosures to
prose, fires three deterministic GREP Conditionals (forced-labor / environmental
/ governance), retrieves cited regulatory + corridor Knowledge Corpora
(CSDDD · CSRD · **EUDR** · UFLPA · LkSG · 16 more), judges against a 12-dimension
rubric Action, walks T1→T4+ with an iterative-revise loop that *surfaces audit
gaps* it cannot resolve, and shares cross-org signals through a k-anonymity +
HMAC pattern (count `< k` buckets dropped). The pipeline produces **risk flags
with citations**, never a forced-labor determination — that stays with the
compliance officer after the supplier's right of reply.

**Claim shape.** Per-dimension precision/recall vs. the bare model on labeled
disclosure packs (`benchmark/esg-supplier-grading-bench`, two model arms). **One
real measured result exists** and is the honest illustration of the shape: a
live GREP test on 2026-05-19 (`data/esg-grep-findings.json`) stayed silent on the
well-disclosed T1 supplier (zero false positives), surfaced 2 high-severity
deforestation flags on a Paraguay T2 soy supplier, and detected all 10 expected
indicators across the three ESG dimensions on a flagged T3 textile workshop. That
is a *deterministic-Conditional* result, not an end-to-end lift number; the
end-to-end pipeline lift is measured per operator on their own labeled set. The
pack is `lifecycle: experimental`.

### 3 · Clinical differential support (OHH)

**The task.** Clinician-facing decision support: ranked differential with
red-flag escalation in the first sentence, cited guidelines, and ICD-10 lookups,
PHI-safe — for triage assistants, low-resource settings, and case-review QA.

**Why a bare model fails.** Two durable reasons. The deliverable needs an
`accountability_license` — an accountable human who can hold a license and be
sued; a model cannot, so the architecture must route to one, not impersonate one.
And ICD-10 is a `coded_vocabulary` where fluency gives zero signal and a
plausible-but-wrong code is worse than abstaining.

**The governed pipeline.** `pipeline/differential-diagnosis`
([recipe](clinical-decision-support.md)) redacts PHI (HIPAA Safe Harbor), screens
clinical red-flags as a deterministic Conditional (ACS, stroke, SAH, anaphylaxis,
OB/psych emergencies), retrieves cited guideline + ICD-10 + drug-interaction
Knowledge Corpora, and runs a citation-first persona Action that **refuses to
diagnose or prescribe** and surfaces any red flag in the first sentence. Defaults
are local-model-only (`adapter/ollama-default`) so no PHI leaves the host.

**Claim shape.** Red-flag escalation recall and ICD-10 coding accuracy
(correct-code vs. confident-wrong vs. abstained) measured paired against the bare
model. The decisive governance metric is the *abstain-when-uncertain* rate — the
pipeline is admitted because it converts confident-wrong codes into cited
candidates or honest abstentions, with an accountable clinician in the loop.
Educational decision support, **not** a substitute for licensed clinical
judgment.

### 4 · Refugee-bureaucracy translation (OHH)

**The task.** Help a displaced person understand and complete host-country
bureaucratic forms, circulars, and notices — in their language, with the
controlled official terminology preserved. (Recipe:
[refugee-bureaucracy-translation.md](refugee-bureaucracy-translation.md).)

**Why a bare model fails.** The authoritative source is frequently
`closed_channel_access` — a circular posted to a login-walled page, a
WhatsApp-forwarded notice, a photographed memo with no text layer — exactly the
channels optimized *against* machine ingestion ([[../concepts/capability-valleys.md]]).
And the output is `anti_fluency`: official terms, agency names, and legal
categories that a fluent model "helpfully" paraphrases into something *wrong*,
where the wrong-but-fluent version costs the applicant their claim.

**The governed pipeline (OHH).** Deterministic Conditionals pin the controlled
vocabulary and route un-ingestible inputs to a human-verified Knowledge Corpus
entry rather than letting the model invent the rule; retrieval grounds every
instruction in a cited, signed source; the Action explains in plain language
*without* mutating the official term; abstain-on-missing-source prevents
confabulating a procedure that doesn't exist in that jurisdiction. This is the
tier-4 build pattern: a screenshot-forwarded rule becomes a citable component
with a signed publisher and CDC freshness.

**Claim shape.** Controlled-term preservation rate and procedure-accuracy vs. the
bare model, plus the abstain-vs-confabulate rate on inputs whose source is not in
the corpus — measured paired on a held-out set of real (synthetic-PII-only)
forms. The lift is structural: it comes from grounding + the abstain gate, not
from a bigger model.

### 5 · Governed code-context served into Claude Code (Baltor)

**The task.** Drop token-dense, *governed* context for a specific codebase
straight into an open agent loop — Claude Code, Cursor, any MCP client — so the
agent reasons over the right slice of the repo without the operator hand-rolling
a context dump.

**Why a bare model / naive setup fails.** A raw repo blows the context window;
the established fix (ad-hoc local CLIs) compresses *once, locally, ungoverned*.
And the failure mode every context-optimization guide flags is real: **compress
too aggressively and you destroy the model's ability to reason**
([[../strategy/context-enrichment-service.md]]). There is no provenance, no
freshness, and no proof the compressed tier preserved enough.

**The served corpus (Baltor).** Baltor hosts the codebase as three tiers built on
the *same* shared compression/memory/cache components OHH uses:
**raw** (object store + source registry), **compressed-structural** (strip
function bodies, keep signatures — the Tree-sitter technique Repomix proves at
**~70% token reduction on code, structure lossless**), and **hyper-efficient**
(distilled facts packaged onto a cacheable prefix so the provider prompt cache
does the rest). It serves whichever tier the operator pays for through four
surfaces — MCP server, packed file / llms.txt, Claude Code skill, CLAUDE.md
fragment — tier-negotiated and CDC-fresh. The output isn't an answer; it's a
governed corpus rendered into the shape the agent ingests.

**Claim shape — fidelity-per-tier, not lift.** Each tier ships a **published
quality delta** from `verify.compression_fidelity`, scored by a *separate*
evaluator ("did this tier preserve enough to answer correctly?") — never
self-graded. The ~70% structural figure above is the **mechanism's** documented
reduction (Repomix/Tree-sitter), *not* a fidelity guarantee; the guarantee is the
measured delta Baltor publishes per tier. The recurring-revenue obligation is
keeping a live corpus fresh — a static download can't.

**Status (honest).** Spec-level. The tier / surface / fidelity **components are
seeded as governed definitions** (`scripts/seed/baltor_components.py`, lifecycle
experimental); the `baltor` web surface is live, but the
`enrichment` platform service is **`status: planned`** in
[`services/registry.yaml`](../../services/registry.yaml) — the tier pipeline, the
MCP serving endpoint, the four emitters, and the fidelity meter are not yet
implemented. Do not read the ~70% number as a shipped product metric.

### 6 · Live-fresh regulatory corpus served to any agent (Baltor)

**The task.** Serve a *volatile* governed knowledge base — e.g. the EUDR / CSDDD
regulatory corpus that already backs use case 2 — into an arbitrary agent loop,
kept current as the underlying regulation changes.

**Why a bare model / static export fails.** The corpus is the antidote to the
`unaddressable_source` / volatile-regulation gap — but only while it stays
current. A frozen download is stale the moment a jurisdiction amends a rule; the
model then cites a repealed clause with full confidence. Freshness, not
compression, is the binding constraint here.

**The served corpus (Baltor).** The *same* governed Knowledge Corpus minted for
the OHH pipeline (use case 2) is served through Baltor's MCP surface with CDC /
freshness tracking — the "context management" surround
([[../strategy/context-enrichment-service.md]], [[../concepts/context-layer-and-the-desk.md]]).
This is the literal "two doors, one object": one provenance trail, one
fidelity/lift score, wired into a bounded pipeline *and* served to an open agent.

**Claim shape.** Freshness SLA (max staleness vs. the primary source) and
citation-validity rate (share of returned citations still in force), plus the
per-tier fidelity delta from use case 5's engine. Pricing follows the freezable
boundary: a static tier is one-time / storage-priced; the *live-served,
kept-fresh* tier is recurring, because freshness is a continuous obligation
([[../strategy/context-enrichment-service.md]]). Same `status: planned` caveat as
use case 5 — the CDC/freshness serving path is specified, not yet shipped.

---

## How these map back to the two doors

| | OHH (bounded pipeline) | Baltor (governed fuel) |
|---|---|---|
| **Buyer** | builders / applied teams operating a pipeline | agent builders / Claude Code users enriching *their own* agent |
| **Sells** | governed **pipelines** | governed **fuel** (tiers + corpora + tools) |
| **The proof** | pipeline-level **lift** (paired, separate evaluator) | **fidelity-per-tier** (paired, separate evaluator) |
| **Recurring vs. freezable** | freezable Conditionals/retrieval/citation gates; pay model cost for the one Action call | raw + compressed are freezable; live-served + CDC-fresh is recurring |
| **Examples here** | 1 · 2 · 3 · 4 | 5 · 6 |

The expensive substrate — clusters, workers, the foundry, the corpora, the
compression/eval engine, the governance — is **one cost center** behind both
doors ([[../strategy/two-services-shared-infrastructure.md]]). A better
compressor or a fresher corpus built for one product is instantly available to
the other, which is why the data plane is attribute-level, not column-level
([[../codex/schema-extensibility.md]]).

## What these use cases are NOT

- **Not** legal, clinical, or compliance *determinations*. Every OHH case above
  produces cited evidence and routes the decision to an accountable human; the
  determination stays with the licensed/responsible party.
- **Not** asserted-lift marketing. Numbers on this page are either (a) the
  documented reduction of a named mechanism, clearly labelled, or (b) the *shape*
  of the metric an operator measures on their own held-out data. No headline lift
  figure is invented.
- **Not** offensive tooling. The trafficking and ESG cases are defensive: red-flags
  and indicators from public NGO/UN/regulatory materials, routed with citations to
  the right authority. No evasion guidance; no real PII — synthetic/public metadata
  only ([[../concepts/capability-valleys.md]]).
- **Not** shipped where marked `planned`. The two Baltor cases are spec-level
  against [[../strategy/context-enrichment-service.md]] and
  [`services/registry.yaml`](../../services/registry.yaml); their components are
  seeded, the serving path is not yet implemented.

## See also

- [[index.md]] — the recipe-level catalog of eight starter use cases with install
  paths and composition diagrams (the "what you can build today" layer).
- [[../concepts/capability-valleys.md]] — the theory of *defensible* gaps and the
  reason-code taxonomy every entry above is tagged against.
- [[../codex/master-goal.md]] — the capability-lift bar as a hard admission floor.
- [[../strategy/two-services-shared-infrastructure.md]],
  [[../strategy/context-enrichment-service.md]] — the two-products-one-backend
  decision and the Baltor spec.
- [[../design/value-propositions.md]] — the promise every surface must say.

---

*Warrant: user-intent — the owner's brief for this doc ("a use-case index + 4–6
concrete use cases spanning BOTH products… each tied to the capability-lift
bar," drawing on "anti-trafficking recruitment screening, EUDR deforestation,
clinical triage + a Baltor one (governed code-context served into Claude Code)").
Corroboration — the cited repo worked examples
([human-trafficking-ugc-detection.md](human-trafficking-ugc-detection.md),
[esg-supply-chain-due-diligence.md](esg-supply-chain-due-diligence.md) incl. the
real `data/esg-grep-findings.json` test, [clinical-decision-support.md](clinical-decision-support.md),
[refugee-bureaucracy-translation.md](refugee-bureaucracy-translation.md)),
[[../strategy/context-enrichment-service.md]], and [`services/registry.yaml`](../../services/registry.yaml).
Principle — the capability-lift bar and the change-verification contract
([[../codex/master-goal.md]], [[../concepts/capability-valleys.md]],
[[../codex/change-verification-contract.md]]): honest real-vs-planned labelling,
no invented metrics, canonical vocabulary (Knowledge Corpus / Conditional /
Action).*
