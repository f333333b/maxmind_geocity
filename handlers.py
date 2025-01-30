import logging
import re
import traceback
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram import Router
from itertools import chain
from help import help_text
#from messages import msgs
from keyboards import keyboard_choice, keyboard_back, keyboard_copy
from db_updating import is_update_needed
from main_func import get_ip_info, to_filter_ips
from config import pattern, user_states, user_data, user_ips

router = Router()

# обработка команды /start
@router.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Выберете нужное действие:", reply_markup=keyboard_choice)

@router.message(Command("help"))
async def command_help_handler(message: Message):
    await message.answer(help_text, parse_mode='HTML', reply_markup=keyboard_choice)

# обработка callback-запросов от кнопок
@router.callback_query()
async def handle_callback(query: CallbackQuery):
    user_id = query.from_user.id

    # сценарий № 1: определение геолокации IP-адресов
    if query.data == 'basic_check':
        user_states[user_id] = 'awaiting_basic_check'
        await query.message.answer("Введите текст с IP-адресами.", reply_markup=keyboard_back)

    # сценарий № 2: определение геолокации IP-адресов с фильтрацией по стране
    elif query.data == 'target_check':
        user_states[user_id] = 'awaiting_target_check'
        await query.message.answer('Введите текст с IP-адресами.\nПервыми двумя буквами текста укажите\nISO-код страны.',
            reply_markup=keyboard_back)

    # сценарий № 3: фильтрация списков IP-адресов (основной список)
    elif query.data == 'filter_ips_1':
        user_states[user_id] = 'awaiting_filter_first_input'
        await query.message.answer("Введите список IP-адресов, которые нужно отфильтровать.", reply_markup=keyboard_back)

    # сценарий № 4: фильтрация списков IP-адресов (второй список)
    elif query.data == 'filter_ips_2':
        user_states[user_id] = 'awaiting_filter_second_input'
        await query.message.answer("Введите второй список IP-адресов.", reply_markup=keyboard_back)

    # сценарий № 5: вывод IP-адресов в столбик для копирования
    elif query.data == 'copy_ips':
        result_copy = user_data.get(user_id, [])
        if not result_copy:
            await query.message.answer('Не указана страна для фильтрации IP-адресов.\nВведите текст с указанием ISO-кода страны (например, "US" для США).', reply_markup=keyboard_back)
        elif result_copy == 'ips not found':
            await query.message.answer('IP-адреса указанной страны не найдены в тексте.', reply_markup=keyboard_back)
        elif result_copy == 'empty':
            await query.message.answer('IP-адреса указанной страны отсутствуют в тексте.', parse_mode="HTML", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_target_check'
        else:
            if all(isinstance(item, str) for item in result_copy):
                # отправляем список IP-адресов пользователю
                formatted_ips = "\n".join(result_copy)
                await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
            else:
                flat_ips = list(chain.from_iterable(
                    item if isinstance(item, list) else [item] for item in result_copy))
                formatted_ips = "\n".join(flat_ips)
                await query.message.answer(formatted_ips, parse_mode="HTML", reply_markup=keyboard_back)
        user_states[user_id] = 'awaiting_target_check'

    # сценарий № 6: помощь (справка)
    elif query.data == "help":
        await query.message.answer(help_text, parse_mode="HTML", reply_markup=keyboard_choice)
    elif query.data == "back_to_choice":
        await query.message.answer(text='Выберете нужное действие:', reply_markup=keyboard_choice)

# обработка сообщений
@router.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    # проверка на наличие актуальной скачанной базы данных
    update_result = await is_update_needed(user_id)
    if update_result == 'error':
        await message.answer(f"При обновлении базы данных возникла ошибка. Попробуйте позднее.")

    # проверка на ввод неверной команды
    if message.text.startswith('/') and message.text.count('\n') <= 1:
        await message.answer(f'Неизвестная команда.\nДля получения справки наберите /help.', reply_markup=keyboard_back)

    # сценарий № 1: определение геолокации IP-адресов с фильтрацией по стране
    elif user_state == 'awaiting_target_check':
        try:
            result, result_copy = await get_ip_info(message.text, target_flag=True)
            if result:
                if result == 'invalid iso':
                    await message.answer('Введен неверный ISO-код страны.\nВведите текст заново, первыми двумя буквами укажите ISO-код страны.\nНапример, "US" для США.', parse_mode="HTML", reply_markup=keyboard_back)
                    user_states[user_id] = 'awaiting_target_check'
                elif isinstance(result, list):
                    await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_copy)
                    user_data[user_id] = result_copy
                else:
                    await message.answer(result, parse_mode="HTML", reply_markup=keyboard_copy)
            else:
                await message.answer('Во введенном тексте IP-адреса не найдены. Попробуйте еще раз.', parse_mode="HTML", reply_markup=keyboard_back)
        except Exception as e:
            await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_copy)
            user_states[user_id] = 'awaiting_target_check'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
            logging.error(traceback.format_exc())

    # сценарий # 2: определение геолокации IP-адресов
    elif user_state == 'awaiting_basic_check':
        try:
            result, result_copy = await get_ip_info(message.text, target_flag=False)
            if result:
                if result == 'invalid iso':
                    await message.answer('Введен неверный ISO-код страны.\nПервыми двумя буквами в тексте укажите ISO-код страны.\nНапример, "US" для США.', parse_mode="HTML", reply_markup=keyboard_back)
                    user_states[user_id] = 'awaiting_basic_check'
                elif isinstance(result, list):
                    await message.answer('\n'.join(str(item) for item in result), parse_mode="HTML", reply_markup=keyboard_back)
                else:
                    await message.answer(result, parse_mode="HTML", reply_markup=keyboard_back)
            else:
                await message.answer('Во введенном тексте IP-адреса не найдены. Попробуйте еще раз.', parse_mode="HTML", reply_markup=keyboard_back)
        except Exception as e:
            await message.answer(f"При выполнении программы возникла ошибка: {e}.", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_basic_check'
            logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
            logging.error(traceback.format_exc())

    # сценарий № 3: фильтрация списков IP-адресов (первый список)
    elif user_state == 'awaiting_filter_first_input':
        if re.findall(pattern, message.text):
            try:
                user_ips[user_id] = {'first': message.text}
                await message.answer("Теперь введите второй список IP-адресов.", reply_markup=keyboard_back)
                user_states[user_id] = 'awaiting_filter_second_input'
            except Exception as e:
                await message.answer(f"При выполнении программы возникла ошибка: {e}.")
                logging.error(f"При выполнении программы возникла ошибка: {e}.\nТекст запроса: {message.text}")
                logging.error(traceback.format_exc())
        else:
            await message.answer("Введенный текст не содержит IP-адреса.", reply_markup=keyboard_back)
            user_states[user_id] = 'awaiting_filter_first_input'

    # сценарий № 4: фильтрация списков IP-адресов (второй список)
    elif user_state == 'awaiting_filter_second_input':
        second_ips = message.text
        if not re.findall(pattern, second_ips):
            await message.answer('Второй список не содержит IP-адреса. Введите второй список еще раз.', reply_markup=keyboard_back)
        else:
            first_ips = user_ips.get(user_id, {}).get('first', '')
            if first_ips.strip():
                try:
                    filtered_ips = await to_filter_ips(first_ips, second_ips)
                    result_filtered_ips = '\n'.join(filtered_ips)
                    if filtered_ips:
                        await message.answer(f"Отфильтрованные IP-адреса:")
                        await message.answer(f"{result_filtered_ips}", reply_markup=keyboard_back)
                        user_states[user_id] = None  # сброс состояния после фильтрации
                    else:
                        await message.answer(f"Отфильтрованный список пуст. IP-адресов нет.", reply_markup=keyboard_back)
                        user_states[user_id] = 'awaiting_filter_first_input'
                except Exception as e:
                    await message.answer(f"Ошибка при фильтрации IP-адресов: {e} Попробуйте снова.", reply_markup=keyboard_back)
                    user_states[user_id] = 'awaiting_filter_first_input'
                    logging.error(f'Ошибка фильтрации для пользователя {user_id}: {e}')
                    logging.error(traceback.format_exc())
            else:
                await message.answer("Ошибка: не был получен первый список IP-адресов.")
                user_states[user_id] = 'awaiting_filter_first_input'

    # сценарий № 5: обновление базы данных в процессе
    elif user_state == 'awaiting_database_update':
        await message.answer(f"База данных обновляется, пожалуйста, подождите.")

    else:
        await message.answer("Выберите нужное действие:", reply_markup=keyboard_choice, parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)
