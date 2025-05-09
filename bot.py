from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os
from io import BytesIO

# Конфигурация
TOKEN = "7544047422:AAHYNo5zclYgECND9iu6ZsxZjd8M2e7dC38"
API_URL = "http://ваш-сервер.railway.app"  # Замените на ваш URL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для работы с вашим API.\n"
        "Доступные команды:\n"
        "/send <текст> - Отправить сообщение\n"
        "/get - Получить последнее сообщение\n"
        "/upload - Загрузить фото (отправьте фото с подписью)\n"
        "/list - Показать все фото\n"
        "/view <имя> - Просмотреть конкретное фото"
    )


async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка сообщения на сервер"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите сообщение после команды /send")
        return

    message = ' '.join(context.args)
    response = requests.get(f"{API_URL}/send_message/{message}")

    if response.status_code == 200:
        await update.message.reply_text("✅ Сообщение отправлено на сервер!")
    else:
        await update.message.reply_text("❌ Ошибка при отправке сообщения")


async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение сообщения с сервера"""
    response = requests.get(f"{API_URL}/get_message")
    data = response.json()

    if data.get("message"):
        await update.message.reply_text(f"📩 Сообщение с сервера:\n{data['message']}")
    else:
        await update.message.reply_text("📭 На сервере нет сообщений")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загружаемых фото"""
    photo = update.message.photo[-1]  # Берем самое большое изображение
    file = await photo.get_file()

    # Загружаем фото в память
    photo_bytes = BytesIO()
    await file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)

    # Отправляем на сервер
    response = requests.post(
        f"{API_URL}/upload_photo",
        files={"file": ("photo.jpg", photo_bytes)}
    )

    if response.status_code == 200:
        data = response.json()
        await update.message.reply_text(
            f"📸 Фото загружено!\n"
            f"Имя файла: {data['filename']}\n"
            f"URL: {API_URL}{data['url']}"
        )
    else:
        await update.message.reply_text("❌ Ошибка при загрузке фото")


async def list_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение списка всех фото"""
    response = requests.get(f"{API_URL}/photos/")

    if response.status_code == 200:
        photos = response.json().get("photos", [])
        if photos:
            await update.message.reply_text(
                "📷 Список доступных фото:\n" +
                "\n".join(photos))
        else:
            await update.message.reply_text("📭 Нет доступных фото")
    else:
        await update.message.reply_text("❌ Ошибка при получении списка фото")



async def view_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр конкретного фото"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите имя файла после команды /view")
        return

    filename = context.args[0]
    response = requests.get(f"{API_URL}/photos/{filename}")

    if response.status_code == 200:
        # Скачиваем фото
        photo_bytes = BytesIO(response.content)
        await update.message.reply_photo(photo=InputFile(photo_bytes, filename=filename))
    else:
        await update.message.reply_text(f"❌ Ошибка при получении фото: {response.text}")

def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_message))
    app.add_handler(CommandHandler("get", get_message))
    app.add_handler(CommandHandler("upload", handle_photo))
    app.add_handler(CommandHandler("list", list_photos))
    app.add_handler(CommandHandler("view", view_photo))

    # Обработчик фото (если отправляют без команды)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()