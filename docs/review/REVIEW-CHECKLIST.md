# Baltor — Review Checklist (run this each evaluation)

Purpose: let you (the owner) **independently verify progress** rather than trust a "green" claim.
Every item is a command YOU can run. Self-tests prove contracts; the **C** section exercises REAL
data so progress isn't circular. Generate a filled, timestamped copy any time with:

```bash
python3 scripts/make_review_pack.py     # → e2e/artifacts/review-pack/REVIEW-latest.md (+ dated)
```

Servers (only needed for the live/visual rows):
```bash
PYTHONPATH=. nohup python3 scripts/baltor_admin_demo_server.py --port 9307 &   # live API + /dashboard
cd web/baltor && python3 -m http.server 8000 &                                 # static console
```

---

## A · Foundation stays green
- [ ] **Every proof contract passes.** `PYTHONPATH=. python3 scripts/baltor_flywheel.py --once`
  → expect `flywheel GREEN N/N`. **N must be ≥ the last review's N** (it grows as proven modules are
  added; today N = 41). A `GREEN N/M` with N≠M means something broke — read which proof.

## B · The connected system is actually wired (not just claimed)
- [ ] **All engines emit onto one bus, byte-identical without a bus.**
  `PYTHONPATH=. python3 scripts/check_event_integration.py --self-test` → expect `… modules CONNECTED`
  (today: **Nine**). The "byte-identical without a bus" assertions prove the wiring is non-breaking.
- [ ] **The pipeline fires live end-to-end** (spawns a real HTTP server, POSTs the pipeline, reads
  real SSE events back). `PYTHONPATH=. python3 scripts/check_live_pipeline.py --self-test` → `PASS`.
- [ ] **(Optional, by hand) hit the live server yourself:**
  `curl -s -X POST http://127.0.0.1:9307/api/demo/run-full-pipeline` → `{"ok": true, "answer_value": 5, …}`
  then `curl -s 'http://127.0.0.1:9307/api/events?limit=500'` → expect 21 distinct event kinds incl.
  `verification.started/completed`, `source.received`, `contradiction_found`, `context_lift.calculated`.

## C · Real-data output (the anti-circular section)
- [ ] **Design-token drift reporter runs on the ACTUAL CSS.**
  `PYTHONPATH=. python3 scripts/check_design_tokens.py` → lists the real drifting palette tokens
  (today: 11). This is No-Magic-Values applied to CSS — a real problem surfaced, not a synthetic pass.
- [ ] **Memory Block reconciles a real decision log.** Feed it your own decisions and confirm it pins
  the latest, supersedes the earlier, and keeps lineage:
  ```bash
  PYTHONPATH=. python3 -c 'from scripts.context_memory_block import build_memory_block as b; \
  print(b([{"decision_id":"x1","key":"k","value":1},{"decision_id":"x2","key":"k","value":2,"supersedes":"x1"}])["pinned"])'
  ```
  → expect `{'k': 2}` (latest wins; `x1` superseded).
- [ ] **Sanctions flow CATCHES a would-be violation + holds it out, with provenance.**
  `PYTHONPATH=. python3 scripts/pipeline/verified_context_flow.py --self-test` → look for
  `would_be_violation … HELD OUT of the served corpus` (the stale "clear" on a newly-listed entity).

## D · Visual evidence (look at it; re-record if stale)
- [ ] Re-record: `cd e2e && BASE=http://127.0.0.1:9307 node record_dashboard.mjs` (16/16) and
  `BASE=http://localhost:8000 node record_demo.mjs` (15/15).
- [ ] **Live dashboard** `e2e/artifacts/dash-03-after.png` / `live-dashboard.gif` — confirm: ≥10 live
  events streamed, ≥1 stage card "hot", **Measured lift > 0**, **Answer = 5**, **Pack tokens shows a
  real `N→M`** (not `undefined`), the artifacts panel shows a `verified flow …` line.
- [ ] **Console** `02-acme-ran.png` / `06-cfpb-ran.png` / `07-reviews.png` — graph renders, lift bars
  present, review queue shows demo-local reviews.

## E · Honesty / no-regression (the bar beyond "it's green")
- [ ] **No canonical mutation** — the review queue says decisions are demo-local; applying is a
  separate grant step. (Visible on `07-reviews.png`; asserted in the swarm self-test.)
- [ ] **Working tree only** — `git status` should show no unexpected commits/pushes (the loop never
  commits).
- [ ] **Receipts match reality** — skim the last entries of `.agent/baltor-goal-loop-log.md`; each
  claims specific files + commands you can re-run. If a receipt's claim doesn't reproduce, that's the
  signal to dig in.

## F · What's deliberately NOT done (owner decisions — should stay parked)
- [ ] Compliance **positioning / site copy** — unchanged unless you steered it.
- [ ] Canonical **palette convergence** — `check_design_tokens.py` still REPORTS (exit 0), is not a
  CI gate, and no `tokens.css` has been imposed. (These are brand decisions; the loop must not make
  them unilaterally — see `docs/codex/change-verification-contract.md`.)

---
**Red flags to escalate:** flywheel N dropped or shows N≠M · "modules CONNECTED" count fell · a C-row
produces no real output · a screenshot is stale/missing · a receipt claim doesn't reproduce · any
commit/push appeared · a parked owner-decision item changed without your say-so.
