import asyncio
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import bot
from handlers import router
from commands import commands
from db_updating import update_check
from middlewares import RateLimitMiddleware

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

    await asyncio.sleep(3)

    # запуск базового логирования (вывод в консоль сообщений о событиях в боте)
    logging.basicConfig(level=logging.DEBUG)

    # запуска пула тегеграм-бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())