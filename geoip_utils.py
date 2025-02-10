import logging
import re
import traceback
from itertools import chain

import countryflag
import geoip2.database
import geoip2.errors
import pycountry

from config import database_filename, pattern, user_data
from db_capitals_utils import get_capital
from keyboards import keyboard_copy
from messages import msg

async def process_check(message, user_id, target_flag):
    """Функция определения геолокации IP-адресов"""
    try:
        result, result_copy = await get_ip_info(message.text, target_flag=target_flag)
        if not result:
            return await message.answer(msg['no_ips'], parse_mode="HTML" if target_flag else None)
        elif result == 'invalid iso':
            return await message.answer(msg['invalid_iso'], parse_mode="HTML")
        elif isinstance(result, list):
            if target_flag:
                user_data[user_id] = result_copy
            return await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)
        else:
            return await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy if target_flag else None)

    except Exception as e:
        logging.error("%s: %s.\nТекст запроса: %s", msg['program_error'], e, message.text)
        logging.error(traceback.format_exc())
        return await message.answer("%s: %s.", msg['program_error'], e)

async def process_target_copy(user_id):
    """Функция вывода отфильтрованных по стране IP-адресов"""
    result_copy = user_data.get(user_id, [])
    if not result_copy or result_copy == 'ips not found':
        return msg['no_ips_to_copy']
    else:
        if all(isinstance(item, str) for item in result_copy):
            return "\n".join(result_copy)
        else:
            flat_ips = list(chain.from_iterable(
                item if isinstance(item, list) else [item] for item in result_copy))
            return "\n".join(flat_ips)

async def get_ip_info(text_input: str, target_flag: bool):
    """Функция для обработки текста и получения IP-адресов"""
    ip_list_text = text_input.splitlines()
    new_text_dict, result_copy, result = {}, [], []
    valid_target = False
    target_country_iso = ''
    if re.findall(pattern, text_input):
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
    result_copy = "ips not found" if valid_target and not result_copy else result_copy
    return result, result_copy

async def get_ip_info_result(new_text_dict, result):
    """Функция перевода результата get_ip_info в список"""
    for country_iso, country_data in new_text_dict.items():
        for section, section_content in country_data.items():
            if isinstance(section_content, str):
                result.append(section_content)
            elif isinstance(section_content, dict):  # cities
                for city_name, city_ips in section_content.items():
                    result.append(city_name)
                    result.extend(city_ips if isinstance(city_ips, list) else [city_ips])

async def make_cities_dict(match, city_file, new_text_dict, target_flag, target_country_iso, result_copy, line):
    """Функция создания словаря с городами"""
    ip = match + '.0' if match.count('.') == 2 else match

    try:
        response = city_file.city(ip)
        country_id = response.country.iso_code
        country_ru = response.country.names.get('ru', '')
        country_en = response.country.names.get('en', '')
        city = response.city.names.get('ru', '') or await get_capital(country_en)
        flag = countryflag.getflag([country_id])

        if country_id not in new_text_dict:
            new_text_dict[country_id] = {'head': f'\n{flag} {country_id} ({country_ru})', 'cities': {}}

        await add_cities(new_text_dict, match, result_copy, line, country_id, city,
                         target_flag=target_flag and target_country_iso == country_id)

    except Exception as e:
        logging.error(f"Ошибка обработки IP {match}: {e}")

        unknown_cities = new_text_dict.setdefault('Unknown', {}).setdefault('cities', {})
        invalid_ip_list = unknown_cities.setdefault('\n❌Invalid IP', [])
        invalid_ip_list.append(line.replace(match, f"<b><code>{match}</code></b>"))

async def add_cities(new_text_dict, match, result_copy, line, country_id, city, target_flag=False):
    """Функция добавления городов с IP-адресами в результирующие списки"""
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match, f"<code>{match}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(match, f"<code>{match}</code>")
)
    if target_flag:
        result_copy.append(line.replace(match, f"<code>{match}</code>"))