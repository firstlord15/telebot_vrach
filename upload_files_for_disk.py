import os
from datetime import datetime
from pydrive.drive import GoogleDrive
from aiogram import Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN
from auth import authenticate

# Аутентифицируемся и подключаемся к Google Диску
gauth = authenticate()
drive = GoogleDrive(gauth)


def get_folder_id_by_name(folder_name):
    # Поиск папки по ее названию
    query = (
        f"title = '{folder_name}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )

    folder_list = drive.ListFile({'q': query}).GetList()

    # Если найдена только одна папка с указанным названием, вернуть ее идентификатор
    if len(folder_list) == 1:
        return folder_list[0]['id']
    # Если найдено несколько папок с указанным названием, вы можете определить необходимую папку способом, наиболее подходящим для ваших потребностей
    elif len(folder_list) < 1:
        print(f"Папка '{folder_name}' не найдена.")


    # print("\n\n\nLEN:", len(folder_list), "\n\n\n")
    # folder_ids = [folder['title'] for folder in folder_list]
    # print("\n\n\nLEN:", folder_ids, "\n\n\n")

    return None


def create_folder_in_folder(parent_folder_id, folder_name):
    # Создаем папку внутри указанной папки
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [{'id': parent_folder_id}]
    }

    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder


async def upload_photo_to_drive(parent_folder_id, photo_path):
    drive = GoogleDrive(gauth)

    # Создаем файл с расширением .jpg
    media = drive.CreateFile({
        'title': f'{photo_path.split("/")[-1]}.jpg',  # Используйте имя файла с расширением .jpg
        'mimeType': 'image/jpeg',  # Установите тип MIME для изображений JPEG
        'parents': [{'id': parent_folder_id}]
    })
    
    media.SetContentFile(photo_path)
    media.Upload()
    print('System: Фотография успешно загружена на Google Диск!')
    return media


# async def handle_photo(parent_folder_id, folder_name, query: types.CallbackQuery):
#     photo = query.message.photo[-1]  # Выбираем фотографию наивысшего качества

#     # Загружаем фото на Google Диск
#     media = await upload_photo_to_drive(photo, parent_folder_id, folder_name)

#     # Отправляем ответное сообщение об успешной загрузке
#     await query.message.reply(f'Ваша фотография была загружена на Google Диск!\n'
#                         f'ID файла: {media["id"]}')


if __name__ == '__main__':
    # Инициализируем бота и диспетчер
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Запускаем бота
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)