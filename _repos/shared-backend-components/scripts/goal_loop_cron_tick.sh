#!/usr/bin/env bash
# goal_loop_cron_tick.sh — one STOP-gated, overlap-guarded, bounded tick of the primitive
# axis-completeness loop, for cron. Drives every funnel axis up (descriptions → deterministic
# code synthesis + oracle → verified execution receipts → embeddings), ratcheting the status
# ladder toward the declared target. Reuses run_aidevobserver_100m_goal_loop.py --once (the loop
# is dry-by-default, bounded, timeout-enforced, resumable across ticks). Everything stays
# candidate=true / serves_truth=false; promotion happens only through the loop's own gates.
#
# Install (every 30 min):  see scripts/install_goal_loop_cron.sh
# Halt everything:         touch <repo>/.agent/STOP_AUTONOMOUS_FACTORY   (or .agent/STOP_GOAL_LOOP)
# Tune per-tick work:      env GOAL_LOOP_STAGE_TIMEOUT / GOAL_LOOP_EXTRA_ARGS
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SBC="$REPO_ROOT/_repos/shared-backend-components"
STOP_GLOBAL="$REPO_ROOT/.agent/STOP_AUTONOMOUS_FACTORY"   # the repo-wide kill switch
STOP_LOOP="$REPO_ROOT/.agent/STOP_GOAL_LOOP"              # this-loop-only pause
LOG_DIR="$SBC/data/dev-intel/aidevobserver_100m_goal_loop"
LOG="$LOG_DIR/cron_ticks.log"
LOCK="$LOG_DIR/.cron.lock"
STAGE_TIMEOUT="${GOAL_LOOP_STAGE_TIMEOUT:-800}"
# Per-stage batches right-sized so each stage COMMITS within STAGE_TIMEOUT (a timed-out stage
# blocks the whole tick — see the 2026-07-10 failure). Throughput measured ~66ms/row for
# description backfill and ~2k rows/s for embeddings; tune via GOAL_LOOP_EXTRA_ARGS to go bigger
# on a faster host. Embedding batch is large because model2vec is cheap.
DEFAULT_LIMITS="--description-limit 6000 --synthesis-limit 2000 --embedding-limit 150000 --search-limit 25000"
EXTRA_ARGS="${GOAL_LOOP_EXTRA_ARGS:-$DEFAULT_LIMITS}"

mkdir -p "$LOG_DIR"
stamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# STOP gate — checked BEFORE doing any work.
if [ -f "$STOP_GLOBAL" ] || [ -f "$STOP_LOOP" ]; then
  echo "$(stamp) SKIP: STOP flag present ($STOP_GLOBAL or $STOP_LOOP)" >> "$LOG"
  exit 0
fi

# Overlap guard — a still-running tick must not be overlapped by the next cron fire.
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(stamp) SKIP: previous tick still running (lock held)" >> "$LOG"
  exit 0
fi

echo "$(stamp) START tick (stage_timeout=${STAGE_TIMEOUT}s args='${EXTRA_ARGS}')" >> "$LOG"
cd "$SBC" || { echo "$(stamp) FAIL: cannot cd $SBC" >> "$LOG"; exit 1; }
PYTHONPATH="$SBC" python3 scripts/run_aidevobserver_100m_goal_loop.py --once \
  --stage-timeout "$STAGE_TIMEOUT" --inventory-timeout "$STAGE_TIMEOUT" $EXTRA_ARGS \
  >> "$LOG" 2>&1
RC=$?
echo "$(stamp) END tick rc=$RC" >> "$LOG"
exit "$RC"
