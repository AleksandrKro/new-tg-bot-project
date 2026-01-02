import os
import logging
import threading
import time
from flask import Flask
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
    int(os.getenv('SOURCE_CHAT_1', '-4973230673')): int(os.getenv('TARGET_TOPIC_1', '11')),
    int(os.getenv('SOURCE_CHAT_2', '-1002705141042')): int(os.getenv('TARGET_TOPIC_2', '2')),
}
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID', '-1002290371611'))

# Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot активен", 200

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

@app.route('/ping')
def ping():
    return "pong", 200

def forward_message(update, context):
    """Пересылает сообщение"""
    chat_id = update.effective_chat.id
    
    if chat_id in CHAT_MAPPING:
        try:
            update.message.forward(
                chat_id=TARGET_CHAT_ID,
                message_thread_id=CHAT_MAPPING[chat_id]
            )
            logger.info(f"✅ Переслано из {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

def run_bot():
    """Запускает бота"""
    if not TOKEN:
        logger.error("❌ Токен не установлен!")
        return
    
    while True:
        try:
            logger.info("🚀 Запуск Telegram бота...")
            
            updater = Updater(TOKEN, use_context=True)
            dp = updater.dispatcher
            
            # Добавляем обработчик ВСЕХ сообщений
            dp.add_handler(MessageHandler(Filters.all, forward_message))
            
            logger.info("🤖 Бот запущен и слушает сообщения...")
            updater.start_polling()
            updater.idle()
            
        except Exception as e:
            logger.error(f"💥 Ошибка: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

def start_bot_thread():
    """Запускает бота в отдельном потоке"""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

def main():
    """Основная функция"""
    logger.info("🔄 Инициализация Web Service...")
    
    # Запускаем бота в фоне
    start_bot_thread()
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🌐 Запуск веб-сервера на порту {port}")
    
    # Используем простой Flask сервер
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    main()
