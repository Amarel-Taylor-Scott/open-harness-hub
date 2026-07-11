#!/usr/bin/env bash
# Codex-managed north-star gap closure loop.
#
# This is the executable runner for `.codex/prompts/north-star-gap-closure-goal.md`.
# It refreshes deterministic state, builds a prompt from the current gap summary, launches
# `codex exec`, writes logs/state, and repeats until stopped.
#
# Usage:
#   scripts/run_codex_north_star_gap_loop.sh --check
#   scripts/run_codex_north_star_gap_loop.sh --dry-run
#   MAX_CYCLES=1 scripts/run_codex_north_star_gap_loop.sh --once
#   scripts/run_codex_north_star_gap_loop.sh
#   ./loop gaps --check
#   ./loop gaps --once
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SBC="$ROOT/_repos/shared-backend-components"
cd "$ROOT"
mkdir -p .agent/logs .agent/north-star-gap-closure
export PYTHONPATH="$SBC:$ROOT/_repos/teleon/backend:$ROOT/_repos/baltor/backend:${PYTHONPATH:-}"

PROMPT_FILE=".codex/prompts/north-star-gap-closure-goal.md"
SUMMARY_FILE=".agent/north-star-gap-closure/summary.md"
STATE_FILE=".agent/codex-north-star-gap-loop-state.json"
PROMPT_OUT=".agent/north-star-gap-closure/current-codex-prompt.txt"
LAST_MESSAGE=".agent/north-star-gap-closure/last-codex-message.md"
STOP_FILE=".agent/CODEX_NORTH_STAR_GAP_STOP_REQUESTED"

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.6-sol}"
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-ultra}"
CYCLE_TIMEOUT="${CYCLE_TIMEOUT:-14400}"
COOLDOWN="${COOLDOWN:-20}"
MAX_CYCLES="${MAX_CYCLES:-0}"

_refresh_state() {
  python3 "$SBC/scripts/repo_code_inventory.py" . --out .agent/repo-code-inventory >/dev/null
  python3 "$SBC/scripts/north_star_gap_closure_loop.py" >/dev/null
}

_build_prompt() {
  _refresh_state
  {
    cat "$PROMPT_FILE"
    printf '\n\n---\n\n# Current Deterministic Gap State\n\n'
    cat "$SUMMARY_FILE"
    printf '\n\n---\n\n'
    printf 'Run one bounded Codex-managed north-star gap closure cycle now.\n'
    printf 'Work the `Next gap` from the summary unless a proof-blocking regression must be fixed first.\n'
    printf 'Make durable repo changes, run focused checks, run `PYTHONPATH=. python3 scripts/run_proofs.py`, then re-run `python3 scripts/north_star_gap_closure_loop.py`.\n'
    printf 'Do not claim completion unless the artifacts and proof gate support it.\n'
  }
}

_check() {
  local ok=1
  echo "== Codex north-star gap loop contract check =="
  [[ -f "$PROMPT_FILE" ]] && echo "  [ok] prompt present: $PROMPT_FILE" || { echo "  [FAIL] missing $PROMPT_FILE"; ok=0; }
  command -v "$CODEX_BIN" >/dev/null && echo "  [ok] codex available: $(command -v "$CODEX_BIN")" || { echo "  [FAIL] codex missing: $CODEX_BIN"; ok=0; }
  python3 "$SBC/scripts/north_star_gap_closure_loop.py" --self-test >/dev/null && echo "  [ok] gap loop self-test green" || { echo "  [FAIL] gap loop self-test failed"; ok=0; }
  grep -q "North Star Gap Closure Loop" "$PROMPT_FILE" && echo "  [ok] prompt names the goal" || { echo "  [FAIL] prompt missing goal header"; ok=0; }
  echo "  stop file: $STOP_FILE"
  echo "  start: _repos/shared-backend-components/scripts/run_codex_north_star_gap_loop.sh"
  echo "  shortcut: ./loop gaps"
  [[ "$ok" == 1 ]] && { echo "CONTRACT OK"; return 0; } || { echo "CONTRACT INCOMPLETE"; return 1; }
}

_write_state() {
  python3 - "$1" "$2" <<'PY' || true
import datetime, json, pathlib, sys
exit_code = int(sys.argv[1])
log = sys.argv[2]
p = pathlib.Path(".agent/codex-north-star-gap-loop-state.json")
state = {}
if p.exists():
    try:
        state = json.loads(p.read_text())
    except Exception:
        state = {}
state.update({
    "last_exit_code": exit_code,
    "last_log": log,
    "last_finished_at": datetime.datetime.utcnow().isoformat() + "Z",
    "runner": "scripts/run_codex_north_star_gap_loop.sh",
    "prompt": ".agent/north-star-gap-closure/current-codex-prompt.txt",
    "last_message": ".agent/north-star-gap-closure/last-codex-message.md",
    "gap_state": ".agent/north-star-gap-closure/state.json",
    "stop_file": ".agent/CODEX_NORTH_STAR_GAP_STOP_REQUESTED",
    "resume_instructions": "Run ./loop gaps or scripts/run_codex_north_star_gap_loop.sh. Work the next_gap from .agent/north-star-gap-closure/summary.md. Keep proofs green.",
    "serves_truth": False,
})
p.write_text(json.dumps(state, indent=2, sort_keys=True))
PY
}

MODE="${1:-}"
if [[ "$MODE" == "--check" ]]; then
  _check
  exit $?
fi
if [[ "$MODE" == "--dry-run" ]]; then
  _build_prompt > "$PROMPT_OUT"
  echo "== codex north-star gap loop dry-run: prompt only, launches no Codex =="
  cat "$PROMPT_OUT"
  exit 0
fi
if [[ "$MODE" == "stop" ]]; then
  : > "$STOP_FILE"
  echo "Codex north-star gap loop stop requested: $STOP_FILE"
  exit 0
fi
if [[ "$MODE" == "resume" ]]; then
  rm -f "$STOP_FILE"
  echo "Codex north-star gap loop stop flag cleared."
  exit 0
fi
if [[ "$MODE" == "status" ]]; then
  python3 "$SBC/scripts/north_star_gap_closure_loop.py" >/dev/null
  sed -n '1,220p' "$SUMMARY_FILE"
  exit 0
fi

echo "Starting Codex north-star gap loop (model=$CODEX_MODEL, reasoning=$CODEX_REASONING_EFFORT, max=$MAX_CYCLES, stop=$STOP_FILE, mode=${MODE:-forever})"
CYCLES=0
while true; do
  if [[ -f "$STOP_FILE" ]]; then
    echo "STOP requested; exiting."
    exit 0
  fi
  if [[ "$MAX_CYCLES" -gt 0 && "$CYCLES" -ge "$MAX_CYCLES" ]]; then
    echo "MAX_CYCLES=$MAX_CYCLES reached; exiting."
    exit 0
  fi

  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  LOG=".agent/logs/codex-north-star-gap-loop-$TS.log"
  _build_prompt > "$PROMPT_OUT"
  echo "[$TS] launching Codex cycle $((CYCLES + 1)) -> $LOG"
  set +e
  timeout "$CYCLE_TIMEOUT" "$CODEX_BIN" -a never exec \
    -C "$ROOT" \
    -s workspace-write \
    -m "$CODEX_MODEL" \
    -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" \
    -o "$LAST_MESSAGE" \
    - < "$PROMPT_OUT" >>"$LOG" 2>&1
  EXIT_CODE=$?
  set -e
  CYCLES=$((CYCLES + 1))
  _write_state "$EXIT_CODE" "$LOG"
  echo "[$TS] Codex cycle $CYCLES exited code=$EXIT_CODE"

  if [[ "$MODE" == "--once" ]]; then
    echo "--once: ran exactly one cycle; exiting."
    exit "$EXIT_CODE"
  fi
  sleep "$COOLDOWN"
done
