import asyncio
import logging
from config import bot
from aiogram import Dispatcher
from handlers import router
from commands import commands
from capitals import capitals
from db_updating import update_check
from aiogram.fsm.storage.memory import MemoryStorage
from db_capitals_utils import check_db_connection, init_db_pool, insert_capitals

# создание диспатчера с временным хранилищем состояний пользователя
dp = Dispatcher(storage=MemoryStorage())

# подключение роутера к диспатчеру
dp.include_router(router)

async def main():
    # запуск обработки сообщений
    await bot.set_my_commands(commands)

    # запуск фонового обновления базы данных
    asyncio.create_task(update_check())

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