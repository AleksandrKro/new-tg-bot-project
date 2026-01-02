import os
import logging
import threading
from flask import Flask
from waitress import serve

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импортируем функцию запуска бота
try:
    from bot import run_bot
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать модуль бота: {e}")
    run_bot = None

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    """Домашняя страница для проверки работы"""
    return "🤖 Telegram Forward Bot активен", 200

@app.route('/health')
def health_check():
    """Health check для Render"""
    return {"status": "healthy", "service": "telegram-forward-bot"}, 200

@app.route('/ping')
def ping():
    """Простой пинг для мониторинга"""
    return "pong", 200

def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    if run_bot:
        try:
            logger.info("🚀 Запуск Telegram бота в отдельном потоке...")
            run_bot()
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
    else:
        logger.error("❌ Функция run_bot недоступна")

def main():
    """Основная функция запуска"""
    logger.info("🔄 Инициализация Web Service на Render...")
    
    # Запускаем бота в отдельном потоке
    if run_bot:
        bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
        bot_thread.start()
        logger.info("✅ Бот запущен в фоновом режиме")
    
    # Запускаем веб-сервер
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🌐 Запуск веб-сервера на порту {port}")
    
    # Используем waitress для продакшена
    serve(app, host='0.0.0.0', port=port, threads=4)

if __name__ == '__main__':
    main()
