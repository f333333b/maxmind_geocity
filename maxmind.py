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
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from capitals import capitals
from itertools import chain

# основной код
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LICENSE_KEY = os.getenv('LICENSE_KEY')
bot = Bot(token=TOKEN)
dp = Dispatcher()
database_filename = 'GeoLite2-City.mmdb'
url = (
    f"https://download.maxmind.com/app/geoip_download?"
    f"edition_id=GeoLite2-City&license_key={LICENSE_KEY}"
    f"&suffix=tar.gz"
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

# справка
help_text = (
        "🤖 **Справка**\n\n"
        "Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Получить справку\n\n"
        "<b>Проверить страну по IP-адресу:</b>\n"
        "1. Введите текст, содержащий IP-адрес(а). Бот построчно проверяет текст и определяет наличие IP-адресов.\n"
        "2. Найденные IP-адреса группируются по странам, а внутри стран — по городам.\n"
        "3. Если в тексте первыми двумя буквами указан ISO-код страны (например, \"US\" для США), IP-адреса этой страны будут выведены первыми в результирующем списке.\n"
        "4. Каждый IP-адрес кликабелен — при нажатии копируется в буфер обмена.\n\n"
        "<b>Пример запроса:</b>\n"
        "\n"
        "US\n"
        "Сервер №36 (35 прокси, 5 подсетей):\n"
        "171.22.76. - 12 прокси\n"
        "102.129.221. - 7 прокси\n"
        "181.214.117. - 6 прокси\n"
        "Сервер №188 (30 прокси, 2 подсетей):\n"
        "195.96.157. - 18 прокси\n"
        "88.216.43. - 12 прокси\n"
        "Сервер №193 (9 прокси, 1 подсетей):\n"
        "176.100.44. - 9 прокси\n"
        "\n\n"
        "<b>Пример ответа:</b>\n"
        "\n"
        "🇺🇸 US (США)\n"
        "Джэксонвилл\n"
        "171.22.76. - 12 прокси\n"
        "Вашингтон\n"
        "102.129.221. - 7 прокси\n"
        "Сакраменто\n"
        "176.100.44. - 9 прокси\n\n"
        "🇦🇪 AE (ОАЭ)\n"
        "Абу-Даби\n"
        "181.214.117. - 6 прокси\n\n"
        "🇸🇨 SC (Сейшельские о-ва)\n"
        "Виктория\n"
        "195.96.157. - 18 прокси\n\n"
        "🇱🇹 LT (Литва)\n"
        "Вильнюс\n"
        "88.216.43. - 12 прокси\n"
        "\n\n"
        "После выполнения этой функции станет доступна кнопка <b>\"Скопировать все IP-адреса\"</b>, которая выдает список всех IP-адресов страны, ISO-код которой был введен в тексте запроса.\n"
        "Если в тексте запроса не был указан ISO-код страны, команда выводит все определенные IP-адреса.\n\n"
        "<b>Пример вывода кнопки \"Скопировать все IP-адреса\":</b>\n"
        "\n"
        "171.22.76. - 12 прокси\n"
        "102.129.221. - 7 прокси\n"
        "181.214.117. - 6 прокси\n"
        "195.96.157. - 18 прокси\n"
        "88.216.43. - 12 прокси\n"
        "176.100.44. - 9 прокси\n"
        "\n\n"
        "<b>Отфильтровать IP:</b>\n"
        "1. Введите первый текст со списком IP-адресов.\n"
        "2. Введите второй текст со списком IP-адресов, которые нужно исключить из первого списка.\n"
        "3. Бот выведет отфильтрованный список IP-адресов."
    )

# кнопки для выбора действия
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

keyboard_choice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Проверить страну по IP-адресу", callback_data="check_country")],
        [InlineKeyboardButton(text="Фильтровать IP", callback_data="filter_ips_1")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]

    ]
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отфильтровать IP-адреса по стране", callback_data="copy_ips")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

keyboard_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

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
                            await bot.send_message(chat_id=user_id, text="База данных обновлена.")
                        else:
                            logging.error(f"Файл {database_filename} не найден в архиве.")
                            await bot.send_message(chat_id=user_id, text="При обновлении базы данных произошла ошибка.", reply_markup=keyboard_choice)
            else:
                logging.error(f"Ошибка при скачивании базы данных: {response.status}")
    user_states[user_id] = 'back_to_choice'

# функция проверки наличия базы и ее актуальности
async def is_update_needed(user_id):
    if not os.path.exists(database_filename):
        await download_database(user_id)
    else:
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
    first_list = re.findall(pattern, first_input)
    second_list = re.findall(pattern, second_input)

    return [ip for ip in first_list if ip not in second_list]

# функция для обработки текста и получения IP-адресов
async def get_ip_info(text_input: str):
    all_ips = re.findall(pattern, text_input)
    target_country = text_input[:2]
    ip_list_text = text_input.splitlines()
    new_text_dict, result_copy = {}, []
    if all_ips:
        with (geoip2.database.Reader(database_filename) as city_file):
            for line in ip_list_text:
                match = re.search(pattern, line)
                if match:
                    ip_original = match.group()
                    ip = ip_original + '.0'
                    response = city_file.city(ip)
                    country_id = response.country.iso_code
                    country_ru = response.country.names.get('ru', '')
                    country_en = response.country.names.get('en', '')
                    city = response.city.names.get('ru', '')
                    if not city:
                        city = capitals[country_en]
                    flag = countryflag.getflag([country_id])
                    if text_input[:2].isalpha() and text_input[:2].isupper():
                        if target_country not in new_text_dict:
                            new_text_dict[target_country] = {'head': f'\n{countryflag.getflag([target_country])} {target_country}'}
                        if 'cities' not in new_text_dict[target_country]:
                            new_text_dict[target_country]['cities'] = {}
                    if country_id not in new_text_dict:
                        new_text_dict[country_id] = {'head': f'\n{flag} {country_id} ({country_ru})', 'cities': {}}
                    if target_country == country_id:
                        if country_ru not in new_text_dict[country_id]['head']:
                            new_text_dict[country_id]['head'] += f' ({country_ru})'
                        add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=True)
                    else:
                        add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city)
        result = []

    for ISO, v in new_text_dict.items():
        for country_dictionary, dictionary_content in v.items():
            if isinstance(dictionary_content, str):
                result.append(dictionary_content)
            elif isinstance(dictionary_content, dict):
                for city_name, v2 in dictionary_content.items():
                    result.append(city_name)
                    for ip_addresses in v2:
                        result.extend(ip_addresses if isinstance(ip_addresses, list) else [ip_addresses])
        return result, result_copy
    else:
        return [], []


# функция добавления городов с IP-адресами в результирующие списки
def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    new_text_dict[country_id]['cities'][city].append(line.replace(match.group(), f"<code>{ip_original}</code>"))
    if target_flag:
        result_copy.append(line.replace(match.group(), f"<code>{ip_original}</code>"))

# обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Здравствуйте! Выберете нужное действие:", reply_markup=keyboard_choice)

@dp.message(Command("help"))
async def command_help_handler(message: Message):
    await message.answer(help_text, parse_mode='HTML', reply_markup=keyboard_choice)

# обработка callback-запросов от кнопок
@dp.callback_query()
async def handle_callback(query: CallbackQuery):
    user_id = query.from_user.id

    # сценарий № 1: определение страны по IP-адресу
    if query.data == 'check_country':
        user_states[user_id] = 'awaiting_check_country'
        await query.message.answer("Введите текст с IP-адресами, и я определю их местоположение (не более 50 IP-адресов за один запрос).", reply_markup=keyboard_back)

    # сценарий № 2: фильтрация списков IP-адресов (основной список)
    elif query.data == 'filter_ips_1':
        user_states[user_id] = 'awaiting_filter_first_input'
        await query.message.answer("Введите список IP-адресов, которые нужно отфильтровать.", reply_markup=keyboard_back)

    # сценарий № 3: фильтрация списков IP-адресов (второй список)
    elif query.data == 'filter_ips_2':
        user_states[user_id] = 'awaiting_filter_second_input'
        await query.message.answer("Введите второй список IP-адресов.", reply_markup=keyboard_back)

    # сценарий № 4: вывод IP-адресов в столбик для копирования
    elif query.data == 'copy_ips':
        result_copy = user_data.get(user_id, [])
        if not result_copy:
            await query.message.answer("Не указана страна для фильтрации IP-адресов. Введите текст снова с указанием ISO-кода страны.", reply_markup=keyboard_back)
        else:
            if all(isinstance(item, str) for item in result_copy):
                # отправляем список IP-адресов пользователю
                formatted_ips = "\n".join(result_copy)
                await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
            else:
                flat_ips = list(chain.from_iterable(
                    item if isinstance(item, list) else [item] for item in result_copy))
                formatted_ips = "\n".join(flat_ips)
                await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
        user_states[user_id] = 'awaiting_check_country'

    # сценарий № 5: помощь (справка)
    elif query.data == "help":
        await query.message.answer(help_text, parse_mode="HTML", reply_markup=keyboard_choice)
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
            result, result_copy = await get_ip_info(message.text)
            if result:
                await message.answer('\n'.join(result), parse_mode="HTML", reply_markup=keyboard_copy)
                user_data[user_id] = result_copy
            else:
                await message.answer('Во введенном текст IP-адреса не найдены. Попробуй еще раз.', parse_mode="HTML", reply_markup=keyboard_back)
        except Exception as e:
            await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_copy)
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
