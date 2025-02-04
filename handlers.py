from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Router
from keyboards import keyboard_main
from db_updating import is_update_needed
from main_func import process_check, process_target_output, filter_ips_input, filter_ips_list, filter_by_octet, log_interaction
from config import user_states, user_data
from commands import commands
from messages import msg
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

# класс для состояния пользователя
class UserState(StatesGroup):
    START = State()
    HELP = State()
    AWAITING_BASIC_CHECK = State()
    AWAITING_TARGET_CHECK = State()
    AWAITING_FILTER_LIST_FIRST = State()
    AWAITING_FILTER_LIST_SECOND = State()
    AWAITING_FILTER_OCTET_FIRST = State()
    AWAITING_FILTER_OCTET_SECOND = State()
    AWAITING_DATABASE_UPDATE = State()
    COPY_IPS = State()

router = Router()

# обработка отправки фото, файлов и т.п.
@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def handle_unsupported_content(message: Message):
    return await message.answer(msg['invalid_input'])

@router.message(UserState.START)
@log_interaction
async def command_start_handler(message: Message):
    """Обработка команды /start"""
    return await message.answer('Здравствуйте! ' + msg['start'], reply_markup=keyboard_main)

@router.message(UserState.HELP)
@log_interaction
async def command_help_handler(message: Message):
    """Обработка команды /help"""
    return await message.answer(msg['help'], parse_mode='HTML')

@router.message(UserState.AWAITING_BASIC_CHECK)
@log_interaction
async def command_check_handler(message: Message):
    """Определение геолокации IP-адресов"""
    return await message.answer(msg["enter_check_ips"])

@router.message(UserState.AWAITING_TARGET_CHECK)
@log_interaction
async def command_target_handler(message: Message):
    """Определение геолокации IP-адресов с фильтрацией по стране"""
    return await message.answer(msg['enter_target_ips'])

@router.callback_query(StateFilter(UserState.COPY_IPS))
@log_interaction
async def handle_callback(query: CallbackQuery):
    """Обработка нажатия кнопки 'Вывести строки с IP-адресами указанной страны'"""
    #user_id = query.from_user.id
    #if query.data == 'copy_ips':
    #    result_copy = user_data.get(user_id, [])
    #    formatted_ips, error_message = await process_target_output(result_copy)
    #    user_states[user_id] = 'awaiting_target_check'
    #    text = error_message or formatted_ips
    #    return await query.message.answer(text=text, parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_LIST_FIRST)
@log_interaction
async def command_filter_handler(message: Message):
    """Обработка команды /filter - фильтрация списков IP-адресов (основной список)"""
    return await message.answer(msg['filter_ips_first'])

@router.message(UserState.AWAITING_FILTER_LIST_SECOND)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обработка ввода второго списка при фильтрации списков IP-адресов"""
    return await message.answer(msg['filter_ips_second'])

@router.message(UserState.AWAITING_FILTER_OCTET_FIRST)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обработка команды /filter_octet - фильтрация списков IP-адресов по октету (ввод списка)"""
    return await message.answer(text=await filter_ips_input(message.text, list_flag=False), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_SECOND)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обработка ввода октета  при фильтрации списков IP-адресов по октету"""
    return await message.answer(text=await filter_by_octet(message.text), parse_mode="HTML")

@router.message(UserState.AWAITING_DATABASE_UPDATE)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обновление базы данных"""
    return await message.answer(msg['db_updating'])


#новые хендлеры
@router.message(UserState.AWAITING_TARGET_CHECK)
@log_interaction
async def handle_target_check(message: Message, state: FSMContext):
    """Определение геолокации IP-адресов с фильтрацией по стране"""
    user_id = message.from_user.id
    await process_check('awaiting_target_check', message, user_id, target_flag=True)




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



def register_handlers(dp):
    dp.include_router(router)