#!/usr/bin/env bash
# run_loops.sh — the terminal runner/supervisor for the autonomous primitive factory loops.
# Idempotent (won't double-launch), STOP-file-gated, per-loop logs. No Claude Code / human input needed once started.
#
#   bash scripts/run_loops.sh start          # launch every loop that isn't already running
#   bash scripts/run_loops.sh status         # pids + tail of each loop's status/log
#   bash scripts/run_loops.sh stop            # graceful stop via STOP files (loops finish the current stage)
#   bash scripts/run_loops.sh kill            # hard stop (kill -9 by pid)
#
# Loops supervised:
#   autonomous_factory   scrape -> deconstruct -> Hy3 manufacture -> Hy3+omniroute executor-synthesis (the master)
#   hy3_flywheel         concurrent free-lane minter (extra throughput; Hy3-first)
#   weak_capability      Hy3 synthesizer over the 36 measured-weak-capability specs
set -u  # NOT pipefail: status tails optional logs whose absence must not fail the command
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO"
SC="_repos/shared-backend-components/scripts"
LOGDIR="_repos/shared-backend-components/data/dev-intel/loop_runner_logs"
AGENT=".agent"
mkdir -p "$LOGDIR" "$AGENT"

# name | STOP-file | pgrep-regex (bracket-safe, avoids self-match) | launch command
_loops() {
  cat <<EOF
autonomous_factory|$AGENT/STOP_AUTONOMOUS_FACTORY|autonomous_primitive_factory_loop[.]py.*--run|python3 $SC/autonomous_primitive_factory_loop.py --run --minutes 600 --cycle-minutes 20
hy3_flywheel|$AGENT/STOP_HY3_FLYWHEEL|hy3_overnight_flywheel[.]py.*--run|python3 $SC/hy3_overnight_flywheel.py --run --iterations 100000 --minutes 600 --workers 12
weak_capability|$AGENT/STOP_WEAK_CAPABILITY|weak_capability_primitive_closer[.]py.*--run|python3 $SC/weak_capability_primitive_closer.py --run
EOF
}

_pid() { pgrep -f "$1" 2>/dev/null | head -1; }

start() {
  echo "== run_loops start =="
  while IFS='|' read -r name stopf regex cmd; do
    [ -z "$name" ] && continue
    rm -f "$stopf" 2>/dev/null                       # clear STOP so the loop may run
    pid="$(_pid "$regex")"
    if [ -n "$pid" ]; then
      echo "  [already up] $name (pid $pid)"
    else
      nohup $cmd > "$LOGDIR/$name.log" 2>&1 &
      echo "  [launched]   $name (pid $!) -> $LOGDIR/$name.log"
    fi
  done < <(_loops)
  echo "stop with: bash $SC/run_loops.sh stop"
}

status() {
  echo "== run_loops status =="
  while IFS='|' read -r name stopf regex cmd; do
    [ -z "$name" ] && continue
    pid="$(_pid "$regex")"
    stopped=""; [ -f "$stopf" ] && stopped=" (STOP file present)"
    if [ -n "$pid" ]; then echo "  RUNNING  $name  pid $pid$stopped"; else echo "  down     $name$stopped"; fi
    [ -f "$LOGDIR/$name.log" ] && tail -1 "$LOGDIR/$name.log" 2>/dev/null | sed 's/^/             /' | cut -c1-140
  done < <(_loops)
}

stop() {
  echo "== run_loops stop (graceful, via STOP files) =="
  while IFS='|' read -r name stopf regex cmd; do
    [ -z "$name" ] && continue
    touch "$stopf"; echo "  touched $stopf ($name will halt after its current stage)"
  done < <(_loops)
}

kill_all() {
  echo "== run_loops kill (hard) =="
  while IFS='|' read -r name stopf regex cmd; do
    [ -z "$name" ] && continue
    touch "$stopf"
    for pid in $(pgrep -f "$regex" 2>/dev/null); do kill -9 "$pid" 2>/dev/null && echo "  killed $name pid $pid"; done
  done < <(_loops)
}

case "${1:-status}" in
  start)  start ;;
  status) status ;;
  stop)   stop ;;
  kill)   kill_all ;;
  *) echo "usage: bash $SC/run_loops.sh {start|status|stop|kill}"; exit 2 ;;
esac
