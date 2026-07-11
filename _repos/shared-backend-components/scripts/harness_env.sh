#!/usr/bin/env bash
# scripts/harness_env.sh — put the Ollama Cloud lane on the environment for opencode + aider.
#
#   source scripts/harness_env.sh      # for an interactive opencode / aider session
#
# Single source of the secret: the gitignored .env (owner key). This maps the repo's
# OH_LLM_* / OLLAMA_API_KEY onto the names the harnesses expect (OPENAI_API_BASE / OPENAI_API_KEY
# for aider's openai-compatible path; OLLAMA_API_KEY for opencode's {env:...} interpolation).
# It does NOT print the key.

_harness_repo="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

_harness_load_env() {
  local f="$1" line key val
  [ -f "$f" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line#export }"
    case "$line" in ''|\#*) continue ;; esac
    case "$line" in *=*) ;; *) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    # strip one layer of surrounding quotes
    val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
    export "$key=$val"
  done < "$f"
}

_harness_load_env "$_harness_repo/.env"

# Canonical names the harnesses read. OLLAMA_API_KEY is the model_index canonical var; fall
# back to OH_LLM_API_KEY (what scripts/_llm_client.py reads) so a single key drives everything.
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-${OH_LLM_API_KEY:-}}"
export OPENAI_API_BASE="${OH_LLM_BASE_URL:-https://ollama.com/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-${OLLAMA_API_KEY:-${OH_LLM_API_KEY:-}}}"

if [ -z "${OLLAMA_API_KEY:-}" ]; then
  echo "harness_env: WARNING — no OLLAMA_API_KEY / OH_LLM_API_KEY found in $_harness_repo/.env" >&2
else
  echo "harness_env: Ollama Cloud lane ready (base=$OPENAI_API_BASE, key=<set>, models: glm-5.2 + kimi-k2.7-code)" >&2
fi

unset -f _harness_load_env
