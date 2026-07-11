#!/usr/bin/env bash
# run_north_star_loop.sh — DURABLE external runner for the Baltor North Star continuous builder.
#
# Why this exists: a model loop can reach a soft-terminal state ("queued", "next tick", "GREEN, done").
# A prompt alone cannot guarantee hours/days of progress. This wrapper makes STOPPING a recoverable event:
# when Claude Code exits (limit, timeout, or soft-stop), the wrapper writes resume state, detects soft-stop
# language, and RELAUNCHES — resuming from .agent/north-star-loop-state.json, not chat memory.
#
# The model can stop. The process should not. Owner stops it by creating .agent/STOP_REQUESTED.
#
# Each cycle SELF-PROMPTS: scripts/loop_prompt_builder.py regenerates the cycle's prompt from
# .agent/next-action.json (which the agent itself updates every cycle), so the loop improves on its own goal.
#
# Usage:
#   scripts/run_north_star_loop.sh --check            # validate the contract; launch NOTHING (safe)
#   scripts/run_north_star_loop.sh --dry-run          # print the next self-prompt; launch NOTHING (safe)
#   CLAUDE_CODE_CMD='claude -p' MAX_CYCLES=1 scripts/run_north_star_loop.sh --once   # run exactly ONE cycle
#   CLAUDE_CODE_CMD='claude -p' scripts/run_north_star_loop.sh   # run the durable loop forever (owner action)
#   (run inside tmux/screen/nohup so it survives terminal close; MAX_CYCLES=N caps total cycles, 0=unbounded)
#   touch .agent/STOP_REQUESTED   # ask the loop to stop after the current cycle
#   rm .agent/STOP_REQUESTED      # resume
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p .agent/logs .agent/loop

# Prompt lives with the Baltor context after the _repos/ migration; ROOT is _repos/shared-backend-components,
# so the sibling repo is one level up (../baltor/context/...).
PROMPT_FILE="../baltor/context/baltor-north-star-continuous-builder.md"
STOP_FILE=".agent/STOP_REQUESTED"
STATE_FILE=".agent/north-star-loop-state.json"
CYCLE_TIMEOUT="${CYCLE_TIMEOUT:-14400}"     # max seconds per cycle (4h) before the wrapper reclaims
COOLDOWN="${COOLDOWN:-20}"                   # seconds between cycles (avoid a tight crash loop)
# Replace with your real Claude Code invocation. The wrapper logs stdout/stderr and continues regardless.
CLAUDE_CODE_CMD="${CLAUDE_CODE_CMD:-claude -p}"
BUILDER="scripts/loop_prompt_builder.py"      # self-prompt generator (built from .agent/next-action.json each cycle)
MAX_CYCLES="${MAX_CYCLES:-0}"                  # 0 = unbounded (until STOP_REQUESTED); >0 caps total cycles
PROMPT_OUT=".agent/loop/current-prompt.txt"    # the exact prompt fed to the current cycle (audit trail)

# Print the NEXT cycle's prompt: prefer the SELF-PROMPT builder (state-driven, regenerated every cycle from
# .agent/next-action.json), fall back to the static continuous-builder prompt if the builder is unavailable.
_build_prompt() { python3 "$BUILDER" --emit 2>/dev/null || cat "$PROMPT_FILE"; }

_check() {
  local ok=1
  echo "== North Star durable runner — contract check =="
  [[ -f "$PROMPT_FILE" ]]  && echo "  [ok] prompt present: $PROMPT_FILE"   || { echo "  [FAIL] missing $PROMPT_FILE"; ok=0; }
  [[ -f "$STATE_FILE" ]]   && echo "  [ok] loop state present: $STATE_FILE" || echo "  [warn] no state yet (created on first run)"
  command -v python3 >/dev/null && echo "  [ok] python3 available"          || { echo "  [FAIL] python3 missing"; ok=0; }
  python3 "$BUILDER" --self-test >/dev/null 2>&1 && echo "  [ok] self-prompt builder green: $BUILDER" || echo "  [warn] builder self-test not green (falls back to static $PROMPT_FILE)"
  grep -q "do not voluntarily stop\|CONTINUOUS BUILD MODE" "$PROMPT_FILE" 2>/dev/null \
    && echo "  [ok] prompt forbids voluntary stop" || { echo "  [FAIL] prompt missing the no-stop contract"; ok=0; }
  echo "  stop file (owner-controlled): $STOP_FILE  (touch to stop, rm to resume)"
  echo "  start: CLAUDE_CODE_CMD='claude -p' scripts/run_north_star_loop.sh   (run in tmux/nohup)"
  [[ "$ok" == 1 ]] && { echo "CONTRACT OK"; return 0; } || { echo "CONTRACT INCOMPLETE"; return 1; }
}

_write_state() {  # $1=exit_code $2=log
  python3 - "$1" "$2" <<'PY' || true
import json, pathlib, datetime, sys
exit_code, log = int(sys.argv[1]), sys.argv[2]
p = pathlib.Path(".agent/north-star-loop-state.json")
state = {}
if p.exists():
    try: state = json.loads(p.read_text())
    except Exception: state = {}
state.update({
    "last_runner_exit_code": exit_code,
    "last_runner_log": log,
    "last_runner_finished_at": datetime.datetime.utcnow().isoformat() + "Z",
    "resume_instructions": ("Read this state file + the latest .agent/logs log, run the repair sweep + "
                            "flywheel --once, then CONTINUE the highest-priority unfinished North Star "
                            "target. Do NOT restart from scratch. Do NOT stop on green."),
    "stop_allowed": False,
})
p.write_text(json.dumps(state, indent=2, sort_keys=True))
PY
}

MODE="${1:-}"
if [[ "$MODE" == "--check" ]]; then _check; exit $?; fi
if [[ "$MODE" == "--dry-run" ]]; then
  echo "== north-star loop dry-run: the next cycle's SELF-PROMPT (launches NOTHING) =="
  _build_prompt
  exit 0
fi

echo "Starting Baltor North Star durable loop (root=$ROOT, builder=$BUILDER, stop=$STOP_FILE, max=$MAX_CYCLES, mode=${MODE:-forever})"
CYCLES=0
while true; do
  if [[ -f "$STOP_FILE" ]]; then echo "STOP_REQUESTED present; exiting durable loop."; exit 0; fi
  if [[ "$MAX_CYCLES" -gt 0 && "$CYCLES" -ge "$MAX_CYCLES" ]]; then echo "MAX_CYCLES=$MAX_CYCLES reached; exiting."; exit 0; fi
  TS="$(date -u +%Y%m%dT%H%M%SZ)"; LOG=".agent/logs/north-star-loop-$TS.log"
  mkdir -p .agent/loop
  _build_prompt > "$PROMPT_OUT"        # SELF-PROMPT this cycle from .agent/next-action.json (audit: $PROMPT_OUT)
  echo "[$TS] launching Claude Code cycle $((CYCLES+1)) → $LOG (self-prompt: $PROMPT_OUT)"
  set +e
  timeout "$CYCLE_TIMEOUT" bash -lc "$CLAUDE_CODE_CMD \"\$(cat '$PROMPT_OUT')\"" >>"$LOG" 2>&1
  EXIT_CODE=$?
  set -e
  CYCLES=$((CYCLES+1))
  echo "[$TS] cycle $CYCLES exited code=$EXIT_CODE"
  _write_state "$EXIT_CODE" "$LOG"
  if [[ "$MODE" == "--once" ]]; then echo "--once: ran exactly one cycle; exiting."; exit 0; fi
  # soft-stop detector: if the model ended on continuation language, relaunch immediately
  if tail -n 80 "$LOG" 2>/dev/null | grep -Eiq "next tick|queued|re-armed|waiting for|background workflow|will continue|standing by|self-pacing|scheduled.*wakeup"; then
    echo "[$TS] soft-stop language detected; relaunching now."
    [[ -f "$STOP_FILE" ]] && { echo "STOP_REQUESTED present; exiting."; exit 0; }
    sleep 5; continue
  fi
  sleep "$COOLDOWN"
done
