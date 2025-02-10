import re
import logging
import traceback

from aiogram.fsm.context import FSMContext

from messages import msg
from states import UserState
from config import pattern

async def filter_ips_input(first_list, filter_type, state: FSMContext):
    """Функция получения списка IP-адресов для фильтрации"""
    if not re.findall(pattern, first_list):
        return msg['no_ips']
    try:
        await state.update_data(first_list=first_list)
        if filter_type == 'filter_by_list':
            await state.set_state(UserState.AWAITING_FILTER_LIST_SECOND)
            return msg['filter_ips_second']
        elif filter_type == 'filter_by_octet':
            await state.set_state(UserState.AWAITING_FILTER_OCTET_SECOND)
            return msg['enter_octet']
        elif filter_type == 'shorten':
            await state.set_state(UserState.AWAITING_FILTER_CHOOSE_FILTER)
            return msg['choose_action']
    except Exception as e:
        logging.error("%s: %s.\nТекст запроса: %s", msg['program_error'], e, first_list)
        logging.error(traceback.format_exc())
        return msg['program_error']

async def filter_ips_list(second_list, state: FSMContext):
    """Функция фильтрации списка IP-адресов по второму списку"""
    if not re.findall(pattern, second_list):
        return msg['no_ips_second']
    else:
        data = await state.get_data()
        first_list_unformatted = data['first_list']
        first_list = re.findall(pattern, first_list_unformatted)
        second_list = re.findall(pattern, second_list)
        result = list(dict.fromkeys([ip for ip in first_list if ip not in second_list]))
        await state.set_state(UserState.AWAITING_FILTER_LIST_FIRST)
        if result:
            return "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"
        else:
            return msg['no_filtered_ips']

async def filter_by_octet(target_octet, state: FSMContext):
    """Функция фильтрации по октету"""
    try:
        target_octet = int(target_octet)
    except ValueError:
        logging.error("Неверно введенный октет: %s", target_octet)
        return msg['invalid_octet']
    if not 0 < target_octet < 256:
        logging.error("Октет вне допустимого диапазона: %s", target_octet)
        return msg['invalid_octet']
    data = await state.get_data()
    first_list = data['first_list']
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

async def shorten_ips(octet_flag, state: FSMContext):
    """Функция обрезки 4-го октета IP-адресов"""
    data = await state.get_data()
    first_list = data['first_list']
    found_ips = re.findall(pattern, first_list)
    if not octet_flag:
        result = found_ips
    else:
        try:
            result = map(lambda ip: ip[:ip.rfind('.')] if ip.count('.') == 3 else ip, found_ips)
        except Exception as e:
            logging.error("Ошибка при фильтрации IP-адресов: %s.\nТекст запроса: %s", e, first_list)
            logging.error(traceback.format_exc())
            return "Произошла ошибка при обработке IP-адресов."
    await state.set_state(UserState.AWAITING_FILTER_SHORTEN_LIST)
    return "Обработанные IP-адреса:\n<code>" + "</code>\n<code>".join(result) + "</code>"