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
from states import UserState
from aiogram.fsm.context import FSMContext
from config import pattern, database_filename, user_loggers, user_data, user_ips
from aiogram.types import Message, CallbackQuery, ContentType

async def setup_user_logger(user_id):
    """Функция запуска логирования"""
    if user_id in user_loggers:
        user_loggers[user_id]

    log_filename = "logs/{}.log".format(user_id)
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

def log_interaction(func):
    """Функция-декоратор для логирования сообщений"""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        logger = await setup_user_logger(user_id)
        if isinstance(event, Message):
            if event.content_type == ContentType.TEXT:
                text = event.text
                logger.info("Пользователь (%s) отправил сообщение:\n%s", user_id, text)
            else:
                logger.info("Пользователь (%s) отправил неподдерживаемый формат контента:\n%s", user_id, event.content_type)
        elif isinstance(event, CallbackQuery):
            data = event.data
            logger.info("Пользователь (%s) нажал кнопку:\n%s", user_id, data)
        bot_response = await func(event, *args, **kwargs)
        if bot_response:
            if isinstance(bot_response, Message):
                logger.info("Ответ бота:\n%s", bot_response.text if bot_response.text else "Текст отсутствует")
            elif isinstance(bot_response, CallbackQuery):
                logger.info("Ответ бота:\n%s", bot_response.data)
            else:
                logger.info("Ответ бота:\n%s", str(bot_response))
        else:
            logger.info("Ответ бота:\nпусто")
        return bot_response
    return wrapper

async def process_check(message, user_id, target_flag):
    """Функция определения геолокации IP-адресов"""
    try:
        result, result_copy = await get_ip_info(message.text, target_flag=target_flag)
        if result:
            if result == 'invalid iso':
                #await state.set_state(UserState.ЖЕЛАЕМОЕ_СОСТОЯНИЕ)
                return await message.answer(msg['invalid_iso'], parse_mode="HTML")
            elif isinstance(result, list):
                if target_flag:
                    user_data[user_id] = result_copy
                return await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)
            else:
                return await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)
        else:
            return await message.answer(msg['no_ips'], parse_mode="HTML" if target_flag else None)
    except Exception as e:
        # user_states[user_id] = user_state_key
        logging.error("%s: %s.\nТекст запроса: %s", msg['program_error'], e, message.text)
        logging.error(traceback.format_exc())
        return await message.answer("%s: %s.", msg['program_error'], e)

async def process_target_copy(result_copy):
    """Функция вывода отфильтрованных по стране IP-адресов"""
    if not result_copy or result_copy == 'ips not found':
        return None, msg['no_ips_to_copy']
    else:
        if all(isinstance(item, str) for item in result_copy):
            return "\n".join(result_copy), None
        else:
            flat_ips = list(chain.from_iterable(
                item if isinstance(item, list) else [item] for item in result_copy))
            return "\n".join(flat_ips)

    user_id = query.message.from_user.id
    result_copy = user_data.get(user_id, [])
    if not result_copy:
        return await query.message.answer(msg['no_ips_to_copy'], reply_markup=keyboard_back)
    elif result_copy == 'ips not found':
        return await query.message.answer(msg['no_ips_to_copy'], reply_markup=keyboard_back)
    elif result_copy == 'empty':
        user_states[user_id] = 'awaiting_target_check'
        return await query.message.answer(msg['no_ips_to_copy'], parse_mode="HTML", reply_markup=keyboard_back)
    else:
        if all(isinstance(item, str) for item in result_copy):
            # отправляем список IP-адресов пользователю
            formatted_ips = "\n".join(result_copy)
            return await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
        else:
            flat_ips = list(chain.from_iterable(
                item if isinstance(item, list) else [item] for item in result_copy))
            formatted_ips = "\n".join(flat_ips)
            return await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
    user_states[user_id] = 'awaiting_target_check'

async def get_ip_info(text_input: str, target_flag: bool):
    """Функция для обработки текста и получения IP-адресов"""
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
            await get_ip_info_result(new_text_dict, result)
    if valid_target and not result_copy:
        result_copy = 'ips not found'
    return result, result_copy

async def get_ip_info_result(new_text_dict, result):
    """Функция перевода результата get_ip_info в список"""
    for ISO, v in new_text_dict.items():
        for country_dictionary, dictionary_content in v.items():
            if isinstance(dictionary_content, str):
                result.append(dictionary_content)
            elif isinstance(dictionary_content, dict):
                for city_name, v2 in dictionary_content.items():
                    result.append(city_name)
                    for ip_addresses in v2:
                        result.extend(ip_addresses if isinstance(ip_addresses, list) else [ip_addresses])

async def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    """Функция добавления городов с IP-адресами в результирующие списки"""
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match, f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(ip_original, f"<code>{ip_original}</code>")
)
    if target_flag:
        result_copy.append(line.replace(ip_original, f"<code>{ip_original}</code>"))

async def make_cities_dict(match, city_file, new_text_dict, target_flag, target_country_iso, result_copy, line):
    """Функция создания словаря с городами"""
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
    except:
        if 'Unknown' not in new_text_dict:
            new_text_dict['Unknown'] = {}
            if 'cities' not in new_text_dict['Unknown']:
                new_text_dict['Unknown']['cities'] = {}
                if '\n❌Invalid IP' not in new_text_dict['Unknown']['cities']:
                    new_text_dict['Unknown']['cities']['\n❌Invalid IP'] = []
            new_text_dict['Unknown']['cities']['\n❌Invalid IP'].append(
                line.replace(match, f"<b><code>{ip_original}</code></b>"))

async def filter_ips_input(first_list, user_id, list_flag, state: FSMContext):
    """Функция получения списка IP-адресов для фильтрации"""
    if not re.findall(pattern, first_list):
        return msg['no_ips']
    try:
        user_ips[user_id] = {'first': first_list}
        if list_flag:
            await state.set_state(UserState.AWAITING_FILTER_LIST_SECOND)
            return msg['filter_ips_second']
        else:
            await state.set_state(UserState.AWAITING_FILTER_OCTET_SECOND)
            return msg['enter_octet']
    except Exception as e:
        logging.error("%s: %s.\nТекст запроса: %s", msg['program_error'], e, first_list)
        logging.error(traceback.format_exc())
        return msg['program_error']

async def filter_ips_list(second_list, user_id, state: FSMContext):
    """Функция фильтрации списка IP-адресов по второму списку"""
    if not re.findall(pattern, second_list):
        return msg['no_ips_second']
    else:
        first_list = re.findall(pattern, user_ips[user_id]['first'])
        second_list = re.findall(pattern, second_list)
        result = list(dict.fromkeys([ip for ip in first_list if ip not in second_list]))
        await state.set_state(UserState.AWAITING_FILTER_LIST_FIRST)
        if result:
            return "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"
        else:
            return msg['no_filtered_ips']

async def filter_by_octet(target_octet, user_id, state: FSMContext):
    """Функция фильтрации по октету"""
    try:
        target_octet = int(target_octet)
    except ValueError:
        logging.error("Неверно введенный октет: %s", target_octet)
        return msg['invalid_octet']
    if not 0 < target_octet < 256:
        logging.error("Октет вне допустимого диапазона: %s", target_octet)
        return msg['invalid_octet']
    first_list = user_ips[user_id]['first']
    found_ips = re.findall(pattern, first_list)
    try:
        result = list(dict.fromkeys([ip for ip in found_ips if ip.split('.')[0] != str(target_octet)]))
        await state.set_state(UserState.AWAITING_FILTER_OCTET_FIRST)
        if not result:
            return msg['no_filtered_ips']
        return "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"
    except Exception as e:
        logging.error("Ошибка при фильтрации IP-адресов: %s.\nТекст запроса: %s", e, first_list)
        logging.error(traceback.format_exc())
        return msg['filter_error']