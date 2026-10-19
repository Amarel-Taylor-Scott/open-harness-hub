#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
go test ./...
./bin/baltorctl-linux-amd64 validate --recipe recipes/showcase.json
./bin/baltorctl-linux-amd64 validate --recipe recipes/layered.json
./bin/baltorctl-linux-amd64 validate --recipe recipes/analyze_existing.json
./bin/baltorctl-linux-amd64 doctor
