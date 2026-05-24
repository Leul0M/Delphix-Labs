#!/usr/bin/env bash
# Install script for Delphix Labs local agent.
# Usage: curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/install.sh | bash

set -euo pipefail

# Allow overriding the repo root via environment variable
REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main}"
INSTALL_PY_URL="$REPO_RAW/install.py"

PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  echo "Error: Python 3.8+ not found in PATH. Please install Python and try again." >&2
  exit 1
fi

# If stdin is not a TTY (e.g. curl | bash), run installer non-interactively.
# Requires TELEGRAM_BOT_TOKEN in the environment before piping.
YES_FLAG=""
if [ ! -t 0 ]; then
  YES_FLAG="--yes"
  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN must be set for non-interactive install." >&2
    echo "Example: TELEGRAM_BOT_TOKEN=123456:ABC... curl -fsSL .../install.sh | bash" >&2
    exit 1
  fi
fi

TMP_PY=$(mktemp /tmp/delphix-install.XXXXXX.py)
trap 'rm -f "$TMP_PY"' EXIT

echo "Downloading installer..."
if ! curl -fsSL "$INSTALL_PY_URL" -o "$TMP_PY"; then
  echo "Failed to download install.py from $INSTALL_PY_URL" >&2
  exit 1
fi

echo "Running installer..."
$PYTHON_CMD "$TMP_PY" "$@" $YES_FLAG
