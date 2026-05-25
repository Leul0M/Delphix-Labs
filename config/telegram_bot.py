"""
Telegram front-end — overlay on Ollama.

Starts Ollama in the background, forwards messages to the local agent, returns replies.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config.agent import FALLBACK_MODEL, HIGH_RAM_MODELS, get_agent
from config.ollama_service import ensure_ollama_background
from config.skills_manager import SkillsManager, get_skills_dir

INSTALL_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(INSTALL_ROOT / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:2b")


def _ensure_runtime() -> bool:
    log_file = INSTALL_ROOT / "ollama.log"
    if not ensure_ollama_background(log_file):
        return False
    get_skills_dir().mkdir(parents=True, exist_ok=True)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    skills = SkillsManager().list_skills()
    skill_note = (
        f"\n• 🧩 {len(skills)} saved skill(s) in skills/"
        if skills
        else "\n• 🧩 Skills folder ready (new tasks can create scripts)"
    )
    ram_warn = ""
    if OLLAMA_MODEL in HIGH_RAM_MODELS:
        ram_warn = (
            f"\n⚠️ `{OLLAMA_MODEL}` needs ~12GB RAM. This PC may only have ~6GB free.\n"
            f"Change .env to OLLAMA_MODEL={FALLBACK_MODEL} and run: ollama pull {FALLBACK_MODEL}\n"
        )
    await update.message.reply_text(
        "Delphix Labs is online.\n\n"
        f"• Ollama model: {OLLAMA_MODEL}{ram_warn}\n"
        "• Telegram ↔ Ollama overlay active\n"
        f"{skill_note}\n\n"
        "Send any message — it goes to Ollama and the reply comes back here.\n"
        'Force skills mode: skill: "your task here"\n'
        "Commands: /help /skills /clear"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Delphix Labs (Telegram + Ollama)\n\n"
        "/start — status\n"
        "/skills — list saved Python skills\n"
        "/clear — reset chat history with Ollama\n"
        "/help — this message\n\n"
        "How it works:\n"
        "1. Ollama runs in the background on this PC\n"
        "2. Your message is sent to the local model\n"
        "3. The reply is sent here on Telegram\n"
        "4. If the model cannot do something, it may create a reusable script in skills/\n\n"
        'Skill mode:\n'
        '  skill: "list my workspace files"\n'
        "  → runs a matching skill, then Ollama explains the result"
    )


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mgr = SkillsManager()
    skills = mgr.list_skills()
    if not skills:
        await update.message.reply_text(
            f"No skills yet.\nFolder: {mgr.skills_dir}\n\n"
            "Ask for a task the model cannot do directly — it can create a skill."
        )
        return
    lines = [f"Skills ({mgr.skills_dir}):\n"]
    for s in skills:
        lines.append(f"• {s.skill_id} — {s.description}")
    await update.message.reply_text("\n".join(lines)[:4000])


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_agent().conversation_history = []
    await update.message.reply_text("Chat history with Ollama cleared.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_runtime():
        await update.message.reply_text(
            "Ollama is not running and could not be started.\n"
            "Install Ollama and run: ollama serve"
        )
        return

    user_message = update.message.text
    user_id = update.effective_user.id
    logger.info("Telegram → Ollama (%s): %s...", user_id, user_message[:80])

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    try:
        response = await get_agent().chat(user_message)
        if len(response) > 4000:
            response = response[:4000] + "\n... (truncated)"
        await update.message.reply_text(response)
        logger.info("Ollama → Telegram (%s): %d chars", user_id, len(response))
    except Exception as e:
        logger.exception("Agent error")
        await update.message.reply_text(f"Error: {e}")


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Add it to .env before starting the bot."
        )

    os.environ.setdefault("DELPHIX_INSTALL_DIR", str(INSTALL_ROOT))
    log_file = INSTALL_ROOT / "ollama.log"
    if ensure_ollama_background(log_file):
        logger.info("Ollama background service ready (model: %s)", OLLAMA_MODEL)
    else:
        logger.warning("Ollama not started — messages may fail until ollama serve runs")

    get_skills_dir().mkdir(parents=True, exist_ok=True)

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("skills", skills_command))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Telegram overlay listening (install: %s)", INSTALL_ROOT)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
