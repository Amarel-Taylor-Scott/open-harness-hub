# Self-reorientation protocol

Run at the start of every working pass (especially a fresh context window). It is why the
goal-loop ships proven increments instead of reinventing existing code.

1. **Re-read the mission** — Baltor is a governed Context Engine (Source → Reconciliation →
   Anti-Fragility → Enhancement → Optimization → Consumption + a universal verification rail). Which
   stage am I touching? Which invariant applies?
2. **Inspect local state** — read `.claude/commands/baltor-goal-loop.md`,
   `.agent/baltor-goal-loop-log.md` (recent receipts), `.agent/flywheel-health.jsonl` (is it green?),
   the relevant `docs/backend/*` + `schemas/*`. **Confirm what already exists before creating it**
   (scouting has repeatedly found existing modules/schemas — e.g. `sanctions_feed.py`,
   `context-object.schema.json` — that must be extended, not duplicated).
3. **Pick the single highest-leverage increment** — prefer the regulated-context beachhead and
   items that close a labeled seam with a real proof. One coherent increment per pass.
4. **State assumptions + blast radius** — what could be stale; which files/consumers are affected;
   backwards-compat risk. Prefer additive changes.
5. **Implement** — additive; behind a capability port if it touches a vendor; real-or-labeled-seam.
6. **PROVE** — a runnable, deterministic, offline self-test (`--self-test`) green + `py_compile`;
   then `python3 scripts/baltor_flywheel.py --once` to confirm nothing regressed.
7. **RECORD a receipt** — append to `.agent/baltor-goal-loop-log.md` (and periodically the ledger):
   goal, files, warrant, commands, proven-vs-seam, next, risks.
8. **Heal red first** — if the flywheel's latest record is RED, fix that regression before new work.

Hard STOP conditions (pause + ask): secrets, destructive ops, real cloud deploys, commits/pushes,
paid resources, breaking changes without a compat layer.
