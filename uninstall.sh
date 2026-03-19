#!/usr/bin/env bash
# Uninstall script for Delphix Labs local agent.
# Usage: curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/uninstall.sh | bash

set -euo pipefail

INSTALL_DIR="${1:-$HOME/local-agent}"

echo "This will remove the Delphix Labs installation at: $INSTALL_DIR"
read -rp "Continue? (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Canceled."
  exit 0
fi

# Attempt to stop running processes (best-effort)
echo "Stopping running Ollama server (if any)..."
if command -v pkill >/dev/null 2>&1; then
  pkill -f "ollama serve" || true
elif command -v killall >/dev/null 2>&1; then
  killall -q ollama || true
else
  echo "Note: pkill/killall not available; please stop Ollama manually." >&2
fi

echo "Stopping running agent bot (if any)..."
if command -v pkill >/dev/null 2>&1; then
  pkill -f "config.telegram_bot" || true
elif command -v killall >/dev/null 2>&1; then
  killall -q python || true
else
  echo "Note: pkill/killall not available; please stop the bot manually." >&2
fi

if [[ -d "$INSTALL_DIR" ]]; then
  echo "Removing $INSTALL_DIR..."
  rm -rf "$INSTALL_DIR"
else
  echo "No installation directory found at $INSTALL_DIR"
fi

echo "Uninstall complete."
