import os
import re
import asyncio
import geoip2.database
import requests
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = ""

# инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# функция для скачивания базы данных GeoLite2, если она отсутствует
def download_geoip_database():
    url = 'https://storage.yandexcloud.net/maxmind-geolite2-city/GeoLite2-City.mmdb'
    if not os.path.exists('GeoLite2-City.mmdb'):
        get_url = requests.get(url)
        with open('GeoLite2-City.mmdb', 'wb') as file:
            file.write(get_url.content)
        print("База данных GeoLite2-City.mmdb успешно загружена.")

# функция для обработки текста и получения IP-адресов
def get_ip_info(ip_input: str):
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
                    results.append(f"IP-адрес: {ip}, Страна: {country}, Город: {city}")
                except (geoip2.errors.AddressNotFoundError, ValueError) as e:
                    results.append(f'Произошла ошибка с IP {ip}: {e}')
    else:
        results.append('В введенном тексте IP-адреса не найдены.')
    return "\n".join(results)

# обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}! Отправьте текст с IP-адресами, и я определю их местоположение")

# обработка сообщений
@dp.message()
async def handle_text(message: Message) -> None:
    # скачиваем базу данных GeoLite2, если она не существует
    download_geoip_database()
    # получаем информацию по IP-адресам из текста
    result = get_ip_info(message.text)
    # печатаем введённое сообщение в консоль (для отладки)
    # print(f"Получено сообщение: {message.text}")
    # отправляем результат обратно в чат
    # print(f"Результат: {result}")
    try:
        await message.answer(result)
    except:
        await message.answer("Слишком частые запросы. Попробуйте позже.")

async def main():
    # запуск обработки сообщений
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())