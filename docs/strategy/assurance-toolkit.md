# Assurance toolkit — the context-assurance machinery (the moat) + the next wedges

The canonical catalog of the **context-assurance toolkit**: the verification tools that prove a
Knowledge Corpus or a claim is **TRUE and current**, not merely faithfully retrieved. This is the job
Contextual structurally avoids — they ground answers in the docs but never check the docs are correct or
current ([[positioning-v2.md]]). This doc is the tool-level companion to the corpus/seed checklist in
[[oracle-corpus-and-tooling-map.md]]; read those two first for *why* and *which corpora* — this doc is
*which tools, by method, and what to build next*. It does not duplicate them.

**Read the honesty column.** Each tool is marked **REAL** (code shipped + self-test), **DEF** (governed
manifest shipped, implementation pending), or **SPEC** (proposed, not yet written). No metrics are quoted
here that we have not run.

## 0. The one rule the whole toolkit enforces

> Verify a claim via **multiple independent methods**; trust nothing on a single point.

Operationalized as the **change-verification contract** ([[../codex/change-verification-contract.md]]),
applied to *context* the same way it gates *our own changes*:

- **≥2 independent agreeing sources** is the admissibility bar. One source — or one agent's assertion — is
  not corroboration. The contract's warrant types map directly onto context: a claim is admissible on
  *corroboration* (≥2 oracles agree), an *established authority* (a registered oracle source_record), or
  explicit *human adjudication* (HITL on a conflict).
- **No agent grades its own work.** The tool that *gathers* a claim is never the tool that *blesses* it.
  The skeptic (`claim_refute`) is a different Action from the gatherers; the human in `cross_source_reconcile`
  is a different party again. This is the contract's "verifier is a different agent than the builder",
  enforced at runtime over context instead of over commits.
- **Provenance ≠ truth.** A signed corpus proves *origin*, not *honesty* — a bad actor can sign misleading
  content ([[oracle-corpus-and-tooling-map.md]] §C). So signing (`oracle_c2pa_attest`) is the *last* step,
  recording *which* assurance verdicts the certification covered, never a substitute for them.

The blast-radius ladder from the contract carries over: a low-stakes summary needs corroboration; a
**sanctions** determination (the beachhead — stale = a federal violation) needs corroboration **plus** the
authority binding **plus** HITL before it is served or signed.

## 1. The toolkit by method

Every verification tool is an **Action** (a tool/processor/harness is an Action in our vocabulary). They are
grouped by *how they get independent evidence* — the point is method diversity, so a single failure mode
(one stale index, one poisoned doc, one model's confident guess) cannot pass.

### A. Deterministic functions (pure-stdlib, no model, no network)

These run over **governed inputs** (a `source_record`, a content_hash, a Knowledge Corpus snapshot) and are
deterministic + idempotent — same input, same verdict. They are the cheapest and most trustworthy rung
because they make no call anyone can spoof.

| Tool | What it verifies | Method | trust_boundary / side_effects | Status |
|---|---|---|---|---|
| `corpus_integrity_check` | an internal doc that **contradicts** or falsely **claims to supersede** the authoritative source (the planted-fake-policy / BadRAG / TrojanRAG attack) | provenance binding + supersession-assertion check + contradiction check → `allow \| review \| quarantine` | `hub` / `read` | **REAL** — `scripts/processors/assurance/corpus_integrity_check.py` (`run()`, self-test); def `catalog/processors/assurance/corpus-integrity-check.yaml` |
| `cross_source_reconcile` | the **resolved value** when ≥2 registered authorities disagree on the same field | align claims by field → governed precedence (higher trust_tier wins; equal tier → later effective_date) → resolve **or** escalate; never silently pick | `hub` / `external_call` | **DEF** — `catalog/processors/assurance/cross-source-reconcile.yaml`; impl pending |
| `multi_source_corroborate` | a single **claim**, by requiring **≥N independent sources to agree** (default ≥2) before it passes | group evidence by the claim's field → collapse non-independence (same publisher/syndication root/mirror counts once, judged from governed provenance not text similarity) → count vs threshold N → `corroborated \| single-source \| contradicted` | `hub` / `read` | **REAL** — `scripts/processors/assurance/multi_source_corroborate.py` (`run()`, self-test); def `catalog/processors/assurance/multi-source-corroborate.yaml` |
| `citation_trace` | that each cited fact actually **traces to a governed source_record** (not a hallucinated or dangling citation) | for each citation, resolve to a `source_record` by id/hash; flag citations with no binding, hash-mismatched bindings, or quote-not-in-source | `hub` / `read` | **DEF** — `catalog/processors/assurance/source-citation-trace.yaml` (`processor/source-citation-trace`); impl pending |

`corpus_integrity_check` and `multi_source_corroborate` are the load-bearing **REAL** anchors: the first
demonstrates *check the document AGAINST the authority instead of trusting the corpus as ground truth*; the
second demonstrates the contract's *≥2 independent sources, counted from governed provenance so mirrors of
one origin can't manufacture agreement*. The rest of the toolkit generalizes these two patterns.

### B. Search calls (gather independent evidence from outside the corpus)

A search call is method-independent from the indexed corpus by construction: it asks a *different* system.
Because it reaches outside, it is `external` / `external_call` and is treated as **one source**, never as
proof on its own — its output feeds corroboration, it does not conclude it.

| Tool | What it verifies | Method | trust_boundary / side_effects | Status |
|---|---|---|---|---|
| `web_search_verify` | whether a claim is **independently attested** outside the corpus | issue a scoped query → collect results → extract the asserted value → return candidate corroborating/contradicting sources (each tagged with origin so `multi_source_corroborate` can dedupe) | `external` / `external_call` | **DEF** — `catalog/processors/assurance/web-search-verify.yaml`; impl pending |

Honesty guard: a search call gives *web-world attestation*, not authority. It is exactly Contextual's kind
of "freshness" (web knowledge + sync) — useful as **one** corroborating method, but it does **not** replace
the registered-oracle authority check. Keeping that line is the whole point of the moat.

### C. Browser / HTTP tools (go to the authority directly)

These fetch from the **authoritative origin itself** and diff it against what the corpus captured — the
freshness axis. `external` / `external_call`, with retry/backoff because the network is fallible.

| Tool | What it verifies | Method | trust_boundary / side_effects | Status |
|---|---|---|---|---|
| `corpus_freshness_diff` | that internal context is **still current** vs the source it was derived from | re-fetch/re-read the registered source → recompute content_hash + effective_date → diff vs the snapshot's captured values → `current \| stale \| unknown` + the hash/date delta as warrant | `external` / `external_call` (retry: exp, 3) | **DEF** — `catalog/processors/assurance/corpus-freshness-diff.yaml`; impl pending |
| `authority_fetch_diff` | a **point claim** against the live authority on demand | fetch the specific authoritative endpoint/page for one claim → extract the field → diff vs the claim → `match \| changed \| unreachable` | `external` / `external_call` | **DEF** — `catalog/processors/assurance/authority-fetch-diff.yaml`; the single-claim, on-demand sibling of `corpus_freshness_diff`; impl pending |

### D. The adversarial skeptic (try to break the claim)

The methodological inverse of the gatherers: instead of finding support, it actively tries to **refute**.
This is the contract's adversarial-verify duty made into a runtime Action — and the structural reason it is
a *separate* tool is the no-agent-grades-its-own-work rule.

| Tool | What it verifies | Method | trust_boundary / side_effects | Status |
|---|---|---|---|---|
| `claim_refute` | whether a claim **survives** a hostile attempt to disprove it | construct the strongest counter-case from the same governed sources (look for a contradicting source_record, a newer effective_date, an unmet precondition, a scope/jurisdiction mismatch) → `refuted \| unrefuted \| insufficient_evidence` with the disconfirming evidence cited | `hub` / `read` (deterministic over governed inputs; `external_call` only if it is allowed to also search) | **DEF** — `catalog/processors/assurance/claim-refute.yaml`; impl pending |

If `claim_refute` is ever implemented with an LLM in the loop, it must declare `model_targets` and the call
discipline of [[../codex/change-verification-contract.md]] applies: it grades a claim it did **not** produce,
and its verdict is evidence for the human, not the final word.

## 2. How they compose — the context-assurance pipeline

The tools are not a menu; they are a **pipeline of seven primitives** with method diversity built into the
order. Each rung is independent of the others' failure modes, and the chain ends in a human and a signature,
not in a model's confidence:

```
Input: claim + candidate corpus object
  │
  ├─ GATHER (multiple independent methods, in parallel)
  │     corpus_integrity_check   — is the doc authentic vs the authority?      [REAL]
  │     corpus_freshness_diff /
  │       authority_fetch_diff   — is it still current vs the live source?     [DEF]
  │     web_search_verify        — is it independently attested outside?       [DEF]
  │
  ├─ CORROBORATE   multi_source_corroborate — do ≥N INDEPENDENT sources agree?  [REAL]
  │                citation_trace           — does every cited fact bind to a source_record? [DEF]
  │
  ├─ REFUTE        claim_refute  — does it survive a hostile counter-case?      [DEF]
  │                              (a DIFFERENT Action from the gatherers)
  │
  ├─ RECONCILE     cross_source_reconcile — authorities conflict? precedence,  [DEF]
  │                              else → HITL (never silently pick a winner)
  │
  ├─ HITL          review_ticket → human adjudicator on any unresolved conflict
  │                              or high-blast-radius determination
  │
  └─ ATTEST        oracle_c2pa_attest — sign the corpus by content_hash AND     [DEF]
                                 record WHICH verdicts above the cert covered
Output: verified context + attestation (verifiable by hash) + the warrant trail
```

Two properties make this the moat rather than a checklist:

1. **Method independence per rung.** Gather uses provenance (function), the live authority (HTTP), and the
   open web (search) — three different failure modes. A poisoned doc fails the function rung; a stale doc
   fails the HTTP rung; an isolated fabrication fails the corroboration rung. No single compromise passes
   all three.
2. **The verdict trail is the warrant.** Every rung emits *why* (which source_record, which field, which
   hash/date delta, which counter-evidence). `oracle_c2pa_attest` records *which of those verdicts the
   certification covered* — so a downstream agent verifying by hash sees not just "signed" but "signed,
   integrity-checked vs source X, fresh as of date Y, corroborated by Z" — and explicitly **not** "proven
   true by the signature." That recorded-but-bounded claim is the honest moat.

## 3. The next wedges worth building

Ranked by the selection test from [[oracle-corpus-and-tooling-map.md]] §D2 — *rules/lists that change faster
than anyone re-indexes, where stale is a legal event* — these are the highest-leverage tools to build after
the four assurance components. All **SPEC** (proposed); each is a new Action, not a re-skin of an existing one.

| # | Tool (proposed) | Method family | Verifies | Why it's a wedge |
|---|---|---|---|---|
| 1 | **sanctions-list delta watcher** | HTTP + function | new/removed/changed entries on OFAC SDN/Consolidated, BIS Entity List, EU/UN since the last snapshot | the **beachhead** at its sharpest: lists already public + machine-readable (no publisher to land), change several×/week, stale = a federal/criminal violation. The freshness-diff specialized to the one domain where the demo writes itself. |
| 2 | **effective-date / version watcher** | HTTP + function | that a cited rule version is the one **in force on the relevant date** (not superseded, not not-yet-effective) | the EU FLR (in force 2027-12-14), AI Act Art.50 (2026-08-02) pattern: the text is right but the *date* is wrong. Generalizes `corpus_freshness_diff` from "did the hash change" to "is this the operative version *as of* date D". |
| 3 | **jurisdiction-conflict detector** | function | when two authorities impose **conflicting requirements** on the same obligation across jurisdictions | the agri-food fragmentation (LkSG + CSDDD + EUDR + RED + FLR) turned into a tool: surfaces the conflict *before* `cross_source_reconcile` adjudicates it — making fragmentation the value, not the failure. |
| 4 | **provenance-chain verifier** | function | the **full C2PA chain** end to end: signature validity, cert trust path, manifest-to-content_hash binding, attestation-registry lookup | the read-side of `oracle_c2pa_attest`: lets *any* agent confirm a corpus's chain by hash without trusting our say-so. Closes the loop from "we signed it" to "you verified it." |
| 5 | **embedding-drift detector** | function | when a corpus's embeddings have **drifted** from the live source's current text enough that retrieval is silently answering from stale vectors | catches the failure mode where the *document* updated but the *index* didn't — the structural cause of "58% update vector indexes monthly-or-less". A freshness check on the vector layer, not just the text layer. |

Build order follows the beachhead: **#1 (sanctions delta)** first — it makes the existing `corpus_freshness_diff`
DEF concrete on the highest-stakes domain and needs no signing relationship to land. **#2 (effective-date)**
and **#4 (provenance-chain)** next, because they harden the freshness and attestation rungs the pipeline
already depends on. **#3** and **#5** follow as the corpus surface broadens.

## 4. What this toolkit does NOT claim (honesty guards)

Carried from [[positioning-v2.md]] and the contract:

- It does **not** out-RAG anyone. Gathering and retrieval quality are table stakes; this toolkit is the
  layer *on top* that checks the corpus is true and current.
- It does **not** assert measured lift the toolkit has not produced. Of the §1 tools, **two are REAL code**
  (`corpus_integrity_check`, `multi_source_corroborate`) and the rest are governed **definitions** (DEF)
  with implementations still pending; everything in §3 is **proposed** (SPEC). The manifests say this in
  their own GOVERNANCE notes — this doc does not inflate them. (The code lane fills DEF→REAL; treat the
  status column as point-in-time.)
- A **signature is not a truth proof**, a **search hit is not authority**, and **no tool grades its own
  output**. Where any of these tools later wraps an LLM, the model's verdict is evidence for the human, not
  the conclusion.

---
*warrant: principle — the change-verification contract (`docs/codex/change-verification-contract.md`:
≥2 independent agreeing sources, no agent grades its own work, provenance ≠ truth) and the canonical
positioning ([[positioning-v2.md]] "verified context, upstream"; [[oracle-corpus-and-tooling-map.md]] §C
three-jobs / §D2 beachhead). Real-vs-spec status verified against the repo at write time:
`scripts/processors/assurance/corpus_integrity_check.py` and `.../multi_source_corroborate.py` exist with a
`run()` entrypoint + self-test (REAL); the other seven `catalog/processors/assurance/*.yaml` manifests
(corpus-freshness-diff, cross-source-reconcile, oracle-c2pa-attest, source-citation-trace, web-search-verify,
authority-fetch-diff, claim-refute) are governed definitions with no implementation file under
`scripts/processors/assurance/` yet (DEF); the §3 wedges are not present in `catalog/` or `scripts/` and are
marked SPEC. Status is point-in-time — re-check the catalog/scripts dirs, since the code lane fills DEF→REAL.
No metrics are quoted that we have not run.*
