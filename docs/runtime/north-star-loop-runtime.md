# North-Star Loop Runtime — run + improve the loop forever, safely

A self-prompting runtime that runs the `/claude-code-max-north-star-execution-loop` continuously: each cycle the
agent records the next target in `.agent/next-action.json`, a builder turns that into the next cycle's prompt, and
either a **Stop hook** (in-session) or the **durable runner** (across sessions) feeds it back — so the human no
longer hand-pastes the giant prompt. The loop keeps picking the next gap and shipping one proof-backed increment.

Proven by `scripts/check_loop_runtime.py` (flywheel-registered). Everything is **off and harmless by default** —
nothing runs until the owner opts in.

## Three layers

1. **Self-prompt builder — `scripts/loop_prompt_builder.py`** (this is "Claude creating the prompts")
   - `--emit` regenerates the next cycle's `/loop` prompt FROM `.agent/next-action.json` (`next_target` + `then` +
     `resume`) + the live flywheel status, wrapped in the fixed standing constraints, the STOP contract, the
     watchdog/flywheel discipline, the hard-won shim-extraction lessons, and an **anti-slop / anti-fake-progress
     gate**. Only the *variable target* comes from state — every invariant is always carried, so a cycle can't drift.
   - The agent updates `next-action.json` every cycle → that becomes the next prompt. The loop writes its own goal.
   - `--self-test` proves the emitted prompt is state-driven, deterministic, and complete.

2. **Stop hook (in-session forever) — `scripts/hooks/north_star_stop_hook.py`**, wired in `.claude/settings.json`.
   - On each turn end it feeds the self-generated prompt back (`{"decision":"block","reason": <prompt>}`) so the
     agent continues the next cycle — **but only when armed.** Three rails + fail-open:
     - **OPT-IN:** does nothing unless `.agent/LOOP_ACTIVE` exists (a normal session is never trapped).
     - **STOP:** allows the stop if `.agent/STOP_REQUESTED` exists (owner kill switch).
     - **CAP:** bounds continuations to `NORTH_STAR_LOOP_MAX_ITERS` (default 200) via `.agent/loop/hook_iterations`.
     - **FAIL-OPEN:** any error (bad input, builder failure) allows the stop — never crash-blocks a session.

3. **Durable runner (across sessions) — `scripts/run_north_star_loop.sh`**
   - A `while` loop that, each cycle: checks STOP → builds the prompt (the builder; static fallback) →
     `claude -p "<prompt>"` (headless) → logs + writes resume state → repeats. Survives crashes/limits by relaunching.
   - `--check` (validate, launch nothing) · `--dry-run` (print the next self-prompt, launch nothing) ·
     `--once` (one cycle) · `MAX_CYCLES=N` (cap, 0 = unbounded). The exact prompt fed each cycle is saved to
     `.agent/loop/current-prompt.txt`.

In-session hook = zero extra processes, runs in your live session. Durable runner = a separate headless process
that survives session death. Use either; they share `.agent/next-action.json` + `.agent/STOP_REQUESTED`.

## Run it (owner action — not auto-started)

```bash
# See exactly what the next cycle would do (safe — launches nothing):
scripts/run_north_star_loop.sh --dry-run
scripts/run_north_star_loop.sh --check

# A) In-session forever loop (this Claude Code session):
touch .agent/LOOP_ACTIVE                     # arm the Stop hook
#   ... the loop now self-continues every turn until you stop it ...
touch .agent/STOP_REQUESTED                  # stop after the current cycle
rm .agent/LOOP_ACTIVE .agent/loop/hook_iterations   # disarm + reset the cap

# B) Durable headless loop (survives this session; run in tmux/nohup):
CLAUDE_CODE_CMD='claude -p' MAX_CYCLES=1 scripts/run_north_star_loop.sh --once   # try one real cycle first
CLAUDE_CODE_CMD='claude -p' nohup scripts/run_north_star_loop.sh >/dev/null 2>&1 &   # forever
touch .agent/STOP_REQUESTED                  # stop;  rm it to resume
```

Disable the in-session hook entirely: remove the `Stop` entry from `.claude/settings.json`.

## Safety model

- **Off by default** (LOOP_ACTIVE opt-in; the durable runner is a manual launch). The flywheel watchdog and the
  loop's own no-fake-completion contract are unaffected.
- **Bounded:** hook cap + runner `MAX_CYCLES`. **Stoppable:** one `touch .agent/STOP_REQUESTED` halts both.
- **Fail-open** hook; **`--check`/`--dry-run`** launch nothing; the self-prompt is auditable in
  `.agent/loop/current-prompt.txt`.
- **Honors every standing constraint** — the builder embeds them in each prompt (no commit/push/pip/cloud/network-LLM,
  exact-pid watchdog, Baltor→Teleon→OpenHarnessHub law, lossless, owner-gated HELD items).

## Anti-slop gate (relationship to `stop-slop`)

`hardikpandya/stop-slop` is a prose-quality **skill** (detects "AI tells" — banned openers, structural patterns,
em-dash overuse — scored 1–10 across five dimensions, "below 35/50: revise"). It is feedback/guidance, not a hook.
This runtime borrows its *spirit* as an **anti-fake-progress gate** in the loop's continuation prompt: a cycle must
ship one real proof-backed increment (passing `--self-test` + flywheel GREEN) or mark a target VERIFIED_DONE with
evidence — never "queued / next tick / will continue" soft-stop slop, never claiming done without a green proof; if
the work is genuinely exhausted it must `touch .agent/STOP_REQUESTED` with a reason rather than loop idle.
Optional follow-up: adopt the stop-slop rubric as a content check for the prose the loop emits (receipts, hub copy).
