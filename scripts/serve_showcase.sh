#!/usr/bin/env bash
# Run the Open Harness Hub paste-to-flow showcase locally with Gemma intelligence
# and a public trycloudflare.com URL you can send to someone to test.
#
#   bash scripts/serve_showcase.sh                 # auto-detect a local Gemma, open a tunnel
#   bash scripts/serve_showcase.sh --model gemma3  # force a specific Ollama model tag
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
OLLAMA_URL="${OH_LLM_BASE_URL:-http://localhost:11434}"
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    --no-tunnel) TUNNEL=0; shift;;
    -h|--help) sed -n '2,12p' "$0"; exit 0;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

say(){ printf '\033[38;2;251;119;20m%s\033[0m\n' "$*"; }
warn(){ printf '\033[33m%s\033[0m\n' "$*"; }

# --- 1. Gemma via Ollama (OpenAI-compatible) -------------------------------
LLM_OK=0
if curl -sf "${OLLAMA_URL}/api/tags" -o /tmp/ohh_tags.json 2>/dev/null; then
  LLM_OK=1
  if [ -z "$MODEL" ]; then
    # auto-detect the first installed Gemma model tag
    MODEL=$(python3 -c "import json;ts=json.load(open('/tmp/ohh_tags.json')).get('models',[]);g=[m['name'] for m in ts if 'gemma' in m['name'].lower()];print(g[0] if g else (ts[0]['name'] if ts else ''))" 2>/dev/null)
  fi
  if [ -z "$MODEL" ]; then
    warn "Ollama is up but has no models. Pull Gemma:  ollama pull gemma2   (or your Gemma 4 tag)"
    LLM_OK=0; MODEL="gemma2"
  else
    say "Gemma intelligence: ON  (Ollama model: $MODEL)"
  fi
else
  MODEL="${MODEL:-gemma2}"
  warn "Ollama not reachable at ${OLLAMA_URL}. The site will run with the deterministic"
  warn "explainer. To enable Gemma: install Ollama, run 'ollama serve', then"
  warn "'ollama pull $MODEL' (or your Gemma 4 tag) and re-run this script."
fi

# Point the provider-neutral LLM route at Ollama (see scripts/model_routes.py).
export OH_LLM_BACKEND=http-openai
export OH_LLM_BASE_URL="${OLLAMA_URL}/v1"
export OH_LLM_MODEL="$MODEL"
# Embeddings stay offline-placeholder unless OH_EMBED_* is already set (cloud later).

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
if [ "$TUNNEL" = 1 ]; then
  if command -v cloudflared >/dev/null 2>&1; then
    say "Opening a public trycloudflare.com tunnel… (Ctrl-C to stop everything)"
    cloudflared tunnel --url "http://localhost:${PORT}" --no-autoupdate 2>&1 \
      | tee /tmp/ohh_tunnel.log | grep --line-buffered -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' \
      | while read -r u; do say "PUBLIC URL → $u   (send this to your tester)"; done &
    TUN=$!
    wait "$SRV"
  else
    warn "cloudflared not found — serving locally only."
    warn "Install it, then re-run:  brew install cloudflared   (macOS)"
    warn "  or download: https://github.com/cloudflare/cloudflared/releases/latest"
    warn "  then:  cloudflared tunnel --url http://localhost:${PORT}"
    wait "$SRV"
  fi
else
  wait "$SRV"
fi
