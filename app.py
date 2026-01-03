import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== НАСТРОЙКА ==========
# 1. Токен бота. ЗАПОЛНИТЬ через переменную окружения BOT_TOKEN!
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("Переменная окружения BOT_TOKEN не установлена!")
    exit(1)

# 2. Настройки пересылки. ЗАПОЛНИТЬ!
# Ключ: ID исходного чата. Значение: ID темы (топика) в целевом чате.
# Пример: из чата -1001234567890 -> в топик 12
SOURCE_CHAT_TO_TOPIC = {
    -4973230673: 11,  # ЗАМЕНИТЕ на реальные данные
    -1002705141042: 2,
}

# 3. ID целевого чата (куда пересылаем). ЗАПОЛНИТЬ!
TARGET_CHAT_ID = -1002290371611  # ЗАМЕНИТЕ на ваш чат

# 4. Бот должен быть админом ВО ВСЕХ указанных чатах!
# ===============================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ЛОГИКА БОТА ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start для проверки работы бота."""
    await update.message.reply_text("✅ Бот-пересылка запущен и работает!\n\n"
                                   "Сообщения из настроенных чатов будут автоматически пересылаться в целевой чат с темами.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение из исходного чата в нужный топик целевого чата."""
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    # Проверяем, нужно ли пересылать из этого чата
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        try:
            await context.bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=message_id,
                message_thread_id=target_topic_id
            )
            logger.info(f"✅ Переслано сообщение {message_id} из чата {chat_id} в топик {target_topic_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки из {chat_id}: {e}")
            # Можно добавить уведомление об ошибке в лог, но не в чат, чтобы не спамить

# ========== FLASK ДЛЯ PING ==========
app = Flask(__name__)

@app.route('/')
def ping():
    return "🟢 Бот активен и работает! Если видите это сообщение, значит ping-запросы достигают сервера.", 200

@app.route('/health')
def health():
    """Дополнительный эндпоинт для проверки здоровья сервиса."""
    return {"status": "healthy", "service": "telegram-forward-bot"}, 200

# ========== ЗАПУСК ==========
def run_bot():
    """Запускает бота в отдельном потоке."""
    try:
        # Создаем приложение бота
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчик команды /start
        bot_app.add_handler(CommandHandler("start", start_command))
        
        # Добавляем обработчик ВСЕХ входящих сообщений (кроме команд)
        bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
        
        logger.info("🟢 Бот запущен в режиме Long-Polling...")
        bot_app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в работе бота: {e}")
        # Здесь можно добавить уведомление администратору

def main():
    """Основная функция запуска приложения."""
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Поток бота запущен")

    # Получаем порт от Render (или используем 10000 по умолчанию)
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Запуск Flask-сервера для ping-запросов на порту {port}")
    
    # Запускаем Flask-сервер для пинга
    # На Render нужно слушать на всех интерфейсах (0.0.0.0)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
