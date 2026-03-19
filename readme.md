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

- Installs and configures a local Telegram bot that acts as an AI assistant.
- Pulls and runs an Ollama model (`qwen3.5:4b` by default).
- Starts an Ollama server locally and connects the bot to it.
- Provides a basic tool system (read files, run shell commands) with safe boundaries.

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

The installer will:

1. Verify Python is 3.8+.
2. Ensure Ollama is installed (attempt install if missing).
3. Pull the default model: **qwen3.5:4b**.
4. Start the Ollama server in the background.
5. Create a virtual environment and install Python dependencies.
6. Prompt for your Telegram bot token (from BotFather) and write it to `.env`.
7. Ask whether you want to start the Delphix Labs agent immediately.

---

## 🧩 How it works

### 1) Ollama server

- Ollama runs locally on `http://localhost:11434`.
- The installer starts `ollama serve` in the background and logs output to `ollama.log`.
- The agent communicates with Ollama via its HTTP API.

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
- `OLLAMA_MODEL` — model name (default `qwen3.5:4b`)
- `WORKSPACE_DIR` — where tools can operate (default `~/agent_workspace`)

You can edit `.env` to change the model or bot token.

### Changing the Ollama model

Update `.env`:

```ini
OLLAMA_MODEL=qwen3.5:4b
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

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
