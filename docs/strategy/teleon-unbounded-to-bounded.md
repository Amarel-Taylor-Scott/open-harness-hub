# From unbounded & inefficient → most-bounded & most-efficient

> The core motion of Teleon, formalized. Single-source thesis for the deck, the site, and sales — consistent
> language, honest claims, every proof point backed by a runnable proof.

## The thesis (one line)
**Teleon takes a capability from unbounded & inefficient to most-bounded & most-efficient — provably, and only as
far as the requirement needs.**

## Two axes, one motion
- **Bounded** ← unbounded: an open-ended, non-deterministic LLM call → schema-constrained → a **deterministic rule**
  wherever the task allows. The capability stops being a guess and becomes a checkable function.
- **Efficient** ← inefficient: expensive → cheap, slow → fast, token-heavy → compressed, fragile/stale → freshness-
  synced, vendor-locked → portable. The same answer, for a fraction of the cost/latency.

These are the **17 descent axes** (determinism↑, cost↓, latency↓, tokens-in/out↓, llm-usage↓, freshness↑,
verifiability↑, reliability↑, locality↑, specialization↑, privacy↑, reproducibility↑, portability↑, resilience↑,
energy↓, safety↑). A capability descends along them — **auto-tuned to the cheapest variation that still meets the
requirement**, escalating only as far as it must.

## The mechanism (what makes it real)
1. **Self-optimizing unit** — a capability measures itself and auto-applies the best governed method per axis,
   emitting a before→after receipt (e.g. input tokens 49→32, determinism 0.2→1.0, cost $0.07→$0/call, model
   $75→$0/Mtok). *Proof: `check_self_optimizing_unit`.*
2. **Automated setup tuning** — any agentic task (document→schema, entity-resolution, transcription, …) runs a
   tiered method grid: deterministic floor → small model → frontier, cheapest-first, escalate only when the
   requirement isn't met. A document pipeline lands the full schema at **~$0.026 vs ~$0.302 frontier-only (~12×)**.
   *Proofs: `check_document_extraction_cascade`, `check_tunable_task_catalog`.*
3. **The brain runs cheap by default** — the orchestrator/reviewer/distiller-judge default to Ollama GLM-5.2 /
   Kimi-k2.7-code, escalating to a frontier model only when a confidence/quality bar fails. The descent applied to
   the brain itself. *Proof: `check_default_brain_policy`.*
4. **A method for every axis, a module for every method** — 17 dimensions × 65 methods × 115 researched candidate
   modules. *Proof: `check_descent_method_catalog`.*

## The honest line (never overclaim)
- **Fully deterministic where appropriate** (a registry lookup, a rule, a parser) — *and only there.*
- Where determinism is impossible (open-ended generation), descend to a **cheaper-but-still-effective** model — never
  a false determinism claim.
- Every descent is **governed**: proof-gated, lossless (the raw + lineage are preserved), accuracy-floored, and the
  output is a candidate the verification rail dispositions. **serves_truth = false** until a gate says otherwise.

## Why it's the wedge
Models, gateways, and the data-gravity platforms make calls *cheaper* and context *closer*. None of them **prove**
a capability got more bounded and more efficient **without losing correctness.** That receipt — unbounded→bounded,
inefficient→efficient, *provably* — is Teleon.

*Single-sourced in the deck (`architecture/teleon_pitch_deck.json`, the `descent` slide + tagline, live numbers).*
