# 🧠 Delphix Labs

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange)](https://ollama.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0)](https://telegram.org)

> **Run your own AI agent locally. Private, secure, and fully under your control.**

Delphix Labs provides a lightweight local AI agent framework that runs on your machine using Ollama + Telegram. The installer creates a virtual environment, configures a Telegram bot, pulls an Ollama model, starts the Ollama server, and lets you interact with the agent via chat.

---

## 📌 Table of Contents

- [What it does](#what-it-does)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [How it works](#how-it-works)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## ✅ What it does

- **Telegram overlay on Ollama** — every message goes to your local model; replies return on Telegram.
- **Ollama in the background** — `ollama serve` starts automatically when you run the bot.
- **Skills folder** — when Ollama cannot do a task directly, it can save a reusable Python script under `skills/` and use it again later.
- Built-in tools: read files, run shell commands (in `~/agent_workspace`).

---

## 🧰 Prerequisites

1. **Python 3.8+** (required for the installer and Telegram bot)
2. **Ollama** (local AI runtime)
   - Download/install from: https://ollama.com/download
3. **Telegram account** (to create a bot via BotFather)

> Tip: The installer will try to install Ollama automatically on macOS/Linux, but on Windows it will ask you to install it manually.

---

## 🚀 Setup

From this repository root, run:

```bash
python install.py
```

Or install directly from GitHub using curl (you will be prompted for your bot token):

```bash
curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/install.sh | bash
```

Fully automated install (no prompts; token must be set first):

```bash
TELEGRAM_BOT_TOKEN="123456789:YOUR_TOKEN" curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/install.sh | bash
```

The installer will:

1. Verify Python is 3.8+.
2. Ensure Ollama is installed (attempt install if missing).
3. Pull the default model: **llama3.2:2b** (or another model that fits your RAM).
4. Start the Ollama server in the background.
5. Create a virtual environment and install Python dependencies.
6. Prompt for your Telegram bot token (from BotFather) and write it to `.env`.
7. Ask whether you want to start the Delphix Labs agent immediately.

---

## 🧩 How it works

### 1) Telegram ↔ Ollama overlay

```
Telegram message → Python bot → Ollama API → reply → Telegram
```

- Ollama runs locally on `http://localhost:11434` (started in the background by `run.sh` / `run.bat`).
- The Python layer does not replace Ollama — it routes chat and runs tools/skills when needed.

### 2) Skills folder

- Path: `~/local-agent/skills/` (or your install directory).
- Each skill: `name.py` + `name.json` (must define `def run(**kwargs) -> str`).
- List skills in Telegram: `/skills`
- The model reuses saved skills before writing new ones.

### 2) Telegram bot

- The Telegram bot is implemented in `config/telegram_bot.py`.
- It forwards user messages to the agent engine.
- The agent decides whether to respond directly or call a tool (e.g., read a file).

### 3) Tool system

The agent includes a basic tool system in `config/agent.py`:

- `file_read` — read files from the workspace (restricted to safe directories)
- `shell` — execute shell commands in the workspace (with basic command blocking)

Tools are called by sending a JSON payload from model output.

---

## ▶️ Usage

### Start the agent (after install)

If you chose **not** to start the agent at the end of installation, run:

```bash
# Linux/macOS
./run.sh

# Windows
run.bat
```

### Interact with the bot

Open Telegram and send messages to your bot:

- `Read welcome.txt` — reads a file from the workspace
- `Run ls -la` — runs a shell command
- Any other question — the model will answer normally

---

## ⚙️ Configuration

### `.env`

The installer creates a `.env` file with:

- `TELEGRAM_BOT_TOKEN` — your bot token
- `OLLAMA_MODEL` — model name (default `llama3.2:2b`)
- `WORKSPACE_DIR` — where tools can operate (default `~/agent_workspace`)

You can edit `.env` to change the model or bot token.

### Changing the Ollama model

Update `.env`:

```ini
OLLAMA_MODEL=llama3.2:2b
```

Then, pull the new model manually and restart the installer/agent:

```bash
ollama pull <model>
```

---

## 🗂️ Project structure

```
local-agent-cli/
├── install.py          # Installer script + setup logic
├── requirements.txt    # Python dependencies
├── config/
│   ├── agent.py        # Agent + tools implementation
│   ├── telegram_bot.py # Telegram bot interface
│   └── security.py     # Security helpers
└── templates/
    └── .env.example    # Example env config
```

---

## 🛠️ Troubleshooting

### `Command not found: home/venv/bin/pip`

The install folder was treated as a relative path named `home` (from the temp install directory), not your real home directory. **Use the latest `install.py`**, press **Enter** at the install path prompt for the default (`~/local-agent`), or type `~` — do not type only `home`.

### `Missing config directory at /tmp/config`

The installer only had `install.py` in `/tmp`, not the full repo. **Use the latest `install.sh`** (it downloads `config/`, `requirements.txt`, etc.), or clone the repo and run `python install.py` from the project root.

### `TELEGRAM_BOT_TOKEN must be set for non-interactive install`

This appeared on older installers when running `curl ... | bash` without a token. **Update to the latest `install.sh`** (or clone the repo and run `python install.py`), then run the curl command again — you should get prompts for your bot token in the same terminal.

Alternatively, set the token before piping:

```bash
TELEGRAM_BOT_TOKEN="123456789:YOUR_TOKEN" curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/install.sh | bash
```

### `model requires more system memory` (Ollama 500)

The chosen model needs more RAM than the PC has free. **`qwen3.5:4b` needs about 12 GB**; many laptops only have ~6–8 GB free.

**Fix on the Ollama machine:**

```bash
ollama pull llama3.2:2b
nano ~/local-agent/.env   # or edit .env on Windows
```

Set:

```env
OLLAMA_MODEL=llama3.2:2b
```

Restart the bot:

```bash
cd ~/local-agent && ./run.sh
```

Other models that usually fit **8 GB RAM or less**: `gemma2:2b`, `phi3:mini`, `qwen2.5:3b`.

### Ollama is not running

- Confirm it is installed: `ollama version`
- Start it manually: `ollama serve`
- Check logs: `ollama.log`

### Telegram bot errors

- Verify `.env` contains a valid token.
- Review bot output for traceback.

### Dependency installation fails

- Ensure you have a working internet connection.
- Try updating pip: `python -m pip install --upgrade pip`

---

## 🧹 Uninstall

To remove the installation (default directory: `~/local-agent`):

```bash
./uninstall.sh
```

Or run directly from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Leul0M/Delphix-Labs/main/uninstall.sh | bash
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
