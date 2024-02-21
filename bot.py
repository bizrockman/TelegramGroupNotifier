import os
import logging
import requests
import base64

from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, ChatMember
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
from telegram.error import BadRequest

from supabase import create_client, Client

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )


def create_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    return create_client(supabase_url, supabase_key)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! This is the TelegramGroupNotifier.')


def create_telegram_application() -> Application:
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(telegram_token).build()
    # application.add_handler(CommandHandler('start', start_command))
    return application


def get_new_messages(supabase: Client):
    now = datetime.utcnow()
    # Fetch messages where 'schedule_for' is null or less than the current time, and 'sent_at' is null.
    result = supabase.table('v_telegram_messages_with_topics') \
        .select('*') \
        .or_('schedule_for.lte.{},schedule_for.is.null'.format(now.isoformat())) \
        .is_('sent_at', 'null') \
        .order('created_at') \
        .execute()

    return result.data


async def process_and_send_new_messages(context: CallbackContext):
    chat_id = os.getenv("CHAT_ID")
    supabase_client: Client = context.job.data['supabase_client']

    new_messages = get_new_messages(supabase_client)

    if new_messages:
        for message in new_messages:
            await send_message(context, chat_id, message)
            update_message_status(supabase_client, message['id'])


async def send_message(context: CallbackContext, chat_id: str, message: dict):
    content = message.get('content')

    parse_mode = 'HTML' if content and '<' in content and '>' in content else None
    media = await prepare_media(message)

    message_thread_id = message.get('group_topic_id')
    #message_thread_id = get_message_thread_id_by_topic_name(supabase_client, topic) # COmmeted because bad db design with string

    # TODO make it cleaner
    message_object = None

    if message.get('media_type') == 'image' and content and media:
        message_object = await context.bot.send_photo(chat_id=chat_id, photo=media, message_thread_id=message_thread_id,caption=content, parse_mode=parse_mode)
    elif message.get('media_type') == 'video' and content and media:
        message_object = await context.bot.send_video(chat_id=chat_id, video=media, message_thread_id=message_thread_id,caption=content, parse_mode=parse_mode)
    elif message.get('media_type') == 'audio' and content and media:
        message_object = await context.bot.send_audio(chat_id=chat_id, audio=media, message_thread_id=message_thread_id,caption=content, parse_mode=parse_mode)
    elif content:
        message_object = await context.bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=content, parse_mode=parse_mode)
    elif media:
        if message.get('media_type') == 'image':
            message_object = await context.bot.send_photo(chat_id=chat_id, photo=media, message_thread_id=message_thread_id)
        elif message.get('media_type') == 'video':
            message_object = await context.bot.send_video(chat_id=chat_id, video=media, message_thread_id=message_thread_id)
        elif message.get('media_type') == 'audio':
            message_object = await context.bot.send_audio(chat_id=chat_id, audio=media, message_thread_id=message_thread_id)

    #TODO: Thinking about pinning the message
    #if message_object:
    #    await context.bot.pin_chat_message(chat_id=chat_id, message_id=message_object.message_id)


def get_message_thread_id_by_topic_name(supabase: Client, topic_name: str):
    result = supabase.table('t_telegram_group_topics') \
        .select('group_topic_id') \
        .eq('group_topic_name', topic_name) \
        .execute()

    # Überprüfen Sie das Ergebnis und geben Sie die ID zurück, wenn ein Eintrag gefunden wurde.
    if result.data:
        return result.data[0]['group_topic_id']
    else:
        return None


async def prepare_media(message: dict):
    media_content = message.get('media_content')
    media_url = message.get('media_url')

    if media_content:
        return BytesIO(base64.b64decode(media_content))
    elif media_url:
        response = requests.get(media_url)
        return BytesIO(response.content)
    return None


def update_message_status(supabase: Client, message_id: int):
    now = datetime.utcnow()
    supabase.table('t_telegram_messages') \
        .update({'sent_at': now.isoformat(), 'status': 'sent'}) \
        .eq('id', message_id) \
        .execute()


def main():
    setup_logging()
    load_dotenv()

    supabase_client: Client = create_supabase_client()
    telegram_application: Application = create_telegram_application()

    (telegram_application.job_queue.run_repeating(process_and_send_new_messages,
                                                  interval=10, first=0, data={'supabase_client': supabase_client}))

    print('Telegram Bot started ...')
    # Run the bot until the user presses Ctrl-C
    telegram_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
