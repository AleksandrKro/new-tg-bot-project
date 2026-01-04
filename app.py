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

# ========== TELEGRAM БОТ ==========
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def handle_start(message: Message):
    """Обработчик команд /start и /help"""
    bot.reply_to(
        message,
        "🤖 Бот-пересылка активен!\n\n"
        "Сообщения из отслеживаемых чатов автоматически пересылаются "
        "в целевой чат с соответствующими темами.\n\n"
        "Для проверки отправьте сообщение в один из отслеживаемых чатов."
    )

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document', 'audio', 'video', 'voice', 'sticker'])
def handle_all_messages(message: Message):
    """Обработчик всех типов сообщений"""
    chat_id = message.chat.id
    
    # Проверяем, нужно ли пересылать из этого чата
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        
        try:
            # Пересылаем сообщение с указанием топика
            forwarded = bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=message.message_id,
                message_thread_id=target_topic_id
            )
            
            if forwarded:
                user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
                logger.info(f"✅ Переслано от {user_info} из чата {chat_id} в топик {target_topic_id}")
            else:
                logger.warning(f"⚠️ Не удалось переслать сообщение из чата {chat_id}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при пересылке из {chat_id}: {str(e)[:100]}")

def run_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        logger.info("🤖 Запуск Telegram бота...")
        logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
        
        # Удаляем вебхук, если он был установлен ранее
        bot.remove_webhook()
        
        # Запускаем polling с правильными параметрами
        bot.polling(
            non_stop=True,           # Не останавливаться при ошибках
            interval=1,              # Интервал опроса (сек)
            timeout=60,              # Таймаут запроса
            long_polling_timeout=60, # Таймаут long polling
            logger_level=logging.INFO,
            skip_pending=True        # Пропустить ожидающие обновления
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в работе бота: {e}")
        # Пытаемся перезапустить через 10 секунд
        time.sleep(10)
        run_bot()

def run_flask():
    """Запускает Flask сервер для ping-запросов"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask запущен на порту {port}")
    
    # Отключаем логирование Flask на уровне INFO, чтобы не засорять логи
    flask_log = logging.getLogger('werkzeug')
    flask_log.setLevel(logging.WARNING)
    
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    print(f"✅ Python версия: {sys.version.split()[0]}")
    print(f"✅ Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"🔧 Настроено чатов: {len(SOURCE_CHAT_TO_TOPIC)}")
    print(f"🎯 Целевой чат: {TARGET_CHAT_ID}")
    
    if SOURCE_CHAT_TO_TOPIC:
        print("📋 Отслеживаемые чаты:")
        for chat_id, topic_id in SOURCE_CHAT_TO_TOPIC.items():
            print(f"   • Чат {chat_id} → топик {topic_id}")
    
    print("=" * 60)
    print("⚙️  Библиотека: pyTelegramBotAPI 4.21.0")
    print("📡 Режим работы: Long-Polling")
    print("=" * 60)
    print("📋 После запуска настройте UptimeRobot:")
    print("   URL: https://ваш-сервис.onrender.com")
    print("   Интервал: 5 минут")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Даем боту время на запуск
    time.sleep(5)
    
    # Запускаем Flask в основном потоке
    run_flask()

if __name__ == '__main__':
    main()
