import os
from pydrive.drive import GoogleDrive
from aiogram import Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN
from auth import authenticate


async def upload_photo_to_drive(photo_path):
    gauth = authenticate()

    drive = GoogleDrive(gauth)
    file_metadata = {'title': os.path.basename(photo_path)}
    media = drive.CreateFile(file_metadata)
    media.SetContentFile(photo_path)
    media.Upload()
    print('System: Photo uploaded to Google Drive successfully!')
    return media


async def handle_photo(message: types.Message):
    photo = message.photo[-1]  # Select the highest quality photo

    # Save the photo locally
    photo_path = f'photos/{photo.file_id}.jpg'
    await photo.download(photo_path)

    # Upload the photo to Google Drive
    media = await upload_photo_to_drive(photo_path)

    # Send a reply confirming the upload
    await message.reply(f'Your photo has been uploaded to Google Drive!\n'
                        f'File ID: {media["id"]}')


if __name__ == '__main__':
    # Initialize the bot and dispatcher
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Register the photo handler
    dp.register_message_handler(handle_photo, content_types=types.ContentType.PHOTO)

    # Start the bot
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
