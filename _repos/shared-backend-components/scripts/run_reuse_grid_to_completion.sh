#!/usr/bin/env bash
# Supervisor: run the RESUMABLE reuse grid until every executed cell is present (or it stalls).
# Single-writer locks live here AND in reuse_experiment_grid.py. Every child has a wall-clock bound and writes a
# durable log; transport errors remain retryable attempts rather than false benchmark failures.
set -uo pipefail
cd /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/shared-backend-components
OUT=data/dev-intel/reuse_experiment_grid
F="$OUT/grid.json"
LOG="$OUT/supervisor.log"
SUPERVISOR_LOCK="$OUT/supervisor.lock"
REPEATS=3
BASE_PROTOCOL="${GRID_BASE_PROTOCOL:-legacy}"
TRACKS="${GRID_TRACKS:-}"
SPECIAL_REPEATS="${GRID_SPECIAL_REPEATS:-}"
SESSION_MAX_TURNS="${GRID_SESSION_MAX_TURNS:-}"
SESSION_TOKEN_BUDGET="${GRID_SESSION_TOKEN_BUDGET:-}"
CHILD_TIMEOUT_SECONDS="${GRID_CHILD_TIMEOUT_SECONDS:-3600}"
STALL_BACKOFF_SECONDS=$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -c \
  'from scripts._config import GEMMA_MIN_CALL_INTERVAL_SECONDS; print(GEMMA_MIN_CALL_INTERVAL_SECONDS)')
GRID_ARGS=(--variants all --repeats "$REPEATS" --base-protocol "$BASE_PROTOCOL")
if [ -n "$TRACKS" ]; then GRID_ARGS+=(--tracks "$TRACKS"); fi
if [ -n "$SPECIAL_REPEATS" ]; then GRID_ARGS+=(--special-repeats "$SPECIAL_REPEATS"); fi
if [ -n "$SESSION_MAX_TURNS" ]; then GRID_ARGS+=(--session-max-turns "$SESSION_MAX_TURNS"); fi
if [ -n "$SESSION_TOKEN_BUDGET" ]; then GRID_ARGS+=(--session-token-budget "$SESSION_TOKEN_BUDGET"); fi
TRACK_LABEL="${TRACKS:-default}"
mkdir -p "$OUT"
read -r EXPECTED PLAN_ID <<< "$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/reuse_experiment_grid.py \
  --expected-only "${GRID_ARGS[@]}" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["expected_cells"], d["plan_id"])')"
case "$EXPECTED" in
  ''|*[!0-9]*) echo "$(date --iso-8601=seconds) INVALID_EXPECTED value=$EXPECTED" | tee -a "$LOG"; exit 64 ;;
esac
case "$PLAN_ID" in
  ''|*[!0-9a-f]*) echo "$(date --iso-8601=seconds) INVALID_PLAN_ID value=$PLAN_ID" | tee -a "$LOG"; exit 64 ;;
esac
exec 9>"$SUPERVISOR_LOCK"
if ! flock -n 9; then
  echo "$(date --iso-8601=seconds) ALREADY_RUNNING supervisor_lock=$SUPERVISOR_LOCK" | tee -a "$LOG"
  exit 75
fi
trap 'echo "$(date --iso-8601=seconds) INTERRUPTED signal=INT" >>"$LOG"; exit 130' INT
trap 'echo "$(date --iso-8601=seconds) INTERRUPTED signal=TERM" >>"$LOG"; exit 143' TERM
trap 'echo "$(date --iso-8601=seconds) INTERRUPTED signal=HUP" >>"$LOG"; exit 129' HUP

progress() {
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 - "$F" "$EXPECTED" "$PLAN_ID" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected = int(sys.argv[2])
plan_id = sys.argv[3]
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("0 0 0 0 0 0")
else:
    completed = data.get("n_completed_cells", data.get("n_rows", 0))
    complete = int(bool(data.get("expected_complete")) and data.get("expected_cells") == expected
                   and data.get("plan_id") == plan_id)
    print(complete, completed, data.get("n_attempts", len(data.get("rows", []))),
          data.get("n_retryable_error_attempts", 0), data.get("n_missing_cells", expected),
          data.get("n_unexpected_completed_cells", 0))
PY
}

stall=0
complete=0
for iter in $(seq 1 40); do
  read -r before_complete before before_attempts before_errors before_missing before_unexpected <<< "$(progress)"
  if [ "$before_complete" -eq 1 ]; then
    complete=1
    echo "$(date --iso-8601=seconds) COMPLETE completed=$before attempts=$before_attempts missing=0 unexpected=$before_unexpected expected=$EXPECTED plan_id=$PLAN_ID tracks=$TRACK_LABEL" | tee -a "$LOG"
    break
  fi
  echo "$(date --iso-8601=seconds) START iter=$iter completed=$before attempts=$before_attempts retryable_errors=$before_errors missing=$before_missing unexpected=$before_unexpected expected=$EXPECTED plan_id=$PLAN_ID tracks=$TRACK_LABEL" | tee -a "$LOG"
  timeout --signal=TERM --kill-after=30s "${CHILD_TIMEOUT_SECONDS}s" \
    python3 scripts/reuse_experiment_grid.py --live "${GRID_ARGS[@]}" >>"$LOG" 2>&1
  child_status=$?
  read -r after_complete after after_attempts after_errors after_missing after_unexpected <<< "$(progress)"
  echo "$(date --iso-8601=seconds) END iter=$iter exit=$child_status completed=$before->$after attempts=$after_attempts retryable_errors=$after_errors missing=$after_missing unexpected=$after_unexpected expected=$EXPECTED" | tee -a "$LOG"
  if [ "$after_complete" -eq 1 ]; then complete=1; break; fi
  if [ "$after" -le "$before" ]; then
    stall=$((stall+1))
    if [ "$stall" -lt 3 ]; then
      echo "$(date --iso-8601=seconds) BACKOFF seconds=$STALL_BACKOFF_SECONDS after_no_progress=$stall" | tee -a "$LOG"
      sleep "$STALL_BACKOFF_SECONDS"
    fi
  else
    stall=0
  fi
  if [ "$child_status" -eq 75 ]; then
    echo "$(date --iso-8601=seconds) LOCKED another grid writer owns grid.lock; stopping supervisor" | tee -a "$LOG"
    exit 75
  fi
  if [ "$stall" -ge 3 ]; then
    echo "$(date --iso-8601=seconds) STALLED count=3 completed=$after; inspect $LOG and provider sessions" | tee -a "$LOG"
    break
  fi
done
read -r final_complete final final_attempts final_errors final_missing final_unexpected <<< "$(progress)"
if [ "$final_complete" -eq 1 ]; then complete=1; fi
echo "$(date --iso-8601=seconds) SUPERVISOR_DONE complete=$complete completed=$final attempts=$final_attempts retryable_errors=$final_errors missing=$final_missing unexpected=$final_unexpected expected=$EXPECTED plan_id=$PLAN_ID tracks=$TRACK_LABEL" | tee -a "$LOG"
if [ "$complete" -ne 1 ]; then exit 2; fi
