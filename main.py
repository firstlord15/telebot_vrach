import logging, re
import asyncio
import time, datetime
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
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Состояния для регистрации пользователя
class RegistrationStates(StatesGroup):
    fullname = State()
    phone_number = State()

# Состояния для редактирования профиля пользователя
class EditProfileStates(StatesGroup):
    entering_name = State()
    editing_fullname = State()
    editing_phone_number = State()

# Функция для форматирования номера телефона
def format_phone_number(phone_number):
    cleaned_phone_number = re.sub(r'\D', '', phone_number)
    formatted_phone_number = f"+7 ({cleaned_phone_number[:3]})-{cleaned_phone_number[3:6]}-{cleaned_phone_number[6:8]}-{cleaned_phone_number[8:]}"
    return formatted_phone_number

# Обработчик команды /start или /menu
@dp.message_handler(commands=["start", "menu"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user

    # Проверка, существует ли пользователь в базе данных
    if user_exists_in_database(user_id):
        await message.answer(f"Привет, {user.username}! Добро пожаловать обратно!")
        await show_main_menu_with_buttons(user_id)
    else:
        await RegistrationStates.fullname.set()
        await message.answer("Привет! Хотите указать информацию о себе?",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton("Поделиться контактом", callback_data='reg')]
                            ]))

# Обработчик нажатия кнопки "Поделиться контактом"
@dp.callback_query_handler(lambda c: c.data == 'reg', state=RegistrationStates)
async def process_registration(callback_query: types.CallbackQuery, state: FSMContext):
    user = callback_query.from_user
    await callback_query.answer()
    await callback_query.message.edit_text("Укажите ваш ФИО:")

    async with state.proxy() as data:
        data['user_id'] = user.id
        data['username'] = user.username
    await RegistrationStates.fullname.set()

# Обработчик указания ФИО
@dp.message_handler(state=RegistrationStates.fullname)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['full_name'] = message.text

    await bot.send_message(chat_id=message.from_user.id, text="Укажите ваш номер телефона:")
    await RegistrationStates.phone_number.set()

# Обработчик указания номера телефона
@dp.message_handler(state=RegistrationStates.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        raw_phone_number = message.text
        data['phone_number'] = raw_phone_number

        # Тут форматируется номера телефона из 89096895085
        # в +7 (909)-689-50-85 с помощью format_phone_number
        data['format_number'] = format_phone_number(raw_phone_number)

    await state.finish()

# Обработчик нажатия кнопки "yes" для отображения главного меню
# Еще не настроен и поэтому не вызван
@dp.callback_query_handler(lambda c: c.data == 'yes')
async def show_main_menu_with_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("Создать отчет", callback_data="create_request"),
        InlineKeyboardButton("Добавить пациента", callback_data="add_clients"),
        InlineKeyboardButton("Редактировать данные", callback_data="edit_data"),
        InlineKeyboardButton("Настройка подключения API", callback_data="setting_API")
    )

    await bot.send_message(user_id, "Выберите действие из меню:", reply_markup=keyboard)


if __name__ == '__main__':
    from aiogram import executor
    create_users_table()
    executor.start_polling(dp, skip_updates=True)
