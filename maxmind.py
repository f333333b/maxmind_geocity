import os
import re
import asyncio
import geoip2.database
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
import countryflag
from datetime import datetime, timedelta
import logging

# основной код
TOKEN = ""
LICENSE_KEY = ''
bot = Bot(token=TOKEN)
dp = Dispatcher()
database_filename = 'GeoLite2-City.mmdb'
url = f'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${LICENSE_KEY}&suffix=tar.gz'
re_format = r'\d+\.\d+\.\d+'
logging.basicConfig(level=logging.INFO)

# функция для обновления базы
async def download_database():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(database_filename, 'wb') as file:
                    file.write(await response.read())
            else:
                logging.error(f"Ошибка при скачивании базы данных: {response.status}")

# функция проверки наличия базы и ее актуальности
async def is_update_needed():
    if not os.path.exists(database_filename):
        await download_database()
    with open(database_filename, 'rb'):
        db_creation_date = datetime.fromtimestamp(os.stat(database_filename).st_ctime)
        if datetime.now() - db_creation_date > timedelta(weeks=1):
            await download_database()

# функция для обработки текста и получения IP-адресов
async def get_ip_info(ip_input: str):
    ip_list_input = re.findall(re_format, ip_input)
    ip_list = list(map(lambda x: x + '.0', ip_list_input))
    results = []
    if ip_list:
        with geoip2.database.Reader(database_filename) as city_file:
            for i in range(len(ip_list)):
                # сохранение IP-адреса в формате, введенном пользователем
                ip = ip_list_input[i]
                try:
                    response = city_file.city(ip)
                    country_id = response.country.iso_code
                    country = response.country.names.get('ru', '')
                    city = response.city.names.get('ru', '')
                    flag = countryflag.getflag([country_id])
                    results.append(f"{flag} {country_id} ({country}) {city} <code>{ip}</code>")
                except (geoip2.errors.AddressNotFoundError, ValueError) as e:
                    logging.error(f"Ошибка при обработке IP {ip}: {e}")
                    results.append(f"Ошибка при обработке IP {ip}: {e}")
    else:
        results.append('В введенном тексте IP-адреса не найдены. Попробуйте ещё раз.')
    return "\n".join(results)

# обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Здравствуйте! Введите текст с IP-адресами, и я определю их местоположение (не более 100 IP-адресов за один запрос)")

# обработка сообщений
@dp.message()
async def handle_text(message: Message):
    # проверяем наличие актуальной скачанной базы данных
    # is_update_needed()
    # получаем информацию по IP-адресам из текста
    result = await get_ip_info(message.text)
    # логирование
    user_logger = setup_user_logger(message.from_user.id)
    user_logger.info(f"Пользователь:{message.from_user.id}\nЗапрос:\n{message.text}\nОтвет:\n{result}")
    # отправляем результат обратно в чат
    try:
        await message.answer(result, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"При выполнении программы возникла ошибка. Попробуйте ещё раз.")
        logging.error(f'Ошибка {e}')

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

asyncio.run(main())
