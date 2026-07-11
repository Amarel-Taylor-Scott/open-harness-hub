#!/usr/bin/env bash
# install_goal_loop_cron.sh — idempotently (un)install the crontab entry that ticks the primitive
# axis-completeness loop. Safe to re-run: it never duplicates the line.
#
#   scripts/install_goal_loop_cron.sh                 # install: every 30 min (default)
#   CRON_SCHEDULE="*/15 * * * *" scripts/install_goal_loop_cron.sh   # custom cadence
#   scripts/install_goal_loop_cron.sh --remove        # uninstall
#   scripts/install_goal_loop_cron.sh --show          # print current entry
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TICK="$REPO_ROOT/_repos/shared-backend-components/scripts/goal_loop_cron_tick.sh"
MARKER="# aidoneright-goal-loop-tick"                 # idempotency marker (one entry only)
SCHEDULE="${CRON_SCHEDULE:-*/30 * * * *}"             # default: every 30 minutes
LINE="$SCHEDULE bash $TICK $MARKER"

chmod +x "$TICK" 2>/dev/null
current="$(crontab -l 2>/dev/null || true)"
without="$(printf '%s\n' "$current" | grep -vF "$MARKER" || true)"

case "${1:-}" in
  --remove)
    printf '%s\n' "$without" | grep -vE '^$' | crontab - 2>/dev/null || crontab -r 2>/dev/null || true
    echo "removed goal-loop cron entry" ;;
  --show)
    printf '%s\n' "$current" | grep -F "$MARKER" || echo "(no goal-loop cron entry installed)" ;;
  *)
    { printf '%s\n' "$without" | grep -vE '^$'; echo "$LINE"; } | crontab -
    echo "installed: $LINE"
    echo "verify:  crontab -l | grep -F '$MARKER'"
    echo "halt:    touch $REPO_ROOT/.agent/STOP_GOAL_LOOP" ;;
esac
