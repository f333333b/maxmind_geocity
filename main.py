import asyncio
import logging
from config import bot
from aiogram import Dispatcher
from handlers import router
from commands import commands
from db_updating import update_check
from aiogram.fsm.storage.memory import MemoryStorage

# основной код
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# блокировка на время скачивания базы данных
db_update_lock = asyncio.Lock()

async def main():
    # запуск обработки сообщений
    await bot.set_my_commands(commands)
    asyncio.create_task(update_check())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())