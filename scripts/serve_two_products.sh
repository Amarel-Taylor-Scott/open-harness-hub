#!/usr/bin/env bash
# Launch BOTH Open Harness Hub products on the shared backend, each pinned to its brand and fronted
# by its OWN persistent trycloudflare.com tunnel (the two-services model — see
# docs/strategy/two-services-shared-infrastructure.md):
#   • Open Harness Hub    (build / monitor pipelines)  → :8000 → dist/showcase-share-url-harness-hub.txt
#   • Baltor   (content refinery / verified context)    → :8001 → dist/showcase-share-url-baltor.txt
# Same code, same catalog, same token — two surfaces. OH_PRODUCT pins the brand (injected into
# index.html by the server). Tunnels are left running on exit so their public URLs stay STABLE across
# server restarts (no dead-tab churn for testers).
#
#   bash scripts/serve_two_products.sh
set -u
cd "$(dirname "$0")/.."
mkdir -p dist
say(){ printf '%s\n' "$*"; }

# --- shared access token: reuse the existing one so any live URL keeps working, else mint one ---
TOKEN="$(grep -oE 'token=[A-Za-z0-9_-]+' dist/showcase-share-url.txt 2>/dev/null | head -1 | cut -d= -f2)"
[ -n "${TOKEN:-}" ] || TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(12))')"
say "token: ${TOKEN}"

bring_up_server(){ # product port slug
  local product="$1" port="$2" slug="$3" ok=0 i
  { fuser -k "${port}/tcp" 2>/dev/null || lsof -ti:"${port}" 2>/dev/null | xargs -r kill 2>/dev/null; }; sleep 0.5
  OH_PRODUCT="$product" OH_SHOWCASE_TOKEN="$TOKEN" setsid \
    python3 -m scripts.showcase --port "$port" >"/tmp/ohh-${slug}.log" 2>&1 < /dev/null &
  disown 2>/dev/null || true
  for i in $(seq 1 60); do
    curl -sf "http://127.0.0.1:${port}/api/health" >/dev/null 2>&1 && { ok=1; break; }
    sleep 1
  done
  [ "$ok" = 1 ] && say "  server[$slug] up on :$port (product=$product)" \
                || say "  server[$slug] NOT healthy on :$port — see /tmp/ohh-${slug}.log"
}

bring_up_tunnel(){ # port slug
  local port="$1" slug="$2" url="" i
  local match="cloudflared tunnel --url http://localhost:${port}"
  local urlfile="dist/showcase-tunnel-url-${slug}.txt"
  local exist; exist="$(cat "$urlfile" 2>/dev/null || true)"
  # legacy fallback: the original single-product tunnel file IS the :8000 tunnel
  [ -z "$exist" ] && [ "$port" = 8000 ] && exist="$(cat dist/showcase-tunnel-url.txt 2>/dev/null || true)"
  # reuse a still-answering tunnel for this port → public URL stays identical across restarts
  if pgrep -f "$match" >/dev/null 2>&1 && [ -n "$exist" ] && curl -sf --max-time 8 "${exist}/api/health" >/dev/null 2>&1; then
    echo "$exist" > "$urlfile"
    printf '%s\n' "${exist}/?token=${TOKEN}" > "dist/showcase-share-url-${slug}.txt"
    say "  tunnel[$slug] reused (stable) → ${exist}/?token=${TOKEN}"
    return
  fi
  pkill -f "$match" 2>/dev/null || true   # clear a dead tunnel for this port
  : > "/tmp/ohh-tunnel-${slug}.log"
  # setsid + disown so the tunnel outlives this script — that is what keeps the URL stable.
  setsid cloudflared tunnel --url "http://localhost:${port}" --no-autoupdate \
    >"/tmp/ohh-tunnel-${slug}.log" 2>&1 < /dev/null &
  disown 2>/dev/null || true
  for i in $(seq 1 60); do
    url="$(grep -Eo 'https://[a-z0-9.-]+\.trycloudflare\.com' "/tmp/ohh-tunnel-${slug}.log" | head -1)"
    [ -n "$url" ] && break
    sleep 1
  done
  if [ -n "$url" ]; then
    echo "$url" > "$urlfile"
    printf '%s\n' "${url}/?token=${TOKEN}" > "dist/showcase-share-url-${slug}.txt"
    say "  tunnel[$slug] up → ${url}/?token=${TOKEN}"
  else
    say "  tunnel[$slug] no URL yet — tail /tmp/ohh-tunnel-${slug}.log"
  fi
}

say "── bringing up both products on the shared backend ──"
bring_up_server harness-hub        8000 harness-hub
bring_up_server baltor 8001 baltor
bring_up_tunnel 8000 harness-hub
bring_up_tunnel 8001 baltor

say ""
say "═══════════════════════════════════════════════════════════════"
say "  Open Harness Hub    →  $(cat dist/showcase-share-url-harness-hub.txt 2>/dev/null)"
say "  Baltor  →  $(cat dist/showcase-share-url-baltor.txt 2>/dev/null)"
say "  shared backend · stable tunnels · stop tunnels: pkill -f 'cloudflared tunnel'"
say "═══════════════════════════════════════════════════════════════"
