from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Router
from keyboards import keyboard_back, keyboard_main
from db_updating import is_update_needed
from main_func import process_check, process_target_output, filter_ips_input, filter_ips_list, filter_by_octet, log_interaction
from config import user_states
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

# обработка команды /help
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
    return await message.answer(msg['enter_target_ips'])

# сценарий № 3: фильтрация списков IP-адресов (основной список)
@router.message(Command("filter"))
@log_interaction
async def command_filter_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_filter_first_input'
    return await message.answer(msg['filter_ips_first'])

# сценарий № 4: фильтрация по октету (ввод октета)
@router.message(Command("filter_octet"))
@log_interaction
async def command_filter_octet_handler(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = 'awaiting_filter_octet_list'
    return await message.answer(msg['filter_ips_first'])

# обработка callback-запросов от Inline-кнопок
@router.callback_query()
@log_interaction
async def handle_callback(query: CallbackQuery):
    user_id = query.from_user.id
    if query.data == 'copy_ips':
        formatted_ips, error_message = await process_target_output(user_id)
        user_states[user_id] = 'awaiting_target_check'
        text = error_message or formatted_ips
        return await query.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard_back)

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
    if message.text.startswith('/') and not any(message.text == command.command for command in commands):
        return await message.answer(msg['invalid_command'])

    # сценарий № 1: определение геолокации IP-адресов с фильтрацией по стране
    if user_state == 'awaiting_target_check':
        await process_check('awaiting_target_check', message, user_id, target_flag=True)

    # сценарий # 2: определение геолокации IP-адресов
    elif user_state == 'awaiting_basic_check':
        await process_check('awaiting_basic_check', message, user_id, target_flag=False)

    # сценарий № 3: фильтрация списков IP-адресов по списку (ввод первого списка)
    elif user_state == 'awaiting_filter_first_input':
        return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=True), parse_mode="HTML")

    # сценарий № 4: фильтрация списка IP-адресов по первому октету (ввод списка)
    elif user_state == 'awaiting_filter_octet_list':
        return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=False), parse_mode="HTML")

    # сценарий № 5: фильтрация списков IP-адресов по списку (ввод второго списка)
    elif user_state == 'awaiting_filter_second_input': # переименовать на awaiting_filter_list?
        return await message.answer(text=await filter_ips_list(message.text, user_id), parse_mode="HTML")

    # сценарий № 6: фильтрация списка IP-адресов по первому октету (ввод октета)
    elif user_state == 'awaiting_filter_by_octet': # переименовать на awaiting_filter_by_octet?
        return await message.answer(text=await filter_by_octet(message.text, user_id), parse_mode="HTML")

    # сценарий № 7: обновление базы данных в процессе
    elif user_state == 'awaiting_database_update':
        return await message.answer(msg['db_updating'])

    else:
        return await message.answer(msg['start'], parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)
