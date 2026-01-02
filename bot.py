import os
import logging
import time
from telegram.ext import Updater, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_MAPPING = {-4973230673: 11, -1002705141042: 2}
TARGET_CHAT_ID = -1002290371611

def forward_message(update, context):
    chat_id = update.effective_chat.id
    if chat_id in CHAT_MAPPING:
        try:
            update.message.forward(
                chat_id=TARGET_CHAT_ID,
                message_thread_id=CHAT_MAPPING[chat_id]
            )
            logging.info(f"✅ Переслано из {chat_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")

def main():
    while True:
        try:
            logging.info("🚀 Запуск бота...")
            updater = Updater(TOKEN, use_context=True)
            updater.dispatcher.add_handler(MessageHandler(Filters.all, forward_message))
            updater.start_polling()
            updater.idle()
        except Exception as e:
            logging.error(f"Ошибка: {e}. Перезапуск через 10 сек...")
            time.sleep(10)

if __name__ == '__main__':
    main()
