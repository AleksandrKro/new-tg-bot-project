import os
import sys
import time
import logging
import threading
from flask import Flask, jsonify
import telebot
from telebot.types import Message

# ========== НАСТРОЙКА ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("   Добавьте в Render: Settings → Environment → BOT_TOKEN")
    sys.exit(1)

# ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ!
SOURCE_CHAT_TO_TOPIC = {
    -4973230673: 11,          # Чат 1 → топик 11
    -1002705141042: 2,        # Чат 2 → топик 2
}
TARGET_CHAT_ID = -1002290371611

# ===============================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== FLASK ДЛЯ PING ==========
app = Flask(__name__)

@app.route('/')
def ping():
    return "✅ Бот активен! Сообщения пересылаются.", 200

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "telegram-forward-bot",
        "config": {
            "source_chats": len(SOURCE_CHAT_TO_TOPIC),
            "target_chat": TARGET_CHAT_ID,
            "bot_token_set": bool(BOT_TOKEN)
        }
    }), 200

# ========== TELEGRAM БОТ (pyTelegramBotAPI) ==========
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    """Обработчик команды /start"""
    bot.reply_to(message, "🤖 Бот-пересылка активен!\nСообщения автоматически пересылаются в целевой чат.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message: Message):
    """Обработчик всех сообщений"""
    chat_id = message.chat.id
    
    # Проверяем, нужно ли пересылать из этого чата
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        
        try:
            # Пересылаем сообщение
            bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=message.message_id,
                message_thread_id=target_topic_id
            )
            logger.info(f"✅ Переслано сообщение из чата {chat_id} в топик {target_topic_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при пересылке из {chat_id}: {e}")

def run_bot():
    """Запускает Telegram бота"""
    logger.info("🤖 Запуск Telegram бота (pyTelegramBotAPI)...")
    logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
    
    # Удаляем вебхук, если он был установлен ранее
    bot.remove_webhook()
    
    # Запускаем polling с настройками
    bot.infinity_polling(
        timeout=60,  # Таймаут в секундах
        long_polling_timeout=60,  # Таймаут long polling
        logger_level=logging.INFO,
        restart_on_change=True,
        skip_pending=True  # Пропустить ожидающие обновления
    )

def run_flask():
    """Запускает Flask сервер для ping-запросов"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask ping-сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    print(f"✅ Python версия: {sys.version}")
    print(f"✅ Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"🔧 Настроено чатов: {len(SOURCE_CHAT_TO_TOPIC)}")
    print(f"🎯 Целевой чат: {TARGET_CHAT_ID}")
    
    if SOURCE_CHAT_TO_TOPIC:
        print("📋 Отслеживаемые чаты:")
        for chat_id, topic_id in SOURCE_CHAT_TO_TOPIC.items():
            print(f"   • Чат {chat_id} → топик {topic_id}")
    
    print("=" * 60)
    print("⚙️  Используется библиотека: pyTelegramBotAPI 4.21.0")
    print("📡 Режим работы: Long-Polling")
    print("=" * 60)
    print("📋 После запуска настройте UptimeRobot для пинга:")
    print(f"   URL: https://ваш-сервис.onrender.com")
    print("   Интервал: 5 минут")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Даем боту время на запуск
    time.sleep(5)
    logger.info("✅ Telegram бот запущен в фоновом режиме")
    
    # Запускаем Flask в основном потоке
    run_flask()

if __name__ == '__main__':
    main()
