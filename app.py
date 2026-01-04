import os
import sys
import time
import logging
from flask import Flask, jsonify
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import threading

# ========== НАСТРОЙКА ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не установлен!")
    print("   Render Dashboard → Settings → Environment → BOT_TOKEN=ваш_токен")
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
        "config": {
            "source_chats": len(SOURCE_CHAT_TO_TOPIC),
            "target_chat": TARGET_CHAT_ID
        }
    }), 200

# ========== СИНХРОННАЯ ЛОГИКА БОТА ==========
def forward_message_sync(bot: Bot, chat_id: int, message_id: int, topic_id: int):
    """Синхронная функция для пересылки сообщений"""
    try:
        bot.forward_message(
            chat_id=TARGET_CHAT_ID,
            from_chat_id=chat_id,
            message_id=message_id,
            message_thread_id=topic_id
        )
        logger.info(f"✅ Переслано из {chat_id} в топик {topic_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка пересылки из {chat_id}: {e}")
        return False

# ========== АСИНХРОННЫЕ ОБРАБОТЧИКИ ==========
async def start_command(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Бот-пересылка активен!")

async def forward_message_async(update, context: ContextTypes.DEFAULT_TYPE):
    """Асинхронный обработчик, который вызывает синхронную функцию в отдельном потоке"""
    chat_id = update.effective_chat.id
    
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        
        # Запускаем синхронную функцию в отдельном потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            forward_message_sync,
            context.bot,
            chat_id,
            update.message.message_id,
            target_topic_id
        )

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

# ========== ЗАПУСК БОТА ==========
def run_bot():
    """Запускает бота в отдельном потоке с собственным event loop"""
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Создаем приложение бота без job_queue (чтобы избежать weak reference)
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message_async))
        application.add_error_handler(error_handler)
        
        logger.info("🤖 Бот запущен...")
        logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
        
        # Запускаем polling
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.start())
        
        # Запускаем polling вручную, без использования стандартного run_polling
        updater = application.updater
        if updater:
            loop.run_until_complete(updater.start_polling(
                allowed_updates=None,
                drop_pending_updates=True
            ))
        
        logger.info("✅ Бот успешно запущен и ожидает сообщений...")
        
        # Бесконечный цикл (удерживаем поток активным)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(application.stop())
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

# ========== ОСНОВНОЙ ЗАПУСК ==========
def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    print(f"✅ Python версия: {sys.version}")
    print(f"✅ Токен: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"🔧 Чатов: {len(SOURCE_CHAT_TO_TOPIC)}")
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
    
    # Ждем немного, чтобы бот успел запуститься
    time.sleep(3)
    
    # Запускаем Flask в основном потоке
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask запущен на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
