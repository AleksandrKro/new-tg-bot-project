import os
import logging
from flask import Flask
import requests

app = Flask(__name__)

# Токен бота (получаем из переменных окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Конфигурация пересылки
SOURCE_CHAT_TO_TOPIC = {
    -4973230673: 11,
    -1002705141042: 2,
}
TARGET_CHAT_ID = -1002290371611

# Эндпоинт для пинга
@app.route('/')
def ping():
    return "🟢 Ping-сервер работает! Бот пересылает сообщения.", 200

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

# Эндпоинт для ручной проверки (опционально)
@app.route('/test')
def test():
    if not BOT_TOKEN:
        return "❌ BOT_TOKEN не установлен", 500
    
    # Проверяем, что бот активен
    try:
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe')
        if response.status_code == 200:
            return "✅ Бот активен, конфигурация загружена", 200
        else:
            return f"❌ Ошибка Telegram API: {response.text}", 500
    except Exception as e:
        return f"❌ Ошибка подключения: {str(e)}", 500

# Запуск Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Сервер запущен на порту {port}")
    print(f"🔧 Конфигурация: {len(SOURCE_CHAT_TO_TOPIC)} чатов для пересылки")
    print(f"📡 Целевой чат: {TARGET_CHAT_ID}")
    
    if BOT_TOKEN:
        print("✅ BOT_TOKEN загружен")
    else:
        print("❌ ВНИМАНИЕ: BOT_TOKEN не установлен!")
    
    app.run(host='0.0.0.0', port=port, debug=False)
