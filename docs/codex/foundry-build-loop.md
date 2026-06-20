# Foundry Build Loop — a runnable goal for the evidence-driven factory

> **What this is.** A long-horizon, never-stop goal an agent (Claude Code) runs to
> drive `scripts/foundry/` to promote **real, evidence-gated components**, cycle
> after cycle. Slots under `master-goal.md` **P1–P2** (foundation + component MVPs);
> it is the concrete build loop for the factory designed in
> `docs/architecture/evidence-driven-component-factory.md`. **Metric: promoted/day,
> never generated.** Run it with the `goal` skill, or one cycle at a time with
> `/loop` (see "How to run" at the bottom).

## The one rule (do not loosen it)

Every promoted component carries all three: a **measured gap** (the bare model
demonstrably fails), a **real licensed source** (`source_url` + author + license),
and a **measured lift** (`pipeline_score − bare_model_score > 0`). The pipeline
enforces this (`contracts.Candidate.evidence_status`); your job is to **feed it real
material and wire the model/agent seams — never to fabricate a lift or relax the
gate.** Offline, lift is measured from *recorded* answers only; no answers + no model
⇒ unmeasured ⇒ routed to review, never invented.

## Priority ladder — each cycle, do the highest **unblocked** item

**P-A · Keep green (every cycle).** `python -m scripts.foundry.pipeline --self-test`
must pass. If red, fix that first.

**P-B · Wire the real seams, in leverage order** (each is a clean injection point;
offline defaults exist so nothing is blocked-by-default):

1. **Real embedder** (Stage 7 `stage_load.Embedder`) — `sentence-transformers`
   locally, or a hosted route via `scripts/_config` (`EMBEDDING_MODELS`). Flips
   `object_embedding.is_real` → vector-search-ready; unblocks the promotion boundary
   (master-goal gate #6). *Blocked by missing dep? `pip install sentence-transformers`
   or wire the hosted route; if neither, branch to P-B-2.*
2. **Source scout** (Stage 1 `sources.SourceScout`) — real acquisition. Start by
   adapting the existing walkers (`scripts.factory.run_factory` registry:
   NIST · USCode · Wikidata · Wikipedia) + the license filter, one **rich vein** at a
   time. Each scout result must carry a minable `payload`.
3. **Component author** (Stage 2 `construction.Author`) — deterministic extractors
   per source kind first (regulation → Knowledge Corpus entries + Conditional rules;
   API → Action/tool); add a **Claude sub-agent author** for material needing
   judgment. Bodies must be schema-complete (Stage 3 validates).
4. **Lift judge + bare-model prober** (Stages 5/0 `measure.Judge` / `gaps.Prober`) —
   wire a model route / LLM-judge so gaps are confirmed *live* and lift is measured
   *live*. Start where deterministic ground truth exists (exact-id / citation tasks),
   where the `DeterministicChecker` already scores correctly.

**P-C · Run real partitions.** Seed gaps from `data/research-queue/areas.jsonl`
(ranked by `scripts/acquisition/research_queue.py`), one partition per source vein,
≤1k per partition (the ledger proved 1k is seconds, 10k monolithic hangs). Promote
what clears the gate; route the rest to review.

**P-D · Widen veins + scale the fleet.** `Foundry.run_fleet({...})` over many
partitions, holding the model-call budget (`FoundryConfig.model_call_budget`). Grow
toward the 10k-**promoted**/day target only once P-A/P-B hold.

## The per-cycle loop (~20–40 min, never stop)

```
ORIENT   → tail data/foundry-ledger.jsonl + `git status`; run the e2e self-test;
           pick the highest-value UNBLOCKED ladder item.
PLAN     → state the ONE durable change this cycle produces.
BUILD    → real, no-shortcut implementation. Keep deterministic stages real;
           respect the seams; never fabricate a lift.
VALIDATE → affected module --self-test + the e2e pipeline --self-test stay green.
           If you touched catalog/schemas, run the fast-path (validate.py changed paths).
RECORD   → append ONE funnel line to data/foundry-ledger.jsonl (schema below).
           Report PROMOTED, never generated.
BRANCH   → blocked (no API key, missing dep, slow/again-rate-limited source)?
           switch to the next unblocked item; note the roadblock + fallback; DO NOT end.
REPEAT.
```

## Gates (a cycle that fails any of these is not "done")

- e2e `pipeline --self-test` green.
- **Anti-filler invariant:** every promoted candidate passes `evidence_status()`.
- **No fabricated lift:** offline scores recorded answers only; otherwise unmeasured → review.
- **Promotion boundary:** nothing tenant-visible with an open/high-risk review ticket,
  a placeholder embedding, or unresolved provenance.
- **No magic values; no real PII/secrets; no insurance work** (carry-overs from `CLAUDE.md`).

## Ledger — `data/foundry-ledger.jsonl` (one JSON line per cycle)

```json
{"date":"2026-05-28","cycle":1,"partition":"esg-csddd","ladder_item":"P-B-2 source scout",
 "funnel":{"areas_probed":40,"gaps_confirmed":31,"sources_found":28,"drafts_built":140,
           "standardized":138,"novel":120,"lift_measured":96,"promoted":71},
 "promoted_ids":["knowledge-pack/...","rule-pack/..."],"blocked":null,"notes":"…"}
```

The day's **yield = sum(promoted)** across cycles. Generated/built are diagnostics, not the score.

## Commands

```bash
python -m scripts.foundry.pipeline --self-test     # end-to-end proof (must stay green)
python -m scripts.foundry.pipeline --demo          # print the funnel ledger for the fixture
python -m scripts.foundry.<stage> --self-test      # any single stage (gaps|sources|…|gate|stage_load)
```

## How to run

- **Autonomous (hours/days):** invoke the `goal` skill — it reads `master-goal.md`
  (this loop is its P1–P2 build path) and runs ORIENT→…→REPEAT without stopping.
- **One increment at a time / on a cadence:** use `/loop` (self-paced) or
  `/loop 45m …` with the one-cycle prompt (see the chat message that delivered this file).
- **Stop condition:** none by design — it branches on every block. Interrupt to redirect.
