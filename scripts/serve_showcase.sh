#!/usr/bin/env bash
# Run the Open Harness Hub paste-to-flow showcase locally with Gemma intelligence
# and a public trycloudflare.com URL you can send to someone to test.
#
#   bash scripts/serve_showcase.sh                 # auto-detect a local Gemma, open a tunnel
#   bash scripts/serve_showcase.sh --model gemma4  # force a specific Ollama model tag
#   bash scripts/serve_showcase.sh --port 8080 --no-tunnel
#
# It is resilient: if Ollama/Gemma isn't running the site still works (the
# builder falls back to a deterministic explanation); if cloudflared isn't
# installed it still serves locally and tells you how to get the tunnel.
set -uo pipefail
cd "$(dirname "$0")/.."

PORT=8000
MODEL=""
TUNNEL=1
FORCE_CPU=0
OLLAMA_URL="${OH_LLM_BASE_URL:-http://localhost:11434}"
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    --no-tunnel) TUNNEL=0; shift;;
    --cpu) FORCE_CPU=1; shift;;
    -h|--help) sed -n '2,14p' "$0"; exit 0;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

say(){ printf '\033[38;2;251;119;20m%s\033[0m\n' "$*"; }
warn(){ printf '\033[33m%s\033[0m\n' "$*"; }

# --- 1. Gemma via Ollama (OpenAI-compatible) -------------------------------
# Auto-start a local Ollama if it's installed but not already serving.
if ! curl -sf "${OLLAMA_URL}/api/tags" -o /tmp/ohh_tags.json 2>/dev/null && command -v ollama >/dev/null 2>&1; then
  say "Starting Ollama (ollama serve)…"
  nohup ollama serve >/tmp/ohh_ollama.log 2>&1 &
  for _ in $(seq 1 20); do curl -sf "${OLLAMA_URL}/api/tags" -o /tmp/ohh_tags.json 2>/dev/null && break; sleep 0.5; done
fi
LLM_OK=0
if curl -sf "${OLLAMA_URL}/api/tags" -o /tmp/ohh_tags.json 2>/dev/null; then
  LLM_OK=1
  if [ -z "$MODEL" ]; then
    # auto-detect the highest-version installed Gemma (prefers Gemma 4 over legacy 2/3)
    MODEL=$(python3 -c "
import json, re
ts = json.load(open('/tmp/ohh_tags.json')).get('models', [])
def ver(n):
    m = re.search(r'gemma[ ._-]?(\d+)', n.lower()); return int(m.group(1)) if m else -1
g = sorted([m['name'] for m in ts if 'gemma' in m['name'].lower()], key=ver, reverse=True)
print(g[0] if g else (ts[0]['name'] if ts else ''))" 2>/dev/null)
  fi
  if [ -z "$MODEL" ]; then
    warn "Ollama is up but has no models. Pull Gemma:  ollama pull gemma4   (or your Gemma 4 tag)"
    LLM_OK=0; MODEL="gemma4"
  else
    say "Gemma intelligence: ON  (Ollama model: $MODEL)"
  fi
else
  MODEL="${MODEL:-gemma4}"
  warn "Ollama not reachable at ${OLLAMA_URL}. The site will run with the deterministic"
  warn "explainer. To enable Gemma: install Ollama, run 'ollama serve', then"
  warn "'ollama pull $MODEL' (or your Gemma 4 tag) and re-run this script."
fi

# Point the provider-neutral LLM route at Ollama (see scripts/model_routes.py).
export OH_LLM_BACKEND=http-openai
export OH_LLM_BASE_URL="${OLLAMA_URL}/v1"
export OH_LLM_MODEL="$MODEL"
# Embeddings stay offline-placeholder unless OH_EMBED_* is already set (cloud later).

# --- compute: GPU if usable, else automatic CPU fallback -------------------
# Ollama uses the GPU automatically when an NVIDIA driver is present and falls
# back to CPU on its own; --cpu forces CPU. We just report the mode clearly.
if [ "$FORCE_CPU" = 1 ]; then
  export OLLAMA_NUM_GPU=0
  say "Compute: CPU (forced via --cpu) — Gemma 4 runs on CPU; slower but fine for testing."
elif command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
  say "Compute: GPU — $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1). Ollama will use it (auto CPU fallback if the driver can't load)."
else
  warn "Compute: no usable NVIDIA GPU (driver missing?) — Gemma 4 runs on CPU automatically. Works, just slower."
fi

# --- 2. pre-build the vector store so first request is fast ----------------
say "Indexing components…"
python3 -m scripts.db.build_vector_store build >/dev/null 2>&1 || true

# --- 3. start the showcase server ------------------------------------------
python3 -m scripts.serve_builder --port "$PORT" &
SRV=$!
cleanup(){ kill "$SRV" "${TUN:-}" 2>/dev/null; }
trap cleanup INT TERM EXIT
# wait until it answers
for _ in $(seq 1 40); do curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1 && break; sleep 0.25; done
say "Local:  http://127.0.0.1:${PORT}"

# --- 4. public trycloudflare.com tunnel ------------------------------------
if [ "$TUNNEL" = 1 ] && command -v cloudflared >/dev/null 2>&1; then
  say "Opening a public trycloudflare.com tunnel… (Ctrl-C stops everything)"
  : > /tmp/ohh_tunnel.log
  cloudflared tunnel --url "http://localhost:${PORT}" --no-autoupdate >/tmp/ohh_tunnel.log 2>&1 &
  TUN=$!
  URL=""
  for _ in $(seq 1 60); do
    URL=$(grep -Eo 'https://[a-z0-9.-]+\.trycloudflare\.com' /tmp/ohh_tunnel.log | head -1)
    [ -n "$URL" ] && break
    sleep 1
  done
  if [ -n "$URL" ]; then
    mkdir -p dist; echo "$URL" > dist/showcase-tunnel-url.txt
    say ""
    say "═══════════════════════════════════════════════════════════════"
    say "  PUBLIC URL  →  $URL"
    say "  send this to your tester · saved to dist/showcase-tunnel-url.txt"
    say "═══════════════════════════════════════════════════════════════"
  else
    warn "Tunnel started but no URL yet — tail /tmp/ohh_tunnel.log (it may still come up)."
  fi
  wait "$TUN"
elif [ "$TUNNEL" = 1 ]; then
  warn "──────────────────────────────────────────────────────────────────────"
  warn "  No public URL: 'cloudflared' is not installed. Install it (Linux,"
  warn "  no sudo) then re-run this script:"
  warn "    mkdir -p ~/.local/bin && curl -L \\"
  warn "      https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \\"
  warn "      -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared"
  warn "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  warn "  The site is live locally at http://127.0.0.1:${PORT} in the meantime."
  warn "──────────────────────────────────────────────────────────────────────"
  wait "$SRV"
else
  wait "$SRV"
fi
