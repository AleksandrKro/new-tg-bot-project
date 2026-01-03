import os
import logging
import threading
import asyncio
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# ========== НАСТРОЙКА ==========
# 1. Токен бота (Установите в Render: Settings → Environment → Add Environment Variable)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не установлен!")
    print("   Перейдите в Render Dashboard → Settings → Environment")
    print("   Добавьте переменную: Key=BOT_TOKEN, Value=ваш_токен_от_BotFather")
    exit(1)

# 2. ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА РЕАЛЬНЫЕ!
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
    """Основной эндпоинт для пинга (используется UptimeRobot)"""
    return "✅ Бот активен! Сообщения пересылаются автоматически.", 200

@app.route('/health')
def health():
    """Эндпоинт для проверки состояния сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "telegram-forward-bot",
        "config": {
            "source_chats_configured": len(SOURCE_CHAT_TO_TOPIC),
            "target_chat_id": TARGET_CHAT_ID,
            "bot_token_set": bool(BOT_TOKEN)
        }
    }), 200

# ========== ЛОГИКА БОТА ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот-пересылка активен!\n"
        "Сообщения из настроенных чатов автоматически пересылаются "
        "в целевой чат с соответствующими темами.\n\n"
        "Для проверки работы отправьте сообщение в один из отслеживаемых чатов."
    )

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в нужный топик целевого чата"""
    chat_id = update.effective_chat.id
    
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        user_info = f"@{update.effective_user.username}" if update.effective_user.username else f"ID: {update.effective_user.id}"
        
        try:
            await context.bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=update.message.message_id,
                message_thread_id=target_topic_id
            )
            logger.info(f"✅ Переслано сообщение от {user_info} из чата {chat_id} в топик {target_topic_id}")
            
        except TelegramError as e:
            logger.error(f"❌ Ошибка Telegram при пересылке из {chat_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при пересылке из {chat_id}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок бота"""
    logger.error(f"Ошибка в обработчике бота: {context.error}")

def run_flask():
    """Запускает Flask-сервер для ping-запросов"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask ping-сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    """Запускает Telegram-бота в отдельном потоке"""
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Создаем приложение бота
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
        application.add_error_handler(error_handler)
        
        logger.info("🤖 Бот запущен в режиме Long-Polling...")
        logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
        logger.info(f"🎯 Целевой чат: {TARGET_CHAT_ID}")
        
        # Выводим список отслеживаемых чатов
        for chat_id, topic_id in SOURCE_CHAT_TO_TOPIC.items():
            logger.info(f"   • Чат {chat_id} → топик {topic_id}")
        
        # Запускаем бота
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в работе бота: {e}")
        raise

# ========== ОСНОВНОЙ ЗАПУСК ==========
if __name__ == '__main__':
    # Выводим информацию о конфигурации при запуске
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    
    # Маскируем токен для безопасности в логах
    masked_token = BOT_TOKEN[:10] + "..." + BOT_TOKEN[-5:] if len(BOT_TOKEN) > 15 else "***"
    print(f"✅ Токен бота: {masked_token}")
    
    print(f"🔧 Настроено чатов для пересылки: {len(SOURCE_CHAT_TO_TOPIC)}")
    print(f"🎯 Целевой чат ID: {TARGET_CHAT_ID}")
    
    # Проверяем конфигурацию
    if TARGET_CHAT_ID == -1001111111111:
        print("⚠️  ВНИМАНИЕ: TARGET_CHAT_ID не изменен!")
        print("   Замените -1001111111111 на реальный ID целевого чата в строке 20")
    
    if not SOURCE_CHAT_TO_TOPIC:
        print("⚠️  ВНИМАНИЕ: SOURCE_CHAT_TO_TOPIC пуст!")
        print("   Добавьте ID чатов и топиков в строки 16-19")
    
    print("=" * 60)
    print("📋 После запуска настройте UptimeRobot для пинга:")
    print(f"   URL: https://ваш-сервис.onrender.com")
    print(f"   Interval: 5 минут")
    print("=" * 60)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Поток Telegram бота запущен")
    
    # Запускаем Flask в основном потоке
    logger.info("✅ Запуск Flask ping-сервера...")
    run_flask()
