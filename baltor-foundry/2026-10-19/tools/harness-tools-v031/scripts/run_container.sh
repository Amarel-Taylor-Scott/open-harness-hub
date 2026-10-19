#!/usr/bin/env bash
# Fail closed if neither supported container runtime is available.
set -euo pipefail
runtime=""
if command -v podman >/dev/null 2>&1; then runtime=podman
elif command -v docker >/dev/null 2>&1; then runtime=docker
else echo 'ERROR: Container runtime unavailable. Install Docker/Podman; no insecure fallback.' >&2; exit 2
fi
if [ "$#" -lt 1 ]; then echo 'Usage: scripts/run_container.sh run --recipe /recipes/showcase.json --workspace /work' >&2; exit 2; fi
project="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$project/work"
exec "$runtime" run --rm \
  --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  --pids-limit=96 --memory=1536m --cpus=2 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --user "$(id -u):$(id -g)" \
  -v "$project/work:/work:rw" \
  -v "$project/recipes:/recipes:ro" \
  baltor/harness-tools:0.3.1 "$@"
