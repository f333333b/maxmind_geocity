import os
import re
import asyncio
import geoip2.database
import geoip2.errors
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import countryflag
from datetime import datetime, timedelta
import logging

# основной код
TOKEN = r""
LICENSE_KEY = ''
bot = Bot(token=TOKEN)
dp = Dispatcher()
database_filename = 'GeoLite2-City.mmdb'
#city_database_filename = 'GeoLite2-City.mmdb'
proxy_database_filename = ''
# url = f'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${LICENSE_KEY}&suffix=tar.gz'
url = r'https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb'
re_format = r'\d+\.\d+\.\d+'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# блокировка на время скачивания базы данных
db_update_lock = asyncio.Lock()

# отслеживание состояния пользователя
user_states = {}
user_data = {}

# переменная для хранения IP-адресов
user_ips = {}

# кнопки для выбора действия
keyboard_choice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Проверить страну по IP-адресу", callback_data="check_country")],
        [InlineKeyboardButton(text="Фильтровать IP", callback_data="filter_ips_1")],
        [InlineKeyboardButton(text="Вывести города по стране", callback_data="get_cities")]

    ]
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Скопировать все IP", callback_data="copy_ips")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

keyboard_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

# async def log_user_action(func):
#    def wrapper(*args, **kwargs):
#        message = args[0]
#        logger.info(f"Пользователь: {message.from_user.id}\nЗапрос:\n{message.text}")
#        result = func(*args, **kwargs)
#        logger.info(f"Ответ:\n{result}")
#        return result
#    return wrapper

# функция для обновления базы
async def download_database(user_id):
    await bot.send_message(chat_id=user_id, text="База данных обновляется, пожалуйста, подождите...")
    user_states[user_id] = 'awaiting_database_update'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(database_filename, 'wb') as file:
                    file.write(await response.read())
            else:
                logging.error(f"Ошибка при скачивании базы данных: {response.status}")
    await bot.send_message(chat_id=user_id, text="Обновление базы данных завершено.", reply_markup=keyboard_choice)
    user_states[user_id] = 'back_to_choice'

# функция проверки наличия базы и ее актуальности
async def is_update_needed(user_id):
    if not os.path.exists(database_filename):
        await download_database(user_id)
    with open(database_filename, 'rb'):
        db_creation_date = datetime.fromtimestamp(os.stat(database_filename).st_ctime)
        if datetime.now() - db_creation_date > timedelta(weeks=1):
            await download_database(user_id)

# функция вывода городов с IP-адресами определенной страны
async def get_cities(text):
    country = text[:2]
    result, result_to_copy = get_ip_info(text)
    country = record.get('country', {}).get('names', {}).get('en', None)
    if country == name:
       city = record.get('city', {}).get('names', {}).get('ru', None)
       if city:
          cities.add(city)
    # return 'Эта функция еще в разработке'

# функция фильтрации списков IP-адресов
async def to_filter_ips(first_input, second_input):
    return set(re.findall(re_format, first_input)).difference(set(re.findall(re_format, second_input)))

# функция для обработки текста и получения IP-адресов
async def get_ip_info(ip_input: str, country_input: str=''):
    ip_list_input = re.findall(re_format, ip_input)
    ip_list = list(map(lambda x: x + '.0', ip_list_input))
    results, results_to_copy = [], []
    if ip_list:
        with geoip2.database.Reader(database_filename) as city_file:
            for i in range(len(ip_list)):
                # сохранение IP-адреса в формате, введенном пользователем
                ip = ip_list_input[i]
                try:
                    response = city_file.city(ip_list[i])
                    print(response)
                    country_id = response.country.iso_code
                    country = response.country.names.get('ru', '')
                    city = response.city.names.get('ru', '')
                    flag = countryflag.getflag([country_id])
                    if country_input:
                        if country_id == country_input:
                            pass
                    else:
                        results.append(f"{flag} {country_id} ({country}) {city} <code>{ip}</code>")
                        results_to_copy.append(ip)

                except (geoip2.errors.AddressNotFoundError, ValueError) as e:
                    results.append(f"Вы ввели неверный IP-адрес.")
                    logging.error(f"Ошибка при обработке IP {ip}: {e}")
                except Exception as e:
                    results.append(f"Ошибка при обработке IP {ip}: {e}")
                    logging.error(f"Ошибка при обработке IP {ip}: {e}")
    else:
        results.append('Неверный формат IP-адреса либо во введенном тексте IP-адреса не найдены.')
    return "\n".join(results), "\n".join(results_to_copy)

# обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Здравствуйте! Выберете нужное действие:", reply_markup=keyboard_choice)

# обработка callback-запросов от кнопок
@dp.callback_query()
async def handle_callback(query: CallbackQuery):
    user_id = query.from_user.id

    # сценарий № 1: определение страны по IP-адресу
    if query.data == 'check_country':
        user_states[user_id] = 'awaiting_check_country'
        await query.message.answer("Введите текст с IP-адресами, и я определю их местоположение (не более 50 IP-адресов за один запрос)", reply_markup=keyboard_back)

    # сценарий № 2: фильтрация списков IP-адресов (основной список)
    elif query.data == 'filter_ips_1':
        user_states[user_id] = 'awaiting_filter_first_input'
        await query.message.answer("Введите список IP-адресов, которые нужно отфильтровать", reply_markup=keyboard_back)

    # сценарий № 3: фильтрация списков IP-адресов (второй список)
    elif query.data == 'filter_ips_2':
        user_states[user_id] = 'awaiting_filter_second_input'
        await query.message.answer("Введите второй список IP-адресов", reply_markup=keyboard_back)

    # сценарий № 4: вывод IP-адресов в столбик для копирования
    elif query.data == 'copy_ips':
        ips_to_copy = user_data.get(user_id, [])
        if ips_to_copy:
            # отправляем список IP-адресов пользователю
            formatted_ips = "".join(ips_to_copy)
            await query.message.answer(f"{formatted_ips}", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_check_country'
        else:
            await query.message.answer("Нет сохраненных IP-адресов для копирования.")
            user_states[user_id] = 'awaiting_check_country'
    elif query.data == 'get_cities':
        await query.message.answer("Введите страну в формате ISO (например 'US', 'FR')", reply_markup=keyboard_back)
        user_states[user_id] = 'get_cities'
    elif query.data == "back_to_choice":
        await query.message.answer(text='Выберете нужное действие:', reply_markup=keyboard_choice
        )

# обработка сообщений
@dp.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    # проверяем наличие актуальной скачанной базы данных
    await is_update_needed(user_id)

    # сценарий № 1: определение страны по IP-адресу
    if user_state == 'awaiting_check_country':
        try:
            result, result_to_copy = await get_ip_info(message.text)
            await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy)
            user_data[user_id] = result_to_copy
        except Exception as e:
            await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_copy)
            user_states[user_id] = 'awaiting_check_country'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")

    # сценарий № 2: фильтрация списков IP-адресов (основной список)
    elif user_state == 'awaiting_filter_first_input':
        if re.findall(re_format, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                await message.answer("Теперь введите второй список IP-адресов.", reply_markup=keyboard_back)
                user_states[user_id] = 'awaiting_filter_second_input'
            except Exception as e:
                await message.answer(f"При выполнении программы возникла ошибка: {e}.")
                logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
        else:
            await message.answer("Введенный текст не содержит IP-адреса.", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_filter_first_input'

    # сценарий № 3: фильтрация списков IP-адресов (второй список)
    elif user_state == 'awaiting_filter_second_input':
        second_ips = message.text
        first_ips = user_ips.get(user_id, {}).get('first', '')
        if first_ips.strip():
            try:
                filtered_ips = await to_filter_ips(first_ips, second_ips)
                result_filtered_ips = '\n'.join(filtered_ips)
                if filtered_ips:
                    await message.answer(f"Отфильтрованные IP-адреса:")
                    await message.answer(f"{result_filtered_ips}", reply_markup=keyboard_back)
                    user_states[user_id] = None  # сброс состояния после фильтрации
                else:
                    await message.answer(f"Отфильтрованный список пуст. IP-адресов нет.", reply_markup=keyboard_back)
                    user_states[user_id] = 'awaiting_filter_first_input'
            except Exception as e:
                await message.answer(f"Ошибка при фильтрации IP-адресов: {e} Попробуйте снова.", reply_markup=keyboard_back)
                user_states[user_id] = 'awaiting_filter_first_input'
                logging.error(f'Ошибка фильтрации для пользователя {user_id}: {e}')
                user_states[user_id] = None  # сброс состояния при ошибке
        else:
            await message.answer("Ошибка: не был получен первый список IP-адресов.")
            user_states[user_id] = 'awaiting_filter_first_input'

    # сценарий № 4: вывод городов с IP-адресами определенной страны
    elif user_state == 'get_cities':
        try:
            result = await get_cities(message.text)
            await message.answer(result, parse_mode="HTML", reply_markup=keyboard_back)
            user_data[user_id] = 'get_cities'
        except Exception as e:
            await message.answer(f"При выполнении программы произошла ошибка {e}", reply_markup=keyboard_back)
            user_data[user_id] = 'back_to_choice'
            logging.error(f'Ошибка при определении списка городов по стране: {e}')
    elif user_state == 'awaiting_database_update':
        await message.answer(f"База данных обновляется, пожалуйста, подождите.")
    else:
        await message.answer("Выберите нужное действие:", reply_markup=keyboard_choice, parse_mode="HTML")

    # логирование
    # user_logger = setup_user_logger(message.from_user.id)
    # user_logger.info(f"Пользователь:{message.from_user.id}\nЗапрос:\n{message.text}\nОтвет:\n{result}")
    # отправляем результат обратно в чат


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
