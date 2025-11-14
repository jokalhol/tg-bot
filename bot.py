import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

# Токен для Telegram-бота
TELEGRAM_TOKEN = ""

# Токен для Hugging Face API
HF_TOKEN = ""

# URL модели для Hugging Face
API_URL = "https://router.huggingface.co/v1/chat/completions"  # Изменить URL для использования правильной модели

# Словарь для хранения контекста беседы для каждого пользователя
user_context = {}

# Функция для отправки запроса к Hugging Face с учетом контекста
def get_huggingface_response(user_id, text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    # Обновляем контекст для пользователя
    if user_id not in user_context:
        user_context[user_id] = []

    # Добавляем новое сообщение в контекст
    user_context[user_id].append({"role": "user", "content": text})

    # Ограничиваем количество сообщений в контексте (например, последние 10 сообщений)
    if len(user_context[user_id]) > 10:
        user_context[user_id] = user_context[user_id][-10:]

    # Формируем данные для запроса
    data = {
        "model": "openai/gpt-oss-20b:groq",  # Заменить на свою модель (например, GPT-2 или GPT-Neo)
        "messages": user_context[user_id],
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        # Возвращаем ответ от модели
        return result['choices'][0]['message']['content']
    else:
        return f"Ошибка: {response.status_code}, {response.text}"

# Функция для отправки длинных сообщений в Telegram (разделение на части)
async def send_long_message(update, text):
    max_message_length = 4096  # Максимальная длина сообщения для Telegram
    if len(text) > max_message_length:
        # Разбиваем текст на части
        for i in range(0, len(text), max_message_length):
            part = text[i:i + max_message_length]
            await update.message.reply_text(part)
    else:
        # Если сообщение не длинное, отправляем его сразу
        await update.message.reply_text(text)

# Функция обработки команды /start
async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот, напиши /aalisixx, чтобы задать мне вопрос."
                                    "/reset чтобы очистить контекст")
# Функция для обработки команды /aalisixx
async def aalisixx(update: Update, context):
    user_message = " ".join(context.args)  # Получаем текст после команды
    if not user_message:
        await update.message.reply_text("Пожалуйста, напишите вопрос после команды /aalisixx.")
        return

    # Получаем ответ от Hugging Face
    response = get_huggingface_response(update.message.from_user.id, user_message)

    # Отправляем ответ пользователю, если он длинный — разбиваем на части
    await send_long_message(update, response)


async def reset(update: Update, context):
    user_id = update.message.from_user.id

    # Очищаем контекст для данного пользователя
    if user_id in user_context:
        del user_context[user_id]
        await update.message.reply_text("Контекст беседы был очищен. Вы можете начать новый разговор!")
    else:
        await update.message.reply_text("Контекст уже очищен.")


# Функция для обработки обычных сообщений
async def handle_message(update: Update, context):
    text = update.message.text.lower()  # Приводим текст к нижнему регистру
    if 'привет' in text:
        await update.message.reply_text('Привет, как дела?')
    elif 'пока' in text:
        await update.message.reply_text('Пока! Хорошего дня!')
    elif 'зачем ты делала стики в 16 лет' in text:
        await update.message.reply_text('твари, мне было 16, не бульте меня')
    else:
        await update.message.reply_text('Я вас не понял, напишите "привет" или "пока".')

# Основная функция для настройки бота
def main():
    # Создаем Application и передаем токен
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("aalisixx", aalisixx))
    application.add_handler(CommandHandler("reset", reset))  # Обработчик для очистки контекста
    # Обработчик для обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
