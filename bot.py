import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Конфигурация бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_MAPPING = {
    -4973230673: 11,     # Из этого чата → в топик 11
    -1002705141042: 2,   # Из этого чата → в топик 2
}
TARGET_CHAT_ID = -1002290371611  # Целевой чат

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в соответствующий топик"""
    chat_id = update.effective_chat.id
    
    if chat_id in CHAT_MAPPING:
        try:
            await update.message.forward(
                chat_id=TARGET_CHAT_ID,
                message_thread_id=CHAT_MAPPING[chat_id]
            )
            logging.info(f"✅ Переслано из {chat_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")

def main():
    """Запуск бота"""
    if not TOKEN:
        logging.error("❌ Токен не найден! Установите TELEGRAM_BOT_TOKEN")
        return
    
    logging.info("🚀 Запуск бота...")
    
    # Создаем и запускаем бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
