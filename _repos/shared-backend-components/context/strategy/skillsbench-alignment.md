# SkillsBench / Skill Lift alignment

**SkillsBench is the field's external proof of the bar we built the registry around.**
BenchFlow's "Skill Lift" benchmark (Kaggle, May–Jul 2026; papers arXiv:2602.12670
SkillsBench, arXiv:2604.05172 ClawsBench) measures one thing: how much a *skill* (a
folder of instructions + scripts + references an agent loads) lifts an agent, paired
**with-skill minus without-skill**, with an adversarial safety gate. That is our
admission criterion, published and peer-reviewed by a third party.

## The mapping is one-to-one

| SkillsBench | OpenHubForAI | Where |
|---|---|---|
| a **skill** (`SKILL.md` + scripts/ + references/) | an **Action** (harness/processor/persona/tool/rubric) | `catalog/harnesses/…`, `scripts/foundry/skillsbench.py` |
| **lift** = Δ pass-rate (with − without) | `pipeline_score − bare_model_score` | `scripts/foundry/measure.py` |
| public→private **generalisation** ("a skill that only works on tasks it has seen is a lookup table") | the **durability** axis (structural, won't close next model) | `scripts/eval/reason_codes.py`, [[two-axis-lift-gate]] |
| **ClawsBench** safety gate (unsafe → score −1.0) | governance: review queues, provenance, deterministic gates | `scripts/foundry/gate.py`, [[governance-is-the-product]] |
| a **task** (instruction + deterministic verifier + oracle) | a **gap** with a measurable verifier | `scripts/foundry/gaps.py` |

## Why their headline numbers are our entire reason to exist

Across 84 expert tasks SkillsBench reports **+16.4pp average lift — but 18 of those 84
tasks get *worse*, and skills a model writes for itself net −1.3pp.** A component can
lift, do nothing, or quietly break. So:

- **Lift must be measured, not asserted** — the two-axis gate ([[two-axis-lift-gate]]),
  the anti-filler factory ([[evidence-driven-factory-no-filler]]).
- **LLM-self-authored components are net-negative** — empirical backing for human
  approval + model-independent gap screening ("the LLM doesn't know what it doesn't
  know"; [[negative-space-corpus-aggregation]]).
- **Capability you can't get safely is worth less than nothing** — governance is the
  product, not a wrapper ([[governance-is-the-product]]).

## What we built (`scripts/foundry/skillsbench.py`)

- **EXPORT** `action_to_skill()` — any catalog Action → a SkillsBench `skills/<slug>/`
  bundle. The procedure is *derived* from the component's real structure
  (input_verification → applied_layers → model_io → output_verification), so the
  `SKILL.md` is genuinely useful, not boilerplate. **Our catalog is submittable to
  Skill Lift today**, and interoperable with the SkillsBench ecosystem.
- **IMPORT** `task_to_evidence()` — a SkillsBench task → our (gap, source, lift) evidence
  triple. A task is a *gap with a deterministic verifier*: lift is measurable by
  construction → `confirmation_source = recorded`, the gold tier. We never fabricate a
  Δ — an unmeasured task is held for measurement (`evidence_to_candidate` ⇒ `lift=None`),
  not promoted. The 94 public tasks are a licensed, externally-measured corpus of exactly
  the negative-space components we admit.

## Acquisition narrative

The two competition tracks are the two halves of this product. **Track 1 (Static Skills)**
is our catalog: measured-lift Actions, exportable and submittable. **Track 2 (Meta-Skills)**
— "skills that write and refine other skills under a budget, without producing unsafe
skills" — *is the foundry itself* (gap → source → construct → measure → gate, with a
safety gate). When an acquirer asks "does this registry actually make models more
capable, provably, without a safety cost?", the answer is no longer our assertion: it is
the metric an independent benchmark publishes, and the harness we can run against it.
