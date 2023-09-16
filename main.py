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
# from database import save_user_to_database, user_exists_in_database, create_users_table, update_platform_url_in_database, get_user_alias_from_database, get_links_from_database, update_user_name_in_database, is_verified, is_banned


API_TOKEN = '6371189535:AAH82ZYpuERqs8vs3AEAQeFhZ8VtpzqQqqw'

logging.basicConfig(level=logging.INFO)
