# Value propositions — what every surface must say

The single source of truth for the product's promise. The `/polish` loop pulls from this to
make each screen *sell*, not just function. Lead with the proof, not the feature.

## The one line

> **Add the capability your base model lacks — measured against it, governed, and mostly
> freezable, so you add capability without adding cost.**

## The four load-bearing claims (the spine of every surface)

1. **Measured lift, never asserted.** Every pipeline shows `▲ +Δ` capability lift over a bare
   model on a held-out task. A component is admitted only if it lifts *and* the lift is
   structural (won't close when the next model ships). Lift is **pipeline-level**; a component
   shows "where it fits," not a number. (Externally validated by the SkillsBench "Skill Lift"
   benchmark — same metric: paired with- vs without-skill. See `docs/strategy/skillsbench-alignment.md`.)
2. **Governance is the product.** Provenance on every fact, signed/verified publishers, live
   corpora with CDC freshness + revocation, accountable signer, auditor-grade attestation. This
   is the moat a bigger model can't copy. (`docs/codex/...`, `[[../strategy/skillsbench-alignment.md]]`.)
3. **Freezable = no recurring cost.** Most lift is deterministic (Conditionals, rule-packs,
   retrieval, citation gates) and freezes into the exported bundle — you pay model cost only for
   the one or two real Action calls. "More lift, cost barely moves."
4. **Open-core, no lock-in.** The spec, the seven-primitive grammar, the SDK/CLI, and the
   export emitters (SPDX/C2PA/JSON-LD/EU-AI-Act) are free and Apache-2.0. The paid layer is the
   vetted components, the live governed knowledge, build-on-demand, and attestation renewal.

## Why we beat the alternatives

- **vs. a bigger/instruct-tuned model:** we target the *negative space* — where base models
  hedge or fabricate (volatile regs, sparse domains, non-English). Our lift is over the best
  model, and it's governed + cited.
- **vs. prompt/skill libraries:** ours are *measured* (lift + safety-gated), versioned, and
  carry provenance — not a folder of untested instructions (16pp of SkillsBench tasks *regress*
  with careless skills; we gate that out).
- **vs. fine-tuning / LoRA / cheap inference-time methods** (e.g. closed-form controllers,
  reasoning-by-sampling — see `docs/strategy/inference-time-capability-watch.md`): when capability
  gets cheap to *add*, the scarce thing becomes *which* capability is real, durable, safe, and
  sourced. Those methods become **components we host and govern**, not competitors.

## Per-surface lead (first screenful must land this)

| Surface | The line it leads with |
|---|---|
| `/` Landing | "Describe a task. Lift the pipeline, not the bill." — bare entry box; capability you can't get from the model alone. |
| `/preview` `/results` | Three flows, **lift-led**; cost shown as low/med/high; "most lift is freezable → zero recurring." |
| `/flow` | The structure *is* the value: Conditionals route, Knowledge feeds one Action call, the loop refines — **if → then** nesting, one model call per item. |
| `/c/:slug` | Pipelines: the lift number + provenance + cost & portability. Components: where it fits + license + lifecycle. |
| `/freshness` `/attest` | The recurring-revenue moat: primary-source gov feeds, CDC + revocation, signed valid-through attestation. |
| `/foundry` | Credibility: components are **promoted on evidence, never generated** — show the funnel + reject log. |
| `/improve` | The wedge: paste your pipeline → measured before/after (lift, cost, governance). |
| `/pricing` | The open-spec ↔ governed boundary made explicit: free to build/export, paid to govern + keep fresh. |

## Words

Say **components / subcomponents**, **Knowledge Corpus**, **Conditional**, **Action**, **lift**,
**freezable**, **provenance/governed**. Avoid "manifest/artifact," "knowledge pack," "rule pack,"
and any asserted-but-unmeasured capability claim. Numbers are real or labelled `sample`.
