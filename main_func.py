import re
import geoip2.database
import geoip2.errors
import countryflag
import pycountry
import traceback
from capitals import capitals
from config import pattern, database_filename

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
    result = []
    if all_ips:
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
                        iso_input = text_input[:2].upper()
                        if iso_input.isalpha() and iso_input.isascii():
                            try:
                                pycountry.countries.get(alpha_2=iso_input)
                                if target_country not in new_text_dict:
                                    new_text_dict[target_country] = {'head': f'\n{countryflag.getflag([target_country])} {target_country}'}
                                if 'cities' not in new_text_dict[target_country]:
                                    new_text_dict[target_country]['cities'] = {}
                            except:
                                result = 'invalid iso'
                        if not result:
                            if country_id not in new_text_dict:
                                new_text_dict[country_id] = {'head': f'\n{flag} {country_id} ({country_ru})', 'cities': {}}
                            if target_country == country_id:
                                if country_ru not in new_text_dict[country_id]['head']:
                                    new_text_dict[country_id]['head'] += f' ({country_ru})'
                                await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=True)
                            else:
                                await add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city)
                    except:
                        result = 'invalid ip'
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
                if iso_input.isalpha() and iso_input.isupper() and not result_copy:
                    result_copy = 'ips not found'
    return result, result_copy

# функция добавления городов с IP-адресами в результирующие списки
async def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match.group(), f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(match.group(), f"<code>{ip_original}</code>"))
    if target_flag:
        result_copy.append(line.replace(match.group(), f"<code>{ip_original}</code>"))
