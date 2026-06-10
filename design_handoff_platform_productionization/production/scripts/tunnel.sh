#!/usr/bin/env bash
# tunnel.sh — expose the local platform publicly via TryCloudflare quick tunnels.
# Requires: cloudflared (brew install cloudflared / https://github.com/cloudflare/cloudflared)
# Quick tunnels are ephemeral and unauthenticated — dev/demo only.
# For named, stable tunnels use the Terraform skeleton in terraform/.
set -euo pipefail

PORT="${1:-8080}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found. Install: brew install cloudflared" >&2
  exit 1
fi

echo "→ Opening a TryCloudflare quick tunnel to http://localhost:${PORT}"
echo "  (the public https://<random>.trycloudflare.com URL prints below)"
exec cloudflared tunnel --no-autoupdate --url "http://localhost:${PORT}"
