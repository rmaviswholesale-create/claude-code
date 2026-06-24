#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.deepseek"

# ── 1. Load env vars ──────────────────────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found."
  echo "  cp $SCRIPT_DIR/.env.deepseek.example $ENV_FILE"
  echo "  Then fill in your DEEPSEEK_API_KEY."
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

if [[ -z "${DEEPSEEK_API_KEY:-}" || "$DEEPSEEK_API_KEY" == "sk-your-deepseek-api-key-here" ]]; then
  echo "ERROR: Set DEEPSEEK_API_KEY in $ENV_FILE"
  exit 1
fi

# ── 2. Start LiteLLM proxy (Anthropic-compatible) ────────────────────────────
echo "Starting LiteLLM proxy on port 4000 (DeepSeek backend)..."
litellm --config "$SCRIPT_DIR/litellm-config.yaml" &
LITELLM_PID=$!

# Give the proxy a moment to bind
sleep 3

# Verify proxy is up
if ! curl -sf http://localhost:4000/health/liveliness > /dev/null 2>&1; then
  echo "WARNING: Proxy may not be ready yet — waiting a few more seconds..."
  sleep 5
fi

echo "Proxy running (PID $LITELLM_PID)"
echo ""

# ── 3. Export env so Claude Code finds the proxy ─────────────────────────────
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_API_KEY="sk-local-proxy"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-4-6}"
export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-claude-haiku-4-5-20251001}"

echo "Claude Code → LiteLLM proxy → DeepSeek V4 Pro"
echo "Run: claude"
echo ""

# ── 4. Launch Claude Code (or drop to shell with the env set) ────────────────
if command -v claude &>/dev/null; then
  claude "$@"
else
  echo "Claude Code CLI not found. Install it with:"
  echo "  npm install -g @anthropic-ai/claude-code"
  echo ""
  echo "Environment is set. Open a new shell after installing and run: claude"
  exec bash
fi

# ── 5. Cleanup ────────────────────────────────────────────────────────────────
trap 'kill $LITELLM_PID 2>/dev/null; echo "Proxy stopped."' EXIT
wait $LITELLM_PID
