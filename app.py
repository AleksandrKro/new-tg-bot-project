import os
import logging
import threading
from flask import Flask, jsonify
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ========== НАСТРОЙКА ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("   Добавьте в Render: Settings → Environment → BOT_TOKEN")
    exit(1)

# ЗАМЕНИТЕ ЭТИ ДАННЫЕ!
SOURCE_CHAT_TO_TOPIC = {
    -4973230673: 11,  # Пример: из чата ID -1001234567890 в топик 12
    -1002705141042: 2,  # Замените на реальные ID ваших чатов и топиков
}

TARGET_CHAT_ID = -1002290371611  # Замените на ID вашего целевого чата

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
        "config": {
            "source_chats": len(SOURCE_CHAT_TO_TOPIC),
            "target_chat": TARGET_CHAT_ID
        }
    })

# ========== ЛОГИКА БОТА (СИНХРОННАЯ) ==========
def start_command(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    update.message.reply_text(
        "🤖 Бот-пересылка активен!\n"
        "Сообщения автоматически пересылаются в целевой чат."
    )

def forward_message(update: Update, context: CallbackContext):
    """Пересылает сообщение в нужный топик"""
    chat_id = update.effective_chat.id
    
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        
        try:
            # Используем context.bot.forward_message для синхронной версии
            context.bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=update.message.message_id,
                message_thread_id=target_topic_id
            )
            logger.info(f"✅ Переслано из {chat_id} в топик {target_topic_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка бота: {context.error}")

def run_bot():
    """Запускает бота в отдельном потоке"""
    try:
        # Создаем updater (синхронная версия)
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем обработчики
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, forward_message))
        dispatcher.add_error_handler(error_handler)
        
        logger.info("🤖 Бот запущен (python-telegram-bot 13.15)")
        logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
        
        # Запускаем бота
        updater.start_polling()
        
        # Блокируем поток
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

def run_flask():
    """Запускает Flask сервер"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask запущен на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    print(f"✅ Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"🔧 Чатов для пересылки: {len(SOURCE_CHAT_TO_TOPIC)}")
    print(f"🎯 Целевой чат: {TARGET_CHAT_ID}")
    
    for chat_id, topic_id in SOURCE_CHAT_TO_TOPIC.items():
        print(f"   • Чат {chat_id} → топик {topic_id}")
    
    print("=" * 60)
    print("📋 После запуска настройте UptimeRobot:")
    print("   URL: https://ваш-сервис.onrender.com")
    print("   Интервал: 5 минут")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask в основном потоке
    run_flask()

if __name__ == '__main__':
    main()
