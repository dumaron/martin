#!/usr/bin/env python
# import logging
import os
import sys

import django
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from pydub import AudioSegment
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
load_dotenv()
is_dev = os.getenv('ENV') == 'dev'
if is_dev:
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
else:
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.prod')
django.setup()

# Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

# Define your bot token (you'll get this from BotFather)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


from core.integrations.openai import speech_to_text
from core.models import Inbox


# Command handlers
async def generic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Send a message when the command /start is issued."""
	user = update.effective_user
	await update.message.reply_text(
		f'Hi {user.first_name}! I am your bot.'
	)

async def save_audio_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	audio = await update.message.voice.get_file()
	file_id = update.message.voice.file_unique_id
	path = f'/tmp/{file_id}'
	await audio.download_to_drive(path + '.oga')
	segment = AudioSegment.from_ogg(path + '.oga')
	segment.export(path + '.mp3')
	mp3 = open(path + '.mp3', 'rb')
	transcript = await sync_to_async(speech_to_text)(mp3)
	note = Inbox(content=transcript.text)
	await sync_to_async(note.save)()
	await update.message.reply_text('Note saved')
	os.remove(path + '.oga')
	os.remove(path + '.mp3')


def main() -> None:
	"""Start the bot."""
	application = ApplicationBuilder().token(TOKEN).build()

	application.add_handler(CommandHandler('start', generic_handler))
	application.add_handler(CommandHandler('help', generic_handler))
	application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, save_audio_note))

	application.run_polling()


if __name__ == '__main__':
	main()
