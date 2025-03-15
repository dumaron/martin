#!/usr/bin/env python
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# Enable logging
logging.basicConfig(
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
   level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your bot token (you'll get this from BotFather)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Send a message when the command /start is issued."""
   user = update.effective_user
   await update.message.reply_text(f'Hi {user.first_name}! I am your bot. Send me a message and I will echo it back.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Send a message when the command /help is issued."""
   await update.message.reply_text('Help! I can echo back any message you send me.')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   """Echo the user message."""
   await update.message.reply_text(update.message.text)


def main() -> None:
   """Start the bot."""
   # Create the Application
   application = ApplicationBuilder().token(TOKEN).build()

   # Add handlers
   application.add_handler(CommandHandler("start", start))
   application.add_handler(CommandHandler("help", help_command))

   # Messages handler - will echo back any message
   application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

   # Start the Bot
   application.run_polling()

   logger.info("Bot started")


if __name__ == '__main__':
   main()