import logging, re, os
import asyncio
import time, datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ContentType
from pydrive.drive import GoogleDrive
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hlink
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import *
from config import API_TOKEN
from auth import authenticate
from upload_files_for_disk import *

logging.basicConfig(level=logging.INFO)

gauth = authenticate()
drive = GoogleDrive(gauth)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class WaitForPhoto(StatesGroup):
    waiting = State()
    waiting_date_manual = State()
    waiting_date_auto = State()


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

markup_date_choice = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markup_date_choice.add(KeyboardButton("Автоматическая дата"))
markup_date_choice.add(KeyboardButton("Ручной ввод даты"))


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
        types.KeyboardButton(text=button["text"]) for button in buttons
    ]

    menu_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    menu_markup.add(*menu_buttons)
    await bot.send_message(chat_id=user_id, text=menu_text, reply_markup=menu_markup)


async def show_other_menu_with_buttons(user_id: int, buttons: list):
    menu_buttons = [
        types.KeyboardButton(text=button["text"]) for button in buttons
    ]

    menu_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    menu_markup.add(*menu_buttons)
    await bot.send_message(chat_id=user_id, text=None, reply_markup=menu_markup)


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
    if len(message.text.split()) != 3:
        # Если ФИО введено некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id, text='Пожалуйста, введите ФИО корректно')
        return

    async with state.proxy() as data:
        data['full_name'] = message.text
        data['token_user'] = message.from_user.id

    await bot.send_message(chat_id=message.from_user.id, text="Укажите ваш номер телефона:")
    await RegistrationStates.next()


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=RegistrationStates.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    phone_pattern = r"^7\d{10}$"
    phone_number = message.text.strip().replace("+", "")

    if not re.match(phone_pattern, phone_number):
        await message.answer("Пожалуйста, введите правильный номер телефона в формате 7XXXXXXXXXX:")
        return

    if not phone_number.isdigit():
        # Если номер введен некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id,
                               text='Номер телефона нужно вводить только цифрами. Попробуйте еще раз.')
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
@dp.message_handler(lambda message: message.text in [button["text"] for button in buttons_list])
async def process_main_menu_buttons(message: types.Message):
    action = message.text
    if action == "Создать отчет":
        await DateForFolderName(message)
    elif action == "Добавить пациента":
        await add_patient_handler(message)
    elif action == "Редактировать данные":
        await message.answer("Раздел 'Редактировать данные' находится в разработке.")
    elif action == "Настройка подключения API":
        await message.answer("Раздел 'Настройка подключения API' находится в разработке.")
    else:
        await message.answer("Произошла ошибка. Пожалуйста, повторите позже.")


# @dp.message_handler(lambda message: message.text == 'Добавить пациента')
async def add_patient_handler(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text='Введите ФИО пациента:')

    # Переходим в состояние регистрации пациента
    await RegisterPatientStates.waiting_for_fullname.set()


@dp.message_handler(state=RegisterPatientStates.waiting_for_fullname)
async def process_full_name(message: types.Message, state: FSMContext):
    patient_list = get_all_patients_from_database()

    """ Тут в коментариях стоит код, для провеки имен пользователей """

    # if message.text.lower() in patient_list.lower():
    #     await bot.send_message(chat_id=message.chat.id, text='Есть пациент с такими ФИО')
    #     return

    if len(message.text.split()) != 3 or message.text not in [button["text"] for button in buttons_list]:
        # Если ФИО введено некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id, text='Пожалуйста, введите ФИО пациента корректно')
        return

    # Сохраняем ФИО пациента в контексте FSM
    await state.update_data(fullname=message.text)
    await bot.send_message(chat_id=message.chat.id, text='Укажите возраст пациента: (введите только цифру)')

    folder_name = message.text
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()

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
    phone_pattern = r"^7\d{10}$"

    if not re.match(phone_pattern, phone_number):
        await message.answer("Пожалуйста, введите правильный номер телефона в формате 7XXXXXXXXXX:")
        return

    formatted_phone_number = format_phone_number(phone_number)

    if not phone_number.isdigit():
        # Если номер введен некорректно, сообщаем об ошибке и ожидаем правильный ввод
        await bot.send_message(chat_id=message.chat.id,
                               text='Номер телефона нужно вводить только цифрами. Попробуйте еще раз.')
        return

    # Сохраняем номер телефона пациента в контексте FSM
    await state.update_data(phone_number=formatted_phone_number)

    data = await state.get_data()
    patient_data = {
        'fullname': data.get('fullname'),
        'age': data.get('age'),
        'phone_number': data.get('phone_number'),
        'token': message.from_user.id
    }

    # Сохраняем данные о пациенте и выводим сообщение об успешной регистрации
    add_patient_to_database(patient_data['fullname'], patient_data['age'], patient_data['phone_number'],
                            patient_data['token'])
    await bot.send_message(chat_id=message.chat.id, text='Пациент успешно зарегистрирован в системе')
    await state.finish()

    # Возвращаемся в первоначальное состояние
    await show_main_menu_with_buttons(user_id=message.from_user.id, buttons=buttons_list)


async def show_patient_list(message: types.Message, patients_list: list):
    menu_text = "Выберите пациента для создания отчета:"
    patients_buttons = (
        types.InlineKeyboardButton(text=patient["fullname"], callback_data=f"report_patient_{patient['id']}")
        for patient in patients_list
    )

    patient_markup = types.InlineKeyboardMarkup(row_width=1)
    patient_markup.add(*patients_buttons)

    await bot.send_message(chat_id=message.from_user.id, text=menu_text, reply_markup=patient_markup)


async def create_report_button_handler(message: types.Message):
    await message.answer('Обработка нажатия кнопки...')
    patients_list = get_all_patients_from_database()

    if patients_list == []:
        await message.answer("Список пациентов пуст.")
        return

    await show_patient_list(message, patients_list)


@dp.callback_query_handler(lambda c: c.data.startswith("report_patient_"))
async def process_report_patient_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    patient_id = int(callback_query.data.split("_")[-1])
    patient_data = get_patient_from_database(patient_id)

    if not patient_data:
        await callback_query.message.answer(
            "Не удалось загрузить информацию о пациенте. Пожалуйста, попробуйте еще раз.")
        return

    # Создайте папку для пациента на Google Диске
    folder_name = patient_data['fullname']
    parent_folder_id = get_folder_id_by_name(folder_name=folder_name)

    if parent_folder_id is None:
        await bot.send_message(chat_id=callback_query.from_user.id, text=f"Папка '{folder_name}' не найдена.")
        return

    # Переведите пользователя в состояние ожидания фотографии
    await WaitForPhoto.waiting.set()

    # Отправьте сообщение с инструкцией о загрузке фотографии
    full_username = get_user_full_name_from_database(user_id=callback_query.from_user.id)

    # Сохраните информацию о папке и пользователях в контексте состояния
    async with state.proxy() as data:
        data['parent_folder_id'] = parent_folder_id
        data['folder_name'] = folder_name
        data['full_username'] = full_username

    menu_text = 'Пожалуйста, загрузите фото и нажмите кнопку *Готово*, когда закончите.'

    ready_button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    ready_button.add(types.KeyboardButton(text="Готово"))
    await bot.send_message(chat_id=callback_query.from_user.id, text=menu_text, reply_markup=ready_button)


async def DateForFolderName(message: types.Message):
    await message.answer("Выберите метод задания даты:", reply_markup=markup_date_choice)
    
    
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InputFile

# ...

@dp.message_handler(lambda message: message.text == "Ручной ввод даты", state="*")
async def DateForFolderName_manual(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text="Введите дату в формате DD.MM.YYYY")

    # Устанавливаем состояние ожидания вручную вводимой даты
    await WaitForPhoto.waiting_date_manual.set()

@dp.callback_query_handler(lambda message: message.text == "Автоматическая дата", state="*")
async def DateForFolderName_auto(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Вы выбрали автоматическую дату")
    async with state.proxy() as data:
        data["status"] = False

    # Устанавливаем состояние ожидания автоматически вводимой даты
    await WaitForPhoto.waiting_date_auto.set()

@dp.callback_query_handler(state=WaitForPhoto.waiting_date_manual)
async def handle_manual_date(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback_query.message.chat.id, text="test1")
    current_time = callback_query.message.text.strip()  # Получаем текст сообщения

    async with state.proxy() as data:
        data["current_time"] = current_time
        data["status"] = True
    
    await state.finish()
    await WaitForPhoto.waiting.set()

@dp.message_handler(state=WaitForPhoto.waiting_date_auto)
async def handle_auto_date(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text="test2")
    # Обработка автоматической даты
    async with state.proxy() as data:
        data["status"] = False
    
    await state.finish()
    await WaitForPhoto.waiting.set()






@dp.message_handler(content_types=ContentType.ANY, state=WaitForPhoto.waiting)
async def handle_uploaded_photo(message: types.Message, state: FSMContext):
    # Определите, является ли фотография сжатой или оригинальной

    if message.text == "Готово":
        await handle_stop_message(message, state)
        return
    elif message.photo == [] and message.document.mime_type.startswith('image'):
        photo = message.document
        photo_path = f'photos/{photo.file_id}.jpg'
    elif message.photo != []:
        photo = message.photo[-1]
        photo_path = f'photos/compressed_{photo.file_id}.jpg'
    else:
        # Если это не фотография и не изображение, игнорируем этот файл
        await bot.send_message(chat_id=message.chat.id, text="Пожалуйста, отправьте только фотографию!")
        return

    # Получить текущее состояние пользователя
    async with state.proxy() as data:
        parent_folder_id = data['parent_folder_id']
        fullname = data['full_username']
        status = data["status"]
        if 'new_folder_id' not in data:
            # Создать папку с текущим временем и дополнительными данными
            if status:
                current_time = data["current_time"]    
            else:
                current_time = datetime.now().strftime('%Y-%m-%d')

            
            new_folder_name = f'{current_time}_{fullname}'

            # Создать папку с новым именем в родительской папке
            FolderNameById = create_folder_in_folder(parent_folder_id, new_folder_name)

            # Сохранить идентификатор папки в состоянии
            data['new_folder_id'] = FolderNameById['id']
        else:
            FolderNameById = {'id': data['new_folder_id']}

    # Скачиваем фото локально
    await bot.send_message(chat_id=message.chat.id, text="Начало загрузки")
    await photo.download(photo_path)

    # Загрузите фотографию на Google Диск
    media = await upload_photo_to_drive(parent_folder_id=FolderNameById['id'], photo_path=photo_path)

    # создаем прямую ссылку фото
    file_link = await get_link(media)

    # Отправьте ответное сообщение об успешной загрузке
    await message.reply(
        f'Ваша фотография была загружена на Google Диск!\n'
        f'Ссылка на файл: {file_link}'
    )


# @dp.message_handler(lambda message: message.text == 'Готово', state=WaitForPhoto.waiting)
async def handle_stop_message(message: types.Message, state: FSMContext):
    chat_id = message.from_user.id
    await state.finish()
    await show_main_menu_with_buttons(user_id=chat_id, buttons=buttons_list)


if __name__ == '__main__':
    from aiogram import executor

    create_users_table()
    executor.start_polling(dp, skip_updates=True)
