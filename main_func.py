import re
import geoip2.database
import geoip2.errors
import countryflag
import pycountry
import traceback
from capitals import capitals
from config import pattern, database_filename
from aiogram.types import BotCommand

# функция фильтрации списков IP-адресов
async def to_filter_ips(first_input, second_input):
    first_list = re.findall(pattern, first_input)
    second_list = re.findall(pattern, second_input)

    return [ip for ip in first_list if ip not in second_list]

# функция для обработки текста и получения IP-адресов
async def get_ip_info(text_input: str, target_flag: bool):
    all_ips = re.findall(pattern, text_input)
    ip_list_text = text_input.splitlines()
    new_text_dict, result_copy = {}, []
    result = []
    if all_ips:
        if target_flag:
            try:
                target_country_iso = text_input[:2].upper()
                if (not (target_country_iso.isalpha() and target_country_iso.isascii()) and
                        pycountry.countries.get(alpha_2=target_country_iso)):
                    result = 'invalid iso'
                    raise Exception(result)
                valid_target = True
                new_text_dict[target_country_iso] = {'head': f'\n{countryflag.getflag([target_country_iso])} {target_country_iso}', 'cities': {}}
            except Exception as e:
                return 'invalid iso', ''
        with geoip2.database.Reader(database_filename) as city_file:
            for line in ip_list_text:
                match = re.search(pattern, line)
                if match:
                    ip_original = match.group()
                    ip = ip_original + '.0'
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
                                await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=True)
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
                                line.replace(match.group(), f"<code>{ip_original}</code>"))
            if not result:
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
        result_copy = 'empty'
    return result, result_copy

# функция добавления городов с IP-адресами в результирующие списки
async def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match.group(), f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(match.group(), f"<code>{ip_original}</code>"))
    if target_flag:
        result_copy.append(line.replace(match.group(), f"<code>{ip_original}</code>"))
