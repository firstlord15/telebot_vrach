import logging, re
import asyncio
from pydrive.auth import GoogleAuth 
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

class RegisterPatientStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_phone = State()
    waiting_for_fullname = State()

# Функция для форматирования номера телефона
def format_phone_number(phone_number):
    cleaned_phone_number = re.sub(r'\D', '', phone_number)
    formatted_phone_number = f"+7 ({cleaned_phone_number[1:4]})-{cleaned_phone_number[4:7]}-{cleaned_phone_number[7:9]}-{cleaned_phone_number[9:]}"
    return formatted_phone_number

# Обработчик команды /start или /menu
@dp.message_handler(commands=["start", "menu"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user

    # Проверка, существует ли пользователь в базе данных
    if user_exists_in_database(user_id):
        await message.answer(f"Привет, {user.username}! Добро пожаловать обратно!")
        await show_main_menu_with_buttons(user_id, buttons_list)
    else:
        await RegistrationStates.fullname.set()
        await message.answer("Привет! Хотите указать информацию о себе?",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton("Поделиться контактом", callback_data='reg')]
                            ]))


buttons_list = [
    {"text": "Создать отчет", "callback_data": "create_request"},
    {"text": "Добавить пациента", "callback_data": "add_clients"},
    {"text": "Редактировать данные", "callback_data": "edit_data"},
    {"text": "Настройка подключения API", "callback_data": "setting_API"},
]

async def show_main_menu_with_buttons(user_id: int, buttons: list):
    menu_text = "Выберите действие:"
    menu_buttons = [
        types.InlineKeyboardButton(text=button["text"], callback_data=button["callback_data"]) for button in buttons
    ]

    menu_markup = types.InlineKeyboardMarkup(row_width=2)
    menu_markup.add(*menu_buttons)
    await bot.send_message(chat_id=user_id, text=menu_text, reply_markup=menu_markup)


# Обработчик нажатия кнопки "Поделиться контактом"
@dp.callback_query_handler(lambda c: c.data == 'reg', state=RegistrationStates.fullname)
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
    await RegistrationStates.next()

@dp.message_handler(content_types=types.ContentTypes.TEXT, state=RegistrationStates.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    phone_pattern = r"^\+\d{1,3}\d{1,14}$"
    phone_number = message.text

    if not re.match(phone_pattern, phone_number):
        await message.answer("Пожалуйста, введите правильный номер телефона в формате +7XXXXXXXXXX:")
        return

    formatted_phone_number = format_phone_number(phone_number)

    async with state.proxy() as data:
        user_id = data['user_id']
        username = data['username']
        full_name = data['full_name']

        save_user_to_database(user_id, username, full_name, formatted_phone_number)

    await message.answer("Спасибо за предоставленную информацию!")
    await state.finish()

    # Теперь отобразим главное меню с кнопками
    await show_main_menu_with_buttons(user_id=message.from_user.id, buttons=buttons_list)


# Обработчик кнопок главного меню    
@dp.callback_query_handler(lambda c: c.data in {"create_request", "add_clients", "edit_data", "setting_API"})
async def process_main_menu_buttons(callback_query: types.CallbackQuery):
    await callback_query.answer()
    action = callback_query.data
    
    if action == "create_request":
        await create_report_button_handler(callback_query=callback_query)
    elif action == "add_clients":
        await add_patient_handler(callback_query.message)
    elif action == "edit_data":
        await callback_query.message.answer("Раздел 'Редактировать данные' находится в разработке.")
    elif action == "setting_API":
        await callback_query.message.answer("Раздел 'Настройка подключения API' находится в разработке.")
    else:
        await callback_query.message.answer("Произошла ошибка. Пожалуйста, повторите позже.")

@dp.message_handler(lambda message: message.text == 'Добавить пациента')
async def add_patient_handler(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text='Введите ФИО пациента:')
    # Переходим в состояние регистрации пациента
    await RegisterPatientStates.waiting_for_fullname.set()

@dp.message_handler(state=RegisterPatientStates.waiting_for_fullname)
async def process_full_name(message: types.Message, state: FSMContext):
    if len(message.text.split()) != 3:
        # Если ФИО введено некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id, text='Пожалуйста, введите ФИО пациента корректно')
        return
    
    # Сохраняем ФИО пациента в контексте FSM
    await state.update_data(fullname=message.text)
    await bot.send_message(chat_id=message.chat.id, text='Укажите возраст пациента: (введите только цифру)')
    # Переходим в следующее состояние
    await RegisterPatientStates.waiting_for_age.set()

@dp.message_handler(state=RegisterPatientStates.waiting_for_age, regexp='^\d+$')
async def process_age(message: types.Message, state: FSMContext):
    # Сохраняем возраст пациента в контексте FSM
    await state.update_data(age=int(message.text))
    await bot.send_message(chat_id=message.chat.id, text='Введите номер телефона пациента:')

    # Переходим в следующее состояние
    await RegisterPatientStates.waiting_for_phone.set()
 
@dp.message_handler(state=RegisterPatientStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.text.strip().replace("+", "")
    if not phone_number.isdigit():
        # Если номер введен некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id, text='Номер телефона нужно вводить только цифрами. Попробуйте еще раз.')
        return
 
    # Сохраняем номер телефона пациента в контексте FSM
    await state.update_data(phone_number=phone_number)
 
    data = await state.get_data()
    patient_data = {
        'fullname': data.get('fullname'),
        'age': data.get('age'),
        'phone_number': data.get('phone_number')
    }
    
    # Сохраняем данные о пациенте и выводим сообщение об успешной регистрации
    add_patient_to_database(patient_data['fullname'], patient_data['age'], patient_data['phone_number'])
    await bot.send_message(chat_id=message.chat.id, text='Пациент успешно зарегистрирован в системе')
    await state.finish()


    # Возвращаемся в первоначальное состояние
    await show_main_menu_with_buttons(user_id=message.from_user.id, buttons=buttons_list)


async def show_patient_list(query: types.CallbackQuery, patients_list: list):
    menu_text = "Выберите пациента для создания отчета:"
    patients_buttons = (
        types.InlineKeyboardButton(text=patient["fullname"], callback_data=f"report_patient_{patient['id']}") 
        for patient in patients_list
    )

    patient_markup = types.InlineKeyboardMarkup(row_width=1)
    patient_markup.add(*patients_buttons)

    await bot.send_message(chat_id=query.from_user.id, text=menu_text, reply_markup=patient_markup)


async def create_report_button_handler(callback_query: types.CallbackQuery):
    await callback_query.answer('Обработка нажатия кнопки...')
    patients_list = get_all_patients_from_database()

    if patients_list == []:
        await callback_query.message.answer("Список пациентов пуст.")
        return

    await show_patient_list(query=callback_query, patients_list=patients_list)




@dp.callback_query_handler(lambda c: c.data.startswith("report_patient_"))
async def process_report_patient_buttons(callback_query: types.CallbackQuery):
    await callback_query.answer()
    patient_id = int(callback_query.data.split("_")[-1])
    patient_data = get_patient_from_database(patient_id)

    if not patient_data:
        await callback_query.message.answer("Не удалось загрузить информацию о пациенте. Пожалуйста, попробуйте еще раз.")
        return

    # Implement the functionality for creating a report for the selected patient
    report_text = f"Создается отчет для: {patient_data['fullname']}"
    await callback_query.message.answer(report_text)




if __name__ == '__main__':
    from aiogram import executor
    create_users_table()
    executor.start_polling(dp, skip_updates=True)
