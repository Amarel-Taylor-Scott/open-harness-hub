#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 2 ]; then echo 'Usage: scripts/install_aliases.sh /path/to/baltorctl /target/bin'; exit 2; fi
src="$(realpath "$1")"; dest="$2"
mkdir -p "$dest"
for sub in run verify plan graph catalog ingest pack inspect doctor validate diff; do
  ln -sfn "$src" "$dest/baltor-$sub"
done
printf 'Created 11 multi-call binary entrypoints in %s\n' "$dest"
