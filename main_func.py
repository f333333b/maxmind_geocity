import geoip2.database
import geoip2.errors
import countryflag
import pycountry
from capitals import capitals
from config import pattern_subnet, pattern_ip, database_filename

# функция фильтрации списков IP-адресов
import re


async def to_filter_ips(first_input, second_input):
    first_ips = re.findall(pattern_ip, first_input)
    first_subnets = re.findall(pattern_subnet, first_input)
    second_ips = re.findall(pattern_ip, second_input)
    second_subnets = re.findall(pattern_subnet, second_input)
    first_subnets = [subnet for subnet in first_subnets if not any(subnet in ip for ip in first_ips)]
    second_subnets = [subnet for subnet in second_subnets if not any(subnet in ip for ip in second_ips)]
    first_list = first_ips + first_subnets
    second_list = second_ips + second_subnets
    return [ip for ip in first_list if ip not in second_list]

# функция для обработки текста и получения IP-адресов
async def get_ip_info(text_input: str, target_flag: bool):
    all_ips = re.findall(pattern_subnet, text_input)
    ip_list_text = text_input.splitlines()
    new_text_dict, result_copy = {}, []
    result = []
    valid_target = False
    subnet_flag = False
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
                if re.findall(pattern_ip, line):
                    match = re.findall(pattern_ip, line)
                else:
                    match = re.findall(pattern_subnet, line)
                    subnet_flag = True
                if match:
                    if isinstance(match, list):
                        for match_instance in match:
                            await make_cities_dict(match_instance, city_file, new_text_dict, target_flag, subnet_flag,
                                                   target_country_iso, result_copy, line)
                    else:
                        await make_cities_dict(match, city_file, new_text_dict, target_flag, subnet_flag,
                                               target_country_iso, result_copy, line)
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
    print("new_text_dict:", new_text_dict)
    return result, result_copy

# функция добавления городов с IP-адресами в результирующие списки
async def add_cities(new_text_dict, ip_original, result_copy, line, match, country_id, city, target_flag=False):
    print(f"Добавляю: {ip_original} → {city}")
    if city not in new_text_dict[country_id]['cities']:
        new_text_dict[country_id]['cities'][city] = []
    if line.replace(match, f"<code>{ip_original}</code>") not in new_text_dict[country_id]['cities'][city]:
        new_text_dict[country_id]['cities'][city].append(line.replace(ip_original, f"<code>{ip_original}</code>")
)
    if target_flag:
        result_copy.append(line.replace(ip_original, f"<code>{ip_original}</code>"))

async def make_cities_dict(match, city_file, new_text_dict, target_flag, subnet_flag, target_country_iso, result_copy, line):
    print(match, "→ make_cities_dict")
    ip_original = match
    ip = ip_original + '.0' if subnet_flag else ip_original
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
                line.replace(match, f"<code>{ip_original}</code>"))
