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
        if result:
            if result == 'invalid iso':
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
    logging.debug(f"add_cities finished with: {new_text_dict}\n{ip_original}\n{result_copy}\n{line}\n{match}\n{country_id}\n{city}\n{target_flag}")
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match, f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(ip_original, f"<code>{ip_original}</code>")
)
    if target_flag:
        result_copy.append(line.replace(ip_original, f"<code>{ip_original}</code>"))
    logging.debug(f"add_cities finished with: {new_text_dict}\n{ip_original}\n{result_copy}\n{line}\n{match}\n{country_id}\n{city}\n{target_flag}")

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
            city = await get_capital(country_en)
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