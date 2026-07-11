# Capability Valleys — a theory of *defensible* LLM gaps

This is the foundational "where do we build?" document for OpenHubForAI. A
component earns a place only if it lets an LLM do something it cannot do
reliably alone (the [capability-lift bar](../../scripts/eval/durable_gap_harness.py)).
But "the model is bad at X" is not enough. Most gaps **close on their own**, and
when they do, the work you did to find and fill them becomes the training set
that erases your own niche. This document is the discipline for telling the two
apart.

Single source of truth for the taxonomy lives in code:
[`scripts/eval/reason_codes.py`](../../scripts/eval/reason_codes.py). The
instrument that applies it: [`scripts/eval/durable_gap_harness.py`](../../scripts/eval/durable_gap_harness.py).
Do not re-define these lists in prose — link to them.

## The one question

> **Will this gap close on its own?**

- **Transient gap** — closes when labs throw scale, data, or a tool at it. The
  expert demonstrations you collect to *find* it are exactly the data that
  *closes* it a generation later. **Discount these. No moat.**
- **Durable gap** — does not close with more model/data/tools, because the human
  advantage is *not a text-prediction advantage at all*, or the authoritative
  source lives in a channel a pipeline structurally cannot ingest. **Build here.**

A capability spike (Karpathy's jagged frontier) needs four things at once:
**(1) volume** of digitized in-domain text, **(2) verifiable ground truth**,
**(3) a benchmark with economic pressure**, and **(4) a stationary target**.
Valleys fail some or all of these. The deepest, most durable valleys fail
condition 4 — the target *moves* — or fail a fifth, architectural condition the
spike formula never named: the ground truth is in a form the machine cannot see.

## First, classify the complaint (the trichotomy)

Most "the model is dumb" claims are really an *architecture* mismatch. Before
anything else, sort the task:

1. **Parametric-knowledge task** — the answer should live in the weights.
   Fixable with training data. (Don't expect a model to *memorize* live data —
   that's not knowledge, it's a database row, stale the moment it's written.)
2. **Retrieval task** — the answer is a lookup/tool call. The right architecture
   is model + tool (function-calling / RAG / MCP), not a bigger model.
3. **No-endpoint task** — there is nothing to point a tool at. The authoritative
   source is un-addressable, ephemeral, oral, or behind a wall.

Tooling rescues 1→2→3 dramatically — and then **sharpens, rather than closes,**
the residual hard part. *Building the tool is the easy 20%; tooling moves the
failure surface rather than eliminating it* (tool selection, schema
heterogeneity, retrieval-returns-garbage, the interpretation trap, rate
limits/auth/freshness). **Our product sells those guardrails**, not the tool.

## The retrievability spectrum

How reachable is the ground truth? (`RETRIEVABILITY_TIERS` in code.)

| Tier | What | Example | Tooling solves it? |
|---|---|---|---|
| 1 | Clean public API | NYC Open Data / Socrata SoQL, Open311 GeoReport v2 | ✅ point a tool at it |
| 2 | Structured, no clean API | scrape/ETL into your own index | ✅ more work, doable |
| 3 | Unstructured but addressable | PDFs/reports on a stable URL → OCR + RAG | ⚠️ lossy but possible |
| 4 | Un-addressable / ephemeral / login-walled | deleted Facebook post in Pidgin, WhatsApp-forwarded circular | ❌ no endpoint exists |
| 5 | Human-only (apex tool call) | go inspect the site, call the regulator, sign as a licensed pro | ❌ highest-cost endpoint |

Tiers 1–3 are *retrieval tasks* — defensibility comes from the guardrails, not
the lookup. Tiers 4–5 are *no-endpoint tasks* — the architectural valley.

## Why the task is hard (mechanisms)

`MECHANISMS` in code. These say *why a model breaks*, independent of
retrievability:

- **anti_fluency** — domain punishes fluent paraphrase, rewards a rigid
  approved-word grammar. *ASD-STE100 / Simplified Technical English, ICAO
  phraseology, Attempto Controlled English.*
- **sub_token** — the task lives below the token boundary. *Exact
  character/byte counting, fixed-width/ASCII alignment, raw digit arithmetic.*
- **rigid_grammar** — long-range structural constraints to satisfy exactly.
  *SMILES/SELFIES valence & ring closure, Verilog/VHDL timing, Coq/Lean/TLA+
  proof tactics, patent-claim antecedent basis, ABC/LilyPond music.*
- **sparse_data** — little in-domain text; the model reverts to a common
  neighbor. *Low-resource & agglutinative languages, COBOL/RPG/JCL, Global
  South statutes/circulars/gazettes.*
- **coded_vocabulary** — output is a code where fluency gives zero signal and a
  plausible-but-wrong code is worse than abstaining. *ICD-10/CPT/SNOMED,
  METAR/TAF/NOTAM, G-code, ARINC 424.*
- **adversarial_concealment** — the target actively mutates to stay
  out-of-distribution. *Laundering typologies, trafficking code words,
  scam-compound rebrands.* (Condition-4 failure → permanent.)
- **channel_inaccessibility** — the authoritative source lives in a channel a
  pipeline cannot ingest. (The architectural valley; see the matrix.)

## The architectural valley: channel × failure

Tier-4 gaps are not a *volume* problem (more crawling/compute won't fix them) —
they are a *medium* problem. The authoritative layer of reality is transmitted
through channels optimized for human immediacy and social reach, which are
exactly the channels optimized *against* machine ingestion, durability, and
addressability. In much of the Global South the closed platform *is* the public
web (Free Basics walled gardens; "Facebook is the internet"), so a regulator
posts where its audience is — precisely where crawlers are locked out.

| Channel | Un-crawlable | Stale / un-current | Un-parseable | Un-addressable (no canonical record) |
|---|---|---|---|---|
| Login-walled post (FB page, WhatsApp broadcast) | ✅ crawlers denied access | ✅ may never enter any snapshot | – | ✅ silently edited/deleted |
| Scanned image-PDF / photographed memo | partial | – | ✅ no text layer; OCR lossy on stamps | – |
| Oral / radio / read-aloud notice | ✅ never digital | ✅ | ✅ | ✅ |
| Ephemeral / edited / screenshot-forwarded | ✅ | ✅ in force in hours | – | ✅ propagates as a photo 3 forwards deep |
| Code-switched vernacular (Taglish, Sheng, Pidgin) | – | – | ✅ filters bias against code-mixing | – |
| Deliberate shutdown / platform block | ✅ unreachable to all | ✅ | – | ✅ |

The failure presents *identically to a confident correct answer*: with nothing
in training, the model doesn't abstain — it confabulates a plausible,
formal, usually Western-shaped rule, and fluency hides the void.

## Why the human won (reason codes — the decision)

For every gap, run a competent human and the model on the same task and tag
**why the human won**. The reason code decides transient vs durable. This is the
moat test, because the same demonstrations that reveal a transient gap are the
training data that closes it. (`REASON_CODES` in code.)

**Transient — discount (the flywheel closes it):**
- `missing_parametric_knowledge` — human knew a fact the model didn't.
- `missing_tool` — human used a tool/source the model wasn't given (wire it; tiers 1–3).
- `stale_parametric` — model snapshot was stale (retrieve over a live source).
- `weak_reasoning_at_scale` — a slip scratchpads / bigger models paper over.

**Durable — build (not a text-prediction advantage at all):**
- `embodiment` — needs a body: inspect, photograph, count, swab.
- `closed_channel_access` — needs reach into a closed/relational channel: join
  the group, call the office, *know a guy* (tier 4).
- `tacit_local_knowledge` — what the rule means in practice, the informal price,
  who really decides — never written down.
- `accountability_license` — deliverable needs an accountable human who can hold
  a license and be sued. A model cannot.
- `realtime_high_stakes_judgment` — novel/adversarial/high-stakes call where
  confident-wrong is catastrophic.
- `unaddressable_source` — ground truth has no ingestible/addressable form
  (tier 4): there is no endpoint to point a tool at.

> **Strategy:** use humans as the measurement instrument to *locate* the
> frontier; use the reason code to decide which side of it is worth building on.
> If the human won because they *knew something* or *had a tool*, it's transient
> — discount it. If they won because they had *access / a body / a license /
> accountability* the model can't have, it's durable — that's the niche.

## How we score it

`gap_durability_score()` (single source) maps a gap to 0–5 (high = defensible):
a durable reason code starts high; each step down the retrievability spectrum,
an adversarial/non-stationary target, and an un-ingestible channel all raise it.
That score is a first-class promotion factor — `"durability"` in
[`candidate_promotion_scorer.py`](../../scripts/factory/candidate_promotion_scorer.py)
— so the factory preferentially promotes components that target gaps the data
flywheel won't erase.

## What we actually build (per tier)

- **Tiers 1–3 (retrieval):** the *guardrails*, not the lookup — schema
  reconciliation across heterogeneous sources, the interpretation-trap gate
  (e.g. 311 counts measure *complaints, not incidence*; rat complaints can mean
  engaged residents, not more rats), the abstain-vs-confabulate gate, freshness
  / rate-limit / dirty-data handling. (Sells exactly where tooling moves the
  failure surface.)
- **Tier 4 (no endpoint):** durable, addressable *encodings* of what is
  otherwise un-ingestible — verified-fact corpora with signed publishers, CDC
  for volatile public facts, provenance, and review queues — so a screenshot-
  forwarded rule becomes a citable component.
- **Tier 5 (human):** human-in-the-loop escalation and accountable-sign-off
  routing as explicit components, not an afterthought.

## Safety stance (non-negotiable)

Many of the richest valleys are sensitive — trafficking, forced labor, debt
bondage, laundering, predatory overcharging. We work the **defensive** view
only: detection red-flags and indicators (FATF / ILO / HRW public materials),
routing to the right hotline/authority *with citations*, review queues for
high-risk output, verified facts, signed publishers, redaction, provenance, and
deterministic gates over "just ask the model." We never produce evasion
guidance, and we never store real PII — public/synthetic metadata only. Detection
is **bidirectional-biased**: a model can miss a real victim *and* manufacture a
false one (over-flagging marginalized people) in the same breath — so these
components carry bias review, not just recall.

## The reusable probes

- **Spike probe:** a domain defeats frontier models in proportion to how much it
  punishes fluent plausibility and rewards exact conformance to a rule set that
  is rigid, sub-token, or rare in training data.
- **Architecture probe:** ask of any "the model is bad at X" — is this
  *parametric*, *retrieval*, or *no-endpoint*?
- **Moat probe:** tag *why the human won*. Transient (knew / had a tool) →
  discount. Durable (access / body / license / accountability / channel) → build.
