#!/usr/bin/env bash
# serve_all_sites.sh — bring up ALL THREE brand surfaces on the shared backend, each pinned to its
# brand and fronted by its OWN persistent trycloudflare.com tunnel, then HEAL-LOOP until every one of
# the three public URLs is fully functional. Supersedes scripts/serve_two_products.sh (which did 2).
#
#   Context is Everything   (parent / mission landing)  → :8002 → web/context-is-everything
#   Baltor                  (verified-context SaaS)      → :8001 → web/baltor
#   OpenHubForAI        (open builder funnel)        → :8000 → web/openhubforai
#
# Same code, same catalog, same access token — three surfaces. OH_PRODUCT pins which web/<product>/
# folder the shared server serves. Tunnels + servers are detached (setsid/disown) so their public URLs
# stay STABLE across restarts and outlive this script. The script does not exit until all three public
# URLs answer (or MAX_HEAL rounds elapse) — see scripts/showcase/verify_tunnels.py for the gate.
#
#   bash scripts/serve_all_sites.sh            # bring up + heal until all 3 green
#   bash scripts/serve_all_sites.sh --status   # just print the current 3 URLs + health, no changes
#
# Brand/identity: docs/strategy/brand-architecture.md (LOCKED 2026-05-29).
set -u
cd "$(dirname "$0")/.."
mkdir -p dist
say(){ printf '%s\n' "$*"; }

# --- the three sites: "product port slug brand-marker" (brand-marker = string that must appear at /) ---
SITES=(
  "openhubforai 8000 openhubforai OpenHubForAI"
  "baltor 8001 baltor Baltor"
  "context-is-everything 8002 context-is-everything Context is Everything"
)
MAX_HEAL="${MAX_HEAL:-12}"     # heal rounds before giving up (each ~10-20s); 0 = forever
HEAL_SLEEP="${HEAL_SLEEP:-8}"

# --- shared access token: reuse the existing one so any live URL keeps working, else mint one ---
TOKEN="$(grep -oE 'token=[A-Za-z0-9_-]+' dist/showcase-share-url.txt 2>/dev/null | head -1 | cut -d= -f2)"
[ -n "${TOKEN:-}" ] || TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(12))')"

server_up(){ # product port slug — (re)start the server only if its local health is down
  local product="$1" port="$2" slug="$3" i
  if curl -sf --max-time 4 "http://127.0.0.1:${port}/api/health" >/dev/null 2>&1; then return 0; fi
  { fuser -k "${port}/tcp" 2>/dev/null || lsof -ti:"${port}" 2>/dev/null | xargs -r kill 2>/dev/null; }; sleep 0.5
  OH_PRODUCT="$product" OH_SHOWCASE_TOKEN="$TOKEN" setsid \
    python3 -m scripts.showcase --port "$port" >"/tmp/ohh-${slug}.log" 2>&1 < /dev/null &
  disown 2>/dev/null || true
  for i in $(seq 1 60); do
    curl -sf --max-time 4 "http://127.0.0.1:${port}/api/health" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

tunnel_up(){ # port slug — reuse a still-answering tunnel (stable URL), else start a fresh one
  local port="$1" slug="$2" url="" i
  local match="cloudflared tunnel --url http://localhost:${port}"
  local urlfile="dist/showcase-tunnel-url-${slug}.txt"
  local exist; exist="$(cat "$urlfile" 2>/dev/null || true)"
  [ -z "$exist" ] && [ "$port" = 8000 ] && exist="$(cat dist/showcase-tunnel-url.txt 2>/dev/null || true)"
  if pgrep -f "$match" >/dev/null 2>&1 && [ -n "$exist" ] && curl -sf --max-time 8 "${exist}/api/health" >/dev/null 2>&1; then
    echo "$exist" > "$urlfile"
    printf '%s\n' "${exist}/?token=${TOKEN}" > "dist/showcase-share-url-${slug}.txt"
    return 0
  fi
  pkill -f "$match" 2>/dev/null || true
  : > "/tmp/ohh-tunnel-${slug}.log"
  setsid cloudflared tunnel --url "http://localhost:${port}" --no-autoupdate \
    >"/tmp/ohh-tunnel-${slug}.log" 2>&1 < /dev/null &
  disown 2>/dev/null || true
  for i in $(seq 1 60); do
    url="$(grep -Eo 'https://[a-z0-9.-]+\.trycloudflare\.com' "/tmp/ohh-tunnel-${slug}.log" | head -1)"
    [ -n "$url" ] && break
    sleep 1
  done
  [ -z "$url" ] && return 1
  echo "$url" > "$urlfile"
  printf '%s\n' "${url}/?token=${TOKEN}" > "dist/showcase-share-url-${slug}.txt"
  return 0
}

public_ok(){ # slug brand-marker — public URL healthy AND serving the right brand?
  local slug="$1" marker="$2"
  local base; base="$(cat "dist/showcase-tunnel-url-${slug}.txt" 2>/dev/null || true)"
  [ -n "$base" ] || return 1
  curl -sf --max-time 12 "${base}/api/health" >/dev/null 2>&1 || return 1
  curl -sf --max-time 12 "${base}/" 2>/dev/null | grep -qF "$marker" || return 1
  return 0
}

print_status(){
  say "═══════════════════════════════════════════════════════════════════════════"
  local row product port slug marker base mark
  for row in "${SITES[@]}"; do
    read -r product port slug marker <<<"$(echo "$row" | sed -E 's/^([^ ]+) ([^ ]+) ([^ ]+) (.*)$/\1 \2 \3 \4/')"
    base="$(cat "dist/showcase-tunnel-url-${slug}.txt" 2>/dev/null || true)"
    if public_ok "$slug" "$marker"; then mark="● LIVE "; else mark="○ DOWN "; fi
    printf '  %s %-22s %s\n' "$mark" "$product" "${base:-(no url)}/?token=${TOKEN}"
  done
  say "  token: ${TOKEN}   ·   stop all: pkill -f 'cloudflared tunnel'; pkill -f scripts.showcase"
  say "═══════════════════════════════════════════════════════════════════════════"
}

if [ "${1:-}" = "--status" ]; then print_status; exit 0; fi

say "── bringing up 3 sites on the shared backend (token: ${TOKEN}) ──"
round=0
while :; do
  round=$((round+1))
  allgreen=1
  for row in "${SITES[@]}"; do
    read -r product port slug marker <<<"$(echo "$row" | sed -E 's/^([^ ]+) ([^ ]+) ([^ ]+) (.*)$/\1 \2 \3 \4/')"
    if public_ok "$slug" "$marker"; then continue; fi
    say "  [round ${round}] healing ${product} (:${port}) …"
    server_up "$product" "$port" "$slug" || say "    server[$slug] not healthy — see /tmp/ohh-${slug}.log"
    tunnel_up "$port" "$slug"            || say "    tunnel[$slug] no URL yet — see /tmp/ohh-tunnel-${slug}.log"
    public_ok "$slug" "$marker" || allgreen=0
  done
  if [ "$allgreen" = 1 ]; then say ""; say "✓ all 3 sites are LIVE and serving the right brand."; break; fi
  if [ "$MAX_HEAL" != 0 ] && [ "$round" -ge "$MAX_HEAL" ]; then
    say ""; say "✗ gave up after ${round} heal rounds — some sites still down (see status below)."; break
  fi
  sleep "$HEAL_SLEEP"
done

print_status
