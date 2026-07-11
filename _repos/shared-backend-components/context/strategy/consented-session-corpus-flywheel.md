# The consented-session corpus flywheel — AIDevObserver as the factory's data source

> Owner idea (2026-06-27): with the **explicit permission** of AIDevObserver users (humans, agents, pipelines),
> retain their sessions and mine them to build useful tools, feed the research queue, and standardize reusable
> primitive components into the registries — **so future users don't have to reinvent them**. This is the loop that
> turns AIDevObserver from a product into the **data source that feeds the entire factory**, grounded in real usage.

## Why this is the highest-leverage idea in the architecture

It closes the loop between the four things we already have:
- **AIDevObserver** already *detects* reinvention, footguns, waste, and missed-cheaper-paths in a session.
- The **reinvention guard** already *interrupts* "a solution already exists" — but its grounding is our curated catalog.
- The **registry federation** already *holds* components, and the **research queue** already *ranks* areas to build.
- The **negative-space thesis** says the moat is *what models lack* — and a real session corpus is the truest map of it.

Today AIDevObserver sees someone rebuild `read_rows()` and says "this exists." The flywheel: **capture that
rebuild, standardize it, register it** — so the *next* person's reinvention guard fires with a real, battle-tested
component drawn from how people actually work. More users → more sessions → more standardized components → a better
reinvention guard + research queue → more value → more users. That compounding is **data gravity we own** (the exact
moat the competitive intel flagged as the real threat).

## The load-bearing rail: CONSENT + privacy (make-or-break)

AIDevObserver today is **read-only / nothing-stored**. This flywheel deliberately adds a *retain-and-learn* mode, so
consent is not a footnote — it is the architecture:

1. **Explicit, granular, revocable opt-in.** Off by default. A user / agent / pipeline opts in per *purpose*
   (tool-extraction · research-queue · component-standardization), per *scope* (which projects/sessions), with a
   retention window and a revoke-and-delete. No consent → the existing read-only/nothing-stored path is unchanged.
2. **Redaction before retention.** Secrets, keys, PII, and proprietary content are stripped at capture (reuse the
   BYO-key redaction + `response_redaction` + the `SkillScannerPort` exfiltration/secret signatures). Only what
   survives redaction is retained.
3. **Tenant isolation is absolute.** A tenant's private patterns NEVER become global — the lossless-distillation
   tenant-privacy rule. Only **consented, anonymized, generalizable** patterns are promoted to the *shared* registries;
   everything else stays in the contributor's private space.
4. **Provenance + revocation propagate.** Every derived component carries lineage to the consented sessions it came
   from; revoking consent removes the contribution and its derivations (CDC-style propagation).

Get this right and it is an ethical, powerful flywheel. Get it wrong and it is a trust disaster — so consent is gate #0.

## The pipeline (each stage already has a home — this wires them, it does not rebuild them)

```
 consent gate ──▶ capture+redact ──▶ MINE (observer detectors) ──▶ STANDARDIZE (distill) ──▶ SCAN (security) ──▶ GOVERN/PROMOTE ──▶ registries
   (opt-in)        (redaction +        reinvention clusters →        raw session pattern →      SkillScannerPort     candidate-only +     (reinvention
    per purpose      scanner)           candidate tools/components    governed primitive          ingest gate         provenance +         guard now
    + revoke)                           footgun/waste → guidance      (7-primitive model),        (>=high →            promotion            grounded in
                                        novel pattern → research      LOSSLESS (raw+lineage)      quarantine)          boundary)            real usage)
                                        queue (areas.jsonl)
```

- **Mine** = the observer's *existing* detectors, run over the consented corpus instead of one live session:
  reinvention clusters → candidate tools/components; footguns/waste → guidance + anti-pattern records; novel/unmet
  needs → `data/research-queue/areas.jsonl` (ranked by `scripts/acquisition/research_queue.py`).
- **Standardize** = the determinism-factory / distill-from-verified pattern: a raw, repeated session pattern is
  distilled into a governed **primitive** (Input · Knowledge · If · Action · Loop · Stop · Output) — **lossless** (raw
  + intermediates + lineage + rejected candidates retained; a winner always traces to its losers).
- **Scan** = the `SkillScannerPort` ingest gate already built: a ≥high finding quarantines the candidate (never
  promoted), with the SARIF on its source record.
- **Govern/Promote** = `serves_truth=false` candidate, the existing promotion boundary (review tickets + the security
  gate), distill **from verified only** — a component is promoted from *confirmed* reuse, never raw model output.

## What flows out (the three deliverables the owner named)

1. **Useful tools** — the most-reinvented patterns become first-class tool/component candidates (the highest-signal
   `lift` because real people kept rebuilding them — durable, structural negative space).
2. **Research queue** — unmet needs + recurring blockers feed `areas.jsonl`; the queue ranks where to build next from
   *demand*, not guesswork.
3. **Standardized primitive components** — governed registry records (Knowledge Corpus / If Statement / Action) so the
   reinvention guard, the compose engine, and future users draw on real, scanned, provenance-backed building blocks.

## Connected assets (reuse-first — this is wiring, not new subsystems)

observer router/detectors · reinvention guard (the consumer) · research queue (`research_queue.py` + `areas.jsonl`) ·
registry federation + `records.py` · `SkillScannerPort` + the two scan gates · determinism factory / distill-from-verified ·
the promotion boundary · response redaction + the credential/key redaction · lossless-distillation tenant-privacy.

## Build order (when greenlit)

1. **Consent model first** — the opt-in/scope/revoke record + the gate (no retention without it). This is the contract
   everything else depends on; ship it before any retention.
2. **Consented capture + redaction** — extend `_repos/teleon/backend/src/teleon/observer/capture.py` with a consented-retain path that
   redacts then stores to a contributor-private corpus (tenant-isolated).
3. **Miner** — run the observer detectors over the corpus → candidate tools/components + research-queue entries.
4. **Standardizer** — distill repeated patterns → governed primitives (lossless), scan (ingest gate), promote via the
   boundary into the registries.
5. **Attribution (optional)** — credit/value for contributors whose sessions seed promoted components (the contributor
   flywheel; strengthens opt-in).

serves_truth=false throughout; consented + redacted + tenant-isolated + provenance-tracked; distill from verified only.
