#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export CGO_ENABLED=0
mkdir -p bin
for target in linux/amd64 linux/arm64 darwin/arm64 windows/amd64; do
  goos="${target%/*}"; goarch="${target#*/}"
  ext=''; if [ "$goos" = windows ]; then ext='.exe'; fi
  out="bin/baltorctl-${goos}-${goarch}${ext}"
  echo "Building $out"
  GOOS="$goos" GOARCH="$goarch" go build -trimpath -buildvcs=false -ldflags='-s -w' -o "$out" ./cmd/baltorctl
  sha256sum "$out"
done
