import os
import re
import asyncio
import geoip2.database
import geoip2.errors
import aiohttp
import countryflag
import logging
import tarfile
import shutil
import tempfile
import countryinfo
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime, timedelta

# основной код
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LICENSE_KEY = os.getenv('LICENSE_KEY')
bot = Bot(token=TOKEN)
dp = Dispatcher()
database_filename = 'GeoLite2-City.mmdb'
url = (
    f"https://download.maxmind.com/app/geoip_download?"
    "edition_id=GeoLite2-City&license_key={LICENSE_KEY}"
    "&suffix=tar.gz"
)
pattern = r'\d+\.\d+\.\d+'
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

keyboard_copy_or_grouped = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Скопировать все IP-адреса", callback_data="copy_ips")],
        [InlineKeyboardButton(text="Сгруппировать IP-адреса по городам", callback_data="group_ips")],
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
                with open('database.tar.gz', 'wb') as file:
                    file.write(await response.read())
                with tarfile.open('database.tar.gz', 'r:gz') as archive:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        target_file = None
                        for filename in archive.getnames():
                            if os.path.basename(filename) == database_filename:
                                archive.extract(filename, path=temp_dir)
                                target_file = os.path.join(temp_dir, filename)
                                break

                        if target_file and os.path.exists(target_file):
                            program_directory = os.path.dirname(os.path.abspath(__file__))
                            destination_path = os.path.join(program_directory, database_filename)
                            shutil.copy2(target_file, destination_path)
                            await bot.send_message(chat_id=user_id, text="База данных обновлена.", reply_markup=keyboard_choice)
                        else:
                            logging.error(f"Файл {database_filename} не найден в архиве.")
                            await bot.send_message(chat_id=user_id, text="При обновлении базы данных произошла ошибка.", reply_markup=keyboard_choice)
            else:
                logging.error(f"Ошибка при скачивании базы данных: {response.status}")
    await bot.send_message(chat_id=user_id, text="Обновление базы данных завершено.", reply_markup=keyboard_choice)
    user_states[user_id] = 'back_to_choice'

# функция проверки наличия базы и ее актуальности
async def is_update_needed(user_id):
    if not os.path.exists(database_filename):
        await download_database(user_id)
    existing_base_date = datetime.fromtimestamp(os.path.getmtime(database_filename))
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            if "Last-Modified" in response.headers:
                updated_base_date = response.headers["Last-Modified"]
                formatted_updated_base_date = datetime.strptime(updated_base_date, "%a, %d %b %Y %H:%M:%S %Z")
                if formatted_updated_base_date - existing_base_date > timedelta(weeks=1):
                    await download_database(user_id)

# функция фильтрации списков IP-адресов
async def to_filter_ips(first_input, second_input):
    return set(re.findall(pattern, first_input)).difference(set(re.findall(pattern, second_input)))

# функция для обработки текста и получения IP-адресов
async def get_ip_info(text_input: str):
    all_ips = re.findall(pattern, text_input)
    if text_input[:2].isalpha():
        country = text_input[:2]
    ip_list_text = text_input.splitlines()
    new_text_list, copy_list, grouped_list = [], [], []
    if all_ips:
        with geoip2.database.Reader(database_filename) as city_file:
            for line in ip_list_text:
                match = re.search(pattern, line)
                if match:
                    # print(match)
                    ip_original = match.group()
                    ip = ip_original + '.0'
                    try:
                        response = city_file.city(ip)
                        country_id = response.country.iso_code
                        country_ru = response.country.names.get('ru', '')
                        country_en = response.country.names.get('en', '')
                        city = response.city.names.get('en', '')
                        if not city:
                            city = CountryInfo(country_en).capital()
                        flag = countryflag.getflag([country_id])
                        new_line = line.replace(match.group(), f"{flag} {country_id} ({country_ru}) {city} <code>{ip_original}</code>")
                    except Exception as e:
                        new_line = line.replace(match.group(), f"Ошибка при обработке IP {ip}: {e}")
                        logging.error(f"Ошибка при обработке IP {ip}: {e}")
                else:
                    new_line = line
                copy_list.append(ip_original + '\n')
                new_text_list.append(new_line + '\n')
    else:
        pass
    return new_text_list, copy_list, grouped_list

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
        ips_to_copy = user_data.get(user_id, [])[0]
        if ips_to_copy:
            # отправляем список IP-адресов пользователю
            formatted_ips = "".join(ips_to_copy)
            await query.message.answer(f"{formatted_ips}", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_check_country'
        else:
            await query.message.answer("Нет сохраненных IP-адресов для копирования.", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_check_country'

    # сценарий № 5: вывод IP-адресов, сгруппированных по городам
    elif query.data == 'group_ips':
        grouped_ips = ips_to_copy = user_data.get(user_id, [])[1]
        if grouped_ips:
            formatted_grouped_ips = "".join(ips_to_copy)
            await query.message.answer(f"{formatted_grouped_ips}", reply_markup=keyboard_choice)
            user_states[user_id] = 'back_to_choice'
        else:
            await query.message.answer("Нет IP-адресов для отображения.", reply_markup=keyboard_choice)
            user_states[user_id] = 'back_to_choice'
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
            result, result_to_copy, result_grouped = await get_ip_info(message.text)
            print(result)
            print(result_to_copy)
            print(result_grouped)
            await message.answer('\n'.join(result), parse_mode="HTML", reply_markup=keyboard_copy_or_grouped)
            user_data[user_id] = [result_to_copy, result_grouped]
        except Exception as e:
            await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_copy_or_grouped)
            user_states[user_id] = 'awaiting_check_country'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")

    # сценарий № 2: фильтрация списков IP-адресов (основной список)
    elif user_state == 'awaiting_filter_first_input':
        if re.findall(pattern, message.text):
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
        if not re.findall(pattern, second_ips):
            await message.answer('Второй список не содержит IP-адреса. Введите второй список еще раз.', reply_markup=keyboard_back)
        else:
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

