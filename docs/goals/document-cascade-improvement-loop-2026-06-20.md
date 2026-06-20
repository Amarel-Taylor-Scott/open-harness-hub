# Goal + loop: improve the document/extraction cascade toward most-bounded & most-efficient (2026-06-20)

**Run it (pick one):**
- One increment in a session: `/goal follow the instructions in docs/goals/document-cascade-improvement-loop-2026-06-20.md`
- Hours/days durable loop (owner-launched, billable): `CLAUDE_CODE_CMD='claude -p' nohup scripts/run_north_star_loop.sh > .agent/logs/runner.out 2>&1 &`
  - stop after the current cycle: `touch .agent/STOP_REQUESTED` · resume: `rm .agent/STOP_REQUESTED`
  - preview the next self-prompt (launches nothing): `scripts/run_north_star_loop.sh --dry-run`
- See it work right now: `PYTHONPATH=. python3 scripts/serve_document_cascade_demo.py --serve` → http://localhost:8088

## The goal
Drive the document/extraction capability (and the descent engine behind it) from **unbounded & inefficient → most-
bounded & most-efficient** — provably, and only as far as the requirement needs. Every increment is **proof-gated**
(flywheel GREEN), governed (candidate≠active, serves_truth=false), and honest (deterministic where appropriate;
cheaper-but-effective otherwise; missing reported, never fabricated).

## The plan (task queue — the loop self-prompts these in order)
1. **Close the measurement loop** — give the cascade a real per-stage accuracy/coverage signal (eval fixtures per
   schema field), so "meets requirement" is MEASURED, not assumed; the cheapest-that-meets choice becomes a live A/B.
2. **Per-input-type extract rules** — email-attachment recursion, web-page→schema, RSS per-item, social-post fields;
   each a deterministic acquire + the shared extraction cascade (extend `input_acquire` + `document_extraction_cascade`).
3. **Wire the cheap default brain as the LLM tier** — route the cascade's LLM stage through the Ollama default brain
   (GLM-5.2 / Kimi-k2.7-code via `default_brain`), escalating to frontier only on the bar; the live call is
   owner-gated (OLLAMA_API_KEY in `.env`) — keep an offline path for the loop.
4. **PR-as-fork for every cascade improvement** — open a capability PR (`capability_pr`) carrying the eval-lift Δ;
   merge ONLY if it lifts within policy (the eval gate is the CI check).
5. **Expand the tunable-task + modality catalogs** with measured cascades; screen new candidate capabilities
   (gap/lift) from the registries/feeds toward promotion-readiness.
6. **Demo polish** — extend the local page with an input-type selector + a PR-fork view; keep it fully working.

## Demos (already runnable; keep green)
- `scripts/serve_document_cascade_demo.py --serve` — write in a capability, watch the cheapest-that-meets cascade.
- `scripts/build_pitch_deck.py --build` — the deck (live numbers, the descent slide).
- `dist/sites/opencontexthub/capability-repo-demo.html` — the GitHub-familiar PR/checks/merge view.

## Adjustments / strategies
- Cheapest-first escalation; deterministic spine before the model core; compress-only-when-an-LLM-is-needed.
- The brain runs cheap by default (Ollama), frontier only on a failed bar.
- Governance rides in the sidecar; nothing serves truth without a gate; lossless (raw + lineage preserved).

## Goals (measurable)
- Every cascade decision backed by a MEASURED accuracy/coverage number (not assumed).
- ≥9 input types with real per-type extract rules; ≥13 tunable tasks with measured cascades.
- Each improvement lands as a passing capability PR (lift Δ ≥ 0, within policy) + flywheel GREEN.

## Standing constraints (the loop honors these; the self-prompt injects them)
Proof-gated every cycle (a NEW proof → register in `scripts/flywheel_proof_modules.py` → sync the computed token →
flywheel GREEN). The loop does NOT commit/push or touch network/LLM/cloud — it leaves the tree green for owner
review; owner-gated items (live LLM/source calls, hosting) are routed around with a ledger entry. Teleon never
imports Baltor. One module/cycle for any extraction/reorg. Stop only on `.agent/STOP_REQUESTED`.
