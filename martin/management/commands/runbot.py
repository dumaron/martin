from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo hello for every message."""
        await update.message.reply_text("hello")

    def handle(self, *args, **options):
        """Run the bot."""
        # Create application
        application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

        # Start the bot
        self.stdout.write(self.style.SUCCESS('Starting bot...'))
        application.run_polling(allowed_updates=Update.ALL_TYPES)