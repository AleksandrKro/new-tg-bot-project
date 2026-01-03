import os
import logging
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ========== НАСТРОЙКА ==========
# 1. Токен бота. ЗАПОЛНИТЬ!
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН_ОТ_BOTFATHER')

# 2. Настройки пересылки. ЗАПОЛНИТЬ!
# Ключ: ID исходного чата. Значение: ID темы (топика) в целевом чате.
# ID чата можно получить через бота @userinfobot или @getidsbot
# ID топика (темы) — число, которое можно скопировать из ссылки на сообщение в теме.
SOURCE_CHAT_TO_TOPIC = {
    -1001234567890: 12,  # Пример: из чата -1001234567890 -> в топик 12
    -1009876543210: 34,  # из чата -1009876543210 -> в топик 34
}

# 3. ID целевого чата (куда пересылаем). ЗАПОЛНИТЬ!
TARGET_CHAT_ID = -1001111111111  # Замените на ваш чат

# 4. Проверка: бот должен быть админом ВО ВСЕХ указанных чатах!
# ===============================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ЛОГИКА БОТА ==========
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
                message_thread_id=target_topic_id  # Ключевой параметр для топика!
            )
            logger.info(f"Переслано из {chat_id} в топик {target_topic_id}")
        except Exception as e:
            logger.error(f"Ошибка пересылки из {chat_id}: {e}")

# ========== FLASK ДЛЯ PING ==========
# Этот сервер нужен ТОЛЬКО для ответа на ping-запросы от сервисов мониторинга.
app = Flask(__name__)

@app.route('/')
def ping():
    return "Bot is alive!", 200

# ========== ЗАПУСК ==========
def run_bot():
    """Запускает бота в отдельном потоке."""
    # Создаем приложение бота
    bot_app = Application.builder().token(BOT_TOKEN).build()
    # Добавляем обработчик ВСЕХ входящих сообщений (кроме команд)
    bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
    # Запускаем бота в режиме Long-Polling
    logger.info("Бот запущен в режиме Long-Polling...")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

def main():
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Получаем порт от Render (или используем 10000 по умолчанию)
    port = int(os.environ.get("PORT", 10000))
    # Запускаем Flask-сервер для пинга на всех интерфейсах (0.0.0.0)
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    main()
