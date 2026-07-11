# Fork & variation generation rigor (owner law, 2026-06-23)

> For **every** component — an architecture decision OR a single registry row, no matter how big or small — don't
> commit the first answer. **Generate forks and variations, ask the variation questions, then choose.** This
> corrects two of my lapses in one: (1) I committed first answers without enumerating alternatives, and (2) when
> told to "ask questions and generate forks," I wrongly collapsed it into a "prefer local" preference. **Local is
> ONE fork to generate and evaluate — never the default.** The discipline is the forking, not any one winner.

## The questions — ask them for everything

**For an architecture / solution choice, generate the forks:**
- What are *all* the ways to do this? Is this the **best**? the **only**? (almost never)
- A **local** way? a **cloud** way? an **open-source model/library**? a **hybrid**? a **deterministic** one?
- (and for a key specifically: do we *really* need it? *why*? can we do it **without** — locally / open-source / deterministically? if needed, BYO + keyless fallback.)

**For a registry ROW / data record, generate the variations:**
- What **variations** of this exist?
- Are there **industry-specific** variations? *How would this vary for healthcare / finance / legal / government / …?*
- How does it vary by **region / scale / regulatory regime**?
- What alternative **approaches** implement it (deterministic / ML / LLM / hybrid)?

Then pick with a stated reason — and where the choice is runtime, keep the forks behind a **policy** rather than
baking one in (see below). Generated forks are governed **candidates** (discovery ≠ trust), never asserted.

## Two mechanisms (built)
- **Forks of an ADAPTER → `registry.plane`** — a plane of candidate adapters selected by a **policy**
  (`local_first` | `keyless_first` | `cheapest` | `best_quality` | …), descending to the first available. The
  flexible alternative to hardcoded `best_X()` wrappers: add an adapter by appending a `Candidate`, add a
  preference by registering a policy; `select()` never changes. `local_first` is just one policy among many.
- **Forks of a ROW → `registry.variations`** — for any record, `variations_of(rec, axis)` /
  `expand_record(rec)` emit governed candidate variations along **industry / region / scale / approach**, plus
  `fork_questions(rec)` (the questions, made explicit per-record). E.g. `contract_review` →
  `{healthcare, finance, legal, government, …}` variants.

## The standing rule
- Never commit the first answer to anything substantive without **enumerating its forks/variations** first.
- Hold runtime choices as a **plane + policy**, not a baked-in branch.
- Generate **industry/region/scale/approach variations** for records as candidates to verify + populate.
- A specific fork (e.g. local, or a cloud key) wins only with a **stated reason** for *this* case — not by default.

Carry with the other laws: [no-magic-values](no-magic-values.md), [change-verification-contract](change-verification-contract.md),
[lossless-distillation](lossless-distillation.md).

> Note: an earlier draft of this file was titled "local-first decision rigor" — that was my over-narrow read.
> The law is fork/variation generation; local-first is one fork.
