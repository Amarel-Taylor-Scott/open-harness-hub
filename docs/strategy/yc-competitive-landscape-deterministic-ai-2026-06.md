# Competitive landscape: the "deterministic AI" wave (2026-06) and where Teleon/Baltor actually wins

**Status:** web-researched 2026-06-19; honest assessment for the YC narrative. Companion to
`memory/deterministic-ai-startups-probably-pramaana.md`. The point of this doc is to survive diligence, so it
states plainly what is table-stakes, what competitors do *better*, and the one wedge that is genuinely ours.

## The wave is real and funded (this is validation, not a threat to fear)

In a single week (June 2026) two startups raised on our exact thesis:

- **Probably** — $9M seed, a16z (founder Peter Elias). A *"data-science mech suit"*: LLM output validated against a
  **deterministic system that rejects mismatches with source data**, with the **model trained against the
  validator**. Their words: *"the better your harness engineering is, the weaker the model can be."* Runs a model
  *"four classes weaker than frontier"* → local, cheap. = our **distillation + harness + model_downgrade + meta-
  learner**, shipped as one vertical (data science).
- **Pramaana Labs** — $27M seed, Khosla (ex-DeepMind Gemini / ex-Glean team; ex-IRS Commissioner advising). A
  *"compiler for high-stakes AI"*: regulatory rules formalized in **Lean**, a question → formal claim → a
  **machine-checkable proof or the rule violation**, *"won't return unless proved."* Domains: tax, medical,
  cybersecurity, financial compliance. = our **verification + promotion-boundary**, via formal proofs (deeper,
  narrower).

Plus a busy field around them: neuro-symbolic verification (ProofNet++, Z3/SMT, autoformalization, VERAFI), and
**AI gateways** that already do provider-neutral routing + cost caps + policy: OpenRouter, Databricks Unity AI
Gateway, Microsoft Agent Governance Toolkit (OSS), Salesforce/MuleSoft, TrueFoundry, Conductor.

## What is TABLE STAKES — do not pitch these as our edge

- **Provider-neutral model routing + cost caps + runtime policy/governance + audit trails.** Crowded incumbent
  territory (the gateways above). Our objective-driven lane selection + org guardrail policy are *necessary plumbing*,
  not a moat.
- **"Make AI deterministic" in the abstract.** Funded (Probably, Pramaana) and academically active. We are neither
  first nor alone.
- **Formal-proof rigor on a narrow formalizable domain.** Pramaana's Lean proofs are a *deeper* correctness
  guarantee than source-authority + corroboration *on that domain*. We **compose** with this (see below), we do
  not claim to beat it.

## What competitors and gateways explicitly DON'T do (verified, from their own materials)

- OpenRouter's own governance docs: it does **not** cover *"output safety evaluation, deterministic verification,
  answer freshness, source provenance, or fact distillation."* Gateways route + cap + log; they do not assure truth.
- Pramaana's guarantee is **bounded by its formal spec**: a proof is valid only w.r.t. the rules domain experts
  encoded — *"if that specification is wrong, incomplete, or fails to capture an exception, the proof is valid
  within the wrong system."* Their materials say nothing about **keeping the formalized rules current as
  regulations change** — it works with *existing* codified rules.
- Probably validates against source data but not source **currency or authority** (which source, kept how current).

## The wedge that is genuinely ours

**Continuously-current, provably-sourced assurance for CHANGING regulated facts — the layer *above* any model,
gateway, or prover.** Concretely, the things nobody above owns:

1. **Freshness / anti-fragility** (`distill_robustness`): bind a fragile, changing-fact capability to an
   authoritative source on a volatility-matched cadence + CDC re-heal; stale answers held out. This is *exactly the
   limitation Pramaana concedes* — who keeps the proven spec current when the law changes monthly.
2. **Earned source-authority + multi-source corroboration**: prove *which* source is authoritative, not just that
   an answer is internally consistent.
3. **Multi-axis descent as one governed system** — 15 axes (determinism, cost, latency, llm_usage, freshness,
   verifiability, reliability, locality, specialization, privacy, reproducibility, portability, resilience, energy,
   safety) with a meta-learner choosing per capability. Competitors are single-axis (Probably: determinism+cost;
   Pramaana: proof) and single-vertical.
4. **Portable receipts + a governed capability catalog** spanning many domains — vs their one vertical.

## Compose, don't compete (turns rivals into features)

- **Pramaana → a strategy, not a rival.** Lean/SMT formal-proof verification is now one entry in our descent
  strategy registry (`formal_proof_verification`), and it is *strictly broader* in our hands: freshness keeps the
  proven spec current and source-authority proves the spec is the authoritative one.
- **Probably → external validation.** Their *"harness → weaker model"* is the cleanest articulation of our
  `model_downgrade` axis. Cite it.
- **Gateways → substrate.** We ride above any gateway as the assurance layer; we do not rebuild routing.

## Evidence we can show today

- **RuleArena (ACL 2025)** found LLMs fail rule-guided reasoning. Our `scripts/eval/rulearena_benchmark.py` measures
  it: on airline-baggage / tax-bracket / overtime / NBA-trade / late-fee tasks, a **distilled deterministic rule
  fork scores 100% vs ~29% for a bare model — a measured 0.71 accuracy lift**. That is the moat as a number, and
  the seed of the A/B strategy harness that will move the meta-learner's lift off 0.0.
- 2,282 governed capability candidates, 1,996 with descent forks; 15 descent axes; the whole engine deterministic +
  proof-gated (flywheel green).

## Honest risks (own them in the pitch)

- Our breadth is **candidate-stage** (discovery ≠ trust) — Probably ships a product, Pramaana has live domains.
  Convert candidates → proven, customer-facing capabilities.
- The multi-axis menu is **copyable**; the durable moat is the **freshness + provenance + receipts data flywheel**,
  not the menu.
- Meta-learner lift is **0.0 until we A/B-test strategies** on benchmarks like RuleArena (now wired).

**One-line positioning:** *Not "we make AI deterministic." We keep the ground truth current and provable as the
world changes — the assurance layer above any model, gateway, or prover — and we descend each capability along
whichever axis matters (determinism, cost, speed, freshness, verifiability, …), governed and receipted.*
