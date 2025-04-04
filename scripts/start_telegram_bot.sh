#!/bin/bash

# Set the Python path to include the project root
export PYTHONPATH=/Users/duma/dev/martin

# Run the Telegram bot
cd /Users/duma/dev/martin && pipenv run python apps/telegram_bot/main.py