import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import asyncio
from aiohttp import web
import socket

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

# ========== HTTP СЕРВЕР ДЛЯ PING ==========
async def handle_ping(request):
    """Обработчик ping-запросов"""
    return web.Response(text="✅ Бот активен! Сообщения пересылаются автоматически.")

async def handle_health(request):
    """Обработчик health check"""
    data = {
        "status": "healthy",
        "service": "telegram-forward-bot",
        "config": {
            "source_chats_configured": len(SOURCE_CHAT_TO_TOPIC),
            "target_chat_id": TARGET_CHAT_ID,
            "bot_token_set": bool(BOT_TOKEN)
        }
    }
    return web.json_response(data)

async def start_http_server():
    """Запускает HTTP сервер для ping-запросов"""
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', handle_health)
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🚀 HTTP ping-сервер запущен на порту {port}")
    logger.info(f"🌐 URL для пинга: http://0.0.0.0:{port}")
    
    # Бесконечно держим сервер запущенным
    await asyncio.Event().wait()

# ========== ОСНОВНОЙ ЗАПУСК ==========
async def main():
    """Основная асинхронная функция"""
    # Выводим информацию о конфигурации при запуске
    print("=" * 60)
    print("🚀 ЗАПУСК TELEGRAM БОТА-ПЕРЕСЫЛКИ")
    print("=" * 60)
    
    # Маскируем токен для безопасности в логах
    masked_token = BOT_TOKEN[:10] + "..." + BOT_TOKEN[-5:] if len(BOT_TOKEN) > 15 else "***"
    print(f"✅ Токен бота: {masked_token}")
    
    print(f"🔧 Настроено чатов для пересылки: {len(SOURCE_CHAT_TO_TOPIC)}")
    print(f"🎯 Целевой чат ID: {TARGET_CHAT_ID}")
    
    # Выводим список отслеживаемых чатов
    if SOURCE_CHAT_TO_TOPIC:
        print("📋 Отслеживаемые чаты:")
        for chat_id, topic_id in SOURCE_CHAT_TO_TOPIC.items():
            print(f"   • Чат {chat_id} → топик {topic_id}")
    
    # Проверяем конфигурацию
    if not SOURCE_CHAT_TO_TOPIC:
        print("⚠️  ВНИМАНИЕ: SOURCE_CHAT_TO_TOPIC пуст!")
        print("   Добавьте ID чатов и топиков в строки 16-19")
    
    print("=" * 60)
    print("📋 После запуска настройте UptimeRobot для пинга:")
    print("   URL: https://ваш-сервис.onrender.com")
    print("   Interval: 5 минут")
    print("=" * 60)
    
    # Создаем и настраиваем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Инициализация бота...")
    
    # Запускаем HTTP сервер в фоне
    http_task = asyncio.create_task(start_http_server())
    
    # Даем время HTTP серверу запуститься
    await asyncio.sleep(2)
    
    logger.info("🤖 Бот запущен в режиме Long-Polling...")
    logger.info(f"📡 Отслеживается {len(SOURCE_CHAT_TO_TOPIC)} чат(ов)")
    logger.info(f"🎯 Целевой чат: {TARGET_CHAT_ID}")
    
    # Запускаем бота
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    logger.info("✅ Бот успешно запущен и ожидает сообщений...")
    
    # Ждем, пока работают оба сервиса
    await asyncio.gather(
        http_task,
        # Бот работает в фоне через polling
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
