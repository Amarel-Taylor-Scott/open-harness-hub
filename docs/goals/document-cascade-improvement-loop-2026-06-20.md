# Goal + loop: improve EVERY surface toward most-bounded & most-efficient (2026-06-20)

> This is a **fully flexible** loop. It is not a fixed queue. Each cycle: ORIENT, then implement the **single most
> defensible improvement on ANY surface** of the three sites + the shared engine. If a path is blocked, switch to
> another high-value path. The document/extraction cascade is **one track among many**, not the whole goal.

**Run it (pick one):**
- One increment in a session: `/goal follow the instructions in docs/goals/document-cascade-improvement-loop-2026-06-20.md`
- Hours/days durable loop (owner-launched, billable): `CLAUDE_CODE_CMD='claude -p' nohup scripts/run_north_star_loop.sh > .agent/logs/runner.out 2>&1 &`
  - stop after the current cycle: `touch .agent/STOP_REQUESTED` · resume: `rm .agent/STOP_REQUESTED`
  - preview the next self-prompt (launches nothing): `scripts/run_north_star_loop.sh --dry-run`
- See the cascade work right now: `PYTHONPATH=. python3 scripts/serve_document_cascade_demo.py --serve` → http://localhost:8088

## The goal
Drive every product surface from **unbounded & inefficient → most-bounded & most-efficient** — provably, and only as
far as the requirement needs. Cover all three sites: **Baltor** (applied context product), **OpenHubForAI** (open
ecosystem + CapabilityTask spec), **AI Done Right** (parent brand). Each increment is **proof-gated** (flywheel GREEN),
governed (candidate≠active, serves_truth=false), and honest (deterministic where appropriate; cheaper-but-effective
otherwise; missing reported, never fabricated).

## The flexible loop (every cycle)
`ORIENT → RESEARCH → PLAN → BUILD → VALIDATE → RECORD → BRANCH → REPEAT`
1. **ORIENT** — flywheel GREEN? what changed? which surface has the highest-value, lowest-blast-radius win right now?
2. **Pick ONE** the most defensible improvement on **any** track below (do not grind a single track if another surface
   is more valuable or the current one is blocked). Decide from repo context — do not stop to ask.
3. **BUILD + VALIDATE** — ship exactly one proof-backed increment (a passing `--self-test` + flywheel GREEN). A new
   proof → register the `(path,name)` tuple in `scripts/flywheel_proof_modules.py` → sync the computed count token in
   `docs/strategy/yc-master-current-state-business-plan-and-pitch.md` → flywheel GREEN.
4. **RECORD + BRANCH** — ledger receipt; refresh `.agent/next-action.json` with the next highest-value target.

## Tracks (a menu, choose by value — NOT a sequence)
- **Extraction / cascade** — measured cheapest-that-meets (done: `check_cascade_measurement`); per-input-type rules
  (email attachments, web→schema, RSS, social); route the LLM tier through the cheap default brain (offline-provable,
  live owner-gated); the demo page (`serve_document_cascade_demo`).
- **Descent engine** — the self-optimizing capability unit; more descent axes/strategies with measured before→after.
- **Capability catalog** — screen governed candidates (gap/lift) from registries/feeds toward promotion-readiness;
  profession deterministic calculators; candidate≠active throughout.
- **Three-site surfaces** — Baltor admin/context-control demos; OpenHubForAI registries + standards interop
  (OKF / native / FtM / SKILL.md); AI Done Right parent pages. Keep copy single-sourced and counts computed.
- **GTM / business** — competitor analysis, hosting/cloud/K8s/serverless/model costs, worker economics, pricing,
  marketing budget, pro-forma financials, fundraising, launch ops (see `docs/strategy/baltor-gtm-fundraising-plan.md`).
- **Hosting / go-live** — close the honest go-live blockers (`check_teleon_go_live_readiness.py`), offline-first.

## LAW: schemas are USER-DEFINED (owner 2026-06-20)
Domain schemas (employment-agency, invoice, …) are fine **only** as code/DB **showcase templates** the user may
**choose** as a starting point. The actual extraction schema is **whatever the user writes** — never hardcode a domain
schema as THE extraction surface. Single source of templates + the `name: class` parser:
`src/teleon/extraction/schema_templates.py` (proof: `scripts/check_schema_templates.py`). Any new "write in a
capability" surface MUST default to user-defined input with templates as an optional, editable prefill.

## Strategies (apply on every track)
Cheapest-first escalation; deterministic spine before the model core; compress-only-when-an-LLM-is-needed; the brain
runs cheap by default (Ollama GLM-5.2/Kimi), frontier only on a failed bar; governance in the sidecar; nothing serves
truth without a gate; lossless (raw + lineage preserved); local-first + OpenAI-compatible model integration.

## Goals (measurable)
- Every selection/cascade decision backed by a MEASURED number (not assumed).
- Every "write in a capability" surface is user-defined-first with optional templates.
- Each cycle: one passing proof + flywheel GREEN; value spread across surfaces over time, not stuck on one.

## Standing constraints (the self-prompt injects these)
The loop does NOT commit/push or touch network/LLM/cloud — it leaves the tree green for owner review; owner-gated items
(live LLM/source calls, hosting, git push) are routed around with a blocker-ledger entry. Teleon never imports Baltor.
One module/cycle for any extraction/reorg. Secrets are env-ref names only (values in gitignored `.env`). Stop only on
`.agent/STOP_REQUESTED`.
