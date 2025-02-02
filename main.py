import asyncio
import logging
from config import bot
from aiogram import Dispatcher
from handlers import router
from aiogram.types import BotCommand

# основной код
dp = Dispatcher()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# блокировка на время скачивания базы данных
db_update_lock = asyncio.Lock()

commands = [
    BotCommand(command="/start", description="Запуск бота"),
    BotCommand(command="/help", description="Справка")
]

async def main():
    # запуск обработки сообщений
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())