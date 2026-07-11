# Continuous build loop — goal + runbook (2026-06-20)

The durable runner already exists; this doc is the **goal** it works toward and the **launch** instructions.
The loop is **self-prompting**: each cycle `scripts/loop_prompt_builder.py --emit` regenerates the prompt from
`.agent/next-action.json` (which the running agent updates every cycle), and `scripts/run_north_star_loop.sh`
feeds it to Claude Code, relaunching on exit. **Owner-launched, runs for hours/days, stops only via a file.**

## The goal (this trajectory)

Continue the governed-capability build. The operative task queue lives in `.agent/next-action.json` (the loop
self-prompts from it); the current order:

1. **SKILL.md interop adapter** — adopt the skill standard that won the cross-vendor format war, at the edge,
   parallel to OKF/FtM (round-trip lossless; assurance in the frontmatter; the 4th built standard).
2. **Profession deterministic calculators** — the profession-specific deterministic capabilities the
   profession seeder declared (HTS, ECCN, hours-of-service, DEA schedule, permit-requirement), each a
   correctness-checked If-Statement like the court-deadline calculator.
3. **Model-index freshness binding** — wire the model index to the freshness/CDC runtime so a stale price/
   endpoint is held out and never selected (offline; the live poller stays owner-gated).
4. **Code-graph-driven incremental reorg** — use `scripts/code_graph.py` to emit an impact-ordered plan to
   align files to `architecture/fundamental_primitives_taxonomy.json`; execute one module/cycle **only after
   owner sign-off**, always with a re-export shim + flywheel green.
5. **Factory expansion** — more O*NET/WORKBank professions + screen discovered candidates toward promotion.

## Guardrails (enforced by the self-prompt's standing constraints)

- **Proof-gated:** every increment ships a passing `--self-test` + flywheel **GREEN 525/525** (and rising); a new
  proof is registered in `scripts/flywheel_proof_modules.py` and the computed token is synced.
- **The loop does NOT commit/push or touch the network/LLM/cloud** — it builds + proves green in the working
  tree; the **owner reviews + commits/pushes**. Owner-gated items (cloud hosting, live LLM/source/model pollers)
  are routed around with a blocker-ledger entry, never started.
- **candidate ≠ active; serves_truth=false** everywhere; Teleon never imports Baltor; lossless distillation.
- One module/cycle for any extraction/reorg; redteam after any new surface.

## Launch (owner action — runs hours/days)

```bash
# 1. (optional) confirm the contract + preview the next self-prompt — launches nothing:
scripts/run_north_star_loop.sh --check
scripts/run_north_star_loop.sh --dry-run

# 2. start the durable loop (run inside tmux/nohup so it survives terminal close):
CLAUDE_CODE_CMD='claude -p' nohup scripts/run_north_star_loop.sh > .agent/logs/runner.out 2>&1 &

# stop after the current cycle:
touch .agent/STOP_REQUESTED
# resume:
rm .agent/STOP_REQUESTED
```

`CLAUDE_CODE_CMD` must be your real, authenticated Claude Code invocation (it is billable + long-running, which
is why it's an explicit owner action). `MAX_CYCLES=N` caps total cycles (0 = unbounded). Each cycle's exact prompt
is logged to `.agent/loop/current-prompt.txt`; receipts append to `.agent/baltor-goal-loop-log.md`; resume state
is `.agent/north-star-loop-state.json`. Only one loop at a time.
