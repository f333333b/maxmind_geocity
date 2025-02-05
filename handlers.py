from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Router
from config import trusted_users
from keyboards import keyboard_main
from main_func import process_check, filter_ips_input, filter_ips_list, filter_by_octet, log_interaction
from commands import commands
from messages import msg
#from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

# класс для состояния пользователя
class UserState(StatesGroup):
    START = State()
    HELP = State()
    BASIC_CHECK = State()
    TARGET_CHECK = State()
    FILTER_LIST = State()
    FILTER_OCTET = State()
    AWAITING_BASIC_CHECK = State()
    AWAITING_TARGET_CHECK = State()
    AWAITING_FILTER_LIST_FIRST = State()
    AWAITING_FILTER_LIST_SECOND = State()
    AWAITING_FILTER_OCTET_FIRST = State()
    AWAITING_FILTER_OCTET_SECOND = State()
    AWAITING_DATABASE_UPDATE = State()
    COPY_IPS = State()

router = Router()

@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def unsupported_content_handler(message: Message):
    """Обработка ввода неподдерживаемых форматов данных - фото, документы и т.д."""
    return await message.answer(msg['invalid_input'])

@router.message(lambda message: message.text.startswith('/') and
                not any(message.text == command.command for command in commands))
@log_interaction
async def handle_unsupported_command_handler(message: Message):
    """Обработка ввода неверной команды"""
    return await message.answer(msg['invalid_command'])

@router.message(UserState.START)
@log_interaction
async def command_start_handler(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    if user_id in trusted_users:
        return await message.answer('Здравствуйте! Вы авторизованы. ' + msg['start'], reply_markup=keyboard_main)
    else:
        return await message.answer(msg['no_access'])

@router.message(UserState.HELP)
@log_interaction
async def command_help_handler(message: Message):
    """Обработка команды /help"""
    return await message.answer(msg['help'], parse_mode='HTML')

@router.message(UserState.BASIC_CHECK)
@log_interaction
async def command_check_handler(message: Message):
    """Обработка команды /check"""
    return await message.answer(msg["enter_check_ips"])

@router.message(UserState.TARGET_CHECK)
@log_interaction
async def command_target_handler(message: Message):
    """Обработка команды /target"""
    return await message.answer(msg['enter_target_ips'])

@router.message(UserState.FILTER_LIST)
@log_interaction
async def command_filter_list_handler(message: Message):
    """Обработка команды /filter"""
    return await message.answer(msg['filter_ips_first'])

@router.message(UserState.FILTER_OCTET)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обработка команды /filter_octet"""
    return await message.answer(text=await filter_ips_input(message.text, list_flag=False), parse_mode="HTML") # переделать

@router.message(UserState.AWAITING_BASIC_CHECK)
@log_interaction
async def process_check_handler(message: Message):
    """Обработка функции /check - ввода текста"""
    return await process_check(message, target_flag=False)

@router.message(UserState.AWAITING_TARGET_CHECK)
@log_interaction
async def process_target_handler(message: Message):
    """Обработка функции /target - ввода текста"""
    return await process_check(message, target_flag=True)

@router.callback_query(StateFilter(UserState.COPY_IPS))
@log_interaction
async def copy_ips_callback_handler(query: CallbackQuery):
    """Обработка нажатия кнопки 'Вывести строки с IP-адресами указанной страны'"""
    pass

@router.message(UserState.AWAITING_FILTER_LIST_FIRST)
@log_interaction
async def process_filter_list_first_handler(message: Message):
    """Обработка первого списка в /filter"""
    return await message.answer(text=await filter_ips_input(message.text, list_flag=True), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_LIST_SECOND)
@log_interaction
async def process_filter_list_second_handler(message: Message):
    """Обработка второго списка в /filter"""
    return await message.answer(text=await filter_ips_list(message.text), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_FIRST)
@log_interaction
async def process_filter_octet_first_handler(message: Message):
    """Обработка списка в /filter_octet"""
    return await message.answer(text=await filter_ips_input(message.text, list_flag=False), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_SECOND)
@log_interaction
async def process_filter_octet_second_handler(message: Message):
    """Обработка октета в /filter_octet"""
    return await message.answer(text=await filter_by_octet(message.text), parse_mode="HTML")

@router.message(UserState.AWAITING_DATABASE_UPDATE)
@log_interaction
async def command_filter_octet_handler(message: Message):
    """Обновление базы данных"""
    return await message.answer(msg['db_updating'])

def register_handlers(dp):
    dp.include_router(router)