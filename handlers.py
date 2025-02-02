import logging
import re
import traceback
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Router
from itertools import chain
from help import help_text
from keyboards import keyboard_choice, keyboard_back, keyboard_copy
from db_updating import is_update_needed
from main_func import get_ip_info, filter_ips, filter_by_octet, log_interaction
from config import pattern_subnets_and_ips, user_states, user_data, user_ips

router = Router()

# обработка отправки фото, файлов и т.п.
@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def handle_unsupported_content(message: Message):
    return await message.answer("Бот поддерживает только текстовые сообщения.", reply_markup=keyboard_back)

# обработка команды /start
@router.message(CommandStart())
@log_interaction
async def command_start_handler(message: Message):
    return await message.answer(f"Выберете нужное действие:", reply_markup=keyboard_main)

@router.message(Command("help"))
@log_interaction
async def command_help_handler(message: Message):
    return await message.answer(help_text, parse_mode='HTML', reply_markup=keyboard_choice)

# обработка callback-запросов от кнопок
@router.callback_query()
@log_interaction
async def handle_callback(query: CallbackQuery):
    user_id = query.from_user.id

    # сценарий № 1: определение геолокации IP-адресов
    if query.data == 'basic_check':
        user_states[user_id] = 'awaiting_basic_check'
        return await query.message.answer("Введите текст с IP-адресами.", reply_markup=keyboard_back)

    # сценарий № 2: определение геолокации IP-адресов с фильтрацией по стране
    elif query.data == 'target_check':
        user_states[user_id] = 'awaiting_target_check'
        return await query.message.answer('Введите текст с IP-адресами.\nПервыми двумя буквами текста укажите\nISO-код страны.',
            reply_markup=keyboard_back)

    # сценарий № 3: фильтрация списков IP-адресов (основной список)
    elif query.data == 'filter_ips_1':
        user_states[user_id] = 'awaiting_filter_first_input'
        return await query.message.answer("Введите список IP-адресов, которые нужно отфильтровать.", reply_markup=keyboard_back)

    # сценарий № 4: фильтрация списка IP-адресов по октету (ввод списка)
    elif query.data == 'callback_filter_by_octet':
        user_states[user_id] = 'awaiting_filter_octet_first'
        return await query.message.answer("Введите список IP-адресов, которые нужно отфильтровать.", reply_markup=keyboard_back)

    # сценарий № 5: вывод IP-адресов в столбик для копирования
    elif query.data == 'copy_ips':
        result_copy = user_data.get(user_id, [])
        if not result_copy:
            return await query.message.answer('Не указана страна для фильтрации IP-адресов.\nВведите текст с указанием ISO-кода страны (например, "US" для США).', reply_markup=keyboard_back)
        elif result_copy == 'ips not found':
            return await query.message.answer('IP-адреса указанной страны не найдены в тексте.', reply_markup=keyboard_back)
        elif result_copy == 'empty':
            user_states[user_id] = 'awaiting_target_check'
            return await query.message.answer('IP-адреса указанной страны отсутствуют в тексте.', parse_mode="HTML", reply_markup=keyboard_back)
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

    # сценарий № 6: помощь (справка)
    elif query.data == "help":
        return await query.message.answer(help_text, parse_mode="HTML", reply_markup=keyboard_choice)
    elif query.data == "back_to_choice":
        return await query.message.answer(text='Выберете нужное действие:', reply_markup=keyboard_choice)


# обработка сообщений
@router.message()
@log_interaction
async def handle_text(message: Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    # проверка на наличие актуальной скачанной базы данных
    update_result = await is_update_needed(user_id)
    if update_result == 'error':
        return await message.answer(f"При обновлении базы данных возникла ошибка. Попробуйте позднее.")

    # проверка на ввод неверной команды
    if message.text.startswith('/') and message.text.count('\n') <= 1:
        return await message.answer(f'Неизвестная команда.\nДля получения справки наберите /help.', reply_markup=keyboard_back)

    # сценарий № 1: определение геолокации IP-адресов с фильтрацией по стране
    elif user_state == 'awaiting_target_check':
        try:
            result, result_copy = await get_ip_info(message.text, target_flag=True)
            if result:
                if result == 'invalid iso':
                    user_states[user_id] = 'awaiting_target_check'
                    return await message.answer('Введен неверный ISO-код страны.\nВведите текст заново, первыми двумя буквами укажите ISO-код страны.\nНапример, "US" для США.', parse_mode="HTML", reply_markup=keyboard_back)
                elif isinstance(result, list):
                    user_data[user_id] = result_copy
                    return await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_copy)
                else:
                    return await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy)
            else:
                return await message.answer('Во введенном тексте IP-адреса не найдены. Попробуйте еще раз.', parse_mode="HTML", reply_markup=keyboard_back)
        except Exception as e:
            user_states[user_id] = 'awaiting_target_check'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
            logging.error(traceback.format_exc())
            return await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_copy)

    # сценарий # 2: определение геолокации IP-адресов
    elif user_state == 'awaiting_basic_check':
        try:
            result, result_copy = await get_ip_info(message.text, target_flag=False)
            if result:
                if result == 'invalid iso':
                    user_states[user_id] = 'awaiting_basic_check'
                    return await message.answer('Введен неверный ISO-код страны.\nПервыми двумя буквами в тексте укажите ISO-код страны.\nНапример, "US" для США.', parse_mode="HTML", reply_markup=keyboard_back)
                elif isinstance(result, list):
                    return await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_back)
                else:
                    return await message.answer(result, parse_mode="HTML", reply_markup=keyboard_back)
            else:
                return await message.answer('Во введенном тексте IP-адреса не найдены. Попробуйте еще раз.', parse_mode="HTML", reply_markup=keyboard_back)
        except Exception as e:
            user_states[user_id] = 'awaiting_basic_check'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
            logging.error(traceback.format_exc())
            return await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_back)

    # сценарий № 3: фильтрация списков IP-адресов (первый список)
    elif user_state == 'awaiting_filter_first_input':
        if re.findall(pattern_subnets_and_ips, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                user_states[user_id] = 'awaiting_filter_second_input'
                return await message.answer("Теперь введите второй список IP-адресов.", reply_markup=keyboard_back)
            except Exception as e:
                logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
                logging.error(traceback.format_exc())
                return await message.answer(f"При выполнении программы возникла ошибка: {e}.")
        else:
            return await message.answer("Введенный текст не содержит IP-адреса.", reply_markup=keyboard_back)

    # сценарий № 4: фильтрация списков IP-адресов (второй список)
    elif user_state == 'awaiting_filter_second_input':
        second_ips = message.text
        if not re.findall(pattern_subnets_and_ips, second_ips):
            return await message.answer('Второй список не содержит IP-адреса. Введите второй список еще раз.', reply_markup=keyboard_back)
        else:
            first_ips = user_ips.get(user_id, {}).get('first', '')
            if first_ips.strip():
                try:
                    filtered_ips = await filter_ips(first_ips, second_ips)
                    if filtered_ips:
                        result_filtered_ips = "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(filtered_ips) + "</code>"
                        return await message.answer(f"{result_filtered_ips}", parse_mode='HTML', reply_markup=keyboard_back)
                    else:
                        return await message.answer(f"Отфильтрованный список пуст. IP-адресов нет.", reply_markup=keyboard_back)
                except Exception as e:
                    user_states[user_id] = 'awaiting_filter_first_input'
                    logging.error(f'Ошибка фильтрации для пользователя {user_id}: {e}')
                    logging.error(traceback.format_exc())
                    return await message.answer(f"Ошибка при фильтрации IP-адресов: {e} Попробуйте снова.", reply_markup=keyboard_back)
                user_states[user_id] = 'awaiting_filter_first_input'
            else:
                user_states[user_id] = 'awaiting_filter_first_input'
                return await message.answer("Ошибка: не был получен первый список IP-адресов.")

    # сценарий № 5: фильтрация списка IP-адресов по первому октету (ввод списка)
    elif user_state == 'awaiting_filter_octet_first':
        if re.findall(pattern_subnets_and_ips, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                user_states[user_id] = 'awaiting_filter_octet_second'
                return await message.answer("Введите октет - число от 1 до 255, по которому нужно отфильтровать IP-адреса.", reply_markup=keyboard_back)
            except Exception as e:
                logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
                logging.error(traceback.format_exc())
                return await message.answer(f"При выполнении программы возникла ошибка: {e}.")
        else:
            return await message.answer("Введенный текст не содержит IP-адреса.", reply_markup=keyboard_back)

    # сценарий № 6: фильтрация списка IP-адресов по первому октету (ввод октета)
    elif user_state == 'awaiting_filter_octet_second':
        try:
            if 0 < int(message.text) < 256:
                ips_input = user_ips.get(user_id, {}).get('first', '')
                try:
                    filtered_ips = await filter_by_octet(ips_input, message.text)
                    if filtered_ips:
                        result_filtered_ips = "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(filtered_ips) + "</code>"
                        user_states[user_id] = 'awaiting_filter_octet_first'
                        return await message.answer(f"{result_filtered_ips}", parse_mode='HTML', reply_markup=keyboard_back)
                    else:
                        user_states[user_id] = 'awaiting_filter_octet_first'
                        return await message.answer(f"Отфильтрованный список пуст. IP-адресов нет.", reply_markup=keyboard_back)
                except Exception as e:
                    return await message.answer(f"Ошибка при фильтрации IP-адресов: {e} Попробуйте снова.", reply_markup=keyboard_back)
            else:
                return await message.answer('Введено неверное значение октета. Попробуйте еще раз.', reply_markup=keyboard_back)
        except Exception as e:
            user_states[user_id] = 'awaiting_filter_octet_second'
            return await message.answer('Введено неверное значение октета. Попробуйте еще раз.', reply_markup=keyboard_back)

    # сценарий № 7: обновление базы данных в процессе
    elif user_state == 'awaiting_database_update':
        return await message.answer(f"База данных обновляется, пожалуйста, подождите.")

    else:
        return await message.answer("Выберите нужное действие:", reply_markup=keyboard_choice, parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)
