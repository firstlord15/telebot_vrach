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
from database import save_user_to_database, user_exists_in_database, create_users_table, update_platform_url_in_database, get_user_alias_from_database, get_links_from_database, update_user_name_in_database, is_verified, is_banned


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
                                 [InlineKeyboardButton("Да", callback_data='yes'), InlineKeyboardButton("Нет", callback_data='no')]
                             ]))


async def show_main_menu_with_buttons(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("Загрузить", callback_data="upload"),
        InlineKeyboardButton("Поддержка", callback_data="supp"),
        InlineKeyboardButton("Редактировать данные", callback_data="edit_data")
    )
    await bot.send_message(user_id, "Выберите действие из меню:", reply_markup=keyboard)
