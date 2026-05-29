# North Star (v2, 2026-05-29) — the goal + the execution sequence

Sharpens [[master-goal.md]]'s "database-backed component registry" mission into the **product focus** the
strategy crystallized to this session (canonical positioning: `docs/strategy/positioning-v2.md`). The
component network is the *substrate*; this is *what we sell and build first*.

## The one goal
**OHH = the open, governed harness funnel; the verified-context service (CEaaS) = the business.** The
product is **verified FUEL**, not the harness. We do NOT win as "a better builder" (Contextual's Agent
Composer + LangGraph/Dify/n8n close that — orchestration/actions/governance are table stakes). We win on
the two things they structurally won't be:
1. **Genuinely open** — real OSS, self-hostable, free for the long tail, works with the agent you already
   run. (OHH = distribution + developer goodwill + the consumption surface for verified corpora.)
2. **Verified context, upstream** — *"Most platforms keep your docs CURRENT. We CONTINUOUSLY verify they are
   CORRECT — cross-checked against external authoritative sources, hunting for contradictions before your
   agent cites them."* Adversarial verification + freshness + provenance + oracle publishers, fed into ANY
   agent. (CEaaS = the moat + the monetization.)

**Beachhead:** sanctions & export controls (OFAC/BIS/EU) — rules that change faster than anyone re-indexes,
where stale is a *legal event*, and the lists are already public + machine-readable.

## The execution sequence (aggressive — build, don't re-document)
Each milestone has a **done bar = real code, self-tested, demoable, warrant-gated.**
- **M1 · Verification toolkit** *(in progress)* — verify / adversarially-review / multi-method tools
  (`scripts/processors/assurance/*`): integrity, multi-source-corroborate, web-search-verify, authority-
  fetch-diff, claim-refute, citation-trace. **Done bar:** each tool runs + is verified non-stub.
- **M2 · Sanctions beachhead, end-to-end** — ingest OFAC SDN / BIS / EU consolidated → freshness-diff
  (detect list change) → flag internal context that lags/contradicts the current list → emit provenance.
  **Done bar:** the "stale sanctions list = a federal violation" demo runs offline on a bundled fixture.
- **M3 · CEaaS productization** — the tier pipeline (raw→compressed→hyper-efficient, real) → **serve** into
  an agent via the four surfaces (MCP · llms.txt · skill · CLAUDE.md) → consumption metering. **Done bar:**
  a governed corpus is served into Claude Code in tiered form with a fidelity record.
- **M4 · Measured-lift / fidelity harness** — the credibility + the differentiator (currently THIN): a
  paired pipeline-vs-bare-model protocol scored by a *separate* evaluator, runnable on a fixture now and on
  a live model route when available. **Done bar:** a reproducible lift/fidelity number with a durability class.
- **M5 · Open funnel polish** — OHH OSS: the free build experience + works-with-your-agent + the consumption
  surface for verified corpora. **Done bar:** a dev installs, builds a governed harness, pulls a verified
  corpus, runs it against their own agent — no account.

## Honest current state (real today)
M1 partial: `corpus_integrity_check` (anti-poisoning, real) + assurance component defs + the tier pipeline
(`scripts/enrichment/tier_pipeline.py`) + the Contextual adapters; M1 toolkit + M2/M3/M4 are the active build.
Both products live behind tunnels (`scripts/serve_two_products.sh`). The thin spot to close = **M4 measured
lift** (it's the differentiator AND the acquihire-credibility item).

## How we build it (carried from master-goal + the contract)
Evidence-driven (measured gap + real source + measured lift), no filler, honest counting; warrant before
commit ([[change-verification-contract.md]]); no insurance domains / no real PII; stage only your files.
Run it via the autonomous loop (`/evolve`) + multi-agent build cycles (build → adversarially verify).
