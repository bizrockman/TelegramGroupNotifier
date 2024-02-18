# TelegramGroupNotifier

TelegramGroupNotifier is an advanced bot designed to automatically publish messages from a Supabase database to Telegram groups or channels. This bot supports scheduling messages for future delivery, including text, images, audio, and other multimedia content, based on schedules set in the Supabase database.

## Features

- **Automated Message Publishing**: Sends messages automatically based on a schedule or immediately as new content appears in the database.
- **Support for Various Media Types**: Capable of handling text, images, audio, and HTML content.
- **Scheduled Sending**: Allows for scheduling messages to be sent at future times.
- **Topic-Based Messages**: Supports sending messages based on specific topics or categories.

## Prerequisites

Before setting up TelegramGroupNotifier, ensure you have the following:

- A Supabase account and a configured database.
- A Telegram bot token created via BotFather in Telegram.
- Python 3.8 or newer.

## Quick Start

1. **Clone the Repository:**

git clone https://github.com/bizrockman/TelegramGroupNotifier.git

2. **Install Dependencies:**

Navigate to the project directory and run:
pip install -r requirements.txt


3. **Configure Environment Variables:**

Create a `.env` file in the project's root directory and define the following variables:

SUPABASE_URL=Your_Supabase_URL\
SUPABASE_KEY=Your_Supabase_Key\
TELEGRAM_TOKEN=Your_Telegram_Bot_Token\
CHAT_ID=Your_Telegram_Chat_Id

4. **Start the Bot:**

python bot.py

## Usage

After starting the bot, it will automatically monitor new entries in the `t_telegram_messages` table in your Supabase database and send messages according to the schedule set or immediately as new content appears.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.


Project Link: https://github.com/bizrockman/TelegramGroupNotifier
