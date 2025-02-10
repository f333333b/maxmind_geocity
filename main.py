import asyncio
import logging
from aiolimiter import AsyncLimiter

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import bot
from handlers import router
from commands import commands
from capitals import capitals
from db_updating import update_check
from logging_utils import logs_to_db
from middlewares import RateLimitMiddleware
from db_capitals_utils import check_db_connection, init_db_pool, insert_capitals

# создание диспатчера с временным хранилищем состояний пользователя
dp = Dispatcher(storage=MemoryStorage())

# подключение роутера к диспатчеру
dp.include_router(router)

# подключение middleware к диспатчеру
dp.update.middleware(RateLimitMiddleware())

async def main():
    # запуск обработки сообщений
    await bot.set_my_commands(commands)

    # запуск фонового обновления базы данных
    asyncio.create_task(update_check())

    # запуск фонового внесения информации из логов в базу данных
    #asyncio.create_task(logs_to_db())

    # запуск пула к базе данных capitals
    await init_db_pool()

    # проверка работы подключения к базе данных capitals
    await check_db_connection()

    # внесение информации в таблицу PostgreSQL capitals
    #await insert_capitals(capitals)

    # запуск базового логирования (вывод в консоль сообщений о событиях в боте)
    logging.basicConfig(level=logging.DEBUG)

    # запуска пула тегеграм-бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())