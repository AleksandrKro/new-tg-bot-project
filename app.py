# =============================================================================
# 📘 TELEGRAM MESSAGE FORWARDER BOT
# =============================================================================
# Этап 3: Разработка кода
# Этот скрипт реализует Telegram-бота для автоматической пересылки сообщений
# из заданных чатов в целевой чат с распределением по темам (топикам).
# Также включает в себя Flask-сервер для поддержания активности на хостинге.
# =============================================================================

# -----------------------------------------------------------------------------
# 3.3.1. Импорты и основные настройки
# -----------------------------------------------------------------------------
import os
import threading
import logging
import telebot
from flask import Flask, jsonify

# --- Конфигурация ---
# Токен бота загружается из переменных окружения для безопасности.
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
except KeyError:
    print("Ошибка: Переменная окружения BOT_TOKEN не установлена.")
    # В локальной среде можно временно задать токен так:
    # BOT_TOKEN = "ВАШ_ТОКЕН"
    # Но не загружайте это на GitHub!
    exit()

# Словарь соответствия: {ID исходного чата: ID целевого топика}
# Данные предоставлены пользователем.
SOURCE_CHAT_TO_TOPIC = {
    -4973230673: 11,
    -1002705141042: 2,
}

# ID целевого чата, куда будут пересылаться все сообщения.
# Данные предоставлены пользователем.
TARGET_CHAT_ID = -1002290371611

# -----------------------------------------------------------------------------
# 3.3.2. Настройка логирования
# -----------------------------------------------------------------------------
# Настраиваем формат логов для удобного отслеживания работы бота.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 3.3.3. Flask ping-сервер
# -----------------------------------------------------------------------------
# Этот веб-сервер нужен, чтобы хостинг (Render.com) не переводил
# нашего бота в спящий режим. UptimeRobot будет периодически
# обращаться к этому серверу.
app = Flask(__name__)

@app.route('/')
def ping():
    """Основной эндпоинт для проверки активности."""
    return "✅ Бот для пересылки сообщений активен!", 200

@app.route('/health')
def health_check():
    """Эндпоинт для более детальной проверки статуса."""
    # В будущем здесь можно добавить проверку доступности Telegram API
    return jsonify({"status": "healthy"}), 200

# -----------------------------------------------------------------------------
# 3.3.4. Обработчики Telegram
# -----------------------------------------------------------------------------
# Инициализируем бота с использованием токена.
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработчик команды /start."""
    bot.reply_to(message, f"🤖 Бот-пересыльщик запущен и работает. Целевой чат: {TARGET_CHAT_ID}")
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'video_note'])
def forward_message(message):
    """
    Главный обработчик. Пересылает любое сообщение из исходных чатов
    в соответствующий топик целевого чата.
    """
    chat_id = message.chat.id

    # Проверяем, есть ли текущий чат в нашем списке источников.
    if chat_id in SOURCE_CHAT_TO_TOPIC:
        target_topic_id = SOURCE_CHAT_TO_TOPIC[chat_id]
        try:
            # Используем встроенный метод forward_message.
            bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=chat_id,
                message_id=message.message_id,
                message_thread_id=target_topic_id
            )
            logger.info(f"✅ Сообщение {message.message_id} успешно переслано из чата {chat_id} в топик {target_topic_id}.")
        except Exception as e:
            logger.error(f"❌ Не удалось переслать сообщение {message.message_id} из чата {chat_id}. Ошибка: {e}")

# -----------------------------------------------------------------------------
# 3.3.5. Запуск в отдельных потоках
# -----------------------------------------------------------------------------
def run_bot():
    """Функция для запуска Telegram-бота в режиме long-polling."""
    logger.info("🚀 Запуск Telegram-бота...")
    # Удаляем вебхук на случай, если он был установлен ранее.
    bot.remove_webhook()
    # Запускаем polling.
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


def run_flask():
    """Функция для запуска Flask-сервера."""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Запуск Flask-сервера на порту {port}...")
    # use_reloader=False важно для того, чтобы избежать двойного запуска кода.
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    # Запускаем бота в отдельном фоновом потоке.
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask-сервер запускаем в основном потоке.
    run_flask()

