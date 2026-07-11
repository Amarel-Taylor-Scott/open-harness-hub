# Token-savings economics + per-seat business plan (owner-requested 2026-07-07)

> **⚠ RECONCILED 2026-07-09 — the 47.5% / 4.7–5.9× headline figures below are PROJECTION** built on savings scenarios
> the 2026-07-08/09 executed experiments did NOT robustly reproduce. Single-shot token savings are prompt/model-dependent;
> the only robust 0-token win is deterministic composition; realistic sessions are input-token-dominated. Treat this as a
> scenario model, NOT a bankable claim. Current handoff + honest ledger: `../HANDOFF-GPT-5.6.md`, `../REAL_SAVINGS_NUMBERS.md`.

> Every number below is labeled MEASURED (receipt exists) or ASSUMPTION/PROJECTION. The canonical savings
> measurement is the orchestrated/planned-lane contract
> ([orchestrated-lane-savings-contract.md](../codex/orchestrated-lane-savings-contract.md)); proxy numbers
> are supporting evidence. Prices in USD; token prices move — recompute before quoting externally.

## 1. What is MEASURED today

| Number | Value | Receipt |
|---|---|---|
| Real bare-vs-planned completion tokens (GLM 5.2, kaggle, 2 turns) | 20,300 → 10,657 (**47.5% avoided**, 14 primitives reused) | `data/dev-intel/real_buildout_ab/` — quality gate NOT yet passed (sandbox deps), so not yet bankable |
| Real-session redundancy (actual Claude Code logs, this repo) | **27.5%** of tool activity repeated | `session_redundancy.py --demo` |
| Proxy 300-session wave (SaaS/ML/Kaggle/large-org, code-state axis) | **4.73×** base registry / **5.92×** with packs; 65.9M tokens saved / 300 sessions (~220K/session) | `data/dev-intel/realistic_session_benchmarks/runs/` (labelled proxy: modeled output budgets, real retrieval) |
| Difficulty-gated routing | −31% vs always-LLM | `workload_token_receipt.json` |
| Repeat-heavy day with results cache | 98% of retrievals at 0 tokens | same |

## 2. Per-developer baseline (ASSUMPTIONS, tiered)

Blended token price assumption: **$5.5/M** (agentic mixes are input-heavy: ~80% input at ~$3/M + ~20%
output at ~$15/M on Sonnet-class lanes; cheaper lanes exist — this is deliberately mid-market).

| Tier | Sessions/mo | Baseline tokens/mo | Baseline spend/mo |
|---|---|---|---|
| Standard AI-assisted dev | 40 (2/workday) | 10M | ~$55 |
| Power user (agentic-heavy) | 40 larger sessions | 36M | ~$200 |

(Both consistent with observed real-world agentic-coding spend ranges.)

## 3. Savings scenarios (rate × baseline)

| Scenario | Rate | Basis |
|---|---|---|
| Conservative | 25% | ONLY quality-gated mechanisms extrapolate: measured input redundancy (27.5% addressable → ~20% net) + planned-lane savings on library-covered turns at TODAY'S coverage (71 executable primitives) |
| Moderate | 60% | planned-lane 47.5% measured on covered turns + proxy input-side effects at partial realization |
| Aggressive | 80% | full proxy benchmark ratios (4.7–5.9×) realized — requires library coverage at scale (the 20K-project grid + minting flywheel) |

## 4. 10,000-developer adoption (PROJECTION)

Aggregate baseline: 10K devs × 10M tokens = **100B tokens/month** ≈ $550K/mo ≈ **$6.6M/yr** (standard tier);
power-user tier ≈ **$24M/yr**.

| Scenario | Savings/yr (standard tier) | Savings/yr (power tier) |
|---|---|---|
| Conservative 25% | $1.65M | $6.0M |
| Moderate 60% | $4.0M | $14.4M |
| Aggressive 80% | $5.3M | $19.2M |

Non-token savings (not priced above, real in sales conversations): fewer broken generations to review
(planned lane compiled where bare didn't), faster sessions (less context re-reading), and the audit trail
(receipts per composition) that pure-LLM coding lacks.

## 5. Per-seat business plan (large development shops)

- **Pricing anchor:** charge 20–30% of realized savings, floored/capped into a familiar per-seat band.
  Standard tier saves ~$33/mo at the moderate scenario → **$19–29/seat/mo**; power tier saves ~$120/mo →
  **$39–59/seat/mo premium band**. Market-normal (Copilot Business $19, Enterprise $39; Cursor $20–40) —
  we price INSIDE the familiar band while the pitch is savings-backed, not vibes-backed.
- **Revenue at 10K seats:** $25/seat → **$3.0M ARR**; blended with premium seats → **$3.5–4.5M ARR**.
  Motion: 5–20 large shops of 500–2,000 seats, not 10K individual sales.
- **The receipt IS the sales instrument:** AIDevObserver runs on the shop's own consented sessions →
  measures THEIR redundancy and savings → the pilot report is their own data (GTM law: AIDevObserver leads).
  Per-tenant savings metering ships with the keyed MCP transport (roadmap Tracks 2/4).
- **Tiers:** free open-core (MCP installer + public registry, the funnel) → team per-seat (governed registry,
  savings receipts, support) → enterprise (private per-shop registries, their fixes minted as THEIR
  primitives, SSO-less per-product auth per design law, compliance/audit exports).
- **COGS / margin:** serving is deterministic local-first (SQLite/pgvector + CPU embedders; zero LLM tokens
  on the deterministic path) → software gross margin >90%. Main real costs: library-growth minting compute
  (cloud LLM verification), support, and the eval fleet.
- **Moat (existing strategy, reinforced):** the verified executable library + per-shop composed-primitive
  candidates = governed data that compounds; usage → glue-dominated turns → minting targets → higher
  avoided-generation fraction → higher realized savings → stronger renewal. Savings proof and registry
  growth are the same loop.

## 5b. Prosumer segment: Claude Code / Codex SUBSCRIPTION users (owner-added 2026-07-07)

Subscription users (~$100–200/mo Max-class plans) pay FLAT — so the pitch is not a smaller bill, it is
**more work per cap**:

- **The binding constraint is the usage limit** (per-window + weekly caps), not the invoice. Measured
  47.5% completion avoidance (planned lane) ≈ ~2× buildouts per cap window; proxy ratios imply more.
  "Your $200 plan does 2–5× more" is the one-line pitch.
- **Secondary value:** faster turns (less generation), fewer broken generations to redo (planned compiled
  where bare didn't), receipts/audit trail for their own work.
- **Pricing:** $15–29/mo add-on — a 10–15% add-on to a $200 plan for a capacity multiplier is an easy
  self-serve sell; annual $150–290. At 25K prosumer subscribers × $19 avg → **~$5.7M ARR** with zero
  enterprise sales cycle.
- **Distribution = the Track-3 installer:** pipx/uvx + one MCP config entry into `~/.claude.json` /
  Codex config — works with BOTH Claude Code and Codex (cross-tool neutrality is a feature the platform
  vendors won't ship for each other). Freemium: public registry free (the funnel), paid = verified/governed
  lanes, private registries, savings receipts.
- **Strategic role:** the PLG wedge under the enterprise motion — prosumers adopt bottom-up inside large
  shops, AIDevObserver pilots convert the shop to per-seat (the Cursor-style path).
- **Platform risk, stated honestly:** Anthropic/OpenAI could bundle registry-like features; mitigations are
  cross-tool neutrality, per-shop PRIVATE registries (their fixes = their moat, not the vendor's), and the
  governed/verified layer (our moat is the data discipline, not the retrieval trick).

## 6. What must be true before quoting these numbers externally

1. Planned-lane receipts pass the QUALITY gate on ≥3 scenario families (fix sandbox deps; run
   standardization/schema.org-domain scenarios where coverage is now strong).
2. Input-side savings measured live (prompt-cache alignment + never-resend-unchanged) on real sessions,
   not proxy.
3. A pilot-shape report: 5–10 real projects, bare vs planned, tokens + quality + wall-time, generated
   entirely from receipts.
