# ADR 0004 — "Expectation Constructs" map to CapabilityTask (external validation, not a new primitive)

## Status
Accepted (2026-07-04). Supersedes nothing; superseded by nothing. Vocabulary adoption (using the phrase
"Expectation Construct" publicly) is **owner-gated** — this ADR records the crosswalk, not a rename.

> This record itself follows the law it affirms: decision records are **superseded, never rewritten**
> (`standards/CHANGE-VERIFICATION.md`, `LOSSLESS-DISTILLATION.md`, `ARCHIVAL-MOVE-NEVER-DELETE.md`). If a later
> decision changes this, add ADR 000N with `Supersedes: 0004` and set this one's status to `Superseded by 000N`
> — do not edit the call out of this file.

## Context
An external framing is circulating ("Expectation Constructs — the missing primitive in agentic AI"): the durable
unit is **Work · Skills · Check · Limits · Handoff**, and "the construct, not the framework, is the asset" —
RAG/ReAct/loops/evaluators/swarms/graphs are replaceable tactics. Adjacent posts push the same direction:
agent **accountability/ownership** ("who owns the outcome when the agent acts?"), and **ontologies** returning to
"ground AI in business meaning." We assess these against what we already own (reuse-first, discovery ≠ trust).

## Decision
1. **Affirm, don't duplicate.** "Never rewrite a decision record — supersede it" is already law here; no new rule
   is added. The ADR log + the three standards are the mechanism.
2. **Record the crosswalk.** The "Expectation Construct" *is* our **CapabilityTask / PurposeTask** — we built the
   thing before this name for it circulated:

   | Expectation Construct | = our element | Lives in |
   |---|---|---|
   | **Work** — what must be produced | PurposeTask objective / CapabilityObjective | teleon (`PurposeTask`) |
   | **Skills** — which capabilities may be used | the component/primitive registry + `ImplementationCandidate`/`RuntimeBinding` | shared-backend-components (registry, primitives) |
   | **Check** — what proves completion | `EvidenceLedger` + `PromotionGate` + two-axis lift gate + verify-the-verifier | teleon + eval-harness |
   | **Limits** — where autonomy stops | `OrgGuardrailPolicy` + `BoundaryApproval` + adaptation ladder (L0–L3 auto / L4–L5 human) + `forbidden_autonomous` | teleon |
   | **Handoff** — what context survives | context packs/memory + receipts/lineage + `AIDONERIGHT-UNIVERSE.md` edges | context-injection + the seams |

   And the tactics it names are exactly our **replaceable paths behind one construct** (multi-path law +
   agnostic adapters): RAG → retrieval-injector · ReAct → runtime-selector · evaluators → EvidenceLedger/gate ·
   loops → re-benchmark/retry · swarms → worker fleet · graphs → primitive composition edges.
3. **Accountability + ontologies are validators, not new work.** "Who owns the outcome" = our `BoundaryApproval` +
   warranted-change ownership + `serves_truth=false` boundary. "Ontologies ground AI in business meaning" = our
   `registry_ontology.json` + surface-registry (ontology fragmentation is already logged as the #1 registry risk).
4. **Vocabulary stays canonical.** `CapabilityTask`/`PurposeTask` remain the names (naming law). "Expectation
   Construct" is usable as an **external synonym in positioning/GTM** to meet the market's language — adopting it
   publicly is an owner decision, not a unilateral rename.

## Consequences
External validation that the thesis holds ("the construct, not the framework, is the asset" = our
primitives/CapabilityTask are the product; frameworks are replaceable tactics). A ready positioning bridge for
buyers who speak "Expectation Constructs." No code, schema, or public-vocabulary change without owner sign-off.

## Enforcement / links
`standards/CHANGE-VERIFICATION.md`, `LOSSLESS-DISTILLATION.md`, `ARCHIVAL-MOVE-NEVER-DELETE.md` (the supersede law);
the CapabilityTask model in `teleon/context/` + `contracts/surface-registry.json` (the capability catalog).
