import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent import get_agent

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Local Agent Online!\n\n"
        "I can help you with:\n"
        "• 📁 Reading files (from ~/agent_workspace)\n"
        "• 🖥️ Running shell commands\n"
        "• 💬 General chat\n\n"
        "Just type your request!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help\n\n"
        "Examples:\n"
        "• 'Read the file test.txt'\n"
        "• 'Run ls -la'\n"
        "• 'What can you do?'"
    )

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent = get_agent()
    agent.conversation_history = []
    await update.message.reply_text("🧹 Conversation history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Message from {user_id}: {user_message[:50]}...")
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    try:
        agent = get_agent()
        response = await agent.chat(user_message)
        
        # Telegram has 4096 char limit
        if len(response) > 4000:
            response = response[:4000] + "\n... (truncated)"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()