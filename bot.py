import os
import logging
from telegram.ext import Updater, MessageHandler, Filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_MAPPING = {
    -4973230673: 11,
    -1002705141042: 2,
}
TARGET_CHAT_ID = -1002290371611

def forward_message(update, context):
    """Пересылает сообщение в соответствующий топик"""
    chat_id = update.effective_chat.id
    
    if chat_id in CHAT_MAPPING:
        try:
            update.message.forward(
                chat_id=TARGET_CHAT_ID,
                message_thread_id=CHAT_MAPPING[chat_id]
            )
            logger.info(f"✅ Переслано из чата {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

def run_bot():
    """Запускает Telegram бота"""
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Добавляем обработчик ВСЕХ сообщений
        dp.add_handler(MessageHandler(Filters.all, forward_message))
        
        logger.info("🤖 Бот запущен и ожидает сообщений...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка бота: {e}")

if __name__ == '__main__':
    run_bot()
