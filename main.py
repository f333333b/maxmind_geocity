import os
import asyncio
import logging
from config import bot
from aiogram import Dispatcher
from handlers import router

# основной код
dp = Dispatcher()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# блокировка на время скачивания базы данных
db_update_lock = asyncio.Lock()

def setup_user_logger(user_id):
    log_filename = f"logs/{user_id}.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logger = logging.getLogger(str(user_id))

    # отключение вывода логирования в консоль
    logger.propagate = False

    handler = logging.FileHandler(log_filename, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

async def main():
    # запуск обработки сообщений
    await dp.start_polling(bot)

if __name__ == "__main__":
	asyncio.run(main())