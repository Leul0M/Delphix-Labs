#!/usr/bin/env bash
# Install script for Delphix Labs local agent.
# Usage: curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/install.sh | bash

set -euo pipefail

# Allow overriding the repo root via environment variable
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main}"
# Files needed beside install.py (install.py copies these into ~/local-agent)
BUNDLE_FILES=(
  install.py
  requirements.txt
  config/__init__.py
  config/agent.py
  config/telegram_bot.py
  config/ollama_service.py
  config/skills_manager.py
  config/security.py
  skills/README.md
  skills/list_workspace.py
  skills/list_workspace.json
  templates/.env.example
)

PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  echo "Error: Python 3.8+ not found in PATH. Please install Python and try again." >&2
  exit 1
fi

# curl | bash has no stdin TTY. Two modes:
#   - TELEGRAM_BOT_TOKEN set  -> fully non-interactive (--yes)
#   - token not set           -> interactive prompts via /dev/tty (install.py)
YES_FLAG=""
if [ ! -t 0 ]; then
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    YES_FLAG="--yes"
    echo "Using TELEGRAM_BOT_TOKEN from the environment (non-interactive install)."
  else
    echo "Piped install detected. You will be prompted for your Telegram bot token in this terminal."
    echo "Tip: get a token from @BotFather on Telegram (/newbot)."
    echo ""
  fi
fi

TMP_DIR=$(mktemp -d /tmp/delphix-install.XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT

fetch_raw() {
  local rel="$1"
  local dest="$TMP_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  if ! curl -fsSL "$REPO_RAW/$rel" -o "$dest"; then
    echo "Failed to download $REPO_RAW/$rel" >&2
    exit 1
  fi
}

echo "Downloading installer bundle..."
for rel in "${BUNDLE_FILES[@]}"; do
  fetch_raw "$rel"
done

echo "Running installer..."
$PYTHON_CMD "$TMP_DIR/install.py" "$@" $YES_FLAG
