import re
import os
import geoip2.database
import geoip2.errors
import countryflag
import pycountry
import logging
import traceback
from itertools import chain
from functools import wraps
from capitals import capitals
from messages import msg
from keyboards import keyboard_copy
from config import pattern, database_filename, user_loggers, user_states, user_data, user_ips
from aiogram.types import Message, CallbackQuery, ContentType

# функция запуска логирования
async def setup_user_logger(user_id):
    if user_id in user_loggers:
        user_loggers[user_id]

    log_filename = f"logs/{user_id}.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logger = logging.getLogger(str(user_id))

    # отключение вывода логирования в консоль
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(log_filename, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    user_loggers[user_id] = logger
    return logger

# функция декоратор для логирования сообщений
def log_interaction(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        logger = await setup_user_logger(user_id)

        if isinstance(event, Message):
            if event.content_type == ContentType.TEXT:
                text = event.text
                logger.info(f"Пользователь ({user_id}) отправил сообщение:\n{text}")
            else:
                logger.info(f"Пользователь ({user_id}) отправил неподдерживаемый формат контента:\n{event.content_type}")
        elif isinstance(event, CallbackQuery):
            data = event.data
            logger.info(f"Пользователь ({user_id}) нажал кнопку:\n{data}")

        bot_response = await func(event, *args, **kwargs)
        if bot_response:
            if isinstance(bot_response, Message):
                logger.info(f"Ответ бота:\n{bot_response.text if bot_response.text else 'Текст отсутствует'}")
            elif isinstance(bot_response, CallbackQuery):
                logger.info(f"Ответ бота:\n{bot_response.data}")
            else:
                logger.info(f"Ответ бота:\n{str(bot_response)}")
        else:
            logger.info("Ответ бота:\nпусто")

        return bot_response
    return wrapper

# функция определения геолокации IP-адресов
async def process_check(user_state_key, message, user_id, target_flag):
    try:
        result, result_copy = await get_ip_info(message.text, target_flag=target_flag)
        if result:
            if result == 'invalid iso':
                user_states[user_id] = user_state_key
                return await message.answer(msg['invalid_iso'], parse_mode="HTML")
            elif isinstance(result, list):
                if target_flag:  # Сохраняем данные только для awaiting_target_check
                    user_data[user_id] = result_copy
                return await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)
            else:
                return await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)
        else:
            return await message.answer(msg['no_ips'], parse_mode="HTML" if target_flag else None)
    except Exception as e:
        user_states[user_id] = user_state_key
        logging.error(f"{msg['program_error']}: {e}.\nТекст запроса: {message.text}")
        logging.error(traceback.format_exc())
        return await message.answer(f"{msg['program_error']}: {e}.")

# функция вывода отфильтрованных по стране IP-адресов
async def process_target_output(user_id):
    result_copy = user_data.get(user_id, [])
    if not result_copy or result_copy == 'ips not found':
        return None, msg['no_ips_to_copy']
    else:
        if all(isinstance(item, str) for item in result_copy):
            return "\n".join(result_copy), None
        else:
            flat_ips = list(chain.from_iterable(
                item if isinstance(item, list) else [item] for item in result_copy))
            return "\n".join(flat_ips)

# функция для обработки текста и получения IP-адресов
async def get_ip_info(text_input: str, target_flag: bool):
    all_ips = re.findall(pattern, text_input)
    ip_list_text = text_input.splitlines()
    new_text_dict, result_copy = {}, []
    result = []
    valid_target = False
    target_country_iso = ''
    if all_ips:
        if target_flag:
            try:
                target_country_iso = text_input[:2].upper()
                if not (target_country_iso.isalpha() and target_country_iso.isascii()
                        and pycountry.countries.get(alpha_2=target_country_iso)):
                    return 'invalid iso', ''
                valid_target = True
                new_text_dict[target_country_iso] = {'head': f'\n{countryflag.getflag([target_country_iso])} {target_country_iso}', 'cities': {}}
            except Exception as e:
                return 'invalid iso', ''
        with geoip2.database.Reader(database_filename) as city_file:
            for line in ip_list_text:
                match = re.findall(pattern, line)
                if match:
                    for match_instance in match:
                        await make_cities_dict(match_instance, city_file, new_text_dict, target_flag,
                                                   target_country_iso, result_copy, line)
            for ISO, v in new_text_dict.items():
                for country_dictionary, dictionary_content in v.items():
                    if isinstance(dictionary_content, str):
                        result.append(dictionary_content)
                    elif isinstance(dictionary_content, dict):
                        for city_name, v2 in dictionary_content.items():
                            result.append(city_name)
                            for ip_addresses in v2:
                                result.extend(ip_addresses if isinstance(ip_addresses, list) else [ip_addresses])
    if valid_target and not result_copy:
        result_copy = 'ips not found'
    return result, result_copy

# функция добавления городов с IP-адресами в результирующие списки
async def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match, f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(ip_original, f"<code>{ip_original}</code>")
)
    if target_flag:
        result_copy.append(line.replace(ip_original, f"<code>{ip_original}</code>"))

# функция создания словаря с городами
async def make_cities_dict(match, city_file, new_text_dict, target_flag, target_country_iso, result_copy, line):
    ip_original = match
    if match.count('.') == 2:
        ip = ip_original + '.0'
    elif match.count('.') == 3:
        ip = ip_original
    try:
        response = city_file.city(ip)
        country_id = response.country.iso_code
        country_ru = response.country.names.get('ru', '')
        country_en = response.country.names.get('en', '')
        city = response.city.names.get('ru', '')
        if not city:
            city = capitals[country_en]
        flag = countryflag.getflag([country_id])
        if country_id not in new_text_dict:
            new_text_dict[country_id] = {'head': f'\n{flag} {country_id} ({country_ru})', 'cities': {}}
        if target_flag:
            if target_country_iso == country_id:
                await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city,
                                 target_flag=True)
            await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city)
        else:
            await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city)
    # когда IP-адрес не найден в базе данных
    except:
        if 'Unknown' not in new_text_dict:
            new_text_dict['Unknown'] = {}
            if 'cities' not in new_text_dict['Unknown']:
                new_text_dict['Unknown']['cities'] = {}
                if '\n❌Invalid IP' not in new_text_dict['Unknown']['cities']:
                    new_text_dict['Unknown']['cities']['\n❌Invalid IP'] = []
            new_text_dict['Unknown']['cities']['\n❌Invalid IP'].append(
                line.replace(match, f"<b><code>{ip_original}</code></b>"))

# функция получения списка IP-адресов для фильтрации
async def filter_ips_input(first_list, user_id, list_flag):
    if not re.findall(pattern, first_list):
        return msg['no_ips']
    try:
        user_ips[user_id] = {'first': first_list}
        if list_flag:
            user_states[user_id] = 'awaiting_filter_second_input'
            return msg['filter_ips_second']
        else:
            user_states[user_id] = 'awaiting_filter_by_octet'
            return msg['enter_octet']
    except Exception as e:
        logging.error(f"{msg['program_error']}: {e}.\nТекст запроса: {first_list}")
        logging.error(traceback.format_exc())
        return msg['program_error']

# функция фильтрации списка IP-адресов по второму списку
async def filter_ips_list(second_list, user_id):
    if not re.findall(pattern, second_list):
        return msg['no_ips_second']
    else:
        first_list = re.findall(pattern, user_ips[user_id]['first'])
        second_list = re.findall(pattern, second_list)
        result = list(dict.fromkeys([ip for ip in first_list if ip not in second_list]))
        user_states[user_id] = 'awaiting_filter_first_input'
        if result:
            return "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"
        else:
            return msg['no_filtered_ips']

# функция фильтрации по октету
async def filter_by_octet(target_octet, user_id):
    try:
        target_octet = int(target_octet)
    except ValueError:
        logging.error(f"Неверно введенный октет: {target_octet}")
        user_states[user_id] = 'awaiting_filter_octet_second'
        return msg['invalid_octet']
    if not 0 < target_octet < 256:
        logging.error(f"Октет вне допустимого диапазона: {target_octet}")
        user_states[user_id] = 'awaiting_filter_octet_second'
        return msg['invalid_octet']
    first_list = user_ips[user_id]['first']
    found_ips = re.findall(pattern, first_list)
    try:
        result = list(dict.fromkeys([ip for ip in found_ips if ip.split('.')[0] != str(target_octet)]))
        if not result:
            user_states[user_id] = 'awaiting_filter_octet_list'
            return msg['no_filtered_ips']
        user_states[user_id] = 'awaiting_filter_octet_list'
        return "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"
    except Exception as e:
        logging.error(f"Ошибка при фильтрации IP-адресов: {e}.\nТекст запроса: {first_list}")
        logging.error(traceback.format_exc())
        user_states[user_id] = 'awaiting_filter_octet_second'
        return msg['filter_error']