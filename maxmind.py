import os
import re
import asyncio
import geoip2.database
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode
import countryflag
from googletrans import Translator

TOKEN = ""

# инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# функция для скачивания базы данных GeoLite2, если она отсутствует
def download_geoip_database():
    url = 'https://storage.yandexcloud.net/maxmind-geolite2-city/GeoLite2-City.mmdb'
    if not os.path.exists('GeoLite2-City.mmdb'):
        get_url = requests.get(url)
        with open('GeoLite2-City.mmdb', 'wb') as file:
            file.write(get_url.content)
        print("База данных GeoLite2-City.mmdb успешно загружена.")

# перевод на русский язык
async def translate_text(english_text):
    async with Translator() as translator:
        return await translator.translate(english_text, dest='ru')

# функция для обработки текста и получения IP-адресов
async def get_ip_info(ip_input: str):
    re_format = r'\d+\.\d+\.\d+'
    ip_list = re.findall(re_format, ip_input)
    results = []
    if ip_list:
        with geoip2.database.Reader('GeoLite2-City.mmdb') as city_file:
            for ip in ip_list:
                try:
                    response = city_file.city(ip)
                    country = response.country.name
                    city = response.city.name
                    flag = countryflag.getflag([country])
                    russian_country = await translate_text(country)
                    russian_city = await translate_text(city)
                    results.append(f"{flag} {russian_country.text} ({russian_city.text}) {ip}")
                except (geoip2.errors.AddressNotFoundError, ValueError) as e:
                    results.append(f'Произошла ошибка с IP {ip}: {e}')
    else:
        results.append('В введенном тексте IP-адреса не найдены.')
    return "\n".join(results)

# обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Привет! Отправь текст с IP-адресами, и я определю их местоположение")

# обработка сообщений
@dp.message()
async def handle_text(message: Message) -> None:
    # скачиваем базу данных GeoLite2, если она не существует
    download_geoip_database()
    # получаем информацию по IP-адресам из текста
    result = await get_ip_info(message.text)
    # отправляем результат обратно в чат
    try:
        await message.answer(result)
    except:
        await message.answer("Слишком частые запросы. Попробуйте позже.")

async def main():
    # запуск обработки сообщений
    await dp.start_polling(bot)

asyncio.run(main())
