import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from config import API_TOKEN

# Создайте объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


