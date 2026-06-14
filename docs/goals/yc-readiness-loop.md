# YC-Readiness Loop — Codex / Claude Code Max handoff goal

Use this file as the long goal. The `/goal` command should point here:

```text
/goal follow the instructions in docs/goals/yc-readiness-loop.md
```

## Mission

Take Baltor + the portfolio from **"multi-agent-audit-passed, source-authority real, 468 proofs
green"** to **YC-submission-ready and live-demo-ready** — one proof-backed increment per cycle.
**Do not end a cycle on diagnosis only.** Every cycle ships a change that leaves the gate green.

## Read first (do not re-derive)

1. **`docs/codex/yc-readiness-handoff-2026-06-13.md`** — the complete current state: what the audit
   found, the 18 fixes already shipped (each cited by commit + gated), the source-authority design
   (BUILT — do not redo), the "dead SPA is intentional lossless preservation — do NOT delete" finding,
   and the remaining owner-decisions each specced.
2. **`docs/codex/change-verification-contract.md`** — every change carries a warrant. **Design / brand /
   strategy / pricing / vocabulary changes are NEVER a unilateral single-agent call** — prepare them and
   flag for owner ratification; do not auto-merge brand voice.
3. **`docs/research/agent-governance-landscape-2026-06-13.md`** — the sharpened wedge (govern TRUTH, not
   just sign EXECUTION) + the EU-AI-Act-Aug-2-2026 why-now. Use it; re-verify quarterly (this space moves
   in weeks).
4. **`docs/strategy/teleon-baltor-openharnesshub-portfolio.md`** + `architecture/brand.json` — the locked
   architecture/brand. Do not edit `brand.json`.

## The gate (every cycle)

```bash
python3 scripts/baltor_flywheel.py --once       # must end GREEN (>=468 proofs); a new behavior = a new proof
python3 scripts/deploy/preflight.py             # must stay GO
```

A change without a passing proof is not done. Add a `check_*.py` and register it in
`scripts/flywheel_proof_modules.py`. Counts are computed, never hand-typed (no-magic law).

## Work queue (highest-value first; pick the top OPEN item each cycle)

**A. Owner-ratification items (PREPARE the change as a diff/PR, flag for the owner — do NOT auto-merge):**
- **A1 — Applying entity + one sentence.** Converge the 5+ competing one-liners to ONE. Recommendation
  (grounded in the locked Baltor=applied-product decision + the wedge): *"Baltor continuously verifies your
  AI's context is CORRECT — not just current — against authoritative sources, with a portable receipt."*
  Demote Teleon / AI-Done-Right / Open*Hubs to "how it's built." Reconcile `yc-application-draft-2026-06.md`
  + `yc-master-…md`. **Brand voice → owner ratifies the exact words.**
- **A2 — Component-count scope.** `1,045` (6 Action-types) vs `2,655` (all components) are different SCOPES.
  Owner picks which to lead with; then mark it `⟦computed⟧` and wire `build_readme_stats.py` so it can't drift.

**B. Safe factual / engineering increments (ship directly, gated):**
- **B1 — Capture ONE dated `--live` OFAC run** (`scripts/ingest/sanctions_feed_live.py --live`) against the
  real SDN list, store the dated receipt, and cite that specific run — then the deck can make the strong
  "caught a real would-be violation" claim truthfully (today it is a synthetic-fixture conformance test).
- **B2 — Next regulated-fact vertical demos** on the real engine (each a `scripts/showcase_pipelines/*.py`
  with a flip-the-source proof, wired into the gallery + flywheel): FDA drug-labeling claim review; BIS
  export-control screening. Each must REUSE `scripts/artifact_graph/source_authority` so it reinforces the moat.
- **B3 — Extend the source-authority registry** with more authoritative publishers per beachhead (state
  Secretary-of-State corp registries for the M&A/ownership vertical; FDA/BIS domains for B2).
- **B4 — Multi-source corroboration** (the next step past authority CLASSIFICATION): when ≥2 independent
  authoritative sources agree, raise confidence + record it in the receipt. Then the deck can say
  "corroborates across independent sources" truthfully (today it establishes single-source authority).

**C. Production-readiness (owner-gated infra, then agent-driven):**
- **C1 — Cloud deploy** once the owner provides Fly account/billing/`fly auth login`/keys + Cloudflare DNS:
  drive `fly/README.generated.md`. Verify with the container e2e first
  (`POSTGRES_PASSWORD=x docker compose -f deploy/docker-compose.deploy.yml -f deploy/docker-compose.localtest.yml up -d`).

## Laws (carry every cycle)
- **Lossless distillation** — never delete the raw/lineage/held-out/legacy (the `legacy.html` front-ends are
  intentional preservations; never delete them).
- **No magic values** — read counts/ports/ids/dims from their one canonical source; add a drift check.
- **Earned, not assumed** — authority/lift/truth is classified or measured, never asserted; flip-the-input
  must change the verdict (the source-authority + showcase pipelines set this bar).
- **One agent at a time** on the same files — concurrent edits conflict.
- **Verify functionality, not numbers** — prove with end-to-end functional tests (real containers/flows),
  not metric-chasing.

## Reconciliation
When this loop and an older goal/runbook disagree on YC-readiness scope, **this file wins for that scope**;
fix the other. The broad portfolio loop is `docs/goals/aidoneright-portfolio-loop.md` — run that for non-YC
family-polish work.
