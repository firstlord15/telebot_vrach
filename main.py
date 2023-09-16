import logging
import asyncio
import time
import datetime
from aiogram.types import ParseMode
from aiogram.types import MediaGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hlink
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import *


API_TOKEN = '6371189535:AAH82ZYpuERqs8vs3AEAQeFhZ8VtpzqQqqw'

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()  # Создаем хранилище состояний
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)  # Передаем хранилище в диспетчер
dp.middleware.setup(LoggingMiddleware())

class RegistrationStates(StatesGroup):
    name = State()
    platforms = State()
    social_id = State()  # New state for capturing social media ID 

class EditProfileStates(StatesGroup):
    entering_name = State()
    editing_platforms = State()
    editing_id = State()

@dp.message_handler(commands=["start", "menu"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user
    
    if user_exists_in_database(user_id):
        await message.answer(f"Привет, {user.username}! Добро пожаловать обратно!")
        await show_main_menu_with_buttons(user_id)  # Вызываем главное меню с кнопками
    else:
        await RegistrationStates.name.set()
        await message.answer("Привет! Хотите указать информацию о себе?",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton("Поделиться  контактом", callback_data='yes')]
                             ]))


