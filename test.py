import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from config import API_TOKEN

# Создайте объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Директория для сохранения фотографий
save_dir = 'F:\\Работа\\2\\telebot_vrach'

# Обработчик для фотографий
@dp.message_handler(content_types=ContentType.PHOTO)
async def handle_photos(message: types.Message):
    # Получите информацию о фотографии
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    # Скачайте фотографию
    file = await bot.download_file(file_path)

    # Определите путь для сохранения фотографии
    file_name = os.path.join(save_dir, f'{file_id}.jpg')

    # Сохраните фотографию в указанной директории
    with open(file_name, 'wb') as new_file:
        new_file.write(file.read())

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
