import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_MAPPING = {
    int(os.getenv('SOURCE_CHAT_1', -4973230673)): int(os.getenv('TARGET_TOPIC_1', 11)),
    int(os.getenv('SOURCE_CHAT_2', -1002705141042)): int(os.getenv('TARGET_TOPIC_2', 2)),
}
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID', -1002290371611))

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в соответствующий топик"""
    chat_id = update.effective_chat.id
    
    if chat_id in CHAT_MAPPING:
        try:
            await update.message.forward(
                chat_id=TARGET_CHAT_ID,
                message_thread_id=CHAT_MAPPING[chat_id]
            )
            logger.info(f"✅ Переслано из чата {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки: {e}")

def run_bot():
    """Функция для запуска бота (вызывается из app.py)"""
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        # Создаем приложение бота
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчик сообщений
        application.add_handler(
            MessageHandler(filters.ALL & ~filters.COMMAND, forward_message)
        )
        
        # Запускаем бота
        logger.info("🤖 Бот запущен и ожидает сообщений...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30,  # Добавляем таймаут
            pool_timeout=30  # Добавляем pool_timeout
        )
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка бота: {e}")
        logger.error("Полная ошибка:", exc_info=True)

# Если файл запускается напрямую (для тестов)
if __name__ == '__main__':
    run_bot()
