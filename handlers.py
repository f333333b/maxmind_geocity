import logging
import re
import traceback
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Router
from itertools import chain
from keyboards import keyboard_back, keyboard_main
from db_updating import is_update_needed
from main_func import process_check, filter_ips, filter_by_octet, log_interaction
from config import pattern_subnets_and_ips, user_states, user_data, user_ips
from commands import commands
from messages import msg

router = Router()

# обработка отправки фото, файлов и т.п.
@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def handle_unsupported_content(message: Message):
    return await message.answer(msg['invalid_input'], reply_markup=keyboard_back)

# обработка команды /start
@router.message(CommandStart())
@log_interaction
async def command_start_handler(message: Message):
    return await message.answer(msg['start'], reply_markup=keyboard_main)

@router.message(Command("help"))
@log_interaction
async def command_help_handler(message: Message):
    return await message.answer(msg['help'], parse_mode='HTML')

# сценарий № 1: определение геолокации IP-адресов
@router.message(Command("check"))
@log_interaction
async def command_check_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_basic_check'
    return await message.answer(msg["enter_check_ips"])

# сценарий № 2: определение геолокации IP-адресов с фильтрацией по стране
@router.message(Command("target"))
@log_interaction
async def command_target_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_target_check'
    return await message.answer(msg['enter_target_ips'],
            reply_markup=keyboard_back)

# сценарий № 3: фильтрация списков IP-адресов (основной список)
@router.message(Command("filter"))
@log_interaction
async def command_filter_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_filter_first_input'
    return await message.answer(msg['filter_ips_first'])

# сценарий № 4: фильтрация списка IP-адресов по октету (ввод списка)
@router.message(Command("filter_octet"))
@log_interaction
async def command_filter_octet_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_filter_octet_first'
    return await message.answer(msg['filter_ips_first'], reply_markup=keyboard_back)

# обработка callback-запросов от Inline-кнопок
@router.callback_query()
@log_interaction
async def handle_callback(query: CallbackQuery):
    if query.data == "back_to_choice":
        return await query.message.answer(text=msg['start'])
    elif query.data == 'copy_ips':
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

# обработка сообщений
@router.message()
@log_interaction
async def handle_text(message: Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    # проверка на наличие актуальной скачанной базы данных
    update_result = await is_update_needed(user_id)
    if update_result == 'error':
        return await message.answer(msg['db_update_error'])

    # проверка на ввод неверной команды
    if message.text.startswith('/') and message.text.count('\n') <= 1 and not any(message.text == command.command for command in commands):
        return await message.answer(msg['invalid_command'])

    # сценарий № 1: определение геолокации IP-адресов с фильтрацией по стране
    if user_state == 'awaiting_target_check':
        await process_check('awaiting_target_check', message, user_id, target_flag=True)

    # сценарий # 2: определение геолокации IP-адресов
    elif user_state == 'awaiting_basic_check':
        await process_check('awaiting_basic_check', message, user_id, target_flag=False)

    # сценарий № 3: фильтрация списков IP-адресов (первый список)
    elif user_state == 'awaiting_filter_first_input':
        if re.findall(pattern_subnets_and_ips, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                user_states[user_id] = 'awaiting_filter_second_input'
                return await message.answer(msg['filter_ips_second'], reply_markup=keyboard_back)
            except Exception as e:
                logging.error(f"{msg['program_error']}: {e}.\nТекст запроса: {message.text}")
                logging.error(traceback.format_exc())
                return await message.answer(f"{msg['program_error']}: {e}.")
        else:
            return await message.answer(msg['no_ips'])

    # сценарий № 4: фильтрация списков IP-адресов (второй список)
    elif user_state == 'awaiting_filter_second_input':
        second_ips = message.text
        if not re.findall(pattern_subnets_and_ips, second_ips):
            return await message.answer(msg['no_ips_second'], reply_markup=keyboard_back)
        else:
            first_ips = user_ips.get(user_id, {}).get('first', '')
            if first_ips.strip():
                try:
                    filtered_ips = await filter_ips(first_ips, second_ips)
                    if filtered_ips:
                        result_filtered_ips = "Отфильтрованные IP-адреса:\n<code>" + "</code>\n<code>".join(filtered_ips) + "</code>"
                        return await message.answer(f"{result_filtered_ips}", parse_mode='HTML')
                    else:
                        return await message.answer(msg['no_filtered_ips'])
                except Exception as e:
                    user_states[user_id] = 'awaiting_filter_first_input'
                    logging.error(f"{msg['filter_error']} для пользователя {user_id}: {e}")
                    logging.error(traceback.format_exc())
                    return await message.answer(f"{msg['filter_error']}: {e} Попробуйте снова.")
                user_states[user_id] = 'awaiting_filter_first_input'
            else:
                user_states[user_id] = 'awaiting_filter_first_input'
                return await message.answer(msg['no_first_input'])

    # сценарий № 5: фильтрация списка IP-адресов по первому октету (ввод списка)
    elif user_state == 'awaiting_filter_octet_first':
        if re.findall(pattern_subnets_and_ips, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                user_states[user_id] = 'awaiting_filter_octet_second'
                return await message.answer(msg['enter_octet'], reply_markup=keyboard_back)
            except Exception as e:
                logging.error(f"{msg['program_error']}: {e}.\nТекст запроса: {message.text}")
                logging.error(traceback.format_exc())
                return await message.answer(f"{msg['program_error']}: {e}.")
        else:
            return await message.answer(msg['no_ips'])

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
                        return await message.answer(f"{result_filtered_ips}", parse_mode='HTML')
                    else:
                        user_states[user_id] = 'awaiting_filter_octet_first'
                        return await message.answer(msg['no_filtered_ips'])
                except Exception as e:
                    return await message.answer(f"Ошибка при фильтрации IP-адресов: {e} Попробуйте снова.")
            else:
                return await message.answer(msg['invalid_octet'], reply_markup=keyboard_back)
        except Exception as e:
            user_states[user_id] = 'awaiting_filter_octet_second'
            return await message.answer(msg['invalid_octet'], reply_markup=keyboard_back)

    # сценарий № 7: обновление базы данных в процессе
    elif user_state == 'awaiting_database_update':
        return await message.answer(msg['db_updating'])

    else:
        return await message.answer(msg['start'], parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)
